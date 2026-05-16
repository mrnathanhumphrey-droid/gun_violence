"""Scrape Tougaloo sundown towns database for all 50 states.

Source: https://justice.tougaloo.edu/location/<statename>/

For each state page, extracts:
  - town_name
  - is_starred (* in label means "not a suspected sundown town, listed for other reasons")

Outputs:
  D:/Gun Violence/historical_mechanism/sundown_towns/sundown_towns_raw.csv
  - cols: state, town_name, is_starred, town_url
"""
import time, re, pathlib
import requests
import pandas as pd

OUT_DIR = pathlib.Path(r"D:/Gun Violence/historical_mechanism/sundown_towns")
OUT_DIR.mkdir(exist_ok=True)

STATES = [
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut",
    "delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa",
    "kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan",
    "minnesota","mississippi","missouri","montana","nebraska","nevada","new-hampshire",
    "new-jersey","new-mexico","new-york","north-carolina","north-dakota","ohio",
    "oklahoma","oregon","pennsylvania","rhode-island","south-carolina","south-dakota",
    "tennessee","texas","utah","vermont","virginia","washington","west-virginia",
    "wisconsin","wyoming"
]

STATE_ABBR = {
    "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA",
    "colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA",
    "hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA","kansas":"KS",
    "kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD","massachusetts":"MA",
    "michigan":"MI","minnesota":"MN","mississippi":"MS","missouri":"MO","montana":"MT",
    "nebraska":"NE","nevada":"NV","new-hampshire":"NH","new-jersey":"NJ","new-mexico":"NM",
    "new-york":"NY","north-carolina":"NC","north-dakota":"ND","ohio":"OH","oklahoma":"OK",
    "oregon":"OR","pennsylvania":"PA","rhode-island":"RI","south-carolina":"SC",
    "south-dakota":"SD","tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT",
    "virginia":"VA","washington":"WA","west-virginia":"WV","wisconsin":"WI","wyoming":"WY"
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Research scrape for academic study"}

# Town links in each state page. Starred entries have <span class="hsj-ast">*</span>
# nested inside the <a>...</a>, so we capture all inner content (including spans).
TOWN_LINK_RE = re.compile(
    r'<a[^>]+href="(https?://justice\.tougaloo\.edu/sundowntown/[^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL
)

all_rows = []
for state in STATES:
    url = f"https://justice.tougaloo.edu/location/{state}/"
    print(f"[{state}] fetching ...", end=" ", flush=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"FAILED: {e}")
        continue
    text = r.text
    matches = TOWN_LINK_RE.findall(text)
    # De-dup within state
    seen_urls = set()
    n_starred = n_unstarred = 0
    for town_url, inner in matches:
        if town_url in seen_urls: continue
        seen_urls.add(town_url)
        # Starred = nested <span class="hsj-ast"> OR literal * in the visible text
        is_starred = ("hsj-ast" in inner.lower()) or ("*" in inner)
        # Clean name = strip HTML tags + whitespace + *
        clean_name = re.sub(r'<[^>]+>', '', inner).strip().rstrip("*").strip()
        all_rows.append({
            "state": state, "state_abbr": STATE_ABBR[state],
            "town_name": clean_name, "is_starred": is_starred,
            "town_url": town_url
        })
        if is_starred: n_starred += 1
        else: n_unstarred += 1
    print(f"{len(seen_urls)} towns ({n_unstarred} sundown / {n_starred} starred)")
    time.sleep(1)  # gentle throttle

df = pd.DataFrame(all_rows)
out_csv = OUT_DIR / "sundown_towns_raw.csv"
df.to_csv(out_csv, index=False)
print(f"\nWrote {out_csv}: {len(df)} total entries  "
      f"({(~df['is_starred']).sum()} suspected sundown, {df['is_starred'].sum()} starred non-sundown)")
print(f"\nBy state (suspected sundown only):")
print(df[~df['is_starred']].groupby('state_abbr').size().sort_values(ascending=False).head(20).to_string())
