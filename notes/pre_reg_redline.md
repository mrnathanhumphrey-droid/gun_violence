# Pre-registration redline — `gun_violence_research_design.pdf` v1 → v2

**Source:** `D:/Gun Violence/notes/gun_violence_research_design.pdf` (PDF created 2026-05-13 00:51 UTC, iOS Quartz PDFContext)

**Date of revisions:** 2026-05-13

**Status:** Pre-OSF-lock. All revisions below were made BEFORE outcome data was inspected (pre-cond 3 satisfied — only metadata-level row counts seen on `psx4-wq38` and GVA mass-shooting subset; no rates, no spatial joins, no cell-level outcome data).

**Trigger:** pre-cond (1) cell-availability + pre-cond (2) CEM-yield testing revealed two structural issues in v1's §2 and §3 operationalizations. Revisions adapt the spec to match achievable data structure while preserving the locked decision rules in §6 and the power-stratified framework in §7.

**Provenance of each revision:**
- §2 changes: `notes/cell_availability_v7_2x2.md` (locked β@0.5 after 2×2 α/β × threshold sweep)
- §3 changes: `notes/cell_availability_v8_cem_yield.md` + `cell_availability_v8b_cem_proper.md` (CEM yields <2% under strict-AND; only 1 of 729 bin tuples shared across all 8 cells under CEM-proper)
- §5 + §8 additions: derive from §3 reframe

---

## §2 — Cell definitions (REVISE)

### What changes
- Inequity composite expands from 4 dims to **5 dims** (adds **health access** via CHR % uninsured + PCP rate per 100k; school dim uses log-transformed PPE to fix near-zero discrimination in raw $/pupil)
- Standardization changes from "z-score against pooled distribution" to **within-urbanicity stratification** (β: rural counties z-scored against rural counties only; urban tracts against urban tracts only)
- Threshold changes from "z ≥ +1.0 across at least 3 of 4 dimensions" to **"mean composite z ≥ +0.5" / "mean composite z ≤ −0.25"** (preserves the 2:1 ratio between high and low thresholds; mean-composite was tested against per-dim conformance rules and is the cleanest single-statistic operationalization)
- Cell-size estimates **revised downward** to match what the locked operationalization actually produces

### v1 (original)
> **Cell inclusion criteria**
>
> Inequity tier is defined by composite z-score across four dimensions:
>
> - Poverty rate (ACS B17001)
> - Food access (USDA Food Access Research Atlas — low-income low-access status)
> - School resource ratio (NCES per-pupil expenditure, student-teacher ratio at district level mapped to tract/county)
> - Housing instability (ACS B25070 rent burden, B25003 owner/renter, eviction rate where available)
>
> High inequity: composite z-score ≥ +1.0 across at least 3 of 4 dimensions.
> Low inequity: composite z-score ≤ −0.5 across at least 3 of 4 dimensions.
> Moderate (excluded from primary analysis): composite z-score between −0.5 and +1.0.

### v2 (replacement)
> **Cell inclusion criteria**
>
> Inequity tier is defined by a mean composite z-score across five standardized dimensions:
>
> - **Poverty rate** (ACS B17001 — pct below federal poverty line)
> - **Food access** (USDA Food Access Research Atlas — pct of population with low supermarket access at 1- or 10-mile threshold, taking the max for rural-sensitivity)
> - **Housing instability** (ACS B25070 rent burden ≥50% income + B25003 renter rate, averaged into a single raw composite)
> - **School resources** (NCES F-33 enrollment-weighted log per-pupil expenditure at county level, sign-flipped so low PPE = high inequity)
> - **Health access** (County Health Rankings 2023 % uninsured + Primary Care Physicians rate per 100k, combined so high uninsured + low PCP = high inequity)
>
> Each dimension is standardized **within urbanicity stratum** (rural / suburban / urban, classified by tract-count per parent county at boundaries 30 and 100). Within-stratum standardization addresses the structural density-dilution problem whereby rural inequity signals get averaged across large geographic units and lose discriminative power when pooled with urban distributions.
>
> Composite z-score = mean of the 5 within-stratum z-scores.
>
> **High inequity:** composite z ≥ **+0.5** (within-stratum).
> **Low inequity:** composite z ≤ **−0.25** (within-stratum; preserves v1's 2:1 ratio between high and low thresholds).
> **Moderate (excluded from primary analysis):** composite z between −0.25 and +0.5.

### v1 cell-size estimates
| Cell | v1 estimate |
|---|---|
| UB-HI | 500–1000 |
| UH-HI | 500–1000 |
| UW-LI | 1000+ |
| SB-MC | 300–500 |
| RW-HI | 150–250 |
| RB-HI | 60–100 |
| RH-HI | 40–60 |
| RNA-HI | 20–30 reservations |

### v2 cell-size estimates (empirical, under locked operationalization)
| Cell | v2 actual | Notes |
|---|---|---|
| UB-HI | **846** | within v1's 500–1000 range |
| UH-HI | **1,830** | exceeds v1 upper bound |
| UW-LI | **4,600** | exceeds v1 1000+ floor |
| SB-MC | **291** | slightly below v1's 300 lower bound; effectively in range |
| RW-HI | **55** | well below v1's 150–250 |
| RB-HI | **51** | slightly below v1's 60–100 |
| RH-HI | **94** | exceeds v1's 40–60 |
| RNA-HI | **12** | well below v1's 20–30 (proxy: AIAN-majority counties; true reservation-level analysis requires AIANNH spatial join, deferred) |

Smaller rural cells reflect a structural finding: rural inequity distributions are intrinsically more compressed than urban ones. The most inequitable rural county is only ~0.5–1.0 SD above the rural mean. This is not a measurement artifact and applies regardless of threshold choice or pop-weighting.

---

## §3 — Working-class American matching profile (REPLACE ENTIRELY)

### What changes
v1's §3 specified Coarsened Exact Matching to a fixed "working-class American" profile (income 30–65th percentile + education + LF + HH structure + age + pop stability). Pre-cond (2) testing revealed this approach is structurally incompatible with §2's high-inequity cells:
- **Strict-AND interpretation** of the §3 thresholds: <2% national retention, 0–7 units post-CEM per high-inequity cell
- **CEM-proper interpretation** (3 bins per dim, retain units in shared bin tuples across all 8 cells): only **1 of 729 possible 6-dim bin tuples** is shared across all cells; UW-LI control cell evaporates to 11 of 4,600 (0.2% retention)

The mutual incompatibility is structural, not algorithmic: §2 high-inequity cells are **definitionally below-average on income, education, LF, family-HH**, while a working-class target sits at the median. CEM with a fixed target removes by design the cells the study exists to study.

### v1 (original §3 — title + purpose)
> **§3. Working-Class American matching profile**
>
> Cells matched on the following dimensions to ensure cross-cell comparability on baseline characteristics that aren't the inequity features being tested.
>
> Matching dimensions: (1) Household income 30th–65th national percentile; (2) Education distribution; (3) Labor force participation; (4) Household structure; (5) Age structure; (6) Stable population.
>
> Matching algorithm: Coarsened Exact Matching (CEM).
>
> Expected match rates: 40–60% retention per cell.

### v2 (replacement §3 — model-based socioeconomic adjustment)
> **§3. Socioeconomic covariate adjustment (replaces v1 matching)**
>
> Cells are NOT additionally filtered to a fixed "working-class" profile. Pre-registration verification (see `cell_availability_v8b_cem_proper.md`) found that high-inequity cells by construction occupy distinct regions of the 6-dimensional socioeconomic space relative to low-inequity control cells (UW-LI), leaving essentially no Coarsened Exact Matching shared support (1 of 729 bin tuples across all 8 cells; UW-LI retention 0.2%). Forcing a single-target match would remove the cells the study exists to compare.
>
> The original §3 instinct — controlling for socioeconomic confounders that aren't the inequity features being tested — is preserved through **model-based covariate adjustment** in the §8 hierarchical Bayesian model:
>
> - **median_hh_income** (ACS B19013)
> - **pct_hs_terminal** (ACS B15003, sum of HS diploma + GED as terminal credentials, divided by 25+ population)
> - **pct_bachelors_plus** (ACS B15003, sum of Bachelor's through Doctorate divided by 25+ population)
> - **pct_employed_civilian_LF** (ACS B23025, civilian employed labor force divided by 16+ population)
> - **pct_family_HH** (ACS B11001, family households divided by total households)
> - **pct_working_age** (ACS B01001, age 18–64 divided by total population)
>
> Each covariate enters the §8 model as a continuous fixed-effect term. The model's hierarchical partial-pooling structure handles within-cell variance; the covariate adjustment handles between-cell baseline socioeconomic differences. This is standard observational-epi practice when matching support is empty (DiPrete & Engelhardt 2004; Cefalu & Dominici 2014).
>
> Population stability (v1 dimension 6) is dropped because (i) it required an older ACS vintage that is not in the data corpus, and (ii) its rationale (filtering rapid demographic transition) is partially served by the within-urbanicity stratification in §2.

---

## §4 — Outcome variable (CLARIFY non-fatal scope)

### What changes
v1's §4 lists "Non-fatal injury by firearm (GVA incident records geocoded to unit)" as a primary outcome component. Pre-registration verification revealed GVA does not expose a "non-fatal injury" report as a discrete pre-built dataset, nor does GVA's collection methodology cover the full US non-fatal firearm injury population (which would require hospital surveillance data — CDC NEISS / HCUP NIS / NEDS — that are out of the data corpus). GVA's tracked incidents are news-mediated and police-report-mediated; routine non-fatal shootings that don't hit local news are systematically under-counted.

The v1 wording "GVA incident records geocoded to unit" is preserved literally; the operational meaning is clarified below.

### v1 (relevant lines from §4)
> Includes:
> - Homicide by firearm (CDC WISQARS underlying cause of death, ICD-10 X93-X95, U01.4)
> - Suicide by firearm (CDC WISQARS, ICD-10 X72-X74, Y22-Y24)
> - Non-fatal injury by firearm (GVA incident records geocoded to unit)

### v2 (revised — same components, operational clarification)
> Includes:
> - **Homicide by firearm** (CDC WISQARS underlying cause of death, ICD-10 X93-X95, U01.4) — scraped from `wisqars.cdc.gov/api/fatal-county` for years 2019–2023, county granularity (see `_scripts/scrape_wisqars.py`).
> - **Suicide by firearm** (CDC WISQARS, ICD-10 X72-X74, Y22-Y24) — same WISQARS scrape, separate intent code.
> - **Non-fatal injury by firearm — GVA incident records geocoded to unit, operational definition: GVA-tracked incident records (the mass-shooting subset published by `dxzys/Gun-Violence-Data`, n ≈ 5,872 incidents 2013–2026 with lat/lon).** This is narrower than the full US non-fatal firearm injury population. GVA's collection is news- and police-report-mediated, which means routine non-fatal shootings outside the mass-shooting category are systematically under-counted. Adding hospital surveillance data (NEISS, HCUP NIS/NEDS) is deferred as a Phase-2 supplement.

### New §4 caveat (add before "Secondary outcomes")
> **Non-fatal coverage caveat (v2):** The non-fatal injury component is operationalized via GVA mass-shooting incident records, which are news-mediated rather than population-comprehensive. The non-fatal arm of the outcome is therefore narrower than v1 implied and is best interpreted as "mass-shooting non-fatal" rather than "all non-fatal firearm injuries." Reporting-rate adjustment factors (§4 Reporting-rate adjustment subsection) apply to the deaths component (WISQARS) where they were originally calibrated; the non-fatal component's selection mechanism is a separate confound that should be addressed in §9 Threat 1 (Reporting-rate adjustment mis-specification) and ideally in a sensitivity analysis that reports findings with vs. without the non-fatal arm.

### §9 Threat 1 — sub-bullet addition
> **(d) Non-fatal-arm selection (new v2):** GVA's news-mediated collection mechanism means non-fatal incidents in cells with weaker local media coverage (rural, smaller cities) are under-represented relative to high-media cells. Sensitivity analysis with non-fatal component dropped reports the deaths-only findings as the robust floor; the deaths+non-fatal findings as the spec-faithful primary; large divergence between these flags the selection mechanism as load-bearing.

---

## §5 — Independent variables (ADD socioeconomic covariate block)

After the existing "Inequity features (separated, not composite, for analysis)" subsection, add:

> **Socioeconomic covariates (added in v2 for model-based adjustment per revised §3):**
>
> - median_hh_income (ACS B19013_001E)
> - pct_hs_terminal (derived from ACS B15003)
> - pct_bachelors_plus (derived from ACS B15003)
> - pct_employed_civilian_LF (derived from ACS B23025)
> - pct_family_HH (derived from ACS B11001)
> - pct_working_age (derived from ACS B01001)

---

## §7 — Power-stratified claim framework (REVISE RW-HI tier; reaffirm others)

### What changes
- **Tier-1 / Tier-2 cutoffs unchanged** (Tier 1 post-CEM ≥120; Tier 2 25–100; Tier 3 8–24; <8 unviable)
- Because v2 drops CEM (per §3 revision), "post-CEM" sample sizes become equal to v2 pre-matched cell sizes — there is no second-stage filter
- Only **RW-HI moves from Tier 1 → Tier 2** (55 units, in Tier 2's 25–100 range)
- All other cells stay at their v1 §7 tier assignment

### v1 §7 (relevant sub-bullets)
> Tier 1: Strong claims (well-powered cells)
> Cells: UB-HI, UH-HI, UW-LI, SB-MC, **RW-HI**
> Sample sizes: post-matching ≥120 units per cell

> Tier 2: Moderate claims (adequately-powered cells)
> Cells: RB-HI, RH-HI
> Sample sizes: post-matching 25–100 units per cell

### v2 §7 (revised)
> Tier 1: Strong claims (well-powered cells)
> Cells: UB-HI, UH-HI, UW-LI, SB-MC
> Sample sizes: ≥120 units per cell (no CEM filter; see revised §3)

> Tier 2: Moderate claims (adequately-powered cells)
> Cells: **RW-HI**, RB-HI, RH-HI
> Sample sizes: 25–100 units per cell

> Tier 3: Hypothesis-generating (under-powered cells)
> Cells: RNA-HI
> Sample sizes: 8–24 units

The decoupled-cells test (H_RACE_PURE vs H_INEQUITY) becomes **asymmetric in power**: SB-MC is Tier 1 (291 units) while its decoupled partner RW-HI is Tier 2 (55 units). The asymmetry should be reported in the findings; the rural arm carries Tier 2 confidence even when the urban-suburban arm reaches Tier 1.

---

## §8 — Analytic plan (ADD covariate terms to model spec)

### v1 (relevant model spec)
> ```
> gun_violence_rate[unit] ~ Negative-Binomial(mean[unit], dispersion[unit])
> log(mean[unit]) = 
>     intercept
>     + cell_type_effect[cell_type[unit]]
>     + race_effect[race_composition[unit]]
>     + inequity_effect[inequity_features[unit]]
>     + race_inequity_interaction[race_composition[unit], inequity_features[unit]]
>     + historical_mechanism_effect[historical_markers[unit]]
>     + geographic_type_inequity_interaction[geo_type[unit], inequity_features[unit]]
>     + reporting_rate_adjustment[geo_type[unit]]
>     + log(population[unit])  // exposure offset
> ```

### v2 (replacement model spec — adds socioeconomic covariate block)
> ```
> gun_violence_rate[unit] ~ Negative-Binomial(mean[unit], dispersion[unit])
> log(mean[unit]) = 
>     intercept
>     + cell_type_effect[cell_type[unit]]
>     + race_effect[race_composition[unit]]
>     + inequity_effect[inequity_features[unit]]
>     + race_inequity_interaction[race_composition[unit], inequity_features[unit]]
>     + historical_mechanism_effect[historical_markers[unit]]
>     + geographic_type_inequity_interaction[geo_type[unit], inequity_features[unit]]
>     + income_effect[median_hh_income[unit]]
>     + education_effect[pct_hs_terminal[unit], pct_bachelors_plus[unit]]
>     + employment_effect[pct_employed_civilian_LF[unit]]
>     + household_structure_effect[pct_family_HH[unit]]
>     + age_structure_effect[pct_working_age[unit]]
>     + reporting_rate_adjustment[geo_type[unit]]
>     + log(population[unit])  // exposure offset
> ```

Each covariate effect is given a **weakly-informative normal prior centered at zero** (effects in the −0.5 to +0.5 log-rate range a priori), with hierarchical shrinkage. Convergence diagnostics + posterior predictive checks per v1's specification apply unchanged.

---

## §9 — Threats to validity (ADD new threat from §3 revision)

After "Threat 5: Causal interpretation," add:

> **Threat 5b: Socioeconomic-covariate residual confounding (new in v2)**
>
> v1's §3 used CEM to control for socioeconomic confounders. v2 drops CEM (see §3 revision) and uses model-based covariate adjustment for the 5 socioeconomic variables. Any unmeasured confounder within the income / education / labor force / household structure / age space that correlates with both inequity exposure and gun violence outcome will contaminate the inequity-effect estimate.
>
> Mitigation:
> (a) Sensitivity analysis: refit the §8 model with each socioeconomic covariate individually omitted; report the inequity-effect coefficient stability across these refits. Stable estimates across omissions argue against residual confounding from the omitted covariate; large coefficient swings flag specific covariates as load-bearing for the result.
> (b) Posterior predictive check: simulate gun violence rates per unit from the fitted model and compare against held-out tracts/counties stratified by each covariate quintile. Systematic miscalibration in any quintile flags inadequate adjustment for that covariate.
> (c) The Bayesian framework reports posterior uncertainty over the inequity effects. Wide posteriors are the honest representation of residual-confounding risk; narrow posteriors with unmeasured confounders would be evidence of model over-confidence, which the posterior predictive checks should surface.

---

## §10–§12 (UNCHANGED)

Timeline, methodology corpus integration, and locked-commitments list carry forward verbatim from v1.

---

## Summary of v1 → v2 changes

| Section | Change type | What |
|---|---|---|
| §2 | Revise | 4-dim → 5-dim inequity composite; within-stratum standardization; mean-composite threshold 0.5; revised cell estimates |
| §3 | Replace entirely | Drop CEM matching; add model-based covariate adjustment with 5 SES covariates |
| §4 | Clarify | Non-fatal arm operational definition = GVA mass-shooting subset (news-mediated, narrower than v1 implied); WISQARS scrape for deaths; deferred NEISS/HCUP for full non-fatal |
| §5 | Add | New "Socioeconomic covariates" subsection |
| §7 | Revise | RW-HI: Tier 1 → Tier 2; document asymmetric decoupling-test power |
| §8 | Add | 5 socioeconomic covariate terms in the model spec |
| §9 | Add | New Threat 5b — socioeconomic residual confounding |
| §0, §1, §6, §10, §11, §12 | Unchanged | — |

**Net effect on the study's hypotheses**: H_INEQUITY, H_RACE_PURE, H_INTERACTION, H_HISTORICAL_MECHANISM, H_GEOGRAPHIC_MECHANISM all retain their original falsification criteria from v1 §6. The cells they test on are different in size; the methodology that adjusts for confounders is different in form (model-based, not matching-based); the decision rules are unchanged.
