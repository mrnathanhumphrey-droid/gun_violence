import os
# RTools for Stan compile (mingw32-make) — same path hydrology uses
RTOOLS = "C:/Users/Nate/.cmdstan/RTools40"
os.environ["PATH"] = f"{RTOOLS}/mingw64/bin;{RTOOLS}/usr/bin;" + os.environ.get("PATH", "")

"""Smoke test — UB-HI parent-county aggregate, simple neg-binom GLM.

Validates:
  - Outcome rate construction from psx4-wq38 FA_Deaths
  - Predictor aggregation tract → county
  - Stan model compile + sample
  - Convergence diagnostics + posterior summary

Production fit uses the locked WISQARS source (rescrape with mech=20890 in flight).
This smoke uses psx4-wq38 firearm county data already on disk.
"""
import pathlib, time, json, zipfile
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
PSX = ROOT / "outcomes/wisqars/cdc_psx4_wq38/cdc_county_injury_violence.parquet"
OUT = ROOT / "analysis/smoke_output"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== UB-HI smoke test ===\n")

# ============================================================
# 1. Build tracts frame with cell-assignment (replicate v7 β@0.5)
# ============================================================
print("[1] Building tracts frame with β@0.5 cell assignment...")

def n(s): return pd.to_numeric(s, errors="coerce")
def load(t, g): return pd.read_parquet(ACS / f"acs5_2023_{t}_{g}.parquet")

# Race + pop + poverty + housing
keys = ["state", "county", "tract"]
b01 = load("B01001", "tract")[keys + ["B01001_001E"] + [f"B01001_{i:03d}E" for i in [3,4,5,6,20,21,22,23,24,25,27,28,29,30,44,45,46,47,48,49]]].copy()
for c in b01.columns[len(keys):]: b01[c] = n(b01[c])
b01["pop"] = b01["B01001_001E"]
b01["under18"] = b01[[f"B01001_{i:03d}E" for i in [3,4,5,6,27,28,29,30]]].sum(axis=1)
b01["over65"] = b01[[f"B01001_{i:03d}E" for i in [20,21,22,23,24,25,44,45,46,47,48,49]]].sum(axis=1)
b01["pct_working_age"] = (b01["pop"] - b01["under18"] - b01["over65"]) / b01["pop"] * 100

b02 = load("B02001", "tract")[keys + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
for c in b02.columns[len(keys):]: b02[c] = n(b02[c])
b02 = b02.rename(columns={"B02001_001E":"race_total","B02001_002E":"white","B02001_003E":"black","B02001_004E":"aian"})

b03 = load("B03003", "tract")[keys + ["B03003_001E","B03003_003E"]].copy()
for c in b03.columns[len(keys):]: b03[c] = n(b03[c])
b03 = b03.rename(columns={"B03003_001E":"hisp_total","B03003_003E":"hisp"})

b17 = load("B17001", "tract")[keys + ["B17001_001E","B17001_002E"]].copy()
for c in b17.columns[len(keys):]: b17[c] = n(b17[c])
b17 = b17.rename(columns={"B17001_001E":"pov_denom","B17001_002E":"below_pov"})

b25t = load("B25003", "tract")[keys + ["B25003_001E","B25003_002E"]].copy()
for c in b25t.columns[len(keys):]: b25t[c] = n(b25t[c])
b25t = b25t.rename(columns={"B25003_001E":"ten_total","B25003_002E":"owner_occ"})

b25r = load("B25070", "tract")[keys + ["B25070_001E","B25070_010E"]].copy()
for c in b25r.columns[len(keys):]: b25r[c] = n(b25r[c])
b25r = b25r.rename(columns={"B25070_001E":"rent_denom","B25070_010E":"rent_50plus"})

b19 = load("B19013", "tract")[keys + ["B19013_001E"]].copy()
b19["median_hh_income"] = n(b19["B19013_001E"])

b15 = load("B15003", "tract")[keys + [f"B15003_{i:03d}E" for i in [1,17,18,22,23,24,25]]].copy()
for c in b15.columns[len(keys):]: b15[c] = n(b15[c])
b15["pct_hs_terminal"] = (b15["B15003_017E"]+b15["B15003_018E"]) / b15["B15003_001E"] * 100
b15["pct_bachelors_plus"] = (b15["B15003_022E"]+b15["B15003_023E"]+b15["B15003_024E"]+b15["B15003_025E"]) / b15["B15003_001E"] * 100

b23 = load("B23025", "tract")[keys + ["B23025_001E","B23025_004E"]].copy()
for c in b23.columns[len(keys):]: b23[c] = n(b23[c])
b23["pct_employed_civilian_LF"] = b23["B23025_004E"] / b23["B23025_001E"] * 100

b11 = load("B11001", "tract")[keys + ["B11001_001E","B11001_002E"]].copy()
for c in b11.columns[len(keys):]: b11[c] = n(b11[c])
b11["pct_family_HH"] = b11["B11001_002E"] / b11["B11001_001E"] * 100

tracts = (b01[keys + ["pop","pct_working_age"]]
    .merge(b02[keys + ["race_total","white","black","aian"]], on=keys)
    .merge(b03[keys + ["hisp_total","hisp"]], on=keys)
    .merge(b17[keys + ["pov_denom","below_pov"]], on=keys)
    .merge(b25t[keys + ["ten_total","owner_occ"]], on=keys)
    .merge(b25r[keys + ["rent_denom","rent_50plus"]], on=keys)
    .merge(b19[keys + ["median_hh_income"]], on=keys)
    .merge(b15[keys + ["pct_hs_terminal","pct_bachelors_plus"]], on=keys)
    .merge(b23[keys + ["pct_employed_civilian_LF"]], on=keys)
    .merge(b11[keys + ["pct_family_HH"]], on=keys))

tracts["pct_black"] = tracts["black"] / tracts["race_total"] * 100
tracts["pct_hispanic"] = tracts["hisp"] / tracts["hisp_total"] * 100
tracts["pct_white"] = tracts["white"] / tracts["race_total"] * 100
tracts["pct_nhw_approx"] = tracts["pct_white"] - tracts["pct_hispanic"]
tracts["poverty_rate"] = tracts["below_pov"] / tracts["pov_denom"] * 100
tracts["renter_rate"] = (1 - tracts["owner_occ"] / tracts["ten_total"]) * 100
tracts["rent_burden_pct"] = tracts["rent_50plus"] / tracts["rent_denom"] * 100

# Food + school + health joins
fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state"], fa["county"], fa["tract"] = fa["CensusTract"].str[:2], fa["CensusTract"].str[2:5], fa["CensusTract"].str[5:]
fa["food_inequity_score"] = pd.concat([
    pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0),
    pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
], axis=1).max(axis=1)
tracts = tracts.merge(fa[["state","county","tract","food_inequity_score"]], on=keys, how="left")
tracts["food_inequity_score"] = tracts["food_inequity_score"].fillna(tracts["food_inequity_score"].median())

with zipfile.ZipFile(F33) as zf, zf.open("sdf22_1a.txt") as f:
    f33 = pd.read_csv(f, sep="\t", dtype=str, low_memory=False, usecols=["CONUM","V33","TOTALEXP","SCHLEV"])
f33["enr"] = n(f33["V33"]); f33["te"] = n(f33["TOTALEXP"])
f33 = f33[f33["SCHLEV"].isin(["01","02","03"]) & (f33["enr"]>0) & (f33["te"]>0)]
f33["log_ppe"] = np.log(f33["te"]*1000/f33["enr"])
cppe = f33.groupby("CONUM").apply(lambda g: (g["log_ppe"]*g["enr"]).sum()/g["enr"].sum()).reset_index(name="county_log_ppe")
cppe["state"], cppe["county"] = cppe["CONUM"].str[:2], cppe["CONUM"].str[2:]
tracts = tracts.merge(cppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
tracts["county_log_ppe"] = tracts["county_log_ppe"].fillna(tracts["county_log_ppe"].median())

chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = n(chr_h["Uninsured__% Uninsured"])
chr_h["pcp_rate"] = n(chr_h["Primary Care Physicians__Primary Care Physicians Rate"])
tracts = tracts.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
for c in ["pct_uninsured","pcp_rate"]:
    tracts[c] = tracts[c].fillna(tracts[c].median())

# Urbanicity proxy + within-stratum z-scores
ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

tracts["raw_housing"] = (tracts["rent_burden_pct"] + tracts["renter_rate"]) / 2
tracts["raw_health"] = tracts["pct_uninsured"] - tracts["pcp_rate"] / 100
cols = {"poverty_z":"poverty_rate","food_z":"food_inequity_score","housing_z":"raw_housing",
        "school_z":"county_log_ppe","health_z":"raw_health"}
for z_name, src in cols.items():
    v = tracts[src]
    tracts[z_name] = np.nan
    for s in tracts["urban_class"].dropna().unique():
        m = tracts["urban_class"] == s
        v_s = v[m]
        if v_s.notna().sum() < 2: continue
        tracts.loc[m, z_name] = (v_s - v_s.mean()) / v_s.std()
    if z_name == "school_z":
        tracts[z_name] = -tracts[z_name]
tracts["composite_mean"] = tracts[list(cols.keys())].mean(axis=1)

# UB-HI: urban Black-majority ≥60%, composite_mean ≥ 0.5
ub_hi = tracts[(tracts["urban_class"]=="urban") & (tracts["pop"]>=1500) &
               (tracts["pct_black"]>=60) & (tracts["composite_mean"]>=0.5)].copy()
print(f"  UB-HI tracts: {len(ub_hi):,}")
print(f"  UB-HI distinct parent counties: {ub_hi[['state','county']].drop_duplicates().shape[0]:,}")

# ============================================================
# 2. Aggregate UB-HI tracts to parent counties
# ============================================================
print("\n[2] Aggregating UB-HI tracts to parent counties (pop-weighted)...")
def pwm(g, col):
    """Population-weighted mean."""
    w = g["pop"]; v = g[col]
    return (v * w).sum() / w.sum() if w.sum() > 0 else np.nan

agg_cols = ["composite_mean","pct_black","median_hh_income","pct_hs_terminal","pct_bachelors_plus",
            "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]
parent_counties = ub_hi.groupby(["state","county"]).agg(
    ub_pop=("pop","sum"),
    n_tracts_ubhi=("pop","count"),
).reset_index()
for c in agg_cols:
    pc = ub_hi.groupby(["state","county"]).apply(lambda g: pwm(g, c)).reset_index(name=c)
    parent_counties = parent_counties.merge(pc, on=["state","county"])
print(f"  parent counties: {len(parent_counties):,}")

# ============================================================
# 3. Join psx4-wq38 FA_Deaths outcome
# ============================================================
print("\n[3] Joining psx4-wq38 firearm-death rates (5-year avg)...")
psx = pd.read_parquet(PSX)
psx = psx[psx["intent"]=="FA_Deaths"]
psx["rate_num"] = pd.to_numeric(psx["rate"], errors="coerce")
# Average per-year rate over 2019-2023 per county (rate is per 100k per year)
# Note: rate_m is a flag (0/1) for whether modeled; the actual published rate is in `rate` for both suppressed and unsuppressed cells
psx_y = psx[psx["period"].isin(["2019","2020","2021","2022","2023"])]
rate_avg = psx_y.groupby("geoid")["rate_num"].mean().reset_index(name="rate_m_5yr_avg")
rate_avg["state"] = rate_avg["geoid"].str[:2]
rate_avg["county"] = rate_avg["geoid"].str[2:]

# County-level full pop (from B01001 county table)
b01c = load("B01001","county")[["state","county","B01001_001E"]].copy()
b01c["pop_county"] = n(b01c["B01001_001E"])

parent_counties = parent_counties.merge(rate_avg[["state","county","rate_m_5yr_avg"]], on=["state","county"], how="left")
parent_counties = parent_counties.merge(b01c[["state","county","pop_county"]], on=["state","county"], how="left")

# Outcome: 5-year cumulative firearm death count
# count = rate_per_100k * pop / 100,000 * 5_years
parent_counties["firearm_deaths_5yr"] = (
    parent_counties["rate_m_5yr_avg"] * parent_counties["pop_county"] / 100_000 * 5
).round().astype("Int64")
parent_counties["log_exposure"] = np.log(parent_counties["pop_county"] * 5)  # person-years

# Drop rows with missing outcome
keep = parent_counties.dropna(subset=["firearm_deaths_5yr","log_exposure","rate_m_5yr_avg"]).copy()
print(f"  rows after outcome merge: {len(keep):,}")
print(f"  5-yr deaths summary: min {keep['firearm_deaths_5yr'].min()}, median {keep['firearm_deaths_5yr'].median()}, max {keep['firearm_deaths_5yr'].max()}")
print(f"  5-yr rate summary: min {keep['rate_m_5yr_avg'].min():.1f}, median {keep['rate_m_5yr_avg'].median():.1f}, max {keep['rate_m_5yr_avg'].max():.1f}")

# ============================================================
# 4. Build design matrix
# ============================================================
print("\n[4] Building design matrix (standardized predictors)...")
predictor_cols = ["composite_mean","pct_black","median_hh_income","pct_hs_terminal",
                  "pct_bachelors_plus","pct_employed_civilian_LF","pct_family_HH","pct_working_age"]
X = keep[predictor_cols].copy()
for c in predictor_cols:
    X[c] = (X[c] - X[c].mean()) / X[c].std()
X = X.values

y = keep["firearm_deaths_5yr"].astype(int).values
log_exp = keep["log_exposure"].values

print(f"  X shape: {X.shape}")
print(f"  y range: {y.min()} to {y.max()}")
print(f"  log_exp range: {log_exp.min():.2f} to {log_exp.max():.2f}")

# Save the analysis frame for inspection
keep.to_parquet(OUT / "ubhi_county_aggregate.parquet", index=False)
print(f"  wrote {OUT/'ubhi_county_aggregate.parquet'}")

# ============================================================
# 5. Compile + sample Stan model
# ============================================================
print("\n[5] Compiling Stan model...")
from cmdstanpy import CmdStanModel
stan_path = ROOT / "analysis/smoke_model.stan"
model = CmdStanModel(stan_file=str(stan_path))
print(f"  compiled in {time.time()-t0:.1f}s")

print("\n[6] Sampling (2 chains × 500 warmup + 500 sampling)...")
fit = model.sample(
    data={"N": len(y), "K": X.shape[1], "deaths": y.tolist(),
          "log_exposure": log_exp.tolist(), "X": X.tolist()},
    chains=2, parallel_chains=2,
    iter_warmup=500, iter_sampling=500,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260514,
)
print(f"  sampling complete in {time.time()-t0:.1f}s")

# ============================================================
# 6. Diagnostics + posterior summary
# ============================================================
print("\n[7] Diagnostics + posterior summary...")
diag = fit.diagnose()
print("  diagnose():")
print("    " + str(diag).replace("\n", "\n    ")[:500])

summary = fit.summary()
print("\n  param summary:")
print(summary[["Mean","StdDev","5%","95%","R_hat","ESS_bulk"]].head(20).to_string())

# Save summary
summary.to_csv(OUT / "posterior_summary.csv")
fit.save_csvfiles(dir=str(OUT/"stan_csvs"))

# Per-predictor effect
print("\n  Beta estimates (predictor effects on log firearm-death rate):")
post = fit.draws_pd()
for i, name in enumerate(predictor_cols):
    beta_i = post[f"beta[{i+1}]"]
    print(f"    {name:<30} mean={beta_i.mean():+.3f}  sd={beta_i.std():.3f}  [{beta_i.quantile(0.025):+.3f}, {beta_i.quantile(0.975):+.3f}]")

print(f"\n=== smoke complete in {time.time()-t0:.1f}s ===")
