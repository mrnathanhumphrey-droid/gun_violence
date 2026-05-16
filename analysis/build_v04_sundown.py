"""v0.4 sundown towns feature build.

Inputs:
  D:/Gun Violence/historical_mechanism/sundown_towns/sundown_towns_raw.csv
    (2,437 suspected sundown towns from Tougaloo Loewen DB scrape)
  D:/Gun Violence/geographic/census_places_gaz_2024/2024_Gaz_place_national.txt
    (Census Places gazetteer with lat/lon centroids)
  D:/Gun Violence/geographic/tiger_county_2024/extracted/tl_2024_us_county.shp
    (already on disk from v0.3 HOLC build)

Method:
  1. Match sundown town (name, state) -> gazetteer row -> (lat, lon) centroid
  2. Spatial-join centroid point -> TIGER county polygon
  3. Aggregate per county: count of sundown towns
  4. Merge into historical_features_county.parquet (add sundown_n + sundown_any)
"""
import re, pathlib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

ROOT = pathlib.Path(r"D:/Gun Violence")
SUNDOWN = ROOT / "historical_mechanism/sundown_towns/sundown_towns_raw.csv"
GAZ = ROOT / "geographic/census_places_gaz_2024/2024_Gaz_place_national.txt"
TIGER = ROOT / "geographic/tiger_county_2024/extracted/tl_2024_us_county.shp"
HIST = ROOT / "analysis/historical_features_county.parquet"
OUT = ROOT / "analysis/historical_features_county_v04.parquet"

print("[1] Loading sundown towns ...")
sd = pd.read_csv(SUNDOWN)
sd_active = sd[~sd["is_starred"]].copy()
print(f"  total entries: {len(sd)}  suspected sundown: {len(sd_active)}")

print("\n[2] Loading Census Places gazetteer ...")
gaz = pd.read_csv(GAZ, sep="\t")
gaz.columns = [c.strip() for c in gaz.columns]
gaz["NAME"] = gaz["NAME"].astype(str).str.strip()
# Strip the LSAD descriptor: "Abbeville city" -> "Abbeville"
LSAD_SUFFIXES = (" city", " town", " village", " borough", " township", " CDP",
                 " municipality", " plantation", " comunidad", " urban county",
                 " consolidated government", " metropolitan government",
                 " unified government", " corporation", " gore")
def strip_lsad(name):
    for suf in LSAD_SUFFIXES:
        if name.lower().endswith(suf):
            return name[: -len(suf)].strip()
    return name
gaz["place_clean"] = gaz["NAME"].apply(strip_lsad)
print(f"  gazetteer rows: {len(gaz):,}")

print("\n[3] Matching sundown towns to gazetteer (state + lowercased name) ...")
gaz["key"] = gaz["USPS"].str.upper() + "|" + gaz["place_clean"].str.lower()
gaz_idx = gaz.set_index("key")

# Sundown town keys with state abbreviation
sd_active["key"] = sd_active["state_abbr"].str.upper() + "|" + sd_active["town_name"].str.strip().str.lower()

# Match against gazetteer
matched_rows = []
unmatched = []
for _, row in sd_active.iterrows():
    k = row["key"]
    if k in gaz_idx.index:
        match = gaz_idx.loc[k]
        # if multiple matches (city + town variants), take first
        if isinstance(match, pd.DataFrame):
            match = match.iloc[0]
        matched_rows.append({
            "town_name": row["town_name"], "state_abbr": row["state_abbr"],
            "lat": match["INTPTLAT"], "lon": match["INTPTLONG"],
            "place_geoid": match["GEOID"],
        })
    else:
        unmatched.append((row["town_name"], row["state_abbr"]))

matched = pd.DataFrame(matched_rows)
print(f"  matched: {len(matched)} / {len(sd_active)}  ({100*len(matched)/len(sd_active):.0f}%)")
print(f"  unmatched sample (first 10): {unmatched[:10]}")

print("\n[4] Loading TIGER counties ...")
counties = gpd.read_file(TIGER)
counties = counties.to_crs(5070)  # equal-area
print(f"  counties: {len(counties)}")

print("\n[5] Spatial join: town centroid point -> county polygon ...")
pts = gpd.GeoDataFrame(
    matched,
    geometry=gpd.points_from_xy(matched["lon"].astype(float), matched["lat"].astype(float)),
    crs="EPSG:4326"
).to_crs(5070)
joined = gpd.sjoin(pts, counties[["STATEFP","COUNTYFP","geometry"]], how="left", predicate="within")
hits = joined.dropna(subset=["STATEFP"])
print(f"  point-in-polygon hits: {len(hits)} / {len(pts)}")

print("\n[6] Aggregating per-county sundown count ...")
agg = (hits.groupby(["STATEFP","COUNTYFP"]).size()
       .reset_index(name="sundown_n")
       .rename(columns={"STATEFP":"state","COUNTYFP":"county"}))
print(f"  counties with at least one sundown town: {len(agg)}")
print(f"  sundown_n distribution: max={agg['sundown_n'].max()}  mean={agg['sundown_n'].mean():.2f}")
print(f"  top 10 counties:")
top = agg.sort_values("sundown_n", ascending=False).head(10)
print(top.to_string(index=False))

print("\n[7] Merging into historical_features_county.parquet ...")
hist = pd.read_parquet(HIST)
print(f"  existing historical_features: {len(hist)} county rows  "
      f"cols: {list(hist.columns)}")
v04 = hist.merge(agg, on=["state","county"], how="left")
v04["sundown_n"] = v04["sundown_n"].fillna(0).astype(int)
v04["sundown_any"] = (v04["sundown_n"] > 0).astype(int)
# Continuous intensity: log1p(count) so 1 town != same as 10 towns
import numpy as np
v04["sundown_log1p"] = np.log1p(v04["sundown_n"])

print(f"  v0.4 cols: {list(v04.columns)}")
print(f"  counties with sundown_any: {v04['sundown_any'].sum()}")
print(f"  joint distributions:")
print(f"    HOLC + sundown:                 {((v04['holc_any']==1) & (v04['sundown_any']==1)).sum()}")
print(f"    VRA + sundown:                  {((v04['vra_section4b']==1) & (v04['sundown_any']==1)).sum()}")
print(f"    HOLC + VRA + sundown all three: {((v04['holc_any']==1) & (v04['vra_section4b']==1) & (v04['sundown_any']==1)).sum()}")

v04.to_parquet(OUT, index=False)
print(f"\nWrote {OUT}: {len(v04)} county rows with HOLC + VRA + sundown features")
