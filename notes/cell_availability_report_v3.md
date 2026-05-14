# Cell-availability v3 — full 4-dim composite per §2

**Dimensions:** poverty (ACS) + food access (USDA) + housing instability (rent burden + renter rate) + school resources (NCES F-33 PPE, negated).

**F-33 vintage:** SY 2021-22. 3,127 counties with computed enrollment-weighted PPE. District-level F-33 aggregated to county; tract-level uses parent county PPE.

## Cell counts under each rule vs §2 estimate

| Cell | §2 est | **spec 3/4** (faithful) | lenient 2/4 | mean z≥1 |
|---|---|---|---|---|
| UB-HI | 500-1000 | **61** | 717 | 193 |
| UH-HI | 500-1000 | **33** | 828 | 146 |
| UW-LI | 1000+ | **2,076** | 5,615 | 2,787 |
| SB-MC | 300-500 | **667** | 441 | 564 |
| RW-HI | 150-250 | **0** | 36 | 7 |
| RB-HI | 60-100 | **1** | 28 | 9 |
| RH-HI | 40-60 | **0** | 5 | 38 |
| RNA-HI | 20-30 reservations (proxy) | **0** | 6 | 3 |

## Dim-level z distributions (tract / county)

Tract-level:
- z_poverty pct≥1: 13.3%
- z_food pct≥1: 21.1%
- z_housing pct≥1: 11.1%
- z_school pct≥1: 9.7%

County-level:
- z_poverty pct≥1: 10.8%
- z_food pct≥1: 14.8%
- z_housing pct≥1: 10.7%
- z_school pct≥1: 0.8%
