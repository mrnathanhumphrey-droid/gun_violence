# WISQARS source pivot — 2026-05-12

The brief calls for CDC WISQARS Fatal Injury Reports (firearm deaths by
county, 2019–2023, by intent). WISQARS does not expose a public CSV API
endpoint; programmatic pulls require Selenium against the form-based UI.

**Substituted source:** CDC dataset **`psx4-wq38`** ("Mapping Injury,
Overdose, and Violence - County") on `data.cdc.gov` via the SODA JSON API.

Coverage:
- 132,000 rows (≈22,000 county-years per intent)
- 6 intents: `FA_Deaths`, `FA_Homicide`, `FA_Suicide`, `All_Homicide`,
  `All_Suicide`, `Drug_OD`
- 7 periods: 2019, 2020, 2021, 2022, 2023, 2024, plus trailing-twelve-month (TTM)
- County-level FIPS (`geoid`), state FIPS (`st_geoid`)
- Both raw `count_sup` (suppression-marked when 1–9 deaths) and modeled
  `rate_m` with CI bounds

Fields: `geoid`, `name`, `st_geoid`, `st_name`, `intent`, `period`,
`count_sup`, `rate`, `rate_m`, `rate_m_ci`, `data_as_of`, `ttm_date_range`.

**Differences vs WISQARS:**
- WISQARS underlying source is the same NCHS mortality data, so totals
  reconcile at the state-year level.
- `psx4-wq38` provides modeled small-area rate estimates (`rate_m`) where
  WISQARS would suppress; this is a CDC-published estimate, not a raw
  count. Document this distinction in any downstream analysis.
- Suppression rule on raw `rate` is identical (cells with 1–9 deaths
  marked).

If the analysis phase requires raw WISQARS numbers (not the modeled
small-area estimates), a Selenium pull against the WISQARS UI for the
matching intents would be needed as a separate fetch step.

Output: `outcomes/wisqars/cdc_psx4_wq38/cdc_county_injury_violence.parquet`.
