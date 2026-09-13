"""DONUT-HOLE TEST — is the estimate driven by events sitting right on the line?

THE THREAT

  HOLC boundaries frequently run down STREETS. Address geocoding places an event at a
  block centroid or a street-segment midpoint, not at the true location, so an event that
  happened on the boundary street can land on either side essentially at random -- or
  worse, systematically on one side, if the geocoder resolves to one block face. That is
  a DIRECTIONAL bias, not noise, and it would inflate or deflate the contrast depending
  on which way the geocoder leans.

  Los Angeles is the reason this matters now. It is the strongest and most robust city
  under every estimator (1.412 pooled, 1.480 under segment fixed effects) AND it has the
  worst measured coordinate precision in the sample (83 m median nearest-neighbour
  distance between distinct coordinates, unique-coordinate ratio 0.286, modal duplicate
  128). It also shows a spike in the 0-100 m D-side bin of the distance profile: 228.9
  per 100k/yr against 113.4 in the next bin out.

TWO TESTS

  1. DONUT SWEEP. Re-estimate the rate ratio excluding everything within h metres of the
     boundary, for h = 0, 25, 50, 75, 100, 150. Both the numerator (events) and the
     denominator (interpolated population) drop the hole, so the rate stays a rate. If
     the estimate is stable in h, displacement at the line is not driving it. If it
     collapses or inflates, it is.

  2. DENSITY AT THE LINE. Counts of events by SIGNED distance in fine 10 m bins across
     +/-150 m. Snapping to block centroids should show as a DEFICIT in the bins nearest
     zero (nothing is geocoded to the middle of the boundary street) with piles at the
     typical half-block offset. A clean point process should show no such hole.

     This is the geocoding analogue of the density test standard in RD practice: not a
     test for manipulation of a running variable, but for whether the running variable
     is measured well enough near the cutoff to support the comparison.

    python displacement/donut_hole_test.py
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
from distance_gradient import interface

BAND = 250
HOLES = [0, 25, 50, 75, 100, 150]
DENS_EDGES = np.arange(-150, 151, 10)


def main():
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]

    print("=" * 104)
    print(f"DONUT-HOLE TEST — band {BAND} m, hole radii {HOLES} m")
    print("Both events AND interpolated population drop the hole, so a rate stays a rate.")
    print("=" * 104)

    rows, dens_rows = [], []
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

        print(f"\n{city}")
        print(f"   {'hole':>6}{'n_D':>8}{'n_C':>8}{'pop_D':>11}{'pop_C':>11}"
              f"{'RR':>9}{'95% CI':>20}{'events kept':>13}")
        base_n = None
        for h in HOLES:
            outer = iface.buffer(BAND)
            ring = outer if h <= 0 else outer.difference(iface.buffer(h))
            dg, cg = Du.intersection(ring), Cu.intersection(ring)
            if dg.is_empty or cg.is_empty:
                continue
            pD, _ = interp(dg, tr, tidx)
            pC, _ = interp(cg, tr, tidx)
            nD = len(psidx.query(dg, predicate="contains"))
            nC = len(psidx.query(cg, predicate="contains"))
            if base_n is None:
                base_n = nD + nC
            if pD <= 0 or pC <= 0 or nC == 0:
                continue
            rr = (nD / pD) / (nC / pC)
            se = np.sqrt(1 / max(nD, 1) + 1 / max(nC, 1))
            lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
            keep = 100 * (nD + nC) / max(base_n, 1)
            print(f"   {h:>5}m{nD:>8,}{nC:>8,}{pD:>11,.0f}{pC:>11,.0f}{rr:>9.3f}"
                  f"   [{lo:.3f}, {hi:.3f}]{keep:>12.1f}%")
            rows.append(dict(city=city, hole=h, n_D=nD, n_C=nC, pop_D=pD, pop_C=pC,
                             rr=rr, lo=lo, hi=hi, pct_events_kept=keep))

        # ---------------------------------------------------------- density at the line
        near = pts[pts.geometry.within(iface.buffer(200))].copy()
        if len(near):
            dist = near.geometry.distance(iface).values
            inD = near.geometry.within(Du).values
            signed = np.where(inD, dist, -dist)
            cnt, _ = np.histogram(signed, bins=DENS_EDGES)
            mids = (DENS_EDGES[:-1] + DENS_EDGES[1:]) / 2
            for m_, c_ in zip(mids, cnt):
                dens_rows.append(dict(city=city, mid=float(m_), n=int(c_)))
            inner = cnt[(mids > -30) & (mids < 30)].mean()
            outer_m = cnt[(np.abs(mids) >= 30) & (np.abs(mids) <= 150)].mean()
            print(f"   density near the line: mean count/10m bin within +/-30 m = {inner:.1f}, "
                  f"30-150 m = {outer_m:.1f}   ratio {inner/max(outer_m,1e-9):.2f}")
            print("     " + " ".join(f"{c}" for c in cnt))

    r = pd.DataFrame(rows)
    r.to_csv(ROOT / "displacement/donut_hole_test.csv", index=False)
    pd.DataFrame(dens_rows).to_csv(ROOT / "displacement/donut_density.csv", index=False)

    print("\n" + "=" * 104)
    print("STABILITY OF THE RATE RATIO IN THE HOLE RADIUS")
    print("=" * 104)
    piv = r.pivot_table(index="city", columns="hole", values="rr")
    print(piv.round(3).to_string())
    print("\nshare of band events retained:")
    print(r.pivot_table(index="city", columns="hole", values="pct_events_kept").round(1).to_string())
    print("\nmax |log RR| shift from h=0:")
    for city, g in r.groupby("city"):
        b = g[g.hole == 0].rr
        if not len(b):
            continue
        b = float(b.iloc[0])
        shift = (np.log(g.rr) - np.log(b)).abs().max()
        print(f"   {city:<14} {shift:.4f}   (RR {b:.3f} -> range "
              f"[{g.rr.min():.3f}, {g.rr.max():.3f}])")
    print("\nwrote donut_hole_test.csv, donut_density.csv")


if __name__ == "__main__":
    main()
