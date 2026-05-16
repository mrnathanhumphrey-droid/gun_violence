"""v0.6: block-group cell assignment.

v0.4 assigns urban/suburban cell membership at TRACT level then
pop-weighted-aggregates matching tracts within county -> (county, cell)
units. v0.6 refines this: assign membership at BLOCK GROUP level (4-5×
finer geography) then aggregate matching BGs within county -> same shape
(county, cell) units, but with PURER within-cell demographic signal.

Rationale: a tract that's 55% Black overall doesn't qualify for UB-HI
(60% threshold) under v0.4, but it likely contains BGs that ARE 70-80%
Black — those should count. v0.6 surfaces them.

Inheritance rules for inequity composite dimensions that don't exist at
BG level:
  * food_inequity_score: tract-level (USDA LA1 flags) -> BG inherits parent tract
  * school county_log_ppe: county-level (NCES F-33) -> BG inherits parent county
  * health pct_uninsured, pcp_rate: county-level (CHR) -> BG inherits parent county

The composite has 5 dims (poverty, food, housing, school, health).
poverty + housing actually vary at BG level. food + school + health are
inherited constants within tract/county. This makes the BG cell-membership
SHARPER on the race/income dimensions, which is the load-bearing axis.

Final unit shape: identical to v0.4 (456 county-units across 8 cells, with
4 urban/suburban cells refined by BG aggregation, 4 rural cells unchanged).
The same v0.4 Stan model fits this — only the design predictors change.
"""
import os
RTOOLS = "C:/Users/Nate/.cmdstan/RTools40"
os.environ["PATH"] = f"{RTOOLS}/mingw64/bin;{RTOOLS}/usr/bin;" + os.environ.get("PATH", "")

import pathlib, time, zipfile, json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS_BG = ROOT / "demographics/acs_5yr_bg"
ACS_TR = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
PSX = ROOT / "outcomes/wisqars/cdc_psx4_wq38/cdc_county_injury_violence.parquet"
OUT = ROOT / "analysis/production_v0_6"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== v0.6: block-group cell assignment ===\n")

def n(s): return pd.to_numeric(s, errors="coerce")

# ----- BG demographics (parallel of v0.1 tract loader) -----
def load_bg(table):
    f = ACS_BG / f"acs5_2023_{table}_bg.parquet"
    return pd.read_parquet(f)

def load_tract(table):
    f = ACS_TR / f"acs5_2023_{table}_tract.parquet"
    return pd.read_parquet(f)

def load_county(table):
    f = ACS_TR / f"acs5_2023_{table}_county.parquet"
    return pd.read_parquet(f)

print("[1] Loading BG demographics (13 ACS tables) ...")
KEYS_BG = ["state","county","tract","block group"]

# Age structure for pct_working_age + population
pop = load_bg("B01001")[KEYS_BG + ["B01001_001E"] + [f"B01001_{i:03d}E" for i in [3,4,5,6,20,21,22,23,24,25,27,28,29,30,44,45,46,47,48,49]]].copy()
for c in pop.columns[len(KEYS_BG):]: pop[c] = n(pop[c])
pop["pop"] = pop["B01001_001E"]
pop["under18"] = pop[[f"B01001_{i:03d}E" for i in [3,4,5,6,27,28,29,30]]].sum(axis=1)
pop["over65"] = pop[[f"B01001_{i:03d}E" for i in [20,21,22,23,24,25,44,45,46,47,48,49]]].sum(axis=1)
pop["pct_working_age"] = (pop["pop"] - pop["under18"] - pop["over65"]) / pop["pop"].replace(0, np.nan) * 100

race = load_bg("B02001")[KEYS_BG + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
for c in race.columns[len(KEYS_BG):]: race[c] = n(race[c])
race.columns = KEYS_BG + ["race_total","white","black","aian"]

hisp = load_bg("B03003")[KEYS_BG + ["B03003_001E","B03003_003E"]].copy()
for c in hisp.columns[len(KEYS_BG):]: hisp[c] = n(hisp[c])
hisp.columns = KEYS_BG + ["hisp_total","hisp"]

pov = load_bg("B17001")[KEYS_BG + ["B17001_001E","B17001_002E"]].copy()
for c in pov.columns[len(KEYS_BG):]: pov[c] = n(pov[c])
pov.columns = KEYS_BG + ["pov_denom","below_pov"]

ten = load_bg("B25003")[KEYS_BG + ["B25003_001E","B25003_002E"]].copy()
for c in ten.columns[len(KEYS_BG):]: ten[c] = n(ten[c])
ten.columns = KEYS_BG + ["ten_total","owner_occ"]

rent = load_bg("B25070")[KEYS_BG + ["B25070_001E","B25070_010E"]].copy()
for c in rent.columns[len(KEYS_BG):]: rent[c] = n(rent[c])
rent.columns = KEYS_BG + ["rent_denom","rent_50plus"]

inc = load_bg("B19013")[KEYS_BG + ["B19013_001E"]].copy()
inc["median_hh_income"] = n(inc["B19013_001E"])

b15 = load_bg("B15003")[KEYS_BG + [f"B15003_{i:03d}E" for i in [1,17,18,22,23,24,25]]].copy()
for c in b15.columns[len(KEYS_BG):]: b15[c] = n(b15[c])
b15["pct_hs_terminal"] = (b15["B15003_017E"]+b15["B15003_018E"]) / b15["B15003_001E"].replace(0, np.nan) * 100
b15["pct_bachelors_plus"] = (b15["B15003_022E"]+b15["B15003_023E"]+b15["B15003_024E"]+b15["B15003_025E"]) / b15["B15003_001E"].replace(0, np.nan) * 100

lf = load_bg("B23025")[KEYS_BG + ["B23025_001E","B23025_004E"]].copy()
for c in lf.columns[len(KEYS_BG):]: lf[c] = n(lf[c])
lf["pct_employed_civilian_LF"] = lf["B23025_004E"] / lf["B23025_001E"].replace(0, np.nan) * 100

hh = load_bg("B11001")[KEYS_BG + ["B11001_001E","B11001_002E"]].copy()
for c in hh.columns[len(KEYS_BG):]: hh[c] = n(hh[c])
hh["pct_family_HH"] = hh["B11001_002E"] / hh["B11001_001E"].replace(0, np.nan) * 100

bg = (pop[KEYS_BG+["pop","pct_working_age"]]
      .merge(race[KEYS_BG+["race_total","white","black","aian"]], on=KEYS_BG)
      .merge(hisp[KEYS_BG+["hisp_total","hisp"]], on=KEYS_BG)
      .merge(pov[KEYS_BG+["pov_denom","below_pov"]], on=KEYS_BG)
      .merge(ten[KEYS_BG+["ten_total","owner_occ"]], on=KEYS_BG)
      .merge(rent[KEYS_BG+["rent_denom","rent_50plus"]], on=KEYS_BG)
      .merge(inc[KEYS_BG+["median_hh_income"]], on=KEYS_BG)
      .merge(b15[KEYS_BG+["pct_hs_terminal","pct_bachelors_plus"]], on=KEYS_BG)
      .merge(lf[KEYS_BG+["pct_employed_civilian_LF"]], on=KEYS_BG)
      .merge(hh[KEYS_BG+["pct_family_HH"]], on=KEYS_BG))
bg["pct_black"] = bg["black"] / bg["race_total"].replace(0, np.nan) * 100
bg["pct_hispanic"] = bg["hisp"] / bg["hisp_total"].replace(0, np.nan) * 100
bg["pct_nhw_approx"] = bg["white"] / bg["race_total"].replace(0, np.nan) * 100 - bg["pct_hispanic"]
bg["pct_aian"] = bg["aian"] / bg["race_total"].replace(0, np.nan) * 100
bg["poverty_rate"] = bg["below_pov"] / bg["pov_denom"].replace(0, np.nan) * 100
bg["renter_rate"] = (1 - bg["owner_occ"] / bg["ten_total"].replace(0, np.nan)) * 100
bg["rent_burden_pct"] = bg["rent_50plus"] / bg["rent_denom"].replace(0, np.nan) * 100
print(f"  block groups: {len(bg):,}")

# ----- Inheritance: food (tract), school (county), health (county) -----
print("\n[2] Inheriting tract-level food access flag -> BG ...")
fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state"], fa["county"], fa["tract"] = fa["CensusTract"].str[:2], fa["CensusTract"].str[2:5], fa["CensusTract"].str[5:]
fa["food_inequity_score"] = pd.concat([
    pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0),
    pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
], axis=1).max(axis=1)
bg = bg.merge(fa[["state","county","tract","food_inequity_score"]], on=["state","county","tract"], how="left")
bg["food_inequity_score"] = bg["food_inequity_score"].fillna(bg["food_inequity_score"].median())
print(f"  BGs with food signal: {bg['food_inequity_score'].notna().sum():,}")

print("\n[3] Inheriting county-level school (F-33 PPE) and health (CHR) -> BG ...")
with zipfile.ZipFile(F33) as zf, zf.open("sdf22_1a.txt") as f:
    f33 = pd.read_csv(f, sep="\t", dtype=str, low_memory=False, usecols=["CONUM","V33","TOTALEXP","SCHLEV"])
f33["enr"] = n(f33["V33"]); f33["te"] = n(f33["TOTALEXP"])
f33 = f33[f33["SCHLEV"].isin(["01","02","03"]) & (f33["enr"]>0) & (f33["te"]>0)]
f33["log_ppe"] = np.log(f33["te"]*1000/f33["enr"])
cppe = f33.groupby("CONUM").apply(lambda g: (g["log_ppe"]*g["enr"]).sum()/g["enr"].sum()).reset_index(name="county_log_ppe")
cppe["state"], cppe["county"] = cppe["CONUM"].str[:2], cppe["CONUM"].str[2:]
bg = bg.merge(cppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
bg["county_log_ppe"] = bg["county_log_ppe"].fillna(bg["county_log_ppe"].median())

chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = n(chr_h["Uninsured__% Uninsured"])
chr_h["pcp_rate"] = n(chr_h["Primary Care Physicians__Primary Care Physicians Rate"])
bg = bg.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
for c in ["pct_uninsured","pcp_rate"]:
    bg[c] = bg[c].fillna(bg[c].median())

# Urbanicity proxy: BG inherits parent county's class (n_tracts in county)
print("\n[4] Computing urbanicity (BG inherits parent county) ...")
# Need n_tracts per county from TRACT data
tr_count = load_tract("B01001")[["state","county","tract"]].drop_duplicates()
ct = tr_count.groupby(["state","county"]).size().reset_index(name="n_tracts")
bg = bg.merge(ct, on=["state","county"], how="left")
bg["n_tracts"] = bg["n_tracts"].fillna(0)
bg["urban_class"] = pd.cut(bg["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])
print(f"  BGs by urbanicity:\n{bg['urban_class'].value_counts().to_string()}")

# Composite β@0.5 standardization (within urbanicity stratum, BG level)
print("\n[5] Composite β@0.5 standardization (within urbanicity, BG level) ...")
def standardize_beta(df):
    out = df.copy()
    out["raw_housing"] = (out["rent_burden_pct"] + out["renter_rate"]) / 2
    out["raw_health"] = out["pct_uninsured"] - out["pcp_rate"] / 100
    cols = {"poverty_z":"poverty_rate","food_z":"food_inequity_score","housing_z":"raw_housing",
            "school_z":"county_log_ppe","health_z":"raw_health"}
    for z, src in cols.items():
        v = out[src]
        out[z] = np.nan
        for s in out["urban_class"].dropna().unique():
            m = out["urban_class"] == s
            v_s = v[m]
            if v_s.notna().sum() < 2: continue
            out.loc[m, z] = (v_s - v_s.mean()) / v_s.std()
        if z == "school_z": out[z] = -out[z]
    out["composite_mean"] = out[list(cols.keys())].mean(axis=1)
    return out

bg = standardize_beta(bg)
print(f"  composite_mean stats: mean={bg['composite_mean'].mean():.3f}, sd={bg['composite_mean'].std():.3f}")

# Cell assignment thresholds (same as v0.1) — applied at BG level for urban/suburban
print("\n[6] BG-level cell assignment (urban+suburban). Rural cells stay county-level ...")
def elig_bg(df):
    """BG-level eligibility filter: pop ≥ 200 (smaller threshold than tracts ≥1500)."""
    df = df[df["pop"] >= 200].copy()
    return df[df["urban_class"]=="urban"], df[df["urban_class"]=="suburban"]

u_bg, s_bg = elig_bg(bg)
print(f"  eligible urban BGs: {len(u_bg):,}  suburban BGs: {len(s_bg):,}")

# Rural cells: load county-level frame from v0.1
print("\n[7] Loading v0.1 design for rural cells (unchanged county-level) ...")
v01 = pd.read_parquet(ROOT / "analysis/production_v0_1/design_units.parquet")
rural = v01[v01["cell_id"].isin(["RW-HI","RB-HI","RH-HI","RNA-HI"])].copy()
print(f"  rural units carried over from v0.1: {len(rural)}")

CELLS_URBAN_SUB = [
    ("UB-HI", "u", lambda d: d["pct_black"] >= 60, "HI"),
    ("UH-HI", "u", lambda d: d["pct_hispanic"] >= 60, "HI"),
    ("UW-LI", "u", lambda d: d["pct_nhw_approx"] >= 70, "LI"),
    ("SB-MC", "s", lambda d: d["pct_black"] >= 60, "MC"),
]

THRESHOLD = 0.5
bg_cells = []
for cid, base_key, race_fn, tier in CELLS_URBAN_SUB:
    base_df = {"u": u_bg, "s": s_bg}[base_key]
    if tier == "HI":
        sel = race_fn(base_df) & (base_df["composite_mean"] >= THRESHOLD)
    elif tier == "LI":
        sel = race_fn(base_df) & (base_df["composite_mean"] <= -THRESHOLD/2)
    else:  # MC
        sel = race_fn(base_df) & (base_df["composite_mean"] > -THRESHOLD/2) & (base_df["composite_mean"] < THRESHOLD)
    sub = base_df[sel].copy()
    sub["cell_id"] = cid
    bg_cells.append(sub)
    print(f"  {cid}: {len(sub):,} BGs (vs v0.4 tract counts: UB-HI 71, UH-HI 64, UW-LI 135, SB-MC 67 — these are county-units after aggregation)")

bg_cells_df = pd.concat(bg_cells, ignore_index=True)

# Aggregate BGs within (state, county, cell) to county-cell units
print("\n[8] Aggregating BG-cells -> (county, cell) units (pop-weighted) ...")
agg_cols = ["composite_mean","pct_black","pct_hispanic","pct_nhw_approx","pct_aian",
            "median_hh_income","pct_hs_terminal","pct_bachelors_plus",
            "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]

def pwm(g, col):
    w = g["pop"]; v = g[col]
    if w.sum() == 0: return np.nan
    return (v.fillna(0) * w).sum() / w.sum()

urban_units = []
for cid, sub in bg_cells_df.groupby("cell_id"):
    gb = sub.groupby(["state","county"])
    rows = gb.agg(pop_in_cell=("pop","sum"), n_bgs=("pop","count")).reset_index()
    for cc in agg_cols:
        rows[cc] = gb.apply(lambda g, cc=cc: pwm(g, cc)).reset_index(drop=True)
    rows["cell_id"] = cid
    rows["n_tracts"] = rows["n_bgs"]  # rename for compatibility with v0.1 schema
    urban_units.append(rows)

urban_df = pd.concat(urban_units, ignore_index=True)
print(f"  urban+suburban (county,cell) units: {len(urban_df)}")
print(urban_df.groupby("cell_id").size().to_string())

# Combine with v0.1 rural units
rural_df = rural[["state","county","cell_id","pop_in_cell","n_tracts"] + agg_cols].copy()
all_units = pd.concat([urban_df[["state","county","cell_id","pop_in_cell","n_tracts"] + agg_cols],
                       rural_df], ignore_index=True)
print(f"\n[9] Total units: {len(all_units)}  (v0.1: 456 for comparison)")
print(all_units.groupby("cell_id").size().to_string())

# Add outcome + historical features from v0.4
print("\n[10] Joining outcome + historical features ...")
psx = pd.read_parquet(PSX)
psx = psx[psx["intent"]=="FA_Deaths"]
psx["rate_num"] = pd.to_numeric(psx["rate"], errors="coerce")
psx_y = psx[psx["period"].isin(["2019","2020","2021","2022","2023"])]
rate_avg = psx_y.groupby("geoid")["rate_num"].mean().reset_index(name="rate_5yr_avg")
rate_avg["state"] = rate_avg["geoid"].str[:2]
rate_avg["county"] = rate_avg["geoid"].str[2:]

b01c = load_county("B01001")[["state","county","B01001_001E"]].copy()
b01c["pop_county"] = n(b01c["B01001_001E"])

all_units = all_units.merge(rate_avg[["state","county","rate_5yr_avg"]], on=["state","county"], how="left")
all_units = all_units.merge(b01c[["state","county","pop_county"]], on=["state","county"], how="left")
all_units["firearm_deaths_5yr"] = (all_units["rate_5yr_avg"] * all_units["pop_county"] / 100_000 * 5).round().astype("Int64")
all_units["log_exposure"] = np.log(all_units["pop_county"] * 5)
all_units = all_units.dropna(subset=["firearm_deaths_5yr","log_exposure","rate_5yr_avg"]).copy()
all_units = all_units[all_units["firearm_deaths_5yr"]>=0]

# Historical features from v0.4
hist = pd.read_parquet(ROOT / "analysis/historical_features_county_v04.parquet")
all_units = all_units.merge(
    hist[["state","county","holc_share_D","holc_any","vra_section4b",
          "sundown_log1p","sundown_any","sundown_n"]],
    on=["state","county"], how="left")
for c in ["holc_share_D","holc_any","vra_section4b","sundown_log1p","sundown_any","sundown_n"]:
    all_units[c] = all_units[c].fillna(0)
for c in ["holc_any","vra_section4b","sundown_any","sundown_n"]:
    all_units[c] = all_units[c].astype(int)

print(f"  final units: {len(all_units)}")
print(f"  by cell:")
print(all_units.groupby("cell_id").size().to_string())

# Save
all_units.to_parquet(OUT / "design_units_v06.parquet", index=False)

# Sanity comparison vs v0.4
v04 = pd.read_parquet(ROOT / "analysis/production_v0_4/design_units_v04.parquet")
print(f"\n[11] v0.4 vs v0.6 comparison (n_units total, mean pct_black per cell):")
print(f"  v0.4 N={len(v04)}, v0.6 N={len(all_units)}")
for cell in sorted(set(v04["cell_id"]) | set(all_units["cell_id"])):
    v4 = v04[v04["cell_id"]==cell]
    v6 = all_units[all_units["cell_id"]==cell]
    print(f"  {cell}: v0.4 n={len(v4)} pct_black mean={v4['pct_black'].mean():.1f}  |  "
          f"v0.6 n={len(v6)} pct_black mean={v6['pct_black'].mean():.1f}")

print(f"\nSaved: {OUT / 'design_units_v06.parquet'}")
print(f"=== build done in {time.time()-t0:.1f}s ===")
