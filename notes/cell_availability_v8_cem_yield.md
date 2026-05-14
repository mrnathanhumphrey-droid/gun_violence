# Pre-cond (2) — CEM yield test (β@0.5 + §3 working-class profile)

**Locked operationalization:** β within-urbanicity z-scores, mean composite ≥ 0.5.

**§3 working-class profile (5 of 6 dims; pop-stability deferred):**
- Median HH income in [$66,384, $88,051] (30th-65th national pop-weighted percentile)
- pct_HS_terminal ≥ 40%
- pct_bachelors_plus ≤ 30%
- pct_employed_civilian_LF ≥ 55%
- pct_family_HH ≥ 50% (proxy for married + single-parent + multigen)
- pct_working_age (18-64) ≥ 55%

**National match rate:** tracts 2.0%, counties 2.2%

## Cell-level CEM yield

| Cell | §2 est | Pre-CEM | Post-CEM | Retention | §3 expected 40-60% |
|---|---|---|---|---|---|
| UB-HI | 500-1000 | 846 | 2 | 0.2% ⚠ low |
| UH-HI | 500-1000 | 1,830 | 7 | 0.4% ⚠ low |
| UW-LI | 1000+ | 4,600 | 59 | 1.3% ⚠ low |
| SB-MC | 300-500 | 291 | 1 | 0.3% ⚠ low |
| RW-HI | 150-250 | 55 | 0 | 0.0% ⚠ low |
| RB-HI | 60-100 | 51 | 0 | 0.0% ⚠ low |
| RH-HI | 40-60 | 94 | 1 | 1.1% ⚠ low |
| RNA-HI | 20-30 (proxy) | 12 | 0 | 0.0% ⚠ low |

## Power tier reassignment (post-CEM)

| Cell | Post-CEM | Tier (§7 cutoffs: T1≥120, T2 25-100, T3 <25) |
|---|---|---|
| UB-HI | 2 | **unviable** |
| UH-HI | 7 | **unviable** |
| UW-LI | 59 | Tier 2 |
| SB-MC | 1 | **unviable** |
| RW-HI | 0 | **unviable** |
| RB-HI | 0 | **unviable** |
| RH-HI | 1 | **unviable** |
| RNA-HI | 0 | **unviable** |

## Caveats

- Population-stability dim (§3.6) deferred — would require older ACS vintage to compute % change.
- HH structure dim uses B11001 pct_family_HH as proxy for married + single-parent + multigen ≥ 50%.
- pct_nhw_approx is conservative under-estimate (subtracts all Hispanic from white-alone, not B03002 cross-tab).
- Retention >60% suggests profile is too permissive for that cell (mostly already working-class). Retention <40% suggests the cell composition diverges substantially from working-class profile.