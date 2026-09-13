"""CASE-DEFINITION SENSITIVITY — does the Baltimore reversal survive a narrower outcome?

WHY, AND WHY IT IS SYMMETRIC

  Baltimore's pre-registered case definition (§4.3) is "any Part 1 offense with a firearm
  weapon code". Under the firearm filter that set includes LARCENY, LARCENY FROM AUTO,
  AUTO THEFT, BURGLARY and ARSON alongside HOMICIDE and SHOOTING. Chicago and
  Philadelphia, by contrast, count people who were SHOT. If armed robbery and armed
  property crime follow commercial corridors rather than residential violence, Baltimore's
  reversal could be an artefact of the outcome rather than a fact about the boundary.

  TESTING ONLY THE CITY THAT REVERSED WOULD BE RIGGED. Handing Baltimore a chance to
  "repair" itself that no other city gets is a shared choice one step removed -- it moves
  which arm is flattered. So the identical decomposition runs on LOS ANGELES too, the
  other offense-level city, which did NOT reverse. Chicago and Philadelphia are already
  shooting-only by construction and serve as the reference.

  The PRE-REGISTERED definition remains primary (§4.3 forbids changing it). This is a
  disclosed sensitivity that diagnoses the reversal; it does not replace the estimate.

    python displacement/case_definition_test.py
"""
from __future__ import annotations
import sys, json, time, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd, requests

sys.path.insert(0, str(Path(__file__).parent))
from multi_city_boundary_design import (load_tracts, interp, effective_window, ROOT, CRS, PRIMARY)
from fetch_city_shootings import get, socrata_pages, ags_pages, epoch_ms, classify_weapons

BAND = 250
CACHE = ROOT / "displacement/data/cities"

# ---------------------------------------------------------------- Baltimore strata
BAL_GUNS = ["FIREARM", "HANDGUN", "RIFLE", "SHOTGUN", "OTHER_FIREARM", "AUTOMATIC_FIREARM",
            "AUTOMATIC_HANDGUN", "AUTOMATIC_RIFLE", "AUTOMATIC_OTHER_FIREARM"]
BAL_STRATA = {
    "D1 PRE-REGISTERED (all Part 1 w/ firearm)": None,
    "D2 SHOOTING ONLY (someone was shot)": ["HOMICIDE", "SHOOTING"],
    "D3 INTERPERSONAL VIOLENCE": ["HOMICIDE", "SHOOTING", "AGG. ASSAULT", "COMMON ASSAULT", "RAPE"],
    "D4 ROBBERY ONLY": ["ROBBERY", "ROBBERY - CARJACKING", "ROBBERY - COMMERCIAL"],
    "D5 PROPERTY ONLY": ["ARSON", "AUTO THEFT", "BURGLARY", "LARCENY", "LARCENY FROM AUTO"],
}


def fetch_baltimore():
    f = CACHE / "baltimore_desc.parquet"
    if f.exists():
        return pd.read_parquet(f)
    layer = ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/"
             "Part1_Crime/FeatureServer/0")
    where = "Weapon IN (" + ",".join(f"'{g}'" for g in BAL_GUNS) + ")"
    d = ags_pages(layer, where, ["CrimeDateTime", "Latitude", "Longitude", "Weapon", "Description"])
    d["date"] = epoch_ms(d["CrimeDateTime"])
    d = d.rename(columns={"Latitude": "lat", "Longitude": "lon"})
    d["lat"] = pd.to_numeric(d.lat, errors="coerce")
    d["lon"] = pd.to_numeric(d.lon, errors="coerce")
    d = d.dropna(subset=["lat", "lon", "date"])
    d = d[~((d.lat == 0) & (d.lon == 0))]
    d = d[d.lat.between(17, 72) & d.lon.between(-180, -65)]
    d["city"] = "Baltimore"
    d = d[["city", "date", "lat", "lon", "Description"]].reset_index(drop=True)
    d.to_parquet(f, index=False)
    return d


def fetch_la():
    f = CACHE / "los_angeles_desc.parquet"
    if f.exists():
        return pd.read_parquet(f)
    srcs = ["https://data.lacity.org/resource/2nrs-mtv8.json",
            "https://data.lacity.org/resource/63jg-8b9z.json"]
    vals = set()
    for u in srcs:
        j = get(u, {"$select": "weapon_desc,weapon_used_cd", "$group": "weapon_desc,weapon_used_cd",
                    "$limit": 1000}).json()
        vals |= {(r.get("weapon_used_cd"), r.get("weapon_desc")) for r in j if r.get("weapon_desc")}
    keep, _ = classify_weapons(sorted({d for _, d in vals}))
    codes = sorted({c for c, dd in vals if dd in set(keep) and c})
    inlist = "(" + ",".join(f"'{c}'" for c in codes) + ")"
    parts = []
    for u in srcs:
        parts.append(socrata_pages(u, {"$select": "date_occ,lat,lon,crm_cd_desc",
                                       "$where": f"weapon_used_cd IN {inlist}"}))
    d = pd.concat(parts, ignore_index=True).rename(columns={"date_occ": "date"})
    d["lat"] = pd.to_numeric(d.lat, errors="coerce")
    d["lon"] = pd.to_numeric(d.lon, errors="coerce")
    d["date"] = pd.to_datetime(d.date, errors="coerce")
    d = d.dropna(subset=["lat", "lon", "date"])
    d = d[~((d.lat == 0) & (d.lon == 0))]
    d = d[d.lat.between(17, 72) & d.lon.between(-180, -65)]
    d["city"] = "Los Angeles"
    d = d[["city", "date", "lat", "lon", "crm_cd_desc"]].reset_index(drop=True)
    d.to_parquet(f, index=False)
    return d


def la_strata(descs):
    """Classify LA crime descriptions into the SAME strata as Baltimore, by meaning."""
    up = {d: str(d).upper() for d in descs}
    shoot = [d for d, s in up.items() if "HOMICIDE" in s or "SHOT" in s or "SHOOTING" in s
             or "MANSLAUGHTER" in s]
    rob = [d for d, s in up.items() if "ROBBERY" in s or "CARJACK" in s or "EXTORTION" in s]
    prop = [d for d, s in up.items() if any(k in s for k in
            ("BURGLARY", "THEFT", "STOLEN", "VANDALISM", "ARSON", "SHOPLIFT", "EMBEZZL",
             "BUNCO", "TRESPASS", "PICKPOCKET", "PURSE"))]
    viol = [d for d, s in up.items() if d in shoot or any(k in s for k in
            ("ASSAULT", "BATTERY", "RAPE", "KIDNAP", "THREAT", "CHILD", "SPOUSAL",
             "LEWD", "SEXUAL", "INTIMATE"))]
    return {"D1 PRE-REGISTERED (all firearm offenses)": None,
            "D2 SHOOTING ONLY (someone was shot)": shoot,
            "D3 INTERPERSONAL VIOLENCE": sorted(set(viol)),
            "D4 ROBBERY ONLY": rob,
            "D5 PROPERTY ONLY": prop}


def run_city(slug, names, st, d, colname, strata):
    holc = gpd.read_file(ROOT / "historical_mechanism/holc_redlining/mappinginequality.json")
    holc["grade"] = holc.grade.astype(str).str.strip()
    holc = holc[holc.city.isin(names) & holc.grade.isin(["C", "D"])].to_crs(CRS)
    holc = holc[holc.geometry.notna() & holc.geometry.is_valid & ~holc.geometry.is_empty]
    Du, Cu = holc[holc.grade == "D"].union_all(), holc[holc.grade == "C"].union_all()
    dband = Du.intersection(Cu.boundary.buffer(BAND))
    cband = Cu.intersection(Du.boundary.buffer(BAND))
    tr = load_tracts(st)
    tidx = tr.sindex
    pD, _ = interp(dband, tr, tidx)
    pC, _ = interp(cband, tr, tidx)

    out = []
    print(f"\n{'='*104}\n{slug.upper()} — case-definition sensitivity at {BAND} m "
          f"(band populations D={pD:,.0f}  C={pC:,.0f})\n{'='*104}")
    print(f"  {'definition':<44}{'n_D':>7}{'n_C':>7}{'RR':>9}{'95% CI':>20}  share of D1")
    for lab, vals in strata.items():
        sub = d if vals is None else d[d[colname].isin(vals)]
        w, yrs, _, _, _ = effective_window(sub, PRIMARY)
        if not len(w):
            print(f"  {lab:<44}   no events in window")
            continue
        pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat),
                               crs=4326).to_crs(CRS)
        nD = int(pts.within(dband).sum())
        nC = int(pts.within(cband).sum())
        if nD + nC < 30:
            print(f"  {lab:<44}{nD:>7}{nC:>7}   too few (n<30)")
            continue
        rr = (nD / pD) / (nC / pC)
        se = np.sqrt(1 / max(nD, 1) + 1 / max(nC, 1))
        lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
        base = out[0]["n_D"] + out[0]["n_C"] if out else nD + nC
        print(f"  {lab:<44}{nD:>7,}{nC:>7,}{rr:>9.3f}   [{lo:.3f}, {hi:.3f}]"
              f"{100*(nD+nC)/base:>10.1f}%")
        out.append(dict(city=slug, definition=lab, n_D=nD, n_C=nC, rr=rr, lo=lo, hi=hi,
                        years=yrs, share_of_D1=100 * (nD + nC) / base))
    return out


rows = []
bal = fetch_baltimore()
print(f"Baltimore w/ Description: {len(bal):,} firearm offenses")
rows += run_city("baltimore", ["Baltimore"], "24", bal, "Description", BAL_STRATA)

la = fetch_la()
print(f"\nLos Angeles w/ crm_cd_desc: {len(la):,} firearm offenses, "
      f"{la.crm_cd_desc.nunique()} distinct descriptions")
ls = la_strata(la.crm_cd_desc.dropna().unique())
for k, v in ls.items():
    if v is not None:
        print(f"   {k:<40} {len(v)} descriptions, e.g. {sorted(v)[:3]}")
rows += run_city("los_angeles", ["Los Angeles"], "06", la, "crm_cd_desc", ls)

r = pd.DataFrame(rows)
r.to_csv(ROOT / "displacement/case_definition_test.csv", index=False)

print("\n" + "=" * 104)
print("VERDICT")
print("=" * 104)
for city in r.city.unique():
    s = r[r.city == city]
    d1 = s[s.definition.str.startswith("D1")].rr.iloc[0]
    d2 = s[s.definition.str.startswith("D2")]
    if len(d2):
        print(f"  {city:<14} pre-registered RR {d1:.3f}  ->  shooting-only RR {d2.rr.iloc[0]:.3f}"
              f"  [{d2.lo.iloc[0]:.3f}, {d2.hi.iloc[0]:.3f}]   (n={d2.n_D.iloc[0]+d2.n_C.iloc[0]:,})")
print("\nwrote displacement/case_definition_test.csv")
