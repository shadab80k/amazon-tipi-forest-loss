"""Smoke tests: pure functions + a synthetic end-to-end zonal computation."""
import numpy as np
import pytest

from zonal_forest_loss import (lat_tile_label, lon_tile_label, pixel_area_m2,
                               tile_bounds, tiles_for_bbox)
from stats_tests import cohen_dz, gini, rank_biserial_wilcoxon


# ---------- tile naming ----------
def test_lon_tile_label():
    assert lon_tile_label(-65) == "070W"
    assert lon_tile_label(-50) == "050W"
    assert lon_tile_label(10) == "010E"


def test_lat_tile_label():
    assert lat_tile_label(-7.5) == "00N"
    assert lat_tile_label(-15) == "10S"
    assert lat_tile_label(4.8) == "10N"
    assert lat_tile_label(-25.1) == "20S"


def test_tile_bounds_roundtrip():
    b = tile_bounds("00N_070W")
    assert b == (-70, -10, -60, 0)
    b2 = tile_bounds("10S_050W")
    assert b2 == (-50, -20, -40, -10)
    b3 = tile_bounds("10N_040W")
    assert b3 == (-40, 0, -30, 10)


def test_tiles_for_bbox_covers_aoi():
    tiles = tiles_for_bbox(-66, -8, -64, -6)
    assert ("00N", "070W") in tiles or ("10S", "070W") in tiles


def test_pixel_area_m2():
    a_eq = pixel_area_m2(0.0)
    a_s15 = pixel_area_m2(-15.0)
    assert 740 < a_eq < 800                 # ~769 m^2 (0.00025 x 110574 x 0.00025 x 111320)
    assert a_s15 < a_eq                     # shrinks with |latitude|


# ---------- statistics helpers ----------
def test_gini():
    assert gini([1, 1, 1, 1]) == pytest.approx(0.0, abs=1e-9)
    assert gini([0, 0, 0, 10]) == pytest.approx(0.75, abs=1e-6)


def test_rank_biserial_and_dz():
    x = np.array([0.10, 0.20, 0.30, 0.40])
    y = np.array([0.05, 0.10, 0.25, 0.20])
    r = rank_biserial_wilcoxon(x, y)
    assert 0.5 < r <= 1.0
    d = cohen_dz(x, y)
    assert d > 0


# ---------- synthetic end-to-end zone counting ----------
def test_synthetic_zonal_counts():
    """Raster a synthetic 4x4-km polygon with known loss; verify zone counts."""
    import geopandas as gpd
    from shapely.geometry import box as shp_box
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds

    # grid: 0.001-deg pixels over 0.04 x 0.04 deg at the equator
    res = 0.001
    left, bottom, right, top = -50.0, 0.0, -49.96, 0.04
    W, H = 40, 40
    transform = from_bounds(left, bottom, right, top, W, H)

    tc = np.full((H, W), 80, dtype="uint8")          # all treecover 80%
    ly = np.zeros((H, W), dtype="uint8")
    ly[15:20, 15:20] = 13                             # 25 px lost in 2013 (inside)
    ly[0:3, 0:40] = 7                                 # 120 px lost in 2007 (outside)

    inside = shp_box(left + 0.01, bottom + 0.01, left + 0.03, bottom + 0.03)  # 20x20 px
    zm = rasterize([(inside, 1)], out_shape=(H, W), transform=transform, fill=0)
    tree_in = int(((tc > 30) & (zm == 1)).sum())
    loss_in = int((((ly > 0) & (tc > 30)) & (zm == 1)).sum())
    assert tree_in == 400
    assert loss_in == 25
    share = loss_in / tree_in
    assert share == pytest.approx(25 / 400)


def test_block_streaming_transform_regression():
    """Regression test: a polygon spanning two row-blocks must be counted
    exactly once per block with the correct georeferencing. This test would
    have caught the double block-offset transform bug (br0 subtracted twice)
    that silently corrupted early production runs.
    """
    import geopandas as gpd
    from shapely.geometry import box as shp_box
    from zonal_forest_loss import PIX, TC_THRESHOLD, zone_counts
    from rasterio.transform import from_bounds

    # synthetic "tile": 100 rows x 200 cols, res 0.01 deg, spans lat 1.0..0.0
    PIXT = 0.01
    left, right, top = -50.0, -48.0, 1.0
    H, W = 100, 200
    full_tc = np.full((H, W), 80, dtype="uint8")
    full_ly = np.zeros((H, W), dtype="uint8")
    full_ly[40:60, 80:120] = 9          # 400 loss px in 2009, rows 40-60

    poly = shp_box(-49.2, 0.2, -48.8, 0.8)   # spans rows 20-80, cols 80-120
    zones = [poly, poly.buffer(0).difference(poly), shp_box(-50, 0, -48, 1).difference(poly.buffer(0))]

    # two blocks: rows 0-49 and 50-100
    acc = [(0, np.zeros(24)) for _ in range(3)]
    for br0, br1 in [(0, 50), (50, 100)]:
        tc_blk = full_tc[br0:br1]
        ly_blk = full_ly[br0:br1]
        rb0 = max(20, br0) - br0
        rb1 = min(80, br1) - br0
        c0, c1 = 80, 120
        tc = tc_blk[rb0:rb1, c0:c1]
        ly = ly_blk[rb0:rb1, c0:c1]
        blk_top = top - br0 * PIXT
        # production transform: block-local offsets only
        tr = from_bounds(left + c0 * PIXT, blk_top - rb1 * PIXT,
                         left + c1 * PIXT, blk_top - rb0 * PIXT,
                         width=c1 - c0, height=rb1 - rb0)
        counts = zone_counts(tc, ly, zones, tr)
        for zn in range(3):
            acc[zn] = (acc[zn][0] + counts[zn][0], acc[zn][1] + counts[zn][1])

    tree_inside, loss_inside = acc[0]
    # polygon is 60 rows x 40 cols = 2400 px, all tree-covered
    assert tree_inside == 2400, f"expected 2400, got {tree_inside}"
    # loss rows 40-60 (20x40=800 px) all inside polygon, year 2009 (code 9)
    assert loss_inside[9] == 800, f"expected 800, got {loss_inside[9]}"
    assert loss_inside.sum() == 800


def test_holm_bonferroni():
    from stats_tests import holm_bonferroni
    p = [0.01, 0.04, 0.03, 0.005, 0.02]
    adj = holm_bonferroni(p)
    # smallest p (0.005) -> 5*0.005 = 0.025; then 4*0.01=0.04; 3*0.02=0.06;
    # 2*0.03=0.06; 1*0.04=0.04
    assert adj[3] == pytest.approx(0.025)
    assert adj[0] == pytest.approx(0.04)
    assert adj[2] == pytest.approx(0.06)
    assert adj[4] == pytest.approx(0.06)
    assert adj[1] == pytest.approx(0.06)  # monotone: >= earlier rank
