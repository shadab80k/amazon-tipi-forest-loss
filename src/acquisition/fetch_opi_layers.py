"""
Fetch isolated-peoples-relevant vector layers from the OPI (Observatorio para a
Protecao dos Povos Isolados e de Recente Contato) GeoServer via WFS 2.0.

Source: https://geoserver.povosisolados.org/geoserver/opi_observatory/ows
All outputs are saved to data/raw/ as GeoJSON (EPSG:4326).

Ethical note: te_amz_povos_isolados (point records of isolated peoples) is a
SENSITIVE layer. It is used here only to link records to Indigenous Land names
and is never published at point precision. No figure or table in the study
shows record-level coordinates.
"""
import json
import os
import sys
import time

import requests

BASE = "https://geoserver.povosisolados.org/geoserver/opi_observatory/ows"
RAW = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

LAYERS = {
    "opi_povos_isolados_area": "opi_observatory:te_amz_povos_isolados_area",
    "opi_povos_isolados_records": "opi_observatory:te_amz_povos_isolados",
    "opi_ti_dutovias": "opi_observatory:te_amz_dutovias",
    "opi_ti_ferrovias": "opi_observatory:te_amz_ferrovias",
    "opi_cidades": "opi_observatory:te_amz_cidade",
    "opi_ucs": "opi_observatory:te_amz_ucs",
}


def get_layer_count(type_name: str) -> int:
    r = requests.get(
        BASE,
        params={
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": type_name,
            "resultType": "hits",
            "outputFormat": "application/json",
        },
        timeout=60,
    )
    txt = r.text
    import re

    m = re.search(r'numberMatched="(\d+)"', txt)
    return int(m.group(1)) if m else -1


def fetch_layer(type_name: str, out_name: str, max_feats: int = 50000) -> dict:
    out_path = os.path.join(RAW, out_name + ".geojson")
    if os.path.exists(out_path):
        print(f"  [skip] {out_name} already exists")
        return {"name": out_name, "path": out_path, "status": "cached"}

    n = get_layer_count(type_name)
    print(f"  {type_name}: ~{n} features")
    if n == 0:
        return {"name": out_name, "status": "empty"}

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": type_name,
        "outputFormat": "application/json",
        "srsName": "urn:ogc:def:crs:EPSG::4326",
        "count": str(max_feats),
        "startIndex": "0",
    }
    print(f"  downloading {type_name} ...", flush=True)
    t0 = time.time()
    r = requests.get(BASE, params=params, timeout=600, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    dt = time.time() - t0
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"  saved {out_name}: {size_mb:.1f} MB in {dt:.0f}s")
    # validate json
    try:
        with open(out_path) as f:
            j = json.load(f)
        nf = len(j.get("features", []))
        print(f"  valid geojson, {nf} features")
        return {"name": out_name, "path": out_path, "status": "ok", "n": nf}
    except Exception as e:
        print(f"  WARNING: json invalid: {e}")
        return {"name": out_name, "path": out_path, "status": "invalid", "error": str(e)}


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    results = []
    for name, tn in LAYERS.items():
        try:
            results.append(fetch_layer(tn, name))
        except Exception as e:
            print(f"  ERROR fetching {tn}: {e}")
            results.append({"name": name, "status": "error", "error": str(e)})
        time.sleep(1)
    summary_path = os.path.join(RAW, "_opi_fetch_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    ok = sum(1 for r in results if r.get("status") in ("ok", "cached"))
    print(f"\nDone: {ok}/{len(results)} layers fetched OK. Summary -> {summary_path}")
    return 0 if ok >= 4 else 1


if __name__ == "__main__":
    sys.exit(main())
