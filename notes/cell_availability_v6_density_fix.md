# Cell-availability v6 — density-aware standardization (threshold = mean z ≥ 0.7)

Three standardizations compared:
- **baseline**: unweighted, single distribution (v4 approach)
- **α pop-weighted**: each unit weighted by population in computing mean+sd
- **β stratified**: z-scores computed within urbanicity tier (urban/suburban/rural)

| Cell | §2 est | baseline | α pop-weighted | β stratified |
|---|---|---|---|---|
| UB-HI | 500-1000 | 341 | **398** | **495** |
| UH-HI | 500-1000 | 776 | **880** | **1,159** |
| UW-LI | 1000+ | 4,877 | **4,782** | **3,676** |
| SB-MC | 300-500 | 466 | **440** | **478** |
| RW-HI | 150-250 | 23 | **111** | **24** |
| RB-HI | 60-100 | 23 | **58** | **25** |
| RH-HI | 40-60 | 58 | **104** | **54** |
| RNA-HI | 20-30 (proxy) | 6 | **14** | **7** |

## Verdict

Compare each row's α/β columns to the §2 estimate. The standardization that brings rural cells closest to §2's expected range is the methodological fix for the density-dilution issue.
