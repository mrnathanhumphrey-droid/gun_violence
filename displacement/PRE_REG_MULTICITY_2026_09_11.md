# PRE-REGISTRATION — MULTI-CITY HOLC BOUNDARY DESIGN

**Frozen:** 2026-09-11
**Analyst:** Nathan Humphrey
**Project:** `D:\Gun Violence`
**Supersedes:** nothing. This is the first pre-registration in this project.

---

## 0. STATE OF THE WORLD AT FREEZE TIME

This section exists so that no later reader — including us — can mistake a known
result for a predicted one.

**Already observed (NOT blind).** The Chicago boundary design has been run. Its
results are known and are reproduced here in full:

| band | n_D | n_C | rate_D | rate_C | RR (D/C) | 95% CI |
|---|---:|---:|---:|---:|---:|---|
| 150 m | 866 | 842 | 180.9 | 163.6 | 1.106 | [1.006, 1.216] |
| 250 m | 1,505 | 1,404 | 194.5 | 162.4 | **1.197** | [1.113, 1.288] |
| 500 m | 2,745 | 2,851 | 195.8 | 161.3 | 1.214 | [1.152, 1.279] |
| 1000 m | 4,254 | 5,709 | 192.4 | 165.6 | 1.162 | [1.117, 1.209] |

Window 2019–2023, firearm victimizations per 100k/yr, `pct_black` SMD −0.021 at 250 m.
All-years 150 m is null (1.025 [0.975, 1.079]).

**Chicago is therefore the discovery sample and cannot serve as confirmation of its
own hypothesis.** Consequence, pre-specified in §6: a leave-Chicago-out pooled
estimate is a CO-PRIMARY, reported with equal prominence to the all-city estimate.

**Not yet observed (blind).** As of freeze, `displacement/data/` contains exactly one
outcome file, `chicago_shootings.parquet`. No outcome data for any other city has been
downloaded, inspected, or analyzed. The endpoint probes run on 2026-09-11 established
only the *existence*, *row count*, *schema*, and *date span* of candidate sources. No
coordinate, no incident location, and no rate for any non-Chicago city has been computed.

**Also already observed, and relevant.** Two prior results constrain what this design
may claim:

1. The national pooled GVA×HOLC estimate was carried by large cities while the
   within-city paired test was **null (p = 0.63)**. Pooling raw counts across cities is
   therefore known to be a biased procedure here and is prohibited in §5.
2. The boundary effect **weakens as the band narrows** — reproduced in both the national
   GVA analysis and in Chicago. This is the opposite of a sharp discontinuity. §7 fixes
   in advance how this must be reported.

---

## 1. QUESTION

Within a single city, holding state, municipal law, police department, and — by
construction and verified by balance — racial composition fixed, is firearm violence
higher on the D side of a 1930s HOLC C/D grade boundary than on the C side?

And: is whatever difference exists a **discontinuity at the line**, or a **smooth
gradient** of which the line is merely an interior marker?

## 2. HYPOTHESES

- **H1 (primary).** The pooled random-effects rate ratio D/C at 250 m exceeds 1.
- **H0.** The pooled rate ratio is 1.
- **H2 (placebo, must FAIL for H1 to mean anything).** The same machinery applied to a
  sham boundary drawn *inside* D territory, where no grade change occurs, returns RR ≈ 1.
- **H3 (form).** The effect is a gradient, not a discontinuity: RR does not increase as
  the band narrows toward the line.

H3 is registered as a **directional prediction we expect to confirm**, not as a caveat.
Chicago and the national analysis both already point this way. Registering it now means
we cannot later present a gradient as if it were a discontinuity.

---

## 3. UNITS

**The unit of analysis is the CITY.**

**New York City counts as ONE unit, not five.** HOLC surveyed Manhattan, Brooklyn,
Queens, the Bronx, and Staten Island as separate documents, and the temptation is to
enter five units. They share one police department, one district attorney structure,
one state firearm code, and one reporting system. Entering them separately would
manufacture independence the data does not have and would give NYC five votes in the
meta-analysis. The five borough geometries are unioned into a single NYC geometry
before band construction. The five-way split is reported as a **sensitivity only**.

**Wave 1 city set, fixed now:**

| unit | HOLC C | HOLC D |
|---|---:|---:|
| Chicago, IL | 327 | 147 |
| Los Angeles, CA | 167 | 71 |
| Detroit, MI | 122 | 62 |
| New York, NY (5 boroughs unioned) | 189 | 119 |
| Philadelphia, PA | 18 | 26 |
| Seattle, WA | 18 | 11 |
| Baltimore, MD | 22 | 9 |

**Excluded at freeze, with reason:**

- **Cleveland, OH** (D=28) — no incident-level open crime data located. Searched ArcGIS
  Hub; nothing returned for the city. Excluded for data absence, not for its result.
- **Cincinnati, OH** — not present in the HOLC file.
- **Austin, TX** — geography is census block group only; HOLC D=7.
- **New Orleans, Pittsburgh, Milwaukee, Minneapolis, Dallas** — plausible sources exist
  but firearm separability is UNVERIFIED at freeze. These are **Wave 2**. If any is
  later added, it is added under an amendment to this document (§10), dated, with the
  Wave 1 result already on the record.

No city may be dropped from Wave 1 after its rate ratio is seen. The only permitted
exclusions are the mechanical ones in §4.4, which are evaluated on geometry and
population, never on the outcome.

---

## 4. DATA AND CASE DEFINITIONS

### 4.1 Denominator (identical for every city)

2023 ACS 5-year tract population (`B01001_001E`), areal-interpolated into each band:
each tract contributes population in proportion to the share of its area inside the
band. This assumes uniform population density within a tract. That is the standard
assumption and a genuine limitation; it is stated in every write-up, not hidden.

Balance covariates, same source, tract level: `B02001` (race), `B17001` (poverty),
`B19013` (median household income), `B25003` (tenure), `B15003` (education).

### 4.2 Geography

HOLC C and D polygons, Mapping Inequality, `mappinginequality.json`.
Tract boundaries: TIGER 2024, `tl_2024_<ss>_tract.zip`.
All geometry in EPSG:5070.

### 4.3 Outcome — per-city case definition, declared now

A case definition, once written here, **may not be changed after any rate ratio for
that city has been computed.** Where a definition cannot yet be stated exactly, the
*rule for deriving it* is stated instead, together with the requirement that the derived
value set be written to the fetch manifest **before** any rate is computed.

| unit | source | case definition | status |
|---|---|---|---|
| Chicago | Socrata `gumc-mgzr` | `gunshot_injury_i = 'YES'`; unit = **victim** | EXACT |
| Philadelphia | Carto `phl.carto.com` table `shootings` | all rows; unit = **victim**; coords `point_x`/`point_y` | EXACT |
| New York | Socrata `5ucz-vwe8` ("Shootings (2006-Present)") | all rows; unit = **incident** | EXACT — see §4.5 |
| Detroit | ArcGIS `RMS_Crime_Incidents` | `charge_des = 'NON-FATAL SHOOTING'`; unit = **incident** | EXACT — see §4.6 |
| Baltimore | ArcGIS `Part1_Crime` | `Weapon ∈ {FIREARM, HANDGUN, RIFLE, SHOTGUN, OTHER_FIREARM, AUTOMATIC_FIREARM, AUTOMATIC_HANDGUN, AUTOMATIC_RIFLE, AUTOMATIC_OTHER_FIREARM}`; unit = **offense** | EXACT |
| Los Angeles | Socrata `2nrs-mtv8` + `63jg-8b9z` | rows whose `weapon_desc` denotes a firearm. **The exact `weapon_used_cd` set is to be enumerated from the live `weapon_desc` value list at fetch time and written to the manifest before any rate is computed.** No code range is asserted here from memory. | DERIVATION RULE |
| Seattle | Socrata `tazs-3rd5` | rows where `shooting_type_group` denotes an actual firearm discharge. **The value list is to be enumerated at fetch time and the retained set written to the manifest before any rate is computed.** | DERIVATION RULE |

### 4.4 Mechanical inclusion rules — evaluated on geometry and population only

A city enters the primary analysis if and only if:

1. it has at least one C polygon and one D polygon whose boundaries lie within the band
   width of each other (i.e. both bands are non-empty);
2. **both** bands contain at least **500** interpolated persons;
3. `n_D + n_C ≥ 30` cases in the primary window.

Rule 3 is a floor on estimability, not on effect size. It is computed from the total on
both sides and is blind to which side the cases fall on.

### 4.5 The NYC file discrepancy — resolution procedure fixed in advance

Two NYPD shooting files exist and they disagree:

- `833y-fsy8` (ARCHIVED, "Historic"): 29,744 rows, 2006-01-01 → 2024-12-31, 29,647 geocoded.
- `5ucz-vwe8` (live, "Shootings (2006-Present)"): 24,310 rows, 2006-01-01 → 2026-06-30, all geocoded.

The live file is lower in **every year** (2019: 777 vs 967; 2020: 1,532 vs 1,948) — a
uniform ≈22% level shift across the whole series, not a tail effect. This is a
definitional change by NYPD, not a data error.

A uniform proportional difference cancels in a rate ratio **only if the dropped records
are spatially neutral with respect to the boundary.** Pre-specified procedure:

- **Primary:** the live file `5ucz-vwe8`.
- **Mandatory robustness:** recompute NYC's RR from `833y-fsy8`. Both are reported.
- If the two log RRs differ by more than **0.10**, the difference is NOT spatially
  neutral, NYC is reported with both estimates and an explicit caveat, and NYC is
  additionally excluded in a sensitivity refit. The decision rule is fixed now so that
  it cannot be chosen after seeing which answer is more convenient.

### 4.6 Detroit — definitional judgment recorded

`charge_des = 'NON-FATAL SHOOTING'` is unambiguously a firearm discharge.
Homicides sit in a separate field (`offense_ca = 'HOMICIDE'`) and are **not** all
firearm. Including them would import non-firearm deaths into a firearm outcome.

**Decision: non-fatal shootings only.** This makes Detroit's case definition
*non-fatal-only* where Chicago's and Philadelphia's include fatalities. That is
acceptable under §5.1 — the rate ratio is invariant to the definition as long as the
same definition is applied to both sides of the boundary — and it is recorded here so
the asymmetry is never discovered later and mistaken for a bug.

### 4.7 Coordinate precision — measured, not assumed

LAPD is documented as rounding coordinates to the hundred block (~100 m), which would
be disqualifying at the 150 m band. Rather than trust documentation, the runner computes
for every city:

- unique coordinate pairs ÷ n cases;
- modal duplicate-coordinate count;
- median nearest-neighbour distance between distinct coordinates.

**Pre-specified rule:** a city whose median nearest-neighbour distance between distinct
coordinates exceeds **half the band width** is excluded from that band, and only that
band. The rule is applied identically to all cities, is computed from coordinates alone,
and is blind to the outcome.

---

## 5. ESTIMAND AND POOLING

### 5.1 Per-city estimand

For band width *b*, within each city:

```
D-side band = (union of D polygons) ∩ buffer(boundary of C polygons, b)
C-side band = (union of C polygons) ∩ buffer(boundary of D polygons, b)

rate_D = 1e5 * n_D / pop_D / years
rate_C = 1e5 * n_C / pop_C / years
RR     = rate_D / rate_C
SE(log RR) = sqrt(1/n_D + 1/n_C)
```

The rate ratio is **within-city**, so any case definition applied identically on both
sides cancels out of the ratio. This is the formal reason cities with different case
definitions (victims vs incidents vs offenses) may be combined at the level of the
*ratio* and may **not** be combined at the level of *counts*.

### 5.2 Pooling — random effects, and never raw counts

Pooled across cities by **DerSimonian–Laird random effects on log RR**. Reported:
pooled RR, 95% CI, **τ²**, **I²**, and a 95% **prediction interval**.

**Pooling raw counts across cities is prohibited.** It is already known to fail here:
the national GVA pooled estimate was carried by large cities while the within-city
paired test was null (p = 0.63). A procedure known to be biased in this exact setting
is not available as a robustness check either.

### 5.3 Primary specification — exactly one number

> **Band 250 m. Window 2019-01-01 to 2023-12-31. DerSimonian–Laird random-effects
> pooled rate ratio across all Wave 1 cities meeting §4.4.**

### 5.4 Co-primary

> **The same estimate with Chicago removed.**

Chicago generated the hypothesis (§0). The leave-Chicago-out estimate is the one that
tests it, and it is reported with equal prominence in the abstract, not buried in a
sensitivity table.

### 5.5 Secondary and sensitivity — all labelled as such

- bands 150 m, 500 m, 1000 m;
- each city's own full date span, in place of 2019–2023;
- NYC split five ways;
- NYC under `833y-fsy8` (§4.5);
- fixed-effect pooling alongside random-effects;
- leave-one-city-out, cycled over every city;
- balance-flagged cities removed (§8).

---

## 6. FALSIFICATION — H2, the sham boundary

Every Wave 1 city is re-run against a **sham boundary**: each D polygon is bisected by a
randomly oriented line through its centroid, the two halves are labelled sham-D and
sham-C, and the identical band, interpolation, and rate machinery is applied. No grade
change occurs anywhere along a sham line.

- **Expected:** sham RR ≈ 1, CI containing 1, pooled across 200 random orientations.
- **If the sham reproduces the real effect**, the design is measuring distance-to-edge
  or polygon interior/exterior structure, **not** redlining grade, and H1 is not
  supported regardless of what the real boundary shows.

This test is what converts "D areas have more shootings" into a claim about the
**boundary**. It is registered as a condition on H1, not as an optional extra.

---

## 7. FORM OF THE EFFECT — how H3 must be reported

Two things are pre-committed here.

**7.1 Signed-distance gradient.** In addition to discrete bands, the rate is estimated
as a function of **signed distance** to the nearest C/D boundary (negative on the C
side, positive on the D side), by local polynomial fit within each city. This is the
proper regression-discontinuity framing and it makes the shape of the effect a measured
quantity rather than a footnote.

**7.2 Reporting rule, fixed in advance.** If RR is non-increasing as the band narrows in
**5 or more of 7** cities, the effect is reported as an **area gradient, not a
discontinuity**, in the abstract, in the results, and in the title if the title makes a
causal claim. The words "discontinuity," "sharp," "jump," and "at the line" are
prohibited in describing the estimate under that outcome.

We expect this outcome. Registering it now removes the option of discovering a reason to
describe a gradient as a discontinuity once the numbers are in.

---

## 8. BALANCE — and what we refuse to do about it

For every city and band, standardized mean differences between the D and C bands on:
`pct_black`, poverty rate, median household income, owner-occupancy, share with a
bachelor's degree.

`pct_black` SMD is the one that matters. In Chicago it is −0.021 at 250 m — racial
composition is held fixed **by the design**, not by conditioning.

- A city with **|SMD| > 0.25 on `pct_black`** at the primary band is **flagged**, and a
  sensitivity refit excludes flagged cities.
- **We do not condition on `pct_black`.** Racial composition is downstream of redlining;
  controlling for it is conditioning on a post-treatment variable and would estimate a
  quantity nobody wants. This project has already retracted one result for a related
  error (a segregation "attenuation" that was isolation, a near-collinear restatement of
  `pct_black`, ρ = 0.967). The design holds race fixed geographically or not at all.

---

## 9. DECISION RULES

**H1 supported** if and only if all three hold:

1. the primary pooled RR (§5.3) has a 95% CI excluding 1;
2. the **co-primary**, Chicago removed (§5.4), also has a 95% CI excluding 1;
3. the sham-boundary pooled RR (§6) has a 95% CI **containing** 1.

**H1 not supported** if any of: the primary CI contains 1; the leave-Chicago-out CI
contains 1; or the sham boundary produces an RR of comparable magnitude to the real one.

**Reported regardless of direction:** τ², I², the prediction interval, every city's
individual RR and n, every excluded city with its mechanical reason, the sham result,
and the signed-distance gradient.

A null result is a publishable result and will be written as one. The within-city
question is worth answering either way, and a well-powered within-city null on seven
cities is a stronger contribution than the national pooled estimate this design
replaces.

---

## 10. AMENDMENTS

Any change to §3–§9 after freeze is appended below with a date and a reason, and the
pre-amendment result stays in the record. Wave 2 cities (New Orleans, Pittsburgh,
Milwaukee, Minneapolis, Dallas) enter by amendment, after Wave 1 is on the record.

### Amendment 1 — 2026-09-11, after Wave 1 fetch, BEFORE any rate was computed

Wave 1 outcome data is now cached (`displacement/data/cities/`, 98,481 events in the
primary window). No band, population, or rate has been computed for any city. These are
**data facts discovered during acquisition**, not design changes; §3–§9 are unaltered.
They are recorded now so that none of them can later be discovered and mistaken for a bug,
or worse, adjusted for after seeing a result.

**A1.1 — Effective observation window differs by city.** The estimand (§5.1) is a
*within-city* ratio, so exposure time cancels exactly and the RR is unaffected. But
*reported rates* would be wrong under a blanket 5.0-year denominator. **Exposure years
for every city are therefore computed from that city's own observed span inside the
primary window, not from the nominal window length.**

| unit | effective window | exposure yrs | note |
|---|---|---:|---|
| Chicago | 2019-01-01 .. 2023-12-31 | 4.99 | full |
| Philadelphia | 2019-01-01 .. 2023-12-31 | 5.00 | full |
| New York | 2019-01-01 .. 2023-12-31 | 4.99 | full |
| Los Angeles | 2019-01-01 .. 2023-12-31 | 5.00 | full |
| Seattle | 2019-01-01 .. 2023-12-31 | 4.99 | full |
| **Baltimore** | 2019-01-01 .. **2023-02-11** | **4.11** | source layer ends 2023-02-11 (confirmed server-side) |
| **Detroit** | **2021-01-01** .. 2023-12-31 | **3.00** | see A1.2 |

**A1.2 — Detroit's case definition has no pre-2021 coverage.** The `NON-FATAL SHOOTING`
charge value is effectively absent before 2021: 2019 = 1 record, 2020 = 2, then 863 /
748 / 659 for 2021 / 2022 / 2023. This is a coding-practice change at Detroit PD, not a
data loss. The case definition registered in §4.6 is **unchanged**; Detroit's effective
window becomes 2021–2023 and is reported as such. Detroit's RR therefore answers the
question for a shorter period than the other cities. Because each city is its own
comparison, this is a heterogeneity source to disclose, not a confound — but it is
disclosed, and Detroit is included in the leave-one-out cycle (§5.5).

**A1.3 — Seattle suppresses ~10% of shooting locations.** Seattle publishes the literal
string `REDACTED` in place of coordinates for **1,044 of 10,319** retained records
(10.1%), plus 741 rows coded `(-1,-1)`. The redaction is a deliberate withholding and is
almost certainly **not spatially random** — suppression of exactly the locations a
boundary design needs. It cannot be repaired. Seattle enters the analysis with this
stated, and the leave-one-out cycle (§5.5) shows what the pooled estimate does without it.

Also recorded: Seattle's retained set is dominated by `Shots Fired
(Eyewitness/Casings/Property Damage)` (7,635 of 10,319) rather than injuries, so
Seattle's construct is *discharges* where Chicago's and Philadelphia's is *victims*.
Permitted under §5.1; disclosed as heterogeneity.

**A1.4 — Two source defects corrected, both recorded in the manifests.**

- **NYC's live file ships `latitude` and `longitude` swapped** — the column named
  `latitude` contains values near −73.9. Detected by an in-US-bounding-box test
  (0.013 as-is → 0.987 swapped), corrected, and flagged in the manifest. Detection is
  dynamic rather than hard-coded so that a future publisher fix does not silently
  re-break it. Cross-check: post-correction in-window n = 6,139, which matches the
  year-by-year totals read independently from the raw API (777+1,532+1,562+1,294+974).
- **Missing-location sentinels** are dropped and counted, never silently kept:
  Baltimore `(0,0)` = 1,619 (3.2%), Seattle `(-1,-1)` = 741, LA `(0,0)` = 44.

**A1.5 — LA coordinate precision, measured.** LA's unique-coordinate ratio is **0.286**
with a modal duplicate count of **128**, confirming heavy hundred-block rounding. Under
the pre-registered §4.7 rule this is expected to exclude LA from the narrow bands. The
rule was fixed before this was measured and is applied unchanged.

**A1.6 — A classification error caught and fixed before use.** The first pass of the
Los Angeles weapon rule vetoed `HECKLER & KOCH 91/93 SEMIAUTOMATIC ASSAULT RIFLE`,
because the veto list contained the substring `HECKLER`. Those are real rifles. Fixed;
the retained set is 21 firearm descriptions, and the full kept/rejected lists are written
to `los_angeles_manifest.json` as §4.3 requires. The same pass rejects `TOY GUN`,
`SIMULATED GUN`, `AIR PISTOL/REVOLVER/RIFLE/BB GUN`, `STARTER PISTOL/REVOLVER` and
`STUN GUN`, which is the contamination that rule exists to prevent.

Separately, the first Seattle rule was a blacklist and **retained `'-'`, the label on
1,549,610 rows of all other crime** — it would have made Seattle's outcome "all crime."
Replaced with a whitelist requiring an affirmative discharge label, plus an assertion
that refuses to proceed if a placeholder value is ever retained.

---

### Amendment 2 — 2026-09-13, after the block bootstrap, BEFORE the meta-analysis

**This amendment is post-hoc with respect to the bootstrap and is labelled as such.** It is
written after seeing that the pre-registered standard error is wrong, and before any
pooled estimate exists. Every change below moves the analysis toward CONSERVATISM — wider
intervals, fewer surviving cities, a weaker headline. That is the opposite direction from
the abuse pre-registration exists to prevent, which is why it is being made rather than
silently honoured or silently ignored.

**A2.1 — §5.1's standard error is replaced.** The pre-registered
`SE(log RR) = sqrt(1/n_D + 1/n_C)` treats each shooting as an independent Poisson draw.
Shootings cluster in space and time through retaliation, so that formula is simply wrong
here. Measured against a design-based bootstrap it is too narrow by **1.50× to 4.67×**:

| city | RR | analytic 95% CI | bootstrap 95% CI | width ratio | eff. clusters |
|---|---:|---|---|---:|---:|
| Philadelphia | 1.460 | [1.340, 1.591] | [1.148, 1.808] | 2.65 | 31.4 |
| Los Angeles | 1.412 | [1.318, 1.513] | [1.114, 1.762] | 3.32 | 104.4 |
| New York | 1.257 | [1.114, 1.419] | [1.027, 1.513] | 1.60 | 97.7 |
| **Chicago** | 1.198 | [1.114, 1.289] | **[0.992, 1.428]** | 2.51 | 109.4 |
| Seattle | 1.200 | [0.919, 1.566] | [0.762, 1.828] | 1.64 | 29.3 |
| Baltimore | 0.798 | [0.734, 0.868] | [0.536, 1.170] | 4.67 | 27.0 |
| Detroit | 0.759 | [0.595, 0.968] | [0.517, 1.076] | 1.50 | 68.4 |

The meta-analysis uses bootstrap-derived standard errors,
`SE = (log hi − log lo) / (2 × 1.96)`. The analytic version is reported alongside as the
pre-registered original, so the effect of the change is visible rather than buried.

**A2.2 — The bootstrap cluster is a segment of the interface, carrying both its sides.**
The design is a PAIRED comparison across a boundary, so the unit that the experiment
re-rolls is a stretch of that boundary together with the D-side and C-side strips facing
each other across it. The C/D interface is cut into 500 m segments; Voronoi cells around
the segment midpoints partition the plane so the per-segment pieces are disjoint; segments
are resampled with replacement, 2,000 times, seed 20260913. Verification: summing the
per-segment pieces reproduces the main per-city estimate to **±0.0000 in all seven cities**,
so the partition neither loses nor double-counts any event or any person.

**A2.3 — CHICAGO, THE DISCOVERY CITY, DOES NOT SURVIVE ITS OWN CONFIRMATION.**
Chicago's corrected interval is **[0.992, 1.428]** and crosses 1. The point estimate is
unchanged (1.198) and the sham placebo passed it marginally (p = 0.045), so the honest
description is *marginal*, not *null*. But Chicago can no longer be stated as a clean
positive result, and any earlier text describing it as one is superseded by this line.
This is precisely the scenario §5.4 made leave-Chicago-out a co-primary for.

**A2.4 — The gradient endpoint contrast is withdrawn as an estimator.** §7.1 asks for the
profile; the local-linear endpoint contrast was an addition, and a bandwidth sweep shows
it is unstable at exactly the widths that matter — Philadelphia moves 0.870 → 0.999 →
1.117 → 1.555 → 1.458 across ±150/250/300/500/1000 m, because it extrapolates a line
through three noisy bins to zero. The §7.1 profile is retained as the FIGURE it was meant
to be; §5.3's band rate ratio remains the estimator. Raw near-boundary bins (no
extrapolation) agree with the independently-constructed band estimates to within 0.04 in
all seven cities, which is a genuine cross-check of two separate geometry implementations.

**A2.5 — Three cities are uninformative, by three independent diagnostics.**
Baltimore, Detroit and Seattle fail the sham placebo (p = 0.330, 0.220, 0.555), have
bootstrap intervals spanning 1, and carry the least usable geography in the sample
(Baltimore 13.8 km of interface and 63.5% of its D-band events in a single polygon;
Seattle 23.2 km and a sign flip on one polygon drop; Detroit 2,270 events over three
years). They remain in the meta-analysis — dropping cities on their results is forbidden —
but the paper must not present the Baltimore or Detroit "reversals" as findings. They are
consistent with no effect and with a large effect in either direction.

### Amendment 3 — 2026-09-13, after literature positioning

Prompted by reading the primary boundary-design literature, not by any result. The
primary (§5.3) is UNCHANGED; this adds one declared sensitivity and two disclosure
obligations.

**A3.1 — SEGMENT (BOUNDARY) FIXED EFFECTS, added as a declared sensitivity.**
Aaronson, Hartley & Mazumder (Chicago Fed WP 2017-12, rev. 2020) and Krimmel (2018) both
restrict comparison to residents of the SAME boundary segment, via boundary fixed effects.
Our §5.1 estimator pools each city's entire C/D interface, which is a weaker comparison:
it allows a D strip on one side of the city to be compared against a C strip on the other.

Added: a **conditional Poisson estimator with one fixed effect per 500 m interface
segment and a log-population offset**, so that only WITHIN-SEGMENT D-vs-C contrasts
identify the parameter. Conditioning on each segment's event total, the D-side count is
binomial with `pi_k = pD_k e^b / (pD_k e^b + pC_k)`; the conditional MLE for `b` is the
segment-fixed-effects log rate ratio. Inference by the same 500 m cluster bootstrap as
Amendment 2. The segment structure already exists — it is what A2.2 resamples.

This is a SENSITIVITY, not a replacement. §5.3's band rate ratio remains the primary, and
both are reported. If the two disagree materially, the disagreement is the finding and is
reported as such.

**A3.2 — Krimmel's identification critique must be cited explicitly, not paraphrased into
a generic caveat.** Krimmel documents that HOLC lines were "drawn precisely along
pre-existing racially segregated areas," with significantly more Black residents on the D
side **in 1940**, and states this "calls into question the identifying assumptions of a
regression discontinuity design." Aaronson et al. likewise report significant pre-trends
from 1910 to 1930 that survive boundary fixed effects. Our balance check (§8) is on
CURRENT covariates and does not answer this. §11 already refuses causal identification of
the 1937 policy; A3.2 requires that refusal to name this literature rather than gesture at
it.

**A3.3 — The contradiction with the leading multi-city firearm study is a result and is
reported as one.** Mehranbod et al. (2022, Preventive Medicine 165:107207; 21 cities, ZIP
code level, exposure = share of ZIP land area by HOLC grade) report associations
"relatively stronger in Baltimore, MD and weaker in Los Angeles, CA." We find the reverse:
Los Angeles is our strongest city and Baltimore is null at the boundary.

Our own data reconciles the two. Baltimore's WHOLE-GRADE contrast (all D territory vs all
C territory, ignoring the boundary) is **1.090, D higher** — consistent in direction with
theirs — while its 250 m boundary contrast is 0.798 with a bootstrap interval spanning 1.
The coarse-unit association is carried by between-neighbourhood composition, not by
anything at the grade line. Both numbers are reported together; neither is presented as
correcting the other, because they estimate different things.

### Amendment 4 — 2026-09-13, after the donut-hole test

**A4.1 — LOS ANGELES HAS A DIRECTIONAL GEOCODING PROBLEM AT THE BOUNDARY.**
HOLC lines frequently run down streets, and address geocoding resolves to a block centroid
or street-segment midpoint rather than a true location. In Los Angeles this is measurable
and it is ASYMMETRIC:

| city | D/C ratio, events ≤25 m of the line | D/C ratio, 25–250 m | ratio of ratios |
|---|---:|---:|---:|
| **Los Angeles** | **1.903** | 1.082 | **1.759** |
| Detroit | 0.849 | 0.660 | 1.286 |
| New York | 1.118 | 1.165 | 0.960 |
| Chicago | 1.038 | 1.075 | 0.966 |
| Philadelphia | 0.938 | 1.244 | 0.754 |
| Baltimore | 0.534 | 0.824 | 0.649 |
| Seattle | 1.071 | 1.703 | 0.629 |

902 Los Angeles events sit within 25 m of the line and land on the D side nearly 2:1,
while events further out are close to balanced. Every other city is at or below 1.29.
The event-density profile shows the pile directly: counts in the 10 m bins astride the
line run 150 / 154 / **277 / 256** against neighbouring bins of 40–70 (within-±30 m to
30–150 m density ratio **2.62**). LA also has the worst measured coordinate precision in
the sample (83 m median nearest-neighbour, unique-coordinate ratio 0.286, modal duplicate
128).

Consequently LA's rate ratio collapses toward 1 as the hole widens — 1.439 → 1.259 →
1.253 → 1.185 → 1.102 → **1.003** at h = 0/25/50/75/100/150 m — while Chicago, New York
and Philadelphia all move the OTHER way.

A competing substantive explanation cannot be excluded: HOLC lines follow arterials, and
the D-side frontage of an arterial may genuinely carry more violence. **We cannot separate
the two with these data, and we do not claim to.** Either way LA's estimate rests on
events whose side assignment is not credible, and it must not be presented as the paper's
strongest evidence. This also explains an earlier open puzzle: LA was the one city with a
discontinuity-like band profile.

**A4.2 — LEAVE-LOS-ANGELES-OUT IS PROMOTED TO A REPORTED HEADLINE**, alongside the §5.3
primary and the §5.4 leave-Chicago-out co-primary:

    primary (all included)      RR 1.251 [1.098, 1.424]
    leave-Chicago-out (§5.4)    RR 1.257 [1.062, 1.487]
    leave-Los-Angeles-out       RR 1.213 [1.042, 1.412]

LA breaks no pre-registered rule — it passes §4.4, §4.7, §8 and the §6 sham (p = 0.000).
It is promoted to the abstract because a DISCLOSED MEASUREMENT PROBLEM in one city belongs
where readers see it, not in a robustness table. LA is NOT dropped: dropping a city on
its results is forbidden by §3, and this is a disclosure, not an exclusion.

**A4.3 — THE DONUT IS A DIAGNOSTIC AND IS EXPLICITLY NOT ADOPTED AS THE PRIMARY.**
The pooled estimate RISES with hole radius: 1.218 → 1.229 → 1.266 → 1.271 → 1.325 → 1.332
(1.176 → 1.422 excluding LA). That is tempting and it is a trap. Widening the hole pushes
the two sides further apart, which is the SAME mechanism as widening the band — more
separation, more racial-composition imbalance, larger apparent effect. It is the third
independent manifestation of the same finding (band width, signed-distance profile, now
donut radius), not a cleaner estimator.

**No donut radius may be adopted as the primary specification.** §5.3's h = 0 tight band
stands. The donut's job was to detect displacement at the line; it did, in exactly one
city, and that is the whole of what it is used for.

### Amendment 5 — 2026-09-13, WAVE 2. Written BEFORE any Wave 2 data is fetched.

§10 requires Wave 2 cities to enter by amendment, after Wave 1 is on the record. Wave 1 is
on the record (primary 1.251 [1.098, 1.424]; co-primary 1.257 [1.062, 1.487]; leave-LA-out
1.213 [1.042, 1.412]; segment FE 1.200 [1.047, 1.374]; sham 1.021 contains 1). No Wave 2
outcome file has been downloaded. Case definitions are declared here FIRST, because
declaring them after seeing a city's rate ratio is precisely the freedom this document
exists to remove.

**A5.1 — WAVE 2 CITY SET.**

*Admitted, schema verified:*

| unit | HOLC D | source | case definition | status |
|---|---:|---|---|---|
| Kansas City, MO | 40 | Socrata `gqy2-yvmn` (KCPD Reported Crime Data, since 2015) | `firearm_used_flag` indicates a firearm; unit = **offense** | EXACT |
| Boston, MA | 12 | data.boston.gov CKAN, Crime Incident Reports | `SHOOTING` flag set; coords `Lat`/`Long`; unit = **incident** | EXACT |
| Dallas, TX | 9 | Socrata `qv6i-rri7` (Police Incidents) | `weaponused` denotes a real firearm, by the SAME word rule and imitation-weapon veto used for Los Angeles (§4.3); unit = **offense** | DERIVATION RULE |

*Admitted conditionally, subject to the A5.3 gate:*

| unit | HOLC D | source | case definition | status |
|---|---:|---|---|---|
| Pittsburgh, PA | 34 | WPRDC CKAN Police Incident Blotter (archived + 30-day) | offences in the free-text `OFFENSES` field denoting **discharge of a firearm**; unit = **incident**; coords are `X` = longitude, `Y` = latitude | DERIVATION RULE |
| Milwaukee, WI | 24 | data.milwaukee.gov `wibr.csv` | a firearm-indicating field, to be enumerated; unit = **offense** | UNVERIFIED |

**A5.2 — PITTSBURGH'S IMITATION-WEAPON PROBLEM IS DECLARED NOW.** Pittsburgh code
**607.03 is "Discharging Firearm or Airgun"** — it bundles a real firearm with an air gun
in a single code. The LA pass already showed what happens when imitation and non-lethal
"guns" are not vetoed. Rule, fixed here: a Pittsburgh offence string is retained only if it
denotes discharge of a FIREARM and does not carry an air/BB/pellet qualifier; **607.03 is
EXCLUDED** because it cannot be separated. The retained and rejected offence-string sets
are written to the fetch manifest before any rate is computed, exactly as §4.3 requires.
Pittsburgh's definition is therefore DISCHARGE-ONLY and narrower than Chicago's or
Philadelphia's, which §5.1 permits because the rate ratio is within-city.

**A5.3 — THE VERIFICATION GATE, DECIDED ON SCHEMA AND COVERAGE ONLY.**
Pittsburgh and Milwaukee enter if and only if, on inspection of the source:

1. a field exists that separates firearm cases from non-firearm cases, and its value set
   can be enumerated and written to the manifest;
2. point coordinates exist, in WGS84 degrees, passing the same US-bounding-box and
   sentinel checks as Wave 1;
3. coverage overlaps 2019–2023 with no year-gap that the A1.1 sustained-coverage rule
   would strike out;
4. the city clears §4.4 (both bands ≥500 people, n_D + n_C ≥ 30) and §4.7 (precision).

**The gate is evaluated on the SCHEMA and the DATE COVERAGE. It is never evaluated on a
rate ratio.** If a city fails the gate it is recorded as MISSING with the failing clause
named — never as a city with no effect.

**A5.4 — EXCLUDED FROM WAVE 2, WITH REASONS RECORDED BEFORE THE FACT.**

- **Norfolk, VA (D=30)** — the Police Incident Reports file carries no coordinates at all,
  only census tract and street address. Self-geocoding those addresses would manufacture
  exactly the directional displacement documented in Amendment 4 for Los Angeles. Excluded
  for absence of geography, not for its result.
- **New Orleans, LA (D=49)** — the largest untouched HOLC footprint, but the portal
  publishes per-year *Calls for Service* rather than verified incidents. A dispatch call is
  a different construct from a confirmed event and cannot be mixed with the Wave 1 outcome
  set. Excluded on construct, not on result. Revisit only if an incident-level file is found.
- Atlanta (32), Birmingham (21), Columbus (15), Minneapolis (14) have real police datasets
  in their catalogues that have NOT been field-checked. They are neither admitted nor
  excluded here; they would require a further amendment.

**A5.5 — WAVE 2 CANNOT REVISE WAVE 1.** The Wave 1 primary, co-primary, leave-LA-out,
segment-FE and sham results stand as reported, permanently. Wave 2 produces an ADDITIONAL,
separately-labelled pooled estimate over the combined city set. Both are reported. Wave 2
is being run because tau^2 and the prediction interval are currently estimated from six
points and the prediction interval [0.899, 1.740] crosses 1 — the purpose is to say
something about a NEW city, not to move the existing point estimate.

**A5.7 — GATE OUTCOME, evaluated on schema and coverage as A5.3 requires.**

- **Milwaukee — ADMITTED.** The *current* NIBRS file covers only 2024–2027 and fails clause
  3, but the historical file `wibrarchive.csv` (1,091,595 rows, 1991-01-01 → 2023-12-31)
  carries **229,963 records inside 2019–2023**, with `Weapon_Used_All` (HANDGUN 65,729;
  FIREARM 39,236; alongside PERSONAL WEAPON, LETHAL CUTTING INSTRUMENT, BLUNT OBJECT, etc.)
  and `Address_Longitude` / `Address_Latitude`. Clauses 1–3 pass; 4 is evaluated by the
  standard machinery. Case definition: `Weapon_Used_All` denoting a real firearm, value set
  enumerated and written to the manifest before any rate, with the same imitation-weapon
  veto as Los Angeles.
- **Pittsburgh — FAILS clause 4, recorded MISSING.** The archived blotter holds 340,996
  records, of which only **530** match a firearm-discharge string city-wide across the whole
  archive — and that 530 still INCLUDES code 607.03, which A5.2 excludes because it bundles
  "Firearm or Airgun". After the declared exclusion, restricted to 2019–2023 and then to a
  250 m band, Pittsburgh cannot reach §4.4's n_D + n_C ≥ 30. The 30-day blotter is
  effectively empty (total = 1).

  **Pittsburgh's definition was NOT broadened to rescue it.** Adding possession and carrying
  offences (6106, 6105) would multiply the count several-fold, and adding aggravated assault
  more still — but possession is not violence, and both changes would be a case definition
  rewritten after seeing that the declared one was too thin. A5.2 exists to forbid exactly
  that. Pittsburgh is recorded as MISSING with the failing clause named, never as a city
  with no effect.

**FINAL WAVE 2 SET: Kansas City (D=40), Milwaukee (D=24), Boston (D=12), Dallas (D=9).**

**A5.6 — ALL WAVE 1 MACHINERY APPLIES UNCHANGED** to Wave 2 cities: §4.4 inclusion, §4.7
measured precision, §8 balance and its |SMD| > 0.25 flag, the §6 sham placebo, the
Amendment 2 block bootstrap, and the Amendment 3 segment fixed effects. No Wave 2 city
receives a rule that Wave 1 cities did not.

---

## 11. WHAT THIS DESIGN CANNOT DO

Stated now so it is not discovered as a limitation later:

- **It is not causal identification of 1937 policy.** Boundaries were drawn where they
  were for reasons, and those reasons persist. Balance on observed covariates is not
  balance on unobserved ones. The design removes state, city, law, police department,
  and racial composition; it does not remove whatever made the surveyor draw the line.
- **A 2023 denominator against a 2019–2023 numerator** measures today's population, not
  the population at risk during the treatment. Within-band population change is unmodelled.
- **Areal interpolation assumes uniform density within tracts.** Violated near parks,
  industrial land, and water.
- **Seven cities is seven cities.** τ² and the prediction interval carry that, and the
  prediction interval is reported precisely because the pooled CI understates what a
  new city would show.
- **These are police-recorded events.** Differential reporting across a boundary inside
  one city is less likely than across cities, but it is not zero, and no dataset here
  can rule it out.

---

**FROZEN 2026-09-11, before any non-Chicago outcome data was fetched.**
