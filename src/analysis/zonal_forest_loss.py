"""
Zonal forest-loss analysis for Indigenous Lands (TIs) using the Hansen/UMD
Global Forest Change dataset (GFC-2023-v1.11; loss years 2000-2023).

ENGINEERING NOTE: GFC tiles are striped GeoTIFFs with full-width rows
(1 x 40000 px blocks), so any windowed read fetches whole rows. We therefore
stream each required tile in row-blocks (BLOCK_ROWS x 40000 px) and process
every candidate TI intersecting each block. Only the row ranges actually
spanned by candidate TIs (+ margin) are fetched, via /vsicurl/.

STUDY DESIGN
  Treatment: TIs with presence of isolated peoples (TIPI), n=81.
  Controls:  for each TIPI, up to 2 other TIs in the same state (UF) with the
             closest log-area (1:2 matched controls), drawn from official
             FUNAI polygons. Matching is 1:2 greedy without replacement.

ZONES per TI: inside; ring 0-10 km; ring 10-50 km (buffers in EPSG:6933,
simplified at sub-pixel tolerance only for rasterization).

RESPONSE: pixels with treecover2000 > 30% and lossyear in 1..23 (GFC v1.11),
aggregated per zone. Primary metric = loss share of year-2000 tree cover.

Outputs:
  results/zonal_results.csv
  results/tile_log.csv
  results/_zonal_progress.json   (crash-safe resume)
"""
import json
import math
import os
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds as tf_from_bounds
from shapely.geometry import box as shapely_box

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "results")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(RES, exist_ok=True)

GFC_BASE = ("https://storage.googleapis.com/earthenginepartners-hansen/"
            "GFC-2023-v1.11/Hansen_GFC-2023-v1.11_{band}_{tile}.tif")
PIX = 0.00025
TC_THRESHOLD = 30
MARGIN_DEG = 0.5
RING1_M = 10_000
RING2_M = 50_000
BLOCK_ROWS = 1500          # 1500 x 40000 px = 60 MB per band per block
N_CTRL_PER_TIPI = 2
EQ = "EPSG:6933"


def lon_tile_label(lon: float) -> str:
    left = math.floor(lon / 10.0) * 10
    return f"{abs(left):03d}{'W' if left < 0 else 'E'}"


def lat_tile_label(lat: float) -> str:
    if lat >= 0:
        top = math.ceil(lat / 10.0) * 10
        return "00N" if top == 0 else f"{top:02d}N"
    top = -math.floor(-lat / 10.0) * 10
    return "00N" if top == 0 else f"{abs(top):02d}S"


def tiles_for_bbox(w, s, e, n):
    tiles = set()
    for lat in np.arange(math.floor(s / 10) * 10, math.ceil(n / 10) * 10 + 1, 10):
        for lon in np.arange(math.floor(w / 10) * 10, math.ceil(e / 10) * 10 + 1, 10):
            tiles.add((lat_tile_label(float(lat)), lon_tile_label(float(lon))))
    return sorted(tiles)


def tile_bounds(tile: str):
    latlab, lonlab = tile.split("_")
    if latlab.endswith("N"):
        top = int(latlab[:-1])
        bottom = top - 10
    else:
        top = -int(latlab[:-1])
        bottom = top - 10
    left = -int(lonlab[:-1]) if lonlab.endswith("W") else int(lonlab[:-1])
    return left, bottom, left + 10, top


def pixel_area_m2(lat_deg: float) -> float:
    dlat_m = PIX * 110_574.0
    dlon_m = PIX * 111_320.0 * math.cos(math.radians(lat_deg))
    return dlat_m * dlon_m


def zone_counts(tc, ly, zone_geos, transform):
    """Core counting unit: per-zone tree-cover and loss pixel counts.

    zone_geos: (inside, ring1, ring2) geometries in the raster CRS.
    Returns [(tree_px, loss_by_year_24)] per zone.
    """
    zmask = rasterize(
        [(zone_geos[0], 1), (zone_geos[1], 2), (zone_geos[2], 3)],
        out_shape=tc.shape, transform=transform,
        fill=0, dtype="uint8", all_touched=False)
    tc_mask = tc > TC_THRESHOLD
    lm = (ly > 0) & tc_mask
    out = []
    for zcode in (1, 2, 3):
        zm = zmask == zcode
        tree = int((tc_mask & zm).sum())
        loss = np.zeros(24, dtype=np.int64)
        yrs, cnts = np.unique(ly[lm & zm], return_counts=True)
        for y, c in zip(yrs, cnts):
            loss[int(y)] = int(c)
        out.append((tree, loss))
    return out


def build_candidates(tis):
    """TIPI (all) + matched controls (1:2 same-UF, nearest log-area)."""
    tipi = tis[tis.has_isolated].copy()
    others = tis[~tis.has_isolated].copy()
    tipi["log_area"] = np.log(tipi["area_ha_geom"].clip(lower=1))
    others["log_area"] = np.log(others["area_ha_geom"].clip(lower=1))
    used = set()
    ctrl_rows = []
    for _, r in tipi.iterrows():
        pool = others[(others["uf"] == r["uf"]) & (~others.index.isin(used))]
        if len(pool) == 0:
            pool = others[~others.index.isin(used)]
        if len(pool) == 0:
            continue
        pool = pool.assign(d=(pool["log_area"] - r["log_area"]).abs())
        picks = pool.sort_values("d").head(N_CTRL_PER_TIPI)
        used.update(picks.index)
        ctrl_rows.append(picks)
    ctrls = pd.concat(ctrl_rows) if ctrl_rows else others.iloc[0:0]
    cand = pd.concat([tipi, ctrls], ignore_index=False).copy()
    cand["is_control"] = ~cand["has_isolated"]
    print(f"candidates: TIPI={int((~cand.is_control).sum())}, controls={int(cand.is_control.sum())}")
    return cand


def main() -> int:
    t0 = time.time()
    tis = gpd.read_file(os.path.join(PROC, "tis_all.gpkg")).to_crs("EPSG:4326")
    tis["geometry"] = tis.geometry.buffer(0)
    print(f"TIs loaded: {len(tis)} (isolated: {int(tis.has_isolated.sum())})", flush=True)

    tipi = tis[tis.has_isolated]
    minx, miny, maxx, maxy = tipi.total_bounds
    w, s, e, n = minx - MARGIN_DEG, miny - MARGIN_DEG, maxx + MARGIN_DEG, maxy + MARGIN_DEG
    tiles = tiles_for_bbox(w, s, e, n)
    print(f"extent ({w:.2f},{s:.2f})-({e:.2f},{n:.2f}); tiles: {tiles}", flush=True)

    cand = build_candidates(tis)

    # keep only candidates overlapping the analysis extent
    ext = gpd.GeoDataFrame(geometry=[shapely_box(w, s, e, n)], crs="EPSG:4326")
    cand = cand[cand.geometry.intersects(ext.geometry.iloc[0])].copy()

    # zone geometries (buffers in EPSG:6933; simplified for rasterization only)
    print("precomputing zones ...", flush=True)
    cand_p = cand.to_crs(EQ)
    zones, zone_area_ha = {}, {}
    for i, row in cand_p.iterrows():
        g = row.geometry
        b1, b2 = g.buffer(RING1_M), g.buffer(RING2_M)
        r1, r2 = b1.difference(g), b2.difference(b1)
        zone_area_ha[i] = [g.area / 1e4, r1.area / 1e4, r2.area / 1e4]
        zs = gpd.GeoSeries([g, r1, r2], crs=EQ).to_crs("EPSG:4326")
        zones[i] = zs.simplify(0.0005, preserve_topology=True)
    print("zones ready", flush=True)

    cand["bbox"] = [g.bounds for g in cand.geometry]
    idx_order = list(cand.index)
    pos_of = {gi: k for k, gi in enumerate(idx_order)}
    n_ti = len(idx_order)
    tree_px = np.zeros((n_ti, 3), dtype=np.int64)
    loss_px = np.zeros((n_ti, 3, 24), dtype=np.int64)
    tile_hits = {gi: [] for gi in idx_order}

    progress_path = os.path.join(RES, "_zonal_progress.json")
    done = set()
    if os.path.exists(progress_path):
        done = set(json.load(open(progress_path)).get("done", []))
        print(f"resume; done tiles: {sorted(done)}", flush=True)

    tile_log = []
    for latlab, lonlab in tiles:
        tile = f"{latlab}_{lonlab}"
        if tile in done:
            continue
        left, bottom, right, top = tile_bounds(tile)
        # candidates overlapping this tile (with margin)
        overlap = []
        for gi in idx_order:
            b = cand.loc[gi, "bbox"]
            if (b[0] - MARGIN_DEG < right and b[2] + MARGIN_DEG > left and
                    b[1] - MARGIN_DEG < top and b[3] + MARGIN_DEG > bottom):
                overlap.append(gi)
        if not overlap:
            tile_log.append({"tile": tile, "n_ti": 0, "status": "skipped"})
            done.add(tile)
            json.dump({"done": sorted(done)}, open(progress_path, "w"))
            continue

        print(f"\n=== TILE {tile} ({left},{bottom})-({right},{top}) "
              f"TIs: {len(overlap)} ===", flush=True)

        # row union needed by the overlapping candidates
        row_ranges = []
        for gi in overlap:
            b = cand.loc[gi, "bbox"]
            wt = min(b[3] + MARGIN_DEG, top)
            wb = max(b[1] - MARGIN_DEG, bottom)
            r_top = int(math.floor((top - wt) / PIX))
            r_bot = int(math.ceil((top - wb) / PIX))
            row_ranges.append((max(0, r_top), min(40000, r_bot)))
        rows_needed = (min(r[0] for r in row_ranges), max(r[1] for r in row_ranges))
        est_mb = (rows_needed[1] - rows_needed[0]) * 40 * 2 / 1000
        print(f"  rows needed: {rows_needed} (~{est_mb:.0f} MB to fetch)", flush=True)

        try:
            with rasterio.open(GFC_BASE.format(band="treecover2000", tile=tile)) as tsrc, \
                 rasterio.open(GFC_BASE.format(band="lossyear", tile=tile)) as lsrc:
                r0, r1_ = rows_needed
                for br0 in range(r0, r1_, BLOCK_ROWS):
                    br1 = min(br0 + BLOCK_ROWS, r1_)
                    ht = br1 - br0
                    t_block = tsrc.read(1, window=rasterio.windows.Window(0, br0, 40000, ht))
                    l_block = lsrc.read(1, window=rasterio.windows.Window(0, br0, 40000, ht))
                    blk_top = top - br0 * PIX
                    blk_bottom = blk_top - ht * PIX
                    for gi in overlap:
                        b = cand.loc[gi, "bbox"]
                        wt = min(b[3] + MARGIN_DEG, top)
                        wb = max(b[1] - MARGIN_DEG, bottom)
                        wtr = int(math.floor((top - wt) / PIX))
                        wbr = int(math.ceil((top - wb) / PIX))
                        if wtr >= br1 or wbr <= br0:
                            continue
                        # column window (limits rasterize cost; zones bound the rest)
                        wl = max(b[0] - MARGIN_DEG, left)
                        wr = min(b[2] + MARGIN_DEG, right)
                        c0 = max(0, int(math.floor((wl - left) / PIX)))
                        c1 = min(40000, int(math.ceil((wr - left) / PIX)))
                        if c1 <= c0:
                            continue
                        rows_in_blk = range(max(wtr, br0), min(wbr, br1))
                        rb0 = max(wtr, br0) - br0
                        rb1 = min(wbr, br1) - br0
                        tc = t_block[rb0:rb1, c0:c1]
                        ly = l_block[rb0:rb1, c0:c1]
                        tr = rasterio.windows.Window(
                            col_off=c0, row_off=br0 + rb0, width=c1 - c0, height=rb1 - rb0)
                        # NOTE: blk_top is the block's local top edge; the sub-window
                        # north/south must be offset by rb0/rb1 rows WITHIN the block
                        # (not by br0 + rb0 -- br0 is already accounted for in blk_top).
                        transform = rasterio.transform.from_bounds(
                            left + c0 * PIX, blk_top - rb1 * PIX,
                            left + c1 * PIX, blk_top - rb0 * PIX,
                            width=c1 - c0, height=rb1 - rb0)
                        zs = zones[gi]
                        counts = zone_counts(tc, ly, zs, transform)
                        k = pos_of[gi]
                        for zn in range(3):
                            tree_px[k, zn] += counts[zn][0]
                            loss_px[k, zn, :] += counts[zn][1]
                        tile_hits[gi].append(tile)
                    print(f"    block rows {br0}-{br1} done ({time.time()-t0:.0f}s)", flush=True)
        except Exception as ex:
            print(f"  ERROR tile {tile}: {ex}", flush=True)
            tile_log.append({"tile": tile, "n_ti": len(overlap), "status": f"error: {ex}"})
            continue
        tile_log.append({"tile": tile, "n_ti": len(overlap), "status": "ok"})
        done.add(tile)
        json.dump({"done": sorted(done)}, open(progress_path, "w"))
        print(f"  TILE {tile} DONE ({time.time()-t0:.0f}s)", flush=True)

    # ---------------- assemble ----------------
    print("\nassembling results ...", flush=True)
    rows = []
    for k, gi in enumerate(idx_order):
        r = cand.loc[gi]
        for z, zname in enumerate(["inside", "ring0_10km", "ring10_50km"]):
            tp = int(tree_px[k, z])
            lp = int(loss_px[k, z, 1:].sum())
            rows.append({
                "ti_name": r["ti_name"], "has_isolated": bool(r["has_isolated"]),
                "is_control": bool(r["is_control"]), "uf": r.get("uf"),
                "fase": r.get("fase"), "area_ha_official": r.get("area_ha_official"),
                "area_ha_geom": r.get("area_ha_geom"),
                "zone": zname, "tree2000_px": tp, "loss_px_2000_2023": lp,
                "loss_share_tree2000": (lp / tp) if tp > 0 else np.nan,
                **{f"loss_px_y{2000 + y}": int(loss_px[k, z, y]) for y in range(1, 24)},
                "tiles_used": ",".join(sorted(set(tile_hits[gi]))),
            })
    df = pd.DataFrame(rows)
    za = {}
    for gi in idx_order:
        tn = cand.loc[gi, "ti_name"]
        for z, zn in enumerate(["inside", "ring0_10km", "ring10_50km"]):
            za[(tn, zn)] = zone_area_ha[gi][z]
    df["zone_area_ha"] = [za[(r.ti_name, r.zone)] for r in df.itertuples()]
    latc = cand.geometry.centroid.y
    df["approx_px_area_m2"] = df["ti_name"].map(
        {cand.loc[gi, "ti_name"]: pixel_area_m2(latc[gi]) for gi in idx_order})
    df["tree2000_ha_approx"] = df["tree2000_px"] * df["approx_px_area_m2"] / 1e4
    df["loss_ha_approx"] = df["loss_px_2000_2023"] * df["approx_px_area_m2"] / 1e4
    df.to_csv(os.path.join(RES, "zonal_results.csv"), index=False)
    pd.DataFrame(tile_log).to_csv(os.path.join(RES, "tile_log.csv"), index=False)
    print(f"DONE in {time.time()-t0:.0f}s -> results/zonal_results.csv", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
