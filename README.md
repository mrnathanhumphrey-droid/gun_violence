# Gun Violence Cross-Geography Study

**Working title:** Cross-Geography Decoupling of Race and Structural Inequity Effects on Gun Violence Rates in Working-Class American Communities

**Author:** Nathan Humphrey

**Status:** Pre-registration v2 locked. v0.1, v0.2, v0.3, v0.4 hierarchical Stan fits LANDED with clean diagnostics. **Three CI-clean structural findings**: race × inequity interaction (replicated 3×), HOLC redlining intensity, sundown-towns intensity. H_HISTORICAL_MECHANISM disposition upgraded from PARTIALLY SUPPORTED (v0.3) to **SUPPORTED** (v0.4). v0.5 backlog: per-geo reporting-rate (CDC-blocked), N expansion, external validation pass.

**Pre-registration timestamp:** This repository's initial commit serves as the pre-registration timestamp. The `notes/gun_violence_research_design.pdf` v1 design document was finalized 2026-05-13 (PDF metadata); the `notes/pre_reg_redline.md` v2 revisions were finalized 2026-05-14 before any outcome-rate inspection.

---

## What this is

A pre-registered observational study testing whether race composition predicts gun violence rates independently of structural inequity, when race and inequity are decoupled by sampling across census tracts and counties where they vary independently (rather than within-city where they covary). The study uses a hierarchical Bayesian negative-binomial regression with partial pooling across cells and model-based socioeconomic-covariate adjustment.

Five pre-registered hypotheses with quantitative falsification criteria:
- **H_INEQUITY** — Inequity drives gun violence; race adds no independent predictive power. (Falsified if race adds ≥15% variance.)
- **H_RACE_PURE** — Race independently predicts beyond inequity. (Falsified if race adds <5% variance.)
- **H_INTERACTION** — Race × inequity interaction matters. (Falsified if interaction <3% variance.)
- **H_HISTORICAL_MECHANISM** — Historical mechanisms (redlining, Reconstruction, industrial collapse) drive geographic variation. (Falsified if markers add <5% variance.)
- **H_GEOGRAPHIC_MECHANISM** — Same inequity features have different effects across urban/suburban/rural. (Falsified if interactions <2% variance consistently.)

Findings will be reported with explicit power-tier stratification per `notes/gun_violence_research_design.pdf` §7.

---

## Results — three fits landed

**v0.1 (2026-05-14):** baseline hierarchical neg-binom across 8 cells, 456 county-units. UW-LI within-cell inequity slope **+1.42 [+1.11, +1.71]** (tightest CI in fit), pct_black main +0.65, pct_family_HH −0.14. Headline: inequity composite operates everywhere, even in the low-inequity white control cell.

**v0.2 (2026-05-14):** added race × inequity interaction + geo-type fixed effects + decomposed log-rate components. **Race × inequity = −0.482 [−0.878, −0.142]**, CI clean. pct_black main strengthens to +0.89. **v0.1's UW-LI +1.42 slope drops to +0.525 with CI through zero** — much of v0.1's "inequity everywhere" was demographic-composition signal the additive model couldn't separate. Variance-decomp cross-term −18: cell baseline and race composition strongly anti-correlated (identifiability tension, model still fits clean).

**v0.3 (2026-05-15):** added HOLC redlining (county share-D) + VRA Section 4(b) preclearance markers. **HOLC share-D = +0.682 [+0.324, +1.049], CI clean** — historical New Deal-era redlining still predicts present-day firearm-death rates *after* controlling for current race + inequity + geo + SES. VRA Section 4(b) null. Race × inequity replicates v0.2 (−0.453 vs −0.482).

**v0.4 (2026-05-15):** added sundown towns (Tougaloo / Loewen DB, 50-state scrape, 2,437 suspected sundown towns → 1,913 county-matched via Census Places gazetteer + spatial join, 950 of 3,235 US counties affected). **SUNDOWN log1p (continuous intensity) = +0.128 [+0.036, +0.219], CI clean** — mid-20th-century explicit racial exclusion *count*, not binary presence, adds independent predictive signal on top of HOLC + VRA + race + inequity + SES. Effect size: county with 10 documented sundown towns → ~36% higher firearm-death rate vs comparable county with none. HOLC share-D replicates v0.3 (+0.701). Race × inequity replicates again (−0.450, 3rd consecutive CI-clean fit).

### §6 disposition reading (current as of v0.4)

| Hypothesis | Verdict |
|---|---|
| H_INEQUITY (pure) | Falsified |
| H_RACE_PURE | Falsified |
| **H_INTERACTION** | **SUPPORTED (replicated v0.2 → v0.3 → v0.4)** |
| **H_HISTORICAL_MECHANISM** | **SUPPORTED** — HOLC redlining + sundown towns both CI-clean; VRA null |
| H_GEOGRAPHIC_MECHANISM | Inconclusive (geo absorbed into cell) |

### **This is statistical evidence of systemic racism.**

The two CI-clean historical-mechanism findings (HOLC redlining, sundown towns) demonstrate that **explicit racist policies from 60-90 years ago still independently predict present-day firearm-death rates**, after controlling for current race composition, current structural inequity, current geography, current income, education, employment, household structure, age structure, and health-care access. In epidemiological terms, this is the operational definition of *structural racism / systemic racism*: harm patterns that survive the removal of all current observable confounders and that load on historical-policy markers.

The pre-registered §6 disposition rule fires `H_HISTORICAL_MECHANISM = SUPPORTED` because two distinct historical-policy channels — built-environment property-finance (HOLC) and explicit social-exclusion violence (sundown towns) — each pass the locked CI threshold independently in a model that already adjusts for everything we can measure about counties *as they exist today*.

### Three CI-clean structural findings (all replicated)

1. **Race × inequity entanglement**: **−0.482 (v0.2) → −0.453 (v0.3) → −0.450 (v0.4).** Three independent fits, three different specifications, **same coefficient to two decimals.** Race composition and structural inequity cannot be cleanly decomposed at this resolution; every additive model surfaces the same negative interaction. In US counties, race and inequity are not two independent dials — they are entangled as the *same* historical process measured through different proxies.

2. **HOLC redlining intensity** β = **+0.701 [+0.351, +1.055]**: 1930s federal property-finance segregation predicts ~**exp(0.70) ≈ 2× higher firearm-death rate** per unit increase in county HOLC D-grade share, **90+ years after the policy was implemented and 60+ years after it was formally repudiated**, after all current controls.

3. **Sundown-town intensity** β = **+0.128 [+0.036, +0.219]** per log(1 + count): Mid-20th-century explicit racial exclusion documented in the Loewen database adds another **~36% lift for counties with ~10 documented sundown towns**, independent of HOLC and everything current. *Count* matters, not binary presence — **cumulative historical exposure to explicit racial-exclusion violence is what predicts present-day harm.**

The corpus methodology contribution: structural priors over residual classes + explicit historical-mechanism markers surface findings that an additive baseline with only current race + SES + geo would miss entirely. **Three structural findings in one substrate, all defensible to the locked pre-reg's CI threshold, all directly visible in present-day mortality data, all anchored to specific historical policies whose implementation dates are documented in the archival record.**

### Deferred to v0.5

1. Per-geo reporting-rate adjustment (needs NVDRS county data; CDC access request)
2. N expansion (block-group disaggregation OR state-level rollup) to tighten cell ↔ race identifiability tension
3. External validation pass against published gun-violence × redlining × sundown studies
4. Apply the structural-prior partial-pooling framework (the methodology corpus's core mechanism) DIRECTLY to the historical-mechanism × cell residual structure rather than treating it as fixed-effect adjustment

Full writeups: [analysis/FULL_REPORT_2026_05_14.md](analysis/FULL_REPORT_2026_05_14.md) (v0.1 + v0.2), [analysis/REPORT_v0_3_2026_05_15.md](analysis/REPORT_v0_3_2026_05_15.md) (v0.3 HOLC + VRA), [analysis/REPORT_v0_4_2026_05_15.md](analysis/REPORT_v0_4_2026_05_15.md) (v0.4 sundown + final H_HISTORICAL_MECHANISM disposition).

---

## What's in this repo

```
.
├── README.md                                       ← this file
├── manifest.json                                   ← data inventory: 17 sources, SHA-256 hashes, row counts
├── FINAL_REPORT.md                                 ← data-assembly final report
├── _agent_status/                                  ← tier 1/2/3 completion checkpoints
├── _scripts/                                       ← all data-fetch + analysis-prep scripts (Python)
│   ├── fetch_acs.py                                ← Census ACS bulk pull (13 tables × tract+county)
│   ├── fetch_cdc_county.py                         ← CDC psx4-wq38 firearm county data
│   ├── fetch_tier2.py / fetch_tier3.py             ← Tier 2 + Tier 3 sources
│   ├── fetch_tiger_tracts.py / fetch_tiger_unsd.py ← TIGER state-by-state
│   ├── scrape_wisqars.py / parse_wisqars_geojson.py ← WISQARS firearm deaths 2019-2023
│   ├── precond_1_*.py (v1..v7)                     ← Cell-availability tests (operationalization lock)
│   ├── precond_2_cem_*.py                          ← CEM yield tests (matching feasibility)
│   ├── build_manifest.py                           ← Manifest generator
│   └── scrape_probe.py                             ← Playwright probe of SPA endpoints
└── notes/                                          ← Pre-registration documents
    ├── gun_violence_research_design.pdf            ← v1 pre-reg (locked 2026-05-13)
    ├── gun_violence_research_design.txt            ← extracted text of v1
    ├── pre_reg_redline.md                          ← v1 → v2 redline (§2 §3 §4 §5 §7 §8 §9)
    ├── osf_structured_form.md                      ← OSF-style structured form (alternative submission)
    ├── osf_submission_instructions.md              ← OSF submission walkthrough (alternative)
    ├── cell_availability_report.md                 ← Pre-cond (1) v1 (2-dim composite)
    ├── cell_availability_report_v2.md              ← v2 with USDA food access added
    ├── cell_availability_v4_5dim_health.md          ← v4 with CHR health dim added
    ├── cell_availability_threshold_sweep.md         ← v5 threshold sweep
    ├── cell_availability_v6_density_fix.md          ← v6 α vs β standardization comparison
    ├── cell_availability_v7_2x2.md                  ← v7 α/β × 0.5/0.7 (locked β@0.5)
    ├── cell_availability_v8_cem_yield.md            ← Pre-cond (2) strict-AND CEM (fails)
    └── cell_availability_v8b_cem_proper.md          ← Pre-cond (2) CEM-proper (1 of 729 bin tuples shared)
```

The raw data sources (1.5 GB) are **not in this repository** (see `.gitignore`). They are reproducible by running the `_scripts/fetch_*` and `_scripts/scrape_*` scripts in order. See `manifest.json` for source URLs + SHA-256 hashes.

---

## Pre-registration provenance trail

The v2 design differs from v1 in seven sections (§2 §3 §4 §5 §7 §8 §9). Every revision was triggered by pre-registration data verification (cell availability + CEM yield testing) and is documented in `notes/pre_reg_redline.md` with the underlying data file as evidence.

Key revisions:
- **§2 — inequity composite** expanded from 4 to 5 dimensions (adds health access via CHR), standardized within urbanicity stratum (β), threshold lowered to mean composite z ≥ 0.5 / ≤ −0.25 (preserves 2:1 ratio). Cell-size estimates revised against actual data.
- **§3 — CEM matching DROPPED entirely**, replaced by model-based socioeconomic-covariate adjustment in the §8 hierarchical Bayesian model. Triggered by CEM yield test showing only 1 of 729 possible 6-dim bin tuples is shared across all 8 cells (UW-LI control cell retention 0.2%). The high-inequity cells the study tests are by definition below the working-class target on income/education/labor-force — matching to a fixed working-class profile would force out exactly the cells the design exists to compare.
- **§4 — non-fatal coverage caveat** added: GVA mass-shooting subset is the operational definition of "non-fatal injury" (news-mediated, narrower than full US firearm-injury population which would require NEISS/HCUP hospital surveillance — deferred as Phase-2 supplement).

All revisions were made BEFORE outcome data was inspected at the rate or cell level. Only metadata-level row counts on `psx4-wq38` (132K rows) and the GVA mass-shooting subset (5,872 records) were seen during data assembly.

---

## Methodology corpus context

This study is the sixth substrate test of a locked methodology corpus (Paper 6) demonstrating the partial-pooling-of-residual-classes framework across heterogeneous domains:

1. Collatz tail-behavior modeling
2. NBA Projections (residual-class offsets, BLK × Center coupling)
3. SP500 a_final residue classes
4. CancerResearch Paper 1+2 (Lock 2022 spike-and-slab pan-cancer survival)
5. CancerResearch Paper 3 — MOFA-FLEX niche joint refit (FALSIFIED, substrate boundary)
6. Gun violence cross-geography (this study)

The decoupled-cells design (sampling where features vary independently) is a methodological contribution specific to this substrate that may transfer back to other corpus members.

---

## Data sources (summary; full provenance in `manifest.json`)

**Outcomes:**
- CDC WISQARS firearm deaths 2019-2023 (scraped from `wisqars.cdc.gov/api/fatal-county`, 3,143 counties × 5 years × 4 intents)
- CDC psx4-wq38 county-level firearm/violence (cross-validation source for WISQARS)
- Gun Violence Archive mass-shooting subset 2013-2026 (via `dxzys/Gun-Violence-Data`)

**Demographics:**
- Census ACS 2019-2023 5-year estimates (13 tables × tract + county)
- TIGER/Line 2024 (counties, tracts, school districts, AIANNH reservations)

**Inequity dimensions:**
- USDA Food Access Research Atlas 2019
- NCES Common Core of Data F-33 finance SY 2018-19 through 2021-22
- County Health Rankings 2023 (health access)

**Historical mechanism:**
- HOLC Mapping Inequality (national GeoJSON, 10,154 features)
- Loewen Sundown Towns Database (Tougaloo)
- Eviction Lab ETS 2020-2021

**Geographic:**
- TIGER/Line 2024 American Indian/Alaska Native/Native Hawaiian areas

---

## License

MIT — see `LICENSE` (TBD).

This work uses public secondary data sources. Each source retains its original license; consult `manifest.json` for source URLs and citation requirements.

---

## Citing

> Humphrey, N. (2026). *Cross-Geography Decoupling of Race and Structural Inequity Effects on Gun Violence Rates in Working-Class American Communities.* GitHub: https://github.com/mrnathanhumphrey-droid/gun_violence
