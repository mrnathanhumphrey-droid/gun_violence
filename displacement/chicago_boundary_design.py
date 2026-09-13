"""CHICAGO HOLC BOUNDARY DESIGN — firearm victimization rates across a redlining grade line.

WHY CHICAGO
  The national GVA file is the mass-shooting subset: 5,871 incidents, of which only 521 fall
  in a 250 m band around a C/D boundary. That produced a rate ratio of 1.15 with a CI of
  [0.97, 1.36] -- underpowered, not null. Chicago's own victim-level file carries 60,009
  firearm victimizations with coordinates, and Chicago has the largest HOLC footprint in the
  sample. One city can settle what the national mass-shooting file cannot.

  This is deliberately a WITHIN-CITY design. State, city, policing, firearm law and regional
  culture are held fixed by construction, and the covariate balance check showed racial
  composition is balanced across these boundaries (pct_black SMD -0.021 at 250 m), so race is
  held fixed by the design rather than by conditioning on it.

DATA
  Outcome    data.cityofchicago.org gumc-mgzr, "Violence Reduction - Victims of Homicides
             and Non-Fatal Shootings", filtered to gunshot_injury_i = YES.
  Denominator 2023 ACS tract population, areal-interpolated into each band (assumes uniform
             density within tract -- the standard assumption and a real limitation).
  Grades     HOLC C and D polygons for Chicago, Mapping Inequality.

  Primary window is 2019-2023 to match the ACS 5-year denominator; all-years is reported as
  a sensitivity.

    python displacement/chicago_boundary_design.py
"""
from __future__ import annotations
import sys, glob, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd, requests

ROOT = Path(r"D:/Gun Violence")
CACHE = ROOT / "displacement/data/chicago_shootings.parquet"
CRS = 5070
BANDS = [150, 250, 500, 1000]
API = "https://data.cityofchicago.org/resource/gumc-mgzr.json"


def fetch():
    if CACHE.exists():
        d = pd.read_parquet(CACHE)
        print(f"cached Chicago firearm victimizations: {len(d):,}")
        return d
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    import time
    out, off, lim = [], 0, 5000       # Socrata 503s on large unauthenticated pages
    while True:
        j = None
        for attempt in range(5):
            try:
                r = requests.get(API, params={"$select": "date,latitude,longitude,"
                                                         "victimization_primary,gunshot_injury_i",
                                              "$limit": lim, "$offset": off,
                                              "$order": ":id"}, timeout=180)
                if r.status_code == 200:
                    j = r.json()
                    break
                time.sleep(2 * (attempt + 1))
            except Exception:
                time.sleep(2 * (attempt + 1))
        if j is None:
            raise RuntimeError(f"failed at offset {off} after retries")
        if not j:
            break
        out.append(pd.DataFrame(j))
        off += lim
        if off % 20000 == 0:
            print(f"   fetched {off:,} ...")
        if len(j) < lim:
            break
    d = pd.concat(out, ignore_index=True)
    d = d[d.gunshot_injury_i.eq("YES")]
    d = d.dropna(subset=["latitude", "longitude"])
    d["latitude"] = pd.to_numeric(d.latitude, errors="coerce")
    d["longitude"] = pd.to_numeric(d.longitude, errors="coerce")
    d["date"] = pd.to_datetime(d.date, errors="coerce")
    d = d.dropna(subset=["latitude", "longitude", "date"])
    d.to_parquet(CACHE, index=False)
    print(f"fetched + cached: {len(d):,} firearm victimizations with coordinates")
    return d


sh = fetch()
print(f"  date range {sh.date.min().date()} .. {sh.date.max().date()}")
print(f"  homicide {int((sh.victimization_primary=='HOMICIDE').sum()):,}  "
      f"non-fatal {int((sh.victimization_primary!='HOMICIDE').sum()):,}\n")

# ------------------------------------------------------------------ geography
h = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
h["grade"] = h.grade.astype(str).str.strip()
h = h[(h.city == "Chicago") & h.grade.isin(["C", "D"])].to_crs(CRS)
h = h[h.geometry.notna() & h.geometry.is_valid & ~h.geometry.is_empty]
print(f"Chicago HOLC polygons: {len(h)}  (C {int((h.grade=='C').sum())}, D {int((h.grade=='D').sum())})")

il = gpd.read_file(ROOT / "demographics/tract_boundaries/by_state/tl_2024_17_tract.zip")[["GEOID", "geometry"]]
pop = pd.read_parquet(ROOT / "demographics/acs_5yr/acs5_2023_B01001_tract.parquet")
pop["GEOID"] = (pop.state.astype(str).str.zfill(2) + pop.county.astype(str).str.zfill(3)
                + pop.tract.astype(str).str.zfill(6))
pop["pop"] = pd.to_numeric(pop.B01001_001E, errors="coerce")
tr = il.merge(pop[["GEOID", "pop"]], on="GEOID", how="left").to_crs(CRS)
tr = tr[tr["pop"].notna() & (tr.area > 0)].copy()
tr["tract_area"] = tr.area
print(f"Illinois tracts with population: {len(tr):,}\n")


def interp_pop(geom):
    if geom.is_empty:
        return 0.0
    cand = tr[tr.intersects(geom)]
    if not len(cand):
        return 0.0
    inter = cand.geometry.intersection(geom)
    return float((cand["pop"].values * (inter.area / cand.tract_area).values).sum())


pts_all = gpd.GeoDataFrame(sh, geometry=gpd.points_from_xy(sh.longitude, sh.latitude),
                           crs=4326).to_crs(CRS)
Du = h[h.grade == "D"].union_all()
Cu = h[h.grade == "C"].union_all()

WINDOWS = {"2019-2023 (matches ACS)": (pts_all.date >= "2019-01-01") & (pts_all.date < "2024-01-01"),
           "all years": pts_all.date.notna()}
YRS = {"2019-2023 (matches ACS)": 5.0, "all years": None}

rows = []
for b in BANDS:
    dband = Du.intersection(Cu.boundary.buffer(b))
    cband = Cu.intersection(Du.boundary.buffer(b))
    pD, pC = interp_pop(dband), interp_pop(cband)
    for wlab, wmask in WINDOWS.items():
        p = pts_all[wmask]
        yrs = YRS[wlab] or (p.date.max() - p.date.min()).days / 365.25
        nD = int(p.within(dband).sum())
        nC = int(p.within(cband).sum())
        rD = 1e5 * nD / pD / yrs
        rC = 1e5 * nC / pC / yrs
        rr = rD / rC
        se = np.sqrt(1 / max(nD, 1) + 1 / max(nC, 1))
        rows.append(dict(band=b, window=wlab, n_D=nD, n_C=nC, pop_D=pD, pop_C=pC,
                         rate_D=rD, rate_C=rC, rr=rr,
                         lo=np.exp(np.log(rr) - 1.96 * se), hi=np.exp(np.log(rr) + 1.96 * se),
                         years=yrs))

r = pd.DataFrame(rows)
r.to_csv(ROOT / "displacement/chicago_boundary_rates.csv", index=False)

for wlab in WINDOWS:
    s = r[r.window == wlab]
    print("=" * 92)
    print(f"CHICAGO — firearm victimization rate per 100k per year, {wlab}")
    print("=" * 92)
    print(f"  {'band':>6}{'n_D':>7}{'n_C':>7}{'pop_D':>11}{'pop_C':>11}"
          f"{'rate_D':>9}{'rate_C':>9}{'RR (D/C)':>11}{'95% CI':>20}")
    for _, x in s.iterrows():
        print(f"  {x.band:>5}m{x.n_D:>7.0f}{x.n_C:>7.0f}{x.pop_D:>11,.0f}{x.pop_C:>11,.0f}"
              f"{x.rate_D:>9.1f}{x.rate_C:>9.1f}{x.rr:>11.3f}"
              f"   [{x.lo:.3f}, {x.hi:.3f}]")
    print()

print("wrote displacement/chicago_boundary_rates.csv")
