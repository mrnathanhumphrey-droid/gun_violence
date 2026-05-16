"""v0.6 Stan fit: same v0.4 model spec applied to BG-aggregated design.

Tests whether refining cell membership from tract -> block group changes
the three CI-clean structural findings (race x inequity entanglement,
HOLC redlining, sundown towns).
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
OUT = ROOT / "analysis/production_v0_6"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== v0.6: BG-aggregated cell design, v0.4 model spec ===\n")

units = pd.read_parquet(OUT / "design_units_v06.parquet")
print(f"loaded v0.6 design_units: {len(units)} county-units")
print(units.groupby("cell_id").size().to_string())

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
print(f"  HOLC any={units['holc_any'].sum()}, VRA={units['vra_section4b'].sum()}, sundown={units['sundown_any'].sum()}")

print("\n[compile + sample] firing v0.4 Stan model on v0.6 BG design ...")
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
        "sundown_log1p": units["sundown_log1p"].astype(float).tolist(),
        "sundown_any": units["sundown_any"].astype(float).tolist(),
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260900,
)
print(f"  sampling complete in {time.time()-t0:.1f}s wall")

diag = fit.diagnose()
print("\n[diagnostics]:"); print("  " + str(diag).replace("\n","\n  ")[:600])

post = fit.draws_pd()

def show(name, key):
    b = post[key]
    print(f"  {name:<32} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[v0.6 key coefficients]:")
show("race x inequity",            "beta_race_x_ineq")
show("HOLC share-D",               "beta_holc_share_D")
show("HOLC any",                   "beta_holc_any")
show("VRA Section 4b",             "beta_vra")
show("SUNDOWN log1p",              "beta_sundown_log1p")
show("SUNDOWN any",                "beta_sundown_any")

print("\n[v0.4 REFERENCES for comparison]:")
print("  race x inequity (v0.4):     -0.450 [-0.803, -0.133]")
print("  HOLC share-D (v0.4):        +0.701 [+0.351, +1.055]")
print("  SUNDOWN log1p (v0.4):       +0.128 [+0.036, +0.219]")

result = {"version":"v0.6", "n_units": int(len(y)), "wall_sec": time.time()-t0, "seed": 20260900}
for k, label in [
    ("beta_race_x_ineq",   "race_x_ineq"),
    ("beta_holc_share_D",  "holc_share_D"),
    ("beta_holc_any",      "holc_any"),
    ("beta_vra",           "vra"),
    ("beta_sundown_log1p", "sundown_log1p"),
    ("beta_sundown_any",   "sundown_any"),
]:
    b = post[k]
    result[f"{label}_mean"] = float(b.mean())
    result[f"{label}_sd"]   = float(b.std())
    result[f"{label}_q025"] = float(b.quantile(0.025))
    result[f"{label}_q975"] = float(b.quantile(0.975))
    result[f"{label}_ci_clean"] = bool((b.quantile(0.025) > 0) or (b.quantile(0.975) < 0))

with open(OUT / "v06_summary.json", "w") as f:
    json.dump(result, f, indent=2)
print(f"\nSaved v06_summary.json")
print(f"=== v0.6 done in {time.time()-t0:.1f}s ===")
