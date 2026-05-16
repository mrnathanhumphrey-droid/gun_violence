# v0.5 Self-Replication Pre-Registration

**Date drafted:** 2026-05-15
**To be locked:** before any new outcome data fetch OR re-fit (target: GitHub commit, public, timestamped)
**Filed alongside:** [notes/pre_reg_redline.md](pre_reg_redline.md) (v1 → v2), [notes/gun_violence_research_design.pdf](gun_violence_research_design.pdf) (v1)
**Tests:** v0.4's three CI-clean structural findings (race × inequity = −0.450, HOLC share-D = +0.701, sundown log1p = +0.128).

---

## 1. Hypothesis

> The three CI-clean structural findings from v0.4 — race × inequity interaction (−0.450), HOLC redlining intensity (+0.701), and sundown-towns intensity (+0.128) — are not sample-specific or time-specific. They replicate (a) on a 2014-2018 outcome window pre-dating the v0.4 sample by one observation period, and (b) on independently-drawn random 80%-subsets of the 456 v0.4 county-units.

If both arms replicate, the v0.4 findings are robust to two independent self-replication axes (time, sample). If either arm fails, the specific failure mode is itself a substrate for investigation (e.g., "race × inequity holds across time but HOLC effect is COVID-era specific" or "all three findings are sample-specific within ±20%").

---

## 2. Arm A — Time-window replication

### Data
- **Outcome:** WISQARS firearm deaths 2014-2018 county-level. Fetched via the same scraper used for 2019-2023 (`_scripts/scrape_wisqars.py`), with `year1=2014 year2=2018 mech=20890`. Same 4 intents (Homicide, Suicide, Unintentional, Legal/War).
- **Exposure:** Same `log(pop_county × 5)` offset, where `pop_county` is the ACS 2019-2023 5-year estimate. **Note:** we knowingly use 2019-2023 population for 2014-2018 deaths because tract-level population stratified by demographics didn't change dramatically. This is a defensible approximation; an alternative (ACS 2014-2018 5-year population) is a v0.6 sensitivity option.
- **All other predictors:** identical to v0.4 (race composition, inequity composite, SES covariates, HOLC, VRA, sundown).

### Model
Identical to v0.4: `fit_production_v0_4.stan` with the new outcome counts.

### Pre-registered constraints
1. No model adjustment based on intermediate Arm A results.
2. Same cell assignments as v0.4 (locked from v0.1 design).
3. Same priors, same chain count (4), same iter count (1000 warmup + 1000 sampling), same seed pattern (use seed 20260601 for Arm A to avoid collision with v0.4's 20260516).
4. Same convergence halt rule (R-hat > 1.05 halts).

### Decision rule

Per the three CI-clean findings of v0.4:

| Coefficient | v0.4 value | Arm A replication "PASS" criterion |
|---|---|---|
| race × inequity | −0.450 [−0.803, −0.133] | mean within ±0.2 of v0.4 AND 95% CI excludes zero (negative) |
| HOLC share-D | +0.701 [+0.351, +1.055] | mean within ±0.3 of v0.4 AND 95% CI excludes zero (positive) |
| sundown log1p | +0.128 [+0.036, +0.219] | mean within ±0.1 of v0.4 AND 95% CI excludes zero (positive) |

Arm A overall verdict:
- **STRONG_REPLICATION** = all 3 PASS
- **PARTIAL_REPLICATION** = 2 of 3 PASS
- **WEAK_REPLICATION** = 1 of 3 PASS
- **REPLICATION_FAILED** = 0 of 3 PASS

---

## 3. Arm B — Random-county 5-fold cross-validation

### Procedure
1. Set RNG seed = 20260602 (locked here; one-time draw, no re-shuffle).
2. Split 456 county-units into 5 disjoint random folds of ~91 units each, stratified by cell to preserve cell representation per fold.
3. For each of fold ∈ {1, 2, 3, 4, 5}: fit v0.4 model on the **other** 4 folds (~365 units). Save posterior summaries.
4. Compare the 3 target coefficient distributions across 5 fold-fits.

### Model
Identical to v0.4. Same priors, same chains, same iters. Each of 5 fold-fits uses seed 20260700 + fold_idx (1..5).

### Pre-registered constraints
1. Cell-stratified 5-fold split is determined ONCE by `set.seed(20260602)` — saved to `analysis/production_v0_5/fold_assignments.csv` before any fold fit runs.
2. No fold re-shuffling based on intermediate results.
3. Same convergence halt per fold.

### Decision rule

Per the three CI-clean findings of v0.4:

| Coefficient | v0.4 value | Arm B replication "PASS" criterion |
|---|---|---|
| race × inequity | −0.450 | ≥ 4 of 5 folds have mean negative AND 95% CI excludes zero |
| HOLC share-D | +0.701 | ≥ 4 of 5 folds have mean positive AND 95% CI excludes zero |
| sundown log1p | +0.128 | ≥ 4 of 5 folds have mean positive AND 95% CI excludes zero |

Arm B overall verdict (same scale as Arm A):
- **STRONG_REPLICATION** = all 3 PASS
- **PARTIAL_REPLICATION** = 2 of 3 PASS
- **WEAK_REPLICATION** = 1 of 3 PASS
- **REPLICATION_FAILED** = 0 of 3 PASS

### Note on 4/5 vs 5/5 threshold

Stricter would be 5/5. Using 4/5 because one fold may legitimately have a noisier subset (e.g., happens to underweight a cell like RNA-HI with only N=10 in v0.4). The 4/5 rule allows for one noisy fold without false-negativing on coefficient stability. This is the only soft constraint in the pre-reg; it's locked here to prevent later softening.

---

## 4. Joint v0.5 disposition

Combined across Arm A + Arm B:

| Joint verdict | Interpretation |
|---|---|
| Arm A STRONG + Arm B STRONG | **Maximum replication: 3 findings hold across time AND random sample subsets** |
| Arm A STRONG + Arm B PARTIAL | Findings time-stable; some sample-specific |
| Arm A PARTIAL + Arm B STRONG | Findings sample-stable; one or more time-window-specific |
| Both PARTIAL | One or more findings is genuinely fragile; identify which |
| Either FAILED | Investigate the specific failure mode as its own substrate |

---

## 5. Pre-registered constraints (locked here)

1. **No model adjustment** between v0.4 and v0.5 — same Stan file, same priors, same predictors.
2. **No data adjustment** beyond the pre-specified outcome time window (Arm A) and the cell-stratified fold split (Arm B).
3. **No "best of N seeds"** — each fit uses the seed specified above. If convergence fails at the locked seed, halt that arm and report.
4. **All Arm B folds run regardless** of any single fold's verdict.
5. **Both Arms run regardless** of each other's outcome.
6. **Decision-rule thresholds locked here** (±0.2 / ±0.3 / ±0.1 for Arm A; 4/5 for Arm B). No post-hoc tuning.

---

## 6. What is reported regardless of outcome

- Total firearm deaths 2014-2018 per cell (Arm A): face-validity check.
- Per-fold cell distribution (Arm B): confirms cell-stratification preserved.
- Convergence diagnostics for Arm A (1 fit) + Arm B (5 fits) = 6 diagnostic reports.
- Three coefficient posteriors per fit: race × inequity, HOLC share-D, sundown log1p.
- For Arm B: distribution of each coefficient across 5 folds (mean, SD, min, max).
- Per-arm verdict + joint v0.5 disposition.

---

## 7. Provenance

This pre-registration is locked at commit SHA: **TBD on GitHub push** (target: `github.com/mrnathanhumphrey-droid/gun_violence` main branch). The GitHub commit timestamp is the methods-section citation for the v0.5 self-replication.

WISQARS 2014-2018 scrape commit timestamp: also recorded post-scrape via the manifest update.

---

## 8. Companion: v0.6 block-group N expansion (separate pre-reg, in flight)

A separate v0.6 pre-registration is in development for the block-group disaggregation arm (N expansion from 456 county-units to ~220K block-groups). The block-group ACS data fetch is in-flight as of 2026-05-15. v0.6 will be its own pre-reg lock because it involves a cell-design architecture change, not just a sample/time replication.
