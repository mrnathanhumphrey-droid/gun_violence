"""Pre-condition (1) v3: full 4-dim inequity composite per §2.

Dims:
1. Poverty rate (ACS B17001)
2. Food access (USDA lapop share)
3. Housing instability (z(rent burden 50%+) + z(renter rate))/2
4. School resources (NCES F-33: -z(county per-pupil expenditure))

Compositing rule per §2: per-dim z ≥ +1.0 in at least 3 of 4 dimensions
(spec-faithful "at least 3 of 4 dimensions").
"""
import pathlib, pandas as pd, numpy as np, zipfile, io

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
OUT = ROOT / "notes"

# === Load NCES F-33 ===
print("Loading NCES F-33 SY 2021-22...")
with zipfile.ZipFile(F33) as zf:
    with zf.open("sdf22_1a.txt") as f:
        f33 = pd.read_csv(f, sep="\t", dtype=str, low_memory=False,
                          usecols=["LEAID","FIPST","CONUM","V33","TOTALEXP","STNAME","NAME","SCHLEV"])

print(f"  rows: {len(f33):,}")
f33["enrollment"] = pd.to_numeric(f33["V33"], errors="coerce")
f33["total_exp"] = pd.to_numeric(f33["TOTALEXP"], errors="coerce")
# Filter to operating elementary/secondary systems (drop service agencies + nonoperating)
f33 = f33[f33["SCHLEV"].isin(["01","02","03"])]
print(f"  operating school systems: {len(f33):,}")
# Filter to valid enrollment + spending
f33 = f33[(f33["enrollment"] > 0) & (f33["total_exp"] > 0)]
print(f"  with valid enrollment + spending: {len(f33):,}")
f33["ppe"] = f33["total_exp"] * 1000 / f33["enrollment"]  # TOTALEXP is in thousands of $
print(f"  district PPE: median {f33['ppe'].median():.0f}, IQR [{f33['ppe'].quantile(0.25):.0f}, {f33['ppe'].quantile(0.75):.0f}]")

# === Aggregate F-33 to county via CONUM (5-digit state+county FIPS) ===
# enrollment-weighted mean PPE per county
def wm(df, col, w):
    return (df[col] * df[w]).sum() / df[w].sum() if df[w].sum() > 0 else np.nan

county_ppe = f33.groupby("CONUM").apply(lambda g: wm(g, "ppe", "enrollment")).reset_index(name="county_ppe")
county_ppe["state"] = county_ppe["CONUM"].str[:2]
county_ppe["county"] = county_ppe["CONUM"].str[2:]
print(f"  counties with PPE: {len(county_ppe):,}")

# === Load ACS (subset same as v2) ===
print("Loading ACS...")
def load(tbl, geo):
    return pd.read_parquet(ACS / f"acs5_2023_{tbl}_{geo}.parquet")
b01 = {g: load("B01001", g) for g in ["tract", "county"]}
b02 = {g: load("B02001", g) for g in ["tract", "county"]}
b03 = {g: load("B03003", g) for g in ["tract", "county"]}
b17 = {g: load("B17001", g) for g in ["tract", "county"]}
b25t = {g: load("B25003", g) for g in ["tract", "county"]}
b25r = {g: load("B25070", g) for g in ["tract", "county"]}

def to_num(s): return pd.to_numeric(s, errors="coerce")

def build(geo):
    keys = ["state","county","tract"] if geo == "tract" else ["state","county"]
    pop = b01[geo][keys + ["B01001_001E"]].copy()
    pop["pop_total"] = to_num(pop["B01001_001E"])
    race = b02[geo][keys + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
    for c in race.columns[len(keys):]: race[c] = to_num(race[c])
    race = race.rename(columns={"B02001_001E":"race_total","B02001_002E":"white_alone","B02001_003E":"black_alone","B02001_004E":"aian_alone"})
    hisp = b03[geo][keys + ["B03003_001E","B03003_003E"]].copy()
    for c in hisp.columns[len(keys):]: hisp[c] = to_num(hisp[c])
    hisp = hisp.rename(columns={"B03003_001E":"hisp_total","B03003_003E":"hispanic"})
    pov = b17[geo][keys + ["B17001_001E","B17001_002E"]].copy()
    for c in pov.columns[len(keys):]: pov[c] = to_num(pov[c])
    pov = pov.rename(columns={"B17001_001E":"pov_denom","B17001_002E":"below_poverty"})
    ten = b25t[geo][keys + ["B25003_001E","B25003_002E"]].copy()
    for c in ten.columns[len(keys):]: ten[c] = to_num(ten[c])
    ten = ten.rename(columns={"B25003_001E":"ten_total","B25003_002E":"owner_occ"})
    rent = b25r[geo][keys + ["B25070_001E","B25070_010E"]].copy()
    for c in rent.columns[len(keys):]: rent[c] = to_num(rent[c])
    rent = rent.rename(columns={"B25070_001E":"rent_denom","B25070_010E":"rent_burden_50plus"})
    df = pop[keys + ["pop_total"]].merge(race, on=keys).merge(hisp, on=keys).merge(pov, on=keys).merge(ten, on=keys).merge(rent, on=keys)
    df["pct_white"] = df["white_alone"]/df["race_total"]*100
    df["pct_black"] = df["black_alone"]/df["race_total"]*100
    df["pct_aian"] = df["aian_alone"]/df["race_total"]*100
    df["pct_hispanic"] = df["hispanic"]/df["hisp_total"]*100
    df["pct_nhw_approx"] = df["pct_white"] - df["pct_hispanic"]
    df["poverty_rate"] = df["below_poverty"]/df["pov_denom"]*100
    df["renter_rate"] = (1 - df["owner_occ"]/df["ten_total"])*100
    df["rent_burden_pct"] = df["rent_burden_50plus"]/df["rent_denom"]*100
    return df

tracts = build("tract")
counties = build("county")

# === USDA Food Access ===
print("Loading USDA Food Access...")
fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state"] = fa["CensusTract"].str[:2]
fa["county"] = fa["CensusTract"].str[2:5]
fa["tract"] = fa["CensusTract"].str[5:]
fa["food_inequity_score"] = pd.concat([
    pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0),
    pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
], axis=1).max(axis=1)
fa["pop_2010"] = pd.to_numeric(fa["Pop2010"], errors="coerce").fillna(0)

# Tract join
tracts = tracts.merge(fa[["state","county","tract","food_inequity_score"]], on=["state","county","tract"], how="left")
tracts["food_inequity_score"] = tracts["food_inequity_score"].fillna(tracts["food_inequity_score"].median())

# County aggregation
fa_county = fa.groupby(["state","county"]).apply(
    lambda g: (g["food_inequity_score"]*g["pop_2010"]).sum() / max(g["pop_2010"].sum(),1)
).reset_index(name="food_inequity_score")
counties = counties.merge(fa_county, on=["state","county"], how="left")
counties["food_inequity_score"] = counties["food_inequity_score"].fillna(counties["food_inequity_score"].median())

# === Join F-33 county PPE ===
counties = counties.merge(county_ppe[["state","county","county_ppe"]], on=["state","county"], how="left")
tracts = tracts.merge(county_ppe[["state","county","county_ppe"]], on=["state","county"], how="left")
counties["county_ppe"] = counties["county_ppe"].fillna(counties["county_ppe"].median())
tracts["county_ppe"] = tracts["county_ppe"].fillna(tracts["county_ppe"].median())
print(f"  tract-level PPE join: {tracts['county_ppe'].notna().sum():,}/{len(tracts):,}")

# === Compute z-scores per dim ===
def add_4dim(df):
    df["z_poverty"] = (df["poverty_rate"] - df["poverty_rate"].mean()) / df["poverty_rate"].std()
    df["z_food"]    = (df["food_inequity_score"] - df["food_inequity_score"].mean()) / df["food_inequity_score"].std()
    df["z_rent_burden"] = (df["rent_burden_pct"] - df["rent_burden_pct"].mean()) / df["rent_burden_pct"].std()
    df["z_renter"]      = (df["renter_rate"] - df["renter_rate"].mean()) / df["renter_rate"].std()
    df["z_housing"] = (df["z_rent_burden"] + df["z_renter"]) / 2
    # School: low PPE = high inequity → negate
    df["z_ppe"] = (df["county_ppe"] - df["county_ppe"].mean()) / df["county_ppe"].std()
    df["z_school"] = -df["z_ppe"]
    # n dims passing (high)
    df["n_dims_high"] = (
        (df["z_poverty"] >= 1.0).astype(int)
        + (df["z_food"] >= 1.0).astype(int)
        + (df["z_housing"] >= 1.0).astype(int)
        + (df["z_school"] >= 1.0).astype(int)
    )
    df["n_dims_low"] = (
        (df["z_poverty"] <= -0.5).astype(int)
        + (df["z_food"] <= -0.5).astype(int)
        + (df["z_housing"] <= -0.5).astype(int)
        + (df["z_school"] <= -0.5).astype(int)
    )
    df["composite_mean"] = (df["z_poverty"] + df["z_food"] + df["z_housing"] + df["z_school"]) / 4
    return df

tracts = add_4dim(tracts)
counties = add_4dim(counties)

# Urban/rural proxy
ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

t_elig = tracts[tracts["pop_total"] >= 1500].copy()
c_elig = counties[counties["pop_total"] >= 3000].copy()
urban_t = t_elig[t_elig["urban_class"] == "urban"]
suburban_t = t_elig[t_elig["urban_class"] == "suburban"]

# === Rules ===
RULES = {
    "spec_3_of_4_dims_high": lambda d: d["n_dims_high"] >= 3,
    "lenient_2_of_4_dims_high": lambda d: d["n_dims_high"] >= 2,
    "mean_z_ge_1": lambda d: d["composite_mean"] >= 1.0,
}
LOW_RULES_FN = {
    "spec_3_of_4_dims_high": lambda d: d["n_dims_low"] >= 3,
    "lenient_2_of_4_dims_high": lambda d: d["n_dims_low"] >= 2,
    "mean_z_ge_1": lambda d: d["composite_mean"] <= -0.5,
}

CELLS = [
    ("UB-HI", urban_t, lambda d: d["pct_black"] >= 60, "HI", "500-1000"),
    ("UH-HI", urban_t, lambda d: d["pct_hispanic"] >= 60, "HI", "500-1000"),
    ("UW-LI", urban_t, lambda d: d["pct_nhw_approx"] >= 70, "LI", "1000+"),
    ("SB-MC", suburban_t, lambda d: d["pct_black"] >= 60, "MC", "300-500"),
    ("RW-HI", c_elig, lambda d: d["pct_nhw_approx"] >= 80, "HI", "150-250"),
    ("RB-HI", c_elig, lambda d: d["pct_black"] >= 50, "HI", "60-100"),
    ("RH-HI", c_elig, lambda d: d["pct_hispanic"] >= 50, "HI", "40-60"),
    ("RNA-HI", c_elig, lambda d: d["pct_aian"] >= 40, "HI", "20-30 reservations (proxy)"),
]

results = []
for rule_name, high_fn in RULES.items():
    low_fn = LOW_RULES_FN[rule_name]
    row = {"rule": rule_name}
    for cell_id, base_df, race_fn, tier, _ in CELLS:
        if tier == "HI":
            sel = race_fn(base_df) & high_fn(base_df)
        elif tier == "LI":
            sel = race_fn(base_df) & low_fn(base_df)
        else:  # MC
            sel = race_fn(base_df) & ~high_fn(base_df) & ~low_fn(base_df)
        row[cell_id] = int(sel.sum())
    results.append(row)

df_results = pd.DataFrame(results).set_index("rule")
ests = {c[0]: c[4] for c in CELLS}

md = ["# Cell-availability v3 — full 4-dim composite per §2", "",
      "**Dimensions:** poverty (ACS) + food access (USDA) + housing instability (rent burden + renter rate) + school resources (NCES F-33 PPE, negated).",
      "",
      f"**F-33 vintage:** SY 2021-22. {len(county_ppe):,} counties with computed enrollment-weighted PPE. District-level F-33 aggregated to county; tract-level uses parent county PPE.",
      "",
      "## Cell counts under each rule vs §2 estimate",
      "",
      "| Cell | §2 est | **spec 3/4** (faithful) | lenient 2/4 | mean z≥1 |",
      "|---|---|---|---|---|",
]
for cell_id, _, _, _, est in CELLS:
    md.append(f"| {cell_id} | {est} | **{df_results.loc['spec_3_of_4_dims_high', cell_id]:,}** | {df_results.loc['lenient_2_of_4_dims_high', cell_id]:,} | {df_results.loc['mean_z_ge_1', cell_id]:,} |")

md += ["",
       "## Dim-level z distributions (tract / county)",
       "",
       "Tract-level:",
       f"- z_poverty pct≥1: {(tracts['z_poverty']>=1).mean()*100:.1f}%",
       f"- z_food pct≥1: {(tracts['z_food']>=1).mean()*100:.1f}%",
       f"- z_housing pct≥1: {(tracts['z_housing']>=1).mean()*100:.1f}%",
       f"- z_school pct≥1: {(tracts['z_school']>=1).mean()*100:.1f}%",
       "",
       "County-level:",
       f"- z_poverty pct≥1: {(counties['z_poverty']>=1).mean()*100:.1f}%",
       f"- z_food pct≥1: {(counties['z_food']>=1).mean()*100:.1f}%",
       f"- z_housing pct≥1: {(counties['z_housing']>=1).mean()*100:.1f}%",
       f"- z_school pct≥1: {(counties['z_school']>=1).mean()*100:.1f}%",
       ""]

(OUT / "cell_availability_report_v3.md").write_text("\n".join(md), encoding="utf-8")
df_results.T.to_csv(OUT / "cell_availability_counts_v3.csv")
print(f"\nwrote {OUT}/cell_availability_report_v3.md")
print(df_results.T)
