"""v0.5 Arm A self-replication: scrape CDC WONDER Multiple Cause of Death (MCD-ICD-10)
for firearm deaths county-level, 2014-2018.

CDC WONDER XML API: https://wonder.cdc.gov/controller/datarequest/D76
Database D76 = Multiple Cause of Death, 1999-2020 (the historical file).

Firearm-related ICD-10 codes (matching standard WISQARS firearm definition):
  W32-W34   Accidental discharge of firearm
  X72-X74   Intentional self-harm by firearm
  X93-X95   Assault by firearm
  Y22-Y24   Firearm discharge, undetermined intent
  U01.4     Terrorism involving firearms

Output: per-county firearm-death count 2014-2018 (5-year sum), to merge into
the v0.4 design at the same geography level as the 2019-2023 WISQARS scrape.
"""
import requests, pathlib, time, sys
from xml.etree import ElementTree as ET
import pandas as pd

OUT = pathlib.Path(r"D:/Gun Violence/outcomes/wisqars/scrape_2014_2018_wonder")
OUT.mkdir(parents=True, exist_ok=True)

API = "https://wonder.cdc.gov/controller/datarequest/D76"
HEADERS = {"Content-Type": "application/xml", "Accept": "application/xml"}

# WONDER rate-limit: API requires AT LEAST 15 SECONDS between consecutive requests.
# Using 20 seconds to be safe. First request needs same delay if any other user from
# the same IP recently hit WONDER (the limit is per-IP, not per-session).
WONDER_THROTTLE_SEC = 20

# Firearm ICD-10 codes (UCD = underlying cause of death)
FIREARM_ICD10 = ["W32", "W33", "W34",
                 "X72", "X73", "X74",
                 "X93", "X94", "X95",
                 "Y22", "Y23", "Y24",
                 "*U01.4"]

# Build the WONDER XML query. The XML API is finicky — every "parameter" needs a name
# and value(s), and many "hidden" params must be present even if empty for it to work.
# Reference: https://wonder.cdc.gov/wonder/help/WONDER-API-Documentation.pdf

def build_xml_query(year_start, year_end):
    """Build the XML request payload for D76 (MCD 1999-2020)."""
    icd_values = "\n".join(f"<value>{c}</value>" for c in FIREARM_ICD10)
    year_values = "\n".join(f"<value>{y}</value>" for y in range(year_start, year_end + 1))
    return f"""<request-parameters>
<parameter><name>accept_datause_restrictions</name><value>true</value></parameter>
<parameter><name>B_1</name><value>D76.V9-level2</value></parameter>
<parameter><name>B_2</name><value>*None*</value></parameter>
<parameter><name>B_3</name><value>*None*</value></parameter>
<parameter><name>B_4</name><value>*None*</value></parameter>
<parameter><name>B_5</name><value>*None*</value></parameter>
<parameter><name>F_D76.V1</name>{year_values}</parameter>
<parameter><name>F_D76.V10</name><value>*All*</value></parameter>
<parameter><name>F_D76.V2</name><value>*All*</value></parameter>
<parameter><name>F_D76.V27</name><value>*All*</value></parameter>
<parameter><name>F_D76.V9</name><value>*All*</value></parameter>
<parameter><name>I_D76.V1</name>{year_values}</parameter>
<parameter><name>I_D76.V10</name><value>*All*</value></parameter>
<parameter><name>I_D76.V2</name><value>*All*</value></parameter>
<parameter><name>I_D76.V27</name><value>*All*</value></parameter>
<parameter><name>I_D76.V9</name><value>*All* (The United States)</value></parameter>
<parameter><name>M_1</name><value>D76.M1</value></parameter>
<parameter><name>M_2</name><value>D76.M2</value></parameter>
<parameter><name>M_3</name><value>D76.M3</value></parameter>
<parameter><name>O_aar</name><value>aar_none</value></parameter>
<parameter><name>O_aar_pop</name><value>0000</value></parameter>
<parameter><name>O_age</name><value>D76.V5</value></parameter>
<parameter><name>O_javascript</name><value>on</value></parameter>
<parameter><name>O_location</name><value>D76.V9</value></parameter>
<parameter><name>O_precision</name><value>1</value></parameter>
<parameter><name>O_rate_per</name><value>100000</value></parameter>
<parameter><name>O_show_totals</name><value>false</value></parameter>
<parameter><name>O_timeperiod</name><value>D76.V1</value></parameter>
<parameter><name>O_title</name><value>v05_arm_a_firearm_2014_2018</value></parameter>
<parameter><name>O_ucd</name><value>D76.V4</value></parameter>
<parameter><name>V_D76.V1</name>{year_values}</parameter>
<parameter><name>V_D76.V10</name><value/></parameter>
<parameter><name>V_D76.V11</name><value>*All*</value></parameter>
<parameter><name>V_D76.V12</name><value>*All*</value></parameter>
<parameter><name>V_D76.V17</name><value>*All*</value></parameter>
<parameter><name>V_D76.V19</name><value>*All*</value></parameter>
<parameter><name>V_D76.V2</name><value>*All*</value></parameter>
<parameter><name>V_D76.V20</name><value>*All*</value></parameter>
<parameter><name>V_D76.V21</name><value>*All*</value></parameter>
<parameter><name>V_D76.V22</name><value>*All*</value></parameter>
<parameter><name>V_D76.V23</name><value>*All*</value></parameter>
<parameter><name>V_D76.V24</name><value>*All*</value></parameter>
<parameter><name>V_D76.V25</name><value>*All*</value></parameter>
<parameter><name>V_D76.V27</name><value/></parameter>
<parameter><name>V_D76.V4</name>{icd_values}</parameter>
<parameter><name>V_D76.V5</name><value>*All*</value></parameter>
<parameter><name>V_D76.V51</name><value>*All*</value></parameter>
<parameter><name>V_D76.V52</name><value>*All*</value></parameter>
<parameter><name>V_D76.V6</name><value>00</value></parameter>
<parameter><name>V_D76.V7</name><value>*All*</value></parameter>
<parameter><name>V_D76.V8</name><value>*All*</value></parameter>
<parameter><name>V_D76.V9</name><value/></parameter>
<parameter><name>action-Send</name><value>Send</value></parameter>
<parameter><name>finder-stage-D76.V1</name><value>codeset</value></parameter>
<parameter><name>finder-stage-D76.V2</name><value>codeset</value></parameter>
<parameter><name>finder-stage-D76.V27</name><value>codeset</value></parameter>
<parameter><name>finder-stage-D76.V4</name><value>codeset</value></parameter>
<parameter><name>finder-stage-D76.V9</name><value>codeset</value></parameter>
<parameter><name>stage</name><value>request</value></parameter>
</request-parameters>"""

def parse_xml_response(xml_text):
    """Parse the WONDER XML response into a DataFrame."""
    root = ET.fromstring(xml_text)
    # Find <data-table>
    table = root.find(".//data-table")
    if table is None:
        return None
    rows = []
    for r in table.findall("r"):
        cells = []
        for c in r.findall("c"):
            cells.append({
                "label": c.get("l", ""),
                "value": c.get("v", ""),
                "row_span": c.get("r", ""),
            })
        rows.append(cells)
    return rows

def fetch_year_range(year_start, year_end):
    xml = build_xml_query(year_start, year_end)
    print(f"  POSTing {year_start}-{year_end} query ({len(xml)} bytes)...")
    r = requests.post(API, data=f"request_xml={xml}&accept_datause_restrictions=true",
                       headers={"Content-Type": "application/x-www-form-urlencoded"},
                       timeout=300)
    print(f"  status {r.status_code}  size {len(r.content)} bytes")
    if r.status_code != 200:
        print(f"  FAIL: {r.text[:500]}")
        return None
    out_xml = OUT / f"wonder_response_{year_start}_{year_end}.xml"
    out_xml.write_text(r.text, encoding="utf-8")
    return r.text

print("=== CDC WONDER MCD-ICD-10 firearm deaths county-level 2014-2018 ===\n")
print(f"[1] Initial throttle: sleeping {WONDER_THROTTLE_SEC}s before first request "
      f"(in case of recent IP activity) ...")
time.sleep(WONDER_THROTTLE_SEC)

print("[2] Per-year queries (one per year, with throttle)...")
for yr in range(2014, 2019):
    print(f"  year {yr}:")
    fetch_year_range(yr, yr)
    print(f"  ... throttle sleep {WONDER_THROTTLE_SEC}s ...")
    time.sleep(WONDER_THROTTLE_SEC)

# Inspect first 5000 chars of any response file to see what we got
import glob
files = sorted(OUT.glob("wonder_response_*.xml"))
print(f"\n[2] Response files: {len(files)}")
for f in files[:3]:
    txt = f.read_text(encoding="utf-8")
    print(f"  {f.name}: {len(txt)} bytes")
    # Check for error markers
    if "<error>" in txt.lower() or "<message>" in txt.lower():
        # Show first error
        print(f"    ERROR/MSG in response (first 400 chars):")
        print(f"    {txt[:400]}")
    elif "<data-table>" in txt:
        print(f"    contains <data-table>")
    else:
        print(f"    first 400 chars: {txt[:400]}")

print("\nDONE (parsing deferred to next step)")
