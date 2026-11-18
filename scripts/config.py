"""Shared settings for the preprocessing scripts."""

YEAR = 2025
SEED = 18  # fixed random seed: the same sky every run

# Black Marble grid: 15 arc-second pixels, 10x10 degree tiles
PX_PER_DEG = 240
MOSAIC = dict(west=120.0, north=50.0, h0=30, v0=4, nh=3, nv=3)
# Output area (Japan)
BBOX = dict(west=122.5, south=24.0, east=149.0, north=46.0)

# Sky glow stand-in: Gaussian blur of the night-light radiance
BLUR_SIGMA_KM = 6.0
BLUR_RADIUS_KM = 15.0  # kernel is cut off at this radius

# Sky classes, darkest first. `max_rad` is the upper bound of the blurred
# radiance (nW/cm2/sr). `visible` is the rough number of naked-eye stars
# quoted for the matching Bortle classes. Stars drawn per km2 = visible / 1000.
CLASSES = [
    dict(id=1, max_rad=0.5, bortle="1-2", visible=4000, visible_range="3,000-5,000"),
    dict(id=2, max_rad=1.5, bortle="3", visible=2500, visible_range="2,000-3,000"),
    dict(id=3, max_rad=4.0, bortle="4", visible=1200, visible_range="1,000-1,500"),
    dict(id=4, max_rad=10.0, bortle="5", visible=500, visible_range="400-700"),
    dict(id=5, max_rad=30.0, bortle="6-7", visible=200, visible_range="100-300"),
    dict(id=6, max_rad=float("inf"), bortle="8-9", visible=30, visible_range="20-50"),
]
STARS_PER_KM2_PER_VISIBLE = 1 / 1000
# "Least light" highlight on the page: blurred radiance below this value
LEAST_LIGHT_RAD = 0.1

TILE_ZOOMS = range(3, 11)  # z3-z10
TILE_PX = 512  # served as 256 CSS px tiles (sharp on high-DPI screens)
