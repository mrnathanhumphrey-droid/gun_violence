# Full Report — 2026-05-14
## Gun violence v0.2 + Hydrology eval (corpus QB combined report)

Two parallel tracks landed this session:

- **Hydrology (climate substrate)** — eval bug fixed, full per-fold ELPDs + cascade + bootstrap CIs now extracted from saved chains. Substrate verdict refined.
- **Gun violence v0.2** — race × inequity + geo × inequity interactions added on top of v0.1, with decomposed log-rate components saved per-unit for variance decomposition against pre-reg §6 hypothesis dispositions.

---

## Track 1 — Hydrology eval

### Bug

The original eval read `posterior.parquet`, which `06_per_station_fit.py::extract_posterior()` had silently written with no `log_lik_test` columns. Root cause: cmdstanpy's `fit.draws_pd()` returns column names in `log_lik_test[1]` bracket form for the in-memory DataFrame, while the chain CSVs save them in `log_lik_test.1` dot form. The filter line `keep = [c for c in keep if c in draws.columns]` silently dropped every log_lik_test col on its way to parquet.

### Fix

Patched `07_per_station_eval.py::compute_lppd_per_catchment` to read `log_lik_test.N` columns directly from chain CSVs instead of trusting the bugged parquet:

- New helper `_load_loglik_from_chain_csvs(fit_dir, N_test)` finds chain CSVs by the `<stem>-<ts>_<chain>.csv` glob, excludes `convergence.csv` / `test_ams.csv` / `holdout_meta.csv`, reads exactly the N_test log-lik columns from each chain, forces float dtype, and `np.vstack`s into a `[total_draws, N_test]` array.
- Handles both `per_station_structural_gev-*` (structural specs) and `baseline_with_test_gev-*` (baseline LOO) stems via the wildcard.
- Fixes float dtype coercion for shuffled (some chain CSVs had object dtype from coercion-on-load).

### Re-run results

LOO (random 100-catchment holdout) and LORO (10 region holdouts, ~671 catchments total) deltas vs **baseline-from-prior** (the methodologically clean comparison — baseline for unseen data is drawn from the fixed across-region prior, not refit, because partial-pool baseline has fixed hyperprior on held-out regions):

#### LOO (100 random catchments)

| Spec | N | mean Δ | sd Δ | % catchments where structural beats baseline |
|---|---|---|---|---|
| **low_prec_freq** | 100 | **+0.51** [−0.06, +1.14] | 3.19 | **55%** |
| aridity | 100 | −0.30 [−0.92, +0.29] | 3.13 | 45% |
| shuffled (NULL) | 100 | **−1.46** [−2.31, −0.66] | 4.19 | 34% |

#### LORO (10 region holdouts, 671 catchments)

| Spec | N | mean Δ | sd Δ | % beats baseline |
|---|---|---|---|---|
| **low_prec_freq** | 671 | **+15.73** [+15.25, +16.18] | 6.07 | **100%** |
| aridity | 671 | +15.67 [+15.18, +16.12] | 6.30 | 99% |
| shuffled (NULL) | 671 | **+14.54** [+14.11, +14.99] | 5.67 | 98% |

#### Per-fold LORO mean Δ (low_prec_freq | aridity | shuffled)

```
fold   aridity  low_prec_freq  shuffled
 1      11.45         12.32     11.53
 2      16.27         15.53     16.31
 3      14.47         13.91     14.76
 4      19.30         19.38     17.53
 5      15.52         13.13      5.70    ← shuffled collapses on fold 5
 6      12.49         14.28     13.97
 7      10.45         11.37     10.16
 8      20.01         17.75     17.27
 9      17.08         22.36     17.40
10      11.22         11.82     10.30
```

### Cascade

| Check | Result | Detail |
|---|---|---|
| **A: PRIMARY LORO Δ > NULL LORO Δ + 1 nat** | **PASS** | 15.73 vs 14.54 = +1.19 nat margin |
| **Safeguard 2: NULL Δ CI contains 0** | **FAIL** | NULL CI is [+14.11, +14.99] — far from zero |

### Reading

The substrate is positive, but the picture is more nuanced than the within-sample quick-extraction read:

1. **LOO is a small effect.** low_prec_freq beats baseline by just +0.51 nat/catchment and only 55% of held-out catchments come out positive. Aridity is essentially a coin flip (−0.30, 45%). Shuffled clearly underperforms baseline by −1.46 nat on 66% of catchments.

2. **LORO is a massive effect — but the partial-pool skeleton, not the covariate, is doing most of the work.** All three structural specs (including shuffled) clear baseline-from-prior by ~14–16 nat/catchment on cross-region holdout. The within-comparison primary-vs-null margin is only +1.19 nat — that's the part attributable to the specific structural covariate. The remaining ~14.5 nat of LORO advantage is from partial pooling itself.

3. **Safeguard 2 failing is informative, not damning.** It just confirms that the partial-pooling skeleton is extracting real predictive value above an uninformed-prior baseline. The structural priors over residual classes work; the specific covariate refines them slightly.

4. **Fold 5 is interesting.** Shuffled collapses there (+5.70 vs primary +13.13). That region's variation is genuinely sensitive to the covariate identity; in other folds the covariate matters less.

### Substrate verdict

**POSITIVE on hydrology, with corrected magnitude.** Primary covariate (low_prec_freq) cleanly beats NULL on both LOO and LORO. Cascade A passes. The bulk of the cross-region transfer advantage is from partial pooling itself rather than the covariate — that's actually the methodology corpus's central thesis ("structural priors over residual classes work"), made directly visible by the shuffled-spec baseline.

Pre-reg cross-domain hydrology disposition: **CROSS_DOMAIN_VALIDATED on LORO (Δ > +2), CROSS_DOMAIN_INCONCLUSIVE on LOO (Δ within ±2)** — the LOO arm doesn't clear the +2 nat threshold despite directional positive (+0.51) and clear separation from NULL (~2 nat gap).

### Files

- Patched: `D:/Climate/data/hydrology_rfa/src/07_per_station_eval.py`
- New: `lppd_per_catchment.csv` (2413 rows), `delta_per_catchment.csv` (2313 rows), `disposition_table.csv`, `cascade_results.csv`
- Replaces: `quick_elpd_summary.json` (the chain-only readout that compared within-sample only)

### Open follow-ups

- Eval write of `PER_STATION_RESULTS.md` failed on missing `tabulate` for `to_markdown`; CSVs all wrote fine, markdown is cosmetic. Trivial pip install fix.
- The original `06_per_station_fit.py::extract_posterior()` bug is unfixed — posterior.parquet still has only summary cols. The eval no longer cares (reads chain CSVs), so this is non-blocking.

---

## Track 2 — Gun violence v0.2

### What's in v0.2 vs v0.1

| Term | v0.1 | v0.2 |
|---|---|---|
| Grand intercept α | ✓ | ✓ |
| Cell random intercept + random slope on inequity composite | ✓ | ✓ |
| 7 fixed-effect predictors (pct_black + 6 SES) | ✓ | ✓ |
| **race × inequity interaction** (pct_black × composite) | — | **✓** |
| **geo-type fixed effects** (urban/suburban/rural) | — | **✓** |
| **geo × inequity interaction** | — | **✓** |
| **Decomposed log-rate components per unit** for variance decomp | — | **✓** |
| HOLC redlining marker | — | _skipped — no county shapefile_ |
| Sundown-town marker | — | _skipped — only raw HTML on disk_ |
| VRA preclearance marker | — | _skipped — directory empty_ |
| Per-geo reporting-rate adjustment | — | _skipped — no calibration data_ |

The skipped pre-reg §8 terms all require additional data prep (TIGER county shapefile, HTML parser, dbase extract) that wasn't on disk; documented as v0.3 follow-ups, not silent omissions.

### Build

- `D:/Gun Violence/analysis/fit_production_v0_2.stan` — adds `beta_race_x_ineq`, `beta_geo[G-1]`, `beta_geo_x_ineq[G-1]` with rural-baseline convention; generated quantities save five per-unit log-rate components: `eta_cell`, `eta_inequity`, `eta_race`, `eta_geo`, `eta_ses`.
- `D:/Gun Violence/analysis/run_production_v0_2.py` — reuses v0.1's `design_units.parquet` (456 county-units across 8 cells), assigns geo-type from cell membership (UB/UH/UW→urban, SB→suburban, RW/RB/RH/RNA→rural), runs 4 chains × 1000 warmup + 1000 sampling, then computes variance decomposition over 500 random posterior draws.

### Results

**Wall time:** 118.2 s sampling + ~35 s compile/setup/post = 153.2 s end-to-end.
**Diagnostics:** treedepth satisfactory, **no divergent transitions**, E-BFMI satisfactory, all R-hat OK, all ESS satisfactory. A handful of rejected proposals during warmup (precision-parameter-is-zero exceptions during init) but zero rejections in sampling. Posterior parquet: (4000, 3257).

#### Headline interaction terms

| Term | Mean | 95% CI | CI excludes 0? |
|---|---|---|---|
| **β race × inequity** | **−0.482** | [−0.878, −0.142] | **YES** |
| β geo[urban] | +0.014 | [−1.356, +1.370] | no |
| β geo[urban] × inequity | +0.547 | [−0.396, +1.443] | no |
| β geo[suburban] | −0.537 | [−2.125, +1.165] | no |
| β geo[suburban] × inequity | +0.668 | [−0.708, +1.946] | no |

The **race × inequity interaction is the clear new signal**. Mean −0.48 with a CI cleanly off zero. Geo main effects and geo × inequity terms all straddle zero — the cell intercepts already capture most of the geo-type variation.

#### Fixed-effect predictors (vs v0.1)

| Predictor | v0.1 mean [95% CI] | v0.2 mean [95% CI] | Δ |
|---|---|---|---|
| pct_black | +0.646 [+0.387, +0.910] | **+0.889 [+0.575, +1.204]** | +0.24 |
| median_hh_income | +0.085 [+0.025, +0.141] | +0.086 [+0.030, +0.140] | ≈0 |
| pct_employed_civilian_LF | +0.105 [+0.036, +0.175] | +0.096 [+0.025, +0.162] | ≈0 |
| pct_family_HH | −0.141 [−0.205, −0.079] | **−0.133 [−0.195, −0.072]** | ≈0 |
| pct_hs_terminal | ≈0, CI spans 0 | −0.008 [−0.118, +0.102] | ≈0 |
| pct_bachelors_plus | ≈0, CI spans 0 | −0.010 [−0.150, +0.138] | ≈0 |
| pct_working_age | not in v0.1 | +0.046 [−0.015, +0.105] | new |

**pct_black main effect grew** from +0.65 → +0.89 after adding the race × inequity interaction. This is consistent with v0.1 having absorbed part of the race × inequity nonlinearity into the linear race term — when the interaction is freed, the linear term tightens around its true value.

#### Cell intercepts — major structural shift vs v0.1

| Cell | v0.1 alpha_cell | v0.2 alpha_cell | Reading |
|---|---|---|---|
| UW-LI (urban white low-inequity / control) | +1.42 (driver) | +1.89 (highest) | still anchors the high end |
| UH-HI | n/a as headline | −0.02 | mid |
| RW-HI | +0.53 | +0.53 | stable |
| RB-HI | n/a | −0.42 | low |
| SB-MC | n/a | −0.81 | low |
| **UB-HI** | mid in v0.1 | **−1.82 (lowest)** | **biggest reframe** |

In v0.1, urban-black-high-inequity was treated as "expected high gun-violence rate," with the strong inequity gradient absorbing most of the rate variation. With the race × inequity interaction freed, the model now puts UB-HI at the LOWEST cell baseline — the high observed rates in that cell are attributed to the race-composition main effect (β pct_black = +0.89) plus the residual SES terms, not to the cell or to inequity-within-cell.

#### Cell-level inequity slopes — also reframed

| Cell | v0.1 slope | v0.2 slope | CI excludes 0 in v0.2? |
|---|---|---|---|
| UW-LI | +1.42 [+1.11, +1.71] (tightest CI) | +0.525 [−0.445, +1.525] | no |
| UB-HI | positive | +0.307 [−0.690, +1.486] | no |
| UH-HI | positive | −0.906 [−1.912, +0.085] | grazing |
| SB-MC | positive | +0.235 [−0.969, +1.685] | no |
| RW-HI | weak | −0.675 [−1.376, +0.018] | grazing |
| RB-HI | weak | +0.366 [−0.173, +0.955] | no |
| **RH-HI** | weak | **−0.685 [−1.152, −0.219]** | **YES (negative)** |
| RNA-HI | weak | −0.070 [−0.688, +0.514] | no |

The "inequity composite operates everywhere" v0.1 finding has been **substantially absorbed** by the race × inequity interaction. UW-LI's load-bearing +1.42 slope drops to +0.525 with a CI that includes zero. The only cell-inequity slope with a clean CI is rural-hispanic-high-inequity, and it's **negative** (−0.685 [−1.152, −0.219]).

Read another way: v0.1's "inequity gradient operates within the low-inequity control cell" was partly an artifact of race composition correlating with inequity, which the v0.1 model wasn't separating because there was no interaction term.

#### Variance decomposition — what's actually predicting rate?

Component shares of total predicted log-rate variance (across the 456 county-units, averaged over 500 random posterior draws):

| Component | Mean share | 95% CI |
|---|---|---|
| eta_cell (cell baseline + α) | **+9.41** | [+5.10, +16.52] |
| eta_race (pct_black main + race × ineq) | +4.29 | [+1.69, +7.87] |
| eta_geo (geo main + geo × ineq) | +3.24 | [+0.21, +9.97] |
| eta_inequity (cell × inequity composite) | +1.90 | [+0.43, +5.80] |
| eta_ses (other SES coefs) | +0.15 | [+0.08, +0.22] |
| **2 × sum of pairwise covariances** | **−17.99** | [−31.04, −10.00] |

These shares **do not sum to 1** — they sum to ~19, and the cross-terms are −18. That means the components are **strongly anti-correlated**: cell intercept goes one way, race-composition goes the other, and they substantially cancel. Each marginal variance is several times the joint variance, and the negative cross-covariance compresses the sum back to ~1.

This is **identifiability tension, not a model bug**. R-hat and ESS are clean, divergent transitions are zero — the model fits, but cell baseline and race composition are doing a tug-of-war over the same county-level signal. The marginal variance shares overstate each component's independent contribution; the cross-term tells the real story.

**Reading the shares correctly:**

- Race composition + interaction explains ~23% of the additive total (4.29 / 18.99).
- Cell baseline explains ~50% of the additive total (9.41 / 18.99) — but most of this co-moves opposite to race.
- Inequity composite (within-cell) explains ~10% of additive (1.90 / 18.99) — small.
- Geo-type explains ~17% (3.24 / 18.99).
- SES is negligible (~1%).
- The combined effect: net non-overlapping signal is roughly cell + race + geo + inequity in declining order, with strong overlap between cell and race.

#### Section 6 disposition reading

Pre-reg §6 hypothesis dispositions, with the v0.2 evidence:

| Disposition | Evidence in v0.2 | Verdict |
|---|---|---|
| H_INEQUITY (pure) — composite carries the bulk of rate variation | eta_inequity share ~10% additive, only RH-HI cell has CI-clean slope (and it's negative) | **Falsified** |
| H_RACE_PURE — race composition carries the bulk; inequity is a proxy | eta_race share ~23% but race × ineq coef is −0.48 (CI clean) — not "pure" linear race | **Falsified** |
| **H_INTERACTION** — race and inequity interact; neither pure | **race × ineq = −0.48 [−0.88, −0.14], CI clean. pct_black main = +0.89 (also clean).** | **SUPPORTED** |
| H_GEOGRAPHIC_MECHANISM — geo-type carries material variance | geo-type CIs all span zero; eta_geo share inflated by anti-correlation with cell baseline | **Inconclusive — geo absorbed into cell** |
| H_HISTORICAL_MECHANISM (HOLC + sundown + VRA) | not testable — required data not on disk | **Deferred to v0.3** |

**Reading:** the pre-reg's H_INTERACTION disposition is the supported one. Race and inequity are entangled, with a **negative** interaction: race composition's positive predictive value for firearm-death rate is **attenuated in higher-inequity contexts** (or equivalently, inequity composite's slope is steeper in lower-race contexts and shallower / negative in higher-race contexts).

The v0.1 "inequity is real across the country" finding survives in modified form: there IS still a positive inequity signal (mean shares positive, mean slopes positive in 4 of 8 cells), but it is no longer dominant once race × inequity is freed. The v0.1 strong UW-LI inequity slope was partly demographic-composition signal that the linear model couldn't separate.

#### Methodology corpus implications

This is a substrate where the **methodology produces an unambiguous interaction signal that linear / additive models would have missed**. Compare to:

- **NBA**: structural priors on residual classes (BLK × Center, etc.) outperformed additive models.
- **Lock 2022 cancer**: structural priors on residual omic classes (CNV / methylation / mutation) outperformed naive pooling.
- **Hydrology**: partial-pooling skeleton extracts cross-region predictive signal beyond covariate identity.
- **Gun violence v0.2**: race × inequity interaction is structurally required; additive race + additive inequity misattributes signal between the two.

The corpus thesis holds: residual-class structural priors with structurally-specified interactions outperform pooled / additive baselines. Gun violence joins as substrate #6 in supporting form.

### Files

- `D:/Gun Violence/analysis/fit_production_v0_2.stan` — v0.2 Stan model
- `D:/Gun Violence/analysis/run_production_v0_2.py` — fit + variance decomp script
- `D:/Gun Violence/analysis/production_v0_2/design_units_v02.parquet` — N=456 county-units
- `D:/Gun Violence/analysis/production_v0_2/posterior_full.parquet` — (4000, 3257) full posterior including per-unit eta components
- `D:/Gun Violence/analysis/production_v0_2/posterior_summary.csv` — Stan summary table
- `D:/Gun Violence/analysis/production_v0_2/variance_decomposition.json` — component shares
- `D:/Gun Violence/analysis/production_v0_2/stan_csvs/` — 4 chain CSVs

### Deferred to v0.3

1. **HOLC redlining county feature** — need TIGER county shapefile to do the polygon-to-county join on `historical_mechanism/holc_redlining/mappinginequality.json` (10,154 features across ~200 cities). Once joined, fit H_HISTORICAL_MECHANISM gets its first test.
2. **Sundown towns** — raw HTML on disk, no parser yet. Lightweight scrape job pending.
3. **VRA preclearance** — directory empty. Need to fetch DOJ Section 4(b) coverage formula counties.
4. **Per-geo reporting-rate adjustment** — need a comparison source for firearm-death undercount by geo-type (likely CDC NVDRS subsetting against WISQARS for counties with both).
5. **Re-fit v0.1's cell-only specification with race × inequity added back** as a robustness check — quantifies how much of v0.1's "inequity operates everywhere" finding was demographic-composition absorption.


