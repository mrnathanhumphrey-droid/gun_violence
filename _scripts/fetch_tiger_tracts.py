"""Pull TIGER 2024 tract shapefiles for all 50 states + DC + PR."""
import os, time, pathlib, requests, json

OUT = pathlib.Path(r"D:/Gun Violence/demographics/tract_boundaries/by_state")
OUT.mkdir(parents=True, exist_ok=True)

STATE_FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17",
              "18","19","20","21","22","23","24","25","26","27","28","29","30","31",
              "32","33","34","35","36","37","38","39","40","41","42","44","45","46",
              "47","48","49","50","51","53","54","55","56","72"]

BASE = "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_{}_tract.zip"

results = {}
for st in STATE_FIPS:
    url = BASE.format(st)
    target = OUT / f"tl_2024_{st}_tract.zip"
    if target.exists():
        results[st] = "skip"
        print(f"  SKIP {st}")
        continue
    try:
        r = requests.get(url, timeout=120, stream=True)
        if r.status_code == 200:
            with open(target, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            sz = target.stat().st_size
            results[st] = f"ok ({sz:,} bytes)"
            print(f"  {st}: {sz:,} bytes")
        else:
            results[st] = f"http {r.status_code}"
            print(f"  {st}: HTTP {r.status_code}")
    except Exception as e:
        results[st] = f"err {e}"
        print(f"  {st}: ERR {e}")
    time.sleep(0.3)

(pathlib.Path(r"D:/Gun Violence/provenance/tiger_tracts_results.json")).write_text(json.dumps(results, indent=2))
print(f"\nDONE: {sum(1 for v in results.values() if 'ok' in v)}/{len(STATE_FIPS)} states")
