"""Download the source data.

NASA Black Marble VNP46A4 (annual night lights) needs a NASA Earthdata token:
    export EARTHDATA_TOKEN=...   (https://urs.earthdata.nasa.gov/ -> Generate Token)
    python scripts/fetch_data.py --year 2025

Natural Earth needs no login.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CMR = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=VNP46A4&version=2"
       "&temporal={y}-01-01T00:00:00Z,{y}-12-31T23:59:59Z&bounding_box=120,20,150,50&page_size=100")
# 10x10 degree Black Marble tiles covering Japan (lon 120-150E, lat 20-50N)
TILES = [f"h{h}v{v:02d}" for v in (4, 5, 6) for h in (30, 31, 32)]
LAYER = "AllAngle_Composite_Snow_Free"
NE = {
    "admin0": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
    "admin1": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip",
    "places": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip",
}


def get(url, dest, token=None):
    req = urllib.request.Request(url, headers={"User-Agent": "stars-map-preprocess"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def fetch_naturalearth():
    out = RAW / "naturalearth"
    out.mkdir(parents=True, exist_ok=True)
    for key, url in NE.items():
        name = url.rsplit("/", 1)[1]
        z = out / name
        if not z.exists():
            print("download", name)
            get(url, z)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(out / name[:-4])


def fetch_blackmarble(year):
    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        sys.exit("EARTHDATA_TOKEN is not set")
    out = RAW / "blackmarble" / str(year)
    out.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(CMR.format(y=year)) as r:
        entries = json.load(r)["feed"]["entry"]
    urls = [l["href"] for e in entries for l in e["links"]
            if l["href"].startswith("https://") and l["href"].endswith(".h5")
            and f".A{year}001." in l["href"]]
    for tile in TILES:
        npy = out / f"{tile}.npy"
        if npy.exists():
            continue
        hits = [u for u in urls if f".{tile}." in u]
        if not hits:
            print("missing tile", tile)
            continue
        name = hits[0].rsplit("/", 1)[1]
        h5 = out / name
        if not h5.exists():
            print("download", name)
            for attempt in range(4):
                try:
                    get(hits[0], h5.with_suffix(".part"), token)
                    h5.with_suffix(".part").rename(h5)
                    break
                except OSError as e:
                    print("  retry:", e)
                    time.sleep(2 ** (attempt + 1))
            else:
                sys.exit(f"download failed: {name}")
        with h5py.File(h5, "r") as f:
            ds = f[f"HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/{LAYER}"]
            raw = ds[()].astype(np.float32)
            fill = np.float32(np.ravel(ds.attrs.get("_FillValue", [-999.9]))[0])
            scale = float(np.ravel(ds.attrs.get("scale_factor", [1.0]))[0])
            offset = float(np.ravel(ds.attrs.get("offset", ds.attrs.get("add_offset", [0.0])))[0])
            lat = f["HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/lat"][()]
        assert lat[0] > lat[-1], "expected north-up rows"
        bad = (raw == fill) | (raw < 0)
        rad = np.where(bad, np.nan, raw * scale + offset).astype(np.float32)
        np.save(npy, rad)
        h5.unlink()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--skip-blackmarble", action="store_true")
    a = ap.parse_args()
    fetch_naturalearth()
    if not a.skip_blackmarble:
        fetch_blackmarble(a.year)
