"""SEGMENT (BOUNDARY) FIXED EFFECTS — pre-registration Amendment 3, A3.1.

WHY

  Aaronson, Hartley & Mazumder (Chicago Fed WP 2017-12) and Krimmel (2018) both restrict
  the comparison to residents of the SAME boundary segment, via boundary fixed effects.
  Our §5.1 estimator pools each city's whole C/D interface, which is a weaker comparison:
  nothing stops a D strip on one side of the city being compared against a C strip on the
  other, and the two can differ for reasons that have nothing to do with the grade line.

THE ESTIMATOR

  Conditional Poisson with one fixed effect per 500 m interface segment and a
  log-population offset:

      n_ks ~ Poisson( pop_ks * exp(alpha_k + b * 1[s = D]) )

  Conditioning on each segment's total events n_k = n_Dk + n_Ck removes every alpha_k,
  and the D-side count is Binomial(n_k, pi_k) with

      pi_k = pD_k * e^b / (pD_k * e^b + pC_k)

  so the conditional MLE of b is the segment-fixed-effects log rate ratio. ONLY
  within-segment D-vs-C contrasts identify it: a segment with events on just one side
  still contributes, but a segment with population on only one side cannot and is dropped
  (and the number dropped is reported, never silently absorbed).

  Inference: the same 500 m segment cluster bootstrap as Amendment 2, so the FE estimate
  and the §5.3 primary are compared on like-for-like inference.

  A3.1 is a SENSITIVITY. §5.3's band rate ratio remains primary. If the two disagree
  materially, the disagreement is the finding.

    python displacement/segment_fixed_effects.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import box
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        ROOT, CRS, PRIMARY)
from distance_gradient import interface
from block_bootstrap import segment_interface, voronoi_cells, SEG_LEN
from meta_analysis import dl

BAND = 250
B = 2000
SEED = 20260913
TALLY = ROOT / f"displacement/segment_tallies_{BAND}m.csv"


def cond_score(b, nD, nC, pD, pC):
    """Derivative of the conditional log-likelihood wrt b. Root = the FE estimate."""
    e = np.exp(b)
    pi = pD * e / (pD * e + pC)
    return float(np.sum(nD - (nD + nC) * pi))


def fit_fe(nD, nC, pD, pC):
    """Conditional MLE. Returns nan when the data cannot identify b."""
    m = (pD > 0) & (pC > 0) & ((nD + nC) > 0)
    if m.sum() < 2:
        return np.nan, int(m.sum())
    nD, nC, pD, pC = nD[m], nC[m], pD[m], pC[m]
    # b is identified only if some segment has events on each side across the sample
    if nD.sum() == 0 or nC.sum() == 0:
        return np.nan, int(m.sum())
    lo, hi = -5.0, 5.0
    f_lo, f_hi = cond_score(lo, nD, nC, pD, pC), cond_score(hi, nD, nC, pD, pC)
    if np.sign(f_lo) == np.sign(f_hi):
        return np.nan, int(m.sum())
    return float(brentq(cond_score, lo, hi, args=(nD, nC, pD, pC), xtol=1e-10)), int(m.sum())


# ------------------------------------------------------------------ tallies
if TALLY.exists():
    tal = pd.read_csv(TALLY)
    print(f"using cached per-segment tallies: {TALLY.name} ({len(tal):,} segments)")
else:
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]
    recs = []
    for slug, (names, st) in UNITS.items():
        f = ROOT / f"displacement/data/cities/{slug}.parquet"
        if not f.exists():
            print(f"{slug}: MISSING cache — skipped, not zero")
            continue
        d = pd.read_parquet(f)
        w, yrs, _, _, _ = effective_window(d, PRIMARY)
        city = w.city.iloc[0]
        g = holc_for(slug, names, holc)
        if not {"C", "D"} <= set(g.grade):
            continue
        Du, Cu = g[g.grade == "D"].union_all(), g[g.grade == "C"].union_all()
        iface = interface(Du, Cu)
        dband = Du.intersection(Cu.boundary.buffer(BAND))
        cband = Cu.intersection(Du.boundary.buffer(BAND))
        mids = segment_interface(iface)
        if len(mids) < 5:
            print(f"{city}: {len(mids)} segments — too few")
            continue
        env = box(*(np.array(dband.union(cband).bounds) + np.array([-5000, -5000, 5000, 5000])))
        cells = voronoi_cells(mids, env)
        tr = load_tracts(st)
        tidx = tr.sindex
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        psidx = pts.sindex
        for k, cell in enumerate(cells):
            if cell is None or cell.is_empty:
                continue
            dp, cp = dband.intersection(cell), cband.intersection(cell)
            pd_ = interp(dp, tr, tidx)[0] if not dp.is_empty else 0.0
            pc_ = interp(cp, tr, tidx)[0] if not cp.is_empty else 0.0
            nd_ = len(psidx.query(dp, predicate="contains")) if not dp.is_empty else 0
            nc_ = len(psidx.query(cp, predicate="contains")) if not cp.is_empty else 0
            recs.append(dict(city=city, slug=slug, seg=k, n_D=nd_, n_C=nc_,
                             pop_D=pd_, pop_C=pc_, years=yrs))
        print(f"   {city}: {len(cells)} segments tallied")
    tal = pd.DataFrame(recs)
    tal.to_csv(TALLY, index=False)
    print(f"wrote {TALLY.name}")

# ------------------------------------------------------------------ fit
print("\n" + "=" * 108)
print(f"SEGMENT FIXED EFFECTS (A3.1) — conditional Poisson, one FE per {SEG_LEN} m of "
      f"interface, band {BAND} m")
print("Only WITHIN-SEGMENT D-vs-C contrasts identify the estimate.")
print("=" * 108)

main = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
main = main[main.band == BAND]
boot_main = pd.read_csv(ROOT / f"displacement/block_bootstrap_{BAND}m.csv")

rows = []
for city, g in tal.groupby("city", sort=False):
    nD, nC = g.n_D.values.astype(float), g.n_C.values.astype(float)
    pD, pC = g.pop_D.values.astype(float), g.pop_C.values.astype(float)
    b, kused = fit_fe(nD, nC, pD, pC)
    usable = (pD > 0) & (pC > 0) & ((nD + nC) > 0)
    dropped = len(g) - int(usable.sum())

    rng = np.random.default_rng(SEED)
    K = len(g)
    vals = []
    for _ in range(B):
        i = rng.integers(0, K, size=K)
        bb, _ = fit_fe(nD[i], nC[i], pD[i], pC[i])
        if np.isfinite(bb):
            vals.append(bb)
    v = np.array(vals)
    lo, hi = (np.percentile(v, [2.5, 97.5]) if len(v) > 50 else (np.nan, np.nan))

    pooled_rr = float(main[main.city == city].rr.iloc[0])
    bm = boot_main[boot_main.city == city]
    plo = float(bm.lo_boot.iloc[0]) if len(bm) else np.nan
    phi = float(bm.hi_boot.iloc[0]) if len(bm) else np.nan
    print(f"\n{city}")
    print(f"   segments {K}  usable {int(usable.sum())}  dropped {dropped} "
          f"(no population on one side)")
    print(f"   pooled-interface RR (§5.3)  {pooled_rr:.3f}  [{plo:.3f}, {phi:.3f}]")
    print(f"   SEGMENT-FE RR (A3.1)        {np.exp(b):.3f}  "
          f"[{np.exp(lo):.3f}, {np.exp(hi):.3f}]"
          + ("   ** crosses 1 **" if np.isfinite(lo) and np.exp(lo) <= 1 <= np.exp(hi) else ""))
    rows.append(dict(city=city, n_seg=K, n_usable=int(usable.sum()), n_dropped=dropped,
                     rr_pooled=pooled_rr, lo_pooled=plo, hi_pooled=phi,
                     log_rr_fe=b, rr_fe=np.exp(b), lo_fe=np.exp(lo), hi_fe=np.exp(hi),
                     se_fe=(hi - lo) / (2 * 1.96) if np.isfinite(lo) else np.nan))

r = pd.DataFrame(rows)
r.to_csv(ROOT / "displacement/segment_fixed_effects.csv", index=False)

print("\n" + "=" * 108)
print("COMPARISON — pooled interface vs segment fixed effects")
print("=" * 108)
print(r[["city", "rr_pooled", "lo_pooled", "hi_pooled", "rr_fe", "lo_fe", "hi_fe",
         "n_seg", "n_dropped"]].round(3).to_string(index=False))

ok = r[np.isfinite(r.se_fe) & (r.se_fe > 0)]
inc = ok[ok.city.isin(main[main.included].city)]
if len(inc) >= 3:
    m = dl(inc.log_rr_fe.values, inc.se_fe.values ** 2)
    print(f"\nPOOLED SEGMENT-FE (DL random effects, k={m['k']}): "
          f"RR {np.exp(m['mu']):.3f} [{np.exp(m['lo']):.3f}, {np.exp(m['hi']):.3f}]  "
          f"tau2={m['tau2']:.4f}  I2={m['I2']:.1f}%")
    print(f"  vs §5.3 primary (pooled interface):  RR 1.251 [1.098, 1.424]")
    noChi = inc[inc.city != "Chicago"]
    if len(noChi) >= 3:
        m2 = dl(noChi.log_rr_fe.values, noChi.se_fe.values ** 2)
        print(f"  segment-FE, no Chicago (co-primary): "
              f"RR {np.exp(m2['mu']):.3f} [{np.exp(m2['lo']):.3f}, {np.exp(m2['hi']):.3f}]")
print("\nwrote segment_fixed_effects.csv")
