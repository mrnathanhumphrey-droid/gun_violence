"""ORIGIN-SIDE TEST — did sundown counties lose, or never have, Black population?

The displacement thesis says exclusion at the origin pushed people toward graded
urban destinations. Its origin-side prediction is that sundown counties show Black
population LOSS or failure-to-grow across 1900-1950, relative to non-sundown counties
in the SAME state.

There is a rival reading that must be separated before any of this means anything:

    EXPULSION   sundown counties HAD Black residents in 1900 and lost them.
    NEVER-HAD   sundown counties were already almost entirely white in 1900, and
                the modern "sundown" label records a settled fact rather than an
                expulsion event.

These make different predictions about the 1900 BASELINE, and only the first supports
displacement. The Loewen/Rigby data carries no founding dates, so this is a trajectory
comparison across the era, not an event study.

Data: NHGIS county race counts 1900-1950 (extract nhgis0012, verified codebooks), joined
to the repo's own county sundown assignment (historical_features_county_v04.parquet).

    python displacement/origin_side_test.py
"""
from __future__ import annotations
import io, sys, zipfile
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, mannwhitneyu

ROOT = Path(r"D:/Gun Violence")
ZIP = ROOT / "displacement/data/nhgis/nhgis0012_csv.zip"
OUT = ROOT / "displacement"

# Black male/female column codes per year, verified against the delivered codebooks
BLACK = {"1900": ["AZ3003", "AZ3004"], "1910": ["A30003", "A30004"],
         "1920": ["A8L005", "A8L006"], "1930": ["BC7003", "BC7004"],
         "1940": ["BV2003", "BV2004"], "1950": ["B3P003", "B3P007"]}
YEARS = list(BLACK)


def gisjoin_to_fips(s):
    """NHGIS pads each FIPS field with a trailing zero: G + state(3) + county(4)."""
    return s.str[1:4].str[:2] + s.str[4:8].str[:3]


def read(pat):
    z = zipfile.ZipFile(ZIP)
    f = [x for x in z.namelist() if x.endswith(".csv") and pat in x][0]
    d = pd.read_csv(io.BytesIO(z.read(f)), low_memory=False)
    return d.iloc[1:].reset_index(drop=True)          # drop NHGIS description row


# ------------------------------------------------------------------ build the panel
frames = []
for y in YEARS:
    d = read(f"_{y}_")
    cols = BLACK[y]
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["black"] = d[cols].sum(axis=1)
    frames.append(d[["GISJOIN", "black"]].assign(year=int(y)))
panel = pd.concat(frames, ignore_index=True)

ts = read("_ts_nominal_")
tot = ts.melt(id_vars=["GISJOIN"], value_vars=[f"A00AA{y}" for y in YEARS],
              var_name="v", value_name="total")
tot["year"] = tot.v.str[-4:].astype(int)
tot["total"] = pd.to_numeric(tot.total, errors="coerce")
panel = panel.merge(tot[["GISJOIN", "year", "total"]], on=["GISJOIN", "year"], how="inner")

# balanced panel only — counties observed in all six decades
keep = panel.groupby("GISJOIN").year.nunique().eq(len(YEARS))
panel = panel[panel.GISJOIN.isin(keep[keep].index)].copy()
panel["fips"] = gisjoin_to_fips(panel.GISJOIN)
panel["black_share"] = 100 * panel.black / panel.total
panel = panel[panel.total > 0]
print(f"balanced panel: {panel.GISJOIN.nunique():,} counties x {len(YEARS)} decades")

# ------------------------------------------------------------------ sundown assignment
h = pd.read_parquet(ROOT / "analysis/historical_features_county_v04.parquet")
h["fips"] = h.state.astype(str).str.zfill(2) + h.county.astype(str).str.zfill(3)
panel = panel.merge(h[["fips", "sundown_n"]], on="fips", how="inner")
panel["sundown"] = (panel.sundown_n > 0).astype(int)
panel["st"] = panel.fips.str[:2]
n_cty = panel.GISJOIN.nunique()
n_sd = panel[panel.sundown == 1].GISJOIN.nunique()
print(f"matched to modern county sundown assignment: {n_cty:,} counties "
      f"({n_sd:,} sundown, {n_cty-n_sd:,} not)\n")

w = panel.pivot_table(index=["fips", "st", "sundown"], columns="year",
                      values="black_share").reset_index()
w = w.dropna(subset=[1900, 1950])

print("=" * 78)
print("Q1  THE 1900 BASELINE — expulsion, or never-had?")
print("=" * 78)
a, b = w[w.sundown == 1][1900], w[w.sundown == 0][1900]
print(f"  Black population share in 1900")
print(f"    sundown counties     median {a.median():6.2f}%   mean {a.mean():6.2f}%   n={len(a)}")
print(f"    non-sundown counties median {b.median():6.2f}%   mean {b.mean():6.2f}%   n={len(b)}")
print(f"    Mann-Whitney p = {mannwhitneyu(a, b).pvalue:.3g}")
print(f"    sundown counties with >=1% Black in 1900: {100*(a>=1).mean():.0f}%  "
      f"(non-sundown {100*(b>=1).mean():.0f}%)")
print(f"    sundown counties with >=5% Black in 1900: {100*(a>=5).mean():.0f}%  "
      f"(non-sundown {100*(b>=5).mean():.0f}%)")

print("\n" + "=" * 78)
print("Q2  TRAJECTORY 1900 -> 1950, WITHIN STATE")
print("=" * 78)
w["chg"] = w[1950] - w[1900]
rec = []
for st, gg in w.groupby("st"):
    s1, s0 = gg[gg.sundown == 1], gg[gg.sundown == 0]
    if len(s1) < 5 or len(s0) < 5:
        continue
    rec.append(dict(st=st, n1=len(s1), n0=len(s0),
                    d1=s1.chg.median(), d0=s0.chg.median(),
                    diff=s1.chg.median() - s0.chg.median(),
                    base1=s1[1900].median(), base0=s0[1900].median()))
r = pd.DataFrame(rec)
print(f"  states testable (>=5 counties each side): {len(r)}")
print(f"  states where sundown counties fell MORE in Black share: "
      f"{(r['diff'] < 0).sum()} / {len(r)}")
wx = wilcoxon(r["diff"])
print(f"  Wilcoxon signed-rank on within-state differences: p = {wx.pvalue:.4g}")
print(f"  median within-state difference: {r['diff'].median():+.3f} pp")
print(f"\n  {'state':<7}{'n_sd':>6}{'n_non':>7}{'base_sd':>9}{'base_non':>10}"
      f"{'chg_sd':>9}{'chg_non':>9}{'diff':>8}")
for _, x in r.sort_values("diff").head(12).iterrows():
    print(f"  {x.st:<7}{int(x.n1):>6}{int(x.n0):>7}{x.base1:>9.2f}{x.base0:>10.2f}"
          f"{x.d1:>9.2f}{x.d0:>9.2f}{x['diff']:>8.2f}")

print("\n" + "=" * 78)
print("Q3  FULL TRAJECTORY (median Black share by decade)")
print("=" * 78)
print(f"  {'group':<24}" + "".join(f"{y:>9}" for y in YEARS))
for lab, m in (("sundown counties", w.sundown == 1), ("non-sundown counties", w.sundown == 0)):
    print(f"  {lab:<24}" + "".join(f"{w[m][int(y)].median():>9.2f}" for y in YEARS))

w.to_csv(OUT / "origin_side_panel.csv", index=False)
print(f"\nwrote {OUT/'origin_side_panel.csv'}")
