"""Pre-condition (1) v2: 3-dim inequity composite + USDA food access.

Adds USDA Food Access Atlas low-access population share as the third
inequity dimension. Tests three compositing rules (lenient → strict).
School-resources (NCES F-33) deferred to v3.
"""
import pathlib, pandas as pd, numpy as np

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
USDA = ROOT / "inequity_features/usda_food_access/FoodAccessResearchAtlasData2019.xlsx"
OUT = ROOT / "notes"

# === Load ACS (subset of v1) ===
print("Loading ACS...")
def load(tbl, geo):
    return pd.read_parquet(ACS / f"acs5_2023_{tbl}_{geo}.parquet")

b01 = {g: load("B01001", g) for g in ["tract", "county"]}
b02 = {g: load("B02001", g) for g in ["tract", "county"]}
b03 = {g: load("B03003", g) for g in ["tract", "county"]}
b17 = {g: load("B17001", g) for g in ["tract", "county"]}
b25t = {g: load("B25003", g) for g in ["tract", "county"]}   # tenure
b25r = {g: load("B25070", g) for g in ["tract", "county"]}   # rent burden

def to_num(s): return pd.to_numeric(s, errors="coerce")

def build(geo):
    keys = ["state","county","tract"] if geo == "tract" else ["state","county"]
    pop = b01[geo][keys + ["B01001_001E"]].copy()
    pop["pop_total"] = to_num(pop["B01001_001E"])

    race = b02[geo][keys + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E"]].copy()
    for c in race.columns[len(keys):]:
        race[c] = to_num(race[c])
    race = race.rename(columns={
        "B02001_001E": "race_total", "B02001_002E": "white_alone",
        "B02001_003E": "black_alone", "B02001_004E": "aian_alone",
    })
    hisp = b03[geo][keys + ["B03003_001E","B03003_003E"]].copy()
    for c in hisp.columns[len(keys):]:
        hisp[c] = to_num(hisp[c])
    hisp = hisp.rename(columns={"B03003_001E": "hisp_total", "B03003_003E": "hispanic"})

    pov = b17[geo][keys + ["B17001_001E","B17001_002E"]].copy()
    for c in pov.columns[len(keys):]:
        pov[c] = to_num(pov[c])
    pov = pov.rename(columns={"B17001_001E": "pov_denom", "B17001_002E": "below_poverty"})

    ten = b25t[geo][keys + ["B25003_001E","B25003_002E"]].copy()
    for c in ten.columns[len(keys):]:
        ten[c] = to_num(ten[c])
    ten = ten.rename(columns={"B25003_001E": "ten_total", "B25003_002E": "owner_occ"})

    rent = b25r[geo][keys + ["B25070_001E","B25070_010E"]].copy()
    for c in rent.columns[len(keys):]:
        rent[c] = to_num(rent[c])
    rent = rent.rename(columns={"B25070_001E": "rent_denom", "B25070_010E": "rent_burden_50plus"})

    df = pop[keys + ["pop_total"]].merge(race, on=keys).merge(hisp, on=keys).merge(pov, on=keys).merge(ten, on=keys).merge(rent, on=keys)

    df["pct_white"] = df["white_alone"] / df["race_total"] * 100
    df["pct_black"] = df["black_alone"] / df["race_total"] * 100
    df["pct_aian"] = df["aian_alone"] / df["race_total"] * 100
    df["pct_hispanic"] = df["hispanic"] / df["hisp_total"] * 100
    df["pct_nhw_approx"] = df["pct_white"] - df["pct_hispanic"]
    df["poverty_rate"] = df["below_poverty"] / df["pov_denom"] * 100
    df["renter_rate"] = (1 - df["owner_occ"] / df["ten_total"]) * 100
    df["rent_burden_pct"] = df["rent_burden_50plus"] / df["rent_denom"] * 100
    return df, keys

tracts, _ = build("tract")
counties, _ = build("county")
print(f"  tracts: {len(tracts):,}  counties: {len(counties):,}")

# === Load USDA Food Access (tract-level) ===
print("Loading USDA Food Access (this may take a moment)...")
fa = pd.read_excel(USDA, sheet_name="Food Access Research Atlas")
print(f"  USDA rows: {len(fa):,}  cols: {len(fa.columns)}")
# Key variables:
#   CensusTract: 11-digit tract GEOID
#   Pop2010: tract pop
#   lapop1share: % pop with low access at 1 mile (urban)
#   lapop10share: % pop with low access at 10 miles (rural)
#   LILATracts_1And10: binary LILA flag
fa["CensusTract"] = fa["CensusTract"].astype(str).str.zfill(11)
fa["state_fips"] = fa["CensusTract"].str[:2]
fa["county_fips"] = fa["CensusTract"].str[2:5]
fa["tract_fips"] = fa["CensusTract"].str[5:]

# Combined low-access share: use 1-mile in urban, 10-mile in rural (USDA convention)
# Simpler: take the max (penalizes if either threshold flags)
fa["low_access_share"] = pd.to_numeric(fa["lapop1share"], errors="coerce").fillna(0)
# Also include 10-mile for rural
fa["low_access_10mi"] = pd.to_numeric(fa["lapop10share"], errors="coerce").fillna(0)
fa["food_inequity_score"] = fa[["low_access_share","low_access_10mi"]].max(axis=1)
# Population for aggregation
fa["pop_2010"] = pd.to_numeric(fa["Pop2010"], errors="coerce").fillna(0)

# Tract-level join key matches ACS state+county+tract
tracts_fa = fa[["state_fips","county_fips","tract_fips","food_inequity_score","pop_2010"]].rename(
    columns={"state_fips":"state","county_fips":"county","tract_fips":"tract"})

tracts2 = tracts.merge(tracts_fa, on=["state","county","tract"], how="left")
n_with_fa = tracts2["food_inequity_score"].notna().sum()
print(f"  tracts with USDA food-access match: {n_with_fa:,} / {len(tracts2):,}")
# Fallback for unmatched tracts: imputed = median
tracts2["food_inequity_score"] = tracts2["food_inequity_score"].fillna(tracts2["food_inequity_score"].median())

# County-level: aggregate FA via population-weighted mean
fa_county = fa.groupby(["state_fips","county_fips"]).apply(
    lambda g: (g["food_inequity_score"] * g["pop_2010"]).sum() / max(g["pop_2010"].sum(), 1)
).reset_index(name="food_inequity_score").rename(columns={"state_fips":"state","county_fips":"county"})
counties2 = counties.merge(fa_county, on=["state","county"], how="left")
counties2["food_inequity_score"] = counties2["food_inequity_score"].fillna(counties2["food_inequity_score"].median())

# === 3-dim inequity composite ===
def add_composites(df):
    df["z_poverty"] = (df["poverty_rate"] - df["poverty_rate"].mean()) / df["poverty_rate"].std()
    df["z_food"]    = (df["food_inequity_score"] - df["food_inequity_score"].mean()) / df["food_inequity_score"].std()
    # Housing instability composite (rent burden + renter rate) standardized once
    df["z_rent_burden"] = (df["rent_burden_pct"] - df["rent_burden_pct"].mean()) / df["rent_burden_pct"].std()
    df["z_renter"]      = (df["renter_rate"] - df["renter_rate"].mean()) / df["renter_rate"].std()
    df["z_housing"] = (df["z_rent_burden"] + df["z_renter"]) / 2

    # Composite for 3-dim (lenient: mean z)
    df["composite_mean"] = (df["z_poverty"] + df["z_food"] + df["z_housing"]) / 3

    # Compositing rule per §2: per-dim z ≥ +1.0 in at least k of 3 dims
    df["n_dims_high"] = (
        (df["z_poverty"] >= 1.0).astype(int)
        + (df["z_food"] >= 1.0).astype(int)
        + (df["z_housing"] >= 1.0).astype(int)
    )
    df["n_dims_low"] = (
        (df["z_poverty"] <= -0.5).astype(int)
        + (df["z_food"] <= -0.5).astype(int)
        + (df["z_housing"] <= -0.5).astype(int)
    )
    return df

tracts2 = add_composites(tracts2)
counties2 = add_composites(counties2)

# === Urban/rural proxy (same as v1) ===
ct = tracts2.groupby(["state","county"]).size().reset_index(name="n_tracts")
tracts2 = tracts2.merge(ct, on=["state","county"])
tracts2["urban_class"] = pd.cut(tracts2["n_tracts"], bins=[0,30,100,1000000], labels=["rural","suburban","urban"])

# === Population thresholds ===
t_elig = tracts2[tracts2["pop_total"] >= 1500].copy()
c_elig = counties2[counties2["pop_total"] >= 3000].copy()

urban_t = t_elig[t_elig["urban_class"] == "urban"]
suburban_t = t_elig[t_elig["urban_class"] == "suburban"]

# === Three rules tested ===
RULES = {
    "lenient_mean_z_ge_1": lambda d: d["composite_mean"] >= 1.0,
    "spec_2_of_3_dims_high": lambda d: d["n_dims_high"] >= 2,
    "strict_3_of_3_dims_high": lambda d: d["n_dims_high"] >= 3,
}
LOW_RULES = {
    "lenient_mean_z_le_neg_half": lambda d: d["composite_mean"] <= -0.5,
    "spec_2_of_3_dims_low": lambda d: d["n_dims_low"] >= 2,
    "strict_3_of_3_dims_low": lambda d: d["n_dims_low"] >= 3,
}

CELLS = [
    ("UB-HI", urban_t, lambda d: d["pct_black"] >= 60, "HI", "500-1000"),
    ("UH-HI", urban_t, lambda d: d["pct_hispanic"] >= 60, "HI", "500-1000"),
    ("UW-LI", urban_t, lambda d: d["pct_nhw_approx"] >= 70, "LI", "1000+"),
    ("SB-MC", suburban_t, lambda d: d["pct_black"] >= 60, "MC", "300-500"),
    ("RW-HI", c_elig, lambda d: d["pct_nhw_approx"] >= 80, "HI", "150-250"),
    ("RB-HI", c_elig, lambda d: d["pct_black"] >= 50, "HI", "60-100"),
    ("RH-HI", c_elig, lambda d: d["pct_hispanic"] >= 50, "HI", "40-60"),
    ("RNA-HI", c_elig, lambda d: d["pct_aian"] >= 40, "HI", "20-30 reservations (proxy: AIAN-maj counties)"),
]

# Build results for each rule
all_results = []
for rule_name in RULES.keys():
    high_fn = RULES[rule_name]
    low_rule = rule_name.replace("ge_1","le_neg_half").replace("dims_high","dims_low")
    # Match the low rule by replacing high with low
    if "lenient" in rule_name:
        low_fn = LOW_RULES["lenient_mean_z_le_neg_half"]
    elif "2_of_3" in rule_name:
        low_fn = LOW_RULES["spec_2_of_3_dims_low"]
    else:
        low_fn = LOW_RULES["strict_3_of_3_dims_low"]
    # MC = neither HI nor LI strictly; for SB-MC use composite_mean between -0.5 and 1.0
    mc_fn = lambda d: ~high_fn(d)

    row = {"rule": rule_name}
    for cell_id, base_df, race_fn, tier, est in CELLS:
        if tier == "HI":
            sel = race_fn(base_df) & high_fn(base_df)
        elif tier == "LI":
            sel = race_fn(base_df) & low_fn(base_df)
        else:  # MC
            sel = race_fn(base_df) & mc_fn(base_df) & (~low_fn(base_df))
        row[cell_id] = int(sel.sum())
    all_results.append(row)

df_results = pd.DataFrame(all_results).set_index("rule")
print("\n=== CELL COUNTS BY RULE ===")
print(df_results.T)

# === Write report ===
ests = {c[0]: c[4] for c in CELLS}
md = ["# Cell-availability v2 — 3-dim composite (poverty + food access + housing instability)", "",
      "## Three compositing rules tested",
      "",
      "| Rule | Description |",
      "|---|---|",
      "| `lenient_mean_z_ge_1` | composite_mean = mean(z_poverty + z_food + z_housing) / 3 ≥ +1.0 |",
      "| `spec_2_of_3_dims_high` | per-dim z ≥ +1.0 in at least 2 of 3 dims (faithful to §2's 'at least 3 of 4' relaxed to 3 dims) |",
      "| `strict_3_of_3_dims_high` | per-dim z ≥ +1.0 in ALL 3 dims (strictest) |",
      "",
      "## Cell counts under each rule vs §2 estimate",
      "",
      "| Cell | §2 est | lenient | spec 2/3 | strict 3/3 |",
      "|---|---|---|---|---|",
]
for cell_id, _, _, _, _ in CELLS:
    md.append(f"| {cell_id} | {ests[cell_id]} | {df_results.loc['lenient_mean_z_ge_1', cell_id]:,} | {df_results.loc['spec_2_of_3_dims_high', cell_id]:,} | {df_results.loc['strict_3_of_3_dims_high', cell_id]:,} |")

md += ["",
       "## Diagnostic: dim-level z-score distributions",
       "",
       "Tract-level (high-inequity-eligible):",
       f"- z_poverty:       mean {tracts2['z_poverty'].mean():.2f}, sd {tracts2['z_poverty'].std():.2f}, pct≥1: {(tracts2['z_poverty']>=1).mean()*100:.1f}%",
       f"- z_food:          mean {tracts2['z_food'].mean():.2f}, sd {tracts2['z_food'].std():.2f}, pct≥1: {(tracts2['z_food']>=1).mean()*100:.1f}%",
       f"- z_housing:       mean {tracts2['z_housing'].mean():.2f}, sd {tracts2['z_housing'].std():.2f}, pct≥1: {(tracts2['z_housing']>=1).mean()*100:.1f}%",
       "",
       "County-level:",
       f"- z_poverty:       mean {counties2['z_poverty'].mean():.2f}, sd {counties2['z_poverty'].std():.2f}, pct≥1: {(counties2['z_poverty']>=1).mean()*100:.1f}%",
       f"- z_food:          mean {counties2['z_food'].mean():.2f}, sd {counties2['z_food'].std():.2f}, pct≥1: {(counties2['z_food']>=1).mean()*100:.1f}%",
       f"- z_housing:       mean {counties2['z_housing'].mean():.2f}, sd {counties2['z_housing'].std():.2f}, pct≥1: {(counties2['z_housing']>=1).mean()*100:.1f}%",
       "",
       "## Verdict",
       "",
       "Compare the three rules' counts to the §2 estimates. Pick the rule whose counts MOST CLOSELY match the §2 expectation — that's the operationalization §2's author had in mind.",
       "",
       "Caveats unchanged from v1: pct_nhw_approx is conservative (subtract Hispanic from white-alone); urban/rural via tract-per-county proxy; school-resources dimension still deferred; RNA-HI uses AIAN-majority county proxy, not reservation.",
       ""]

(OUT / "cell_availability_report_v2.md").write_text("\n".join(md), encoding="utf-8")
df_results.T.to_csv(OUT / "cell_availability_counts_v2.csv")
print(f"\nwrote {OUT}/cell_availability_report_v2.md")
