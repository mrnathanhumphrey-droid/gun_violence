"""Pull TIGER 2024 UNSD (unified school district) shapefiles state-by-state."""
import os, time, pathlib, requests, json

OUT = pathlib.Path(r"D:/Gun Violence/geographic/school_district_boundaries/by_state")
OUT.mkdir(parents=True, exist_ok=True)

STATE_FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17",
              "18","19","20","21","22","23","24","25","26","27","28","29","30","31",
              "32","33","34","35","36","37","38","39","40","41","42","44","45","46",
              "47","48","49","50","51","53","54","55","56","72"]

BASE = "https://www2.census.gov/geo/tiger/TIGER2024/UNSD/tl_2024_{}_unsd.zip"

results = {}
for st in STATE_FIPS:
    url = BASE.format(st)
    target = OUT / f"tl_2024_{st}_unsd.zip"
    if target.exists() and target.stat().st_size > 50000:
        results[st] = "skip"
        continue
    try:
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code == 200:
            with open(target, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            results[st] = f"ok ({target.stat().st_size:,} bytes)"
            print(f"  {st}: {target.stat().st_size:,} bytes")
        else:
            results[st] = f"http {r.status_code}"
            target.unlink(missing_ok=True)
            print(f"  {st}: HTTP {r.status_code}")
    except Exception as e:
        results[st] = f"err {e}"
        print(f"  {st}: ERR {e}")
    time.sleep(0.2)

(pathlib.Path(r"D:/Gun Violence/provenance/tiger_unsd_results.json")).write_text(json.dumps(results, indent=2))
print(f"\nDONE: {sum(1 for v in results.values() if 'ok' in v or 'skip' in v)}/{len(STATE_FIPS)}")
