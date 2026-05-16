"""Production v0.2 — extends v0.1 with race x inequity + geo x inequity interactions
plus decomposed log-mu components for variance-decomposition test of pre-reg
section 6 hypothesis dispositions.

Skipped vs full section 8 spec (data not on disk):
  - HOLC redlining: no TIGER county shapefile available to join HOLC polygons
  - Sundown towns: raw HTML page, parser not built
  - VRA preclearance: directory empty
  - Reporting-rate adjustment: no calibration data
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
OUT = ROOT / "analysis/production_v0_2"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== Production v0.2: race x ineq + geo x ineq + variance decomp ===\n")

# Reuse v0.1 design_units (already has all the cell assignments + aggregations)
V01_UNITS = ROOT / "analysis/production_v0_1/design_units.parquet"
units = pd.read_parquet(V01_UNITS)
print(f"loaded v0.1 design_units: {len(units)} county-units")
print(units.groupby("cell_id").size().to_string())

# CELLS list from v0.1 (with geo mapping)
CELLS = [
    ("UB-HI",  "tract",  "urban"),
    ("UH-HI",  "tract",  "urban"),
    ("UW-LI",  "tract",  "urban"),
    ("SB-MC",  "tract",  "suburban"),
    ("RW-HI",  "county", "rural"),
    ("RB-HI",  "county", "rural"),
    ("RH-HI",  "county", "rural"),
    ("RNA-HI", "county", "rural"),
]
cell_to_geo = {c: g for c, _, g in CELLS}
units["geo_type_str"] = units["cell_id"].map(cell_to_geo)
geo_codes = {"urban": 1, "suburban": 2, "rural": 3}
units["geo_type"] = units["geo_type_str"].map(geo_codes)

# Predictors (same order as v0.1: pct_black FIRST, then SES)
predictor_cols = ["pct_black", "median_hh_income", "pct_hs_terminal", "pct_bachelors_plus",
                  "pct_employed_civilian_LF", "pct_family_HH", "pct_working_age"]
X = units[predictor_cols].copy()
X_mean = X.mean()
X_std = X.std()
for c in predictor_cols:
    X[c] = (X[c] - X_mean[c]) / X_std[c]
X_arr = X.values

# race_centered = standardized pct_black (same as X[:, 0])
race_centered = X_arr[:, 0]

inequity = units["composite_mean"].values
inequity = (inequity - inequity.mean()) / inequity.std()

y = units["firearm_deaths_5yr"].astype(int).values
log_exp = units["log_exposure"].values
cell_idx = pd.Categorical(units["cell_id"],
                           categories=[c[0] for c in CELLS]).codes + 1

print(f"\n[design] N={len(y)}, K={X_arr.shape[1]}, C=8, G=3")
print(f"  geo type counts: {pd.Series(units['geo_type_str']).value_counts().to_dict()}")
print(f"  y range: {y.min()} to {y.max()}  median: {np.median(y):.0f}")

units.to_parquet(OUT / "design_units_v02.parquet", index=False)

print("\n[compile + sample] firing Stan v0.2 fit ...")
from cmdstanpy import CmdStanModel
model = CmdStanModel(stan_file=str(ROOT / "analysis/fit_production_v0_2.stan"))
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
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260514,
)
print(f"  sampling complete in {time.time()-t0:.1f}s wall")

print("\n[diagnostics]:")
diag = fit.diagnose()
print("  " + str(diag).replace("\n","\n  ")[:800])

summary = fit.summary()
summary.to_csv(OUT / "posterior_summary.csv")
fit.save_csvfiles(dir=str(OUT/"stan_csvs"))

post = fit.draws_pd()
post.to_parquet(OUT / "posterior_full.parquet")
print(f"  posterior parquet: {post.shape}")

print("\n[cell intercepts] (alpha_cell):")
cell_labels = [c[0] for c in CELLS]
for i, cid in enumerate(cell_labels):
    a = post[f"alpha_cell[{i+1}]"]
    print(f"  {cid:<8} mean={a.mean():+.3f}  sd={a.std():.3f}")

print("\n[cell inequity slopes] (beta_inequity_cell):")
for i, cid in enumerate(cell_labels):
    b = post[f"beta_inequity_cell[{i+1}]"]
    print(f"  {cid:<8} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[fixed-effect predictors] (beta):")
for i, name in enumerate(predictor_cols):
    b = post[f"beta[{i+1}]"]
    print(f"  {name:<30} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[interactions]:")
brxi = post["beta_race_x_ineq"]
print(f"  race x inequity:                     mean={brxi.mean():+.3f}  sd={brxi.std():.3f}  [{brxi.quantile(0.025):+.3f}, {brxi.quantile(0.975):+.3f}]")
for k, g in [(1,"urban"),(2,"suburban")]:
    bg = post[f"beta_geo[{k}]"]
    bgi = post[f"beta_geo_x_ineq[{k}]"]
    print(f"  geo[{g}]:                          mean={bg.mean():+.3f}  sd={bg.std():.3f}  [{bg.quantile(0.025):+.3f}, {bg.quantile(0.975):+.3f}]")
    print(f"  geo[{g}] x inequity:               mean={bgi.mean():+.3f}  sd={bgi.std():.3f}  [{bgi.quantile(0.025):+.3f}, {bgi.quantile(0.975):+.3f}]")

# Variance decomposition: for each posterior draw, get var of each eta component
# across units, and shares = var_component / total_var. Averaged across draws.
print("\n[variance decomposition] (across units, posterior mean of variance share)...")
eta_names = ["eta_cell", "eta_inequity", "eta_race", "eta_geo", "eta_ses"]
N = len(y)

shares_per_draw = {n: [] for n in eta_names}
total_var_per_draw = []
covar_per_draw = []  # the covariance cross-terms

# Sample 500 random posterior draws to keep memory in check
n_draws_use = min(500, len(post))
rng = np.random.default_rng(20260514)
draw_idx = rng.choice(len(post), n_draws_use, replace=False)

# Build column matrices once
eta_cols = {n: [f"{n}[{i+1}]" for i in range(N)] for n in eta_names}

for d in draw_idx:
    row = post.iloc[d]
    etas = {n: row[eta_cols[n]].values.astype(float) for n in eta_names}
    eta_sum = sum(etas.values())
    total_var = float(np.var(eta_sum))
    if total_var <= 0:
        continue
    total_var_per_draw.append(total_var)
    for n in eta_names:
        shares_per_draw[n].append(float(np.var(etas[n])) / total_var)
    # Cross-covariance contribution to total
    cov_total = sum(2 * float(np.cov(etas[a], etas[b], ddof=0)[0,1])
                    for i, a in enumerate(eta_names) for b in eta_names[i+1:]) / total_var
    covar_per_draw.append(cov_total)

decomp_summary = {}
for n in eta_names:
    v = np.array(shares_per_draw[n])
    decomp_summary[n] = {
        "mean_share": float(v.mean()),
        "sd_share": float(v.std()),
        "q025": float(np.percentile(v, 2.5)),
        "q975": float(np.percentile(v, 97.5)),
    }
decomp_summary["cross_terms_share"] = {
    "mean_share": float(np.mean(covar_per_draw)),
    "sd_share": float(np.std(covar_per_draw)),
    "q025": float(np.percentile(covar_per_draw, 2.5)),
    "q975": float(np.percentile(covar_per_draw, 97.5)),
}

for n, s in decomp_summary.items():
    print(f"  {n:<22} mean share = {s['mean_share']:+.3f}  [{s['q025']:+.3f}, {s['q975']:+.3f}]")

with open(OUT / "variance_decomposition.json", "w") as f:
    json.dump(decomp_summary, f, indent=2)
print(f"\nwrote {OUT}/variance_decomposition.json")

# Section 6 disposition logic (pre-reg style):
# H_INEQUITY (pure):           eta_inequity dominant, eta_race share small
# H_RACE_PURE:                  eta_race dominant, eta_inequity share small
# H_INTERACTION:                race x inequity coef material + variance share noticeable
# H_GEOGRAPHIC_MECHANISM:       eta_geo + geo x ineq share material
# H_HISTORICAL_MECHANISM:       not testable in v0.2 (HOLC deferred)
print("\n[section 6 disposition signals]")
ineq_share = decomp_summary["eta_inequity"]["mean_share"]
race_share = decomp_summary["eta_race"]["mean_share"]
cell_share = decomp_summary["eta_cell"]["mean_share"]
geo_share = decomp_summary["eta_geo"]["mean_share"]
ses_share = decomp_summary["eta_ses"]["mean_share"]
race_x_share = abs(brxi.mean())  # rough proxy: was race x ineq coef material

print(f"  eta_inequity share (cell-level partial pooling on composite): {ineq_share:+.3f}")
print(f"  eta_race share (pct_black main + race x ineq):                  {race_share:+.3f}")
print(f"  eta_cell share (cell baseline + grand intercept):              {cell_share:+.3f}")
print(f"  eta_geo share (geo main + geo x ineq):                          {geo_share:+.3f}")
print(f"  eta_ses share (remaining SES):                                  {ses_share:+.3f}")
print(f"  race x inequity beta:                                           {brxi.mean():+.3f}  [{brxi.quantile(0.025):+.3f}, {brxi.quantile(0.975):+.3f}]")

print(f"\n=== v0.2 complete in {time.time()-t0:.1f}s ===")
