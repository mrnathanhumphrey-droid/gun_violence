"""v0.5 Arm B: re-fit v0.4 model on each of 5 cell-stratified folds.

For each fold k ∈ {1..5}: fit v0.4 Stan model on the 4 OTHER folds (~365 units).
Save the 3 target coefficients (race × inequity, HOLC share-D, sundown log1p)
and per-cell intercepts/slopes for the pre-reg decision rule.

Usage:
  python run_production_v0_5_fold.py <fold_held_out>   (fold_held_out in 1..5)
"""
import os, sys, pathlib, time, json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
RTOOLS = "C:/Users/Nate/.cmdstan/RTools40"
os.environ["PATH"] = f"{RTOOLS}/mingw64/bin;{RTOOLS}/usr/bin;" + os.environ.get("PATH", "")

import numpy as np
import pandas as pd

if len(sys.argv) < 2:
    sys.exit("Usage: run_production_v0_5_fold.py <fold_held_out>")
fold_id = int(sys.argv[1])
assert fold_id in [1,2,3,4,5], "fold must be 1..5"

ROOT = pathlib.Path(r"D:/Gun Violence")
OUT = ROOT / "analysis/production_v0_5" / f"fold_{fold_id}"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print(f"=== v0.5 Arm B: fold {fold_id} held out, training on other 4 folds ===\n")

# Load v0.4 design + fold assignments
units = pd.read_parquet(ROOT / "analysis/production_v0_4/design_units_v04.parquet")
fold_df = pd.read_csv(ROOT / "analysis/production_v0_5/fold_assignments.csv",
                       dtype={"state":str,"county":str})
units = units.merge(fold_df[["state","county","fold"]], on=["state","county"], how="left")
n_in = (units["fold"] != fold_id).sum()
n_out = (units["fold"] == fold_id).sum()
print(f"  total units: {len(units)}  training (not in fold {fold_id}): {n_in}  held-out: {n_out}")

units_train = units[units["fold"] != fold_id].copy()

# Same cell + geo encoding as v0.4
CELLS = [("UB-HI","tract","urban"),("UH-HI","tract","urban"),("UW-LI","tract","urban"),
         ("SB-MC","tract","suburban"),("RW-HI","county","rural"),("RB-HI","county","rural"),
         ("RH-HI","county","rural"),("RNA-HI","county","rural")]
cell_to_geo = {c: g for c, _, g in CELLS}
units_train["geo_type_str"] = units_train["cell_id"].map(cell_to_geo)
geo_codes = {"urban": 1, "suburban": 2, "rural": 3}
units_train["geo_type"] = units_train["geo_type_str"].map(geo_codes)

predictor_cols = ["pct_black","median_hh_income","pct_hs_terminal","pct_bachelors_plus",
                  "pct_employed_civilian_LF","pct_family_HH","pct_working_age"]
X = units_train[predictor_cols].copy()
for c in predictor_cols: X[c] = (X[c] - X[c].mean()) / X[c].std()
X_arr = X.values

race_centered = X_arr[:, 0]
inequity = units_train["composite_mean"].values
inequity = (inequity - inequity.mean()) / inequity.std()

y = units_train["firearm_deaths_5yr"].astype(int).values
log_exp = units_train["log_exposure"].values
cell_idx = pd.Categorical(units_train["cell_id"], categories=[c[0] for c in CELLS]).codes + 1

units_train.to_parquet(OUT / f"design_units_fold{fold_id}_train.parquet", index=False)

print("\n[compile + sample] firing Stan v0.4 fit on fold-{}-held-out training set ...".format(fold_id))
from cmdstanpy import CmdStanModel
model = CmdStanModel(stan_file=str(ROOT / "analysis/fit_production_v0_4.stan"))
seed_val = 20260700 + fold_id  # per pre-reg
fit = model.sample(
    data={
        "N": len(y), "C": 8, "K": X_arr.shape[1], "G": 3,
        "cell": cell_idx.tolist(),
        "geo_type": units_train["geo_type"].astype(int).tolist(),
        "deaths": y.tolist(),
        "log_exposure": log_exp.tolist(),
        "X": X_arr.tolist(),
        "inequity": inequity.tolist(),
        "race_centered": race_centered.tolist(),
        "holc_share_D": units_train["holc_share_D"].astype(float).tolist(),
        "holc_any": units_train["holc_any"].astype(float).tolist(),
        "vra_section4b": units_train["vra_section4b"].astype(float).tolist(),
        "sundown_log1p": units_train["sundown_log1p"].astype(float).tolist(),
        "sundown_any": units_train["sundown_any"].astype(float).tolist(),
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=seed_val,
)
print(f"  sampling complete in {time.time()-t0:.1f}s wall (seed {seed_val})")

# Diagnostics
diag = fit.diagnose()
print("\n[diagnostics]:")
print("  " + str(diag).replace("\n","\n  ")[:600])

# Save lightweight outputs
post = fit.draws_pd()
target_keys = ["beta_race_x_ineq", "beta_holc_share_D", "beta_sundown_log1p",
               "beta_holc_any", "beta_vra", "beta_sundown_any"]
result = {"fold": fold_id, "n_train": int(n_in), "wall_sec": time.time()-t0, "seed": seed_val}
for k in target_keys:
    b = post[k]
    result[f"{k}_mean"] = float(b.mean())
    result[f"{k}_sd"]   = float(b.std())
    result[f"{k}_q025"] = float(b.quantile(0.025))
    result[f"{k}_q975"] = float(b.quantile(0.975))
    result[f"{k}_ci_clean"] = bool((b.quantile(0.025) > 0) or (b.quantile(0.975) < 0))

# Cell coefs
for i, cid in enumerate([c[0] for c in CELLS]):
    a = post[f"alpha_cell[{i+1}]"]
    s = post[f"beta_inequity_cell[{i+1}]"]
    result[f"alpha_{cid}_mean"] = float(a.mean())
    result[f"beta_inequity_{cid}_mean"] = float(s.mean())
    result[f"beta_inequity_{cid}_q025"] = float(s.quantile(0.025))
    result[f"beta_inequity_{cid}_q975"] = float(s.quantile(0.975))

with open(OUT / f"fold_{fold_id}_summary.json", "w") as f:
    json.dump(result, f, indent=2)
print(f"\n[3 target coefficients on fold {fold_id} training set]:")
for k in ["beta_race_x_ineq", "beta_holc_share_D", "beta_sundown_log1p"]:
    print(f"  {k:<22} mean={result[f'{k}_mean']:+.3f} "
          f"[{result[f'{k}_q025']:+.3f}, {result[f'{k}_q975']:+.3f}]  "
          f"CI {'CLEAN' if result[f'{k}_ci_clean'] else 'spans 0'}")

print(f"\nSaved fold_{fold_id}_summary.json")
print(f"=== fold {fold_id} done in {time.time()-t0:.1f}s ===")
