# Gun Violence Cross-Geography Data Pull — Final Report

**Pull date:** 2026-05-12 / 2026-05-13 UTC
**Root:** `D:/Gun Violence/`
**Manifest:** `manifest.json` (17 sources)

---

## Tier completion

| Tier | Sources | Complete | Partial | Documented-skip | Failed | Bytes pulled |
|---|---|---|---|---|---|---|
| 1 (required) | 10 | 9 | 1 | 0 | 0 | 845 MB |
| 2 (important) | 3 | 2 | 1 | 0 | 0 | 645 MB |
| 3 (stretch) | 4 | 0 | 0 | 4 | 0 | n/a |
| **Total** | **17** | **11** | **2** | **4** | **0** | **~1.49 GB** |

Checkpoints: `_agent_status/tier_{1,2,3}_complete.json`.

---

## Tier 1 (required, must succeed) — 9 complete, 1 partial

| Source | Status | Files | Bytes | Notes |
|---|---|---|---|---|
| Gun Violence Archive (mass shootings) | complete | 1 csv | 673 KB | Scope flag below |
| CDC psx4-wq38 (firearm/violence county) | complete | 1 parquet | 632 KB | WISQARS substitute |
| Census ACS 5-year 2023 | complete | 26 parquet | 66 MB | 13 tables × tract + county |
| USDA Food Access Atlas 2019 | complete | 1 xlsx | 86 MB | |
| NCES F-33 finance (SY 18-19 to 21-22) | complete | 4 zips | 15 MB | Fixed-width txt inside |
| NCES EDGE LEA geocode SY 24-25 | **partial** | 1 zip | 8 MB | Directory only; CCD demographic detail not pulled |
| TIGER 2024 counties | complete | 1 zip | 84 MB | |
| TIGER 2024 tracts (per state) | complete | 52 zips | 421 MB | |
| TIGER 2024 unified school districts | complete | 52 zips | 146 MB | No national bundle |
| TIGER 2024 AIANNH (reservations) | complete | 1 zip | 9 MB | Covers Tier 3 BIA |

## Tier 2 (important) — 2 complete, 1 partial

| Source | Status | Files | Bytes | Notes |
|---|---|---|---|---|
| HOLC Mapping Inequality | complete | 1 GeoJSON | 10.5 MB | 10,154 polygons across ~200 cities |
| Eviction Lab (ETS 2020-21) | complete | 4 files | 634 MB | Direct S3, no registration needed |
| Loewen Sundown Towns | **partial** | 1 HTML | 231 KB | UI-only DB; only index page captured |

## Tier 3 (stretch) — 4 documented, 0 pulled

| Source | Status | Reason |
|---|---|---|
| NVDRS | substituted_tier_1 | psx4-wq38 covers same NCHS-derived totals at county level |
| NIBRS | registration_walled | api.data.gov key required (no account creation per brief) |
| Property tax (national) | per_state_required | No unified source; Tax Foundation summaries as proxy |
| BIA reservations | covered_by_tier_1 | TIGER 2024 AIANNH is canonical |

`SOURCE_NOTE.md` files written under each Tier 3 target dir.

---

## Material changes from design document

These three findings should be surfaced to the analysis phase before research-design assumptions harden:

### (1) GVA repo is mass-shootings only, not full-incident
The `dxzys/Gun-Violence-Data` repo tracks GVA's mass-shooting definition (4+ shot, perp excluded). **5,872 incidents 2013–2026**, not the full ~50–70k incidents/year. User directive 2026-05-12: keep mass-shooting subset; flag in manifest. Full GVA incident data is not exposed via API and requires Selenium scrape of year-by-year reports (24+ hr).

### (2) WISQARS has no public CSV API
WISQARS Fatal Injury Reports is form-driven; no programmatic CSV pull without Selenium. **Substituted source:** CDC dataset `psx4-wq38` ("Mapping Injury, Overdose, and Violence - County") via SODA JSON API. Same NCHS underlying data, but `psx4-wq38` adds modeled small-area `rate_m` estimates where raw cells are suppressed. See `outcomes/wisqars/NOTE_SOURCE_PIVOT.md`.

### (3) NCES bulk LEA Universe files migrated to EDGE
The older `ccd_lea_*.zip` per-year files (LEA Universe, Membership, Staff, IDEA, ELL) are not at canonical URLs for SY 2020-21 onward. NCES has consolidated geocodes + directory into EDGE (`EDGE_GEOCODE_PUBLICLEA_2425.zip`). **Full district-level demographic detail (enrollment by race, FRL, ELL, special ed) is not pulled** — those require EDFacts API or manual ElsiNet queries. The F-33 finance files (4 years pulled) cover financial side fully; demographic side is gap.

### (4) HOLC `fullshpfile.zip` / `citiesData.zip` URLs serve SPA HTML
The URLs that show in old documentation now return the React SPA bootstrap HTML (1.4 KB). The canonical national HOLC dataset is the GeoJSON at `mappinginequality.json` (10.5 MB, 10,154 features) — sufficient for all spatial analysis.

---

## Three pointed follow-up questions

1. **Does the research design strictly require full-incident GVA, or are mass shootings (4+ shot) the relevant subpopulation?**
   If full-incident is load-bearing, a separate 24+ hr Selenium scrape is needed against GVA's year-by-year reports. If mass shootings suffice (per the user directive), the current pull is complete.

2. **Does the design need raw WISQARS counts, or are modeled small-area `rate_m` estimates from `psx4-wq38` acceptable?**
   Raw WISQARS counts suppress cells with 1–9 deaths. `psx4-wq38` provides both the suppression-marked `count_sup` AND a published modeled rate. For research designs that explicitly model suppression as missing-not-at-random, the modeled rates may be a confound. For designs that treat suppressed cells as zero or use small-area smoothing themselves, `psx4-wq38` is strictly better.

3. **Does the design require district-level student demographics (enrollment by race/FRL/ELL/IDEA), or is district finance + geocode sufficient?**
   F-33 finance + EDGE LEA geocode together give per-pupil expenditure, Title I status, district location, and basic enrollment counts. Detailed demographic breakdowns (per-race enrollment, FRL %, ELL %, special-ed %) require pulling CCD's separate Membership/IDEA/ELL files via EDFacts or ElsiNet, which were not exposed at canonical URLs in this pull window.

---

## Disk usage summary

```
D:/Gun Violence/                      1.49 GB total
├── outcomes/                          1.3 MB     (GVA + CDC firearm + Tier 3 notes)
├── demographics/                      487 MB     (ACS + TIGER tracts + TIGER county)
├── geographic/                        155 MB     (UNSD + AIANNH + tract-to-county note)
├── inequity_features/                 758 MB     (USDA + Eviction + NCES + property note)
├── historical_mechanism/              10.8 MB    (HOLC + Sundown notes)
├── provenance/                        ~250 KB    (logs, JSON results, methodology snapshots)
└── _agent_status/                     ~4 KB      (tier checkpoints)
```

Plus: `manifest.json`, `FINAL_REPORT.md`, `.env`, `_scripts/`.

---

## Next steps for the analysis phase

1. Verify integrity via the SHA-256 hashes in `manifest.json` (per-file).
2. For any tract-level joins, the TIGER tract zips need to be unzipped (52 state files); a one-time `unzip *.zip -d unpacked/` is the natural pre-processing step.
3. For F-33 finance, the layout file is at `https://nces.ed.gov/ccd/data/txt/sdf{YY}_1a_layout.txt` (not bundled).
4. For ACS parquet files, dedup-check `state` / `county` / `tract` columns vs `GEO_ID` since both are returned by the API.
5. If full GVA incidents or full NCES LEA demographics are needed, those are the remaining heavy fetches.

---

*Pulled by Claude Code (Opus 4.7, 1M context) on behalf of the analysis researcher, 2026-05-12 EDT.*
