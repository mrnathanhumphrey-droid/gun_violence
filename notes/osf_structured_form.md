# OSF Pre-Registration — Structured Form Fields

Paste each section verbatim into the corresponding field on OSF's pre-registration form. Field names below match OSF's standard "OSF Preregistration" template (also compatible with "OSF Standard Pre-Data-Collection Registration").

**Source document for the PDF upload:** `gun_violence_research_design_v2.pdf` (merge v1 PDF + `pre_reg_redline.md` revisions before upload).

---

## Study Information

### Title
Cross-Geography Decoupling of Race and Structural Inequity Effects on Gun Violence Rates in Working-Class American Communities

### Description / Abstract (1–2 paragraphs)
This study tests whether race composition predicts gun violence rates independently of structural inequity features, when race and inequity are decoupled by sampling across census tracts and counties where they vary independently rather than within-city where they covary. Cells are defined by demographic × inequity × geographic-type combinations and include intentionally-decoupled comparisons: Black-majority suburban tracts at low-to-moderate inequity (SB-MC) and white-majority rural counties at high inequity (RW-HI). Five pre-registered hypotheses (H_INEQUITY, H_RACE_PURE, H_INTERACTION, H_HISTORICAL_MECHANISM, H_GEOGRAPHIC_MECHANISM) each carry a quantitative falsification criterion. The analysis uses a hierarchical Bayesian negative-binomial regression with partial pooling across cells and model-based socioeconomic-covariate adjustment.

Cell-level inequity is operationalized as a mean composite z-score across five within-urbanicity-stratified dimensions: poverty rate, food access (USDA), housing instability, school resources (NCES log per-pupil expenditure), and health access (CHR uninsured + PCP rate). Findings are reported with explicit power-tier stratification: Tier 1 strong claims, Tier 2 moderate, Tier 3 hypothesis-generating only. The study sits methodologically inside a multi-substrate methodology corpus (Paper 6) demonstrating the partial-pooling-of-residual-classes framework across mathematics, sports, options, cancer genomics, and now gun violence.

### Hypotheses (verbatim from §6 with falsification criteria)

**H_INEQUITY** — Inequity features predict gun violence rates. Race composition predicts only through correlation with inequity features. After conditioning on the inequity feature set, race adds no significant independent predictive power.

*Predicted pattern in decoupled cells:* SB-MC (Black-majority, low inequity) has low gun violence rates comparable to UW-LI; RW-HI (white-majority, high inequity) has high rates comparable to other high-inequity cells; cross-cell variation tracks inequity composite not race; race coefficient in joint model approximately zero after inequity adjustment.

*Falsification criterion:* Race composition contributes **≥15%** additional variance beyond inequity features in the joint model.

**H_RACE_PURE** — Race composition independently predicts gun violence rates beyond what inequity features explain. Some causal pathway operates through race-specific mechanisms not captured by measured inequity features.

*Predicted pattern in decoupled cells:* SB-MC gun violence rates elevated relative to UW-LI despite comparable inequity; RW-HI rates not as elevated as urban Black-majority cells despite comparable inequity; race coefficient retains significance after inequity adjustment.

*Falsification criterion:* Race composition contributes **<5%** additional variance beyond inequity features.

**H_INTERACTION** — Race × inequity interaction effects predict gun violence rates. Neither marginal effect is sufficient; the joint co-occurrence is what matters.

*Predicted pattern:* Maximum rates in cells where high-inequity Black-majority intersect (UB-HI > sum of marginal effects); off-diagonal cells (SB-MC, RW-HI) have intermediate rates; interaction term significant in joint model.

*Falsification criterion:* Race × inequity interaction explains **<3%** additional variance beyond main effects.

**H_HISTORICAL_MECHANISM** — Specific historical mechanisms (redlining, Reconstruction violence, economic collapse, treaty violations) explain geographic variation in gun violence rates beyond contemporary inequity features. The mechanism, not the current condition, is the causal driver.

*Predicted pattern:* Cells with same contemporary inequity profile but different historical mechanisms have different gun violence rates; UB-HI (post-redlining) ≠ RB-HI (post-Reconstruction) ≠ RW-HI (post-industrial collapse); historical mechanism markers add significant predictive power in joint model.

*Falsification criterion:* Historical mechanism markers add **<5%** additional variance beyond contemporary inequity features.

**H_GEOGRAPHIC_MECHANISM** — Specific inequity features have different effects in different geographic types. The food-access effect in urban tracts works through different intermediate pathways than the food-access effect in rural counties.

*Predicted pattern:* Same inequity feature has different effect sizes (and possibly different signs) across geographic types; geographic-type × inequity-feature interaction significant; findings stratified by geographic type rather than averaged.

*Falsification criterion:* Geographic-type × inequity-feature interactions consistently explain **<2%** additional variance beyond main effects.

**Note:** The hypotheses are not mutually exclusive. Findings may support combinations (e.g., H_INEQUITY + H_GEOGRAPHIC_MECHANISM). The pre-registration is what each hypothesis would predict, not which hypothesis is expected.

---

## Design Plan

### Study type
Observational cross-sectional study with decoupled-cell sampling design.

### Blinding
Not applicable (no intervention, no participant assignment).

### Study design
Cross-sectional observational at unit-of-analysis level: census tracts (urban + suburban cells) and counties (rural cells), with reservations as a separate cell type. The decoupled-cell design samples across geographic types where race composition and structural inequity vary independently, rather than within a single city where they covary (e.g., Baltimore-style within-city studies). The decoupling is the methodological contribution: cells like SB-MC (Black-majority, low inequity) and RW-HI (white-majority, high inequity) are sampled specifically because they break the standard within-city correlation between race and inequity.

### Randomization
Not applicable. Sampling is deliberately stratified by cell, not random.

---

## Sampling Plan

### Existing data
Existing data only. All outcome and predictor data are publicly available secondary data (no human-subjects collection):
- Census ACS 2019–2023 5-year estimates (tract + county; 13 tables)
- CDC WISQARS firearm deaths 2019–2023 (county-level, scraped via API)
- Gun Violence Archive mass-shooting subset 2013–2026 (via dxzys/Gun-Violence-Data)
- USDA Food Access Research Atlas 2019
- NCES Common Core of Data F-33 finance SY 2018-19 through 2021-22
- TIGER/Line 2024 (counties, tracts, school districts, AIANNH reservations)
- HOLC Mapping Inequality (1935–1940, historical mechanism marker)
- Eviction Lab ETS 2020–2021 (where available)
- County Health Rankings 2023 (health access dimension)

Data manifest: `D:/Gun Violence/manifest.json` (17 sources, ~1.5 GB total).

### Explanation of existing data
All data are pre-existing secondary public records. No outcome data has been inspected at the cell level or rate level prior to pre-registration. Pre-condition (3) of Prompt 1 was verified: only metadata-level row counts seen on CDC psx4-wq38 (132K rows, 6 intent classes) and the GVA mass-shooting subset (5,872 records); no spatial joins, no rate calculations, no cell-level outcome data inspected.

### Data collection procedures
Data assembly is complete. The 17 sources were pulled and verified for integrity (SHA-256 hashes in `manifest.json`) before any cell-level construction. WISQARS firearm-death data scraped from the `wisqars.cdc.gov/api/fatal-county` endpoint with `mech=20810` (firearm) for years 2019–2023, all intents (homicide + suicide + unintentional + undetermined), national county granularity. Provides 3,143 counties × 5 years × 4 intents.

### Sample size
Pre-CEM-replacement (CEM dropped per v2 §3 revision; see v2 redline `pre_reg_redline.md`):

| Cell | Sample size | Power tier |
|---|---|---|
| UB-HI (urban Black-maj ≥60%, high inequity) | 846 tracts | Tier 1 (strong claims) |
| UH-HI (urban Hispanic-maj ≥60%, high inequity) | 1,830 tracts | Tier 1 |
| UW-LI (urban white-maj ≥70%, low inequity, control) | 4,600 tracts | Tier 1 |
| SB-MC (suburban Black-maj ≥60%, low-to-moderate inequity) | 291 tracts | Tier 1 |
| RW-HI (rural white-maj ≥80%, high inequity) | 55 counties | Tier 2 (moderate claims) |
| RB-HI (rural Black-maj ≥50%, high inequity) | 51 counties | Tier 2 |
| RH-HI (rural Hispanic-maj ≥50%, high inequity) | 94 counties | Tier 2 |
| RNA-HI (reservation/AIAN-maj ≥40%, high inequity) | 12 (county proxy) | Tier 3 (hypothesis-generating) |

### Sample size rationale
Power tiers per §7: Tier 1 cells (≥120 units) support strong-claim effect estimates with 95% credible intervals; Tier 2 cells (25–100) support moderate claims with caveats; Tier 3 cells (8–24) support hypothesis-generating language only. Cross-cell pattern claims use the full joint sample (8,779 units total) and are well-powered for cross-cell effects even where individual cells are not.

### Stopping rule
No stopping rule applicable to a cross-sectional observational design on a fixed time window (2019–2023). The cell sizes above are determined by the cell-inclusion criteria applied to the full ACS / WISQARS / GVA universe.

---

## Variables

### Manipulated variables
None (observational design).

### Measured variables — outcomes
Primary outcome: **gun violence rate per 100,000 population per year, averaged over the 2019–2023 window.** Components:
- Firearm homicide (WISQARS ICD-10 X93-X95, U01.4) — scraped from wisqars.cdc.gov/api
- Firearm suicide (WISQARS X72-X74, Y22-Y24) — same source
- Non-fatal firearm injury — operationally defined as GVA-tracked incident records (mass-shooting subset, n ≈ 5,872 since 2013, geocoded to lat/lon). **Caveat:** GVA's collection is news-mediated and does not cover the full US non-fatal firearm injury population (hospital surveillance — NEISS/HCUP — would be needed for that, deferred as Phase-2 supplement).

Excluded from outcome: police-involved shootings (different mechanism); accidental shootings (sparse counts); mass shootings as a separate categorical outcome (rare events, statistically unstable at cell level).

Secondary outcomes: firearm homicide only; firearm suicide only; non-fatal firearm injury only — for sensitivity analyses.

### Measured variables — independent variables (predictors)
1. **Race composition** (ACS B02001 + B03003): pct non-Hispanic white, pct non-Hispanic Black, pct Hispanic, pct non-Hispanic Asian, pct non-Hispanic Native American, pct other/multi.
2. **Inequity composite** — mean of five within-urbanicity-stratified z-scores (v2 §2):
   - Poverty rate (ACS B17001)
   - Food access (USDA Food Access Research Atlas: pct population with limited supermarket access at 1- or 10-mile threshold, max)
   - Housing instability (ACS B25070 rent burden ≥50% income + B25003 renter rate, averaged into single raw composite)
   - School resources (NCES F-33 enrollment-weighted log per-pupil expenditure at county level, sign-flipped)
   - Health access (CHR 2023: % uninsured + PCP rate per 100k, combined so low access = high inequity)
3. **Historical mechanism markers**: HOLC redlining grade (Mapping Inequality, urban-only); sundown town status (Loewen database); Voting Rights Act preclearance status (pre-2013); reservation status.
4. **Geographic-type indicator** (categorical): urban tract / suburban tract / rural county / reservation.

### Measured variables — socioeconomic control covariates (added v2 §3)
1. median_hh_income (ACS B19013)
2. pct_HS_terminal (ACS B15003 — sum of HS diploma + GED divided by 25+ population)
3. pct_bachelors_plus (ACS B15003 — sum of Bachelor's through Doctorate divided by 25+ population)
4. pct_employed_civilian_LF (ACS B23025 — civilian employed labor force divided by 16+ population)
5. pct_family_HH (ACS B11001 — family households divided by total households)
6. pct_working_age (ACS B01001 — age 18–64 divided by total population)

### Indices
Composite inequity index — mean of 5 within-urbanicity-stratified z-scores (see §2 of design document). High inequity: composite z ≥ +0.5. Low inequity: composite z ≤ −0.25. Moderate: between −0.25 and +0.5.

---

## Analysis Plan

### Statistical models
Hierarchical Bayesian negative-binomial regression with partial pooling. Model spec (v2 §8):

```
gun_violence_rate[unit] ~ Negative-Binomial(mean[unit], dispersion[unit])
log(mean[unit]) = 
    intercept
    + cell_type_effect[cell_type[unit]]
    + race_effect[race_composition[unit]]
    + inequity_effect[inequity_features[unit]]
    + race_inequity_interaction[race_composition[unit], inequity_features[unit]]
    + historical_mechanism_effect[historical_markers[unit]]
    + geographic_type_inequity_interaction[geo_type[unit], inequity_features[unit]]
    + income_effect[median_hh_income[unit]]
    + education_effect[pct_hs_terminal[unit], pct_bachelors_plus[unit]]
    + employment_effect[pct_employed_civilian_LF[unit]]
    + household_structure_effect[pct_family_HH[unit]]
    + age_structure_effect[pct_working_age[unit]]
    + reporting_rate_adjustment[geo_type[unit]]
    + log(population[unit])    // exposure offset
```

Priors:
- Cell-type effects: hierarchical normal with shrinkage to overall mean
- Race effects: hierarchical normal
- Inequity effects: weakly informative normal centered on direction from existing literature
- Interactions: tighter shrinkage (regularizing prior to avoid overfitting)
- Reporting-rate adjustment: informed prior based on validation literature (urban 1.0, suburban 1.10–1.20, rural-with-media 1.20–1.40, rural-without 1.30–1.60, reservation 1.40–1.80)
- Socioeconomic covariates: weakly informative normal centered at zero, hierarchical shrinkage

Inference via Stan (HMC) or PyMC. Multiple chains, R-hat ≤ 1.05 convergence threshold, ESS_bulk ≥ 1000 per parameter, posterior predictive checks per Gelman et al. 2013.

### Transformations
- `log(population)` as offset for exposure (rate-per-100k interpretation)
- `log(per_pupil_expenditure)` for school dim (corrects right-skew distribution, fixes raw-PPE near-zero discrimination)
- Within-urbanicity-stratified z-scores for all 5 inequity dims (addresses density-dilution issue where rural inequity signals get averaged across large geographic units)

### Inference criteria (pre-registered)
Per-hypothesis falsification criteria (see Hypotheses section above):
- H_INEQUITY supported if race adds ≥15% additional variance beyond inequity
- H_RACE_PURE supported if race adds beyond inequity AND <5% threshold not met
- H_INTERACTION supported if race × inequity adds ≥3% additional variance
- H_HISTORICAL_MECHANISM supported if historical markers add ≥5% additional variance
- H_GEOGRAPHIC_MECHANISM supported if geo-type × inequity interactions add ≥2% additional variance consistently

Each hypothesis disposition: SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE. Reporting stratified by §7 power tier — strong-claim language reserved for Tier 1 cells, moderate-claim for Tier 2, hypothesis-generating for Tier 3.

### Data exclusion
Pre-registered exclusions:
- Census tracts with population < 1,500 (excludes extreme small-cell noise)
- Rural counties with population < 3,000 (same reasoning)
- Reservations with population < 1,000 unless aggregated
- Cells with inequity composite between −0.25 and +0.5 (Moderate tier, excluded from primary high/low comparisons)
- Police-involved shootings, accidental shootings (excluded from primary outcome by component definition)

No post-hoc exclusions based on outcome inspection. Any exclusion not in the above list is flagged as post-hoc in the manuscript.

### Missing data
- ACS missingness: multiple imputation (m=20) using `mice` or equivalent for missing socioeconomic covariates; missing-not-at-random sensitivity analyses for variables with >20% missingness
- WISQARS suppressed cells (1–9 deaths): treated as Truncated-Poisson missing with reporting-rate-prior carrying the uncertainty (the model handles small-count suppression natively via the negative-binomial likelihood)
- Outcome missingness (unit with no WISQARS or GVA record): listwise exclusion if all three outcome components missing; otherwise component-wise pooling

### Exploratory analyses (clearly demarcated as not pre-registered)
The following are exploratory and will be reported separately from the pre-registered tests:
- Post-hoc inequity-feature interactions beyond race × inequity
- Cell-specific findings beyond the §6 pre-registered hypotheses
- Year-by-year temporal trends within the 2019–2023 window
- Cross-validation of GVA non-fatal records against WISQARS-derived rates (calibration check)
- Findings stratified by sub-region or specific city

---

## Other Information

### Methodology corpus integration
This study serves as the sixth substrate for the locked methodology corpus (Paper 6, at `C:/Users/Nate/OneDrive/Documents/methodology/`, locked 2026-05-12): "noise is misclassified structure" framework demonstrated across mathematics (Collatz), sports (NBA Projections), options (a_final SP500), cancer genomics (CancerResearch Paper 1+2), MOFA-FLEX niche (Paper 3, FALSIFIED), and now gun violence cross-geography. The decoupled-cells design (sampling where features vary independently) is a methodological contribution specific to this substrate that may transfer back to other corpus members.

### Provenance trail for v2 design revisions
The v2 design differs from v1 in §2 (inequity composite), §3 (CEM replaced by covariate adjustment), §4 (non-fatal scope clarification), §5 (socioeconomic covariates added), §7 (RW-HI tier demotion), §8 (model expanded), §9 (new threat added). Each revision was triggered by pre-registration data verification (cell availability + CEM yield testing) and is documented with the underlying data file in `D:/Gun Violence/notes/pre_reg_redline.md`. All revisions were made BEFORE outcome data inspection. See pre_reg_redline.md for the verbatim before/after of each affected section.
