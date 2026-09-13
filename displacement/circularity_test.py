"""CIRCULARITY TEST — is the sundown/expulsion association definitional?

THE THREAT
  The expulsion-event finding (sundown counties are ~2.8x more likely to show a sharp
  one-decade collapse in Black population share) is only evidence if the sundown coding
  was made INDEPENDENTLY of the census. Loewen's identification method partly used census
  patterns -- an all-white town surrounded by Black population was one of his signals. If
  documentation depended on observing the absence, then "sundown counties had collapses"
  is partly a restatement of the coding rule.

THE TEST
  Rigby records WHY each entity is classified sundown, in `exclusion_method`. Split it:

    MECHANISM-documented (independent of census outcome)
        Violent Expulsion, Threat of Violence, Police or Other Official Action,
        Zoning, Realtors, Violence Towards Newcomers, Private Bad Behavior, Other
    OUTCOME-adjacent (could be inferred from absence)
        Reputation, Unknown

  Re-run the expulsion-event test using ONLY mechanism-documented counties as treated.
  If the odds ratio survives there, circularity is largely answered.

  Stated in advance: `Unknown` is 1,305 of 2,347 records, so the clean subset is small and
  an underpowered result is a live possibility. Underpowered is NOT the same as null and
  will be reported as such.

GEOGRAPHY
  exclusion_method is recorded per town, so towns must be placed in counties:
    type=county   -> matching_county (5-digit FIPS), authoritative
    type=place    -> Census Places gazetteer centroid -> spatial join to county
  County-subdivision and no-match entries are excluded and counted.

    python displacement/circularity_test.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, geopandas as gpd
from scipy.stats import fisher_exact

ROOT = Path(r"D:/Gun Violence")
YEARS = ["1900", "1910", "1920", "1930", "1940", "1950"]

MECHANISM = ["Violent Expulsion", "Threat of Violence", "Police or Other Official Action",
             "Zoning", "Realtors", "Violence Towards Newcomers", "Private Bad Behavior",
             "Other"]
OUTCOME_ADJACENT = ["Reputation", "Unknown"]

r = pd.read_csv(ROOT / "historical_mechanism/sundown_towns_rigby_2025/sundown_linked_to_census.csv",
                low_memory=False)
r["method"] = r.exclusion_method.fillna("Unknown").astype(str).str.strip()


def classify(m):
    # values can be concatenations, e.g. "Violent ExpulsionReputation"
    if any(k in m for k in MECHANISM):
        return "mechanism"
    return "outcome_adjacent"


r["basis"] = r.method.map(classify)
print("documentation basis, all Rigby records:")
print(r.basis.value_counts().to_string(), "\n")

# ---------------------------------------------------------------- towns -> counties
# county-type: authoritative FIPS
cty = r[r.type.astype(str).str.strip().eq("county")].copy()
cty["mc"] = cty.matching_county.astype(str).str.strip()
cty = cty[cty.mc.str.fullmatch(r"\d{5}")]
cty["fips"] = cty.mc

# place-type: gazetteer centroid -> county polygon
g = pd.read_csv(ROOT / "geographic/census_places_gaz_2024/2024_Gaz_place_national.txt",
                sep="\t", dtype=str)
g.columns = [c.strip() for c in g.columns]
for c in ("GEOID", "INTPTLAT", "INTPTLONG"):
    g[c] = g[c].str.strip()
st = dict(zip(g.USPS, g.GEOID.str[:2]))

pl = r[r.type.astype(str).str.strip().eq("place")].copy()
pl["place5"] = pl.contemporary_place_match.astype(str).str.extract(r"PLACE[:](\d{5})", flags=2)[0]
pl["place5"] = pl.place5.fillna(pl.contemporary_place_match.astype(str).str.extract(r"[:](\d{5})")[0])
pl["gaz"] = pl.state.map(st) + pl.place5
pl = pl.merge(g[["GEOID", "INTPTLAT", "INTPTLONG"]], left_on="gaz", right_on="GEOID", how="left")
ok = pl.INTPTLAT.notna()
print(f"place entries geocoded via gazetteer: {int(ok.sum())} / {len(pl)}")
pl = pl[ok].copy()
pts = gpd.GeoDataFrame(pl, geometry=gpd.points_from_xy(pl.INTPTLONG.astype(float),
                                                       pl.INTPTLAT.astype(float)), crs=4326)
cnty = gpd.read_file(ROOT / "demographics/tract_boundaries/tl_2024_us_county.zip")[["GEOID", "geometry"]]
pts = gpd.sjoin(pts.to_crs(5070), cnty.to_crs(5070), how="left", predicate="within")
print(f"placed in a county by spatial join:     {int(pts.GEOID_right.notna().sum() if 'GEOID_right' in pts else pts.GEOID.notna().sum())} / {len(pts)}")
gcol = "GEOID_right" if "GEOID_right" in pts.columns else "GEOID"
pts = pts[pts[gcol].notna()].copy()
pts["fips"] = pts[gcol]

allsd = pd.concat([cty[["fips", "basis"]], pts[["fips", "basis"]]], ignore_index=True)
excluded = len(r) - len(cty) - len(pl)
print(f"county-subdivision / no-match entries excluded: {excluded}\n")

by_cty = allsd.groupby("fips").basis.agg(
    any_mechanism=lambda s: (s == "mechanism").any(),
    n_entries="size").reset_index()
print(f"sundown counties resolved: {len(by_cty)}  "
      f"of which mechanism-documented: {int(by_cty.any_mechanism.sum())}\n")

# ---------------------------------------------------------------- expulsion events
w = pd.read_csv(ROOT / "displacement/origin_side_panel_v2.csv")
w.columns = [str(c) for c in w.columns]
w["fips"] = w.fips.astype(str).str.zfill(5)
w = w.merge(by_cty, on="fips", how="left")
w["any_mechanism"] = w.any_mechanism.fillna(False)
# Control must be counties sundown by NEITHER source. The v2 flag is Tougaloo-derived and
# the Rigby resolution above is independent; 48 counties are sundown in Rigby but absent
# from v2, and leaving them among the controls biases every OR toward the null.
w["rigby_sd"] = w.n_entries.notna()
w["clean_control"] = (~w.sundown_v2.astype(bool)) & (~w.rigby_sd)
w["sundown_any_src"] = w.sundown_v2.astype(bool) | w.rigby_sd
print(f"control cleaned: {int((~w.sundown_v2.astype(bool)).sum())} -> "
      f"{int(w.clean_control.sum())} counties "
      f"({int(((~w.sundown_v2.astype(bool)) & w.rigby_sd).sum())} known-sundown removed)\n")

long = w.melt(id_vars=["fips"], value_vars=YEARS, var_name="year", value_name="share")
long["year"] = long.year.astype(int)
long = long.sort_values(["fips", "year"])
long["prev"] = long.groupby("fips").share.shift(1)
long["drop"] = 1 - long.share / long.prev


def event_test(base, dr, treat_mask, label, elig_extra=None):
    ev = long[(long.prev >= base) & (long["drop"] >= dr)]
    hit = set(ev.fips)
    e = w[w[YEARS].max(axis=1) >= base].copy()
    if elig_extra is not None:
        e = e[elig_extra(e)]
    e["event"] = e.fips.isin(hit)
    t = e[treat_mask(e)]
    c = e[e.clean_control]                     # sundown by NEITHER source
    if len(t) < 15:
        return f"  {label:<42} n_treated={len(t):<4} TOO FEW"
    tab = [[int(t.event.sum()), int((~t.event).sum())],
           [int(c.event.sum()), int((~c.event).sum())]]
    orr, p = fisher_exact(tab)
    return (f"  {label:<42} treated {100*t.event.mean():5.1f}% (n={len(t):>4})  "
            f"control {100*c.event.mean():5.1f}% (n={len(c):>4})  OR={orr:5.2f}  p={p:.3g}")


print("=" * 96)
print("EXPULSION-EVENT TEST BY DOCUMENTATION BASIS   (control = never-sundown counties)")
print("=" * 96)
for base, dr in [(2, 0.5), (1, 0.5), (2, 0.3), (5, 0.5)]:
    print(f"\n  threshold: baseline >={base}% Black, drop >={int(dr*100)}%")
    print(event_test(base, dr, lambda e: e.sundown_any_src,
                     "ALL sundown counties (either source)"))
    print(event_test(base, dr, lambda e: e.sundown_any_src & e.any_mechanism,
                     "MECHANISM-documented only"))
    print(event_test(base, dr, lambda e: e.sundown_any_src & ~e.any_mechanism,
                     "outcome-adjacent only (Reputation/Unknown)"))

w.to_csv(ROOT / "displacement/origin_side_panel_v3.csv", index=False)
print(f"\nwrote displacement/origin_side_panel_v3.csv")
