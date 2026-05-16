"""Production v0.1 — all 8 cells, hierarchical negative-binomial fit.

Extends the smoke pipeline:
  - Adds all 8 cells (was just UB-HI)
  - Cell-level random intercept + random slope on inequity composite
  - Same county-aggregation approach for tract-level cells
  - Same 6 SES + race covariates
  - 4 chains × 1000 warmup + 1000 sampling

Deferred to v0.2:
  - Race × inequity interaction
  - Geo-type × inequity interaction
  - Historical mechanism markers (HOLC, sundown, VRA)
  - Reporting-rate adjustment per geo-type
"""
import os
RTOOLS = "C:/Users/Nate/.cmdstan/RTools40"
os.environ["PATH"] = f"{RTOOLS}/mingw64/bin;{RTOOLS}/usr/bin;" + os.environ.get("PATH", "")

import pathlib, time, json, zipfile
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
PSX = ROOT / "outcomes/wisqars/cdc_psx4_wq38/cdc_county_injury_violence.parquet"
OUT = ROOT / "analysis/production_v0_1"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== Production v0.1: all 8 cells, hierarchical neg-binom ===\n")

# ============================================================
# Same loader as smoke
# ============================================================
def n(s): return pd.to_numeric(s, errors="coerce")
def load(t, g): return pd.read_parquet(ACS / f"acs5_2023_{t}_{g}.parquet")

print("[1] Building tract + county frames (β@0.5 cell assignment)...")

def build(geo):
    keys = ["state","county","tract"] if geo=="tract" else ["state","county"]
    pop = load("B01001", geo)[keys + ["B01001_001E"] + [f"B01001_{i:03d}E" for i in [3,4,5,6,20,21,22,23,24,25,27,28,29,30,44,45,46,47,48,49]]].copy()
    for c in pop.columns[len(keys):]: pop[c] = n(pop[c])
    pop["pop"] = pop["B01001_001E"]
    pop["under18"] = pop[[f"B01001_{i:03d}E" for i in [3,4,5,6,27,28,29,30]]].sum(axis=1)
    pop["over65"] = pop[[f"B01001_{i:03d}E" for i in [20,21,22,23,24,25,44,45,46,47,48,49]]].sum(axis=1)
    pop["pct_working_age"] = (pop["pop"] - pop["under18"] - pop["over65"]) / pop["pop"] * 100

    race = load("B02001", geo)[keys + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
    for c in race.columns[len(keys):]: race[c] = n(race[c])
    race.columns = list(race.columns[:len(keys)]) + ["race_total","white","black","aian"]

    hisp = load("B03003", geo)[keys + ["B03003_001E","B03003_003E"]].copy()
    for c in hisp.columns[len(keys):]: hisp[c] = n(hisp[c])
    hisp.columns = list(hisp.columns[:len(keys)]) + ["hisp_total","hisp"]

    pov = load("B17001", geo)[keys + ["B17001_001E","B17001_002E"]].copy()
    for c in pov.columns[len(keys):]: pov[c] = n(pov[c])
    pov.columns = list(pov.columns[:len(keys)]) + ["pov_denom","below_pov"]

    ten = load("B25003", geo)[keys + ["B25003_001E","B25003_002E"]].copy()
    for c in ten.columns[len(keys):]: ten[c] = n(ten[c])
    ten.columns = list(ten.columns[:len(keys)]) + ["ten_total","owner_occ"]

    rent = load("B25070", geo)[keys + ["B25070_001E","B25070_010E"]].copy()
    for c in rent.columns[len(keys):]: rent[c] = n(rent[c])
    rent.columns = list(rent.columns[:len(keys)]) + ["rent_denom","rent_50plus"]

    inc = load("B19013", geo)[keys + ["B19013_001E"]].copy()
    inc["median_hh_income"] = n(inc["B19013_001E"])

    b15 = load("B15003", geo)[keys + [f"B15003_{i:03d}E" for i in [1,17,18,22,23,24,25]]].copy()
    for c in b15.columns[len(keys):]: b15[c] = n(b15[c])
    b15["pct_hs_terminal"] = (b15["B15003_017E"]+b15["B15003_018E"]) / b15["B15003_001E"] * 100
    b15["pct_bachelors_plus"] = (b15["B15003_022E"]+b15["B15003_023E"]+b15["B15003_024E"]+b15["B15003_025E"]) / b15["B15003_001E"] * 100

    lf = load("B23025", geo)[keys + ["B23025_001E","B23025_004E"]].copy()
    for c in lf.columns[len(keys):]: lf[c] = n(lf[c])
    lf["pct_employed_civilian_LF"] = lf["B23025_004E"] / lf["B23025_001E"] * 100

    hh = load("B11001", geo)[keys + ["B11001_001E","B11001_002E"]].copy()
    for c in hh.columns[len(keys):]: hh[c] = n(hh[c])
    hh["pct_family_HH"] = hh["B11001_002E"] / hh["B11001_001E"] * 100

    df = (pop[keys+["pop","pct_working_age"]]
          .merge(race[keys+["race_total","white","black","aian"]], on=keys)
          .merge(hisp[keys+["hisp_total","hisp"]], on=keys)
          .merge(pov[keys+["pov_denom","below_pov"]], on=keys)
          .merge(ten[keys+["ten_total","owner_occ"]], on=keys)
          .merge(rent[keys+["rent_denom","rent_50plus"]], on=keys)
          .merge(inc[keys+["median_hh_income"]], on=keys)
          .merge(b15[keys+["pct_hs_terminal","pct_bachelors_plus"]], on=keys)
          .merge(lf[keys+["pct_employed_civilian_LF"]], on=keys)
          .merge(hh[keys+["pct_family_HH"]], on=keys))
    df["pct_black"] = df["black"]/df["race_total"]*100
    df["pct_hispanic"] = df["hisp"]/df["hisp_total"]*100
    df["pct_nhw_approx"] = df["white"]/df["race_total"]*100 - df["pct_hispanic"]
    df["pct_aian"] = df["aian"]/df["race_total"]*100
    df["poverty_rate"] = df["below_pov"]/df["pov_denom"]*100
    df["renter_rate"] = (1 - df["owner_occ"]/df["ten_total"])*100
    df["rent_burden_pct"] = df["rent_50plus"]/df["rent_denom"]*100
    return df

tracts = build("tract")
counties = build("county")
print(f"  tracts: {len(tracts):,}  counties: {len(counties):,}")

# Food + school + health
print("[2] Joining inequity dimensions (USDA + F-33 + CHR)...")
fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state"], fa["county"], fa["tract"] = fa["CensusTract"].str[:2], fa["CensusTract"].str[2:5], fa["CensusTract"].str[5:]
fa["food_inequity_score"] = pd.concat([
    pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0),
    pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
], axis=1).max(axis=1)
fa["pop_2010"] = pd.to_numeric(fa["Pop2010"], errors="coerce").fillna(0)
tracts = tracts.merge(fa[["state","county","tract","food_inequity_score"]], on=["state","county","tract"], how="left")
tracts["food_inequity_score"] = tracts["food_inequity_score"].fillna(tracts["food_inequity_score"].median())
fa_county = fa.groupby(["state","county"]).apply(
    lambda g: (g["food_inequity_score"]*g["pop_2010"]).sum() / max(g["pop_2010"].sum(),1)
).reset_index(name="food_inequity_score")
counties = counties.merge(fa_county, on=["state","county"], how="left")
counties["food_inequity_score"] = counties["food_inequity_score"].fillna(counties["food_inequity_score"].median())

with zipfile.ZipFile(F33) as zf, zf.open("sdf22_1a.txt") as f:
    f33 = pd.read_csv(f, sep="\t", dtype=str, low_memory=False, usecols=["CONUM","V33","TOTALEXP","SCHLEV"])
f33["enr"] = n(f33["V33"]); f33["te"] = n(f33["TOTALEXP"])
f33 = f33[f33["SCHLEV"].isin(["01","02","03"]) & (f33["enr"]>0) & (f33["te"]>0)]
f33["log_ppe"] = np.log(f33["te"]*1000/f33["enr"])
cppe = f33.groupby("CONUM").apply(lambda g: (g["log_ppe"]*g["enr"]).sum()/g["enr"].sum()).reset_index(name="county_log_ppe")
cppe["state"], cppe["county"] = cppe["CONUM"].str[:2], cppe["CONUM"].str[2:]
tracts = tracts.merge(cppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
counties = counties.merge(cppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
for df in [tracts, counties]: df["county_log_ppe"] = df["county_log_ppe"].fillna(df["county_log_ppe"].median())

chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = n(chr_h["Uninsured__% Uninsured"])
chr_h["pcp_rate"] = n(chr_h["Primary Care Physicians__Primary Care Physicians Rate"])
tracts = tracts.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
counties = counties.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
for df in [tracts, counties]:
    for c in ["pct_uninsured","pcp_rate"]:
        df[c] = df[c].fillna(df[c].median())

# Urbanicity proxy
ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])
counties = counties.merge(ct, on=["state","county"], how="left")
counties["n_tracts"] = counties["n_tracts"].fillna(0)
counties["urban_class"] = pd.cut(counties["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

# β@0.5 standardization (within urbanicity stratum)
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

tracts = standardize_beta(tracts)
counties = standardize_beta(counties)

# Cell assignment under β@0.5
print("[3] Cell assignment...")
def elig(t, c):
    t_e = t[t["pop"]>=1500].copy()
    c_e = c[c["pop"]>=3000].copy()
    return t_e[t_e["urban_class"]=="urban"], t_e[t_e["urban_class"]=="suburban"], c_e

u, s, c = elig(tracts, counties)

CELLS = [
    ("UB-HI", "u", lambda d: d["pct_black"] >= 60, "HI"),
    ("UH-HI", "u", lambda d: d["pct_hispanic"] >= 60, "HI"),
    ("UW-LI", "u", lambda d: d["pct_nhw_approx"] >= 70, "LI"),
    ("SB-MC", "s", lambda d: d["pct_black"] >= 60, "MC"),
    ("RW-HI", "c", lambda d: d["pct_nhw_approx"] >= 80, "HI"),
    ("RB-HI", "c", lambda d: d["pct_black"] >= 50, "HI"),
    ("RH-HI", "c", lambda d: d["pct_hispanic"] >= 50, "HI"),
    ("RNA-HI", "c", lambda d: d["pct_aian"] >= 40, "HI"),
]

THRESHOLD = 0.5
all_cells = []
for cid, base_key, race_fn, tier in CELLS:
    base_df = {"u": u, "s": s, "c": c}[base_key]
    if tier == "HI":
        sel = race_fn(base_df) & (base_df["composite_mean"] >= THRESHOLD)
    elif tier == "LI":
        sel = race_fn(base_df) & (base_df["composite_mean"] <= -THRESHOLD/2)
    else:
        sel = race_fn(base_df) & (base_df["composite_mean"] > -THRESHOLD/2) & (base_df["composite_mean"] < THRESHOLD)
    sub = base_df[sel].copy()
    sub["cell_id"] = cid
    sub["cell_geo"] = "tract" if base_key in ("u","s") else "county"
    all_cells.append(sub)
    print(f"  {cid}: {len(sub):,} {'tracts' if base_key in ('u','s') else 'counties'}")

cells_df = pd.concat(all_cells, ignore_index=True)

# Aggregate tract-level cells to parent county
print("\n[4] Aggregating tract-level cells to parent counties...")
def pwm(g, col):
    w = g["pop"]; v = g[col]
    return (v*w).sum() / w.sum() if w.sum()>0 else np.nan

agg_cols = ["composite_mean","pct_black","pct_hispanic","pct_nhw_approx","pct_aian",
            "median_hh_income","pct_hs_terminal","pct_bachelors_plus",
            "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]

unit_rows = []
for cid, sub in cells_df.groupby("cell_id"):
    if sub["cell_geo"].iloc[0] == "tract":
        gb = sub.groupby(["state","county"])
        agg = gb.agg(pop_in_cell=("pop","sum"), n_tracts=("pop","count")).reset_index()
        for cc in agg_cols:
            pc = gb.apply(lambda g: pwm(g, cc)).reset_index(name=cc)
            agg = agg.merge(pc, on=["state","county"])
        agg["cell_id"] = cid
        unit_rows.append(agg)
    else:
        sub = sub.rename(columns={"pop":"pop_in_cell"})
        sub["n_tracts"] = 1
        unit_rows.append(sub[["state","county","pop_in_cell","n_tracts"] + agg_cols + ["cell_id"]])

units = pd.concat(unit_rows, ignore_index=True)
print(f"  county-level units across all cells: {len(units):,}")
print(units.groupby("cell_id").size().to_string())

# Join WISQARS rate (psx4-wq38) — outcome
print("\n[5] Joining outcome (psx4-wq38 FA_Deaths rate 2019-2023 avg)...")
psx = pd.read_parquet(PSX)
psx = psx[psx["intent"]=="FA_Deaths"]
psx["rate_num"] = pd.to_numeric(psx["rate"], errors="coerce")
psx_y = psx[psx["period"].isin(["2019","2020","2021","2022","2023"])]
rate_avg = psx_y.groupby("geoid")["rate_num"].mean().reset_index(name="rate_5yr_avg")
rate_avg["state"] = rate_avg["geoid"].str[:2]
rate_avg["county"] = rate_avg["geoid"].str[2:]

b01c = load("B01001","county")[["state","county","B01001_001E"]].copy()
b01c["pop_county"] = n(b01c["B01001_001E"])

units = units.merge(rate_avg[["state","county","rate_5yr_avg"]], on=["state","county"], how="left")
units = units.merge(b01c[["state","county","pop_county"]], on=["state","county"], how="left")
units["firearm_deaths_5yr"] = (units["rate_5yr_avg"] * units["pop_county"] / 100_000 * 5).round().astype("Int64")
units["log_exposure"] = np.log(units["pop_county"] * 5)

units = units.dropna(subset=["firearm_deaths_5yr","log_exposure","rate_5yr_avg"]).copy()
units = units[units["firearm_deaths_5yr"]>=0]
print(f"  units after outcome merge: {len(units):,}")

# Build design matrix
predictor_cols = ["pct_black","median_hh_income","pct_hs_terminal","pct_bachelors_plus",
                  "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]
X = units[predictor_cols].copy()
for ccol in predictor_cols: X[ccol] = (X[ccol] - X[ccol].mean()) / X[ccol].std()
X = X.values

inequity = units["composite_mean"].values
# Center but don't rescale (already z-scored)
inequity = (inequity - inequity.mean()) / inequity.std()

y = units["firearm_deaths_5yr"].astype(int).values
log_exp = units["log_exposure"].values
cell_idx = pd.Categorical(units["cell_id"], categories=[c[0] for c in CELLS]).codes + 1  # 1-indexed for Stan

print(f"\n[6] design matrix: N={len(y)}, K={X.shape[1]}, C={cell_idx.max()}")
print(f"  cells: {dict(zip([c[0] for c in CELLS], np.bincount(cell_idx, minlength=9)[1:]))}")
print(f"  y range: {y.min()} to {y.max()}")
print(f"  median y: {np.median(y):.0f}")

units.to_parquet(OUT / "design_units.parquet", index=False)

# Compile + sample
print("\n[7] Compiling + sampling Stan model...")
from cmdstanpy import CmdStanModel
model = CmdStanModel(stan_file=str(ROOT / "analysis/fit_production.stan"))
fit = model.sample(
    data={
        "N": len(y), "C": 8, "K": X.shape[1],
        "cell": cell_idx.tolist(), "deaths": y.tolist(),
        "log_exposure": log_exp.tolist(), "X": X.tolist(),
        "inequity": inequity.tolist(),
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260514,
)
print(f"  sampling complete in {time.time()-t0:.1f}s wall")

# Diagnostics
print("\n[8] Diagnostics + key posteriors:")
diag = fit.diagnose()
print("  " + str(diag).replace("\n","\n  ")[:600])

summary = fit.summary()
summary.to_csv(OUT / "posterior_summary.csv")
fit.save_csvfiles(dir=str(OUT/"stan_csvs"))

post = fit.draws_pd()

# Key parameters of interest
print("\n[9] Cell-level inequity slopes (beta_inequity_cell):")
cell_labels = [c[0] for c in CELLS]
for i, cid in enumerate(cell_labels):
    b = post[f"beta_inequity_cell[{i+1}]"]
    print(f"  {cid:<8} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[10] Cell intercepts (alpha_cell, log-rate scale):")
for i, cid in enumerate(cell_labels):
    a = post[f"alpha_cell[{i+1}]"]
    print(f"  {cid:<8} mean={a.mean():+.3f}  sd={a.std():.3f}")

print("\n[11] Fixed-effect predictor coefficients:")
for i, name in enumerate(predictor_cols):
    b = post[f"beta[{i+1}]"]
    print(f"  {name:<30} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print(f"\n=== production v0.1 complete in {time.time()-t0:.1f}s ===")
