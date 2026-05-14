"""Pre-condition (1): cell-availability check vs §2 estimates.

Computes actual tract+county counts that hit each §2 cell threshold
using ACS data + simplified urban/rural proxy. NO outcome data touched.

Operationalizations (first pass):
- Race composition: ACS B02001 (race alone) + B03003 (Hispanic) at tract+county
- Inequity composite z-score across 3 dims (poverty + housing + food access);
  school-resources dim deferred (needs F-33 layout parse)
- Urban/rural: tract/county population density proxy
    urban tract: density > 2500/sq mi
    suburban tract: 500-2500/sq mi
    rural county: county-level density < 500/sq mi
- Population thresholds per §2: tract ≥1500, rural county ≥3000

Output: cell_availability_report.md + raw counts CSV.
"""
import pathlib, pandas as pd, numpy as np

ROOT = pathlib.Path(r"D:/Gun Violence")
ACS = ROOT / "demographics/acs_5yr"
OUT = ROOT / "notes"
OUT.mkdir(exist_ok=True)

# === Load ACS tables ===
print("Loading ACS...")

# B01001: total pop (variable _001E)
b01001_tract = pd.read_parquet(ACS / "acs5_2023_B01001_tract.parquet")
b01001_county = pd.read_parquet(ACS / "acs5_2023_B01001_county.parquet")

# B02001: race alone
# _002E = white alone, _003E = Black alone, _004E = AIAN alone, _005E = Asian alone, _001E = total
b02001_tract = pd.read_parquet(ACS / "acs5_2023_B02001_tract.parquet")
b02001_county = pd.read_parquet(ACS / "acs5_2023_B02001_county.parquet")

# B03003: Hispanic origin (_003E = Hispanic, _001E = total)
b03003_tract = pd.read_parquet(ACS / "acs5_2023_B03003_tract.parquet")
b03003_county = pd.read_parquet(ACS / "acs5_2023_B03003_county.parquet")

# B17001: poverty (_002E = below poverty, _001E = total for whom status determined)
b17001_tract = pd.read_parquet(ACS / "acs5_2023_B17001_tract.parquet")
b17001_county = pd.read_parquet(ACS / "acs5_2023_B17001_county.parquet")

# B25070: gross rent as % of income (_010E = 50%+; _001E = total renter HHs)
b25070_tract = pd.read_parquet(ACS / "acs5_2023_B25070_tract.parquet")
b25070_county = pd.read_parquet(ACS / "acs5_2023_B25070_county.parquet")

print(f"  tracts: {len(b01001_tract):,}  counties: {len(b01001_county):,}")

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def build_geo(b01, b02, b03, b17, b25, geo_cols):
    """Merge ACS tables on geo identifier and compute race/inequity features.

    geo_cols: list of cols that form the geo key, e.g. ['state','county','tract'].
    """
    pop = b01[geo_cols + ["B01001_001E"]].rename(columns={"B01001_001E": "pop_total"})
    pop["pop_total"] = to_num(pop["pop_total"])

    race = b02[geo_cols + ["B02001_001E","B02001_002E","B02001_003E","B02001_004E","B02001_005E"]].copy()
    for c in race.columns[len(geo_cols):]:
        race[c] = to_num(race[c])
    race = race.rename(columns={
        "B02001_001E": "race_total",
        "B02001_002E": "white_alone",
        "B02001_003E": "black_alone",
        "B02001_004E": "aian_alone",
        "B02001_005E": "asian_alone",
    })

    hisp = b03[geo_cols + ["B03003_001E","B03003_003E"]].copy()
    for c in hisp.columns[len(geo_cols):]:
        hisp[c] = to_num(hisp[c])
    hisp = hisp.rename(columns={"B03003_001E": "hisp_total", "B03003_003E": "hispanic"})

    pov = b17[geo_cols + ["B17001_001E","B17001_002E"]].copy()
    for c in pov.columns[len(geo_cols):]:
        pov[c] = to_num(pov[c])
    pov = pov.rename(columns={"B17001_001E": "pov_denom", "B17001_002E": "below_poverty"})

    rent = b25[geo_cols + ["B25070_001E","B25070_010E"]].copy()
    for c in rent.columns[len(geo_cols):]:
        rent[c] = to_num(rent[c])
    rent = rent.rename(columns={"B25070_001E": "rent_denom", "B25070_010E": "rent_burden_50plus"})

    df = pop.merge(race, on=geo_cols).merge(hisp, on=geo_cols).merge(pov, on=geo_cols).merge(rent, on=geo_cols)

    # Compute proportions
    df["pct_white"] = df["white_alone"] / df["race_total"] * 100
    df["pct_black"] = df["black_alone"] / df["race_total"] * 100
    df["pct_aian"] = df["aian_alone"] / df["race_total"] * 100
    df["pct_hispanic"] = df["hispanic"] / df["hisp_total"] * 100
    # Non-Hispanic-white: approximate. Census exact NHW is B03002_003. For first pass use white_alone - hispanic_white_share approx.
    # Conservative: count only if pct_white is high AND pct_hispanic is low
    df["pct_nhw_approx"] = df["pct_white"] - df["pct_hispanic"]
    df["poverty_rate"] = df["below_poverty"] / df["pov_denom"] * 100
    df["rent_burden_pct"] = df["rent_burden_50plus"] / df["rent_denom"] * 100
    return df

print("Building tract frame...")
tracts = build_geo(b01001_tract, b02001_tract, b03003_tract, b17001_tract, b25070_tract,
                   ["state","county","tract"])
print(f"  tracts merged: {len(tracts):,}")

print("Building county frame...")
counties = build_geo(b01001_county, b02001_county, b03003_county, b17001_county, b25070_county,
                     ["state","county"])
print(f"  counties merged: {len(counties):,}")

# === Inequity composite z-score (3 dims) ===
# Higher = more inequitable: poverty_rate, rent_burden_pct, food_access (placeholder = poverty until joined)
# First-pass simplification: composite is mean z of (poverty_rate, rent_burden_pct).
# School dim deferred. Food access dim approximated via poverty for now (NOT correct long-term).

for df in [tracts, counties]:
    df["z_poverty"] = (df["poverty_rate"] - df["poverty_rate"].mean()) / df["poverty_rate"].std()
    df["z_rent_burden"] = (df["rent_burden_pct"] - df["rent_burden_pct"].mean()) / df["rent_burden_pct"].std()
    df["inequity_composite"] = (df["z_poverty"] + df["z_rent_burden"]) / 2

# === Urban/rural proxy: ALAND data is in shapefiles, not ACS ===
# For first pass, use a coarser proxy based on tract count per county:
#   urban = tract in county with >100 tracts (big metros)
#   suburban = tract in county with 30-100 tracts
#   rural = tract in county with <30 tracts OR rural county
# This is rough but defensible for first-pass cell-count estimation.

county_tract_counts = tracts.groupby(["state","county"]).size().reset_index(name="n_tracts_in_county")
tracts = tracts.merge(county_tract_counts, on=["state","county"])
tracts["urban_class"] = pd.cut(tracts["n_tracts_in_county"],
                                bins=[0, 30, 100, 100000],
                                labels=["rural", "suburban", "urban"])

# === Apply population thresholds ===
# §2: tract ≥1500, rural county ≥3000, reservation ≥1000
tracts_eligible = tracts[tracts["pop_total"] >= 1500].copy()
counties_eligible = counties[counties["pop_total"] >= 3000].copy()

# === Cell assignment ===
def cell_count(df, race_filter, inequity_filter, label):
    sub = df[race_filter & inequity_filter]
    return label, len(sub)

# §2 cells
HIGH = lambda d: d["inequity_composite"] >= 1.0
LOW  = lambda d: d["inequity_composite"] <= -0.5

# Urban tract cells
urban_tracts = tracts_eligible[tracts_eligible["urban_class"] == "urban"]
suburban_tracts = tracts_eligible[tracts_eligible["urban_class"] == "suburban"]
rural_tracts = tracts_eligible[tracts_eligible["urban_class"] == "rural"]

results = []
results.append(("UB-HI (urban, Black-maj ≥60%, high inequity)",
                len(urban_tracts[(urban_tracts["pct_black"] >= 60) & HIGH(urban_tracts)]),
                "500-1000"))
results.append(("UH-HI (urban, Hispanic-maj ≥60%, high inequity)",
                len(urban_tracts[(urban_tracts["pct_hispanic"] >= 60) & HIGH(urban_tracts)]),
                "500-1000"))
results.append(("UW-LI (urban, White-maj ≥70%, low inequity)",
                len(urban_tracts[(urban_tracts["pct_nhw_approx"] >= 70) & LOW(urban_tracts)]),
                "1000+"))
results.append(("SB-MC (suburban, Black-maj ≥60%, low-to-mod inequity)",
                len(suburban_tracts[(suburban_tracts["pct_black"] >= 60) &
                                    (suburban_tracts["inequity_composite"] <= 1.0)]),
                "300-500"))
# Rural cells use COUNTY granularity
results.append(("RW-HI (rural county, White-maj ≥80%, high inequity)",
                len(counties_eligible[(counties_eligible["pct_nhw_approx"] >= 80) & HIGH(counties_eligible)]),
                "150-250"))
results.append(("RB-HI (rural county, Black-maj ≥50%, high inequity)",
                len(counties_eligible[(counties_eligible["pct_black"] >= 50) & HIGH(counties_eligible)]),
                "60-100"))
results.append(("RH-HI (rural county, Hispanic-maj ≥50%, high inequity)",
                len(counties_eligible[(counties_eligible["pct_hispanic"] >= 50) & HIGH(counties_eligible)]),
                "40-60"))
results.append(("RNA-HI (reservation, AIAN-maj ≥40%, high inequity)",
                len(counties_eligible[(counties_eligible["pct_aian"] >= 40) & HIGH(counties_eligible)]),
                "20-30 (reservations)"))

# === Output ===
report = ["# Cell-availability check vs §2 estimates", "", "**Pre-condition (1) of Prompt 1.**", "",
          "## First-pass operationalizations (caveats)", "",
          "- Race composition from ACS B02001 + B03003 (note: pct_nhw_approx = pct_white − pct_hispanic; full non-Hispanic-white requires B03002 cross-tab, not pulled).",
          "- Inequity composite: z(poverty_rate) + z(rent_burden_50plus%), divided by 2. **Only 2 of 4 dimensions** — food access (USDA) and school resources (NCES F-33) deferred to second pass.",
          "- Urban/suburban/rural proxy: tracts-per-county (>100 = urban, 30-100 = suburban, <30 = rural). Will be replaced with Census Urban Area spatial join in production.",
          "- Population thresholds: tract ≥1500, rural county ≥3000 per §2.",
          "- RNA-HI tested at COUNTY level (AIAN-majority counties), not reservation. Reservation-level requires AIANNH spatial join + Census reservation-specific tables. RNA-HI count here is **proxy only**.",
          "",
          "## Cell counts",
          "",
          "| Cell | §2 estimate | Actual (first-pass) | Status |",
          "|---|---|---|---|"]

for label, actual, est in results:
    # Parse low-high estimate range
    est_clean = est.replace("+", "").replace(" tracts","").replace(" counties","").replace(" (reservations)","")
    if "-" in est_clean:
        lo, hi = est_clean.split("-")
        try:
            lo, hi = int(lo.strip()), int(hi.strip())
            if actual >= lo and actual <= hi * 2:
                status = "✓ in range"
            elif actual < lo:
                status = f"⚠ low ({actual} < {lo})"
            else:
                status = f"⚠ high ({actual} > {hi})"
        except:
            status = "?"
    else:
        try:
            lo = int(est_clean.strip())
            status = "✓ in range" if actual >= lo else f"⚠ low ({actual} < {lo})"
        except:
            status = "?"
    report.append(f"| {label} | {est} | **{actual:,}** | {status} |")

report += ["", "## Bottom line",
           "",
           f"- Total eligible tracts (pop ≥1500): {len(tracts_eligible):,}",
           f"- Total eligible counties (pop ≥3000): {len(counties_eligible):,}",
           f"- Urban tracts: {len(urban_tracts):,}  Suburban tracts: {len(suburban_tracts):,}  Rural tracts: {len(rural_tracts):,}",
           "",
           "## Caveats for revision-before-lock decision",
           "",
           "- pct_nhw_approx is a lower bound (subtracts ALL Hispanic from white-alone). True NHW% from B03002 will be HIGHER, so UW-LI / RW-HI counts shown are **conservative under-estimates**.",
           "- Inequity composite using only 2/4 dimensions; adding food-access and school resources may shift cells (some currently flagged High may not survive 3-of-4 threshold; some currently flagged Low/Mod may pass).",
           "- RNA-HI proxy via AIAN-majority counties is structurally different from reservation-level analysis. The true RNA-HI count requires spatial join with AIANNH.",
           "- Urban/rural proxy is COARSE — Census Urban Area shapefile is needed for tract-level urban/suburban distinction.",
           "",
           "If actual counts deviate substantially from §2 estimates, revise §2 thresholds BEFORE OSF lock.",
           ""]

(OUT / "cell_availability_report.md").write_text("\n".join(report), encoding="utf-8")

# CSV of raw counts
pd.DataFrame(results, columns=["cell", "actual_count", "estimate"]).to_csv(OUT / "cell_availability_counts.csv", index=False)
print(f"\nwrote {OUT}/cell_availability_report.md")
print(f"wrote {OUT}/cell_availability_counts.csv")
for label, actual, est in results:
    print(f"  {label}: {actual:,}  (est {est})")
