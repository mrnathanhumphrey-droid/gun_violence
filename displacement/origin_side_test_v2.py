"""ORIGIN-SIDE TEST v2 — with county-level sundown entries restored.

DEFECT FOUND VIA POSITIVE CONTROL
  Forsyth County GA (the Oscarville expulsion, 1912) shows a textbook collapse in the
  census panel: Black share 9.38% (1900) -> 9.20% (1910) -> 0.26% (1920). Adjacent
  Dawson GA, expelled the same year, 3.24% -> 0.00%. Adjacent Hall GA, not expelled,
  drifts 15.77% -> 13.02%. The MEASUREMENT works.

  But Forsyth was coded sundown=0. Rigby's `type` field is:
      place 1951 | county 205 | county subdivision 137 | no match 54
  and the repo's county assignment joined sundown TOWNS to counties through a place
  gazetteer, so all 342 county / county-subdivision entries were dropped. Forsyth is
  `type=county`, `matching_county=13117`, `confidence_level=Surely` -- fully coded in the
  source, silently absent from the analysis variable.

  These are systematically the WHOLE-COUNTY exclusions, i.e. the most complete ones and
  the ones where the largest population collapse is expected. The misclassification is
  therefore non-random and attenuates toward the null.

v2 restores county-type entries (matching_county, authoritative in Rigby) on top of the
existing place-based count, and re-runs the origin-side test.

    python displacement/origin_side_test_v2.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, mannwhitneyu

ROOT = Path(r"D:/Gun Violence")
YEARS = ["1900", "1910", "1920", "1930", "1940", "1950"]

w = pd.read_csv(ROOT / "displacement/origin_side_panel.csv")
w.columns = [str(c) for c in w.columns]
w["fips"] = w.fips.astype(str).str.zfill(5)
w["st"] = w.fips.str[:2]

# ---- restore county-level sundown entries ------------------------------------------
r = pd.read_csv(ROOT / "historical_mechanism/sundown_towns_rigby_2025/sundown_linked_to_census.csv",
                low_memory=False)
cty = r[r.type.astype(str).str.strip().eq("county") & r.matching_county.notna()].copy()
cty["mc"] = cty.matching_county.astype(str).str.strip()
# 201/205 are clean 5-digit FIPS. 3 are multi-county lists with no state prefix
# ('061,103,083') and 1 is a bare 3-digit code ('133'); their state cannot be recovered
# without guessing, so they are DROPPED and counted, not imputed.
bad = cty[~cty.mc.str.fullmatch(r"\d{5}")]
cty = cty[cty.mc.str.fullmatch(r"\d{5}")].copy()
cty["fips"] = cty.mc
add = cty.groupby("fips").size().rename("sundown_county_entries").reset_index()
print(f"county-type sundown entries restored: {len(cty)} rows -> {len(add)} counties "
      f"({len(bad)} dropped: unrecoverable county codes {sorted(set(bad.mc))})")

w = w.merge(add, on="fips", how="left")
w["sundown_county_entries"] = w.sundown_county_entries.fillna(0)
w["sundown_v2"] = ((w.sundown == 1) | (w.sundown_county_entries > 0)).astype(int)

n1, n2 = int(w.sundown.sum()), int(w.sundown_v2.sum())
newly = w[(w.sundown == 0) & (w.sundown_v2 == 1)]
print(f"sundown counties: v1 {n1}  ->  v2 {n2}   (+{n2-n1})")
print(f"Forsyth GA now flagged: {int(w.loc[w.fips=='13117','sundown_v2'].iloc[0]) if (w.fips=='13117').any() else 'not in panel'}")
print(f"newly flagged counties' median 1900 Black share: {newly['1900'].median():.2f}%  "
      f"(previously-flagged {w[w.sundown==1]['1900'].median():.2f}%, "
      f"never-flagged {w[w.sundown_v2==0]['1900'].median():.2f}%)\n")

# ---- Q1 baseline -------------------------------------------------------------------
print("=" * 78)
print("Q1  1900 BASELINE  (v2 treatment)")
print("=" * 78)
a, b = w[w.sundown_v2 == 1]["1900"], w[w.sundown_v2 == 0]["1900"]
print(f"  sundown     median {a.median():6.2f}%  mean {a.mean():6.2f}%  >=5% Black: {100*(a>=5).mean():3.0f}%  n={len(a)}")
print(f"  non-sundown median {b.median():6.2f}%  mean {b.mean():6.2f}%  >=5% Black: {100*(b>=5).mean():3.0f}%  n={len(b)}")
print(f"  Mann-Whitney p = {mannwhitneyu(a, b).pvalue:.3g}")

# ---- Q2 relative trajectory --------------------------------------------------------
v = w[w["1900"] > 0].copy()
v["logchg"] = np.log((v["1950"] + 0.01) / (v["1900"] + 0.01))
print("\n" + "=" * 78)
print("Q2  RELATIVE TRAJECTORY 1900->1950, WITHIN STATE  (v2 treatment)")
print("=" * 78)
for lab, sub in (("all counties with 1900 Black>0", v),
                 ("counties with >=5% Black in 1900", v[v["1900"] >= 5])):
    rec = []
    for st, g in sub.groupby("st"):
        s1, s0 = g[g.sundown_v2 == 1], g[g.sundown_v2 == 0]
        if len(s1) < 5 or len(s0) < 5:
            continue
        rec.append(s1.logchg.median() - s0.logchg.median())
    if len(rec) < 3:
        print(f"  {lab:<34} too few states"); continue
    p = wilcoxon(rec).pvalue
    print(f"  {lab:<34} states={len(rec):>3}  sundown fell more in {sum(1 for x in rec if x<0):>3}"
          f"  median diff {np.median(rec):+.3f}  Wilcoxon p={p:.4g}")

# ---- Q3 the expulsion signature: sharp collapses ------------------------------------
print("\n" + "=" * 78)
print("Q3  EXPULSION EVENTS — sharp one-decade collapses, not average drift")
print("=" * 78)
print("  An expulsion is a rare discontinuous event; means and medians wash it out.")
print("  Definition: a county-decade with >=2% Black share falling by >=50% in ten years.\n")
long = w.melt(id_vars=["fips", "st", "sundown_v2"], value_vars=YEARS,
              var_name="year", value_name="share")
long["year"] = long.year.astype(int)
long = long.sort_values(["fips", "year"])
long["prev"] = long.groupby("fips").share.shift(1)
long["drop"] = 1 - long.share / long.prev
ev = long[(long.prev >= 2) & (long["drop"] >= 0.5)]
cnt = ev.groupby("fips").size().rename("n_events").reset_index()
flag = w[["fips", "sundown_v2"]].merge(cnt, on="fips", how="left").fillna({"n_events": 0})
elig = w[w[YEARS].max(axis=1) >= 2]
print(f"  counties ever >=2% Black: {len(elig)}")
for lab, col in (("v1 treatment", "sundown"), ("v2 treatment", "sundown_v2")):
    e = elig.merge(cnt, on="fips", how="left").fillna({"n_events": 0})
    s1, s0 = e[e[col] == 1], e[e[col] == 0]
    r1 = 100 * (s1.n_events > 0).mean()
    r0 = 100 * (s0.n_events > 0).mean()
    from scipy.stats import fisher_exact
    tab = [[int((s1.n_events > 0).sum()), int((s1.n_events == 0).sum())],
           [int((s0.n_events > 0).sum()), int((s0.n_events == 0).sum())]]
    orr, pf = fisher_exact(tab)
    print(f"  {lab}: expulsion-event rate  sundown {r1:5.1f}% (n={len(s1)})  "
          f"non-sundown {r0:5.1f}% (n={len(s0)})   OR={orr:.2f}  Fisher p={pf:.3g}")

print("\n  largest collapses in the panel (any county):")
top = ev.sort_values("drop", ascending=False).head(10)
for _, x in top.iterrows():
    sd = int(w.loc[w.fips == x.fips, "sundown_v2"].iloc[0])
    print(f"    {x.fips}  {x.year-10}->{x.year}  {x.prev:6.2f}% -> {x.share:5.2f}%  "
          f"({100*x['drop']:.0f}% drop)  sundown_v2={sd}")

w.to_csv(ROOT / "displacement/origin_side_panel_v2.csv", index=False)
print(f"\nwrote displacement/origin_side_panel_v2.csv")
