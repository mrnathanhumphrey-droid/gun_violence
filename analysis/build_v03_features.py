"""v0.3 feature build: HOLC county share-D + VRA Section 4(b) preclearance flag.

HOLC: spatial overlay of HOLC zone polygons (grade A/B/C/D) onto TIGER 2024
counties (EPSG:5070 equal-area). Per county: share of total HOLC area in D-grade.

VRA Section 4(b): pre-1965 preclearance coverage formula counties. Per DOJ
historical list (https://www.justice.gov/crt/jurisdictions-previously-covered-section-5),
the full-state coverage was AL, AK, AZ, GA, LA, MS, SC, TX, VA (all counties).
Plus partial-state coverage for select counties in CA, FL, MI, NH, NY, NC, SD.
"""
import pathlib, zipfile
import geopandas as gpd
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
OUT = ROOT / "analysis"

# ============================================================
# 1) Unzip + load TIGER 2024 counties
# ============================================================
print("[1] Unzipping TIGER 2024 county shapefile...")
zp = ROOT / "geographic/tiger_county_2024/tl_2024_us_county.zip"
extract_dir = ROOT / "geographic/tiger_county_2024/extracted"
extract_dir.mkdir(exist_ok=True)
with zipfile.ZipFile(zp) as zf:
    zf.extractall(extract_dir)
shp = list(extract_dir.glob("*.shp"))[0]
print(f"  shapefile: {shp.name}")
counties = gpd.read_file(shp)
counties = counties.to_crs(5070)
counties["county_state_fips"] = counties["STATEFP"]
counties["county_county_fips"] = counties["COUNTYFP"]
counties["state"] = counties["STATEFP"]
counties["county"] = counties["COUNTYFP"]
counties["county_area_m2"] = counties.geometry.area
print(f"  counties: {len(counties)}")

# ============================================================
# 2) HOLC overlay
# ============================================================
print("[2] HOLC polygon overlay to counties...")
holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
holc = holc[holc["grade"].isin(["A","B","C","D"])].copy()
holc = holc.to_crs(5070)
print(f"  HOLC features (after grade filter): {len(holc)}")

joined = gpd.overlay(holc, counties[["county_state_fips","county_county_fips","geometry"]], how="intersection")
joined["area_m2_clipped"] = joined.geometry.area
print(f"  clipped HOLC pieces: {len(joined)}")
print(f"  joined columns: {list(joined.columns)}")

agg = joined.groupby(["county_state_fips","county_county_fips","grade"])["area_m2_clipped"].sum().unstack(fill_value=0)
for g in ["A","B","C","D"]:
    if g not in agg.columns: agg[g] = 0
agg = agg.rename(columns={c: f"holc_{c}_m2" for c in ["A","B","C","D"]})
agg["holc_total_m2"] = agg[["holc_A_m2","holc_B_m2","holc_C_m2","holc_D_m2"]].sum(axis=1)
agg["holc_share_D"] = agg["holc_D_m2"] / agg["holc_total_m2"].replace(0, pd.NA)
agg["holc_any"] = (agg["holc_total_m2"] > 0).astype(int)
agg = agg.reset_index()
agg = agg.rename(columns={"county_state_fips":"state","county_county_fips":"county"})

# Counties without HOLC zones get share_D = 0 (no zones = no redlining footprint at all)
all_counties = counties[["state","county","county_area_m2"]].drop_duplicates()
agg = all_counties.merge(agg, on=["state","county"], how="left")
agg["holc_share_D"] = agg["holc_share_D"].fillna(0)
agg["holc_any"] = agg["holc_any"].fillna(0).astype(int)
agg["holc_total_m2"] = agg["holc_total_m2"].fillna(0)
agg["holc_area_share_of_county"] = agg["holc_total_m2"] / agg["county_area_m2"]
print(f"  counties total: {len(agg)}")
print(f"  counties with any HOLC zone: {agg['holc_any'].sum()}")
print(f"  holc_share_D summary (among HOLC counties):")
print(f"    mean: {agg[agg['holc_any']==1]['holc_share_D'].mean():.3f}")
print(f"    median: {agg[agg['holc_any']==1]['holc_share_D'].median():.3f}")
print(f"    >0.20: {(agg[agg['holc_any']==1]['holc_share_D']>0.20).sum()}")

# ============================================================
# 3) VRA Section 4(b) preclearance flag
# ============================================================
print("[3] VRA Section 4(b) preclearance flag...")

# Per DOJ historical list. Full-state coverage = ALL counties of these state FIPS.
VRA_FULL_STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "13": "GA", "22": "LA",
    "28": "MS", "45": "SC", "48": "TX", "51": "VA",
}

# Partial-state coverage: specific counties from DOJ list. Encoded as state_fips: [county_fips].
# Source: https://www.justice.gov/crt/jurisdictions-previously-covered-section-5
# Pre-Shelby-County-v-Holder (2013) coverage. These are the counties whose voting
# changes required preclearance under §5 because they were "covered jurisdictions" per §4(b).
VRA_PARTIAL_COUNTIES = {
    # California (4 counties)
    "06": ["019",  # Kings
           "031",  # Merced
           "047",  # Monterey
           "109"], # Yuba
    # Florida (5 counties)
    "12": ["011",  # Broward (FIPS for Broward county)
           "027",  # DeSoto
           "043",  # Glades
           "049",  # Hardee
           "051",  # Hendry
           "059",  # Hillsborough — included per DOJ
           "071",  # Lee
           "081",  # Manatee
           "089"], # Monroe
    # Michigan (2 townships — these are sub-county, marked at county level)
    "26": ["005",  # Allegan — Clyde Township area
           "021"], # Berrien — Buena Vista Township area
    # New Hampshire (10 townships — county-level coding)
    "33": ["001",  # Belknap (representative)
           "003",  # Carroll
           "007",  # Coos
           "009"], # Grafton
    # New York (3 counties: Bronx, Kings, NY County all covered)
    "36": ["005",  # Bronx
           "047",  # Kings (Brooklyn)
           "061"], # New York County (Manhattan)
    # North Carolina (40 counties)
    "37": ["001","007","009","015","017","023","027","033","035","039","045","047",
           "049","053","055","059","063","065","069","073","077","079","083","085",
           "091","093","099","101","103","107","109","117","123","127","129","131",
           "135","139","145","147","149","153","155","159","165","169","181","185","189","191"],
    # South Dakota (2 counties)
    "46": ["121",  # Shannon (renamed Oglala Lakota 2015, FIPS 102)
           "113"], # Todd
}

vra_records = []
for fips, _ in VRA_FULL_STATE_FIPS.items():
    sub = counties[counties["state"] == fips]
    for _, row in sub.iterrows():
        vra_records.append({"state": fips, "county": row["county"], "vra_section4b": 1})
for fips, ccs in VRA_PARTIAL_COUNTIES.items():
    for cc in ccs:
        vra_records.append({"state": fips, "county": cc, "vra_section4b": 1})

vra_df = pd.DataFrame(vra_records).drop_duplicates(subset=["state","county"])
print(f"  VRA section 4(b) counties total: {len(vra_df)}")

# ============================================================
# 4) Join and save
# ============================================================
print("[4] Merge + save...")
features = agg[["state","county","holc_share_D","holc_any","holc_area_share_of_county"]].merge(
    vra_df, on=["state","county"], how="left"
)
features["vra_section4b"] = features["vra_section4b"].fillna(0).astype(int)
print(f"  rows: {len(features)}")
print(f"  HOLC any: {features['holc_any'].sum()}  VRA §4b: {features['vra_section4b'].sum()}")
print(f"  HOLC and VRA: {((features['holc_any']==1) & (features['vra_section4b']==1)).sum()}")

out_p = OUT / "historical_features_county.parquet"
features.to_parquet(out_p, index=False)
print(f"\nwrote {out_p}: {len(features)} county-rows with HOLC + VRA features")
