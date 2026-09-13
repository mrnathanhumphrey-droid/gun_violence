"""HOLC BOUNDARY DESIGN — firearm-violence RATES across a redlining grade line.

Incident counts alone are not a result: 263 D-side vs 259 C-side incidents says nothing
until there is population at risk on each side. This builds the denominators.

DESIGN
  Within each HOLC-surveyed city, for a band width b:
      D-side band = (union of D polygons) INTERSECT buffer(boundary of C polygons, b)
      C-side band = (union of C polygons) INTERSECT buffer(boundary of D polygons, b)
  i.e. the strip of each grade lying within b metres of the other grade -- the same rule
  used for the incident-level balance check, so counts and denominators agree.

  Population is areal-interpolated from 2023 ACS tracts: each tract contributes population
  in proportion to the share of its area falling inside the band. This assumes population
  is uniform within a tract, which is the standard assumption and a real limitation --
  stated, not hidden.

  The comparison is WITHIN CITY by construction, so state, city, policing, firearm law and
  regional culture are all held fixed. Covariate balance was verified separately
  (mean |SMD| 0.072 at 250 m; pct_black SMD -0.021), so racial composition is held fixed by
  the design rather than by conditioning on it.

  Outcome: GVA incidents 2013-2026 (mass shootings, 4+ victims -- NOT general firearm
  homicide). Denominator is a 2023 ACS snapshot against a 2013-2026 numerator.

    python displacement/holc_boundary_rates.py
"""
from __future__ import annotations
import sys, glob, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import poisson

ROOT = Path(r"D:/Gun Violence")
CRS = 5070
BANDS = [250, 500]

# ------------------------------------------------------------------ inputs
h = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
h["grade"] = h.grade.astype(str).str.strip()
h = h[h.grade.isin(["C", "D"])].to_crs(CRS)
h = h[h.geometry.notna() & h.geometry.is_valid & ~h.geometry.is_empty]
print(f"HOLC C/D polygons: {len(h)} across {h.city.nunique()} cities")

g = pd.read_csv(ROOT / "outcomes/gva/Gun-Violence-Data/data/gva_master.csv", low_memory=False)
pts = gpd.GeoDataFrame(g, geometry=gpd.points_from_xy(g.longitude, g.latitude),
                       crs=4326).to_crs(CRS)

tr = []
for f in sorted(glob.glob(str(ROOT / "demographics/tract_boundaries/by_state/*.zip"))):
    tr.append(gpd.read_file(f)[["GEOID", "geometry"]])
tracts = gpd.GeoDataFrame(pd.concat(tr, ignore_index=True), geometry="geometry",
                          crs=4269).to_crs(CRS)
pop = pd.read_parquet(ROOT / "demographics/acs_5yr/acs5_2023_B01001_tract.parquet")
pop["GEOID"] = (pop.state.astype(str).str.zfill(2) + pop.county.astype(str).str.zfill(3)
                + pop.tract.astype(str).str.zfill(6))
pop["pop"] = pd.to_numeric(pop.B01001_001E, errors="coerce")
tracts = tracts.merge(pop[["GEOID", "pop"]], on="GEOID", how="left")
tracts = tracts[tracts["pop"].notna() & (tracts.area > 0)].copy()
tracts["tract_area"] = tracts.area
print(f"tracts with population: {len(tracts):,}\n")
tidx = tracts.sindex


def interp_pop(geom):
    """Areal interpolation: population share of each tract by area overlap."""
    if geom.is_empty:
        return 0.0
    cand = tracts.iloc[list(tidx.query(geom, predicate="intersects"))]
    if not len(cand):
        return 0.0
    inter = cand.geometry.intersection(geom)
    frac = inter.area / cand.tract_area
    return float((cand["pop"].values * frac.values).sum())


rows = []
for b in BANDS:
    for city, gg in h.groupby("city"):
        D, C = gg[gg.grade == "D"], gg[gg.grade == "C"]
        if not len(D) or not len(C):
            continue
        Du, Cu = D.union_all(), C.union_all()
        dband = Du.intersection(Cu.boundary.buffer(b))
        cband = Cu.intersection(Du.boundary.buffer(b))
        if dband.is_empty or cband.is_empty:
            continue
        pd_, pc_ = interp_pop(dband), interp_pop(cband)
        if pd_ < 500 or pc_ < 500:          # too little population for a rate
            continue
        nd = int(pts.within(dband).sum())
        nc = int(pts.within(cband).sum())
        rows.append(dict(band=b, city=city, state=gg.state.iloc[0],
                         pop_D=pd_, pop_C=pc_, n_D=nd, n_C=nc,
                         area_D=dband.area / 1e6, area_C=cband.area / 1e6))
    print(f"band {b} m: {sum(1 for r in rows if r['band']==b)} cities with both sides populated")

r = pd.DataFrame(rows)
r.to_csv(ROOT / "displacement/holc_boundary_rates.csv", index=False)

RATE = 1e5
for b in BANDS:
    s = r[r.band == b]
    ND, NC = s.n_D.sum(), s.n_C.sum()
    PD, PC = s.pop_D.sum(), s.pop_C.sum()
    rd, rc = RATE * ND / PD, RATE * NC / PC
    rr = rd / rc
    # exact Poisson CI for the rate ratio, conditioning on the total
    lo, hi = poisson.interval(0.95, ND) if ND else (0, 0)
    se = np.sqrt(1 / max(ND, 1) + 1 / max(NC, 1))
    l95, u95 = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
    print("\n" + "=" * 76)
    print(f"BAND {b} m   ({len(s)} cities, {s.state.nunique()} states)")
    print("=" * 76)
    print(f"  D side : {ND:>5} incidents / {PD:>12,.0f} people = {rd:6.2f} per 100k")
    print(f"  C side : {NC:>5} incidents / {PC:>12,.0f} people = {rc:6.2f} per 100k")
    print(f"  RATE RATIO D/C = {rr:.3f}   95% CI [{l95:.3f}, {u95:.3f}]")
    # within-city paired test, cities with incidents on either side
    p = s[(s.n_D + s.n_C) > 0].copy()
    p["rate_D"] = RATE * p.n_D / p.pop_D
    p["rate_C"] = RATE * p.n_C / p.pop_C
    higher = int((p.rate_D > p.rate_C).sum())
    from scipy.stats import wilcoxon
    try:
        wp = wilcoxon(p.rate_D - p.rate_C).pvalue
    except Exception:
        wp = float("nan")
    print(f"  within-city: D rate higher in {higher} of {len(p)} cities   Wilcoxon p={wp:.4g}")
    print(f"  population balance D/C = {PD/PC:.3f}   area balance = {s.area_D.sum()/s.area_C.sum():.3f}")

print(f"\nwrote displacement/holc_boundary_rates.csv")
