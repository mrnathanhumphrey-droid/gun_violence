"""Path 1b: sweep mean-composite threshold to find the value that preserves
§2's cell structure (especially rural cells).

Tests mean z ≥ 0.5, 0.6, 0.7, 0.8, 1.0. Low-inequity threshold scaled
proportionally (low = -high/2 to match §2's ratio).
"""
import pathlib, pandas as pd, numpy as np, zipfile

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
F33 = ROOT / "inequity_features/nces_school/Sdf22_1a.zip"
CHR = ROOT / "inequity_features/health_access/2023_chr_data_v1.xlsx"
OUT = ROOT / "notes"

# Reuse v4 build logic
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
county_ppe["state"] = county_ppe["CONUM"].str[:2]
county_ppe["county"] = county_ppe["CONUM"].str[2:]

print("Loading CHR 2023...")
chr_df = pd.read_excel(CHR, sheet_name="Ranked Measure Data", header=[0,1])
chr_df.columns = [f"{c[0]}__{c[1]}" if "Unnamed" not in c[0] else c[1] for c in chr_df.columns]
chr_h = chr_df[["FIPS","Uninsured__% Uninsured","Primary Care Physicians__Primary Care Physicians Rate"]].copy()
chr_h["FIPS"] = chr_h["FIPS"].astype(str).str.zfill(5)
chr_h["state"], chr_h["county"] = chr_h["FIPS"].str[:2], chr_h["FIPS"].str[2:]
chr_h["pct_uninsured"] = pd.to_numeric(chr_h["Uninsured__% Uninsured"], errors="coerce")
chr_h["pcp_rate"] = pd.to_numeric(chr_h["Primary Care Physicians__Primary Care Physicians Rate"], errors="coerce")

print("Loading ACS...")
def load(t,g): return pd.read_parquet(ACS / f"acs5_2023_{t}_{g}.parquet")
b01 = {g: load("B01001", g) for g in ["tract","county"]}
b02 = {g: load("B02001", g) for g in ["tract","county"]}
b03 = {g: load("B03003", g) for g in ["tract","county"]}
b17 = {g: load("B17001", g) for g in ["tract","county"]}
b25t = {g: load("B25003", g) for g in ["tract","county"]}
b25r = {g: load("B25070", g) for g in ["tract","county"]}
def n(s): return pd.to_numeric(s, errors="coerce")
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
tracts, counties = build("tract"), build("county")

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

# Join F33 + CHR
for df_pair in [(tracts,), (counties,)]:
    pass
tracts = tracts.merge(county_ppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
counties = counties.merge(county_ppe[["state","county","county_log_ppe"]], on=["state","county"], how="left")
tracts["county_log_ppe"] = tracts["county_log_ppe"].fillna(tracts["county_log_ppe"].median())
counties["county_log_ppe"] = counties["county_log_ppe"].fillna(counties["county_log_ppe"].median())

tracts = tracts.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
counties = counties.merge(chr_h[["state","county","pct_uninsured","pcp_rate"]], on=["state","county"], how="left")
for df in [tracts, counties]:
    df["pct_uninsured"] = df["pct_uninsured"].fillna(df["pct_uninsured"].median())
    df["pcp_rate"] = df["pcp_rate"].fillna(df["pcp_rate"].median())

# 5-dim composite
def add_composite(df):
    df["z_poverty"] = (df["poverty_rate"] - df["poverty_rate"].mean()) / df["poverty_rate"].std()
    df["z_food"]    = (df["food_inequity_score"] - df["food_inequity_score"].mean()) / df["food_inequity_score"].std()
    df["z_rent_b"]  = (df["rent_burden_pct"] - df["rent_burden_pct"].mean()) / df["rent_burden_pct"].std()
    df["z_renter"]  = (df["renter_rate"] - df["renter_rate"].mean()) / df["renter_rate"].std()
    df["z_housing"] = (df["z_rent_b"] + df["z_renter"]) / 2
    df["z_log_ppe"] = (df["county_log_ppe"] - df["county_log_ppe"].mean()) / df["county_log_ppe"].std()
    df["z_school"]  = -df["z_log_ppe"]
    df["z_uninsured"] = (df["pct_uninsured"] - df["pct_uninsured"].mean()) / df["pct_uninsured"].std()
    df["z_pcp"]       = (df["pcp_rate"] - df["pcp_rate"].mean()) / df["pcp_rate"].std()
    df["z_health"]    = (df["z_uninsured"] + (-df["z_pcp"])) / 2
    df["composite_mean"] = (df["z_poverty"] + df["z_food"] + df["z_housing"] + df["z_school"] + df["z_health"]) / 5
    return df
tracts = add_composite(tracts)
counties = add_composite(counties)

# Urban/rural proxy
ct = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts = tracts.merge(ct, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])
t_elig = tracts[tracts["pop_total"] >= 1500].copy()
c_elig = counties[counties["pop_total"] >= 3000].copy()
urban_t = t_elig[t_elig["urban_class"] == "urban"]
suburban_t = t_elig[t_elig["urban_class"] == "suburban"]

# Threshold sweep
THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 1.0]

CELLS = [
    ("UB-HI", urban_t, lambda d: d["pct_black"] >= 60, "HI", "500-1000"),
    ("UH-HI", urban_t, lambda d: d["pct_hispanic"] >= 60, "HI", "500-1000"),
    ("UW-LI", urban_t, lambda d: d["pct_nhw_approx"] >= 70, "LI", "1000+"),
    ("SB-MC", suburban_t, lambda d: d["pct_black"] >= 60, "MC", "300-500"),
    ("RW-HI", c_elig, lambda d: d["pct_nhw_approx"] >= 80, "HI", "150-250"),
    ("RB-HI", c_elig, lambda d: d["pct_black"] >= 50, "HI", "60-100"),
    ("RH-HI", c_elig, lambda d: d["pct_hispanic"] >= 50, "HI", "40-60"),
    ("RNA-HI", c_elig, lambda d: d["pct_aian"] >= 40, "HI", "20-30 (proxy)"),
]

results = []
for t_high in THRESHOLDS:
    t_low = -t_high / 2  # preserve §2's 2:1 ratio (high=1.0, low=-0.5)
    row = {"threshold": f"high≥{t_high}, low≤{t_low}"}
    for cell_id, base_df, race_fn, tier, _ in CELLS:
        if tier == "HI":
            sel = race_fn(base_df) & (base_df["composite_mean"] >= t_high)
        elif tier == "LI":
            sel = race_fn(base_df) & (base_df["composite_mean"] <= t_low)
        else:  # MC: not high, not low
            sel = race_fn(base_df) & (base_df["composite_mean"] > t_low) & (base_df["composite_mean"] < t_high)
        row[cell_id] = int(sel.sum())
    results.append(row)

df_r = pd.DataFrame(results).set_index("threshold")
ests = {c[0]: c[4] for c in CELLS}

md = ["# Cell-availability v5 — mean-composite threshold sweep", "",
      "Locked operationalization: mean of 5 z-scores (poverty + food + housing + school + health). Sweep tested values for the high/low cutoff.",
      "",
      "| Cell | §2 est | mean≥0.5 | mean≥0.6 | **mean≥0.7** | mean≥0.8 | mean≥1.0 |",
      "|---|---|---|---|---|---|---|"]
for cell_id, _, _, _, est in CELLS:
    md.append(f"| {cell_id} | {est} | {df_r.iloc[0, df_r.columns.get_loc(cell_id)]:,} | {df_r.iloc[1, df_r.columns.get_loc(cell_id)]:,} | **{df_r.iloc[2, df_r.columns.get_loc(cell_id)]:,}** | {df_r.iloc[3, df_r.columns.get_loc(cell_id)]:,} | {df_r.iloc[4, df_r.columns.get_loc(cell_id)]:,} |")

md += ["", "## Post-CEM projection (50% retention assumed)", ""]
md += ["| Cell | mean≥0.5 | mean≥0.7 | mean≥1.0 |", "|---|---|---|---|"]
for cell_id, _, _, _, _ in CELLS:
    md.append(f"| {cell_id} | ~{df_r.iloc[0, df_r.columns.get_loc(cell_id)]//2:,} | ~{df_r.iloc[2, df_r.columns.get_loc(cell_id)]//2:,} | ~{df_r.iloc[4, df_r.columns.get_loc(cell_id)]//2:,} |")
md.append("")

(OUT / "cell_availability_threshold_sweep.md").write_text("\n".join(md), encoding="utf-8")
df_r.T.to_csv(OUT / "cell_availability_threshold_sweep.csv")
print(f"\nwrote {OUT}/cell_availability_threshold_sweep.md")
print(df_r.T)
