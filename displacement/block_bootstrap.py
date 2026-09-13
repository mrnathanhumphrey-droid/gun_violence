"""SPATIAL BLOCK BOOTSTRAP — design-based inference for the per-city rate ratios.

THE PROBLEM THIS FIXES

  Every CI reported so far uses SE(log RR) = sqrt(1/n_D + 1/n_C), which treats each
  shooting as an independent Poisson draw. Shootings are the textbook violation: they
  cluster in space and in time through retaliation. Those intervals are therefore too
  narrow, and by an unknown amount. The sham placebo already showed the size of the
  problem from the other direction -- Baltimore's analytic CI is [0.734, 0.868] while
  arbitrary lines in Baltimore produce RRs spanning [0.677, 1.404].

THE RESAMPLING UNIT

  Size on what the experiment re-rolls. This design is a PAIRED comparison across an
  interface: every stretch of C/D boundary contributes a D-side strip and the C-side
  strip facing it. So the cluster is a SEGMENT OF THE INTERFACE, carrying both of its
  sides, and resampling segments with replacement preserves both the spatial clustering
  and the D/C pairing.

  The interface is cut into 500 m segments. Voronoi cells around the segment midpoints
  partition the plane, so intersecting each band with a cell gives DISJOINT per-segment
  pieces -- no event and no person is counted twice, which a naive buffer-per-segment
  would do at every joint.

  Per segment k we tally (n_D, pop_D, n_C, pop_C) once. The bootstrap then resamples
  segments with replacement and recomputes RR = (Sn_D/Spop_D)/(Sn_C/Spop_C).

  The effective number of clusters is reported, because that -- not the number of
  shootings -- is what actually limits inference here. Baltimore has 13.8 km of
  interface against Chicago's 140.8 km, and no amount of events repairs that.

    python displacement/block_bootstrap.py
    python displacement/block_bootstrap.py --band 150
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import MultiPoint, LineString, box
from shapely.ops import voronoi_diagram

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        ROOT, CRS, PRIMARY)
from distance_gradient import interface

SEG_LEN = 500          # metres of interface per cluster
B = 2000               # bootstrap resamples
SEED = 20260913


def segment_interface(iface, seg_len=SEG_LEN):
    """Cut the interface into ~seg_len pieces; return their midpoints."""
    lines = [iface] if iface.geom_type == "LineString" else list(getattr(iface, "geoms", []))
    mids = []
    for ln in lines:
        if ln.geom_type != "LineString" or ln.length <= 0:
            continue
        k = max(1, int(round(ln.length / seg_len)))
        for i in range(k):
            s = ln.interpolate((i + 0.5) * ln.length / k)
            mids.append(s)
    return mids


def voronoi_cells(mids, envelope):
    """Voronoi partition around segment midpoints, each cell matched to its midpoint."""
    mp = MultiPoint(mids)
    vd = voronoi_diagram(mp, envelope=envelope)
    cells = list(vd.geoms)
    out = [None] * len(mids)
    # match by containment; a midpoint lies in exactly one cell
    from shapely.strtree import STRtree
    tree = STRtree(cells)
    for i, p in enumerate(mids):
        cand = tree.query(p)
        for j in cand:
            if cells[j].contains(p):
                out[i] = cells[j]
                break
        if out[i] is None and len(cand):
            out[i] = cells[cand[0]]
    return out


def main():
    """Runner, guarded so segment_interface()/voronoi_cells() can be reused."""
    band_w = 250
    if "--band" in sys.argv:
        band_w = int(sys.argv[sys.argv.index("--band") + 1])

    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]
    analytic = pd.read_csv(ROOT / "displacement/multi_city_rates.csv")

    print("=" * 108)
    print(f"SPATIAL BLOCK BOOTSTRAP — band {band_w} m, {SEG_LEN} m interface segments, "
          f"{B:,} resamples, seed {SEED}")
    print("Cluster = a stretch of C/D boundary WITH BOTH OF ITS SIDES (the design is paired).")
    print("=" * 108)

    rows = []
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
        dband = Du.intersection(Cu.boundary.buffer(band_w))
        cband = Cu.intersection(Du.boundary.buffer(band_w))
        if dband.is_empty or cband.is_empty:
            continue

        mids = segment_interface(iface)
        if len(mids) < 5:
            print(f"\n{city}: only {len(mids)} interface segments — too few to bootstrap")
            continue
        env = box(*(np.array(dband.union(cband).bounds) + np.array([-5000, -5000, 5000, 5000])))
        cells = voronoi_cells(mids, env)

        tr = load_tracts(st)
        tidx = tr.sindex
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        psidx = pts.sindex

        nD = np.zeros(len(cells)); pD = np.zeros(len(cells))
        nC = np.zeros(len(cells)); pC = np.zeros(len(cells))
        for k, cell in enumerate(cells):
            if cell is None or cell.is_empty:
                continue
            dp = dband.intersection(cell)
            cp = cband.intersection(cell)
            if not dp.is_empty:
                pD[k], _ = interp(dp, tr, tidx)
                nD[k] = len(psidx.query(dp, predicate="contains"))
            if not cp.is_empty:
                pC[k], _ = interp(cp, tr, tidx)
                nC[k] = len(psidx.query(cp, predicate="contains"))

        # the point estimate must reproduce the main analysis from these pieces
        rr_hat = (nD.sum() / pD.sum()) / (nC.sum() / pC.sum())
        a = analytic[(analytic.city == city) & (analytic.band == band_w)]
        rr_main = float(a.rr.iloc[0]) if len(a) else np.nan
        lo_a = float(a.lo.iloc[0]) if len(a) else np.nan
        hi_a = float(a.hi.iloc[0]) if len(a) else np.nan

        rng = np.random.default_rng(SEED)
        K = len(cells)
        idx = rng.integers(0, K, size=(B, K))
        bD = nD[idx].sum(1); bPD = pD[idx].sum(1)
        bC = nC[idx].sum(1); bPC = pC[idx].sum(1)
        ok = (bPD > 0) & (bPC > 0) & (bC > 0)
        boot = (bD[ok] / bPD[ok]) / (bC[ok] / bPC[ok])
        lo_b, hi_b = np.percentile(boot, [2.5, 97.5])

        # how concentrated is the evidence across clusters?
        tot = nD + nC
        share = np.sort(tot)[::-1] / max(tot.sum(), 1)
        eff_k = 1.0 / np.sum((tot / max(tot.sum(), 1)) ** 2)      # Kish-style effective clusters

        widen = (np.log(hi_b) - np.log(lo_b)) / (np.log(hi_a) - np.log(lo_a)) if np.isfinite(lo_a) else np.nan
        print(f"\n{city}")
        print(f"   interface {iface.length/1000:>6.1f} km -> {K} segments   "
              f"effective clusters {eff_k:.1f}   top cluster {100*share[0]:.1f}% of events")
        print(f"   piece-sum RR {rr_hat:.4f}  vs main analysis {rr_main:.4f}  "
              f"(diff {rr_hat-rr_main:+.4f})")
        print(f"   analytic  95% CI [{lo_a:.3f}, {hi_a:.3f}]   (Poisson, assumes independence)")
        print(f"   BOOTSTRAP 95% CI [{lo_b:.3f}, {hi_b:.3f}]   <- design-based")
        print(f"   interval is {widen:.2f}x the analytic width"
              + ("   ** CROSSES 1 **" if lo_b <= 1 <= hi_b else ""))
        rows.append(dict(city=city, band=band_w, rr=rr_hat, rr_main=rr_main,
                         lo_analytic=lo_a, hi_analytic=hi_a, lo_boot=lo_b, hi_boot=hi_b,
                         n_segments=K, eff_clusters=eff_k, top_cluster_share=100 * share[0],
                         iface_km=iface.length / 1000, width_ratio=widen,
                         crosses_one=bool(lo_b <= 1 <= hi_b)))

    r = pd.DataFrame(rows)
    r.to_csv(ROOT / f"displacement/block_bootstrap_{band_w}m.csv", index=False)
    print("\n" + "=" * 108)
    print("SUMMARY — design-based vs analytic inference")
    print("=" * 108)
    print(r[["city", "rr", "lo_analytic", "hi_analytic", "lo_boot", "hi_boot",
             "width_ratio", "eff_clusters", "crosses_one"]].round(3).to_string(index=False))
    sur = r[~r.crosses_one]
    print(f"\nsurvive design-based inference (CI excludes 1): {len(sur)} of {len(r)}  {list(sur.city)}")
    print(f"\nwrote block_bootstrap_{band_w}m.csv")



if __name__ == "__main__":
    main()
