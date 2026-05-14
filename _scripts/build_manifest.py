"""Build manifest.json from the assembled data tree.

Walks D:/Gun Violence/ and records per-source: paths, sizes, sha256, row
counts (for parquet/csv), known limitations.
"""
import os, json, hashlib, pathlib, datetime
import pandas as pd

ROOT = pathlib.Path(r"D:/Gun Violence")

def sha256(path, max_bytes=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        if max_bytes:
            h.update(f.read(max_bytes))
        else:
            for chunk in iter(lambda: f.read(1<<20), b""):
                h.update(chunk)
    return h.hexdigest()

def rowcount(path):
    p = pathlib.Path(path)
    try:
        if p.suffix == ".parquet":
            return len(pd.read_parquet(p, columns=[]))
        if p.suffix == ".csv":
            return sum(1 for _ in open(p, encoding="utf-8", errors="ignore")) - 1
    except Exception as e:
        return f"err: {e}"
    return None

def collect(rel_glob):
    """Collect files matching glob (relative to ROOT)."""
    out = []
    for p in sorted(ROOT.glob(rel_glob)):
        if p.is_file():
            out.append({
                "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "size_bytes": p.stat().st_size,
                "sha256": sha256(p),
                "rows": rowcount(p),
            })
    return out

sources = []
now = datetime.datetime.utcnow().isoformat() + "Z"

# === Tier 1 ===

sources.append({
    "source_id": "gva_mass_shootings",
    "source_name": "Gun Violence Archive (mass shootings subset)",
    "url_pulled": "https://github.com/dxzys/Gun-Violence-Data",
    "pull_timestamp": now,
    "version_or_vintage": "git clone --depth 1 (master @ 2026-05-12)",
    "files": collect("outcomes/gva/Gun-Violence-Data/data/*.csv"),
    "year_coverage": "2013–2026",
    "geographic_coverage": "national, lat/lon",
    "known_limitations": (
        "SCOPE MISMATCH vs brief: this repo tracks GVA's mass-shootings "
        "definition only (4+ shot, perp excluded), not the full ~50–70k "
        "incidents/year. ~5,872 incidents 2013–present. Full incident data "
        "would require Selenium scrape of GVA year-by-year reports. User "
        "directive 2026-05-12: keep mass-shootings as-is."
    ),
    "tier": 1,
    "status": "complete",
    "notes": "Materially narrower than brief implied; flagged.",
})

sources.append({
    "source_id": "cdc_psx4_wq38",
    "source_name": "CDC Mapping Injury, Overdose, and Violence - County (replaces WISQARS)",
    "url_pulled": "https://data.cdc.gov/resource/psx4-wq38.json",
    "pull_timestamp": now,
    "version_or_vintage": "2026-04-20 data_as_of",
    "files": collect("outcomes/wisqars/cdc_psx4_wq38/*.parquet"),
    "year_coverage": "2019–2024 + TTM",
    "geographic_coverage": "national, county-level (GEOID)",
    "known_limitations": (
        "Source PIVOT from WISQARS (no public CSV API). psx4-wq38 publishes "
        "modeled small-area rate estimates (rate_m) where raw counts are "
        "suppressed; raw count_sup field separately marks 1–9 cells. See "
        "outcomes/wisqars/NOTE_SOURCE_PIVOT.md."
    ),
    "tier": 1,
    "status": "complete",
    "notes": "6 intents incl FA_Deaths/FA_Homicide/FA_Suicide, 132K rows.",
})

sources.append({
    "source_id": "census_acs5_2023",
    "source_name": "Census ACS 5-year estimates (2019–2023)",
    "url_pulled": "https://api.census.gov/data/2023/acs/acs5",
    "pull_timestamp": now,
    "version_or_vintage": "2023 ACS 5-year (2019–2023)",
    "files": collect("demographics/acs_5yr/*.parquet"),
    "year_coverage": "2019–2023 (5-year estimate)",
    "geographic_coverage": "tract + county, all 50 states + DC + PR",
    "known_limitations": "13 tables × 2 geographies = 26 parquet files.",
    "tier": 1,
    "status": "complete",
    "notes": "Tables: B01001 B02001 B03003 B17001 B19013 B19301 B25003 B25070 B25077 B15003 B23025 B11001 B11003",
})

sources.append({
    "source_id": "usda_food_access_2019",
    "source_name": "USDA Food Access Research Atlas 2019",
    "url_pulled": "https://www.ers.usda.gov/sites/default/files/_laserfiche/DataFiles/80591/FoodAccessResearchAtlasData2019.xlsx",
    "pull_timestamp": now,
    "version_or_vintage": "2019 (current public release)",
    "files": collect("inequity_features/usda_food_access/*.xlsx"),
    "year_coverage": "2019",
    "geographic_coverage": "tract-level national",
    "known_limitations": "2019 vintage; check if newer release available later.",
    "tier": 1,
    "status": "complete",
})

sources.append({
    "source_id": "nces_f33_finance",
    "source_name": "NCES Common Core of Data — School District Finance Survey (F-33)",
    "url_pulled": "https://nces.ed.gov/ccd/data/zip/Sdf{YY}_1a.zip",
    "pull_timestamp": now,
    "version_or_vintage": "SY 2018-19 through SY 2021-22",
    "files": collect("inequity_features/nces_school/Sdf*.zip"),
    "year_coverage": "SY 2018-19 / 2019-20 / 2020-21 / 2021-22",
    "geographic_coverage": "district-level (LEAID), national",
    "known_limitations": "Fixed-width .txt inside zip; layout files at NCES /ccd/data/txt/sdfYY_1a_layout.txt (not bundled here).",
    "tier": 1,
    "status": "complete",
})

sources.append({
    "source_id": "nces_edge_lea_2425",
    "source_name": "NCES EDGE — Public LEA geocodes SY 2024-25",
    "url_pulled": "https://nces.ed.gov/programs/edge/data/EDGE_GEOCODE_PUBLICLEA_2425.zip",
    "pull_timestamp": now,
    "version_or_vintage": "SY 2024-25",
    "files": collect("inequity_features/nces_school/EDGE_GEOCODE_*.zip"),
    "year_coverage": "SY 2024-25",
    "geographic_coverage": "national, district-level with lat/lon",
    "known_limitations": "Directory + geocodes only; full demographic detail (enrollment by race, FRL, ELL) requires CCD LEA Membership/IDEA/ELL files (not pulled).",
    "tier": 1,
    "status": "partial",
    "notes": "Modern replacement for the older CCD LEA Universe per-year zips.",
})

sources.append({
    "source_id": "tiger_2024_county",
    "source_name": "TIGER/Line 2024 — Counties",
    "url_pulled": "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip",
    "pull_timestamp": now,
    "version_or_vintage": "TIGER 2024",
    "files": collect("demographics/tract_boundaries/tl_2024_us_county.zip"),
    "year_coverage": "2024 vintage",
    "geographic_coverage": "national",
    "tier": 1,
    "status": "complete",
})

sources.append({
    "source_id": "tiger_2024_tract",
    "source_name": "TIGER/Line 2024 — Census Tracts (state-by-state)",
    "url_pulled": "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_{ST}_tract.zip",
    "pull_timestamp": now,
    "version_or_vintage": "TIGER 2024",
    "files": collect("demographics/tract_boundaries/by_state/*.zip"),
    "year_coverage": "2024 vintage",
    "geographic_coverage": "50 states + DC + PR (52 zips)",
    "tier": 1,
    "status": "complete",
})

sources.append({
    "source_id": "tiger_2024_unsd",
    "source_name": "TIGER/Line 2024 — Unified School Districts (state-by-state)",
    "url_pulled": "https://www2.census.gov/geo/tiger/TIGER2024/UNSD/tl_2024_{ST}_unsd.zip",
    "pull_timestamp": now,
    "version_or_vintage": "TIGER 2024",
    "files": collect("geographic/school_district_boundaries/by_state/*.zip"),
    "year_coverage": "2024 vintage",
    "geographic_coverage": "50 states + DC + PR (52 zips); no national bundle on Census",
    "known_limitations": "Census doesn't publish a national UNSD bundle; per-state required.",
    "tier": 1,
    "status": "complete",
})

sources.append({
    "source_id": "tiger_2024_aiannh",
    "source_name": "TIGER/Line 2024 — American Indian/Alaska Native/Native Hawaiian Areas",
    "url_pulled": "https://www2.census.gov/geo/tiger/TIGER2024/AIANNH/tl_2024_us_aiannh.zip",
    "pull_timestamp": now,
    "version_or_vintage": "TIGER 2024",
    "files": collect("geographic/reservation_boundaries/*.zip"),
    "year_coverage": "2024 vintage",
    "geographic_coverage": "national",
    "tier": 1,
    "status": "complete",
})

# === Tier 2 ===

sources.append({
    "source_id": "holc_mapping_inequality",
    "source_name": "Mapping Inequality (HOLC redlining national GeoJSON)",
    "url_pulled": "https://dsl.richmond.edu/panorama/redlining/static/mappinginequality.json",
    "pull_timestamp": now,
    "version_or_vintage": "current as of 2026-05-12 pull",
    "files": collect("historical_mechanism/holc_redlining/*.json"),
    "year_coverage": "1935–1940 HOLC surveys",
    "geographic_coverage": "~200 cities mapped (national GeoJSON, 10,154 features)",
    "known_limitations": "Coverage limited to cities HOLC actually surveyed; ~200 cities total; the dsl.richmond shapefile + cities zip URLs serve SPA HTML and are not real downloads.",
    "tier": 2,
    "status": "complete",
    "notes": "Properties incl. area_id, city, state, grade (A/B/C/D), category (Best/Still Desirable/Definitely Declining/Hazardous), residential/commercial/industrial flags.",
})

sources.append({
    "source_id": "eviction_lab",
    "source_name": "Eviction Lab — Eviction Tracking System (multi-site weekly + monthly)",
    "url_pulled": "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/",
    "pull_timestamp": now,
    "version_or_vintage": "2020–2021 ETS release (most recent multi-site bulk)",
    "files": collect("inequity_features/eviction_lab/*"),
    "year_coverage": "2020–2021 weekly + monthly",
    "geographic_coverage": "~40 cities + state-level for participating states",
    "known_limitations": "ETS coverage is partial (~40 cities + 6-8 states); does not provide universal county-level eviction rates. Direct S3 URLs served without registration despite brief noting registration requirement.",
    "tier": 2,
    "status": "complete",
    "notes": "Direct S3 (no auth required); 633 MB total across 3 CSVs + dictionary.",
})

sources.append({
    "source_id": "sundown_towns",
    "source_name": "Loewen Sundown Towns Database (Tougaloo)",
    "url_pulled": "https://justice.tougaloo.edu/sundown-towns/using-the-sundown-towns-database/state-map/",
    "pull_timestamp": now,
    "version_or_vintage": "current as of 2026-05-12 pull",
    "files": collect("historical_mechanism/sundown_towns/*.html"),
    "year_coverage": "historical (varies per town)",
    "geographic_coverage": "captured state-map page only",
    "known_limitations": "The Loewen database is interactive UI-driven; no bulk download endpoint exposed. State-map page captured for provenance; per-town drill-down requires manual UI navigation. For bulk extraction, screen-scrape across all states is required.",
    "tier": 2,
    "status": "partial",
    "notes": "Index page only; bulk data not available without scraping.",
})

# === Tier 3 (documented, not pulled) ===

for sid, name, status_text, url, notes_text in [
    ("nvdrs", "CDC NVDRS (restricted-access)", "substituted_tier_1",
     "https://www.cdc.gov/nvdrs/",
     "Substantially substituted by psx4-wq38 (Tier 1); incident-level requires restricted-access app."),
    ("nibrs", "FBI NIBRS via Crime Data Explorer", "registration_walled",
     "https://api.usa.gov/crime/fbi/cde/",
     "api.data.gov API key required (no account creation per brief)."),
    ("property_tax", "Property tax (national)", "per_state_required",
     "various state-level portals",
     "No unified national source; Tax Foundation summary table is practical proxy."),
    ("bia_reservations", "BIA reservation data", "covered_by_tier_1",
     "https://biamaps.geoplatform.gov/",
     "Already covered by TIGER 2024 AIANNH (Tier 1)."),
]:
    rel_dir_map = {
        "nvdrs": "outcomes/nvdrs",
        "nibrs": "outcomes/nibrs",
        "property_tax": "inequity_features/property_tax",
        "bia_reservations": "geographic/reservation_boundaries",
    }
    sources.append({
        "source_id": sid,
        "source_name": name,
        "url_pulled": url,
        "pull_timestamp": now,
        "version_or_vintage": "n/a (not pulled)",
        "files": collect(f"{rel_dir_map[sid]}/SOURCE_NOTE.md"),
        "year_coverage": "n/a",
        "geographic_coverage": "n/a",
        "known_limitations": notes_text,
        "tier": 3,
        "status": status_text,
        "notes": "See SOURCE_NOTE.md in target dir.",
    })

manifest = {
    "manifest_version": 1,
    "built_at": now,
    "root": str(ROOT).replace("\\", "/"),
    "sources": sources,
}

(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

# Tier 1 status checkpoint
tier1 = [s for s in sources if s["tier"] == 1]
status = {
    "tier": 1,
    "built_at": now,
    "n_sources": len(tier1),
    "complete": sum(1 for s in tier1 if s["status"] == "complete"),
    "partial":  sum(1 for s in tier1 if s["status"] == "partial"),
    "failed":   sum(1 for s in tier1 if s["status"] == "failed"),
    "sources": [{"id": s["source_id"], "status": s["status"], "n_files": len(s["files"]), "total_bytes": sum(f["size_bytes"] for f in s["files"])} for s in tier1],
}
(ROOT / "_agent_status" / "tier_1_complete.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

print(f"manifest.json: {len(sources)} sources")
print(f"tier_1_complete.json: {status['complete']}/{status['n_sources']} complete, {status['partial']} partial")
print(f"total bytes (tier 1): {sum(s['total_bytes'] for s in status['sources']):,}")

# Tier 2 checkpoint
tier2 = [s for s in sources if s["tier"] == 2]
status2 = {
    "tier": 2,
    "built_at": now,
    "n_sources": len(tier2),
    "complete": sum(1 for s in tier2 if s["status"] == "complete"),
    "partial":  sum(1 for s in tier2 if s["status"] == "partial"),
    "failed":   sum(1 for s in tier2 if s["status"] == "failed"),
    "sources": [{"id": s["source_id"], "status": s["status"], "n_files": len(s["files"]), "total_bytes": sum(f["size_bytes"] for f in s["files"])} for s in tier2],
}
(ROOT / "_agent_status" / "tier_2_complete.json").write_text(json.dumps(status2, indent=2), encoding="utf-8")
print(f"tier_2_complete.json: {status2['complete']}/{status2['n_sources']} complete, {status2['partial']} partial")
print(f"total bytes (tier 2): {sum(s['total_bytes'] for s in status2['sources']):,}")
