# WhatsApp_Report.py  — PART 1 / 5
import streamlit as st
import json
import os
import urllib.parse
import sqlite3
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE (SQLite)
# --------------------------
DB_FILE = "vessel_report.db"
SAVE_FILE = "vessel_report.json"  # fallback, not used if DB OK
TZ = pytz.timezone("Africa/Johannesburg")

DEFAULT_CUMULATIVE = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": "06h00 - 07h00",
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10h55",
    "planned_load": 687,
    "planned_disch": 38,
    "planned_restow_load": 13,
    "planned_restow_disch": 13,
    "opening_load": 0,
    "opening_disch": 0,
    "opening_restow_load": 0,
    "opening_restow_disch": 0,
    # flags
    "_openings_applied": False
}

def get_db_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    """Create tables if missing and seed defaults."""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # keys: cumulative, fourh
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    r = cur.fetchone()
    if r is None:
        cur.execute("INSERT INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(DEFAULT_CUMULATIVE)))
    cur.execute("SELECT value FROM meta WHERE key='fourh';")
    r = cur.fetchone()
    if r is None:
        empty_fourh = {
            "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
            "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
            "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
            "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
            "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
            "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
            "count_hours": 0
        }
        cur.execute("INSERT INTO meta (key, value) VALUES (?, ?);", ("fourh", json.dumps(empty_fourh)))
    conn.commit()
    conn.close()

def load_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    r = cur.fetchone()
    cumulative = DEFAULT_CUMULATIVE.copy()
    if r:
        try:
            cumulative = json.loads(r[0])
            # ensure defaults exist
            for k, v in DEFAULT_CUMULATIVE.items():
                if k not in cumulative:
                    cumulative[k] = v
        except Exception:
            cumulative = DEFAULT_CUMULATIVE.copy()
    cur.execute("SELECT value FROM meta WHERE key='fourh';")
    r2 = cur.fetchone()
    fourh = None
    if r2:
        try:
            fourh = json.loads(r2[0])
        except Exception:
            fourh = None
    if fourh is None:
        fourh = {
            "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
            "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
            "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
            "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
            "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
            "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
            "count_hours": 0
        }
    conn.close()
    return cumulative, fourh

def save_db(cumulative: dict, fourh: dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(cumulative)))
    cur.execute("REPLACE INTO meta (key, value) VALUES (?, ?);", ("fourh", json.dumps(fourh)))
    conn.commit()
    conn.close()

# start DB
init_db()
cumulative_db, fourh_db = load_db()
# We'll use these variables to seed session_state (below)
# WhatsApp_Report.py  — PART 2 / 5

# --------------------------
# HOUR HELPERS
# --------------------------
def hour_range_list():
    return [f"{h:02d}h00 - {(h+1)%24:02d}h00" for h in range(24)]

def next_hour_label(current_label: str):
    hours = hour_range_list()
    if current_label in hours:
        idx = hours.index(current_label)
    else:
        idx = 0
    return hours[(idx + 1) % len(hours)]

def four_hour_blocks():
    # strict consecutive 06-10,10-14...
    return [
        "06h00 - 10h00",
        "10h00 - 14h00",
        "14h00 - 18h00",
        "18h00 - 22h00",
        "22h00 - 02h00",
        "02h00 - 06h00",
    ]

# --------------------------
# SESSION STATE INIT (seed from DB)
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# seed cumulative and fourh into session_state if missing
init_key("cumulative", cumulative_db)
init_key("fourh", fourh_db)

# date & labels
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", st.session_state["cumulative"].get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"]))
init_key("berthed_date", st.session_state["cumulative"].get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"]))

# plans & openings (from DB, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, int(st.session_state["cumulative"].get(k, DEFAULT_CUMULATIVE.get(k, 0))))

# First and last lift (ensure present)
init_key("first_lift", st.session_state["cumulative"].get("first_lift", ""))
init_key("last_lift", st.session_state["cumulative"].get("last_lift", ""))

# HOURLY inputs (each hour; default 0)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "gearbox_hourly"  # temporary hourly gearbox count, not cumulative
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", st.session_state["cumulative"].get("last_hour", hours_list[0]))

# 4H manual override fields
for k in [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
]:
    init_key(k, 0)

init_key("fourh_block", four_hour_blocks()[0])
init_key("fourh_manual_override", False)

# small helper
def sum_list(lst):
    return int(sum(lst)) if lst else 0

# ensure fourh structure exists in session_state (list of last up to 4 hourly entries)
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
        "hist_hours": []  # store labels of the last hours for summary
    }

# if DB had fourh we seeded it earlier; ensure keys exist
if not isinstance(st.session_state["fourh"], dict):
    st.session_state["fourh"] = empty_tracker()
else:
    # ensure hist_hours present (backwards compatibility)
    if "hist_hours" not in st.session_state["fourh"]:
        st.session_state["fourh"]["hist_hours"] = []

# --------------------------
# Persist-save helper
# --------------------------
def persist_state_to_db():
    # merge back into cumulative and save both cumulative and fourh
    cum = st.session_state["cumulative"]
    # update meta fields from session widgets
    for k in ["vessel_name", "berthed_date", "planned_load","planned_disch",
              "planned_restow_load","planned_restow_disch","opening_load","opening_disch",
              "opening_restow_load","opening_restow_disch","first_lift","last_lift","last_hour"]:
        if k == "last_hour":
            cum["last_hour"] = st.session_state.get("hourly_time", cum.get("last_hour"))
        else:
            cum[k] = st.session_state.get(k, cum.get(k))
    # ensure numeric ints
    for nk in ["planned_load","planned_disch","planned_restow_load","planned_restow_disch",
               "opening_load","opening_disch","opening_restow_load","opening_restow_disch"]:
        cum[nk] = int(cum.get(nk, 0))
    # write
    save_db(cum, st.session_state["fourh"])
    st.session_state["cumulative"] = cum
    # WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# UI Title & Vessel inputs
# --------------------------
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# Date & Vessel columns
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # do not reassign widget return values into session_state; use key only
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    # First & Last lift should be at the top (user required)
    st.text_input("First Lift (e.g., 06h05 Crane A)", key="first_lift")
    st.text_input("Last Lift (e.g., 06h55 Crane C)", key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date")

# Plan Totals & Opening Balance
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load")
        st.number_input("Planned Discharge", min_value=0, key="planned_disch")
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load")
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch")
    with c2:
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load")
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch")

# --------------------------
# Hour selector (24h) with safe override
# --------------------------
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

# ensure valid label
if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = st.session_state["cumulative"].get("last_hour", hour_range_list()[0])

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge) — keep as collapsibles as requested
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, key="hr_poop_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch")

# Restows (Load & Discharge)
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch")

# Hatch Moves (Open & Close)
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

# Gearbox (hourly-only count)
with st.expander("⚙️ Gearbox (Hourly)"):
    st.number_input("Gearbox Total This Hour (one-off)", min_value=0, key="gearbox_hourly")
    # WhatsApp_Report.py  — PART 4 / 5

# Idle / Delays
st.subheader("⏸️ Idle / Delays")
idle_options = [
    "Stevedore tea time/shift change",
    "Awaiting cargo",
    "Awaiting AGL operations",
    "Awaiting FPT gang",
    "Awaiting Crane driver",
    "Awaiting onboard stevedores",
    "Windbound",
    "Crane break down/ wipers",
    "Crane break down/ lights",
    "Crane break down/ boom limit",
    "Crane break down",
    "Vessel listing",
    "Struggling to load container",
    "Cell guide struggles",
    "Spreader difficulties",
]
with st.expander("🛑 Idle Entries", expanded=False):
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries")
    entries = []
    for i in range(st.session_state["num_idle_entries"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30")
        end   = c3.text_input(f"End {i+1}",   key=f"idle_end_{i}",   placeholder="e.g., 12h40")
        sel   = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}")
        entries.append({
            "crane": (crane or "").strip(),
            "start": (start or "").strip(),
            "end": (end or "").strip(),
            "delay": (custom or "").strip() if (custom or "").strip() else sel
        })
    st.session_state["idle_entries"] = entries

# --------------------------
# Hourly Totals Tracker (split by position)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": ss["hr_fwd_load"],       "MID": ss["hr_mid_load"],       "AFT": ss["hr_aft_load"],       "POOP": ss["hr_poop_load"]},
        "disch":      {"FWD": ss["hr_fwd_disch"],      "MID": ss["hr_mid_disch"],      "AFT": ss["hr_aft_disch"],      "POOP": ss["hr_poop_disch"]},
        "restow_load":{"FWD": ss["hr_fwd_restow_load"],"MID": ss["hr_mid_restow_load"],"AFT": ss["hr_aft_restow_load"],"POOP": ss["hr_poop_restow_load"]},
        "restow_disch":{"FWD": ss["hr_fwd_restow_disch"],"MID": ss["hr_mid_restow_disch"],"AFT": ss["hr_aft_restow_disch"],"POOP": ss["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": ss["hr_hatch_fwd_open"], "MID": ss["hr_hatch_mid_open"], "AFT": ss["hr_hatch_aft_open"]},
        "hatch_close":{"FWD": ss["hr_hatch_fwd_close"],"MID": ss["hr_hatch_mid_close"],"AFT": ss["hr_hatch_aft_close"]},
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")

# WhatsApp (Hourly) – template
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    cum = st.session_state["cumulative"]
    # Done shown on template must include opening balances (but DB stores done separately)
    done_load = int(cum.get("done_load", 0)) + int(st.session_state.get("opening_load", 0))
    done_disch = int(cum.get("done_disch", 0)) + int(st.session_state.get("opening_disch", 0))
    done_restow_load = int(cum.get("done_restow_load", 0)) + int(st.session_state.get("opening_restow_load", 0))
    done_restow_disch = int(cum.get("done_restow_disch", 0)) + int(st.session_state.get("opening_restow_disch", 0))

    remaining_load = int(st.session_state["planned_load"]) - done_load
    remaining_disch = int(st.session_state["planned_disch"]) - done_disch
    remaining_restow_load = int(st.session_state["planned_restow_load"]) - done_restow_load
    remaining_restow_disch = int(st.session_state["planned_restow_disch"]) - done_restow_disch

    # Avoid negative remains; if negative, adjust plan upwards (persisted)
    if remaining_load < 0:
        st.session_state["planned_load"] = int(st.session_state["planned_load"]) + abs(remaining_load)
        remaining_load = 0
    if remaining_disch < 0:
        st.session_state["planned_disch"] = int(st.session_state["planned_disch"]) + abs(remaining_disch)
        remaining_disch = 0
    if remaining_restow_load < 0:
        st.session_state["planned_restow_load"] = int(st.session_state["planned_restow_load"]) + abs(remaining_restow_load)
        remaining_restow_load = 0
    if remaining_restow_disch < 0:
        st.session_state["planned_restow_disch"] = int(st.session_state["planned_restow_disch"]) + abs(remaining_restow_disch)
        remaining_restow_disch = 0

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
Hour: {st.session_state['hourly_time']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {st.session_state['hr_fwd_load']:>5}     {st.session_state['hr_fwd_disch']:>5}
MID       {st.session_state['hr_mid_load']:>5}     {st.session_state['hr_mid_disch']:>5}
AFT       {st.session_state['hr_aft_load']:>5}     {st.session_state['hr_aft_disch']:>5}
POOP      {st.session_state['hr_poop_load']:>5}     {st.session_state['hr_poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {st.session_state['hr_fwd_restow_load']:>5}     {st.session_state['hr_fwd_restow_disch']:>5}
MID       {st.session_state['hr_mid_restow_load']:>5}     {st.session_state['hr_mid_restow_disch']:>5}
AFT       {st.session_state['hr_aft_restow_load']:>5}     {st.session_state['hr_aft_restow_disch']:>5}
POOP      {st.session_state['hr_poop_restow_load']:>5}     {st.session_state['hr_poop_restow_disch']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {done_load:>5}      {done_disch:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {done_restow_load:>5}      {done_restow_disch:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearboxes*
Total      {st.session_state['gearbox_hourly']:>5}
_________________________
*First Lift* {st.session_state.get('first_lift','') }
*Last Lift*  {st.session_state.get('last_lift','')}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# Actions: generate hourly
# --------------------------
def add_current_hour_to_4h():
    tr = st.session_state["fourh"]
    tr["fwd_load"].append(int(st.session_state["hr_fwd_load"]))
    tr["mid_load"].append(int(st.session_state["hr_mid_load"]))
    tr["aft_load"].append(int(st.session_state["hr_aft_load"]))
    tr["poop_load"].append(int(st.session_state["hr_poop_load"]))

    tr["fwd_disch"].append(int(st.session_state["hr_fwd_disch"]))
    tr["mid_disch"].append(int(st.session_state["hr_mid_disch"]))
    tr["aft_disch"].append(int(st.session_state["hr_aft_disch"]))
    tr["poop_disch"].append(int(st.session_state["hr_poop_disch"]))

    tr["fwd_restow_load"].append(int(st.session_state["hr_fwd_restow_load"]))
    tr["mid_restow_load"].append(int(st.session_state["hr_mid_restow_load"]))
    tr["aft_restow_load"].append(int(st.session_state["hr_aft_restow_load"]))
    tr["poop_restow_load"].append(int(st.session_state["hr_poop_restow_load"]))

    tr["fwd_restow_disch"].append(int(st.session_state["hr_fwd_restow_disch"]))
    tr["mid_restow_disch"].append(int(st.session_state["hr_mid_restow_disch"]))
    tr["aft_restow_disch"].append(int(st.session_state["hr_aft_restow_disch"]))
    tr["poop_restow_disch"].append(int(st.session_state["hr_poop_restow_disch"]))

    tr["hatch_fwd_open"].append(int(st.session_state["hr_hatch_fwd_open"]))
    tr["hatch_mid_open"].append(int(st.session_state["hr_hatch_mid_open"]))
    tr["hatch_aft_open"].append(int(st.session_state["hr_hatch_aft_open"]))

    tr["hatch_fwd_close"].append(int(st.session_state["hr_hatch_fwd_close"]))
    tr["hatch_mid_close"].append(int(st.session_state["hr_hatch_mid_close"]))
    tr["hatch_aft_close"].append(int(st.session_state["hr_hatch_aft_close"]))

    # push hour label
    tr["hist_hours"].append(st.session_state["hourly_time"])
    # keep only last 4
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr.get("count_hours", 0) + 1)

def on_generate_hourly():
    # compute this hour's totals
    hour_load = int(st.session_state["hr_fwd_load"]) + int(st.session_state["hr_mid_load"]) + int(st.session_state["hr_aft_load"]) + int(st.session_state["hr_poop_load"])
    hour_disch = int(st.session_state["hr_fwd_disch"]) + int(st.session_state["hr_mid_disch"]) + int(st.session_state["hr_aft_disch"]) + int(st.session_state["hr_poop_disch"])
    hour_restow_load = int(st.session_state["hr_fwd_restow_load"]) + int(st.session_state["hr_mid_restow_load"]) + int(st.session_state["hr_aft_restow_load"]) + int(st.session_state["hr_poop_restow_load"])
    hour_restow_disch = int(st.session_state["hr_fwd_restow_disch"]) + int(st.session_state["hr_mid_restow_disch"]) + int(st.session_state["hr_aft_restow_disch"]) + int(st.session_state["hr_poop_restow_disch"])
    hour_hatch_open = int(st.session_state["hr_hatch_fwd_open"]) + int(st.session_state["hr_hatch_mid_open"]) + int(st.session_state["hr_hatch_aft_open"])
    hour_hatch_close = int(st.session_state["hr_hatch_fwd_close"]) + int(st.session_state["hr_hatch_mid_close"]) + int(st.session_state["hr_hatch_aft_close"])

    # update DB cumulative (store only the actual done, not opening; we'll show opening on template)
    cum = st.session_state["cumulative"]
    cum["done_load"] = int(cum.get("done_load", 0)) + hour_load
    cum["done_disch"] = int(cum.get("done_disch", 0)) + hour_disch
    cum["done_restow_load"] = int(cum.get("done_restow_load", 0)) + hour_restow_load
    cum["done_restow_disch"] = int(cum.get("done_restow_disch", 0)) + hour_restow_disch
    cum["done_hatch_open"] = int(cum.get("done_hatch_open", 0)) + hour_hatch_open
    cum["done_hatch_close"] = int(cum.get("done_hatch_close", 0)) + hour_hatch_close

    # apply opening only once to background done totals if not applied
    if not cum.get("_openings_applied", False):
        cum["done_load"] += int(st.session_state.get("opening_load", 0))
        cum["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cum["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cum["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cum["_openings_applied"] = True

    # ensure done never exceeds plan: if it does, increase plan to avoid negative remain
    if cum["done_load"] > int(st.session_state["planned_load"]):
        st.session_state["planned_load"] = cum["done_load"]
    if cum["done_disch"] > int(st.session_state["planned_disch"]):
        st.session_state["planned_disch"] = cum["done_disch"]
    if cum["done_restow_load"] > int(st.session_state["planned_restow_load"]):
        st.session_state["planned_restow_load"] = cum["done_restow_load"]
    if cum["done_restow_disch"] > int(st.session_state["planned_restow_disch"]):
        st.session_state["planned_restow_disch"] = cum["done_restow_disch"]

    # persist vessel meta too
    cum["vessel_name"] = st.session_state.get("vessel_name", cum.get("vessel_name"))
    cum["berthed_date"] = st.session_state.get("berthed_date", cum.get("berthed_date"))
    cum["planned_load"] = int(st.session_state.get("planned_load", cum.get("planned_load")))
    cum["planned_disch"] = int(st.session_state.get("planned_disch", cum.get("planned_disch")))
    cum["planned_restow_load"] = int(st.session_state.get("planned_restow_load", cum.get("planned_restow_load")))
    cum["planned_restow_disch"] = int(st.session_state.get("planned_restow_disch", cum.get("planned_restow_disch")))
    cum["opening_load"] = int(st.session_state.get("opening_load", cum.get("opening_load")))
    cum["opening_disch"] = int(st.session_state.get("opening_disch", cum.get("opening_disch")))
    cum["opening_restow_load"] = int(st.session_state.get("opening_restow_load", cum.get("opening_restow_load")))
    cum["opening_restow_disch"] = int(st.session_state.get("opening_restow_disch", cum.get("opening_restow_disch")))
    cum["first_lift"] = st.session_state.get("first_lift", cum.get("first_lift", ""))
    cum["last_lift"] = st.session_state.get("last_lift", cum.get("last_lift", ""))
    cum["last_hour"] = st.session_state.get("hourly_time", cum.get("last_hour"))

    st.session_state["cumulative"] = cum

    # add this hour to 4h tracker
    add_current_hour_to_4h()

    # persist to DB
    save_db(st.session_state["cumulative"], st.session_state["fourh"])

    # prepare safe hour advance on next run
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

# Buttons (single Generate button as requested — no Preview button)
colA, colB = st.columns([2,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        # generate text and update DB, totals, and 4h tracker
        on_generate_hourly()
        txt = generate_hourly_template_text()
        st.code(txt, language="text")
with colB:
    if st.button("📤 Open WhatsApp (Hourly)"):
        txt = generate_hourly_template_text()
        wa_text = f"```{txt}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")
            # WhatsApp_Report.py  — PART 5 / 5

# Reset HOURLY inputs + safe hour advance
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "gearbox_hourly"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)

# --------------------------
# 4-Hourly Tracker & Report
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely (strict sequence)
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
        "hist_hours": tr.get("hist_hours", [])
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"], "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"], "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"], "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"], "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"], "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"], "hatch_aft_close": ss["m4h_hatch_aft_close"],
        "hist_hours": ss["fourh"].get("hist_hours", [])
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    # show last 4 hourly labels summary
    if calc.get("hist_hours"):
        st.write("**Last hourly labels (most recent to oldest):**", " | ".join(reversed(calc["hist_hours"])))

with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto-calculated", key="fourh_manual_override")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("FWD Load 4H", min_value=0, key="m4h_fwd_load")
        st.number_input("FWD Disch 4H", min_value=0, key="m4h_fwd_disch")
        st.number_input("FWD Rst Load 4H", min_value=0, key="m4h_fwd_restow_load")
        st.number_input("FWD Rst Disch 4H", min_value=0, key="m4h_fwd_restow_disch")
        st.number_input("FWD Hatch Open 4H", min_value=0, key="m4h_hatch_fwd_open")
        st.number_input("FWD Hatch Close 4H", min_value=0, key="m4h_hatch_fwd_close")
    with c2:
        st.number_input("MID Load 4H", min_value=0, key="m4h_mid_load")
        st.number_input("MID Disch 4H", min_value=0, key="m4h_mid_disch")
        st.number_input("MID Rst Load 4H", min_value=0, key="m4h_mid_restow_load")
        st.number_input("MID Rst Disch 4H", min_value=0, key="m4h_mid_restow_disch")
        st.number_input("MID Hatch Open 4H", min_value=0, key="m4h_hatch_mid_open")
        st.number_input("MID Hatch Close 4H", min_value=0, key="m4h_hatch_mid_close")
    with c3:
        st.number_input("AFT Load 4H", min_value=0, key="m4h_aft_load")
        st.number_input("AFT Disch 4H", min_value=0, key="m4h_aft_disch")
        st.number_input("AFT Rst Load 4H", min_value=0, key="m4h_aft_restow_load")
        st.number_input("AFT Rst Disch 4H", min_value=0, key="m4h_aft_restow_disch")
        st.number_input("AFT Hatch Open 4H", min_value=0, key="m4h_hatch_aft_open")
        st.number_input("AFT Hatch Close 4H", min_value=0, key="m4h_hatch_aft_close")
    with c4:
        st.number_input("POOP Load 4H", min_value=0, key="m4h_poop_load")
        st.number_input("POOP Disch 4H", min_value=0, key="m4h_poop_disch")
        st.number_input("POOP Rst Load 4H", min_value=0, key="m4h_poop_restow_load")
        st.number_input("POOP Rst Disch 4H", min_value=0, key="m4h_poop_restow_disch")

# Populate button — copies computed 4H into manual fields and enables manual override
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    calc_vals = computed_4h()
    st.session_state["m4h_fwd_load"] = calc_vals["fwd_load"]
    st.session_state["m4h_mid_load"] = calc_vals["mid_load"]
    st.session_state["m4h_aft_load"] = calc_vals["aft_load"]
    st.session_state["m4h_poop_load"] = calc_vals["poop_load"]

    st.session_state["m4h_fwd_disch"] = calc_vals["fwd_disch"]
    st.session_state["m4h_mid_disch"] = calc_vals["mid_disch"]
    st.session_state["m4h_aft_disch"] = calc_vals["aft_disch"]
    st.session_state["m4h_poop_disch"] = calc_vals["poop_disch"]

    st.session_state["m4h_fwd_restow_load"] = calc_vals["fwd_restow_load"]
    st.session_state["m4h_mid_restow_load"] = calc_vals["mid_restow_load"]
    st.session_state["m4h_aft_restow_load"] = calc_vals["aft_restow_load"]
    st.session_state["m4h_poop_restow_load"] = calc_vals["poop_restow_load"]

    st.session_state["m4h_fwd_restow_disch"] = calc_vals["fwd_restow_disch"]
    st.session_state["m4h_mid_restow_disch"] = calc_vals["mid_restow_disch"]
    st.session_state["m4h_aft_restow_disch"] = calc_vals["aft_restow_disch"]
    st.session_state["m4h_poop_restow_disch"] = calc_vals["poop_restow_disch"]

    st.session_state["m4h_hatch_fwd_open"] = calc_vals["hatch_fwd_open"]
    st.session_state["m4h_hatch_mid_open"] = calc_vals["hatch_mid_open"]
    st.session_state["m4h_hatch_aft_open"] = calc_vals["hatch_aft_open"]

    st.session_state["m4h_hatch_fwd_close"] = calc_vals["hatch_fwd_close"]
    st.session_state["m4h_hatch_mid_close"] = calc_vals["hatch_mid_close"]
    st.session_state["m4h_hatch_aft_close"] = calc_vals["hatch_aft_close"]

    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")
    # persist manual values to DB so other devices see them
    save_db(st.session_state["cumulative"], st.session_state["fourh"])

# choose which 4h values to render in template
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template_text():
    cum = st.session_state["cumulative"]
    # Done shown includes opening (same as hourly template)
    done_load = int(cum.get("done_load", 0)) + int(st.session_state.get("opening_load", 0))
    done_disch = int(cum.get("done_disch", 0)) + int(st.session_state.get("opening_disch", 0))
    done_restow_load = int(cum.get("done_restow_load", 0)) + int(st.session_state.get("opening_restow_load", 0))
    done_restow_disch = int(cum.get("done_restow_disch", 0)) + int(st.session_state.get("opening_restow_disch", 0))

    remaining_load = int(st.session_state["planned_load"]) - done_load
    remaining_disch = int(st.session_state["planned_disch"]) - done_disch
    remaining_restow_load = int(st.session_state["planned_restow_load"]) - done_restow_load
    remaining_restow_disch = int(st.session_state["planned_restow_disch"]) - done_restow_disch

    # avoid negative remain by adjusting plan
    if remaining_load < 0:
        st.session_state["planned_load"] = int(st.session_state["planned_load"]) + abs(remaining_load)
        remaining_load = 0
    if remaining_disch < 0:
        st.session_state["planned_disch"] = int(st.session_state["planned_disch"]) + abs(remaining_disch)
        remaining_disch = 0
    if remaining_restow_load < 0:
        st.session_state["planned_restow_load"] = int(st.session_state["planned_restow_load"]) + abs(remaining_restow_load)
        remaining_restow_load = 0
    if remaining_restow_disch < 0:
        st.session_state["planned_restow_disch"] = int(st.session_state["planned_restow_disch"]) + abs(remaining_restow_disch)
        remaining_restow_disch = 0

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {vals4h['fwd_load']:>5}     {vals4h['fwd_disch']:>5}
MID       {vals4h['mid_load']:>5}     {vals4h['mid_disch']:>5}
AFT       {vals4h['aft_load']:>5}     {vals4h['aft_disch']:>5}
POOP      {vals4h['poop_load']:>5}     {vals4h['poop_disch']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {vals4h['fwd_restow_load']:>5}     {vals4h['fwd_restow_disch']:>5}
MID       {vals4h['mid_restow_load']:>5}     {vals4h['mid_restow_disch']:>5}
AFT       {vals4h['aft_restow_load']:>5}     {vals4h['aft_restow_disch']:>5}
POOP      {vals4h['poop_restow_load']:>5}     {vals4h['poop_restow_disch']:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {done_load:>5}      {done_disch:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {done_restow_load:>5}      {done_restow_disch:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*First Lift* {st.session_state.get('first_lift','') }
*Last Lift*  {st.session_state.get('last_lift','')}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template_text(), language="text")

# WhatsApp 4H send
st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB, cC = st.columns([1,1,1])
with cA:
    if st.button("👁️ Preview 4-Hourly Template Only"):
        st.code(generate_4h_template_text(), language="text")
with cB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template_text()
        wa_text = f"```{t}```"
        if st.session_state.get("wa_num_4h"):
            link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_4h"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")
with cC:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        st.session_state["fourh"] = empty_tracker()
        save_db(st.session_state["cumulative"], st.session_state["fourh"])
        st.success("4-hourly tracker reset.")

# --------------------------
# MASTER RESET (wipe everything and restore defaults)
# --------------------------
def master_reset():
    # Clear session_state keys that are data (keep UI defaults)
    keys_to_clear = [k for k in list(st.session_state.keys()) if not k.startswith("report_") and k not in ("page_config",)]
    for k in keys_to_clear:
        try:
            del st.session_state[k]
        except Exception:
            pass
    # Reset DB to defaults
    init_db()
    cum, fourh = load_db()
    st.session_state["cumulative"] = cum
    st.session_state["fourh"] = fourh
    st.experimental_rerun()

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Gearbox is hourly-only and is displayed on templates but not cumulative. "
    "• Opening balances are applied once into Done (background) and shown on templates. "
    "• Master Reset clears everything (use with care)."
)

st.button("⚠️ MASTER RESET (clear all data & DB)", on_click=master_reset)
