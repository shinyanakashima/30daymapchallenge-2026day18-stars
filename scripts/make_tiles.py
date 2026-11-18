"""Scatter stars by sky class and write XYZ tiles (site/tiles/{z}/{x}/{y}.png).

Every star gets a fixed position, brightness and a random rank u (seeded,
so the sky is the same every run). At zoom z only stars with
u < ZOOM_FRACTION ** (10 - z) are drawn, and a star's size tier comes from
its rank among the stars drawn at that zoom.
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
M = 6  # margin so stars on tile edges continue into the next tile
ZOOM_FRACTION = 0.43
KM_PER_PX_LAT = 111.32 / C.PX_PER_DEG

# (upper bound of local rank, sigma px, peak) - brighter tiers are rarer
TIERS = [(0.012, 1.25, 255.0), (0.07, 0.85, 225.0), (0.28, 0.6, 165.0), (1.0, 0.0, 120.0)]


def sprite(sigma):
    if sigma == 0:
        return np.array([[0]]), np.array([[0]]), np.array([[1.0]])
    r = int(math.ceil(sigma * 2.6))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    w = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    keep = w > 0.03
    return yy[keep], xx[keep], w[keep]


SPRITES = [sprite(s) for _, s, _ in TIERS]


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
    return lon, lat, u, bright


def merc(lon, lat, z):
    s = T * 2 ** z
    x = (lon + 180.0) / 360.0 * s
    lr = np.radians(lat)
    y = (1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / math.pi) / 2 * s
    return x, y


def png(arr):
    b = io.BytesIO()
    Image.fromarray(arr, "L").save(b, "PNG", optimize=True)
    return b.getvalue()


def main():
    lon, lat, u, bright = make_stars()
    print(f"{lon.size:,} stars")
    if OUT.exists():
        shutil.rmtree(OUT)
    black = png(np.zeros((T, T), np.uint8))
    b = C.BBOX
    summary = {}
    for z in C.TILE_ZOOMS:
        frac = ZOOM_FRACTION ** (10 - z)
        sel = u < frac
        x, y = merc(lon[sel], lat[sel], z)
        v = u[sel] / frac
        br = bright[sel]
        tier = np.searchsorted([t[0] for t in TIERS], v, side="right")
        tier = np.minimum(tier, len(TIERS) - 1)
        x0, y0 = merc(np.array([b["west"]]), np.array([b["north"]]), z)
        x1, y1 = merc(np.array([b["east"]]), np.array([b["south"]]), z)
        tx0, tx1 = int(x0[0] // T), int(x1[0] // T)
        ty0, ty1 = int(y0[0] // T), int(y1[0] // T)
        order = np.argsort(y)
        x, y, br, tier = x[order], y[order], br[order], tier[order]
        ntiles = nstar = 0
        width = (tx1 - tx0 + 1) * T + 2 * M
        for ty in range(ty0, ty1 + 1):
            a = np.searchsorted(y, ty * T - M)
            e = np.searchsorted(y, (ty + 1) * T + M)
            canvas = np.zeros((T + 2 * M, width), np.float32)
            xi = np.floor(x[a:e] - (tx0 * T - M)).astype(np.int64)
            yi = np.floor(y[a:e] - (ty * T - M)).astype(np.int64)
            for k, (_, _, peak) in enumerate(TIERS):
                m = tier[a:e] == k
                if not m.any():
                    continue
                dy, dx, wt = SPRITES[k]
                for oy, ox, ww in zip(dy.ravel(), dx.ravel(), wt.ravel()):
                    yy, xx = yi[m] + oy, xi[m] + ox
                    ok = (yy >= 0) & (yy < canvas.shape[0]) & (xx >= 0) & (xx < width)
                    np.add.at(canvas, (yy[ok], xx[ok]), (peak * ww) * br[a:e][m][ok])
            img = (255 * (1 - np.exp(-canvas / 210.0))).astype(np.uint8)
            for tx in range(tx0, tx1 + 1):
                c0 = (tx - tx0) * T + M
                t = img[M:M + T, c0:c0 + T]
                p = OUT / str(z) / str(tx)
                p.mkdir(parents=True, exist_ok=True)
                (p / f"{ty}.png").write_bytes(png(t) if t.any() else black)
                ntiles += 1
            nstar += e - a
        summary[z] = dict(tiles=ntiles, stars=int(sel.sum()))
        print(z, summary[z])
    (OUT / "summary.json").write_text(json.dumps(summary))


if __name__ == "__main__":
    main()
