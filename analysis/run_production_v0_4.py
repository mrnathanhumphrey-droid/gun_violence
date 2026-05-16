"""Production v0.4 - adds sundown towns (Loewen DB) as third historical mechanism
marker on top of v0.3's HOLC + VRA.

Tests whether sundown-towns presence + intensity adds independent predictive power
for county firearm-death rate after controlling for cell + race + inequity + geo +
SES + HOLC + VRA. Final cut at the H_HISTORICAL_MECHANISM disposition for Phase 1.
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
OUT = ROOT / "analysis/production_v0_4"
OUT.mkdir(parents=True, exist_ok=True)

t0 = time.time()
print("=== Production v0.4: sundown towns + HOLC + VRA ===\n")

V01_UNITS = ROOT / "analysis/production_v0_1/design_units.parquet"
units = pd.read_parquet(V01_UNITS)
print(f"loaded v0.1 design_units: {len(units)} county-units")

hist = pd.read_parquet(ROOT / "analysis/historical_features_county_v04.parquet")
print(f"loaded v0.4 historical features: {len(hist)} county rows  "
      f"HOLC={hist['holc_any'].sum()}, VRA={hist['vra_section4b'].sum()}, "
      f"sundown={hist['sundown_any'].sum()}")

units = units.merge(
    hist[["state","county","holc_share_D","holc_any","vra_section4b",
          "sundown_log1p","sundown_any","sundown_n"]],
    on=["state","county"], how="left")
for c in ["holc_share_D","holc_any","vra_section4b","sundown_log1p","sundown_any","sundown_n"]:
    units[c] = units[c].fillna(0)
for c in ["holc_any","vra_section4b","sundown_any","sundown_n"]:
    units[c] = units[c].astype(int)

print(f"\n[merge] units with all historical features:")
print(f"  N={len(units)}  HOLC_any={units['holc_any'].sum()}  "
      f"VRA={units['vra_section4b'].sum()}  sundown_any={units['sundown_any'].sum()}")
print(f"  by cell:")
print(units.groupby("cell_id").agg(
    N=("pop_in_cell","size"),
    HOLC=("holc_any","sum"),
    VRA=("vra_section4b","sum"),
    SDN=("sundown_any","sum")
).to_string())

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
print(f"  sundown_log1p range: 0.0 to {units['sundown_log1p'].max():.2f}  "
      f"non-zero: {(units['sundown_log1p']>0).sum()}")

units.to_parquet(OUT / "design_units_v04.parquet", index=False)

print("\n[compile + sample] firing Stan v0.4 fit ...")
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
    show_progress=False, seed=20260516,
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
show("SUNDOWN log1p (continuous)", "beta_sundown_log1p")
show("SUNDOWN any (binary)", "beta_sundown_any")

print("\n[variance decomposition] (eta_history now includes 5 historical terms)...")
eta_names = ["eta_cell","eta_inequity","eta_race","eta_geo","eta_ses","eta_history"]
N = len(y)
shares_per_draw = {n: [] for n in eta_names}
covar_per_draw = []
n_draws_use = min(500, len(post))
rng = np.random.default_rng(20260516)
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

print("\n[section 6 H_HISTORICAL_MECHANISM final disposition]:")
ci_clean = []
for name, key in [("HOLC share-D","beta_holc_share_D"),
                   ("HOLC any","beta_holc_any"),
                   ("VRA section 4(b)","beta_vra"),
                   ("SUNDOWN log1p","beta_sundown_log1p"),
                   ("SUNDOWN any","beta_sundown_any")]:
    b = post[key]
    lo, hi = b.quantile(0.025), b.quantile(0.975)
    clean = (lo > 0) or (hi < 0)
    ci_clean.append((name, b.mean(), lo, hi, clean))
    print(f"  {name:<24} CI {'CLEAN' if clean else 'spans 0':<8} mean={b.mean():+.3f} [{lo:+.3f}, {hi:+.3f}]")

n_clean = sum(1 for _, _, _, _, c in ci_clean if c)
print(f"\n  {n_clean}/5 historical markers have CI-clean coefficients")

print(f"\n=== v0.4 complete in {time.time()-t0:.1f}s ===")
