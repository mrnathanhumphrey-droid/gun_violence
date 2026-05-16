"""Tier 3 / v0.6 sundown source replication: Rigby et al. 2025 dataset.

Replaces the Tougaloo/Loewen scrape (v0.4 source) with the Rigby et al.
2025 *Scientific Data* canonical dataset (https://osf.io/fh7r6/, DOI
10.17605/OSF.IO/FH7R6, 2,347 entries with confidence tiers + Census linkage).

Output: per-county sundown count (Rigby), to swap into the v0.4 design at
the same geography level for direct coefficient comparison.

Geography strategy (4 cases, see Rigby `type` column):
  type=place              -> CDP code in matching_cdp -> gazetteer lat/lon -> spatial join to TIGER county
  type=county             -> matching_county is 5-digit FIPS (use directly)
  type=county subdivision -> county_fips encoded as state_fips*1000 + county_fips_3digit
  type=no match           -> parse centroid2020 lon/lat -> spatial join

Confidence filter: include rows with confidence_level in {Surely, Probable,
Possible}. Exclude {Unlikely}. (Tougaloo equivalent was `is_starred=False`.)
"""
import pathlib
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

ROOT = pathlib.Path(r"D:/Gun Violence")
RIGBY = ROOT / "historical_mechanism/sundown_towns_rigby_2025/sundown_linked_to_census.csv"
GAZ = ROOT / "geographic/census_places_gaz_2024/2024_Gaz_place_national.txt"
TIGER = ROOT / "geographic/tiger_county_2024/extracted/tl_2024_us_county.shp"
HIST_V04 = ROOT / "analysis/historical_features_county_v04.parquet"
OUT = ROOT / "analysis/historical_features_county_v06_rigby.parquet"

CRS_EQUAL_AREA = "EPSG:5070"

print("[1] Loading Rigby 2025 sundown towns ...")
rg = pd.read_csv(RIGBY)
print(f"  total rows: {len(rg)}")
print(f"  confidence distribution: {rg['confidence_level'].value_counts().to_dict()}")
print(f"  type distribution:       {rg['type'].value_counts().to_dict()}")

KEEP_CONF = {"Surely", "Probable", "Possible"}
rg = rg[rg["confidence_level"].isin(KEEP_CONF)].copy()
print(f"\n[2] After confidence filter (Surely/Probable/Possible): {len(rg)}")

# Case A: type=county
mask_county = (rg["type"] == "county") & rg["matching_county"].notna()
case_a = rg[mask_county].copy()
case_a["cf_str"] = case_a["matching_county"].astype(str).str.zfill(5)
print(f"\n[3a] type=county rows resolved: {len(case_a)}")

# Case B: type=county subdivision (encoded state_fips*1000 + 3digit)
mask_sub = (rg["type"] == "county subdivision") & rg["county_fips"].notna()
case_b = rg[mask_sub].copy()
def encode_sub(v):
    v = int(v)
    s = v // 1000
    c = v % 1000
    return f"{s:02d}{c:03d}"
case_b["cf_str"] = case_b["county_fips"].apply(encode_sub)
print(f"[3b] type=county subdivision rows resolved: {len(case_b)}")

# Case C: type=place + matching_cdp -> gazetteer lookup
mask_place = (rg["type"] == "place") & rg["matching_cdp"].notna()
case_c = rg[mask_place].copy()
case_c["cdp_id"] = case_c["matching_cdp"].astype(str).str.replace(r"^CDP:", "", regex=True)
print(f"[3c] type=place rows to resolve via gazetteer: {len(case_c)}")

print("\n[4] Loading Census Places 2024 gazetteer for place->lat/lon ...")
gaz = pd.read_csv(GAZ, sep="\t")
gaz.columns = [c.strip() for c in gaz.columns]
# Gazetteer GEOID = state(2) + place(5). Rigby matching_cdp = 5-digit place code, state context from `state`.
gaz["geoid_str"] = gaz["GEOID"].astype(str).str.zfill(7)
gaz["place_id"] = gaz["geoid_str"].str[2:]
gaz["LAT"] = pd.to_numeric(gaz["INTPTLAT"], errors="coerce")
gaz["LON"] = pd.to_numeric(gaz["INTPTLONG"], errors="coerce")
gaz_lookup = gaz[["USPS", "place_id", "LAT", "LON"]].drop_duplicates(subset=["USPS","place_id"])
print(f"  gazetteer rows: {len(gaz):,}, unique (state,place_id): {len(gaz_lookup):,}")

case_c = case_c.merge(gaz_lookup, left_on=["state","cdp_id"], right_on=["USPS","place_id"], how="left")
n_place_matched = case_c["LAT"].notna().sum()
print(f"  gazetteer matches (state+place_id): {n_place_matched} / {len(case_c)}")

# Case D: type=no match with centroid2020
mask_nm = (rg["type"] == "no match") & rg["centroid2020"].notna()
case_d = rg[mask_nm].copy()
def parse_centroid(s):
    parts = [p.strip() for p in str(s).replace("\t", ",").split(",")]
    if len(parts) >= 2:
        try:
            lon, lat = float(parts[0]), float(parts[1])
            return lon, lat
        except ValueError:
            return None, None
    return None, None
case_d[["LON", "LAT"]] = case_d["centroid2020"].apply(
    lambda s: pd.Series(parse_centroid(s)))
n_centroid_parsed = case_d["LAT"].notna().sum()
print(f"[3d] type=no match rows with parsed centroid: {n_centroid_parsed} / {len(case_d)}")

# Spatial-join cases C + D
spatial_rows = pd.concat([
    case_c[["unique_id", "LAT", "LON"]],
    case_d[["unique_id", "LAT", "LON"]],
], ignore_index=True).dropna(subset=["LAT", "LON"])
print(f"\n[5] Spatial-joining {len(spatial_rows)} centroid points -> TIGER county polygons ...")

print("    loading TIGER county shapefile ...")
counties = gpd.read_file(TIGER)[["STATEFP", "COUNTYFP", "GEOID", "geometry"]].copy()
counties = counties.to_crs(CRS_EQUAL_AREA)

pts = gpd.GeoDataFrame(
    spatial_rows,
    geometry=[Point(lon, lat) for lon, lat in zip(spatial_rows["LON"], spatial_rows["LAT"])],
    crs="EPSG:4326",
).to_crs(CRS_EQUAL_AREA)

joined = gpd.sjoin(pts, counties, how="left", predicate="within")
n_sjoin_matched = joined["GEOID"].notna().sum()
print(f"    spatial-join matched: {n_sjoin_matched} / {len(spatial_rows)}")
joined["cf_str"] = joined["GEOID"]

# Combine all 4 cases
case_a_fc = case_a[["unique_id", "cf_str"]]
case_b_fc = case_b[["unique_id", "cf_str"]]
case_cd_fc = joined[["unique_id", "cf_str"]].dropna(subset=["cf_str"])
all_resolved = pd.concat([case_a_fc, case_b_fc, case_cd_fc], ignore_index=True)
all_resolved = all_resolved.dropna(subset=["cf_str"]).drop_duplicates(subset="unique_id")
print(f"\n[6] Total rows resolved to county FIPS: {len(all_resolved)} / {len(rg)} (filtered)")

# Aggregate per county
agg = all_resolved.groupby("cf_str").size().reset_index(name="sundown_n_rigby")
agg["state_fips"] = agg["cf_str"].str[:2]
agg["county_fips"] = agg["cf_str"].str[2:]
print(f"\n[7] Unique counties with >=1 sundown entry: {len(agg)}")
print(f"   distribution of sundown_n_rigby:")
print("  ", agg["sundown_n_rigby"].describe().to_string().replace("\n","\n   "))

# Merge into v0.4 historical features
print(f"\n[8] Merging into v0.4 historical features ...")
hist = pd.read_parquet(HIST_V04)
print(f"   v0.4 hist shape: {hist.shape}, cols: {list(hist.columns)}")
hist = hist.merge(agg.rename(columns={"state_fips":"state", "county_fips":"county"})[
    ["state","county","sundown_n_rigby"]],
    on=["state","county"], how="left")
hist["sundown_n_rigby"] = hist["sundown_n_rigby"].fillna(0).astype(int)
import numpy as np
hist["sundown_log1p_rigby"] = np.log1p(hist["sundown_n_rigby"])
hist["sundown_any_rigby"] = (hist["sundown_n_rigby"] > 0).astype(int)
print(f"   merged shape: {hist.shape}")
print(f"   counties with sundown_any_rigby=1: {hist['sundown_any_rigby'].sum()} / {len(hist)}")
print(f"   compare v0.4 Tougaloo (sundown_any): {hist['sundown_any'].sum()} / {len(hist)}")

hist.to_parquet(OUT, index=False)
print(f"\nSaved: {OUT}")
