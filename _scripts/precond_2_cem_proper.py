"""Pre-cond (2) CEM proper — bin each §3 dim into 3 bins, retain units
in bin tuples shared across all cells.

Bin boundaries are anchored to §3's thresholds (midpoint of each 3-bin range
is the §3-stated value).
"""
import pathlib, pandas as pd, numpy as np, zipfile
from itertools import product

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
OUT = ROOT / "notes"

# === Load everything (same as precond_2_cem_yield.py) ===
print("Loading F-33 + CHR + ACS + USDA...")
with zipfile.ZipFile(F33) as zf, zf.open("sdf22_1a.txt") as f:
    f33 = pd.read_csv(f, sep="\t", dtype=str, low_memory=False,
                      usecols=["LEAID","CONUM","V33","TOTALEXP","SCHLEV"])
f33["enrollment"] = pd.to_numeric(f33["V33"], errors="coerce")
f33["total_exp"] = pd.to_numeric(f33["TOTALEXP"], errors="coerce")
f33 = f33[f33["SCHLEV"].isin(["01","02","03"]) & (f33["enrollment"] > 0) & (f33["total_exp"] > 0)]
f33["log_ppe"] = np.log(f33["total_exp"] * 1000 / f33["enrollment"])
county_ppe = f33.groupby("CONUM").apply(
    lambda g: (g["log_ppe"] * g["enrollment"]).sum() / g["enrollment"].sum()
).reset_index(name="county_log_ppe")
county_ppe["state"], county_ppe["county"] = county_ppe["CONUM"].str[:2], county_ppe["CONUM"].str[2:]

chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = pd.to_numeric(chr_h["Uninsured__% Uninsured"], errors="coerce")
chr_h["pcp_rate"] = pd.to_numeric(chr_h["Primary Care Physicians__Primary Care Physicians Rate"], errors="coerce")

def load(t, g): return pd.read_parquet(ACS / f"acs5_2023_{t}_{g}.parquet")
def n(s): return pd.to_numeric(s, errors="coerce")

b01 = {g: load("B01001", g) for g in ["tract","county"]}
b02 = {g: load("B02001", g) for g in ["tract","county"]}
b03 = {g: load("B03003", g) for g in ["tract","county"]}
b17 = {g: load("B17001", g) for g in ["tract","county"]}
b19 = {g: load("B19013", g) for g in ["tract","county"]}
b25t = {g: load("B25003", g) for g in ["tract","county"]}
b25r = {g: load("B25070", g) for g in ["tract","county"]}
b15 = {g: load("B15003", g) for g in ["tract","county"]}
b23 = {g: load("B23025", g) for g in ["tract","county"]}
b11 = {g: load("B11001", g) for g in ["tract","county"]}

def build(geo):
    keys = ["state","county","tract"] if geo == "tract" else ["state","county"]
    pop = b01[geo][keys + ["B01001_001E"]].copy(); pop["pop_total"] = n(pop["B01001_001E"])
    race = b02[geo][keys + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
    for c in race.columns[len(keys):]: race[c] = n(race[c])
    race = race.rename(columns={"B02001_001E":"race_total","B02001_002E":"white_alone","B02001_003E":"black_alone","B02001_004E":"aian_alone"})
    hisp = b03[geo][keys + ["B03003_001E","B03003_003E"]].copy()
    for c in hisp.columns[len(keys):]: hisp[c] = n(hisp[c])
    hisp = hisp.rename(columns={"B03003_001E":"hisp_total","B03003_003E":"hispanic"})
    pov = b17[geo][keys + ["B17001_001E","B17001_002E"]].copy()
    for c in pov.columns[len(keys):]: pov[c] = n(pov[c])
    pov = pov.rename(columns={"B17001_001E":"pov_denom","B17001_002E":"below_poverty"})
    ten = b25t[geo][keys + ["B25003_001E","B25003_002E"]].copy()
    for c in ten.columns[len(keys):]: ten[c] = n(ten[c])
    ten = ten.rename(columns={"B25003_001E":"ten_total","B25003_002E":"owner_occ"})
    rent = b25r[geo][keys + ["B25070_001E","B25070_010E"]].copy()
    for c in rent.columns[len(keys):]: rent[c] = n(rent[c])
    rent = rent.rename(columns={"B25070_001E":"rent_denom","B25070_010E":"rent_burden_50plus"})
    inc = b19[geo][keys + ["B19013_001E"]].copy(); inc["median_hh_income"] = n(inc["B19013_001E"])
    ed_keys = keys + [f"B15003_{i:03d}E" for i in [1,17,18,25,26,27,28]]
    ed = b15[geo][[c for c in ed_keys if c in b15[geo].columns]].copy()
    for c in ed.columns[len(keys):]: ed[c] = n(ed[c])
    ed["pct_hs_terminal"] = (ed.get("B15003_017E",0)+ed.get("B15003_018E",0)) / ed["B15003_001E"] * 100
    ed["pct_bachelors_plus"] = (ed.get("B15003_025E",0)+ed.get("B15003_026E",0)+ed.get("B15003_027E",0)+ed.get("B15003_028E",0)) / ed["B15003_001E"] * 100
    ed = ed[keys + ["pct_hs_terminal","pct_bachelors_plus"]]
    lf_keys = keys + ["B23025_001E","B23025_004E"]
    lf = b23[geo][[c for c in lf_keys if c in b23[geo].columns]].copy()
    for c in lf.columns[len(keys):]: lf[c] = n(lf[c])
    lf["pct_employed_civilian_LF"] = lf["B23025_004E"] / lf["B23025_001E"] * 100
    lf = lf[keys + ["pct_employed_civilian_LF"]]
    under18_M = [f"B01001_{i:03d}E" for i in [3,4,5,6]]; under18_F = [f"B01001_{i:03d}E" for i in [27,28,29,30]]
    over65_M = [f"B01001_{i:03d}E" for i in [20,21,22,23,24,25]]; over65_F = [f"B01001_{i:03d}E" for i in [44,45,46,47,48,49]]
    age_cols = keys + ["B01001_001E"] + under18_M + under18_F + over65_M + over65_F
    age = b01[geo][[c for c in age_cols if c in b01[geo].columns]].copy()
    for c in age.columns[len(keys):]: age[c] = n(age[c])
    age["under18"] = age[under18_M].sum(axis=1) + age[under18_F].sum(axis=1)
    age["over65"] = age[over65_M].sum(axis=1) + age[over65_F].sum(axis=1)
    age["pct_working_age"] = (age["B01001_001E"]-age["under18"]-age["over65"]) / age["B01001_001E"] * 100
    age = age[keys + ["pct_working_age"]]
    hh = b11[geo][keys + ["B11001_001E","B11001_002E"]].copy()
    for c in hh.columns[len(keys):]: hh[c] = n(hh[c])
    hh["pct_family_HH"] = hh["B11001_002E"] / hh["B11001_001E"] * 100
    hh = hh[keys + ["pct_family_HH"]]
    df = (pop[keys+["pop_total"]].merge(race,on=keys).merge(hisp,on=keys).merge(pov,on=keys)
          .merge(ten,on=keys).merge(rent,on=keys).merge(inc[keys+["median_hh_income"]],on=keys)
          .merge(ed,on=keys).merge(lf,on=keys).merge(age,on=keys).merge(hh,on=keys))
    df["pct_white"] = df["white_alone"]/df["race_total"]*100
    df["pct_black"] = df["black_alone"]/df["race_total"]*100
    df["pct_aian"] = df["aian_alone"]/df["race_total"]*100
    df["pct_hispanic"] = df["hispanic"]/df["hisp_total"]*100
    df["pct_nhw_approx"] = df["pct_white"] - df["pct_hispanic"]
    df["poverty_rate"] = df["below_poverty"]/df["pov_denom"]*100
    df["renter_rate"] = (1 - df["owner_occ"]/df["ten_total"])*100
    df["rent_burden_pct"] = df["rent_burden_50plus"]/df["rent_denom"]*100
    return df

tracts, counties = build("tract"), build("county")

fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state"], fa["county"], fa["tract"] = fa["CensusTract"].str[:2], fa["CensusTract"].str[2:5], fa["CensusTract"].str[5:]
fa["food_inequity_score"] = pd.concat([
    pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0),
    pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
], axis=1).max(axis=1)
fa["pop_2010"] = pd.to_numeric(fa["Pop2010"], errors="coerce").fillna(0)
tracts = tracts.merge(fa[["state","county","tract","food_inequity_score"]], on=["state","county","tract"], how="left")
tracts["food_inequity_score"] = tracts["food_inequity_score"].fillna(tracts["food_inequity_score"].median())
fa_county = fa.groupby(["state","county"]).apply(
    lambda g: (g["food_inequity_score"]*g["pop_2010"]).sum() / max(g["pop_2010"].sum(),1)
).reset_index(name="food_inequity_score")
counties = counties.merge(fa_county, on=["state","county"], how="left")
counties["food_inequity_score"] = counties["food_inequity_score"].fillna(counties["food_inequity_score"].median())

tracts = tracts.merge(county_ppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
counties = counties.merge(county_ppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
for df in [tracts, counties]:
    df["county_log_ppe"] = df["county_log_ppe"].fillna(df["county_log_ppe"].median())

tracts = tracts.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
counties = counties.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
for df in [tracts, counties]:
    df["pct_uninsured"] = df["pct_uninsured"].fillna(df["pct_uninsured"].median())
    df["pcp_rate"] = df["pcp_rate"].fillna(df["pcp_rate"].median())

ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])
counties = counties.merge(ct, on=["state","county"], how="left")
counties["n_tracts"] = counties["n_tracts"].fillna(0)
counties["urban_class"] = pd.cut(counties["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

def standardize_beta(df):
    out = df.copy()
    out["raw_housing"] = (out["rent_burden_pct"] + out["renter_rate"]) / 2
    out["raw_health"] = out["pct_uninsured"] - out["pcp_rate"] / 100
    cols = {"poverty_z":"poverty_rate","food_z":"food_inequity_score",
            "housing_z":"raw_housing","school_z":"county_log_ppe","health_z":"raw_health"}
    for z_name, src in cols.items():
        v = out[src]
        out[z_name] = np.nan
        for s in out["urban_class"].dropna().unique():
            m = out["urban_class"] == s
            v_s = v[m]
            if v_s.notna().sum() < 2: continue
            out.loc[m, z_name] = (v_s - v_s.mean()) / v_s.std()
        if z_name == "school_z":
            out[z_name] = -out[z_name]
    out["composite_mean"] = out[list(cols.keys())].mean(axis=1)
    return out

tracts = standardize_beta(tracts); counties = standardize_beta(counties)

# === Cell assignment under β@0.5 ===
THRESHOLD = 0.5
def elig(t, c):
    t_e = t[t["pop_total"] >= 1500].copy()
    c_e = c[c["pop_total"] >= 3000].copy()
    return t_e[t_e["urban_class"]=="urban"], t_e[t_e["urban_class"]=="suburban"], c_e
u, s, c = elig(tracts, counties)

CELLS = [
    ("UB-HI", "u", lambda d: d["pct_black"] >= 60, "HI"),
    ("UH-HI", "u", lambda d: d["pct_hispanic"] >= 60, "HI"),
    ("UW-LI", "u", lambda d: d["pct_nhw_approx"] >= 70, "LI"),
    ("SB-MC", "s", lambda d: d["pct_black"] >= 60, "MC"),
    ("RW-HI", "c", lambda d: d["pct_nhw_approx"] >= 80, "HI"),
    ("RB-HI", "c", lambda d: d["pct_black"] >= 50, "HI"),
    ("RH-HI", "c", lambda d: d["pct_hispanic"] >= 50, "HI"),
    ("RNA-HI", "c", lambda d: d["pct_aian"] >= 40, "HI"),
]

print("Assigning cells...")
cell_dfs = {}
for cell_id, base_key, race_fn, tier in CELLS:
    base_df = {"u": u, "s": s, "c": c}[base_key]
    if tier == "HI":
        sel = race_fn(base_df) & (base_df["composite_mean"] >= THRESHOLD)
    elif tier == "LI":
        sel = race_fn(base_df) & (base_df["composite_mean"] <= -THRESHOLD/2)
    else:
        sel = race_fn(base_df) & (base_df["composite_mean"] > -THRESHOLD/2) & (base_df["composite_mean"] < THRESHOLD)
    cell_dfs[cell_id] = base_df[sel].copy()
    cell_dfs[cell_id]["cell"] = cell_id

# === CEM proper: bin each dim, find shared bin tuples ===
print("CEM binning...")

# Build pop-weighted national income percentile (30, 65)
all_units = pd.concat([
    tracts[["pop_total","median_hh_income"]],
    counties[["pop_total","median_hh_income"]],
], ignore_index=True).dropna(subset=["median_hh_income","pop_total"])
all_units = all_units[all_units["pop_total"] > 0].sort_values("median_hh_income")
all_units["cum_pop"] = all_units["pop_total"].cumsum()
all_units["pct"] = all_units["cum_pop"] / all_units["pop_total"].sum() * 100
inc_30 = float(all_units[all_units["pct"] >= 30]["median_hh_income"].iloc[0])
inc_65 = float(all_units[all_units["pct"] >= 65]["median_hh_income"].iloc[0])

# 3-bin boundaries anchored to §3 thresholds (midpoint of middle bin is §3 value)
BINS = {
    "median_hh_income":          [-np.inf, inc_30, inc_65, np.inf],         # low / mid (30-65) / high
    "pct_hs_terminal":           [-np.inf, 30, 50, np.inf],                  # low / mid (30-50, §3=40) / high
    "pct_bachelors_plus":        [-np.inf, 20, 40, np.inf],                  # low (<20) / mid (20-40, §3=30) / high
    "pct_employed_civilian_LF":  [-np.inf, 45, 65, np.inf],                  # low / mid (45-65, §3=55) / high
    "pct_family_HH":             [-np.inf, 40, 60, np.inf],                  # low / mid (40-60, §3=50) / high
    "pct_working_age":           [-np.inf, 50, 60, np.inf],                  # low / mid (50-60, §3=55) / high
}
LABELS = ["lo","mid","hi"]

def bin_cell(df):
    out = df.copy()
    for col, edges in BINS.items():
        out[f"bin_{col}"] = pd.cut(out[col], bins=edges, labels=LABELS).astype(str)
    out["bin_tuple"] = out[[f"bin_{c}" for c in BINS]].agg(tuple, axis=1)
    return out

for cid in cell_dfs:
    cell_dfs[cid] = bin_cell(cell_dfs[cid])

# Find shared bin tuples (present in ALL cells)
tuple_sets = {cid: set(df["bin_tuple"].dropna()) for cid, df in cell_dfs.items()}
shared = set.intersection(*tuple_sets.values())
print(f"  shared bin tuples (across all 8 cells): {len(shared)}")

# Also compute pairwise shared support for diagnostic
pair_shared = {}
cell_ids = list(cell_dfs.keys())
for i, a in enumerate(cell_ids):
    for b in cell_ids[i+1:]:
        pair_shared[(a,b)] = len(tuple_sets[a] & tuple_sets[b])

# Pre + post-CEM counts
results = []
for cid, df in cell_dfs.items():
    pre = len(df)
    post_all8 = int(df["bin_tuple"].isin(shared).sum())
    retention = post_all8 / pre * 100 if pre > 0 else float("nan")
    results.append({"cell": cid, "pre": pre, "post_all8": post_all8, "retention_all8": round(retention,1) if pre>0 else None})

# Write report
md = ["# Pre-cond (2) v2 — CEM proper (binned + shared support across all 8 cells)", "",
      "**Method:** Each §3 dim discretized into 3 bins (lo / mid / hi), bin boundaries anchored to §3 thresholds.",
      "Retain units whose 6-dim bin tuple appears in ALL 8 cells (proper CEM shared support).",
      "",
      f"**Income bin edges (pop-weighted national):** lo < ${inc_30:,.0f} ≤ mid ≤ ${inc_65:,.0f} < hi",
      "",
      "**Bin spec (lo/mid/hi):**",
      f"- median_hh_income: < ${inc_30:,.0f} / ${inc_30:,.0f}-${inc_65:,.0f} (§3 target) / > ${inc_65:,.0f}",
      "- pct_hs_terminal: <30 / 30-50 (§3 ≥40) / >50",
      "- pct_bachelors_plus: <20 / 20-40 (§3 ≤30) / >40",
      "- pct_employed_civilian_LF: <45 / 45-65 (§3 ≥55) / >65",
      "- pct_family_HH: <40 / 40-60 (§3 ≥50) / >60",
      "- pct_working_age: <50 / 50-60 (§3 ≥55) / >60",
      "",
      f"## Shared bin tuples across all 8 cells: **{len(shared)}** (out of 729 possible)",
      "",
      "## Per-cell CEM yield",
      "",
      "| Cell | Pre-CEM | Post-CEM (all-8 shared) | Retention | §3 expected 40-60% |",
      "|---|---|---|---|---|"]
for r in results:
    ret = f"{r['retention_all8']}%" if r['retention_all8'] is not None else "n/a"
    flag = ""
    if r['retention_all8'] is not None:
        if r['retention_all8'] < 40: flag = " ⚠ low"
        elif r['retention_all8'] > 60: flag = " ⚠ high"
        else: flag = " ✓"
    md.append(f"| {r['cell']} | {r['pre']:,} | {r['post_all8']:,} | {ret}{flag} |")

# Pairwise shared support for key comparisons
md += ["", "## Pairwise shared bin tuples (key comparisons)", "",
       "| Cell A | Cell B | Shared tuples |", "|---|---|---|"]
key_pairs = [("UB-HI","SB-MC"),("UB-HI","UW-LI"),("SB-MC","RW-HI"),
             ("UB-HI","RB-HI"),("UW-LI","RW-HI"),("RB-HI","RW-HI"),("RH-HI","RB-HI")]
for a,b in key_pairs:
    md.append(f"| {a} | {b} | {pair_shared.get((a,b), pair_shared.get((b,a), '?'))} |")

# Post-CEM power tier
md += ["", "## Power tier reassignment (post-CEM, all-8 shared)", "",
       "| Cell | Post-CEM | Tier (§7: T1≥120, T2 25-100, T3 8-24, <8=unviable) |",
       "|---|---|---|"]
for r in results:
    pc = r["post_all8"]
    if pc >= 120: tier = "**Tier 1**"
    elif pc >= 25: tier = "Tier 2"
    elif pc >= 8: tier = "Tier 3"
    else: tier = "**unviable**"
    md.append(f"| {r['cell']} | {pc:,} | {tier} |")

(OUT / "cell_availability_v8b_cem_proper.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nwrote {OUT}/cell_availability_v8b_cem_proper.md")
print(f"shared bin tuples (all 8): {len(shared)}")
for r in results:
    ret = f"{r['retention_all8']}%" if r['retention_all8'] is not None else "n/a"
    print(f"  {r['cell']:<8} pre={r['pre']:>6,}  post={r['post_all8']:>6,}  retention={ret}")
