"""META-ANALYSIS — pre-registration §5.2-§5.5 and §9. The last pre-registered step.

WHAT IS POOLED, AND WHAT IS NOT

  §5.2 forbids pooling raw counts across cities. That procedure already failed in this
  project: the national GVA estimate was carried by large cities while the within-city
  paired test was null at p = 0.63. This file pools LOG RATE RATIOS by DerSimonian-Laird
  random effects and reports tau^2, I^2 and a PREDICTION INTERVAL -- the last of these
  because with heterogeneity this large the pooled CI describes the average of seven
  cities, not what an eighth city would show.

  §5.3 primary      250 m band, 2019-2023, DL random effects over all included cities
  §5.4 CO-PRIMARY   the same with CHICAGO REMOVED -- Chicago generated the hypothesis and
                    cannot confirm it, and under A2.3 it no longer survives on its own
  §5.5 sensitivity  other bands, fixed effects, leave-one-city-out, Seattle excluded
  §6   condition    the sham-boundary pooled RR must CONTAIN 1
  §9   decision     H1 needs primary CI excluding 1, co-primary CI excluding 1, AND the
                    sham CI containing 1

  Standard errors come from the design-based block bootstrap per Amendment 2. The
  pre-registered analytic SE is pooled alongside so the effect of that change is visible.

    python displacement/meta_analysis.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import ROOT

BAND = 250


def dl(y, v):
    """DerSimonian-Laird random effects on log RR.
    Returns dict with pooled estimate, CI, tau^2, I^2, Q, and prediction interval."""
    y, v = np.asarray(y, float), np.asarray(v, float)
    k = len(y)
    wf = 1 / v
    mu_f = np.sum(wf * y) / np.sum(wf)
    Q = float(np.sum(wf * (y - mu_f) ** 2))
    df = k - 1
    C = np.sum(wf) - np.sum(wf ** 2) / np.sum(wf)
    tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    w = 1 / (v + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    se = float(np.sqrt(1 / np.sum(w)))
    I2 = max(0.0, 100 * (Q - df) / Q) if Q > 0 else 0.0
    out = dict(k=k, mu=mu, se=se, lo=mu - 1.96 * se, hi=mu + 1.96 * se,
               tau2=tau2, I2=I2, Q=Q, p_Q=float(1 - stats.chi2.cdf(Q, df)) if df > 0 else np.nan)
    # prediction interval: what a NEW city would show (Higgins-Thompson-Spiegelhalter)
    if k > 2 and tau2 > 0:
        t = stats.t.ppf(0.975, k - 2)
        half = t * np.sqrt(tau2 + se ** 2)
        out["pi_lo"], out["pi_hi"] = mu - half, mu + half
    else:
        out["pi_lo"], out["pi_hi"] = np.nan, np.nan
    # fixed effect, for §5.5
    out["fe_mu"] = float(mu_f)
    out["fe_se"] = float(np.sqrt(1 / np.sum(wf)))
    return out


def show(lab, r, indent="  "):
    ex = np.exp
    s = (f"{indent}{lab:<34} k={r['k']}  RR {ex(r['mu']):.3f} "
         f"[{ex(r['lo']):.3f}, {ex(r['hi']):.3f}]   "
         f"tau2={r['tau2']:.4f}  I2={r['I2']:.1f}%")
    if np.isfinite(r["pi_lo"]):
        s += f"   PI [{ex(r['pi_lo']):.3f}, {ex(r['pi_hi']):.3f}]"
    print(s)
    return r


def main():
    """Runner, guarded so dl() can be imported without re-running the pooling."""
    # ------------------------------------------------------------------ inputs
    band = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
    band = band[band.band == BAND].copy()
    boot = pd.read_csv(ROOT / f"displacement/block_bootstrap_{BAND}m.csv")
    sham = pd.read_csv(ROOT / "displacement/sham_boundary_summary.csv")

    d = band.merge(boot[["city", "lo_boot", "hi_boot", "eff_clusters"]], on="city", how="left")
    d = d.merge(sham[["city", "p_perm", "sham_median"]], on="city", how="left")
    d["y"] = np.log(d.rr)
    d["v_analytic"] = d.se_log_rr ** 2
    d["se_boot"] = (np.log(d.hi_boot) - np.log(d.lo_boot)) / (2 * 1.96)   # Amendment 2
    d["v_boot"] = d.se_boot ** 2

    print("=" * 108)
    print(f"META-ANALYSIS — §5.2-§5.5, §9.   band {BAND} m, window 2019-2023")
    print("=" * 108)
    print("\nPER-CITY INPUTS (bootstrap SE per Amendment 2; analytic shown for comparison)")
    print(d[["city", "n_D", "n_C", "rr", "lo", "hi", "lo_boot", "hi_boot",
             "se_log_rr", "se_boot", "eff_clusters", "p_perm", "included"]]
          .round(3).to_string(index=False))

    # §4.4/§4.7 inclusion was decided on geometry/coordinates, never on an outcome
    inc = d[d.included].copy()
    excl = d[~d.included]
    if len(excl):
        print(f"\nexcluded by pre-registered mechanical rules: "
              f"{[(c, e) for c, e in zip(excl.city, excl.exclusion)]}")

    print("\n" + "=" * 108)
    print("POOLED — DerSimonian-Laird random effects on log RR")
    print("=" * 108)
    print("\n  [Amendment 2 — design-based bootstrap SE]")
    primary = show("§5.3 PRIMARY (all included)", dl(inc.y, inc.v_boot))
    noChi = inc[inc.city != "Chicago"]
    coprim = show("§5.4 CO-PRIMARY (no Chicago)", dl(noChi.y, noChi.v_boot))

    print("\n  [pre-registered analytic SE — superseded, shown for transparency]")
    show("§5.3 primary, analytic SE", dl(inc.y, inc.v_analytic))
    show("§5.4 co-primary, analytic SE", dl(noChi.y, noChi.v_analytic))

    print("\n" + "=" * 108)
    print("§5.5 SENSITIVITY")
    print("=" * 108)
    fe = dl(inc.y, inc.v_boot)
    print(f"  fixed effect (bootstrap SE)          RR {np.exp(fe['fe_mu']):.3f} "
          f"[{np.exp(fe['fe_mu']-1.96*fe['fe_se']):.3f}, {np.exp(fe['fe_mu']+1.96*fe['fe_se']):.3f}]"
          f"   Q={fe['Q']:.1f}  p={fe['p_Q']:.4g}")
    noSea = inc[inc.city != "Seattle"]
    show("Seattle excluded (§8 flagged)", dl(noSea.y, noSea.v_boot))
    info = inc[~inc.city.isin(["Baltimore", "Detroit", "Seattle"])]
    show("uninformative 3 excluded (A2.5)", dl(info.y, info.v_boot))

    print("\n  leave-one-city-out:")
    for c in inc.city:
        s = inc[inc.city != c]
        r = dl(s.y, s.v_boot)
        print(f"    without {c:<14} RR {np.exp(r['mu']):.3f} "
              f"[{np.exp(r['lo']):.3f}, {np.exp(r['hi']):.3f}]  tau2={r['tau2']:.4f}")

    print("\n  other bands (bootstrap SEs are only available at the primary band, so these")
    print("  use the pre-registered analytic SE and are INDICATIVE ONLY):")
    allb = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
    for b in (150, 500, 1000):
        s = allb[(allb.band == b) & allb.included].copy()
        if len(s) < 3:
            continue
        s["y"] = np.log(s.rr)
        r = dl(s.y, s.se_log_rr ** 2)
        print(f"    {b:>5} m   k={r['k']}  RR {np.exp(r['mu']):.3f} "
              f"[{np.exp(r['lo']):.3f}, {np.exp(r['hi']):.3f}]  I2={r['I2']:.1f}%")

    # ------------------------------------------------------------------ §6 / §9
    print("\n" + "=" * 108)
    print("§6 SHAM-BOUNDARY CONDITION")
    print("=" * 108)
    sh = sham.dropna(subset=["sham_median"]).copy()
    sh["y"] = np.log(sh.sham_median)
    # spread of the sham distribution as its standard error
    sh["v"] = ((np.log(sh.sham_p95) - np.log(sh.sham_p05)) / (2 * 1.645)) ** 2
    shr = dl(sh.y, sh.v)
    print(f"  pooled sham RR {np.exp(shr['mu']):.3f} "
          f"[{np.exp(shr['lo']):.3f}, {np.exp(shr['hi']):.3f}]   "
          f"contains 1: {np.exp(shr['lo']) <= 1 <= np.exp(shr['hi'])}")

    print("\n" + "=" * 108)
    print("§9 DECISION")
    print("=" * 108)
    c1 = not (np.exp(primary["lo"]) <= 1 <= np.exp(primary["hi"]))
    c2 = not (np.exp(coprim["lo"]) <= 1 <= np.exp(coprim["hi"]))
    c3 = np.exp(shr["lo"]) <= 1 <= np.exp(shr["hi"])
    print(f"  (1) primary CI excludes 1 ............ {c1}   "
          f"RR {np.exp(primary['mu']):.3f} [{np.exp(primary['lo']):.3f}, {np.exp(primary['hi']):.3f}]")
    print(f"  (2) co-primary (no Chicago) excludes 1  {c2}   "
          f"RR {np.exp(coprim['mu']):.3f} [{np.exp(coprim['lo']):.3f}, {np.exp(coprim['hi']):.3f}]")
    print(f"  (3) sham CI contains 1 ............... {c3}   "
          f"RR {np.exp(shr['mu']):.3f} [{np.exp(shr['lo']):.3f}, {np.exp(shr['hi']):.3f}]")
    print(f"\n  H1 {'SUPPORTED' if (c1 and c2 and c3) else 'NOT SUPPORTED'} under §9")
    print(f"\n  heterogeneity: tau2={primary['tau2']:.4f}  I2={primary['I2']:.1f}%  "
          f"Q={primary['Q']:.1f} (p={primary['p_Q']:.4g})")
    if np.isfinite(primary["pi_lo"]):
        print(f"  PREDICTION INTERVAL for a new city: "
              f"[{np.exp(primary['pi_lo']):.3f}, {np.exp(primary['pi_hi']):.3f}]"
              "  <- what an eighth city would plausibly show")

    out = d[["city", "n_D", "n_C", "rr", "lo", "hi", "lo_boot", "hi_boot", "se_boot",
             "eff_clusters", "p_perm", "included"]]
    out.to_csv(ROOT / "displacement/meta_analysis_inputs.csv", index=False)
    pd.DataFrame([dict(spec="primary", **primary), dict(spec="co_primary", **coprim),
                  dict(spec="sham", **shr)]).to_csv(
        ROOT / "displacement/meta_analysis_results.csv", index=False)
    print("\nwrote meta_analysis_inputs.csv, meta_analysis_results.csv")



if __name__ == "__main__":
    main()
