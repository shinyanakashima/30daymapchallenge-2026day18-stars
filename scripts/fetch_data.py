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
import urllib.request
import zipfile
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LADS = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/VNP46A4"
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
    with urllib.request.urlopen(f"{LADS}/{year}/001.json") as r:
        listing = json.load(r)["content"]
    for tile in TILES:
        npy = out / f"{tile}.npy"
        if npy.exists():
            continue
        names = [c["name"] for c in listing if f".{tile}." in c["name"]]
        if not names:
            print("missing tile", tile)
            continue
        h5 = out / names[0]
        print("download", names[0])
        get(f"{LADS}/{year}/001/{names[0]}", h5, token)
        with h5py.File(h5, "r") as f:
            ds = f[f"HDFEOS/GRIDS/VIIRS_Grid_DNB_2d/Data Fields/{LAYER}"]
            raw = ds[()].astype(np.float32)
            fill = float(np.ravel(ds.attrs.get("_FillValue", [65535]))[0])
            scale = float(np.ravel(ds.attrs.get("scale_factor", [1.0]))[0])
            offset = float(np.ravel(ds.attrs.get("add_offset", [0.0]))[0])
        rad = np.where(raw == fill, np.nan, raw * scale + offset).astype(np.float32)
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
