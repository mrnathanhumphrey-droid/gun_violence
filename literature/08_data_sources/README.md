# Data sources — pointers, not PDFs

No PDFs here on purpose. These are datasets, and the live copies live with the analysis code.

## HOLC polygons — Mapping Inequality
Nelson, R. K., Winling, L., Marciano, R., Connolly, N., et al. *Mapping Inequality: Redlining in
New Deal America.* American Panorama, ed. R. K. Nelson & E. L. Ayers. Digital Scholarship Lab,
University of Richmond. https://dsl.richmond.edu/panorama/redlining/

- **Licence: CC BY-NC-SA 4.0.** Attribution required; record the access date in the paper.
- Local copy: `../../historical_mechanism/holc_redlining/mappinginequality.json`
- Filtering is routed through the single shared `holc_for()` in `multi_city_boundary_design.py`.
  ⚠ **Kansas City trap:** 38 of 87 polygons labelled `state=MO` are physically in Kansas
  (16 of 40 grade D). A C/D pair across a state line is not a within-city comparison.
  `CLIP_TO_STATE = {"kansas_city": "29"}` handles it.
- Mirrors: Virginia Tech Figshare (data.lib.vt.edu/articles/dataset/Mapping_Inequality/14113463);
  GeoParquet/PMTiles build at source.coop/cboettig/mappinginequality.

## Population denominators — ACS 5-year, census tracts
Areally interpolated into band polygons; see `interp()` in `multi_city_boundary_design.py`.
Geometry in EPSG:5070. Optional upgrade not yet taken: block-level 2020 PL 94-171 denominators.

## Shooting/firearm-incident data — per-city open portals
Socrata / CKAN / ArcGIS FeatureServer / Carto. Adapters and per-city manifests in
`../../displacement/fetch_city_shootings.py`. A failed fetch records **MISSING, never 0**.

Known per-city traps, all caught by manifests rather than by the fetch succeeding:
- **NYC** ships `latitude`/`longitude` **swapped**; detected dynamically by bounding-box fraction.
  Two NYPD files (live 5ucz-vwe8, archive 833y-fsy8) disagree by ~22%; §4.5 fixes the test.
- **Seattle** classifier retained `'-'` = 1.55M rows of unrelated crime. Whitelist + assertion.
- **Boston** 2019–22 tz-naive vs 2023+ tz-aware concat ⇒ object column ⇒ 1,975 NaT while the
  fetch printed OK. A whole year vanished silently. >10% date-drop now warns.
- **LA** has the worst coordinate precision in the sample (83 m median NN); geocoding asymmetry
  quantified at ratio-of-ratios 1.759 (Amendment 4).

## Sentinel / suppression values to screen for
`(0,0)`, `(-1,-1)`, literal `"REDACTED"`, CDC `-999`.
