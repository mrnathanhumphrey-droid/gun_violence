"""Parse WISQARS GeoJSON dumps from scrape_2019_2023/*.json into a flat parquet."""
import json, pathlib, pandas as pd

IN_DIR = pathlib.Path(r"D:/Gun Violence/outcomes/wisqars/scrape_2019_2023")
OUT_DIR = IN_DIR  # write parquets next to JSONs

def parse_features(path, **extra_cols):
    d = json.loads(path.read_text())
    features = d.get("rawdata", {}).get("features", [])
    rows = []
    for f in features:
        p = f.get("properties", {})
        row = {**p, **extra_cols}
        rows.append(row)
    return pd.DataFrame(rows)

# Per-year (firearm, all intents)
per_year_dfs = []
for yr in ["2019","2020","2021","2022","2023"]:
    p = IN_DIR / f"fatal_county_{yr}.json"
    if not p.exists():
        print(f"  missing {p.name}")
        continue
    df = parse_features(p, year=yr, intent_label="all", mech_label="firearm")
    per_year_dfs.append(df)
    print(f"  {yr}: {len(df):,} county features")

if per_year_dfs:
    combined = pd.concat(per_year_dfs, ignore_index=True)
    target = OUT_DIR / "wisqars_firearm_deaths_by_county_year.parquet"
    combined.to_parquet(target, index=False)
    print(f"\nWROTE {target}: {len(combined):,} rows × {len(combined.columns)} cols")
    print(f"states: {combined['ST'].nunique()}, counties: {combined['GEOID'].nunique()}")
    print(f"total deaths (sum, with suppression artefacts): {pd.to_numeric(combined['deaths'], errors='coerce').sum():,.0f}")
    print(f"suppressed cells: {(pd.to_numeric(combined['SupressFlag'], errors='coerce')==1).sum():,}")

# Per-intent (firearm, 2019-2023 combined)
intent_dfs = []
for label in ["homicide","suicide","unintentional","undetermined"]:
    p = IN_DIR / f"fatal_county_{label}.json"
    if not p.exists():
        continue
    df = parse_features(p, year="2019-2023", intent_label=label, mech_label="firearm")
    intent_dfs.append(df)
    print(f"  intent={label}: {len(df):,} rows")

if intent_dfs:
    combined_i = pd.concat(intent_dfs, ignore_index=True)
    target_i = OUT_DIR / "wisqars_firearm_deaths_by_county_intent.parquet"
    combined_i.to_parquet(target_i, index=False)
    print(f"\nWROTE {target_i}: {len(combined_i):,} rows")

# Also save the all-years all-intents single dataset
p_all = IN_DIR / "fatal_county_2019_2023_all_intents.json"
if p_all.exists():
    df_all = parse_features(p_all, year="2019-2023", intent_label="all", mech_label="firearm")
    df_all.to_parquet(OUT_DIR / "wisqars_firearm_deaths_2019_2023_combined.parquet", index=False)
    print(f"\nALL combined: {len(df_all):,} rows")

print("\nDONE")
