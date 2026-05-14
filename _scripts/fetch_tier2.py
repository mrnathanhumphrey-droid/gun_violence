"""Tier 2 fetch: HOLC redlining, Eviction Lab, Sundown Towns."""
import os, time, json, pathlib, requests

ROOT = pathlib.Path(r"D:/Gun Violence")

TIER2 = [
    # HOLC Mapping Inequality (Richmond DSL)
    ("historical_mechanism/holc_redlining/mappinginequality.json",
     "https://dsl.richmond.edu/panorama/redlining/static/mappinginequality.json"),
    ("historical_mechanism/holc_redlining/fullshpfile.zip",
     "https://dsl.richmond.edu/panorama/redlining/static/fullshpfile.zip"),
    ("historical_mechanism/holc_redlining/citiesData.zip",
     "https://dsl.richmond.edu/panorama/redlining/static/citiesData.zip"),
    # Eviction Lab (direct S3, no registration on direct file URLs)
    ("inequity_features/eviction_lab/data_dictionary_weekly_monthly.xlsx",
     "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/data_dictionary_weekly_monthly.xlsx"),
    ("inequity_features/eviction_lab/all_sites_weekly_2020_2021.csv",
     "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_weekly_2020_2021.csv"),
    ("inequity_features/eviction_lab/all_sites_monthly_2020_2021.csv",
     "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/all_sites_monthly_2020_2021.csv"),
    ("inequity_features/eviction_lab/allstates_weekly_2020_2021.csv",
     "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/allstates_weekly_2020_2021.csv"),
]

results = {}
for rel, url in TIER2:
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        results[rel] = "skip"
        print(f"  SKIP {rel}")
        continue
    try:
        r = requests.get(url, timeout=120, stream=True)
        if r.status_code == 200:
            with open(target, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            sz = target.stat().st_size
            results[rel] = f"ok ({sz:,} bytes)"
            print(f"  {rel}: {sz:,} bytes")
        else:
            results[rel] = f"http {r.status_code}"
            print(f"  {rel}: HTTP {r.status_code}")
    except Exception as e:
        results[rel] = f"err {e}"
        print(f"  {rel}: ERR {e}")
    time.sleep(0.3)

# Sundown towns: tougaloo site, check
sundown_url = "https://justice.tougaloo.edu/sundown-towns/using-the-sundown-towns-database/state-map/"
try:
    r = requests.get(sundown_url, timeout=30)
    (ROOT / "historical_mechanism/sundown_towns/state_map_page.html").write_text(r.text, encoding="utf-8")
    results["historical_mechanism/sundown_towns/state_map_page.html"] = f"ok ({len(r.text)} chars; HTML page only, no bulk download)"
    print(f"  sundown page: {len(r.text)} chars")
except Exception as e:
    results["sundown_towns"] = f"err {e}"

(ROOT / "provenance" / "tier2_results.json").write_text(json.dumps(results, indent=2))
print("\nTier 2 DONE")
print(json.dumps(results, indent=2))
