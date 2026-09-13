"""PRE-REGISTRATION CLOSE-OUT — the two declared checks that had not been run.

§4.5  NEW YORK, LIVE FILE vs ARCHIVE FILE.  MANDATORY, not optional.
      NYPD publishes two shooting files that disagree by a uniform ~22% level shift in
      every year. The live file (5ucz-vwe8, 24,310 rows) is the pre-registered primary;
      the archive (833y-fsy8, 29,647 rows) is the declared robustness arm. A uniform
      proportional difference cancels in a RATE RATIO **only if the dropped records are
      spatially neutral with respect to the boundary**. §4.5 fixed the test in advance:

          if |log RR_live - log RR_archive| > 0.10  ->  NOT spatially neutral.
          NYC is then reported with both estimates and an explicit caveat, and a
          sensitivity refit excludes NYC entirely.

      This matters more than it did at freeze time: New York is one of the three cities
      carrying the pooled result.

§5.5  ALL-YEARS WINDOW, pooled, alongside the 2019-2023 primary.

    python displacement/prereg_closeout.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        precision, ROOT, CRS, PRIMARY)
from meta_analysis import dl

BAND = 250
DIVERGENCE_RULE = 0.10          # §4.5, fixed before the data was seen


def city_rr(slug, names, st, band=BAND, window=PRIMARY):
    """Band rate ratio for one cached city file, using the same helpers as the design."""
    d = pd.read_parquet(ROOT / f"displacement/data/cities/{slug}.parquet")
    w, yrs, dmin, dmax, _ = effective_window(d, window)
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc_for(slug, names, holc[holc.grade.isin(["C", "D"])]).to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]
    Du, Cu = holc[holc.grade == "D"].union_all(), holc[holc.grade == "C"].union_all()
    dband = Du.intersection(Cu.boundary.buffer(band))
    cband = Cu.intersection(Du.boundary.buffer(band))
    tr = load_tracts(st)
    tidx = tr.sindex
    pD, _ = interp(dband, tr, tidx)
    pC, _ = interp(cband, tr, tidx)
    pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat), crs=4326).to_crs(CRS)
    psidx = pts.sindex
    nD = len(psidx.query(dband, predicate="contains"))
    nC = len(psidx.query(cband, predicate="contains"))
    rr = (nD / pD) / (nC / pC)
    se = np.sqrt(1 / max(nD, 1) + 1 / max(nC, 1))
    nn = precision(np.c_[pts.geometry.x.values, pts.geometry.y.values])
    return dict(slug=slug, n=len(w), n_D=nD, n_C=nC, pop_D=pD, pop_C=pC, rr=rr,
                log_rr=np.log(rr), se=se, yrs=yrs, span=f"{dmin}..{dmax}", nn_m=nn)


print("=" * 100)
print("§4.5 — NEW YORK: LIVE FILE vs ARCHIVE FILE")
print("=" * 100)
nyc_names = UNITS["nyc"][0]
live = city_rr("nyc", nyc_names, "36")
arch = city_rr("nyc_archive", nyc_names, "36")

for lab, r in (("LIVE 5ucz-vwe8 (primary)", live), ("ARCHIVE 833y-fsy8", arch)):
    print(f"  {lab:<28} n={r['n']:>6,}  n_D={r['n_D']:>4}  n_C={r['n_C']:>4}  "
          f"RR={r['rr']:.4f}  log RR={r['log_rr']:+.4f}   [{r['span']}, {r['yrs']:.2f} yrs]")

div = abs(live["log_rr"] - arch["log_rr"])
print(f"\n  |log RR difference| = {div:.4f}   rule threshold = {DIVERGENCE_RULE}")
if div > DIVERGENCE_RULE:
    print("  >> EXCEEDS THE RULE. The 22% level shift is NOT spatially neutral.")
    print("     §4.5 requires: report both estimates with an explicit caveat, AND a")
    print("     sensitivity refit that excludes New York.")
else:
    print("  >> WITHIN THE RULE. The definitional difference between the two NYPD files")
    print("     is spatially neutral with respect to the C/D boundary, so it cancels in")
    print("     the rate ratio. The live file stands as the primary, uncaveated.")

print(f"\n  (population denominators are identical by construction: "
      f"D={live['pop_D']:,.0f}  C={live['pop_C']:,.0f}; only the numerator differs)")
print(f"  archive/live event ratio in band: D {arch['n_D']/max(live['n_D'],1):.3f}   "
      f"C {arch['n_C']/max(live['n_C'],1):.3f}   "
      f"(a spatially neutral shift gives the SAME ratio on both sides)")

# ---------------------------------------------------------------- §5.5 all years
print("\n" + "=" * 100)
print("§5.5 — ALL-YEARS WINDOW, POOLED")
print("=" * 100)
f = ROOT / "displacement/multi_city_rates_allyears.csv"
if not f.exists():
    print("  multi_city_rates_allyears.csv not present — run:")
    print("     python displacement/multi_city_boundary_design.py --window all")
else:
    a = pd.read_csv(f)
    a = a[(a.band == BAND) & a.included].copy()
    a["y"] = np.log(a.rr)
    print(a[["city", "n_D", "n_C", "rr", "lo", "hi", "years", "win_start", "win_end"]]
          .round(3).to_string(index=False))
    r = dl(a.y, a.se_log_rr ** 2)
    print(f"\n  pooled, all years, analytic SE  k={r['k']}  RR {np.exp(r['mu']):.3f} "
          f"[{np.exp(r['lo']):.3f}, {np.exp(r['hi']):.3f}]  I2={r['I2']:.1f}%")
    p = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
    p = p[(p.band == BAND) & p.included].copy()
    p["y"] = np.log(p.rr)
    rp = dl(p.y, p.se_log_rr ** 2)
    print(f"  pooled, 2019-2023,  analytic SE  k={rp['k']}  RR {np.exp(rp['mu']):.3f} "
          f"[{np.exp(rp['lo']):.3f}, {np.exp(rp['hi']):.3f}]  I2={rp['I2']:.1f}%")
    print("\n  (both use the pre-registered analytic SE so the two windows are comparable;")
    print("   the Amendment 2 bootstrap SEs exist only for the 2019-2023 primary band)")

pd.DataFrame([live, arch]).to_csv(ROOT / "displacement/prereg_nyc_file_check.csv", index=False)
print("\nwrote prereg_nyc_file_check.csv")
