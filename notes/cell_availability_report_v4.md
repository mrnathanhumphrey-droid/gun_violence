# Cell-availability v4 — 5-dim composite (adds health access)

**Dimensions:** poverty + food access + housing instability + school resources (log-PPE) + **health access (uninsured + PCP rate)**.

**Sources added vs v3:** CHR 2023 (% Uninsured, PCP Rate per 100k); school dim now log-PPE (fixes v3's 0.8%-only z≥1 issue).

## Cell counts under each rule vs §2 estimate

| Cell | §2 est | **spec-equiv 4/5** | lenient 3/5 | very lenient 2/5 | mean z≥1 |
|---|---|---|---|---|---|
| UB-HI | 500-1000 | **10** | 101 | 761 | 90 |
| UH-HI | 500-1000 | **3** | 177 | 1,170 | 195 |
| UW-LI | 1000+ | **1,633** | 4,200 | 6,891 | 3,179 |
| SB-MC | 300-500 | **684** | 591 | 318 | 618 |
| RW-HI | 150-250 | **0** | 3 | 72 | 0 |
| RB-HI | 60-100 | **0** | 3 | 34 | 4 |
| RH-HI | 40-60 | **0** | 2 | 25 | 16 |
| RNA-HI | 20-30 (proxy) | **0** | 1 | 7 | 3 |

## Per-dim z distributions (% with z ≥ +1.0)

Tract-level:
- z_poverty: 13.3%
- z_food:    21.1%
- z_housing: 11.1%
- z_school:  13.7%  (log-PPE; v3 used raw PPE = 0.8%)
- z_health:  10.4%

County-level:
- z_poverty: 10.8%
- z_food:    14.8%
- z_housing: 10.7%
- z_school:  10.5%
- z_health:  9.5%
