"""SIGNED-DISTANCE GRADIENT — pre-registration §7.1.

WHY THIS IS THE RESULT, NOT A ROBUSTNESS CHECK

  §7.2 already fired: the rate ratio does NOT strengthen as the band narrows, in 6 of 7
  cities. By our own pre-registered rule the effect must be reported as an area GRADIENT,
  and the words "discontinuity", "sharp", "jump" and "at the line" are prohibited for the
  estimate. That makes the discrete bands a robustness table around the real object, which
  is the SHAPE of the rate profile as you cross the grade line.

WHAT IS COMPUTED

  The C/D interface is the portion of the D boundary that actually touches C -- not the
  whole D outline, which mostly faces A, B, water or nothing.

  Signed distance: negative on the C side, positive on the D side. For a bin [lo, hi):
      positive bin geometry = D ∩ (buffer(iface, hi) \\ buffer(iface, lo))
      negative bin geometry = C ∩ (buffer(iface, hi) \\ buffer(iface, lo))
  Population is areal-interpolated into each bin and events are counted inside it, so each
  bin yields a genuine rate per 100k per year rather than a raw count that just tracks how
  much land the bin happens to contain.

  A population-weighted local linear fit on each side gives the slope of the profile and
  the fitted rate as the line is approached from either side. Their ratio is reported as
  a GRADIENT ENDPOINT CONTRAST -- it is deliberately NOT called a discontinuity estimate,
  because §7.2 forbids that description and because 6 of 7 cities say it would be wrong.

    python displacement/distance_gradient.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        ROOT, CRS, PRIMARY)

EDGES = np.arange(-1000, 1001, 50)             # 50 m bins, -1000 .. +1000
# Endpoint contrasts are refit at each of these half-widths. A local-linear endpoint
# estimate over +/-1000 m is a very wide bandwidth; if the contrast is real it should
# not depend on how far out the fit reaches.
BANDWIDTHS = [150, 250, 300, 500, 1000]
MIN_BIN_POP = 250                              # a bin below this cannot support a rate


def interface(Du, Cu):
    """The part of D's boundary that actually faces C."""
    iface = Du.boundary.intersection(Cu.boundary)
    if iface.is_empty or iface.length < 1.0:
        iface = Du.boundary.intersection(Cu.buffer(1.0))
    return iface


def annulus(iface, lo, hi):
    outer = iface.buffer(hi)
    return outer if lo <= 0 else outer.difference(iface.buffer(lo))


def wls(x, y, w):
    """Population-weighted least squares. Returns (intercept at x=0, slope)."""
    m = np.isfinite(x) & np.isfinite(y) & np.isfinite(w) & (w > 0)
    if m.sum() < 2:
        return np.nan, np.nan
    X = np.c_[np.ones(m.sum()), x[m]]
    W = np.diag(w[m])
    try:
        b = np.linalg.solve(X.T @ W @ X, X.T @ W @ y[m])
    except np.linalg.LinAlgError:
        return np.nan, np.nan
    return float(b[0]), float(b[1])


def main():
    """Runner, guarded so `interface()` can be imported without re-running the
    whole gradient. Third module in this project to need it -- same lesson."""
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]

    print("=" * 104)
    print("SIGNED-DISTANCE GRADIENT — §7.1.  negative = C side, positive = D side")
    print("=" * 104)

    rows, fits = [], []
    for slug, (names, st) in UNITS.items():
        f = ROOT / f"displacement/data/cities/{slug}.parquet"
        if not f.exists():
            print(f"\n{slug}: MISSING cache — skipped, not zero")
            continue
        d = pd.read_parquet(f)
        w, yrs, _, _, _ = effective_window(d, PRIMARY)
        city = w.city.iloc[0]
        g = holc_for(slug, names, holc)
        if not {"C", "D"} <= set(g.grade):
            continue
        Du, Cu = g[g.grade == "D"].union_all(), g[g.grade == "C"].union_all()
        iface = interface(Du, Cu)
        tr = load_tracts(st)
        tidx = tr.sindex
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        psidx = pts.sindex

        print(f"\n{city}   interface length {iface.length/1000:,.1f} km,  {yrs:.2f} exposure yrs")
        prof = []
        for lo_e, hi_e in zip(EDGES[:-1], EDGES[1:]):
            # distance from the line is |.|; the SIGN picks which grade the ring is cut against
            a, b = abs(hi_e), abs(lo_e)
            r_lo, r_hi = min(a, b), max(a, b)
            ring = annulus(iface, r_lo, r_hi)
            geom = (Du if lo_e >= 0 else Cu).intersection(ring)
            if geom.is_empty:
                continue
            p, _ = interp(geom, tr, tidx)
            n = len(psidx.query(geom, predicate="contains"))   # CONTAINS: points inside polygon
            if p < MIN_BIN_POP:
                continue
            mid = (lo_e + hi_e) / 2
            rate = 1e5 * n / p / yrs
            prof.append(dict(city=city, lo=lo_e, hi=hi_e, mid=mid, side="D" if mid > 0 else "C",
                             n=n, pop=p, rate=rate))
        pf = pd.DataFrame(prof)
        if len(pf) < 4:
            print("   too few usable bins")
            continue
        rows += prof

        sweep = {}
        for bw in BANDWIDTHS:
            sub = pf[pf.mid.abs() <= bw]
            Ds, Cs = sub[sub.mid > 0], sub[sub.mid < 0]
            a_d, s_d = wls(Ds.mid.values, Ds.rate.values, Ds["pop"].values)
            a_c, s_c = wls(Cs.mid.values, Cs.rate.values, Cs["pop"].values)
            sweep[bw] = (a_d / a_c if a_c and np.isfinite(a_c) and a_c > 0 else np.nan,
                         a_c, a_d, s_c, s_d, len(Cs), len(Ds))
        aD, sD = sweep[1000][2], sweep[1000][4]
        aC, sC = sweep[1000][1], sweep[1000][3]
        contrast = sweep[1000][0]

        print(f"   usable bins {len(pf)} of {len(EDGES)-1}  "
              f"(dropped: population < {MIN_BIN_POP})")
        print(f"   C-side fit: rate at line {aC:8.1f}   slope {sC:+.4f} per m")
        print(f"   D-side fit: rate at line {aD:8.1f}   slope {sD:+.4f} per m")
        print(f"   GRADIENT ENDPOINT CONTRAST (D/C at the line) = {contrast:.3f}"
              "   [NOT a discontinuity estimate — §7.2]")
        print("   bandwidth sweep: " + "  ".join(
            f"±{bw}m={sweep[bw][0]:.3f}(n={sweep[bw][5]}/{sweep[bw][6]})" for bw in BANDWIDTHS))
        rec = dict(city=city, rate_at_line_C=aC, rate_at_line_D=aD,
                   slope_C=sC, slope_D=sD, endpoint_contrast=contrast,
                   n_bins=len(pf), iface_km=iface.length / 1000)
        for bw in BANDWIDTHS:
            rec[f"contrast_bw{bw}"] = sweep[bw][0]
        fits.append(rec)

    pd.DataFrame(rows).to_csv(ROOT / "displacement/distance_gradient_profile.csv", index=False)
    fi = pd.DataFrame(fits)
    fi.to_csv(ROOT / "displacement/distance_gradient_fits.csv", index=False)

    print("\n" + "=" * 104)
    print("SUMMARY — §7.1")
    print("=" * 104)
    print(fi[["city","rate_at_line_C","rate_at_line_D","slope_C","slope_D",
              "endpoint_contrast","n_bins","iface_km"]].round(3).to_string(index=False))
    print("\nBANDWIDTH SENSITIVITY of the endpoint contrast — a real contrast should not")
    print("depend on how far out the local-linear fit reaches:")
    print(fi[["city"] + [f"contrast_bw{bw}" for bw in BANDWIDTHS]].round(3).to_string(index=False))
    band = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
    b250 = band[band.band == 250][["city", "rr"]].rename(columns={"rr": "RR_250m_band"})
    cmp = fi[["city", "endpoint_contrast"]].merge(b250, on="city", how="left")
    print("\nendpoint contrast vs the 250 m band RR (they answer different questions):")
    print(cmp.round(3).to_string(index=False))
    print("\nwrote distance_gradient_profile.csv, distance_gradient_fits.csv")



if __name__ == "__main__":
    main()
