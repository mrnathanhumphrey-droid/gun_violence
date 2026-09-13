"""PRE-PERIOD TEST — 1870-1950. Never-had, or did we open the window too late?

The 1900-1950 panel could not distinguish:
  NEVER-HAD           sundown counties were always overwhelmingly white
  WINDOW TOO LATE     the racial-cleansing wave (~1890-1910) largely predates 1900, so a
                      1900 baseline is already post-treatment

A 1870 baseline sits in front of that wave. This extends the panel to nine decades and asks
where in time the collapses actually happen.

    python displacement/preperiod_test.py
"""
from __future__ import annotations
import io, sys, zipfile, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

ROOT = Path(r"D:/Gun Violence")
PRE = ROOT / "displacement/data/nhgis_preperiod/nhgis0013_csv.zip"
BLACK_PRE = {"1870": ["AK3002"], "1880": ["APP002"], "1890": ["AV0007", "AV0008"]}
OLD = ["1900", "1910", "1920", "1930", "1940", "1950"]
ALLY = ["1870", "1880", "1890"] + OLD


def gisjoin_to_fips(s):
    return s.str[1:4].str[:2] + s.str[4:8].str[:3]


def read(zp, pat):
    z = zipfile.ZipFile(zp)
    f = [x for x in z.namelist() if x.endswith(".csv") and pat in x][0]
    return pd.read_csv(io.BytesIO(z.read(f)), low_memory=False).iloc[1:].reset_index(drop=True)


# ---- pre-period race + totals -------------------------------------------------------
frames = []
for y, cols in BLACK_PRE.items():
    d = read(PRE, f"_{y}_")
    for c in cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["black"] = d[cols].sum(axis=1)
    frames.append(d[["GISJOIN", "black"]].assign(year=int(y)))
pre = pd.concat(frames, ignore_index=True)

ts = read(PRE, "_ts_nominal_")
tot = ts.melt(id_vars=["GISJOIN"], value_vars=[f"A00AA{y}" for y in BLACK_PRE],
              var_name="v", value_name="total")
tot["year"] = tot.v.str[-4:].astype(int)
tot["total"] = pd.to_numeric(tot.total, errors="coerce")
pre = pre.merge(tot[["GISJOIN", "year", "total"]], on=["GISJOIN", "year"], how="inner")
pre["fips"] = gisjoin_to_fips(pre.GISJOIN)
pre = pre[pre.total > 0]
pre["share"] = 100 * pre.black / pre.total
prew = pre.pivot_table(index="fips", columns="year", values="share")
prew.columns = [str(c) for c in prew.columns]
print(f"pre-period counties with data: 1870 {prew['1870'].notna().sum()}, "
      f"1880 {prew['1880'].notna().sum()}, 1890 {prew['1890'].notna().sum()}")

# ---- join to the existing panel + treatment -----------------------------------------
w = pd.read_csv(ROOT / "displacement/origin_side_panel_v3.csv")
w.columns = [str(c) for c in w.columns]
w["fips"] = w.fips.astype(str).str.zfill(5)
w["sd"] = (w.sundown_v2.astype(bool) | w.n_entries.notna())
w["clean_control"] = ~w.sd
w = w.merge(prew.reset_index(), on="fips", how="left")
full = w.dropna(subset=ALLY).copy()
print(f"balanced 9-decade panel: {len(full)} counties "
      f"({int(full.sd.sum())} sundown, {int((~full.sd).sum())} not)\n")

# ---- Q1 how far back does the gap go? ----------------------------------------------
print("=" * 84)
print("Q1  MEDIAN BLACK SHARE BY DECADE — does the gap predate the sundown era?")
print("=" * 84)
print(f"  {'group':<22}" + "".join(f"{y:>8}" for y in ALLY))
for lab, m in (("sundown counties", full.sd), ("non-sundown counties", ~full.sd)):
    print(f"  {lab:<22}" + "".join(f"{full[m][y].median():>8.2f}" for y in ALLY))
print()
for y in ALLY:
    a, b = full[full.sd][y], full[~full.sd][y]
    print(f"  {y}  sundown median {a.median():6.2f}%  non-sundown {b.median():6.2f}%  "
          f"ratio {b.median()/max(a.median(),0.001):6.1f}x   MW p={mannwhitneyu(a,b).pvalue:.2g}")

# ---- Q2 when do the collapses happen? ----------------------------------------------
print("\n" + "=" * 84)
print("Q2  WHEN DO EXPULSION EVENTS OCCUR?  (>=2% base, >=50% one-decade drop)")
print("=" * 84)
long = full.melt(id_vars=["fips", "sd"], value_vars=ALLY, var_name="year", value_name="share")
long["year"] = long.year.astype(int)
long = long.sort_values(["fips", "year"])
long["prev"] = long.groupby("fips").share.shift(1)
long["drop"] = 1 - long.share / long.prev
ev = long[(long.prev >= 2) & (long["drop"] >= 0.5)]
print(f"  {'decade':<14}{'sundown events':>16}{'non-sundown':>14}{'sd share':>11}")
for y in sorted(ev.year.unique()):
    e = ev[ev.year == y]
    n1, n0 = int((e.sd).sum()), int((~e.sd).sum())
    print(f"  {y-10}->{y:<8}{n1:>16}{n0:>14}{(100*n1/max(n1+n0,1)):>10.0f}%")
print(f"  {'TOTAL':<14}{int(ev.sd.sum()):>16}{int((~ev.sd).sum()):>14}"
      f"{100*ev.sd.mean():>10.0f}%")

# ---- Q3 does the association hold in the pre-1900 window? ---------------------------
print("\n" + "=" * 84)
print("Q3  ASSOCIATION BY WINDOW")
print("=" * 84)
for lab, yrs in (("pre-1900  (1880, 1890, 1900 transitions)", [1880, 1890, 1900]),
                 ("post-1900 (1910-1950 transitions)", [1910, 1920, 1930, 1940, 1950]),
                 ("full span (1880-1950)", sorted(ev.year.unique()))):
    e = ev[ev.year.isin(yrs)]
    hit = set(e.fips)
    elig = full[full[[str(y) for y in yrs] + [str(y-10) for y in yrs if str(y-10) in ALLY]]
                .max(axis=1) >= 2].copy()
    elig["event"] = elig.fips.isin(hit)
    t, c = elig[elig.sd], elig[~elig.sd]
    if len(t) < 15:
        print(f"  {lab:<42} too few"); continue
    tab = [[int(t.event.sum()), int((~t.event).sum())],
           [int(c.event.sum()), int((~c.event).sum())]]
    orr, p = fisher_exact(tab)
    print(f"  {lab:<42} sundown {100*t.event.mean():5.1f}% (n={len(t):>4})  "
          f"control {100*c.event.mean():5.1f}% (n={len(c):>4})  OR={orr:5.2f}  p={p:.3g}")

full.to_csv(ROOT / "displacement/panel_1870_1950.csv", index=False)
print(f"\nwrote displacement/panel_1870_1950.csv")
