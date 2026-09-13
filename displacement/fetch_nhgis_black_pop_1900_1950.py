"""Fetch NHGIS county-level race counts, 1900-1950, for the displacement origin-side test.

WHY
  The paper's thesis is that sundown-town exclusion and HOLC redlining are two ends of one
  DISPLACEMENT: people excluded from small towns were concentrated into graded urban
  neighbourhoods. The county-attribute models cannot see this because a flow is not a
  property of either endpoint.

  Individual linked origin->destination is NOT obtainable: IPUMS birthplace is state-level
  for US-born, and the 1940 "residence in 1935" item is state-level too. So the flow is
  established by DEMOGRAPHIC ACCOUNTING instead:

    origin        do sundown counties lose / fail to gain Black population 1900-1950,
                  relative to same-state non-sundown counties?
    destination   do HOLC-graded city counties absorb it over the same decades?
    commensurate  are the magnitudes consistent?

  This script fetches the origin-side inputs. It establishes displacement as an aggregate
  accounting identity, NOT as linked individual movement, and it tests a trajectory across
  the era rather than a response to a dated event -- the Rigby/Loewen sundown data carries
  no founding dates, so no event study is possible.

TABLES (pinned from the NHGIS metadata API, 2026-09-10)
  NHGIS has NO harmonised race time series before 1970 -- only A00 (Total Population,
  1790-2020) and A08 (Persons by Sex) reach this era. Race must therefore come from the raw
  decennial datasets, on ORIGINAL county boundaries, and the boundary crosswalk is real work
  downstream. A00 is requested alongside as a consistent-boundary denominator and as a
  cross-check on the raw county totals.

    1900  1900_cPHAM   NT7   Non-White Population by Race by Sex   AZ3003 / AZ3004
    1910  1910_cPHA    NT11  Race by Sex                           A30003 / A30004
    1920  1920_cPHAM   NT5   Race/Nativity by Sex                  A8L005 / A8L006
    1930  1930_cAge40  NT6   Race by Sex                           BC7003 / BC7004
    1940  1940_cAge    NT6   Race by Sex                           BV2003 / BV2004
    1950  1950_cPHA    NT6   Sex by Race/Nativity                  B3P003 / B3P007
    +     A00 time series (county) Total Population 1790-2020, harmonised boundaries

  Verified against the delivered codebooks: all six years carry an explicit Black count with
  universe = Persons (1900's universe is Non-White Persons, which is the table's own scope,
  not a subpopulation restriction on the Black count). 1950's two codes are non-adjacent
  because that table is Sex >> Race/Nativity with four race categories per sex.

  Table structure differs year to year (Race by Sex vs Race vs Race/Nativity), so
  harmonising to one "Black population per county per year" column requires reading each
  codebook. That is the next step, not this one.

  Idempotent: records the submitted extract id and will not resubmit if one is pending or
  already downloaded.

    python displacement/fetch_nhgis_black_pop_1900_1950.py
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from ipumspy import IpumsApiClient, AggregateDataExtract, NhgisDataset, TimeSeriesTable

OUT = Path(r"D:/Gun Violence/displacement/data/nhgis")
STATE = OUT / "extract_state.json"

DATASETS = [
    ("1900_cPHAM",  ["NT7"]),    # Non-White Population by Race by Sex  -> AZ3003/4 Negro M/F
    ("1910_cPHA",   ["NT11"]),   # Race by Sex                          -> A30003/4 Negro M/F
    ("1920_cPHAM",  ["NT5"]),    # Race/Nativity by Sex                 -> A8L005/6 Negro M/F
    ("1930_cAge40", ["NT6"]),    # Race by Sex        (universe Persons)
    ("1940_cAge",   ["NT6"]),    # Race by Sex                          -> BV2003/4 Negro M/F
    ("1950_cPHA",   ["NT6"]),    # Sex by Race/Nativity (universe Persons) -> Negro M/F
]
# Two picks were CORRECTED after reading the extract-1 codebooks -- description alone is not
# enough, the UNIVERSE has to be checked:
#   1930 NT11 "Race"  gave only White/Non-white (no Black count)            -> NT6 "Race by Sex"
#   1950 NT14 "Race"  had universe "Persons 75 Years and Over" (elderly!)
#   1950 NT20 "Race by Sex" then gave only White/Non-white -> 1950_cPHA NT6 has Negro M/F
# Extract 1 (nhgis0010) is SUPERSEDED by this one; do not mix them.
TST = [("A00", ["1900", "1910", "1920", "1930", "1940", "1950"])]


def main():
    key = os.environ.get("IPUMS_API_KEY")
    if not key:
        print("ERROR: IPUMS_API_KEY not set."); sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    c = IpumsApiClient(key)

    if STATE.exists():
        st = json.loads(STATE.read_text())
        eid = st.get("extract_id")
        try:
            status = c.extract_status(eid, collection="nhgis")
        except Exception as e:
            status = f"unknown ({e})"
        print(f"prior extract {eid} status: {status}")
        if status == "completed" and any(OUT.glob("*.zip")):
            print("already downloaded; nothing to do."); return
        if status in ("queued", "started", "produced"):
            print("still running; re-run this script later to download."); return
        if status == "completed":
            print("completed but not downloaded -- downloading now ...")
            c.download_extract(_reload(c, eid), download_dir=OUT)
            print(f"downloaded -> {OUT}"); return

    ex = AggregateDataExtract(
        collection="nhgis",
        description="Displacement paper: county race counts 1900-1950 + A00 total pop",
        datasets=[NhgisDataset(name=n, data_tables=t, geog_levels=["county"])
                  for n, t in DATASETS],
        time_series_tables=[TimeSeriesTable(name=n, geog_levels=["county"], years=y)
                            for n, y in TST],
        data_format="csv_header",
    )
    print("submitting NHGIS extract ...")
    for n, t in DATASETS:
        print(f"   {n:<12} {t}")
    print(f"   time series  {[n for n, _ in TST]}  (county, harmonised)")

    c.submit_extract(ex)
    eid = ex.extract_id
    STATE.write_text(json.dumps({"extract_id": eid, "collection": "nhgis",
                                 "submitted": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "datasets": DATASETS, "time_series": TST}, indent=2))
    print(f"submitted. extract id = {eid}   (state -> {STATE})")

    print("waiting for it to build (this can take several minutes) ...")
    c.wait_for_extract(ex, collection="nhgis")
    c.download_extract(ex, download_dir=OUT)
    print(f"downloaded -> {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"   {f.name}  {f.stat().st_size/1e6:.1f} MB")


def _reload(c, eid):
    return c.get_extract_by_id(eid, collection="nhgis")


if __name__ == "__main__":
    main()
