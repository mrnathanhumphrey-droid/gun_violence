## Tier 3 — Sundown-Source Replication (Rigby et al. 2025)

**Date:** 2026-05-15
**Source under test:** Rigby et al. 2025, "A national data set of historical
US sundown towns for quantitative analysis," *Scientific Data*, DOI
[10.1038/s41597-024-04330-9](https://doi.org/10.1038/s41597-024-04330-9). Dataset
deposited at OSF: [https://osf.io/fh7r6/](https://osf.io/fh7r6/) (DOI
10.17605/OSF.IO/FH7R6).

**Question.** Does the sundown × firearm coefficient hold when we swap the
v0.4 Tougaloo/Loewen scrape for Rigby's canonical Census-linked dataset?

**Decision rule (locked at v0.5 pre-reg):** sundown_log1p coefficient under
the Rigby source must be within **±0.1** of the v0.4 Tougaloo reference
(+0.128) AND CI clean positive.

### Headline

| Quantity | v0.4 (Tougaloo) | Tier 3 (Rigby 2025) | Δ |
|---|---|---|---|
| sundown_log1p coefficient | **+0.128** [+0.036, +0.219] | **+0.120** [+0.029, +0.216] | **−0.008** |
| race × inequity | −0.450 [−0.803, −0.133] | −0.434 [−0.793, −0.111] | +0.016 |
| HOLC share-D | +0.701 [+0.351, +1.055] | +0.689 [+0.331, +1.052] | −0.012 |

**All three replicate. Sundown coefficient differs from Tougaloo by 0.008
— essentially identical to one decimal place. Far inside the ±0.1
tolerance band. CI clean positive.**

**Verdict: STRONG_REPLICATION (sundown).**

### Why this matters

The Tougaloo/Loewen database is the field's longest-running sundown towns
archive but has a known limitation: it's a community-sourced wiki with
unverified evidence tiers. Rigby et al. 2025 published a new canonical
academic dataset (in Nature *Scientific Data*) intended to supersede
Tougaloo for quantitative work — they recoded confidence tiers (Surely /
Probable / Possible / Unlikely), removed duplicates, and pre-linked every
entry to Census geographies (places, county subdivisions, counties, plus
2020 centroids for unmatched).

By swapping the source and re-running the same v0.4 model, we're asking:
is the +0.128 coefficient an artifact of how Tougaloo coded sundown
status, or is it the underlying mid-20th-century-racial-exclusion signal
that any reasonable measurement would surface?

**Answer: the underlying signal.** Two independently constructed datasets
of mid-20th-century racially-exclusionary places, run through the same
model with the same controls, produce coefficients 0.008 apart.

### Source concordance

Concordance check at the county-unit level (n = 456 county-units in our
design):

|  | Rigby flagged | Rigby not flagged |
|---|---|---|
| **Tougaloo flagged**     | 190 | 11 |
| **Tougaloo not flagged** | 27  | 228 |

- Cohen's-κ-like agreement: 91.7% identical classification on county-unit level
- Pearson r between Tougaloo and Rigby sundown_n: **0.982**
- Tougaloo flagged 11 county-units that Rigby did not (rare-source-only entries)
- Rigby flagged 27 county-units that Tougaloo missed (likely Rigby's
  Census-linkage caught entries Tougaloo's place-name field lost)

US-wide aggregate: Rigby flags 1,084 of 3,235 US counties (33.5%) at the
Surely/Probable/Possible confidence threshold; Tougaloo flagged 950 of
3,235 (29.4%).

### Method

Identical to v0.4 except for the sundown columns. Same v0.1 design units
(N=456 county-units across 8 cells), same 7 SES predictors, same HOLC +
VRA historical-mechanism controls, same v0.4 Stan model
(`fit_production_v0_4.stan`), 4 chains × 1000 warmup × 1000 sampling,
adapt_delta 0.95, seed 20260800.

The only change: where v0.4 fed `sundown_log1p` and `sundown_any` columns
derived from `historical_features_county_v04.parquet` (Tougaloo), Tier 3
feeds `sundown_log1p_rigby` and `sundown_any_rigby` from
`historical_features_county_v06_rigby.parquet` (Rigby).

### Geography pipeline (Rigby → county FIPS)

Rigby's 2,322 confidence-eligible entries (Unlikely excluded) were
resolved to county FIPS via four cases per the `type` column:

| Rigby type | n | Pipeline |
|---|---|---|
| place | 1,927 | matching_cdp → 2024 Census Places gazetteer (state + place_id) → lat/lon → spatial join to TIGER 2024 county polygon |
| county | 204 | matching_county = 5-digit county FIPS, use directly |
| county subdivision | 137 | county_fips = state_fips × 1000 + 3-digit county FIPS, decoded |
| no match (centroid only) | 40 | centroid2020 = "lon, lat" → spatial join to TIGER county |

**Resolved: 2,213 of 2,322 entries (95.3%)**. Unresolved (109) had missing
or unparseable geography fields.

### Diagnostics

All four chains converged cleanly:
- No divergent transitions
- Treedepth satisfactory for all transitions
- E-BFMI satisfactory
- R-hat ≈ 1 for all parameters
- Effective sample size satisfactory

(A handful of "Precision parameter is 0" non-fatal warnings emitted during
warmup — these are HMC's standard initial-exploration messages when the
sampler probes extreme regions; all chains converged and no divergences
post-warmup.)

### What this adds to the v0.4 evidence

The v0.4 result said: a county's *count* of documented sundown towns from
the Tougaloo database predicts present-day firearm-death rate at +0.128
per log(1+count), CI clean positive, after every current control.

Tier 3 says: that result is **not specific to Tougaloo's coding choices**.
Run the same model with an independently constructed academic dataset
that uses different confidence tiers, different linkage methodology, and
catches different individual towns — and the coefficient lands at +0.120,
within 0.008 of Tougaloo's number, CI still clean positive.

That is a 4th axis of validation for the v0.4 finding, complementing the
v0.5 Arm B 5-fold replication (sample axis), the original v0.4 within-fit
diagnostics (model axis), and the v0.4 within-cell replication of race ×
inequity at -0.45 to 2 decimal places (specification axis).

### Files

- `historical_mechanism/sundown_towns_rigby_2025/sundown_linked_to_census.csv` (Rigby raw, 2,347 rows, 1.4 MB, fetched from OSF dhvz8)
- `analysis/build_v06_sundown_rigby.py` (Rigby → county FIPS pipeline)
- `analysis/historical_features_county_v06_rigby.parquet` (county features including both Tougaloo + Rigby variants)
- `analysis/run_tier3_rigby.py` (fit runner)
- `analysis/tier3_rigby_2025/design_units_tier3.parquet` (final design)
- `analysis/tier3_rigby_2025/tier3_summary.json` (key coefficients + CI)

### Citation

> Rigby, D., Esposito, M. H., Lee, H., Van Riper, D. C., Hicken, M. T., & Berrey, S. A. (2025). A national data set of historical US sundown towns for quantitative analysis. *Scientific Data*, 12, 156. https://doi.org/10.1038/s41597-024-04330-9
>
> Rigby, D., Esposito, M. H., Lee, H., Van Riper, D. C., Hicken, M. T., & Berrey, S. A. (2025). *Historical Sundown Towns Linked to US Census Geographies* [Dataset]. OSF. https://doi.org/10.17605/OSF.IO/FH7R6

### Pre-registration provenance

This Tier 3 test was queued (without specific source) in the v0.5
pre-registration locked at commit `b162e71` (2026-05-15) under "Queued
(Tier 3): Bayly 2024 sundown source replication." The author was
mis-attributed as Bayly; the correct authorship is Rigby et al. The
methodological framework — locked threshold ±0.1 around v0.4 reference of
+0.128, CI clean positive — is unchanged from the pre-reg.
