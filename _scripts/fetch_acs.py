"""Pull 13 ACS 5-year tables at tract + county for all states.

Output: D:/Gun Violence/demographics/acs_5yr/acs5_2023_<TABLE>_<geo>.parquet
"""
import os, time, json, sys, pathlib, requests
import pandas as pd

KEY = os.environ["CENSUS_API_KEY"]
VINTAGE = "2023"
TABLES = ["B01001","B02001","B03003","B17001","B19013","B19301",
          "B25003","B25070","B25077","B15003","B23025","B11001","B11003"]

# 50 states + DC + PR
STATE_FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17",
              "18","19","20","21","22","23","24","25","26","27","28","29","30","31",
              "32","33","34","35","36","37","38","39","40","41","42","44","45","46",
              "47","48","49","50","51","53","54","55","56","72"]

OUT = pathlib.Path(r"D:/Gun Violence/demographics/acs_5yr")
OUT.mkdir(parents=True, exist_ok=True)
PROV = pathlib.Path(r"D:/Gun Violence/provenance/acs")
PROV.mkdir(parents=True, exist_ok=True)

BASE = f"https://api.census.gov/data/{VINTAGE}/acs/acs5"

def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"  err: {e}", file=sys.stderr)
        time.sleep(2 ** attempt)
    return None

def pull_table_geo(table, geo):
    """geo in {'tract', 'county'}."""
    target = OUT / f"acs5_{VINTAGE}_{table}_{geo}.parquet"
    if target.exists():
        print(f"  SKIP (exists): {target.name}")
        return "skip"

    if geo == "county":
        url = f"{BASE}?get=NAME,group({table})&for=county:*&key={KEY}"
        j = fetch(url)
        if not j:
            return "fail"
        df = pd.DataFrame(j[1:], columns=j[0])
        df = df.loc[:, ~df.columns.duplicated()]
        df.to_parquet(target, index=False)
        print(f"  WROTE {target.name}: {len(df)} rows")
        return "ok"

    # tract: per-state loop
    parts = []
    for st in STATE_FIPS:
        url = f"{BASE}?get=NAME,group({table})&for=tract:*&in=state:{st}&key={KEY}"
        j = fetch(url)
        if not j:
            print(f"    state {st} FAILED", file=sys.stderr)
            continue
        parts.append(pd.DataFrame(j[1:], columns=j[0]))
        time.sleep(0.1)  # gentle throttle
    if not parts:
        return "fail"
    df = pd.concat(parts, ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df.to_parquet(target, index=False)
    print(f"  WROTE {target.name}: {len(df)} rows (across {len(parts)} states)")
    return "ok"

results = {}
for table in TABLES:
    for geo in ["county", "tract"]:
        key = f"{table}_{geo}"
        print(f"-> {key}")
        t0 = time.time()
        status = pull_table_geo(table, geo)
        results[key] = {"status": status, "elapsed_s": round(time.time()-t0, 1)}
        print(f"   [{status}] {round(time.time()-t0,1)}s")

(PROV / "acs_pull_results.json").write_text(json.dumps(results, indent=2))
print("\nDONE")
print(json.dumps(results, indent=2))
