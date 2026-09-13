"""AUDIT OF THE BAND CONSTRUCTION — the two checks that must pass before pooling.

The meta-analysis inherits every defect in the per-city numbers, so these run first.

AUDIT A — DO THE DENOMINATORS BEHAVE?
  Every band rate is benchmarked against rates computed by the SAME interpolation code
  on much larger polygons (the whole D grade, the whole C grade, the entire HOLC
  footprint), and against an EXTERNAL citywide rate from ACS county population.
  For Baltimore (24510), Philadelphia (42101) and New York (5 counties) city and county
  are the same geography, so that external benchmark is exact. For Chicago, Detroit,
  Los Angeles and Seattle the county strictly CONTAINS the city, so the citywide rate is
  an UNDER-estimate and the band/citywide ratio an OVER-estimate -- labelled, not hidden.
  A band rate far out of line with the larger-polygon rates means the interpolation is
  failing at band scale, which is exactly where high-vacancy cities are most suspect.

AUDIT B — IS A "BAND" ACTUALLY AN EDGE STRIP?
  The D band is  D ∩ buffer(boundary(C), b).  A D polygon smaller than the band width
  enters ENTIRELY -- it stops being an edge strip and becomes a whole neighbourhood.
  Baltimore has NINE D polygons in total, so if most of its D band is whole polygons
  then "Baltimore's D side" is two named places and the estimate is not about D-ness.

  The band is decomposed into one piece per polygon, which yields in a single pass:
    - absorbed fraction  piece area / polygon area   (1.0 = the whole polygon is in)
    - the share of band population and events contributed by fully-absorbed polygons
    - concentration: the share of band events from the single largest contributing polygon
    - an EXACT leave-one-polygon-out jackknife of the rate ratio

  If dropping one polygon flips a city's sign, that city's estimate is one neighbourhood.

    python displacement/audit_bands.py
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (holc_for, UNITS, load_tracts, interp, effective_window,
                                        precision, ROOT, CRS, PRIMARY)

BAND = 250
# county FIPS whose geography EQUALS the city, so the external benchmark is exact
EXACT_COUNTY = {"baltimore": ["24510"], "philadelphia": ["42101"],
                "nyc": ["36005", "36047", "36061", "36081", "36085"]}
APPROX_COUNTY = {"chicago": ["17031"], "detroit": ["26163"],
                 "los_angeles": ["06037"], "seattle": ["53033"]}

cpop = pd.read_parquet(ROOT / "demographics/acs_5yr/acs5_2023_B01001_county.parquet")
cpop["fips"] = cpop.state.astype(str).str.zfill(2) + cpop.county.astype(str).str.zfill(3)
cpop["pop"] = pd.to_numeric(cpop.B01001_001E, errors="coerce")
CPOP = dict(zip(cpop.fips, cpop["pop"]))

holc_all = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
holc_all["grade"] = holc_all.grade.astype(str).str.strip()
holc_all = holc_all.to_crs(CRS)
holc_all = holc_all[holc_all.geometry.notna() & holc_all.geometry.is_valid
                    & ~holc_all.geometry.is_empty]

print("=" * 112)
print(f"AUDIT OF THE BAND CONSTRUCTION — primary band {BAND} m, window {PRIMARY[0]}..{PRIMARY[1]}")
print("=" * 112)

A_rows, B_rows, J_rows = [], [], []

for slug, (names, st) in UNITS.items():
    f = ROOT / f"displacement/data/cities/{slug}.parquet"
    if not f.exists():
        print(f"\n{slug}: MISSING cache — skipped, not zero")
        continue
    d = pd.read_parquet(f)
    w, yrs, dmin, dmax, _ = effective_window(d, PRIMARY)
    city = w.city.iloc[0]
    g = holc_for(slug, names, holc_all)
    gcd = g[g.grade.isin(["C", "D"])]
    tr = load_tracts(st)
    tidx = tr.sindex
    pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                           crs=4326).to_crs(CRS)

    D = gcd[gcd.grade == "D"].reset_index(drop=True)
    C = gcd[gcd.grade == "C"].reset_index(drop=True)
    Du, Cu = D.union_all(), C.union_all()
    Fu = g.union_all()                              # entire HOLC footprint, all grades

    band = BAND
    dband = Du.intersection(Cu.boundary.buffer(band))
    cband = Cu.intersection(Du.boundary.buffer(band))

    # ---------------------------------------------------------- AUDIT A
    def rate(geom):
        p, _ = interp(geom, tr, tidx)
        n = int(pts.within(geom).sum())
        return n, p, (1e5 * n / p / yrs if p > 0 else np.nan)

    nDb, pDb, rDb = rate(dband)
    nCb, pCb, rCb = rate(cband)
    nDw, pDw, rDw = rate(Du)
    nCw, pCw, rCw = rate(Cu)
    nF, pF, rF = rate(Fu)

    cty = EXACT_COUNTY.get(slug) or APPROX_COUNTY.get(slug, [])
    exact = slug in EXACT_COUNTY
    cp = sum(CPOP.get(c, np.nan) for c in cty) if cty else np.nan
    r_city = 1e5 * len(w) / cp / yrs if cp and np.isfinite(cp) else np.nan

    print(f"\n{'='*112}\n{city}   window {dmin}..{dmax} ({yrs:.2f} yrs), n={len(w):,}")
    print(f"{'='*112}")
    print(f"  AUDIT A — rates per 100k/yr, all from the same interpolation code")
    print(f"    D band  ({band} m) : n={nDb:>6,}  pop={pDb:>10,.0f}  rate={rDb:>8.1f}")
    print(f"    C band  ({band} m) : n={nCb:>6,}  pop={pCb:>10,.0f}  rate={rCb:>8.1f}")
    print(f"    D grade, entire    : n={nDw:>6,}  pop={pDw:>10,.0f}  rate={rDw:>8.1f}")
    print(f"    C grade, entire    : n={nCw:>6,}  pop={pCw:>10,.0f}  rate={rCw:>8.1f}")
    print(f"    HOLC footprint     : n={nF:>6,}  pop={pF:>10,.0f}  rate={rF:>8.1f}")
    lab = "EXACT (city = county)" if exact else "APPROX (county ⊇ city ⇒ rate UNDERstated)"
    print(f"    citywide, ACS county {','.join(cty) if cty else '--':<28}"
          f" pop={cp:>10,.0f}  rate={r_city:>8.1f}   [{lab}]")
    if np.isfinite(r_city) and r_city > 0:
        print(f"    band/citywide ratio: D {rDb/r_city:5.2f}x   C {rCb/r_city:5.2f}x"
              + ("" if exact else "   (both OVERstated)"))
    A_rows.append(dict(city=city, n_Dband=nDb, n_Cband=nCb, rate_Dband=rDb, rate_Cband=rCb,
                       rate_Dgrade=rDw, rate_Cgrade=rCw, rate_footprint=rF,
                       rate_citywide=r_city, county_exact=exact,
                       ratio_D=rDb / r_city if r_city else np.nan,
                       ratio_C=rCb / r_city if r_city else np.nan))

    # ---------------------------------------------------------- AUDIT B
    def pieces(poly_gdf, other_union, label):
        """Decompose the band into one piece per polygon: absorbed share, pop, events."""
        buf = other_union.boundary.buffer(band)
        out = []
        for i, row in poly_gdf.iterrows():
            geom = row.geometry
            pc = geom.intersection(buf)
            if pc.is_empty:
                continue
            p, _ = interp(pc, tr, tidx)
            n = int(pts.within(pc).sum())
            out.append(dict(idx=i, grade=label, absorbed=pc.area / geom.area if geom.area else 0,
                            piece_area_km2=pc.area / 1e6, pop=p, n=n))
        return pd.DataFrame(out)

    dp = pieces(D, Cu, "D")
    cp_ = pieces(C, Du, "C")

    for lab, pc_df, n_tot, p_tot in (("D", dp, nDb, pDb), ("C", cp_, nCb, pCb)):
        if not len(pc_df):
            continue
        full = pc_df[pc_df.absorbed > 0.95]
        top = pc_df.sort_values("n", ascending=False).head(1)
        print(f"  AUDIT B — {lab} band: {len(pc_df)} contributing polygons of "
              f"{len(D) if lab=='D' else len(C)}")
        print(f"      fully absorbed (>95% of polygon inside band): {len(full)} polygons, "
              f"{100*full['pop'].sum()/max(p_tot,1):.1f}% of band population, "
              f"{100*full.n.sum()/max(n_tot,1):.1f}% of band events")
        print(f"      largest single polygon contributes "
              f"{100*float(top.n.iloc[0])/max(n_tot,1):.1f}% of band events")
        B_rows.append(dict(city=city, grade=lab, n_polys_total=len(D) if lab == "D" else len(C),
                           n_polys_contrib=len(pc_df), n_fully_absorbed=len(full),
                           pct_pop_fully_absorbed=100 * full["pop"].sum() / max(p_tot, 1),
                           pct_events_fully_absorbed=100 * full.n.sum() / max(n_tot, 1),
                           pct_events_top_poly=100 * float(top.n.iloc[0]) / max(n_tot, 1)))

    # ---- exact leave-one-polygon-out jackknife of the rate ratio -------------
    base_rr = (nDb / pDb) / (nCb / pCb) if pDb and pCb and nCb else np.nan
    jk = []
    for lab, pc_df, n_tot, p_tot in (("D", dp, nDb, pDb), ("C", cp_, nCb, pCb)):
        for _, r in pc_df.iterrows():
            if lab == "D":
                nd, pd_, nc, pc2 = n_tot - r.n, p_tot - r["pop"], nCb, pCb
            else:
                nd, pd_, nc, pc2 = nDb, pDb, n_tot - r.n, p_tot - r["pop"]
            if pd_ <= 0 or pc2 <= 0 or nc <= 0:
                continue
            jk.append(((nd / pd_) / (nc / pc2), lab, int(r.idx), int(r.n)))
    if jk:
        vals = np.array([x[0] for x in jk])
        lo_i, hi_i = int(np.argmin(vals)), int(np.argmax(vals))
        flips = int(((vals - 1) * (base_rr - 1) < 0).sum())
        print(f"  AUDIT B — leave-one-polygon-out jackknife of RR (base {base_rr:.3f}):")
        print(f"      range [{vals.min():.3f}, {vals.max():.3f}] over {len(vals)} polygons")
        print(f"      most influential: drop {jk[lo_i][1]}#{jk[lo_i][2]} -> {vals.min():.3f} | "
              f"drop {jk[hi_i][1]}#{jk[hi_i][2]} -> {vals.max():.3f}")
        print(f"      SIGN FLIPS (RR crosses 1) on dropping a single polygon: {flips}"
              + ("   <-- ESTIMATE IS ONE NEIGHBOURHOOD" if flips else ""))
        J_rows.append(dict(city=city, base_rr=base_rr, jk_min=vals.min(), jk_max=vals.max(),
                           n_polys=len(vals), sign_flips=flips))

pd.DataFrame(A_rows).to_csv(ROOT / "displacement/audit_A_rate_benchmark.csv", index=False)
pd.DataFrame(B_rows).to_csv(ROOT / "displacement/audit_B_polygon_composition.csv", index=False)
pd.DataFrame(J_rows).to_csv(ROOT / "displacement/audit_B_jackknife.csv", index=False)

print("\n" + "=" * 112)
print("SUMMARY")
print("=" * 112)
a = pd.DataFrame(A_rows)
print("\nAUDIT A — band rate vs citywide rate (x). Exact-county cities are the real test:")
print(a[["city", "rate_Dband", "rate_Cband", "rate_Dgrade", "rate_Cgrade",
         "rate_footprint", "rate_citywide", "ratio_D", "ratio_C",
         "county_exact"]].round(2).to_string(index=False))
b = pd.DataFrame(B_rows)
print("\nAUDIT B — is the band an edge strip or a set of whole neighbourhoods?")
print(b.round(1).to_string(index=False))
j = pd.DataFrame(J_rows)
print("\nAUDIT B — leave-one-polygon-out jackknife:")
print(j.round(3).to_string(index=False))
print("\nwrote audit_A_rate_benchmark.csv, audit_B_polygon_composition.csv, audit_B_jackknife.csv")
