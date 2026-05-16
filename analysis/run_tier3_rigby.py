"""Tier 3: sundown-source replication using Rigby et al. 2025 dataset
(https://osf.io/fh7r6/, DOI 10.17605/OSF.IO/FH7R6) in place of the
Tougaloo/Loewen scrape used in v0.4.

Method: identical v0.4 hierarchical neg-binom Stan model, identical
covariates, identical cell structure. Only difference: sundown_log1p and
sundown_any are computed from Rigby's canonical Census-linked dataset
(confidence Surely/Probable/Possible, 2,213 entries resolved to 1,084
counties — vs Tougaloo's 950 counties).

Pre-reg comparison: sundown_log1p coefficient under v0.4 was +0.128 [+0.036,
+0.219]. Direction-agreement (positive) is the minimum bar. Magnitude
within v0.4 CI is strong replication. CI must remain clean positive.
"""
import os
RTOOLS = "C:/Users/Nate/.cmdstan/RTools40"
os.environ["PATH"] = f"{RTOOLS}/mingw64/bin;{RTOOLS}/usr/bin;" + os.environ.get("PATH", "")

import pathlib, time, json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")
OUT = ROOT / "analysis/tier3_rigby_2025"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== Tier 3: Rigby 2025 sundown-source replication ===\n")

V01_UNITS = ROOT / "analysis/production_v0_1/design_units.parquet"
units = pd.read_parquet(V01_UNITS)
print(f"loaded v0.1 design_units: {len(units)} county-units")

hist = pd.read_parquet(ROOT / "analysis/historical_features_county_v06_rigby.parquet")
print(f"loaded historical features (Rigby variant): {len(hist)} county rows  "
      f"HOLC={hist['holc_any'].sum()}, VRA={hist['vra_section4b'].sum()}, "
      f"sundown_TG={hist['sundown_any'].sum()}, sundown_RIGBY={hist['sundown_any_rigby'].sum()}")

# Merge in BOTH sundown variants so we can sanity-check correlation
units = units.merge(
    hist[["state","county","holc_share_D","holc_any","vra_section4b",
          "sundown_log1p","sundown_any","sundown_n",
          "sundown_log1p_rigby","sundown_any_rigby","sundown_n_rigby"]],
    on=["state","county"], how="left")
for c in ["holc_share_D","holc_any","vra_section4b",
          "sundown_log1p","sundown_any","sundown_n",
          "sundown_log1p_rigby","sundown_any_rigby","sundown_n_rigby"]:
    units[c] = units[c].fillna(0)
for c in ["holc_any","vra_section4b","sundown_any","sundown_n",
          "sundown_any_rigby","sundown_n_rigby"]:
    units[c] = units[c].astype(int)

# Concordance check between sources
both = (units["sundown_any"]==1) & (units["sundown_any_rigby"]==1)
tg_only = (units["sundown_any"]==1) & (units["sundown_any_rigby"]==0)
rg_only = (units["sundown_any"]==0) & (units["sundown_any_rigby"]==1)
neither = (units["sundown_any"]==0) & (units["sundown_any_rigby"]==0)
print(f"\n[concordance Tougaloo vs Rigby on county-units]:")
print(f"  both flagged:       {both.sum()}")
print(f"  Tougaloo only:      {tg_only.sum()}")
print(f"  Rigby only:         {rg_only.sum()}")
print(f"  neither:            {neither.sum()}")
print(f"  Pearson r (counts): {units['sundown_n'].corr(units['sundown_n_rigby']):.3f}")

CELLS = [("UB-HI","tract","urban"),("UH-HI","tract","urban"),("UW-LI","tract","urban"),
         ("SB-MC","tract","suburban"),("RW-HI","county","rural"),("RB-HI","county","rural"),
         ("RH-HI","county","rural"),("RNA-HI","county","rural")]
cell_to_geo = {c: g for c, _, g in CELLS}
units["geo_type_str"] = units["cell_id"].map(cell_to_geo)
geo_codes = {"urban": 1, "suburban": 2, "rural": 3}
units["geo_type"] = units["geo_type_str"].map(geo_codes)

predictor_cols = ["pct_black","median_hh_income","pct_hs_terminal","pct_bachelors_plus",
                  "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]
X = units[predictor_cols].copy()
for c in predictor_cols: X[c] = (X[c] - X[c].mean()) / X[c].std()
X_arr = X.values

race_centered = X_arr[:, 0]
inequity = units["composite_mean"].values
inequity = (inequity - inequity.mean()) / inequity.std()

y = units["firearm_deaths_5yr"].astype(int).values
log_exp = units["log_exposure"].values
cell_idx = pd.Categorical(units["cell_id"], categories=[c[0] for c in CELLS]).codes + 1

print(f"\n[design] N={len(y)}, K={X_arr.shape[1]}, C=8, G=3")
print(f"  Rigby sundown_log1p range: 0.0 to {units['sundown_log1p_rigby'].max():.2f}  "
      f"non-zero: {(units['sundown_log1p_rigby']>0).sum()}")

units.to_parquet(OUT / "design_units_tier3.parquet", index=False)

print("\n[compile + sample] firing Stan v0.4 model with Rigby sundown ...")
from cmdstanpy import CmdStanModel
model = CmdStanModel(stan_file=str(ROOT / "analysis/fit_production_v0_4.stan"))
fit = model.sample(
    data={
        "N": len(y), "C": 8, "K": X_arr.shape[1], "G": 3,
        "cell": cell_idx.tolist(),
        "geo_type": units["geo_type"].astype(int).tolist(),
        "deaths": y.tolist(),
        "log_exposure": log_exp.tolist(),
        "X": X_arr.tolist(),
        "inequity": inequity.tolist(),
        "race_centered": race_centered.tolist(),
        "holc_share_D": units["holc_share_D"].astype(float).tolist(),
        "holc_any": units["holc_any"].astype(float).tolist(),
        "vra_section4b": units["vra_section4b"].astype(float).tolist(),
        "sundown_log1p": units["sundown_log1p_rigby"].astype(float).tolist(),  # RIGBY
        "sundown_any":   units["sundown_any_rigby"].astype(float).tolist(),     # RIGBY
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260800,
)
print(f"  sampling complete in {time.time()-t0:.1f}s wall")

print("\n[diagnostics]:")
diag = fit.diagnose()
print("  " + str(diag).replace("\n","\n  ")[:800])

post = fit.draws_pd()

def show(name, key):
    b = post[key]
    print(f"  {name:<32} mean={b.mean():+.3f}  sd={b.std():.3f}  "
          f"[{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[Tier 3 key coefficients]:")
show("race x inequity",            "beta_race_x_ineq")
show("HOLC share-D",               "beta_holc_share_D")
show("HOLC any",                   "beta_holc_any")
show("VRA Section 4b",             "beta_vra")
show("SUNDOWN log1p (Rigby)",      "beta_sundown_log1p")
show("SUNDOWN any (Rigby)",        "beta_sundown_any")

# Build result dict for verdict file
result = {
    "tier3_source": "Rigby et al. 2025 (10.17605/OSF.IO/FH7R6)",
    "n_units": int(len(y)),
    "n_counties_flagged_tougaloo": int(units["sundown_any"].sum()),
    "n_counties_flagged_rigby": int(units["sundown_any_rigby"].sum()),
    "wall_sec": time.time()-t0,
    "seed": 20260800,
}
for k, label in [
    ("beta_race_x_ineq",   "race_x_ineq"),
    ("beta_holc_share_D",  "holc_share_D"),
    ("beta_holc_any",      "holc_any"),
    ("beta_vra",           "vra"),
    ("beta_sundown_log1p", "sundown_log1p_rigby"),
    ("beta_sundown_any",   "sundown_any_rigby"),
]:
    b = post[k]
    result[f"{label}_mean"] = float(b.mean())
    result[f"{label}_sd"]   = float(b.std())
    result[f"{label}_q025"] = float(b.quantile(0.025))
    result[f"{label}_q975"] = float(b.quantile(0.975))
    result[f"{label}_ci_clean"] = bool((b.quantile(0.025) > 0) or (b.quantile(0.975) < 0))

with open(OUT / "tier3_summary.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"\n[V0.4 REFERENCES for direct comparison]:")
print(f"  race x inequity (v0.4):     -0.450 [-0.803, -0.133]")
print(f"  HOLC share-D (v0.4):        +0.701 [+0.351, +1.055]")
print(f"  SUNDOWN log1p Tougaloo:     +0.128 [+0.036, +0.219]")

print(f"\nSaved tier3_summary.json + design_units_tier3.parquet")
print(f"=== Tier 3 done in {time.time()-t0:.1f}s ===")
