"""
Fetch all 657 official FUNAI Indigenous Land polygons (Terras Indigenas do
Brasil -- Delimitacoes Oficiais FUNAI; Esri BR_Content FeatureServer mirror)
as GeoJSON (EPSG:4326).

Output: data/raw/funai_tis_raw.geojson
"""
import json
import os
import sys
import time

import requests

BASE = ("https://services5.arcgis.com/qF5YxIC9zJuMN2dV/arcgis/rest/services/"
        "terras_indigenas/FeatureServer/0/query")
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw")


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    out_path = os.path.join(RAW, "funai_tis_raw.geojson")
    if os.path.exists(out_path):
        print(f"[skip] {out_path} exists")
        return 0

    offs, feats = 0, []
    while True:
        p = dict(where="1=1", outFields="*", outSR="4326", f="geojson",
                 resultOffset=str(offs), resultRecordCount="1000")
        for attempt in range(5):
            try:
                r = requests.get(BASE, params=p, timeout=120)
                r.raise_for_status()
                j = r.json()
                break
            except Exception as e:
                print(f"  retry {attempt}: {e}")
                time.sleep(3 * (attempt + 1))
        else:
            print("FAILED after retries")
            return 1
        batch = j.get("features", [])
        feats.extend(batch)
        exc = j.get("exceededTransferLimit", False)
        print(f"offset {offs}: got {len(batch)} (total {len(feats)})")
        if not exc or not batch:
            break
        offs += len(batch)
        time.sleep(0.4)

    with open(out_path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": feats}, f)
    print(f"saved {len(feats)} TIs -> {out_path}")
    return 0 if len(feats) > 600 else 1


if __name__ == "__main__":
    sys.exit(main())
