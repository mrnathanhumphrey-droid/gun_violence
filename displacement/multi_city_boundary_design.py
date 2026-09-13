"""MULTI-CITY HOLC BOUNDARY DESIGN — per-city rate ratios across a redlining grade line.

Governed by PRE_REG_MULTICITY_2026_09_11.md (frozen 2026-09-11, Amendment 1 2026-09-11).
This file computes PER-CITY estimates only. It does NOT pool. Pooling is §5.2's
random-effects step and lives in meta_analysis.py, because pooling raw counts across
cities is prohibited and keeping the two steps in separate files makes that violation
impossible to commit by accident.

WHAT IS COMPUTED, AND WHICH CLAUSE REQUIRES IT

  §5.1  per-city RR = rate_D / rate_C on facing bands, SE = sqrt(1/n_D + 1/n_C)
  §4.4  mechanical inclusion: both bands >=500 interpolated people, n_D+n_C >= 30
  §4.7  coordinate-precision test, MEASURED: a city is excluded FROM A BAND when the
        median nearest-neighbour distance between distinct coordinates exceeds b/2
  §8    balance: population-weighted SMD on pct_black, poverty, income, tenure, degree
  A1.1  exposure years come from each city's OWN observed span inside the window
  A1.2  Detroit's effective window starts 2021 (its charge code has no earlier coverage)

Every exclusion here is decided on geometry, population, or coordinates. None is decided
on an outcome. The rules were fixed before any multi-city rate existed.

    python displacement/multi_city_boundary_design.py
    python displacement/multi_city_boundary_design.py --window all
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd
from scipy.spatial import cKDTree

ROOT = Path(r"D:/Gun Violence")
CITIES = ROOT / "displacement/data/cities"
CRS = 5070
BANDS = [150, 250, 500, 1000]
PRIMARY = ("2019-01-01", "2023-12-31")
MIN_POP, MIN_N = 500, 30                      # §4.4
YEAR_COVERAGE_FLOOR = 0.01                    # A1.2: a year holding <1% is not coverage

# slug -> (HOLC city names, state FIPS for the tract file)
# NEW YORK IS ONE UNIT (§3): five borough surveys, one police department, one state code.
UNITS = {
    "chicago":      (["Chicago"], "17"),
    "philadelphia": (["Philadelphia"], "42"),
    "nyc":          (["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"], "36"),
    "detroit":      (["Detroit"], "26"),
    "baltimore":    (["Baltimore"], "24"),
    "los_angeles":  (["Los Angeles"], "06"),
    "seattle":      (["Seattle"], "53"),
    # --- Wave 2, admitted by Amendment 5 after the A5.3 gate ---
    "kansas_city":  (["Greater Kansas City"], "29"),
    "milwaukee":    (["Milwaukee Co."], "55"),
    "boston":       (["Boston"], "25"),
    "dallas":       (["Dallas"], "48"),
}

# A C/D pair straddling a STATE LINE is not a within-city comparison (§3): it crosses two
# police departments and two legal regimes. The HOLC file labels every "Greater Kansas
# City" polygon state=MO, but 38 of its 87 C/D polygons -- including 16 of 40 grade D --
# lie WEST of the state line, in Kansas City, KANSAS. KCPD data covers Missouri only, so
# those polygons would contribute population and ZERO events regardless of true violence.
# Clip to the state whose police data we actually hold.
CLIP_TO_STATE = {"kansas_city": "29"}
_STATE_GEOM: dict = {}


def state_union(fips):
    """Union of a state's tracts, as the clipping geometry. Cached per process."""
    if fips not in _STATE_GEOM:
        g = gpd.read_file(ROOT / f"demographics/tract_boundaries/by_state/tl_2024_{fips}_tract.zip")
        _STATE_GEOM[fips] = g.to_crs(CRS).union_all()
    return _STATE_GEOM[fips]


def holc_for(slug, names, holc):
    """City's C/D polygons, clipped to the police jurisdiction's state where required.
    Every script that builds bands must go through this, so the clip cannot be applied
    in one place and forgotten in another."""
    g = holc[holc.city.isin(names)].copy()
    fips = CLIP_TO_STATE.get(slug)
    if fips and len(g):
        keep = state_union(fips)
        g["geometry"] = g.geometry.intersection(keep)
        g = g[~g.geometry.is_empty & g.geometry.notna()]
    return g

COVARS = {                                     # §8
    "pct_black":  ("B02001", "B02001_003E", "B02001_001E"),
    "pct_poverty": ("B17001", "B17001_002E", "B17001_001E"),
    "pct_owner":  ("B25003", "B25003_002E", "B25003_001E"),
    "med_income": ("B19013", "B19013_001E", None),
}


# ====================================================================== inputs
def load_tracts(state):
    g = gpd.read_file(ROOT / f"demographics/tract_boundaries/by_state/tl_2024_{state}_tract.zip")
    g = g[["GEOID", "geometry"]].to_crs(CRS)
    pop = pd.read_parquet(ROOT / "demographics/acs_5yr/acs5_2023_B01001_tract.parquet")
    pop["GEOID"] = (pop.state.astype(str).str.zfill(2) + pop.county.astype(str).str.zfill(3)
                    + pop.tract.astype(str).str.zfill(6))
    pop["pop"] = pd.to_numeric(pop.B01001_001E, errors="coerce")
    g = g.merge(pop[["GEOID", "pop"]], on="GEOID", how="left")

    for name, (tbl, num, den) in COVARS.items():
        c = pd.read_parquet(ROOT / f"demographics/acs_5yr/acs5_2023_{tbl}_tract.parquet")
        c["GEOID"] = (c.state.astype(str).str.zfill(2) + c.county.astype(str).str.zfill(3)
                      + c.tract.astype(str).str.zfill(6))
        n = pd.to_numeric(c[num], errors="coerce")
        if den is None:
            v = n.where(n >= 0)                # ACS medians use negative sentinels
        else:
            d = pd.to_numeric(c[den], errors="coerce")
            v = 100 * n / d.where(d > 0)
        g = g.merge(pd.DataFrame({"GEOID": c.GEOID, name: v}), on="GEOID", how="left")

    # education needs a sum over the bachelor's-and-above columns
    e = pd.read_parquet(ROOT / "demographics/acs_5yr/acs5_2023_B15003_tract.parquet")
    e["GEOID"] = (e.state.astype(str).str.zfill(2) + e.county.astype(str).str.zfill(3)
                  + e.tract.astype(str).str.zfill(6))
    hi = [f"B15003_{i:03d}E" for i in (22, 23, 24, 25)]
    num = sum(pd.to_numeric(e[c], errors="coerce") for c in hi)
    den = pd.to_numeric(e["B15003_001E"], errors="coerce")
    g = g.merge(pd.DataFrame({"GEOID": e.GEOID, "pct_degree": 100 * num / den.where(den > 0)}),
                on="GEOID", how="left")

    g = g[g["pop"].notna() & (g.area > 0)].copy()
    g["tract_area"] = g.area
    return g


def interp(geom, tr, tidx):
    """Areal interpolation + population-weighted covariate means inside `geom`."""
    if geom.is_empty:
        return 0.0, {}
    cand = tr.iloc[list(tidx.query(geom, predicate="intersects"))]
    if not len(cand):
        return 0.0, {}
    inter = cand.geometry.intersection(geom)
    frac = (inter.area / cand.tract_area).values
    w = cand["pop"].values * frac                      # people of this tract in the band
    total = float(np.nansum(w))
    stats = {}
    for c in list(COVARS) + ["pct_degree"]:
        x = pd.to_numeric(cand[c], errors="coerce").values
        m = np.isfinite(x) & np.isfinite(w) & (w > 0)
        if m.sum() < 2 or w[m].sum() <= 0:
            stats[c] = (np.nan, np.nan, 0)
            continue
        mu = float(np.average(x[m], weights=w[m]))
        var = float(np.average((x[m] - mu) ** 2, weights=w[m]))
        stats[c] = (mu, np.sqrt(var), int(m.sum()))
    return total, stats


def smd(a, b):
    """Standardized mean difference from (mean, sd, n) tuples. Pooled SD denominator."""
    (ma, sa, na), (mb, sb, nb) = a, b
    if not np.isfinite(ma) or not np.isfinite(mb):
        return np.nan
    sp = np.sqrt((sa ** 2 + sb ** 2) / 2)
    return np.nan if not np.isfinite(sp) or sp == 0 else (ma - mb) / sp


def effective_window(d, window):
    """A1.1/A1.2 — exposure comes from the city's OWN sustained coverage.

    A calendar year holding <1% of the city's in-window events is not coverage; it is a
    handful of stray records under a charge code that did not yet exist. Detroit has 1
    record in 2019 and 2 in 2020 against 863/748/659 in 2021-23. Counting 2019-2023 as
    five years of exposure there would understate its rate by 40%."""
    w = d[d.date.between(*window)] if window != "all" else d
    if not len(w):
        return w, 0.0, None, None, []
    yc = w.groupby(w.date.dt.year).size()
    keep = yc[yc / yc.sum() >= YEAR_COVERAGE_FLOOR].index
    dropped = sorted(int(y) for y in yc.index if y not in keep)
    w = w[w.date.dt.year.isin(keep)]
    if not len(w):
        return w, 0.0, None, None, dropped
    yrs = (w.date.max() - w.date.min()).days / 365.25
    return w, max(yrs, 1e-9), w.date.min().date(), w.date.max().date(), dropped


def precision(pts_xy):
    """§4.7 — median nearest-neighbour distance between DISTINCT coordinates, metres."""
    u = np.unique(pts_xy, axis=0)
    if len(u) < 2:
        return np.inf
    dist, _ = cKDTree(u).query(u, k=2)
    return float(np.median(dist[:, 1]))


# ====================================================================== main
def main():
    """Runner. Kept under a guard so audit_bands.py can import the helpers
    above and audit THE SAME CODE rather than a copy of it."""
    window = "all" if "--window" in sys.argv and "all" in sys.argv else PRIMARY
    wlab = "all years" if window == "all" else f"{window[0]}..{window[1]}"

    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]

    print("=" * 108)
    print(f"MULTI-CITY HOLC BOUNDARY DESIGN — window {wlab}")
    print("PRE_REG_MULTICITY_2026_09_11.md · per-city only, NO pooling in this file (§5.2)")
    print("=" * 108)

    rows, notes = [], {}
    for slug, (names, st) in UNITS.items():
        f = CITIES / f"{slug}.parquet"
        man = CITIES / f"{slug}_manifest.json"
        if not f.exists():
            m = json.loads(man.read_text(encoding="utf-8")) if man.exists() else {}
            notes[slug] = f"MISSING — no cache ({m.get('status','absent')})"
            print(f"\n{slug}: MISSING, excluded. Not zero.")     # never 0 for a failed fetch
            continue

        d = pd.read_parquet(f)
        w, yrs, dmin, dmax, dropped_yrs = effective_window(d, window)
        g = holc_for(slug, names, holc)
        if not len(g) or not {"C", "D"} <= set(g.grade):
            notes[slug] = "no C/D pair in HOLC"
            continue

        tr = load_tracts(st)
        tidx = tr.sindex
        Du, Cu = g[g.grade == "D"].union_all(), g[g.grade == "C"].union_all()
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        xy = np.c_[pts.geometry.x.values, pts.geometry.y.values]
        nnd = precision(xy)

        city = w.city.iloc[0] if len(w) else slug
        print(f"\n{city}  ({len(names)} HOLC survey{'s' if len(names) > 1 else ''}, "
              f"C={int((g.grade=='C').sum())} D={int((g.grade=='D').sum())})")
        print(f"   effective window {dmin}..{dmax}  = {yrs:.2f} exposure yrs, n={len(w):,}"
              + (f"   [A1.2: dropped sub-1% years {dropped_yrs}]" if dropped_yrs else ""))
        print(f"   §4.7 median nearest-neighbour distance between distinct coords: {nnd:,.0f} m")

        for b in BANDS:
            dband = Du.intersection(Cu.boundary.buffer(b))
            cband = Cu.intersection(Du.boundary.buffer(b))
            if dband.is_empty or cband.is_empty:
                continue
            pD, sD = interp(dband, tr, tidx)
            pC, sC = interp(cband, tr, tidx)
            nD = int(pts.within(dband).sum())
            nC = int(pts.within(cband).sum())

            # --- pre-specified, outcome-blind exclusions -------------------------
            excl = []
            if nnd > b / 2:
                excl.append(f"§4.7 precision (nn {nnd:.0f}m > {b/2:.0f}m)")
                print(f"   {b:>5}m  EXCLUDED — §4.7 precision: nearest-neighbour {nnd:,.0f} m "
                      f"exceeds half the band ({b/2:.0f} m)")
            if pD < MIN_POP or pC < MIN_POP:
                excl.append(f"§4.4 population (D={pD:.0f}, C={pC:.0f})")
            if nD + nC < MIN_N:
                excl.append(f"§4.4 n (n_D+n_C={nD+nC})")

            rD = 1e5 * nD / pD / yrs if pD > 0 and yrs > 0 else np.nan
            rC = 1e5 * nC / pC / yrs if pC > 0 and yrs > 0 else np.nan
            rr = rD / rC if rC and np.isfinite(rC) and rC > 0 else np.nan
            se = np.sqrt(1 / max(nD, 1) + 1 / max(nC, 1))

            r = dict(slug=slug, city=city, band=b, n_D=nD, n_C=nC, pop_D=pD, pop_C=pC,
                     rate_D=rD, rate_C=rC, rr=rr, log_rr=np.log(rr) if rr and rr > 0 else np.nan,
                     se_log_rr=se,
                     lo=np.exp(np.log(rr) - 1.96 * se) if rr and rr > 0 else np.nan,
                     hi=np.exp(np.log(rr) + 1.96 * se) if rr and rr > 0 else np.nan,
                     years=yrs, win_start=str(dmin), win_end=str(dmax), nn_dist_m=nnd,
                     included=not excl, exclusion="; ".join(excl))
            for c in list(COVARS) + ["pct_degree"]:
                r[f"smd_{c}"] = smd(sD.get(c, (np.nan,) * 3), sC.get(c, (np.nan,) * 3))
                r[f"D_{c}"] = sD.get(c, (np.nan,) * 3)[0]
                r[f"C_{c}"] = sC.get(c, (np.nan,) * 3)[0]
            rows.append(r)

            if not excl:
                print(f"   {b:>5}m  n_D={nD:>6,} n_C={nC:>6,}  pop {pD:>9,.0f}/{pC:>9,.0f}  "
                      f"rate {rD:>7.1f}/{rC:>7.1f}  RR={rr:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]  "
                      f"SMD_black={r['smd_pct_black']:+.3f}")
            elif "§4.7" not in " ".join(excl):
                print(f"   {b:>5}m  EXCLUDED — {'; '.join(excl)}")

    res = pd.DataFrame(rows)
    out = ROOT / ("displacement/multi_city_rates.csv" if window != "all"
                  else "displacement/multi_city_rates_allyears.csv")
    res.to_csv(out, index=False)

    # ---------------------------------------------------------------- summary
    p = res[(res.band == 250)]
    print("\n" + "=" * 108)
    print("PRIMARY BAND (250 m) — per city. NOT POOLED HERE (§5.2 pooling lives in meta_analysis.py)")
    print("=" * 108)
    if len(p):
        show = p[["city", "n_D", "n_C", "rate_D", "rate_C", "rr", "lo", "hi",
                  "smd_pct_black", "included", "exclusion"]].copy()
        for c in ("rate_D", "rate_C"):
            show[c] = show[c].round(1)
        for c in ("rr", "lo", "hi", "smd_pct_black"):
            show[c] = show[c].round(3)
        print(show.to_string(index=False))

    print("\n§8 BALANCE at 250 m — SMD, D band minus C band (pooled-SD denominator)")
    bal = p[["city"] + [f"smd_{c}" for c in list(COVARS) + ["pct_degree"]]].round(3)
    print(bal.to_string(index=False))
    flag = p[(p.smd_pct_black.abs() > 0.25)]
    print(f"\n§8 flagged on |SMD pct_black| > 0.25: "
          f"{list(flag.city) if len(flag) else 'none'}")
    if notes:
        print(f"\nunits not estimated: {notes}")
    print(f"\nwrote {out.relative_to(ROOT)}")



if __name__ == "__main__":
    main()
