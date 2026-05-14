"""Pull CDC 'Mapping Injury, Overdose, and Violence - County' (psx4-wq38).

County-level death counts + rates for drug OD, suicide, homicide, firearm
injuries, etc. Replaces WISQARS county-level firearm mortality.

Note: 1-9 deaths suppressed; rate_m is a modeled small-area estimate.
"""
import os, time, json, sys, pathlib, requests
import pandas as pd

OUT = pathlib.Path(r"D:/Gun Violence/outcomes/wisqars/cdc_psx4_wq38")
OUT.mkdir(parents=True, exist_ok=True)
PROV = pathlib.Path(r"D:/Gun Violence/provenance/cdc_firearm")
PROV.mkdir(parents=True, exist_ok=True)

URL = "https://data.cdc.gov/resource/psx4-wq38.json"
LIMIT = 50000

# Save metadata
meta = requests.get("https://data.cdc.gov/api/views/psx4-wq38", timeout=30).json()
(PROV / "psx4_wq38_metadata.json").write_text(json.dumps(meta, indent=2))
print(f"saved metadata: {len(meta.get('columns',[]))} columns")

# Paginated pull
parts = []
offset = 0
while True:
    r = requests.get(URL, params={"$limit": LIMIT, "$offset": offset, "$order": "geoid,intent,period"}, timeout=60)
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    parts.append(pd.DataFrame(batch))
    print(f"  offset {offset}: {len(batch)} rows (running total {sum(len(p) for p in parts):,})")
    if len(batch) < LIMIT:
        break
    offset += LIMIT
    time.sleep(0.5)

df = pd.concat(parts, ignore_index=True)
df.to_parquet(OUT / "cdc_county_injury_violence.parquet", index=False)
print(f"\nWROTE {OUT / 'cdc_county_injury_violence.parquet'}: {len(df):,} rows")
print(f"intents: {df['intent'].value_counts().to_dict()}")
print(f"periods: {sorted(df['period'].unique())}")
