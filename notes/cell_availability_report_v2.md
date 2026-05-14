# Cell-availability v2 — 3-dim composite (poverty + food access + housing instability)

## Three compositing rules tested

| Rule | Description |
|---|---|
| `lenient_mean_z_ge_1` | composite_mean = mean(z_poverty + z_food + z_housing) / 3 ≥ +1.0 |
| `spec_2_of_3_dims_high` | per-dim z ≥ +1.0 in at least 2 of 3 dims (faithful to §2's 'at least 3 of 4' relaxed to 3 dims) |
| `strict_3_of_3_dims_high` | per-dim z ≥ +1.0 in ALL 3 dims (strictest) |

## Cell counts under each rule vs §2 estimate

| Cell | §2 est | lenient | spec 2/3 | strict 3/3 |
|---|---|---|---|---|
| UB-HI | 500-1000 | 404 | 692 | 45 |
| UH-HI | 500-1000 | 309 | 759 | 9 |
| UW-LI | 1000+ | 3,110 | 4,358 | 749 |
| SB-MC | 300-500 | 505 | 463 | 677 |
| RW-HI | 150-250 | 15 | 35 | 0 |
| RB-HI | 60-100 | 20 | 28 | 1 |
| RH-HI | 40-60 | 61 | 5 | 0 |
| RNA-HI | 20-30 reservations (proxy: AIAN-maj counties) | 5 | 5 | 0 |

## Diagnostic: dim-level z-score distributions

Tract-level (high-inequity-eligible):
- z_poverty:       mean 0.00, sd 1.00, pct≥1: 13.3%
- z_food:          mean -0.00, sd 1.00, pct≥1: 21.1%
- z_housing:       mean 0.00, sd 0.78, pct≥1: 11.1%

County-level:
- z_poverty:       mean -0.00, sd 1.00, pct≥1: 10.8%
- z_food:          mean 0.00, sd 1.00, pct≥1: 14.8%
- z_housing:       mean -0.00, sd 0.80, pct≥1: 10.7%

## Verdict

Compare the three rules' counts to the §2 estimates. Pick the rule whose counts MOST CLOSELY match the §2 expectation — that's the operationalization §2's author had in mind.

Caveats unchanged from v1: pct_nhw_approx is conservative (subtract Hispanic from white-alone); urban/rural via tract-per-county proxy; school-resources dimension still deferred; RNA-HI uses AIAN-majority county proxy, not reservation.
