"""NORMALISED RETENTION — each county indexed to ITS OWN historical Black population.

THE CORRECTION (Nate, 2026-09-10)
  Every previous test gated eligibility on an ABSOLUTE share floor (">=2% Black"). That
  structurally excludes the typical sundown county: median sundown share is 0.63% in 1870,
  so such a county can lose its entire Black population and never once enter the test. The
  comparison was therefore being made only among counties that looked like non-sundown
  counties to begin with.

  Fix: index each county to its OWN historical level. Eligibility becomes a COUNT floor --
  enough people for a percentage to be numerically stable -- rather than a share floor,
  which is a statement about what kind of county qualifies.

    peak       max Black COUNT over 1870-1890 (before the sundown wave)
    retention  Black count in 1950 / peak count, that county's own scale
    eligible   peak count >= FLOOR (default 25 persons)

  Retention is bounded below by 0 and is directly comparable across counties of wildly
  different composition, which share-based measures are not.

    python displacement/normalized_retention_test.py
"""
from __future__ import annotations
import io, sys, zipfile, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon, fisher_exact

ROOT = Path(r"D:/Gun Violence")
MAIN = ROOT / "displacement/data/nhgis/nhgis0012_csv.zip"
PRE = ROOT / "displacement/data/nhgis_preperiod/nhgis0013_csv.zip"
BLACK = {"1870": (PRE, ["AK3002"]), "1880": (PRE, ["APP002"]), "1890": (PRE, ["AV0007", "AV0008"]),
         "1900": (MAIN, ["AZ3003", "AZ3004"]), "1910": (MAIN, ["A30003", "A30004"]),
         "1920": (MAIN, ["A8L005", "A8L006"]), "1930": (MAIN, ["BC7003", "BC7004"]),
         "1940": (MAIN, ["BV2003", "BV2004"]), "1950": (MAIN, ["B3P003", "B3P007"])}
PRE_YEARS = ["1870", "1880", "1890"]
FLOOR = 25


def read(zp, pat):
    z = zipfile.ZipFile(zp)
    f = [x for x in z.namelist() if x.endswith(".csv") and pat in x][0]
    return pd.read_csv(io.BytesIO(z.read(f)), low_memory=False).iloc[1:].reset_index(drop=True)


rows = []
for y, (zp, cols) in BLACK.items():
    d = read(zp, f"_{y}_")
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["black"] = d[cols].sum(axis=1)
    d["fips"] = d.GISJOIN.str[1:4].str[:2] + d.GISJOIN.str[4:8].str[:3]
    rows.append(d[["fips", "black"]].assign(year=int(y)))
cnt = pd.concat(rows, ignore_index=True)
wide = cnt.pivot_table(index="fips", columns="year", values="black", aggfunc="sum")
wide.columns = [str(c) for c in wide.columns]
wide = wide.dropna()
print(f"counties with Black counts in all nine decades: {len(wide):,}")

# treatment (either source), from the circularity-test panel
t = pd.read_csv(ROOT / "displacement/origin_side_panel_v3.csv")
t.columns = [str(c) for c in t.columns]
t["fips"] = t.fips.astype(str).str.zfill(5)
t["sd"] = t.sundown_v2.astype(bool) | t.n_entries.notna()
d = wide.reset_index().merge(t[["fips", "sd", "any_mechanism"]], on="fips", how="inner")
d["any_mechanism"] = d.any_mechanism.fillna(False).astype(bool)
d["st"] = d.fips.str[:2]
d["peak"] = d[PRE_YEARS].max(axis=1)
d["peak_share_yr"] = d[PRE_YEARS].idxmax(axis=1)
print(f"matched to treatment: {len(d):,} counties ({int(d.sd.sum()):,} sundown)\n")

# ---------------------------------------------------------------- what the old rule cost
print("=" * 84)
print("WHAT THE ABSOLUTE SHARE FLOOR WAS EXCLUDING")
print("=" * 84)
p = pd.read_csv(ROOT / "displacement/panel_1870_1950.csv")
p.columns = [str(c) for c in p.columns]
p["fips"] = p.fips.astype(str).str.zfill(5)
share_elig = set(p[p[[str(y) for y in BLACK]].max(axis=1) >= 2].fips)
for lab, m in (("sundown", d.sd), ("non-sundown", ~d.sd)):
    tot = int(m.sum())
    old = int(d[m].fips.isin(share_elig).sum())
    new = int((d[m].peak >= FLOOR).sum())
    print(f"  {lab:<14} n={tot:>5}   eligible under >=2% share: {old:>5} ({100*old/tot:4.1f}%)"
          f"   under >={FLOOR}-person peak: {new:>5} ({100*new/tot:4.1f}%)")
print("\n  The share floor admitted a far smaller and differently-composed set of sundown")
print("  counties; the count floor asks only whether a percentage is stable.\n")

e = d[d.peak >= FLOOR].copy()
e["retention"] = e["1950"] / e.peak
print(f"eligible counties (peak >= {FLOOR}): {len(e):,} "
      f"({int(e.sd.sum()):,} sundown, {int((~e.sd).sum()):,} not)\n")

# ---------------------------------------------------------------- retention
print("=" * 84)
print(f"RETENTION — 1950 Black count as a fraction of that county's own 1870-1890 peak")
print("=" * 84)
a, b = e[e.sd].retention, e[~e.sd].retention
print(f"  sundown      median {a.median():6.3f}   mean {a.mean():6.3f}   n={len(a)}")
print(f"  non-sundown  median {b.median():6.3f}   mean {b.mean():6.3f}   n={len(b)}")
print(f"  Mann-Whitney p = {mannwhitneyu(a, b).pvalue:.3g}")
for thr in (0.5, 0.25, 0.10):
    print(f"  lost >={100*(1-thr):.0f}% of peak:  sundown {100*(a<thr).mean():5.1f}%   "
          f"non-sundown {100*(b<thr).mean():5.1f}%")

print("\n  within state (median retention difference, sundown - non-sundown):")
rec = []
for st, g in e.groupby("st"):
    s1, s0 = g[g.sd], g[~g.sd]
    if len(s1) < 5 or len(s0) < 5:
        continue
    rec.append(s1.retention.median() - s0.retention.median())
if len(rec) >= 3:
    print(f"    states={len(rec)}   sundown retained LESS in {sum(1 for x in rec if x<0)}"
          f"   median diff {np.median(rec):+.3f}   Wilcoxon p={wilcoxon(rec).pvalue:.4g}")

# ---------------------------------------------------------------- mechanism subset
print("\n" + "=" * 84)
print("SAME, MECHANISM-DOCUMENTED SUNDOWN COUNTIES ONLY")
print("=" * 84)
am = e[e.sd & e.any_mechanism].retention
print(f"  mechanism-documented  median {am.median():6.3f}  n={len(am)}")
print(f"  never-sundown control median {b.median():6.3f}  n={len(b)}")
print(f"  Mann-Whitney p = {mannwhitneyu(am, b).pvalue:.3g}")

# ---------------------------------------------------------------- near-total loss
print("\n" + "=" * 84)
print("NEAR-TOTAL LOSS  (retained <10% of own peak) — the expulsion signature, normalised")
print("=" * 84)
e["wipe"] = e.retention < 0.10
tab = [[int(e[e.sd].wipe.sum()), int((~e[e.sd].wipe).sum())],
       [int(e[~e.sd].wipe.sum()), int((~e[~e.sd].wipe).sum())]]
orr, pv = fisher_exact(tab)
print(f"  sundown {100*e[e.sd].wipe.mean():5.1f}% (n={int(e.sd.sum())})   "
      f"non-sundown {100*e[~e.sd].wipe.mean():5.1f}% (n={int((~e.sd).sum())})   "
      f"OR={orr:.2f}  p={pv:.3g}")

e.to_csv(ROOT / "displacement/normalized_retention.csv", index=False)
print(f"\nwrote displacement/normalized_retention.csv")
