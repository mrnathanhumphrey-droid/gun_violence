"""Tier 3 fetch (stretch): NVDRS, NIBRS, property tax, BIA.

Per brief: "Tier 2 and Tier 3 failures: log in manifest with reason,
continue." Per brief: do NOT create accounts.

Status:
- NVDRS:    publicly walled; substantially substituted by CDC psx4-wq38 in Tier 1.
- NIBRS:    api.usa.gov/crime/fbi/cde requires api.data.gov key (registration);
            ICPSR/NACJD requires academic registration. Skipped per brief constraint.
- Property: no unified national source; per-state assessor portals required.
- BIA:      reservation boundaries already covered by TIGER 2024 AIANNH (Tier 1)
            which IS the canonical Census-sourced reservation polygon set.

This script writes per-source documentation files capturing what's blocking
each Tier 3 source and where the data would come from with proper access.
"""
import json, pathlib, datetime

ROOT = pathlib.Path(r"D:/Gun Violence")

# Per-source documentation
DOCS = {
    "outcomes/nvdrs/SOURCE_NOTE.md": """# NVDRS source note — 2026-05-12

The CDC National Violent Death Reporting System (NVDRS) public files are
narrow (state-level aggregates only) and the incident-level Restricted
Access Database requires a formal CDC application + IRB approval.

**Substituted for Tier 1**: `outcomes/wisqars/cdc_psx4_wq38/` already
contains county-level firearm + violence death counts and rates derived
from the same NCHS underlying mortality data that feeds NVDRS state
totals. For most cross-geography research designs that don't require
narrative incident-level circumstances, `psx4-wq38` is sufficient.

If incident-level circumstances are required (perpetrator-victim
relationship, weapon detail, narrative free-text), the NVDRS Restricted
Access Database application is at:
  https://www.cdc.gov/nvdrs/about/restricted-access-database.html

Status: substituted in Tier 1; restricted-access tier deferred.
""",
    "outcomes/nibrs/SOURCE_NOTE.md": """# NIBRS source note — 2026-05-12

The FBI Crime Data Explorer (CDE) at the old `cde.ucr.cjis.gov` and
`crime-data-explorer.fr.cloud.gov` endpoints has been migrated.
The current programmatic endpoint is **api.usa.gov/crime/fbi/cde/**,
which **requires an api.data.gov API key** (free, registration-walled).

Sample query (with key): `https://api.usa.gov/crime/fbi/cde/agencies?API_KEY=<key>`

ICPSR's National Archive of Criminal Justice Data (NACJD) hosts the
canonical NIBRS bulk archive at series #128 (1991–latest), but downloads
require academic registration.

Per brief: do NOT create accounts. Skipped.

If the analysis phase determines NIBRS is load-bearing:
1. Request api.data.gov key (instant, free): https://api.data.gov/signup/
2. Or request ICPSR account (academic only): https://www.icpsr.umich.edu/web/NACJD/series/128

Known coverage gaps once acquired: many large jurisdictions did not
report NIBRS in 2021 (Florida, NY, Illinois). Coverage improved 2022+.

Status: registration-walled; skipped.
""",
    "inequity_features/property_tax/SOURCE_NOTE.md": """# Property tax source note — 2026-05-12

There is no unified national property-tax dataset at the
parcel/assessment level. Property-tax data is structurally per-state and
often per-county. Aggregators (ATTOM, CoreLogic) license commercially.

Public per-state options (a sample):
- California: https://www.sco.ca.gov/ardtax_property_tax.html (state controller)
- Texas: https://comptroller.texas.gov/taxes/property-tax/ (state comptroller)
- Florida: https://floridarevenue.com/property/Pages/DataPortal.aspx (DOR)
- Illinois: https://tax.illinois.gov/programs/proptax.html (DOR)
- New York: https://orps.tax.ny.gov/ (state ORPTS)
- Massachusetts: https://www.mass.gov/division-of-local-services-municipal-databank

State-level summary aggregates (state-by-state effective rates only):
- Tax Foundation property tax tables: https://taxfoundation.org/data/all/state/property-taxes-by-state/
- Lincoln Institute Significant Features of the Property Tax database

Per brief: state-level summaries acceptable; per-state acquisition flagged
as a separate workstream.

Status: not pulled; documented as requiring per-state per-jurisdiction
acquisition. For research-design purposes the Tax Foundation summary
table is the most practical immediate proxy.
""",
    "geographic/reservation_boundaries/SOURCE_NOTE.md": """# Reservation boundaries source note — 2026-05-12

**Tier 3 BIA reservation data is already covered by Tier 1's TIGER
2024 AIANNH file** (American Indian / Alaska Native / Native Hawaiian
areas). The Census Bureau's AIANNH polygons are sourced from BIA's
own boundary information and are the canonical reservation-boundary
dataset used in federal research.

File: `geographic/reservation_boundaries/tl_2024_us_aiannh.zip` (9 MB).

The BIA's own GIS portal (biamaps.geoplatform.gov) hosts equivalent
shapefiles with different metadata fields — most research uses the
Census AIANNH version for consistency with other Census-Bureau-aligned
geographic identifiers.

For BIA-specific economic indicators (tribal enrollment, IHS service
population, BIE school data), see:
- IHS open data: https://www.ihs.gov/data/ (free, programmatic)
- BIE schools (NCES has BIE in standard CCD via "operational status" code)
- Tribal-specific socioeconomic data often requires direct tribal-government
  outreach.

Status: equivalent data already in Tier 1 (AIANNH from TIGER).
""",
}

now = datetime.datetime.now(datetime.UTC).isoformat()
for rel, content in DOCS.items():
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"  wrote {rel}")

# Tier 3 checkpoint
status = {
    "tier": 3,
    "built_at": now,
    "n_sources": 4,
    "complete": 0,
    "partial": 0,
    "documented_skipped": 4,
    "failed": 0,
    "notes": "All 4 Tier 3 sources documented as: registration-walled (NIBRS), "
             "substituted in Tier 1 (NVDRS via psx4-wq38, BIA via TIGER AIANNH), "
             "or requires per-state acquisition (property tax).",
    "sources": [
        {"id": "nvdrs", "status": "substituted_tier_1", "notes": "psx4-wq38 covers same NCHS-derived totals at county level."},
        {"id": "nibrs", "status": "registration_walled", "notes": "Requires api.data.gov key or ICPSR registration."},
        {"id": "property_tax", "status": "per_state_required", "notes": "No unified national source; Tax Foundation summaries available as proxy."},
        {"id": "bia_reservations", "status": "covered_by_tier_1", "notes": "TIGER 2024 AIANNH is canonical."},
    ],
}
(ROOT / "_agent_status" / "tier_3_complete.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
print(f"\nTier 3 documented: 4 sources, 0 pulled, 4 documented-skipped (per brief constraints)")
