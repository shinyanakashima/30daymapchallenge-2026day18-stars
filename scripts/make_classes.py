"""Night lights -> blurred sky brightness -> sky classes on Japan's land.

Outputs
  data/processed/sky_class.png   uint8 grid, 15", 0 = not Japan land, 1-6 = class
  data/processed/meta.json       grid, thresholds, statistics
  site/data/sky_class.png        1/2 resolution lookup image for the web page
  site/data/coastline.geojson    Japan outline (Natural Earth)
  site/data/cities.geojson       main cities (Natural Earth)
"""
import json
import math
from pathlib import Path

import numpy as np
import shapefile
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

import config as C

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
SITE = ROOT / "site" / "data"
NE = RAW / "naturalearth"
KM_PER_PX_LAT = 111.32 / C.PX_PER_DEG

CITIES = ["Sapporo", "Asahikawa", "Hakodate", "Obihiro", "Kushiro", "Aomori", "Morioka",
          "Akita", "Sendai", "Niigata", "Tokyo", "Yokohama", "Nagano", "Kanazawa", "Shizuoka",
          "Nagoya", "Kyoto", "Ōsaka", "Kōbe", "Okayama", "Hiroshima", "Matsuyama", "Kochi",
          "Fukuoka", "Kumamoto", "Kagoshima", "Naha"]


def records(path):
    r = shapefile.Reader(str(path))
    names = [f[0] for f in r.fields[1:]]
    for sr in r.iterShapeRecords():
        yield dict(zip(names, sr.record)), sr.shape


def rings(shape):
    parts = list(shape.parts) + [len(shape.points)]
    for a, b in zip(parts[:-1], parts[1:]):
        yield shape.points[a:b]


def mosaic(year):
    m = C.MOSAIC
    n = 10 * C.PX_PER_DEG
    arr = np.zeros((m["nv"] * n, m["nh"] * n), np.float32)
    for j in range(m["nv"]):
        for i in range(m["nh"]):
            p = RAW / "blackmarble" / str(year) / f"h{m['h0'] + i}v{m['v0'] + j:02d}.npy"
            tile = np.load(p) if p.exists() else np.zeros((n, n), np.float32)
            arr[j * n:(j + 1) * n, i * n:(i + 1) * n] = np.nan_to_num(tile, nan=0.0)
    return arr


def blur(rad):
    """Gaussian blur with sigma in km; the x sigma follows latitude band by band."""
    m = C.MOSAIC
    sy = C.BLUR_SIGMA_KM / KM_PER_PX_LAT
    trunc = C.BLUR_RADIUS_KM / C.BLUR_SIGMA_KM
    out = np.empty_like(rad)
    band = C.PX_PER_DEG  # 1 degree bands
    pad = int(math.ceil(C.BLUR_RADIUS_KM / KM_PER_PX_LAT)) + 2
    for r0 in range(0, rad.shape[0], band):
        r1 = min(r0 + band, rad.shape[0])
        lat = m["north"] - (r0 + r1) / 2 / C.PX_PER_DEG
        sx = sy / math.cos(math.radians(lat))
        a0, a1 = max(0, r0 - pad), min(rad.shape[0], r1 + pad)
        b = gaussian_filter(rad[a0:a1], sigma=(sy, sx), truncate=trunc, mode="nearest")
        out[r0:r1] = b[r0 - a0:r0 - a0 + (r1 - r0)]
    return out


def crop(arr):
    m, b = C.MOSAIC, C.BBOX
    c0 = round((b["west"] - m["west"]) * C.PX_PER_DEG)
    c1 = round((b["east"] - m["west"]) * C.PX_PER_DEG)
    r0 = round((m["north"] - b["north"]) * C.PX_PER_DEG)
    r1 = round((m["north"] - b["south"]) * C.PX_PER_DEG)
    return arr[r0:r1, c0:c1]


def to_px(lon, lat, scale=1):
    b = C.BBOX
    return ((lon - b["west"]) * C.PX_PER_DEG * scale, (b["north"] - lat) * C.PX_PER_DEG * scale)


def raster_polys(shapes, w, h, scale=1, value=255):
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for shp in shapes:
        for ring in rings(shp):
            d.polygon([to_px(x, y, scale) for x, y in ring], fill=value)
    return np.array(img)


def main():
    rad = mosaic(C.YEAR)
    sky = crop(blur(rad))
    h, w = sky.shape
    japan = [s for r, s in records(NE / "ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
             if r["ADM0_A3"] == "JPN"]
    land = raster_polys(japan, w, h) > 0

    bounds = [c["max_rad"] for c in C.CLASSES[:-1]]
    cls = (np.digitize(sky, bounds) + 1).astype(np.uint8)
    cls[~land] = 0
    Image.fromarray(cls).save(OUT / "sky_class.png", optimize=True)

    # web lookup (every 2nd pixel, value*40 so it survives any 8-bit handling)
    Image.fromarray((cls[::2, ::2] * 40).astype(np.uint8)).save(SITE / "sky_class.png", optimize=True)

    lat_c = C.BBOX["north"] - (np.arange(h) + 0.5) / C.PX_PER_DEG
    cell_km2 = (KM_PER_PX_LAT ** 2) * np.cos(np.radians(lat_c))[:, None] * np.ones((1, w))
    total = float(cell_km2[land].sum())
    stats = []
    for c in C.CLASSES:
        sel = cls == c["id"]
        area = float(cell_km2[sel].sum())
        stats.append(dict(id=c["id"], area_km2=round(area), share=round(area / total, 4),
                          stars=round(area * c["visible"] * C.STARS_PER_KM2_PER_VISIBLE)))

    # prefecture ranking by stars drawn per km2
    s = 4
    cls_s = cls[::s, ::s]
    km_s = cell_km2[::s, ::s]
    dens = np.zeros(8, np.float64)
    for c in C.CLASSES:
        dens[c["id"]] = c["visible"] * C.STARS_PER_KM2_PER_VISIBLE
    prefs = []
    for r, shp in records(NE / "ne_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp"):
        if r["adm0_a3"] != "JPN":
            continue
        m = raster_polys([shp], cls_s.shape[1], cls_s.shape[0], 1 / s) > 0
        m &= cls_s > 0
        if not m.any():
            continue
        a = km_s[m].sum()
        prefs.append(dict(en=r["name"], ja=r["name_ja"],
                          stars_per_km2=round(float((dens[cls_s[m]] * km_s[m]).sum() / a), 3),
                          darkest_share=round(float(km_s[m & (cls_s == 1)].sum() / a), 3)))
    prefs.sort(key=lambda p: -p["stars_per_km2"])

    meta = dict(year=C.YEAR, layer="VNP46A4 AllAngle_Composite_Snow_Free", bbox=C.BBOX,
                px_per_deg=C.PX_PER_DEG, width=w, height=h,
                blur_sigma_km=C.BLUR_SIGMA_KM, blur_radius_km=C.BLUR_RADIUS_KM,
                classes=[{**c, "max_rad": (None if math.isinf(c["max_rad"]) else c["max_rad"])}
                         for c in C.CLASSES],
                stats=stats, land_km2=round(total),
                sky_percentiles={str(p): round(float(np.percentile(sky[land], p)), 3)
                                 for p in (5, 25, 50, 75, 90, 95, 99)},
                prefectures=prefs)
    (OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    site_meta = dict(year=C.YEAR, bbox=C.BBOX, lookup_px_per_deg=C.PX_PER_DEG / 2,
                     lookup_scale=40, classes=meta["classes"], stats=stats,
                     stars_per_km2_per_visible=C.STARS_PER_KM2_PER_VISIBLE)
    (SITE / "meta.json").write_text(json.dumps(site_meta, ensure_ascii=False, indent=1))

    # coastline: Japan outline
    feats = []
    for shp in japan:
        for ring in rings(shp):
            if len(ring) < 4:
                continue
            feats.append(dict(type="Feature", properties={},
                              geometry=dict(type="LineString",
                                            coordinates=[[round(x, 4), round(y, 4)] for x, y in ring])))
    (SITE / "coastline.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats)))

    cities = {}
    for r, shp in records(NE / "ne_10m_populated_places/ne_10m_populated_places.shp"):
        if r["ADM0_A3"] == "JPN" and r["NAME"] in CITIES and r["NAME"] not in cities:
            x, y = shp.points[0]
            cities[r["NAME"]] = dict(type="Feature",
                                     properties=dict(en=r["NAME"], ja=("東京" if r["NAME"] == "Tokyo" else r["NAME_JA"].removesuffix("市")),
                                                     rank=int(r["SCALERANK"])),
                                     geometry=dict(type="Point", coordinates=[round(x, 4), round(y, 4)]))
    missing = set(CITIES) - set(cities)
    if missing:
        print("cities not found:", missing)
    (SITE / "cities.geojson").write_text(json.dumps(dict(type="FeatureCollection",
                                                         features=list(cities.values())),
                                                    ensure_ascii=False))
    print(json.dumps(dict(stats=stats, pct=meta["sky_percentiles"], top=prefs[:8]),
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
