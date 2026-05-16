"""v0.5 Arm A self-replication: scrape WISQARS firearm deaths county-level 2014-2018.

Same API + same mech code (20890=firearm) + same intent codes as the 2019-2023 scrape,
just a different year window. Output to a separate dir so we don't clobber the v0.4 data.
"""
import os, json, time, pathlib, requests
import pandas as pd

OUT = pathlib.Path(r"D:/Gun Violence/outcomes/wisqars/scrape_2014_2018")
OUT.mkdir(parents=True, exist_ok=True)

API = "https://wisqars.cdc.gov/api/fatal-county"
HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Accept": "application/json"}

def to_df(resp):
    """WISQARS returns geojson-ish. Convert features → flat dataframe."""
    if not isinstance(resp, dict):
        return None
    feats = resp.get("rawdata", {}).get("features", [])
    if not feats:
        return None
    rows = []
    for f in feats:
        p = f.get("properties", {})
        rows.append({
            "geoid": p.get("st_co_fips") or p.get("FIPS") or p.get("fips") or p.get("geoid"),
            "state_fips": p.get("st_fips") or p.get("statefips") or p.get("STATEFP"),
            "county_fips": p.get("co_fips") or p.get("countyfips") or p.get("COUNTYFP"),
            "name": p.get("st_co_name") or p.get("name") or p.get("NAME"),
            "deaths": p.get("deaths") or p.get("DEATHS") or p.get("count"),
            "population": p.get("population") or p.get("POPULATION") or p.get("pop"),
            "rate": p.get("rate") or p.get("RATE") or p.get("crude_rate"),
        })
    df = pd.DataFrame(rows)
    return df if len(df) else None

# Per-year national queries (matches the structure of the 2019-2023 scrape's [2] block)
print("=== WISQARS scrape: firearm deaths by county, 2014-2018 ===")

per_year = []
for yr in ["2014","2015","2016","2017","2018"]:
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
    combined.to_parquet(OUT / "fatal_county_per_year_2014_2018.parquet", index=False)
    print(f"\nWROTE {OUT/'fatal_county_per_year_2014_2018.parquet'}: {len(combined):,} rows")
    print(f"  total deaths summed: {pd.to_numeric(combined['deaths'], errors='coerce').sum():,.0f}")

print("\nDONE")
