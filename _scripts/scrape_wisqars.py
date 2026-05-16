"""Scrape WISQARS firearm deaths county-level 2019-2023 via /api/fatal-county.

Matches §4 of pre-reg: firearm homicide + suicide + accident + undetermined,
all ages/sex/race, county granularity, 2019-2023 window.
"""
import requests, json, pathlib, time, sys
import pandas as pd

OUT = pathlib.Path(r"D:/Gun Violence/outcomes/wisqars/scrape_2019_2023")
OUT.mkdir(parents=True, exist_ok=True)

API = "https://wisqars.cdc.gov/api/fatal-county"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://wisqars.cdc.gov",
    "Referer": "https://wisqars.cdc.gov/explore/fatal",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
}

# Intent codes (best guess from API param naming; will need to refine if 0=all isn't enough)
# 0 = All Intents; specific codes for homicide / suicide / unintentional / undetermined to be confirmed via /api/fatal-intents
INTENTS = {
    "ALL": "0",
    # We'll fall back to ALL and break down via separate intent queries if needed
}

def query_all_years_national_county(intent="0"):
    """Single query: all years 2019-2023, all intents, firearm mech, national county breakdown."""
    payload = {
        "filterset": {
            "parameters": {
                "ethnicty": "0",
                "agebuttn": "ALL",
                "fiveyr1": "0", "fiveyr2": "199",
                "c_age1": "0", "c_age2": "199",
                "intent": intent,
                "mech": "20890",          # firearm
                "race": "0",
                "sex": "1,2,3",            # all
                "race_yr": "2",
                "state": "00",             # national
                "tbi": "0",
                "urbrul": "0",
                "year1": "2019", "year2": "2023",
                "groupby1": "AGEGP",
                "ypllage": "65",
            }
        },
        "mapParams": {
            "color": "yellowbrown", "detail": "county", "interval": "5",
            "region": "mapRegionOption", "render": "actual", "showas": "actual"
        }
    }
    r = requests.post(API, headers=HEADERS, data=json.dumps(payload), timeout=60)
    print(f"  status: {r.status_code} | bytes: {len(r.content):,}")
    return r

# Per-year national queries (in case the 2019-2023 range is sliced server-side)
print("=== WISQARS scrape: firearm deaths by county, 2019-2023 ===")

# Try the all-years-combined query first
print("\n[1] Single query, year1=2019 year2=2023, intent=0 (all), mech=20810 (firearm)...")
r = query_all_years_national_county(intent="0")
if r.status_code != 200:
    print(f"FAIL: {r.text[:500]}")
    sys.exit(1)

data = r.json()
(OUT / "fatal_county_2019_2023_all_intents.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"  saved JSON ({len(json.dumps(data)):,} bytes)")
print(f"  top-level keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

# Try to parse into DataFrame
def to_df(d):
    """Attempt various JSON-to-DF conversions."""
    if isinstance(d, list):
        return pd.DataFrame(d)
    if isinstance(d, dict):
        for k in ["data","rows","result","results","items","records","table"]:
            if k in d and isinstance(d[k], list):
                return pd.DataFrame(d[k])
        # fallback: convert first list-valued key
        for k, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return pd.DataFrame(v)
    return None

df = to_df(data)
if df is not None and len(df):
    df.to_parquet(OUT / "fatal_county_2019_2023_all_intents.parquet", index=False)
    print(f"  PARSED: {len(df):,} rows × {len(df.columns)} cols")
    print(f"  cols: {list(df.columns)[:15]}")
    print(f"  head:\n{df.head(3)}")
else:
    print(f"  could not auto-parse JSON to DF. Raw keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")

# Per-year breakdown for robustness
print("\n[2] Per-year queries for finer granularity...")
per_year = []
for yr in ["2019","2020","2021","2022","2023"]:
    print(f"  year {yr}...")
    payload = {
        "filterset": {
            "parameters": {
                "ethnicty": "0", "agebuttn": "ALL",
                "fiveyr1": "0", "fiveyr2": "199",
                "c_age1": "0", "c_age2": "199",
                "intent": "0", "mech": "20890", "race": "0", "sex": "1,2,3",
                "race_yr": "2", "state": "00", "tbi": "0", "urbrul": "0",
                "year1": yr, "year2": yr,
                "groupby1": "AGEGP", "ypllage": "65",
            }
        },
        "mapParams": {"color": "yellowbrown", "detail": "county", "interval": "5",
                      "region": "mapRegionOption", "render": "actual", "showas": "actual"}
    }
    r = requests.post(API, headers=HEADERS, data=json.dumps(payload), timeout=60)
    if r.status_code == 200:
        d = r.json()
        (OUT / f"fatal_county_{yr}.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
        df_y = to_df(d)
        if df_y is not None and len(df_y):
            df_y["year"] = yr
            per_year.append(df_y)
            print(f"    {len(df_y):,} rows")
        else:
            print(f"    no DF parsed")
    else:
        print(f"    FAIL {r.status_code}: {r.text[:200]}")
    time.sleep(1)

if per_year:
    combined = pd.concat(per_year, ignore_index=True)
    combined.to_parquet(OUT / "fatal_county_per_year_2019_2023.parquet", index=False)
    print(f"\nWROTE {OUT/'fatal_county_per_year_2019_2023.parquet'}: {len(combined):,} rows")

# Intent breakdown (homicide=1, suicide=2, unintentional=3, undetermined=5)
# Trying common WISQARS intent codes
print("\n[3] Per-intent queries (firearm, 2019-2023, all years)...")
intent_codes = {"homicide": "1", "suicide": "2", "unintentional": "3", "undetermined": "5"}
per_intent = {}
for label, code in intent_codes.items():
    payload = {
        "filterset": {
            "parameters": {
                "ethnicty": "0", "agebuttn": "ALL",
                "fiveyr1": "0", "fiveyr2": "199",
                "c_age1": "0", "c_age2": "199",
                "intent": code, "mech": "20890", "race": "0", "sex": "1,2,3",
                "race_yr": "2", "state": "00", "tbi": "0", "urbrul": "0",
                "year1": "2019", "year2": "2023",
                "groupby1": "AGEGP", "ypllage": "65",
            }
        },
        "mapParams": {"color": "yellowbrown", "detail": "county", "interval": "5",
                      "region": "mapRegionOption", "render": "actual", "showas": "actual"}
    }
    r = requests.post(API, headers=HEADERS, data=json.dumps(payload), timeout=60)
    if r.status_code == 200:
        d = r.json()
        (OUT / f"fatal_county_{label}.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
        df_i = to_df(d)
        if df_i is not None and len(df_i):
            df_i["intent_label"] = label
            per_intent[label] = df_i
            print(f"  {label} (code={code}): {len(df_i):,} rows")
        else:
            print(f"  {label}: no DF parsed")
    else:
        print(f"  {label} FAIL {r.status_code}: {r.text[:200]}")
    time.sleep(1)

if per_intent:
    combined_intents = pd.concat(per_intent.values(), ignore_index=True)
    combined_intents.to_parquet(OUT / "fatal_county_per_intent_2019_2023.parquet", index=False)
    print(f"\nWROTE {OUT/'fatal_county_per_intent_2019_2023.parquet'}: {len(combined_intents):,} rows across {len(per_intent)} intents")

print("\nDONE")
