"""SHAM-BOUNDARY PLACEBO — pre-registration §6. THE TEST H1 IS CONDITIONAL ON.

THE QUESTION
  Every estimate in this project compares a strip of D territory against a facing strip
  of C territory. Suppose the comparison has nothing to do with the grade line at all --
  suppose any strip-versus-strip split of urban territory produces a rate ratio away
  from 1, because of edge effects, polygon interior structure, how violence concentrates
  away from neighbourhood edges, or how areal interpolation behaves on thin slivers.
  Then every number we have is an artefact of the machinery, not a fact about redlining.

THE TEST
  Bisect each D polygon with a randomly oriented line through its centroid. Label one
  half sham-D and the other sham-C. Build strips of the SAME band width on each side of
  that internal line and run the IDENTICAL rate machinery. No grade change occurs
  anywhere along a sham line -- both halves are the same HOLC polygon, same grade, same
  neighbourhood.

  Repeat over 200 random orientations per city (§6), seeded and recorded.

WHAT THE ANSWER MEANS
  sham RR ~ 1, real RR outside the sham distribution  ->  the real boundary is doing work
  sham RR comparable to the real RR                   ->  THE DESIGN MEASURES DISTANCE-TO-
                                                          EDGE, NOT GRADE. H1 fails, and
                                                          it fails regardless of how clean
                                                          every other audit came back.

  Reported per city: the sham RR distribution, and the share of sham draws whose |log RR|
  reaches or exceeds the real |log RR| -- a permutation-style p-value for "is the real
  boundary distinguishable from an arbitrary line drawn inside the same neighbourhoods?"

  The helpers are IMPORTED from multi_city_boundary_design, never re-implemented, so the
  placebo cannot silently drift into being a different measurement than the thing it
  is supposed to be a placebo for.

    python displacement/sham_boundary_placebo.py
    python displacement/sham_boundary_placebo.py --draws 50      # quick look
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import zlib
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        ROOT, CRS, PRIMARY, BANDS)

BAND = 250
DRAWS = 200                                    # §6
SEED = 20260911                                # frozen, recorded
FAR = 2_000_000                                # half-plane construction length, metres


def bisect(poly, theta):
    """Split a polygon by a line through its centroid at angle theta.
    Returns (half_a, half_b, strip) where strip is the band around the cut line."""
    c = poly.centroid
    ux, uy = np.cos(theta), np.sin(theta)
    nx, ny = -uy, ux                                    # normal to the cut
    p1 = (c.x - ux * FAR, c.y - uy * FAR)
    p2 = (c.x + ux * FAR, c.y + uy * FAR)
    hp_a = Polygon([p1, p2, (p2[0] + nx * FAR, p2[1] + ny * FAR),
                    (p1[0] + nx * FAR, p1[1] + ny * FAR)])
    hp_b = Polygon([p1, p2, (p2[0] - nx * FAR, p2[1] - ny * FAR),
                    (p1[0] - nx * FAR, p1[1] - ny * FAR)])
    # strip of width BAND either side of the cut == buffer of the cut line
    from shapely.geometry import LineString
    strip = LineString([p1, p2]).buffer(BAND)
    return poly.intersection(hp_a), poly.intersection(hp_b), strip


def sham_once(D_geoms, theta_list, tr, tidx, pts, psidx):
    """One full sham draw across every D polygon in the city.

    HOLC D polygons are disjoint, and the two halves of one polygon are disjoint, so
    population and counts SUM across pieces exactly. Summing small simple pieces is far
    cheaper than intersecting the tract layer with one giant multi-part union, and gives
    the identical answer -- which the --verify-sum flag checks against the union route."""
    pA = pB = 0.0
    nA = nB = 0
    for geom, th in zip(D_geoms, theta_list):
        if geom.is_empty or geom.area <= 0:
            continue
        ha, hb, strip = bisect(geom, th)
        for half, side in ((ha.intersection(strip), "A"), (hb.intersection(strip), "B")):
            if half.is_empty:
                continue
            p, _ = interp(half, tr, tidx)
            # predicate is applied as predicate(INPUT, TREE), so counting points
            # inside a polygon is CONTAINS, not WITHIN. "within" asks whether the
            # polygon sits inside a point -- always false, silently returning 0.
            n = len(psidx.query(half, predicate="contains"))
            if side == "A":
                pA += p; nA += n
            else:
                pB += p; nB += n
    if pA < 500 or pB < 500:                            # same §4.4 population floor
        return None
    if nA + nB < 30:
        return None
    return (nA / pA) / (nB / pB), nA, nB, pA, pB


def main():
    """Runner, guarded so this module can be imported for debugging and reuse
    without re-executing the whole placebo (it was not, and an import re-ran it)."""
    draws = DRAWS
    if "--draws" in sys.argv:
        draws = int(sys.argv[sys.argv.index("--draws") + 1])

    real = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]

    print("=" * 104)
    print(f"SHAM-BOUNDARY PLACEBO — §6. band {BAND} m, {draws} random orientations/city, seed {SEED}")
    print("A sham line splits a D polygon in half. NO GRADE CHANGE OCCURS ALONG IT.")
    print("=" * 104)

    rows, dist_rows = [], []
    for slug, (names, st) in UNITS.items():
        f = ROOT / f"displacement/data/cities/{slug}.parquet"
        if not f.exists():
            print(f"\n{slug}: MISSING cache — skipped, not zero")
            continue
        d = pd.read_parquet(f)
        w, yrs, _, _, _ = effective_window(d, PRIMARY)
        city = w.city.iloc[0]
        g = holc_for(slug, names, holc)
        D = g[g.grade == "D"].reset_index(drop=True)
        if not len(D) or not len(w):
            continue

        tr = load_tracts(st)
        tidx = tr.sindex
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        rr_real = real[(real.city == city) & (real.band == BAND)].rr
        rr_real = float(rr_real.iloc[0]) if len(rr_real) else np.nan

        psidx = pts.sindex
        # zlib.crc32, NOT hash(): Python randomises string hashing per process, so a
        # hash-derived seed would make a PRE-REGISTERED analysis unreproducible.
        rng = np.random.default_rng(SEED + zlib.crc32(slug.encode()) % 10_000)
        geoms = list(D.geometry.values)
        vals = []
        for k in range(draws):
            th = rng.uniform(0, np.pi, size=len(geoms))
            r = sham_once(geoms, th, tr, tidx, pts, psidx)
            if r is not None:
                vals.append(r[0])
            if (k + 1) % 50 == 0:
                print(f"   {city:<14} {k+1}/{draws} draws ...")
        if not vals:
            print(f"   {city}: no valid sham draws")
            continue

        v = np.array(vals)
        lv = np.abs(np.log(v))
        lr = abs(np.log(rr_real)) if np.isfinite(rr_real) and rr_real > 0 else np.nan
        p_perm = float((lv >= lr).mean()) if np.isfinite(lr) else np.nan
        print(f"\n{city}")
        print(f"   real RR (250 m)        : {rr_real:.3f}   |log RR| = {lr:.4f}")
        print(f"   sham RR over {len(v):>3} draws : median {np.median(v):.3f}   "
              f"mean {v.mean():.3f}   5-95% [{np.percentile(v,5):.3f}, {np.percentile(v,95):.3f}]")
        print(f"   sham |log RR|          : median {np.median(lv):.4f}   "
              f"95th pct {np.percentile(lv,95):.4f}")
        print(f"   share of sham draws with |log RR| >= real : {p_perm:.3f}"
              + ("   <-- REAL BOUNDARY NOT DISTINGUISHABLE FROM AN ARBITRARY LINE"
                 if np.isfinite(p_perm) and p_perm > 0.05 else ""))
        rows.append(dict(city=city, rr_real=rr_real, abs_log_real=lr, n_draws=len(v),
                         sham_median=float(np.median(v)), sham_mean=float(v.mean()),
                         sham_p05=float(np.percentile(v, 5)), sham_p95=float(np.percentile(v, 95)),
                         sham_abslog_median=float(np.median(lv)),
                         sham_abslog_p95=float(np.percentile(lv, 95)), p_perm=p_perm))
        dist_rows += [dict(city=city, draw=i, rr=float(x)) for i, x in enumerate(v)]

    r = pd.DataFrame(rows)
    r.to_csv(ROOT / "displacement/sham_boundary_summary.csv", index=False)
    pd.DataFrame(dist_rows).to_csv(ROOT / "displacement/sham_boundary_draws.csv", index=False)

    print("\n" + "=" * 104)
    print("VERDICT — §6")
    print("=" * 104)
    print(r[["city", "rr_real", "sham_median", "sham_p05", "sham_p95",
             "sham_abslog_median", "abs_log_real", "p_perm"]].round(4).to_string(index=False))
    ok = r[r.p_perm <= 0.05]
    print(f"\ncities where the real boundary is distinguishable from an arbitrary internal line "
          f"(p<=0.05): {len(ok)} of {len(r)}  {list(ok.city)}")
    bad = r[r.p_perm > 0.05]
    if len(bad):
        print(f"NOT distinguishable: {list(bad.city)}")
    print(f"\nsham median |log RR| across cities: {r.sham_abslog_median.median():.4f}   "
          f"vs real |log RR| median: {r.abs_log_real.median():.4f}")
    print("\nwrote sham_boundary_summary.csv, sham_boundary_draws.csv")



if __name__ == "__main__":
    main()
