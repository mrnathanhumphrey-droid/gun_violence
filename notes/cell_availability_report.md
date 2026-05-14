# Cell-availability check vs §2 estimates

**Pre-condition (1) of Prompt 1.**

## First-pass operationalizations (caveats)

- Race composition from ACS B02001 + B03003 (note: pct_nhw_approx = pct_white − pct_hispanic; full non-Hispanic-white requires B03002 cross-tab, not pulled).
- Inequity composite: z(poverty_rate) + z(rent_burden_50plus%), divided by 2. **Only 2 of 4 dimensions** — food access (USDA) and school resources (NCES F-33) deferred to second pass.
- Urban/suburban/rural proxy: tracts-per-county (>100 = urban, 30-100 = suburban, <30 = rural). Will be replaced with Census Urban Area spatial join in production.
- Population thresholds: tract ≥1500, rural county ≥3000 per §2.
- RNA-HI tested at COUNTY level (AIAN-majority counties), not reservation. Reservation-level requires AIANNH spatial join + Census reservation-specific tables. RNA-HI count here is **proxy only**.

## Cell counts

| Cell | §2 estimate | Actual (first-pass) | Status |
|---|---|---|---|
| UB-HI (urban, Black-maj ≥60%, high inequity) | 500-1000 | **1,055** | ✓ in range |
| UH-HI (urban, Hispanic-maj ≥60%, high inequity) | 500-1000 | **1,116** | ✓ in range |
| UW-LI (urban, White-maj ≥70%, low inequity) | 1000+ | **3,941** | ✓ in range |
| SB-MC (suburban, Black-maj ≥60%, low-to-mod inequity) | 300-500 | **421** | ✓ in range |
| RW-HI (rural county, White-maj ≥80%, high inequity) | 150-250 | **34** | ⚠ low (34 < 150) |
| RB-HI (rural county, Black-maj ≥50%, high inequity) | 60-100 | **36** | ⚠ low (36 < 60) |
| RH-HI (rural county, Hispanic-maj ≥50%, high inequity) | 40-60 | **84** | ✓ in range |
| RNA-HI (reservation, AIAN-maj ≥40%, high inequity) | 20-30 (reservations) | **7** | ⚠ low (7 < 20) |

## Bottom line

- Total eligible tracts (pop ≥1500): 81,073
- Total eligible counties (pop ≥3000): 3,034
- Urban tracts: 42,193  Suburban tracts: 18,004  Rural tracts: 20,876

## Caveats for revision-before-lock decision

- pct_nhw_approx is a lower bound (subtracts ALL Hispanic from white-alone). True NHW% from B03002 will be HIGHER, so UW-LI / RW-HI counts shown are **conservative under-estimates**.
- Inequity composite using only 2/4 dimensions; adding food-access and school resources may shift cells (some currently flagged High may not survive 3-of-4 threshold; some currently flagged Low/Mod may pass).
- RNA-HI proxy via AIAN-majority counties is structurally different from reservation-level analysis. The true RNA-HI count requires spatial join with AIANNH.
- Urban/rural proxy is COARSE — Census Urban Area shapefile is needed for tract-level urban/suburban distinction.

If actual counts deviate substantially from §2 estimates, revise §2 thresholds BEFORE OSF lock.
