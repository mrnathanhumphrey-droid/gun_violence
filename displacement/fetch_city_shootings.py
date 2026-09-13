"""WAVE 1 OUTCOME FETCHERS — one cache + one manifest per city.

Governed by PRE_REG_MULTICITY_2026_09_11.md. Nothing here computes a rate; this file
only acquires outcome data and records, in an auditable manifest, exactly what was
acquired and under which case definition.

TWO RULES THIS FILE ENFORCES

  1. A FAILED FETCH RECORDS `MISSING`, NEVER 0.
     A city that errors writes a manifest with status="FAILED" and NO parquet. The
     design runner must treat an absent city as missing, never as a city with zero
     shootings. (`except: -> 0` has shipped fabricated data in three prior arcs.)

  2. DERIVED CASE DEFINITIONS ARE ENUMERATED AND WRITTEN BEFORE ANY RATE EXISTS.
     Pre-reg §4.3 leaves two case definitions as derivation rules rather than exact
     value sets: Los Angeles (`weapon_used_cd`) and Seattle (`shooting_type_group`).
     Both are enumerated from the LIVE schema here, the retained AND rejected values
     are printed and written to the manifest, and only then are rows fetched. No code
     range is asserted from memory anywhere in this file.

STANDARD OUTPUT SCHEMA  displacement/data/cities/<slug>.parquet
    city   str        unit label used by the design runner
    date   datetime64 event date
    lat    float64    WGS84
    lon    float64    WGS84

    python displacement/fetch_city_shootings.py            # all wave 1
    python displacement/fetch_city_shootings.py chicago philadelphia
    python displacement/fetch_city_shootings.py --force    # ignore cache
"""
from __future__ import annotations
import sys, io, json, time, warnings
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, requests

ROOT = Path(r"D:/Gun Violence")
OUT = ROOT / "displacement/data/cities"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research)"}
PRIMARY = ("2019-01-01", "2023-12-31")     # pre-reg §5.3

# US bounding box — a coordinate outside this is a parse error, not a location
LAT_RANGE, LON_RANGE = (17.0, 72.0), (-180.0, -65.0)


# ====================================================================== helpers
def get(url, params=None, tries=6, timeout=180):
    """GET with backoff. Raises on exhaustion — callers turn that into MISSING."""
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}: {r.text[:150]}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url} :: {last}")


def socrata_pages(url, params, page=50000, cap=4_000_000):
    """Page a Socrata resource on a stable :id order."""
    out, off = [], 0
    while off < cap:
        p = dict(params)
        p.update({"$limit": page, "$offset": off, "$order": ":id"})
        j = get(url, p).json()
        if not j:
            break
        out.append(pd.DataFrame(j))
        got = len(j)
        off += got
        if off % 200000 == 0:
            print(f"      ... {off:,}")
        if got < page:
            break
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def ags_pages(layer, where, fields, page=None):
    """Page an ArcGIS FeatureServer layer by resultOffset, attributes only."""
    meta = get(layer, {"f": "json"}).json()
    page = page or min(int(meta.get("maxRecordCount", 1000) or 1000), 2000)
    out, off = [], 0
    while True:
        j = get(layer + "/query", {"where": where, "outFields": ",".join(fields),
                                   "returnGeometry": "false", "resultOffset": off,
                                   "resultRecordCount": page, "f": "json"}).json()
        if "error" in j:
            raise RuntimeError(f"ArcGIS error: {str(j['error'])[:200]}")
        f = j.get("features", [])
        if not f:
            break
        out.append(pd.DataFrame([x["attributes"] for x in f]))
        off += len(f)
        if off % 20000 == 0:
            print(f"      ... {off:,}")
        if not j.get("exceededTransferLimit") and len(f) < page:
            break
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def epoch_ms(s):
    return pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", errors="coerce")


def finalize(df, city, man):
    """Coerce to the standard schema, sanity-check coordinates, record provenance."""
    n_raw = len(df)
    d = df.copy()

    # NON-NUMERIC COORDINATE TOKENS ARE SUPPRESSION, NOT NOISE. Seattle publishes the
    # literal string "REDACTED" for ~10% of shootings. That is a deliberate, almost
    # certainly non-random withholding of location, and it must appear in the manifest
    # so it can be disclosed -- the same class of defect as the CDC `-999` that silently
    # deleted 639 counties from an earlier analysis in this project.
    raw_lat = d["lat"].astype(str)
    unparsed = raw_lat[pd.to_numeric(d["lat"], errors="coerce").isna()]
    man["suppressed_coord_tokens"] = {str(k): int(v) for k, v in
                                      unparsed.value_counts().head(5).items()}
    man["n_suppressed_coord"] = int(len(unparsed))

    d["lat"] = pd.to_numeric(d["lat"], errors="coerce")
    d["lon"] = pd.to_numeric(d["lon"], errors="coerce")
    d["date"] = pd.to_datetime(d["date"], errors="coerce")

    n_nodate = int(d.date.isna().sum())
    n_nogeo = int(d.lat.isna().sum() | d.lon.isna().sum())
    # A LARGE SILENT DROP IS A BUG UNTIL PROVEN OTHERWISE. Boston lost an entire year
    # (1,975 rows, every 2023+ shooting) to a datetime-format mismatch while the fetch
    # still printed OK. Anything over 10% now announces itself.
    for lab, k in (("unparseable dates", n_nodate), ("missing coordinates", n_nogeo)):
        if n_raw and k / n_raw > 0.10:
            print(f"      !! {city}: {k:,}/{n_raw:,} rows ({100*k/n_raw:.1f}%) dropped for "
                  f"{lab} — CHECK THIS IS REAL, not a parse failure")
    d = d.dropna(subset=["lat", "lon", "date"])

    # NUMERIC MISSING-LOCATION SENTINELS: (0,0) in Baltimore (3.2%) and LAPD,
    # (-1,-1) in Seattle. These are not coordinates. Counted and recorded, never silent.
    zero = (((d.lat == 0) & (d.lon == 0)) | ((d.lat == -1) & (d.lon == -1)))
    n_zero = int(zero.sum())
    d = d[~zero]

    # A coordinate outside the US box is a parse failure, not a location. Before failing,
    # test whether the two columns are simply SWAPPED -- NYC's live shooting file ships
    # longitude in the column named `latitude`. Detected rather than hard-coded, so that
    # if the publisher later fixes the file this does not silently re-break it.
    def inbox(la, lo):
        return float((la.between(*LAT_RANGE) & lo.between(*LON_RANGE)).mean()) if len(la) else 1.0
    f_asis, f_swap = inbox(d.lat, d.lon), inbox(d.lon, d.lat)
    swapped = False
    if f_swap > f_asis and f_swap > 0.95:
        d = d.rename(columns={"lat": "lon", "lon": "lat"})
        swapped = True
        print(f"      !! {city}: lat/lon columns are SWAPPED at source "
              f"(in-box as-is {f_asis:.3f} -> swapped {f_swap:.3f}). Corrected and recorded.")

    bad = ~(d.lat.between(*LAT_RANGE) & d.lon.between(*LON_RANGE))
    n_bad = int(bad.sum())
    if n_bad and n_bad / max(len(d), 1) > 0.02:
        raise RuntimeError(f"{city}: {n_bad:,}/{len(d):,} coords outside the US box "
                           f"(in-box as-is {f_asis:.3f}, swapped {f_swap:.3f}) — "
                           f"coordinates are not WGS84 degrees")
    d = d[~bad]
    man.update(n_dropped_zero_coord=n_zero, coord_swap_applied=swapped,
               inbox_frac_asis=round(f_asis, 4), inbox_frac_swapped=round(f_swap, 4))

    d["city"] = city
    d = d[["city", "date", "lat", "lon"]].reset_index(drop=True)

    inwin = int(d.date.between(*PRIMARY).sum())
    # cheap precision signal; the binding test is §4.7 in the design runner
    uniq = d.groupby(["lat", "lon"]).size()
    man.update(dict(
        status="OK", n_raw=n_raw, n_dropped_nodate=n_nodate, n_dropped_nogeo=n_nogeo,
        n_dropped_offbox=n_bad, n_final=len(d),
        date_min=str(d.date.min().date()), date_max=str(d.date.max().date()),
        n_primary_window=inwin,
        unique_coords=int(len(uniq)), unique_coord_ratio=round(len(uniq) / max(len(d), 1), 4),
        modal_dup_count=int(uniq.max()) if len(uniq) else 0,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return d


def write(city, slug, d, man):
    d.to_parquet(OUT / f"{slug}.parquet", index=False)
    (OUT / f"{slug}_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    print(f"   OK  {city:<14} n={man['n_final']:>7,}  "
          f"{man['date_min']}..{man['date_max']}  "
          f"in-window={man['n_primary_window']:,}  "
          f"uniq-coord={man['unique_coord_ratio']:.3f}  modal-dup={man['modal_dup_count']}")


def fail(city, slug, man, err):
    """RULE 1: a failed fetch records MISSING, never 0."""
    man.update(dict(status="FAILED", error=str(err)[:500], n_final="MISSING",
                    fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds")))
    (OUT / f"{slug}_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    p = OUT / f"{slug}.parquet"
    if p.exists():
        p.unlink()                       # never leave a stale cache beside a FAILED manifest
    print(f"   !! {city:<14} FAILED — recorded MISSING, not 0\n      {str(err)[:300]}")


# ====================================================================== adapters
def chicago():
    """Pre-reg §4.3: gunshot_injury_i = 'YES'; unit = VICTIM."""
    man = dict(city="Chicago", unit="victim", source_kind="socrata",
               source_url="https://data.cityofchicago.org/resource/gumc-mgzr.json",
               case_definition="gunshot_injury_i = 'YES'")
    src = ROOT / "displacement/data/chicago_shootings.parquet"
    if src.exists():
        d = pd.read_parquet(src)
        man["note"] = "re-used existing displacement/data/chicago_shootings.parquet"
    else:
        d = socrata_pages(man["source_url"],
                          {"$select": "date,latitude,longitude,gunshot_injury_i"}, page=5000)
        d = d[d.gunshot_injury_i.eq("YES")]
    return finalize(d.rename(columns={"latitude": "lat", "longitude": "lon"}),
                    "Chicago", man), man


def philadelphia():
    """Pre-reg §4.3: all rows of the shootings table; unit = VICTIM."""
    man = dict(city="Philadelphia", unit="victim", source_kind="carto",
               source_url="https://phl.carto.com/api/v2/sql",
               case_definition="all rows of table `shootings` (the table IS the case definition)")
    q = "SELECT date_, point_x, point_y, fatal FROM shootings"
    j = get(man["source_url"], {"q": q}).json()
    d = pd.DataFrame(j["rows"])
    man["n_source_rows"] = len(d)
    return finalize(d.rename(columns={"date_": "date", "point_y": "lat", "point_x": "lon"}),
                    "Philadelphia", man), man


def nyc(fid="5ucz-vwe8", label="New York"):
    """Pre-reg §4.3/§4.5: primary = live file 5ucz-vwe8; unit = INCIDENT.
    833y-fsy8 is fetched separately as the mandatory robustness arm."""
    url = f"https://data.cityofnewyork.us/resource/{fid}.json"
    man = dict(city=label, unit="incident", source_kind="socrata", source_url=url,
               case_definition=f"all rows of {fid} (the file IS the case definition)",
               prereg_note="§4.5 — the two NYPD files differ by a uniform ~22% level shift; "
                           "both are fetched, RRs compared, divergence >0.10 in log RR means "
                           "the difference is not spatially neutral")
    d = socrata_pages(url, {"$select": "occur_date,latitude,longitude,boro"})
    return finalize(d.rename(columns={"occur_date": "date", "latitude": "lat",
                                      "longitude": "lon"}), label, man), man


def detroit():
    """Pre-reg §4.6: charge_des = 'NON-FATAL SHOOTING' ONLY; unit = INCIDENT.
    Homicides live in a separate field and are NOT all firearm — including them would
    import non-firearm deaths into a firearm outcome."""
    layer = ("https://services2.arcgis.com/RQcpPaCpMAXzUI5g/arcgis/rest/services/"
             "RMS_Crime_Incidents/FeatureServer/0")
    man = dict(city="Detroit", unit="incident", source_kind="arcgis", source_url=layer,
               case_definition="charge_des = 'NON-FATAL SHOOTING'",
               prereg_note="§4.6 — non-fatal only; Detroit's definition is therefore "
                           "non-fatal where Chicago/Philadelphia include fatalities. "
                           "Permitted under §5.1 because the RR is within-city.")
    d = ags_pages(layer, "charge_des = 'NON-FATAL SHOOTING'",
                  ["incident_t", "ibr_date", "latitude", "longitude", "charge_des"])
    if not len(d):
        raise RuntimeError("no rows returned for charge_des = 'NON-FATAL SHOOTING'")
    # prefer the incident timestamp, fall back to the IBR date
    dt = epoch_ms(d["incident_t"]) if "incident_t" in d else pd.Series(pd.NaT, index=d.index)
    if dt.isna().mean() > 0.5 and "ibr_date" in d:
        dt = epoch_ms(d["ibr_date"])
        man["date_field"] = "ibr_date"
    else:
        man["date_field"] = "incident_t"
    d["date"] = dt
    return finalize(d.rename(columns={"latitude": "lat", "longitude": "lon"}),
                    "Detroit", man), man


def baltimore():
    """Pre-reg §4.3: Weapon in the enumerated firearm set; unit = OFFENSE."""
    layer = ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/"
             "Part1_Crime/FeatureServer/0")
    guns = ["FIREARM", "HANDGUN", "RIFLE", "SHOTGUN", "OTHER_FIREARM",
            "AUTOMATIC_FIREARM", "AUTOMATIC_HANDGUN", "AUTOMATIC_RIFLE",
            "AUTOMATIC_OTHER_FIREARM"]
    where = "Weapon IN (" + ",".join(f"'{g}'" for g in guns) + ")"
    man = dict(city="Baltimore", unit="offense", source_kind="arcgis", source_url=layer,
               case_definition=where, firearm_values=guns)
    d = ags_pages(layer, where, ["CrimeDateTime", "Latitude", "Longitude", "Weapon",
                                 "Description"])
    if not len(d):
        raise RuntimeError("no rows returned for the firearm Weapon set")
    d["date"] = epoch_ms(d["CrimeDateTime"])
    man["weapon_breakdown"] = d.Weapon.value_counts().to_dict()
    return finalize(d.rename(columns={"Latitude": "lat", "Longitude": "lon"}),
                    "Baltimore", man), man


# ---------------------------------------------------------------- derivation rules
FIREARM_WORDS = ("PISTOL", "REVOLVER", "RIFLE", "SHOTGUN", "FIREARM", "GUN",
                 "AUTOMATIC WEAPON", "UZI", "MAC-10", "MAC-11", "AK-47", "M1-1",
                 "ASSAULT WEAPON", "CARBINE", "HECKLER & KOCH")
# imitation, non-lethal and non-firearm "guns". A rule that kept TOY GUN, BB GUN or
# STUN GUN would not be a firearm case definition.
#   NOTE: "HECKLER" must NOT appear here. It vetoed HECKLER & KOCH 91/93 SEMIAUTOMATIC
#   ASSAULT RIFLE on a first pass -- those are real rifles. Match on the non-lethal
#   MECHANISM, never on a substring that can occur inside a manufacturer's name.
NOT_REALLY_A_GUN = ("TOY", "SIMULATED", "AIR PISTOL", "AIR/", "BB GUN", "PELLET",
                    "STARTER PISTOL", "FLARE", "TEAR GAS", "STUN GUN", "TASER",
                    "GLUE GUN", "NAIL GUN", "SPRAY", "MACE/", "DEMAND NOTE",
                    "BOW AND ARROW", "UNKNOWN WEAPON", "OTHER WEAPON", "VERBAL",
                    "PHYSICAL PRESENCE", "STRONG-ARM")


def classify_weapons(values):
    """Word-rule over the LIVE value list. Returns (keep, reject) — both recorded.
    Imitation and non-lethal 'guns' are rejected explicitly; a rule that kept TOY GUN
    or BB GUN would not be a firearm case definition."""
    keep, rej = [], []
    for v in values:
        s = str(v).upper()
        hit = any(w in s for w in FIREARM_WORDS)
        veto = any(w in s for w in NOT_REALLY_A_GUN)
        (keep if (hit and not veto) else rej).append(v)
    return keep, rej


def los_angeles():
    """Pre-reg §4.3: DERIVATION RULE — enumerate weapon_desc from the live schema,
    classify, record BOTH the retained and rejected sets, then fetch."""
    srcs = [("2nrs-mtv8", "https://data.lacity.org/resource/2nrs-mtv8.json"),
            ("63jg-8b9z", "https://data.lacity.org/resource/63jg-8b9z.json")]
    man = dict(city="Los Angeles", unit="offense", source_kind="socrata",
               source_url=[u for _, u in srcs],
               case_definition="DERIVED: weapon_desc denoting a real firearm",
               prereg_note="§4.3 derivation rule + §4.7 — LAPD rounds coordinates to the "
                           "hundred block; the precision test decides which bands LA enters")
    # 1. enumerate the live value list
    vals = set()
    for _, u in srcs:
        j = get(u, {"$select": "weapon_desc,weapon_used_cd", "$group": "weapon_desc,weapon_used_cd",
                    "$limit": 1000}).json()
        vals |= {(r.get("weapon_used_cd"), r.get("weapon_desc")) for r in j
                 if r.get("weapon_desc")}
    descs = sorted({d for _, d in vals})
    keep, rej = classify_weapons(descs)
    codes = sorted({c for c, d in vals if d in set(keep) and c})
    man.update(weapon_desc_all=descs, weapon_desc_kept=keep,
               weapon_desc_rejected=rej, weapon_used_cd_kept=codes)
    print(f"      enumerated {len(descs)} weapon_desc values -> kept {len(keep)}, "
          f"rejected {len(rej)}; {len(codes)} codes")
    print(f"      KEPT    : {keep}")
    print(f"      REJECTED: {rej}")
    if not codes:
        raise RuntimeError("weapon classification retained no codes")
    # 2. fetch only those rows
    inlist = "(" + ",".join(f"'{c}'" for c in codes) + ")"
    parts = []
    for fid, u in srcs:
        print(f"      fetching {fid} ...")
        p = socrata_pages(u, {"$select": "date_occ,lat,lon,weapon_used_cd,weapon_desc",
                              "$where": f"weapon_used_cd IN {inlist}"})
        man[f"n_{fid}"] = len(p)
        parts.append(p)
    d = pd.concat(parts, ignore_index=True)
    d = d.rename(columns={"date_occ": "date"})
    # LAPD writes unknown locations as exactly (0,0); finalize() drops and records them.
    return finalize(d, "Los Angeles", man), man


def seattle():
    """Pre-reg §4.3: DERIVATION RULE — enumerate shooting_type_group, classify, record."""
    u = "https://data.seattle.gov/resource/tazs-3rd5.json"
    man = dict(city="Seattle", unit="offense", source_kind="socrata", source_url=u,
               case_definition="DERIVED: shooting_type_group denoting an actual firearm discharge")
    j = get(u, {"$select": "shooting_type_group,count(*) as n",
                "$group": "shooting_type_group", "$limit": 500}).json()
    tab = {r.get("shooting_type_group"): int(r["n"]) for r in j}
    vals = [v for v in tab if v]
    # WHITELIST, not a blacklist. A blacklist had to anticipate every non-shooting label
    # and did not: it kept '-', which is 1,549,610 rows of ALL OTHER CRIME. Seattle's
    # outcome would silently have become "all crime". Only affirmative discharge labels
    # are retained.
    DISCHARGE = ("SHOOTING", "SHOTS FIRED")
    keep = [v for v in vals if str(v).strip().upper().startswith(DISCHARGE)]
    rej = [v for v in vals if v not in keep]
    man.update(shooting_type_group_counts=tab, kept=keep, rejected=rej,
               classification_rule="whitelist: value starts with 'Shooting' or 'Shots Fired'",
               injury_only_alternative=[v for v in keep if "SHOTS FIRED" not in str(v).upper()])
    print(f"      shooting_type_group value counts: {tab}")
    print(f"      KEPT    : {keep}")
    print(f"      REJECTED: {rej}")
    if not keep:
        raise RuntimeError("shooting_type_group classification retained no values")
    if any(str(v).strip() in ("-", "") for v in keep):
        raise RuntimeError("classifier retained a non-shooting placeholder value")
    inlist = "(" + ",".join(f"'{v}'" for v in keep) + ")"
    d = socrata_pages(u, {"$select": "offense_date,report_date_time,latitude,longitude,"
                                     "shooting_type_group",
                          "$where": f"shooting_type_group IN {inlist}"})
    if not len(d):
        raise RuntimeError("no rows returned for the retained shooting_type_group set")
    dcol = "offense_date" if "offense_date" in d.columns else "report_date_time"
    man["date_field"] = dcol
    return finalize(d.rename(columns={dcol: "date", "latitude": "lat",
                                      "longitude": "lon"}), "Seattle", man), man


# ====================================================================== WAVE 2
# Admitted by Amendment 5 after the A5.3 schema-and-coverage gate. Pittsburgh FAILED that
# gate (530 firearm-discharge records city-wide, and that count still includes code 607.03
# "Discharging Firearm or Airgun", which A5.2 excludes) and is recorded MISSING, not zero.
# Its definition was deliberately NOT broadened to rescue it.
def kansas_city():
    """A5.1: firearm_used_flag; unit = OFFENSE.
    NOTE the geography hazard handled in the design runner, not here: 38 of 87 'Greater
    Kansas City' HOLC polygons (16 of 40 D) lie WEST of the state line in Kansas City,
    KANSAS, though the HOLC file labels every one of them state=MO. KCPD covers Missouri
    only, so those polygons would show zero events regardless of true violence."""
    u = "https://data.kcmo.org/resource/gqy2-yvmn.json"
    man = dict(city="Kansas City", unit="offense", source_kind="socrata", source_url=u,
               case_definition="firearm_used_flag = true",
               prereg_note="A5.1 Wave 2. HOLC footprint spans MO and KS; the design runner "
                           "CLIPS to Missouri because a C/D pair straddling the state line "
                           "is not a within-city comparison (§3).")
    d = socrata_pages(u, {"$select": "reported_date,latitude,longitude,description,offense_type",
                          "$where": "firearm_used_flag = true"})
    return finalize(d.rename(columns={"reported_date": "date", "latitude": "lat",
                                      "longitude": "lon"}), "Kansas City", man), man


def boston():
    """A5.1: the SHOOTING flag; unit = INCIDENT. Per-year CSVs."""
    res = {2019: "34e0ae6b-8c94-4998-ae9e-1b51551fe9ba",
           2020: "be047094-85fe-4104-a480-4fa3d03f9623",
           2021: "f4495ee9-c42c-4019-82c1-d067f07e45d2",
           2022: "313e56df-6d77-49d2-9c49-ee411f10cf58",
           2023: "b973d8cb-eeb2-4e7e-99da-c92938efc9c0"}
    man = dict(city="Boston", unit="incident", source_kind="ckan",
               source_url="https://data.boston.gov/dataset/crime-incident-reports",
               case_definition="SHOOTING flag set", resources=res)
    parts = []
    for yr, rid in res.items():
        j = get("https://data.boston.gov/api/3/action/resource_show",
                {"id": rid}).json()["result"]
        raw = get(j["url"]).content.decode("utf-8", "ignore")
        p = pd.read_csv(io.StringIO(raw), low_memory=False)
        p.columns = [c.strip().upper() for c in p.columns]
        # PARSE EACH FILE'S DATES BEFORE CONCATENATION. Boston's 2023+ file writes
        # OCCURRED_ON_DATE in a different format from the 2019-2022 files; concatenating
        # first makes pandas infer ONE format from the leading rows and silently coerce
        # every non-matching row to NaT. That dropped all 1,975 of the 2023+ shootings
        # while the fetch still reported OK -- only the manifest's n_dropped_nodate
        # revealed it.
        t = pd.to_datetime(p["OCCURRED_ON_DATE"], errors="coerce", format="mixed")
        # ...and DROP THE TIMEZONE. The 2019-2022 files are tz-NAIVE; the 2023+ file is
        # tz-AWARE ("2023-01-27 22:44:00+00"). Concatenating the two yields an OBJECT
        # column, and coercing that NaTs every aware value -- which is how an entire year
        # vanished. Only the date is used (for the window), so tz is dropped explicitly
        # rather than left to produce a dtype that silently poisons the concat.
        if getattr(t.dtype, "tz", None) is not None:
            t = t.dt.tz_localize(None)
        p["OCCURRED_ON_DATE"] = t
        bad = int(p["OCCURRED_ON_DATE"].isna().sum())
        if bad:
            print(f"      {yr}: {bad:,}/{len(p):,} unparseable dates")
        parts.append(p)
    d = pd.concat(parts, ignore_index=True)
    vals = d["SHOOTING"].astype(str).str.strip().str.upper().value_counts().to_dict()
    man["shooting_flag_values"] = {str(k): int(v) for k, v in vals.items()}
    print(f"      SHOOTING flag values: {vals}")
    keep = {"1", "Y", "YES", "TRUE"}
    d = d[d["SHOOTING"].astype(str).str.strip().str.upper().isin(keep)]
    man["shooting_kept_values"] = sorted(keep & set(str(k) for k in vals))
    return finalize(d.rename(columns={"OCCURRED_ON_DATE": "date", "LAT": "lat",
                                      "LONG": "lon"}), "Boston", man), man


def milwaukee():
    """A5.1/A5.7: Weapon_Used_All denoting a real firearm; unit = OFFENSE.
    The ARCHIVE file is the one that covers 2019-2023; the 'current' file starts 2024."""
    url = ("https://data.milwaukee.gov/dataset/5a537f5c-10d7-40a2-9b93-3527a4c89fbd/"
           "resource/395db729-a30a-4e53-ab66-faeb5e1899c8/download/wibrarchive.csv")
    man = dict(city="Milwaukee", unit="offense", source_kind="csv", source_url=url,
               case_definition="DERIVED: Weapon_Used_All denoting a real firearm")
    raw = get(url, timeout=600).content.decode("utf-8", "ignore")
    d = pd.read_csv(io.StringIO(raw), low_memory=False)
    # Weapon_Used_All can carry several weapons for one offense; split and test each.
    toks = sorted({t.strip() for s in d.Weapon_Used_All.dropna().astype(str)
                   for t in s.replace("|", ",").split(",") if t.strip()})
    keep, rej = classify_weapons(toks)
    man.update(weapon_values_all=toks, weapon_kept=keep, weapon_rejected=rej)
    print(f"      enumerated {len(toks)} Weapon_Used_All tokens -> kept {len(keep)}")
    print(f"      KEPT    : {keep}")
    print(f"      REJECTED: {rej}")
    if not keep:
        raise RuntimeError("weapon classification retained nothing")
    kp = set(keep)
    m = d.Weapon_Used_All.fillna("").astype(str).apply(
        lambda s: any(t.strip() in kp for t in s.replace("|", ",").split(",")))
    d = d[m]
    return finalize(d.rename(columns={"Incident_Date": "date", "Address_Latitude": "lat",
                                      "Address_Longitude": "lon"}), "Milwaukee", man), man


def dallas():
    """A5.1: weaponused denoting a real firearm, SAME rule and imitation veto as LA."""
    u = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    man = dict(city="Dallas", unit="offense", source_kind="socrata", source_url=u,
               case_definition="DERIVED: weaponused denoting a real firearm")
    j = get(u, {"$select": "weaponused", "$group": "weaponused", "$limit": 500}).json()
    vals = sorted({r.get("weaponused") for r in j if r.get("weaponused")})
    keep, rej = classify_weapons(vals)
    man.update(weapon_values_all=vals, weapon_kept=keep, weapon_rejected=rej)
    print(f"      enumerated {len(vals)} weaponused values -> kept {len(keep)}")
    print(f"      KEPT    : {keep}")
    if not keep:
        raise RuntimeError("weapon classification retained nothing")
    inlist = "(" + ",".join("'" + v.replace("'", "''") + "'" for v in keep) + ")"
    d = socrata_pages(u, {"$select": "date1,geocoded_column,weaponused",
                          "$where": f"weaponused IN {inlist}"})
    # Dallas ships the point as a nested geocoded_column dict
    gc = d["geocoded_column"].apply(lambda x: x if isinstance(x, dict) else {})
    d["lat"] = gc.apply(lambda x: (x.get("coordinates") or [None, None])[1]
                        if x.get("coordinates") else x.get("latitude"))
    d["lon"] = gc.apply(lambda x: (x.get("coordinates") or [None, None])[0]
                        if x.get("coordinates") else x.get("longitude"))
    return finalize(d.rename(columns={"date1": "date"}), "Dallas", man), man


# ====================================================================== driver
CITIES = {
    "chicago":      ("Chicago",       chicago),
    "philadelphia": ("Philadelphia",  philadelphia),
    "nyc":          ("New York",      nyc),
    "nyc_archive":  ("New York (archive 833y-fsy8)",
                     lambda: nyc("833y-fsy8", "New York (archive)")),
    "detroit":      ("Detroit",       detroit),
    "baltimore":    ("Baltimore",     baltimore),
    "los_angeles":  ("Los Angeles",   los_angeles),
    "seattle":      ("Seattle",       seattle),
    # --- Wave 2 (Amendment 5) ---
    "kansas_city":  ("Kansas City",   kansas_city),
    "milwaukee":    ("Milwaukee",     milwaukee),
    "boston":       ("Boston",        boston),
    "dallas":       ("Dallas",        dallas),
}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    todo = args or list(CITIES)
    bad = [a for a in todo if a not in CITIES]
    if bad:
        sys.exit(f"unknown city keys: {bad}\nvalid: {list(CITIES)}")

    print("=" * 96)
    print("WAVE 1 OUTCOME FETCH — governed by PRE_REG_MULTICITY_2026_09_11.md")
    print("=" * 96)
    done, missing = [], []
    for slug in todo:
        label, fn = CITIES[slug]
        p = OUT / f"{slug}.parquet"
        if p.exists() and not force:
            m = json.loads((OUT / f"{slug}_manifest.json").read_text(encoding="utf-8"))
            print(f"   -- {label:<14} cached n={m.get('n_final'):,}")
            done.append(slug)
            continue
        print(f"\n>> {label}")
        man = {}
        try:
            d, man = fn()
            write(label, slug, d, man)
            done.append(slug)
        except Exception as e:
            if not man:
                man = dict(city=label)
            fail(label, slug, man, e)
            missing.append(slug)

    print("\n" + "=" * 96)
    print(f"FETCHED {len(done)}   MISSING {len(missing)}   {missing if missing else ''}")
    print("=" * 96)
    rows = []
    for slug in done:
        m = json.loads((OUT / f"{slug}_manifest.json").read_text(encoding="utf-8"))
        rows.append(dict(city=m["city"], unit=m.get("unit"), n=m.get("n_final"),
                         in_window=m.get("n_primary_window"),
                         span=f"{m.get('date_min')}..{m.get('date_max')}",
                         uniq_ratio=m.get("unique_coord_ratio"),
                         modal_dup=m.get("modal_dup_count")))
    if rows:
        print(pd.DataFrame(rows).to_string(index=False))
    print(f"\ncaches + manifests in {OUT}")
