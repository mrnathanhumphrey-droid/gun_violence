"""Production v0.3 — adds HOLC + VRA historical mechanism features on top of v0.2.

Tests H_HISTORICAL_MECHANISM disposition from pre-reg section 6.

Skipped from full section 8 spec (data not on disk):
  - Sundown towns (needs 50-state HTML scrape, pending v0.4)
  - Per-geo reporting-rate adjustment (no NVDRS on disk)
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
OUT = ROOT / "analysis/production_v0_3"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== Production v0.3: HOLC + VRA historical mechanism ===\n")

# Reuse v0.1 design_units (which v0.2 also used)
V01_UNITS = ROOT / "analysis/production_v0_1/design_units.parquet"
units = pd.read_parquet(V01_UNITS)
print(f"loaded v0.1 design_units: {len(units)} county-units")

# Join historical features
hist = pd.read_parquet(ROOT / "analysis/historical_features_county.parquet")
print(f"loaded historical features: {len(hist)} county rows  "
      f"HOLC={hist['holc_any'].sum()}, VRA={hist['vra_section4b'].sum()}")

units = units.merge(hist[["state","county","holc_share_D","holc_any","vra_section4b"]],
                    on=["state","county"], how="left")
# Fill any non-matches with 0 (counties not in TIGER list get treated as no-HOLC / no-VRA)
for c in ["holc_share_D","holc_any","vra_section4b"]:
    units[c] = units[c].fillna(0)
units["holc_any"] = units["holc_any"].astype(int)
units["vra_section4b"] = units["vra_section4b"].astype(int)

print(f"\n[merge] v0.1 units with historical features:")
print(f"  N={len(units)}  HOLC_any={units['holc_any'].sum()}  VRA={units['vra_section4b'].sum()}")
print(f"  HOLC_share_D summary among HOLC units: mean={units[units['holc_any']==1]['holc_share_D'].mean():.3f}  "
      f"n>0.20={int((units[units['holc_any']==1]['holc_share_D']>0.20).sum())}")
print(f"  by cell breakdown:")
print(units.groupby("cell_id").agg(N=("pop_in_cell","size"), HOLC=("holc_any","sum"), VRA=("vra_section4b","sum")).to_string())

# Cell + geo encoding (same as v0.2)
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
print(f"  HOLC_share_D non-zero: {int((units['holc_share_D']>0).sum())}")
print(f"  VRA section 4(b): {int(units['vra_section4b'].sum())}")

units.to_parquet(OUT / "design_units_v03.parquet", index=False)

print("\n[compile + sample] firing Stan v0.3 fit...")
from cmdstanpy import CmdStanModel
model = CmdStanModel(stan_file=str(ROOT / "analysis/fit_production_v0_3.stan"))
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
    },
    chains=4, parallel_chains=4,
    iter_warmup=1000, iter_sampling=1000,
    adapt_delta=0.95, max_treedepth=10,
    show_progress=False, seed=20260515,
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

cell_labels = [c[0] for c in CELLS]

print("\n[cell intercepts]:")
for i, cid in enumerate(cell_labels):
    a = post[f"alpha_cell[{i+1}]"]
    print(f"  {cid:<8} mean={a.mean():+.3f}  sd={a.std():.3f}")

print("\n[cell inequity slopes]:")
for i, cid in enumerate(cell_labels):
    b = post[f"beta_inequity_cell[{i+1}]"]
    print(f"  {cid:<8} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[fixed-effect predictors]:")
for i, name in enumerate(predictor_cols):
    b = post[f"beta[{i+1}]"]
    print(f"  {name:<30} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")

print("\n[interactions + historical]:")
def show(name, key):
    b = post[key]
    print(f"  {name:<32} mean={b.mean():+.3f}  sd={b.std():.3f}  [{b.quantile(0.025):+.3f}, {b.quantile(0.975):+.3f}]")
show("race x inequity", "beta_race_x_ineq")
show("geo[urban]", "beta_geo[1]")
show("geo[urban] x inequity", "beta_geo_x_ineq[1]")
show("geo[suburban]", "beta_geo[2]")
show("geo[suburban] x inequity", "beta_geo_x_ineq[2]")
show("HOLC share-D", "beta_holc_share_D")
show("HOLC any (binary)", "beta_holc_any")
show("VRA section 4(b)", "beta_vra")

# Variance decomposition
print("\n[variance decomposition] (eta_history added to v0.2 components)...")
eta_names = ["eta_cell","eta_inequity","eta_race","eta_geo","eta_ses","eta_history"]
N = len(y)
shares_per_draw = {n: [] for n in eta_names}
covar_per_draw = []
n_draws_use = min(500, len(post))
rng = np.random.default_rng(20260515)
draw_idx = rng.choice(len(post), n_draws_use, replace=False)
eta_cols = {n: [f"{n}[{i+1}]" for i in range(N)] for n in eta_names}

for d in draw_idx:
    row = post.iloc[d]
    etas = {n: row[eta_cols[n]].values.astype(float) for n in eta_names}
    eta_sum = sum(etas.values())
    total_var = float(np.var(eta_sum))
    if total_var <= 0: continue
    for n in eta_names:
        shares_per_draw[n].append(float(np.var(etas[n])) / total_var)
    cov_total = sum(2 * float(np.cov(etas[a], etas[b], ddof=0)[0,1])
                    for i, a in enumerate(eta_names) for b in eta_names[i+1:]) / total_var
    covar_per_draw.append(cov_total)

decomp_summary = {}
for n in eta_names:
    v = np.array(shares_per_draw[n])
    decomp_summary[n] = {"mean_share": float(v.mean()), "sd_share": float(v.std()),
                          "q025": float(np.percentile(v, 2.5)), "q975": float(np.percentile(v, 97.5))}
decomp_summary["cross_terms_share"] = {
    "mean_share": float(np.mean(covar_per_draw)), "sd_share": float(np.std(covar_per_draw)),
    "q025": float(np.percentile(covar_per_draw, 2.5)), "q975": float(np.percentile(covar_per_draw, 97.5)),
}
for n, s in decomp_summary.items():
    print(f"  {n:<22} mean share = {s['mean_share']:+.3f}  [{s['q025']:+.3f}, {s['q975']:+.3f}]")

with open(OUT / "variance_decomposition.json", "w") as f:
    json.dump(decomp_summary, f, indent=2)

# section 6 disposition signals
print("\n[section 6 disposition signals]:")
shares = {n: decomp_summary[n]["mean_share"] for n in eta_names}
brxi = post["beta_race_x_ineq"]
print(f"  eta_cell        share = {shares['eta_cell']:+.3f}")
print(f"  eta_race        share = {shares['eta_race']:+.3f}")
print(f"  eta_inequity    share = {shares['eta_inequity']:+.3f}")
print(f"  eta_geo         share = {shares['eta_geo']:+.3f}")
print(f"  eta_history     share = {shares['eta_history']:+.3f}     <-- NEW in v0.3")
print(f"  eta_ses         share = {shares['eta_ses']:+.3f}")
print(f"  race x inequity beta = {brxi.mean():+.3f} [{brxi.quantile(0.025):+.3f}, {brxi.quantile(0.975):+.3f}]")

# H_HISTORICAL_MECHANISM test: any historical coef CI clean of zero AND eta_history share > 1%
hist_ci_clean = []
for name, key in [("HOLC share-D","beta_holc_share_D"),
                   ("HOLC any","beta_holc_any"),
                   ("VRA section 4(b)","beta_vra")]:
    b = post[key]
    lo, hi = b.quantile(0.025), b.quantile(0.975)
    clean = (lo > 0) or (hi < 0)
    hist_ci_clean.append((name, b.mean(), lo, hi, clean))
    print(f"  {name:<24} CI {'CLEAN' if clean else 'spans 0':6}  mean={b.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]")

print(f"\n=== v0.3 complete in {time.time()-t0:.1f}s ===")
