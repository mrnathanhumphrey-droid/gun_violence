"""Fetch NHGIS county race counts for 1870-1890 — the pre-period.

WHY
  The 1900-1950 panel shows sundown counties were ALREADY nearly all-white in 1900
  (median 0.49% Black vs 5.03%). Two readings survive that and the 1900-1950 window
  cannot separate them:

    NEVER-HAD             these counties were always overwhelmingly white; the sundown
                          label records a settled condition rather than an expulsion.
    WINDOW OPENED LATE    Loewen dates much of the racial-cleansing wave to ~1890-1910,
                          so a 1900 baseline is already POST-treatment and finding no
                          decline after it is exactly what you would expect.

  A 1870 baseline sits in front of that wave. If sundown counties held real Black
  populations in 1870-1890 and lost them, the collapses happened before we were looking.

TABLES (pinned from the metadata API; universe checked, not just description)
    1870  1870_cPAX    NT4  Race                  universe=Persons
    1880  1880_cPAX    NT4  Race                  universe=Persons
    1890  1890_cPHAM   NT6  Race/Nativity by Sex  universe=Persons
    +     A00 time series (county) Total Population, 1870/1880/1890

  Verify the delivered codebooks before use. In the 1900-1950 pull, two tables whose
  DESCRIPTION said "Race" turned out to be White/Non-white only or to have universe
  "Persons 75 Years and Over". Description is not sufficient.

    python displacement/fetch_nhgis_preperiod_1870_1890.py
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from ipumspy import IpumsApiClient, AggregateDataExtract, NhgisDataset, TimeSeriesTable

OUT = Path(r"D:/Gun Violence/displacement/data/nhgis_preperiod")
STATE = OUT / "extract_state.json"
DATASETS = [("1870_cPAX", ["NT4"]), ("1880_cPAX", ["NT4"]), ("1890_cPHAM", ["NT6"])]
TST = [("A00", ["1870", "1880", "1890"])]


def main():
    key = os.environ.get("IPUMS_API_KEY")
    if not key:
        print("ERROR: IPUMS_API_KEY not set."); sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    c = IpumsApiClient(key)

    if STATE.exists() and any(OUT.glob("*.zip")):
        print("already downloaded; nothing to do."); return

    ex = AggregateDataExtract(
        collection="nhgis",
        description="Displacement paper: county race counts 1870-1890 (pre-period)",
        datasets=[NhgisDataset(name=n, data_tables=t, geog_levels=["county"])
                  for n, t in DATASETS],
        time_series_tables=[TimeSeriesTable(name=n, geog_levels=["county"], years=y)
                            for n, y in TST],
        data_format="csv_header",
    )
    print("submitting pre-period extract ...")
    for n, t in DATASETS:
        print(f"   {n:<12} {t}")
    c.submit_extract(ex)
    STATE.write_text(json.dumps({"extract_id": ex.extract_id, "collection": "nhgis",
                                 "submitted": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "datasets": DATASETS}, indent=2))
    print(f"submitted. extract id = {ex.extract_id}")
    c.wait_for_extract(ex, collection="nhgis")
    c.download_extract(ex, download_dir=OUT)
    print(f"downloaded -> {OUT}")
    for f in sorted(OUT.iterdir()):
        print(f"   {f.name}  {f.stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
