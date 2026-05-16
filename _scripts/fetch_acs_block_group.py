"""Pull 13 ACS 5-year tables at BLOCK-GROUP level for all states.

Per-state loop (block-group queries require state AND county wildcards).
Output: D:/Gun Violence/demographics/acs_5yr_bg/acs5_2023_<TABLE>_bg.parquet

Block-group is the finest geography ACS publishes 5-year estimates at.
N is ~220K block groups vs 84K tracts vs 3.2K counties — addresses the
identifiability tension in v0.4's variance-decomp cross-term (-15).
"""
import os, time, sys, pathlib, requests
import pandas as pd

KEY = os.environ.get("CENSUS_API_KEY")
if not KEY:
    sys.exit("CENSUS_API_KEY env var not set")

VINTAGE = "2023"
# Same 13 tables as the tract/county pull
TABLES = ["B01001","B02001","B03003","B17001","B19013","B19301",
          "B25003","B25070","B25077","B15003","B23025","B11001","B11003"]

STATE_FIPS = ["01","02","04","05","06","08","09","10","11","12","13","15","16","17",
              "18","19","20","21","22","23","24","25","26","27","28","29","30","31",
              "32","33","34","35","36","37","38","39","40","41","42","44","45","46",
              "47","48","49","50","51","53","54","55","56","72"]

OUT = pathlib.Path(r"D:/Gun Violence/demographics/acs_5yr_bg")
OUT.mkdir(parents=True, exist_ok=True)

BASE = f"https://api.census.gov/data/{VINTAGE}/acs/acs5"

def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        except Exception as e:
            print(f"  err: {e}", file=sys.stderr)
        time.sleep(2 ** attempt)
    return None

def pull_table_bg(table):
    target = OUT / f"acs5_{VINTAGE}_{table}_bg.parquet"
    if target.exists():
        print(f"  SKIP (exists): {target.name}")
        return "skip"
    parts = []
    for st in STATE_FIPS:
        url = (f"{BASE}?get=NAME,group({table})"
               f"&for=block%20group:*&in=state:{st}%20county:*&key={KEY}")
        j = fetch(url)
        if not j:
            print(f"    state {st} FAILED", file=sys.stderr)
            continue
        parts.append(pd.DataFrame(j[1:], columns=j[0]))
        time.sleep(0.15)  # gentle throttle
        print(f"    state {st}: {len(parts[-1])} bg rows", flush=True)
    if not parts:
        return "fail"
    df = pd.concat(parts, ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df.to_parquet(target, index=False)
    print(f"  WROTE {target.name}: {len(df)} rows (across {len(parts)} states)")
    return "ok"

for table in TABLES:
    print(f"\n=== {table} (block group) ===")
    t0 = time.time()
    status = pull_table_bg(table)
    print(f"  {status} ({time.time()-t0:.1f}s)")
