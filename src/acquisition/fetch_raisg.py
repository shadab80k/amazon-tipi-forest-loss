"""
Fetch the Amazon biome boundary (RAISG/OTCA 2024 'LimBiogeografico' layer)
as GeoJSON (EPSG:4326).

Output: data/raw/amazon_biome_raisg.json
"""
import json
import os
import sys

import requests

BASE = ("https://services5.arcgis.com/ys9ZOA2LzLraNRFP/arcgis/rest/services/"
        "LimBiogeografico/FeatureServer/0/query")
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw")


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    out_path = os.path.join(RAW, "amazon_biome_raisg.json")
    if os.path.exists(out_path):
        print("[skip] exists")
        return 0
    r = requests.get(BASE, params=dict(where="1=1", outFields="*", outSR="4326",
                                       f="geojson"), timeout=180)
    j = r.json()
    feats = j.get("features", [])
    fc = {"type": "FeatureCollection", "features": feats}
    with open(out_path, "w") as f:
        json.dump(fc, f)
    print(f"saved {len(fc['features'])} biome polygons -> {out_path}")
    return 0 if fc["features"] else 1


if __name__ == "__main__":
    sys.exit(main())
