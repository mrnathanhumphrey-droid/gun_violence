# Pre-cond (2) v2 — CEM proper (binned + shared support across all 8 cells)

**Method:** Each §3 dim discretized into 3 bins (lo / mid / hi), bin boundaries anchored to §3 thresholds.
Retain units whose 6-dim bin tuple appears in ALL 8 cells (proper CEM shared support).

**Income bin edges (pop-weighted national):** lo < $66,384 ≤ mid ≤ $88,051 < hi

**Bin spec (lo/mid/hi):**
- median_hh_income: < $66,384 / $66,384-$88,051 (§3 target) / > $88,051
- pct_hs_terminal: <30 / 30-50 (§3 ≥40) / >50
- pct_bachelors_plus: <20 / 20-40 (§3 ≤30) / >40
- pct_employed_civilian_LF: <45 / 45-65 (§3 ≥55) / >65
- pct_family_HH: <40 / 40-60 (§3 ≥50) / >60
- pct_working_age: <50 / 50-60 (§3 ≥55) / >60

## Shared bin tuples across all 8 cells: **1** (out of 729 possible)

## Per-cell CEM yield

| Cell | Pre-CEM | Post-CEM (all-8 shared) | Retention | §3 expected 40-60% |
|---|---|---|---|---|
| UB-HI | 846 | 91 | 10.8% ⚠ low |
| UH-HI | 1,830 | 214 | 11.7% ⚠ low |
| UW-LI | 4,600 | 11 | 0.2% ⚠ low |
| SB-MC | 291 | 29 | 10.0% ⚠ low |
| RW-HI | 55 | 23 | 41.8% ✓ |
| RB-HI | 51 | 14 | 27.5% ⚠ low |
| RH-HI | 94 | 5 | 5.3% ⚠ low |
| RNA-HI | 12 | 4 | 33.3% ⚠ low |

## Pairwise shared bin tuples (key comparisons)

| Cell A | Cell B | Shared tuples |
|---|---|---|
| UB-HI | SB-MC | 54 |
| UB-HI | UW-LI | 51 |
| SB-MC | RW-HI | 10 |
| UB-HI | RB-HI | 12 |
| UW-LI | RW-HI | 8 |
| RB-HI | RW-HI | 8 |
| RH-HI | RB-HI | 8 |

## Power tier reassignment (post-CEM, all-8 shared)

| Cell | Post-CEM | Tier (§7: T1≥120, T2 25-100, T3 8-24, <8=unviable) |
|---|---|---|
| UB-HI | 91 | Tier 2 |
| UH-HI | 214 | **Tier 1** |
| UW-LI | 11 | Tier 3 |
| SB-MC | 29 | Tier 2 |
| RW-HI | 23 | Tier 3 |
| RB-HI | 14 | Tier 3 |
| RH-HI | 5 | **unviable** |
| RNA-HI | 4 | **unviable** |