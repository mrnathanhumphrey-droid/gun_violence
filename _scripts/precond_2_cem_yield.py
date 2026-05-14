"""Pre-cond (2) CEM yield test.

Apply §3 working-class American matching profile (5 of 6 dims; pop-stability
needs older vintage, deferred). Compute pre-CEM and post-CEM cell sizes
under locked β@0.5 cell typology.

§3 thresholds:
  (1) HH income: median in [30th, 65th] national percentile
  (2) Education: pct_HS_terminal >= 40, pct_bachelors+ <= 30
  (3) Labor force: pct_employed_civilian_LF >= 55
  (4) HH structure: pct_family_HH >= 50  (proxy for married+single+multigen)
  (5) Age: pct_working_age_18_64 >= 55
  (6) Pop stability: SKIPPED (need older ACS vintage to compute change)

Unit qualifies if ALL 5 conditions hold.
"""
import pathlib, pandas as pd, numpy as np, zipfile

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
OUT = ROOT / "notes"

# === Load F-33 + CHR (school + health dims for cell assignment) ===
print("Loading F-33...")
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

print("Loading CHR...")
chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = pd.to_numeric(chr_h["Uninsured__% Uninsured"], errors="coerce")
chr_h["pcp_rate"] = pd.to_numeric(chr_h["Primary Care Physicians__Primary Care Physicians Rate"], errors="coerce")

print("Loading ACS (all needed tables)...")
def load(t, g):
    return pd.read_parquet(ACS / f"acs5_2023_{t}_{g}.parquet")
def n(s): return pd.to_numeric(s, errors="coerce")

b01 = {g: load("B01001", g) for g in ["tract","county"]}   # sex by age
b02 = {g: load("B02001", g) for g in ["tract","county"]}   # race
b03 = {g: load("B03003", g) for g in ["tract","county"]}   # Hispanic
b17 = {g: load("B17001", g) for g in ["tract","county"]}   # poverty
b19 = {g: load("B19013", g) for g in ["tract","county"]}   # median HH income
b25t = {g: load("B25003", g) for g in ["tract","county"]}  # tenure
b25r = {g: load("B25070", g) for g in ["tract","county"]}  # rent burden
b15 = {g: load("B15003", g) for g in ["tract","county"]}   # education
b23 = {g: load("B23025", g) for g in ["tract","county"]}   # employment
b11 = {g: load("B11001", g) for g in ["tract","county"]}   # household type

def build(geo):
    keys = ["state","county","tract"] if geo == "tract" else ["state","county"]

    # --- v7 base fields ---
    pop = b01[geo][keys + ["B01001_001E"]].copy()
    pop["pop_total"] = n(pop["B01001_001E"])

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

    # --- CEM matching fields (§3) ---
    # Income (B19013): median HH income
    inc = b19[geo][keys + ["B19013_001E"]].copy()
    inc["median_hh_income"] = n(inc["B19013_001E"])

    # Education (B15003): need denom + HS-terminal + bachelors-plus
    ed_keys = keys + [f"B15003_{i:03d}E" for i in [1,17,18,22,23,24,25,26,27,28]]
    ed = b15[geo][[c for c in ed_keys if c in b15[geo].columns]].copy()
    for c in ed.columns[len(keys):]: ed[c] = n(ed[c])
    ed["pct_hs_terminal"] = (ed.get("B15003_017E",0) + ed.get("B15003_018E",0)) / ed["B15003_001E"] * 100
    ed["pct_bachelors_plus"] = (ed.get("B15003_025E",0) + ed.get("B15003_026E",0) + ed.get("B15003_027E",0) + ed.get("B15003_028E",0)) / ed["B15003_001E"] * 100
    ed = ed[keys + ["pct_hs_terminal","pct_bachelors_plus"]]

    # Labor force (B23025): pct civilian employed of 16+ pop
    lf_keys = keys + ["B23025_001E","B23025_004E"]
    lf = b23[geo][[c for c in lf_keys if c in b23[geo].columns]].copy()
    for c in lf.columns[len(keys):]: lf[c] = n(lf[c])
    lf["pct_employed_civilian_LF"] = lf["B23025_004E"] / lf["B23025_001E"] * 100
    lf = lf[keys + ["pct_employed_civilian_LF"]]

    # Age (B01001): pct working-age 18-64
    # under 18: M cols 003-006, F cols 027-030
    # 65+: M cols 020-025, F cols 044-049
    under18_M = [f"B01001_{i:03d}E" for i in [3,4,5,6]]
    under18_F = [f"B01001_{i:03d}E" for i in [27,28,29,30]]
    over65_M = [f"B01001_{i:03d}E" for i in [20,21,22,23,24,25]]
    over65_F = [f"B01001_{i:03d}E" for i in [44,45,46,47,48,49]]
    age_cols = keys + ["B01001_001E"] + under18_M + under18_F + over65_M + over65_F
    age = b01[geo][[c for c in age_cols if c in b01[geo].columns]].copy()
    for c in age.columns[len(keys):]: age[c] = n(age[c])
    age["under18"] = age[under18_M].sum(axis=1) + age[under18_F].sum(axis=1)
    age["over65"] = age[over65_M].sum(axis=1) + age[over65_F].sum(axis=1)
    age["pct_working_age"] = (age["B01001_001E"] - age["under18"] - age["over65"]) / age["B01001_001E"] * 100
    age = age[keys + ["pct_working_age"]]

    # Household structure (B11001): pct family households
    hh_keys = keys + ["B11001_001E","B11001_002E"]
    hh = b11[geo][[c for c in hh_keys if c in b11[geo].columns]].copy()
    for c in hh.columns[len(keys):]: hh[c] = n(hh[c])
    hh["pct_family_HH"] = hh["B11001_002E"] / hh["B11001_001E"] * 100
    hh = hh[keys + ["pct_family_HH"]]

    # --- Merge ---
    df = (pop[keys + ["pop_total"]]
          .merge(race, on=keys).merge(hisp, on=keys).merge(pov, on=keys)
          .merge(ten, on=keys).merge(rent, on=keys)
          .merge(inc[keys + ["median_hh_income"]], on=keys)
          .merge(ed, on=keys).merge(lf, on=keys).merge(age, on=keys).merge(hh, on=keys))

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

# Join food access, school, health (for cell assignment composite)
print("Loading USDA...")
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

# Urbanicity
ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])
counties = counties.merge(ct, on=["state","county"], how="left")
counties["n_tracts"] = counties["n_tracts"].fillna(0)
counties["urban_class"] = pd.cut(counties["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

# β@0.5 standardization (within-urbanicity)
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

tracts = standardize_beta(tracts)
counties = standardize_beta(counties)

# === CEM working-class profile filter ===
# Compute national income percentiles from population-weighted distribution
print("Computing CEM filter (§3 working-class profile)...")
all_units = pd.concat([
    tracts[["pop_total","median_hh_income"]].assign(geo="tract"),
    counties[["pop_total","median_hh_income"]].assign(geo="county"),
], ignore_index=True)
# pop-weighted income percentiles
all_units = all_units.dropna(subset=["median_hh_income","pop_total"])
all_units = all_units[all_units["pop_total"] > 0]
all_units = all_units.sort_values("median_hh_income")
all_units["cum_pop"] = all_units["pop_total"].cumsum()
all_units["pct"] = all_units["cum_pop"] / all_units["pop_total"].sum() * 100
inc_30 = all_units[all_units["pct"] >= 30]["median_hh_income"].iloc[0]
inc_65 = all_units[all_units["pct"] >= 65]["median_hh_income"].iloc[0]
print(f"  national income 30th pctile: ${inc_30:,.0f}")
print(f"  national income 65th pctile: ${inc_65:,.0f}")

def working_class_filter(df):
    """Return boolean mask: True if unit matches §3 working-class profile."""
    return (
        df["median_hh_income"].between(inc_30, inc_65) &
        (df["pct_hs_terminal"] >= 40) &
        (df["pct_bachelors_plus"] <= 30) &
        (df["pct_employed_civilian_LF"] >= 55) &
        (df["pct_family_HH"] >= 50) &
        (df["pct_working_age"] >= 55)
    )

tracts["working_class_match"] = working_class_filter(tracts)
counties["working_class_match"] = working_class_filter(counties)

print(f"  national tract match rate: {tracts['working_class_match'].mean()*100:.1f}%")
print(f"  national county match rate: {counties['working_class_match'].mean()*100:.1f}%")

# === Cell counts pre + post-CEM under β@0.5 ===
THRESHOLD = 0.5

def elig(t, c):
    t_e = t[t["pop_total"] >= 1500].copy()
    c_e = c[c["pop_total"] >= 3000].copy()
    return t_e[t_e["urban_class"]=="urban"], t_e[t_e["urban_class"]=="suburban"], c_e

u, s, c = elig(tracts, counties)

CELLS = [
    ("UB-HI", "u", lambda d: d["pct_black"] >= 60, "HI", "500-1000"),
    ("UH-HI", "u", lambda d: d["pct_hispanic"] >= 60, "HI", "500-1000"),
    ("UW-LI", "u", lambda d: d["pct_nhw_approx"] >= 70, "LI", "1000+"),
    ("SB-MC", "s", lambda d: d["pct_black"] >= 60, "MC", "300-500"),
    ("RW-HI", "c", lambda d: d["pct_nhw_approx"] >= 80, "HI", "150-250"),
    ("RB-HI", "c", lambda d: d["pct_black"] >= 50, "HI", "60-100"),
    ("RH-HI", "c", lambda d: d["pct_hispanic"] >= 50, "HI", "40-60"),
    ("RNA-HI", "c", lambda d: d["pct_aian"] >= 40, "HI", "20-30 (proxy)"),
]

results = []
for cell_id, base_key, race_fn, tier, est in CELLS:
    base_df = {"u": u, "s": s, "c": c}[base_key]
    if tier == "HI":
        sel = race_fn(base_df) & (base_df["composite_mean"] >= THRESHOLD)
    elif tier == "LI":
        sel = race_fn(base_df) & (base_df["composite_mean"] <= -THRESHOLD/2)
    else:  # MC
        sel = race_fn(base_df) & (base_df["composite_mean"] > -THRESHOLD/2) & (base_df["composite_mean"] < THRESHOLD)
    pre = int(sel.sum())
    post = int((sel & base_df["working_class_match"]).sum())
    retention = post / pre * 100 if pre > 0 else float("nan")
    results.append({
        "cell": cell_id, "est": est, "pre_cem": pre, "post_cem": post,
        "retention_pct": round(retention, 1) if pre > 0 else None,
    })

# Write report
md = ["# Pre-cond (2) — CEM yield test (β@0.5 + §3 working-class profile)", "",
      "**Locked operationalization:** β within-urbanicity z-scores, mean composite ≥ 0.5.",
      "",
      "**§3 working-class profile (5 of 6 dims; pop-stability deferred):**",
      f"- Median HH income in [${inc_30:,.0f}, ${inc_65:,.0f}] (30th-65th national pop-weighted percentile)",
      "- pct_HS_terminal ≥ 40%",
      "- pct_bachelors_plus ≤ 30%",
      "- pct_employed_civilian_LF ≥ 55%",
      "- pct_family_HH ≥ 50% (proxy for married + single-parent + multigen)",
      "- pct_working_age (18-64) ≥ 55%",
      "",
      f"**National match rate:** tracts {tracts['working_class_match'].mean()*100:.1f}%, counties {counties['working_class_match'].mean()*100:.1f}%",
      "",
      "## Cell-level CEM yield",
      "",
      "| Cell | §2 est | Pre-CEM | Post-CEM | Retention | §3 expected 40-60% |",
      "|---|---|---|---|---|---|"]
for r in results:
    ret = f"{r['retention_pct']}%" if r['retention_pct'] is not None else "n/a"
    flag = ""
    if r['retention_pct'] is not None:
        if r['retention_pct'] < 40: flag = " ⚠ low"
        elif r['retention_pct'] > 60: flag = " ⚠ high"
        else: flag = " ✓"
    md.append(f"| {r['cell']} | {r['est']} | {r['pre_cem']:,} | {r['post_cem']:,} | {ret}{flag} |")

md += ["",
       "## Power tier reassignment (post-CEM)",
       "",
       "| Cell | Post-CEM | Tier (§7 cutoffs: T1≥120, T2 25-100, T3 <25) |",
       "|---|---|---|"]
for r in results:
    if r["post_cem"] >= 120: tier = "**Tier 1**"
    elif r["post_cem"] >= 25: tier = "Tier 2"
    elif r["post_cem"] >= 8: tier = "Tier 3"
    else: tier = "**unviable**"
    md.append(f"| {r['cell']} | {r['post_cem']:,} | {tier} |")

md.append("")
md.append("## Caveats")
md.append("")
md.append("- Population-stability dim (§3.6) deferred — would require older ACS vintage to compute % change.")
md.append("- HH structure dim uses B11001 pct_family_HH as proxy for married + single-parent + multigen ≥ 50%.")
md.append("- pct_nhw_approx is conservative under-estimate (subtracts all Hispanic from white-alone, not B03002 cross-tab).")
md.append("- Retention >60% suggests profile is too permissive for that cell (mostly already working-class). Retention <40% suggests the cell composition diverges substantially from working-class profile.")

(OUT / "cell_availability_v8_cem_yield.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nwrote {OUT}/cell_availability_v8_cem_yield.md")
for r in results:
    ret = f"{r['retention_pct']}%" if r['retention_pct'] is not None else "n/a"
    print(f"  {r['cell']:<8} pre={r['pre_cem']:>6,}  post={r['post_cem']:>6,}  retention={ret}")
