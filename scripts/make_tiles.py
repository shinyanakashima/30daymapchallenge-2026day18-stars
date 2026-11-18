"""Scatter stars by sky class and write XYZ tiles (site/tiles/{z}/{x}/{y}.png).

Every star gets a fixed position, brightness, colour and a random rank u
(seeded, so the sky is the same every run). At zoom z only stars with
u < ZOOM_FRACTION ** (10 - z) are drawn, and a star's size tier comes from
its rank among the stars drawn at that zoom.

The brightest stars are also written to site/tiles/twinkle.geojson for the
twinkling layer on the page.
"""
import io
import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

import config as C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "tiles"
T = C.TILE_PX
M = 12  # margin so stars and glows on tile edges continue into the next tile
ZOOM_FRACTION = 0.47
KM_PER_PX_LAT = 111.32 / C.PX_PER_DEG
TWINKLE_STARS = 3000

# (upper bound of local rank, core sigma px, peak, glow sigma px, glow strength)
TIERS = [
    (0.012, 1.3, 255.0, 4.0, 0.16),
    (0.07, 0.9, 230.0, 2.4, 0.10),
    (0.28, 0.6, 175.0, 0.0, 0.0),
    (1.0, 0.0, 130.0, 0.0, 0.0),
]
# star colours (RGB multipliers) and their shares: white, blue-white, warm, pale blue
COLOURS = np.array([[1.00, 1.00, 1.00], [0.78, 0.86, 1.00], [1.00, 0.88, 0.70], [0.88, 0.94, 1.00]],
                   np.float32)
COLOUR_SHARE = np.cumsum([0.45, 0.25, 0.18, 0.12])


def sprite(sigma, glow_sigma, glow):
    r = int(math.ceil(max(sigma * 2.6, glow_sigma * 2.6, 0.5)))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    d2 = xx ** 2 + yy ** 2
    w = np.exp(-d2 / (2 * sigma ** 2)) if sigma else (d2 == 0).astype(float)
    if glow:
        w = w + glow * np.exp(-d2 / (2 * glow_sigma ** 2))
    keep = w > 0.012
    return yy[keep], xx[keep], w[keep]


SPRITES = [sprite(s, gs, g) for _, s, _, gs, g in TIERS]


def make_stars():
    cls = np.array(Image.open(ROOT / "data" / "processed" / "sky_class.png"))
    h, w = cls.shape
    dens = np.zeros(8, np.float64)
    for c in C.CLASSES:
        dens[c["id"]] = c["visible"] * C.STARS_PER_KM2_PER_VISIBLE
    lat_c = C.BBOX["north"] - (np.arange(h) + 0.5) / C.PX_PER_DEG
    cell = (KM_PER_PX_LAT ** 2) * np.cos(np.radians(lat_c))
    lam = dens[cls] * cell[:, None]
    rng = np.random.default_rng(C.SEED)
    counts = rng.poisson(lam).ravel()
    idx = np.repeat(np.arange(counts.size), counts)
    n = idx.size
    row, col = np.divmod(idx, w)
    lon = C.BBOX["west"] + (col + rng.random(n)) / C.PX_PER_DEG
    lat = C.BBOX["north"] - (row + rng.random(n)) / C.PX_PER_DEG
    u = rng.random(n)
    bright = rng.uniform(0.5, 1.0, n)
    colour = np.searchsorted(COLOUR_SHARE, rng.random(n), side="right").clip(0, len(COLOURS) - 1)
    return lon, lat, u, bright, colour


def merc(lon, lat, z):
    s = T * 2 ** z
    x = (lon + 180.0) / 360.0 * s
    lr = np.radians(lat)
    y = (1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / math.pi) / 2 * s
    return x, y


def png(arr):
    b = io.BytesIO()
    Image.fromarray(arr, "RGB").save(b, "PNG", optimize=True)
    return b.getvalue()


def write_twinkle(lon, lat, u, colour):
    order = np.argsort(u)[:TWINKLE_STARS]
    feats = []
    for k, i in enumerate(order):
        r, g, b = (COLOURS[colour[i]] * 255).astype(int)
        feats.append(dict(type="Feature",
                          properties=dict(g=int(k % 3), s=round(float(1.6 - u[i] / u[order[-1]]), 2),
                                          c=f"#{r:02x}{g:02x}{b:02x}"),
                          geometry=dict(type="Point", coordinates=[round(float(lon[i]), 4),
                                                                   round(float(lat[i]), 4)])))
    (OUT / "twinkle.geojson").write_text(json.dumps(dict(type="FeatureCollection", features=feats),
                                                    separators=(",", ":")))


def main():
    lon, lat, u, bright, colour = make_stars()
    print(f"{lon.size:,} stars")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    write_twinkle(lon, lat, u, colour)
    black = png(np.zeros((T, T, 3), np.uint8))
    b = C.BBOX
    summary = {}
    for z in C.TILE_ZOOMS:
        frac = ZOOM_FRACTION ** (10 - z)
        sel = u < frac
        x, y = merc(lon[sel], lat[sel], z)
        v = u[sel] / frac
        br = bright[sel]
        rgb = COLOURS[colour[sel]]
        tier = np.searchsorted([t[0] for t in TIERS], v, side="right")
        tier = np.minimum(tier, len(TIERS) - 1)
        x0, y0 = merc(np.array([b["west"]]), np.array([b["north"]]), z)
        x1, y1 = merc(np.array([b["east"]]), np.array([b["south"]]), z)
        tx0, tx1 = int(x0[0] // T), int(x1[0] // T)
        ty0, ty1 = int(y0[0] // T), int(y1[0] // T)
        order = np.argsort(y)
        x, y, br, tier, rgb = x[order], y[order], br[order], tier[order], rgb[order]
        ntiles = 0
        width = (tx1 - tx0 + 1) * T + 2 * M
        for ty in range(ty0, ty1 + 1):
            a = np.searchsorted(y, ty * T - M)
            e = np.searchsorted(y, (ty + 1) * T + M)
            canvas = np.zeros((T + 2 * M, width, 3), np.float32)
            xi = np.floor(x[a:e] - (tx0 * T - M)).astype(np.int64)
            yi = np.floor(y[a:e] - (ty * T - M)).astype(np.int64)
            for k, (_, _, peak, _, _) in enumerate(TIERS):
                m = tier[a:e] == k
                if not m.any():
                    continue
                val = (peak * br[a:e][m])[:, None] * rgb[a:e][m]
                dy, dx, wt = SPRITES[k]
                for oy, ox, ww in zip(dy, dx, wt):
                    yy, xx = yi[m] + oy, xi[m] + ox
                    ok = (yy >= 0) & (yy < canvas.shape[0]) & (xx >= 0) & (xx < width)
                    for ch in range(3):
                        np.add.at(canvas[:, :, ch], (yy[ok], xx[ok]), ww * val[ok, ch])
            img = (255 * (1 - np.exp(-canvas / 200.0))).astype(np.uint8)
            for tx in range(tx0, tx1 + 1):
                c0 = (tx - tx0) * T + M
                t = img[M:M + T, c0:c0 + T]
                p = OUT / str(z) / str(tx)
                p.mkdir(parents=True, exist_ok=True)
                (p / f"{ty}.png").write_bytes(png(t) if t.any() else black)
                ntiles += 1
        summary[z] = dict(tiles=ntiles, stars=int(sel.sum()))
        print(z, summary[z], flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary))


if __name__ == "__main__":
    main()
