import streamlit as st
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import pytz

# --------------------------
# Page config
# --------------------------
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# Constants
# --------------------------
SAVE_DB = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# --------------------------
# DATABASE (sqlite) HELPERS
# --------------------------
def get_db_conn():
    # use check_same_thread False because Streamlit may reuse threads
    conn = sqlite3.connect(SAVE_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    # meta table stores small JSON blobs (cumulative, fourh, settings)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)
    # ensure cumulative key exists
    cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("cumulative", json.dumps(default_cumulative()))
        )
    # ensure fourh (tracker) exists
    cur.execute("SELECT value FROM meta WHERE key = 'fourh';")
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?);",
            ("fourh", json.dumps(empty_tracker()))
        )
    conn.commit()
    conn.close()

def load_cumulative_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            pass
    return default_cumulative()

def save_cumulative_db(data: dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES (?,?);", ("cumulative", json.dumps(data)))
    conn.commit()
    conn.close()

def load_fourh_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = 'fourh';")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            pass
    return empty_tracker()

def save_fourh_db(data: dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES (?,?);", ("fourh", json.dumps(data)))
    conn.commit()
    conn.close()

# --------------------------
# Default cumulative data (if DB empty or corrupted)
# --------------------------
def default_cumulative():
    return {
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
        # flag to indicate openings applied to cumulative (so we don't double-add)
        "_openings_applied": False,
        # first/last lift placeholders
        "first_lift": "",
        "last_lift": ""
    }

# --------------------------
# Hour helpers
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
    return [
        "06h00 - 10h00",
        "10h00 - 14h00",
        "14h00 - 18h00",
        "18h00 - 22h00",
        "22h00 - 02h00",
        "02h00 - 06h00",
    ]

# --------------------------
# FOUR-HOUR tracker helper (structure stored in DB)
# --------------------------
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
        "history_last_4_summaries": []  # keep last 4 summary splits (for summary display)
    }

# --------------------------
# Initialize DB and load persistent data
# --------------------------
# create DB and keys if not present
init_db()

# load cumulative and fourh from DB into variables (we will mirror into session_state)
cumulative = load_cumulative_db()
fourh_db = load_fourh_db()

# --------------------------
# SESSION STATE INIT helper
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# --------------------------
# Initialize keys (persisted fields and inputs)
# --------------------------
# date & labels
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", default_cumulative()["vessel_name"]))
init_key("berthed_date", cumulative.get("berthed_date", default_cumulative()["berthed_date"]))

# plans & openings (from DB, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, default_cumulative()[k]))

# first / last lift (persisted)
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

# HOURLY inputs (these are widgets; initialised to 0)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    # gearbox (hour-only, not cumulative)
    "hr_gearbox", 
]:
    init_key(k, 0)

# gearbox total display (hour-only, not persisted across hours)
init_key("hour_gearbox_total", 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker stored in session (mirror of DB)
init_key("fourh", fourh_db)
init_key("fourh_manual_override", False)

# manual 4H fields for override (editable)
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

# flag to control that openings were applied into cumulative only once
init_key("_openings_applied", cumulative.get("_openings_applied", False))

# --------------------------
# SMALL HELPERS (session-safe)
# --------------------------
def sum_list(lst):
    return int(sum(lst)) if lst else 0

def add_current_hour_to_4h():
    tr = st.session_state["fourh"]
    # append current hourly splits
    tr["fwd_load"].append(int(st.session_state.get("hr_fwd_load", 0)))
    tr["mid_load"].append(int(st.session_state.get("hr_mid_load", 0)))
    tr["aft_load"].append(int(st.session_state.get("hr_aft_load", 0)))
    tr["poop_load"].append(int(st.session_state.get("hr_poop_load", 0)))

    tr["fwd_disch"].append(int(st.session_state.get("hr_fwd_disch", 0)))
    tr["mid_disch"].append(int(st.session_state.get("hr_mid_disch", 0)))
    tr["aft_disch"].append(int(st.session_state.get("hr_aft_disch", 0)))
    tr["poop_disch"].append(int(st.session_state.get("hr_poop_disch", 0)))

    tr["fwd_restow_load"].append(int(st.session_state.get("hr_fwd_restow_load", 0)))
    tr["mid_restow_load"].append(int(st.session_state.get("hr_mid_restow_load", 0)))
    tr["aft_restow_load"].append(int(st.session_state.get("hr_aft_restow_load", 0)))
    tr["poop_restow_load"].append(int(st.session_state.get("hr_poop_restow_load", 0)))

    tr["fwd_restow_disch"].append(int(st.session_state.get("hr_fwd_restow_disch", 0)))
    tr["mid_restow_disch"].append(int(st.session_state.get("hr_mid_restow_disch", 0)))
    tr["aft_restow_disch"].append(int(st.session_state.get("hr_aft_restow_disch", 0)))
    tr["poop_restow_disch"].append(int(st.session_state.get("hr_poop_restow_disch", 0)))

    tr["hatch_fwd_open"].append(int(st.session_state.get("hr_hatch_fwd_open", 0)))
    tr["hatch_mid_open"].append(int(st.session_state.get("hr_hatch_mid_open", 0)))
    tr["hatch_aft_open"].append(int(st.session_state.get("hr_hatch_aft_open", 0)))

    tr["hatch_fwd_close"].append(int(st.session_state.get("hr_hatch_fwd_close", 0)))
    tr["hatch_mid_close"].append(int(st.session_state.get("hr_hatch_mid_close", 0)))
    tr["hatch_aft_close"].append(int(st.session_state.get("hr_hatch_aft_close", 0)))

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr.get("count_hours", 0) + 1)

    # update history summary (last 4 hourly splits) so we can show a 4-hour summary snapshot
    # produce summary dict for this hour (split)
    summary = {
        "fwd_load": tr["fwd_load"][-1] if tr["fwd_load"] else 0,
        "mid_load": tr["mid_load"][-1] if tr["mid_load"] else 0,
        "aft_load": tr["aft_load"][-1] if tr["aft_load"] else 0,
        "poop_load": tr["poop_load"][-1] if tr["poop_load"] else 0,
        "fwd_disch": tr["fwd_disch"][-1] if tr["fwd_disch"] else 0,
        "mid_disch": tr["mid_disch"][-1] if tr["mid_disch"] else 0,
        "aft_disch": tr["aft_disch"][-1] if tr["aft_disch"] else 0,
        "poop_disch": tr["poop_disch"][-1] if tr["poop_disch"] else 0,
    }
    hist = tr.get("history_last_4_summaries", [])
    hist.append(summary)
    tr["history_last_4_summaries"] = hist[-4:]

    # persist fourh to DB
    save_fourh_db(tr)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    save_fourh_db(st.session_state["fourh"])

# --------------------------
# End of PART 1
# --------------------------
# Next: UI rendering (Part 2 will start with top of UI: vessel info, plan inputs, hourly inputs, etc.)
```0
# --------------------------
# PART 2: UI — Vessel info, Plans, Hour selector, Hourly inputs (crane/restow/hatch/gearbox), Idle
# --------------------------

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # text_input binds to session_state keys (persisted via DB on generate/save)
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    # first / last lift inputs (persisted)
    st.text_input("First Lift (call sign / time)", key="first_lift")
    st.text_input("Last Lift (call sign / time)", key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date")

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load")
        st.number_input("Planned Discharge", min_value=0, key="planned_disch")
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load")
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch")
    with c2:
        # Opening balances — these should be treated as already done amounts and applied once
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load")
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch")

# --------------------------
# Hour selector (24h) with safe override handoff
# --------------------------
# Apply pending hour change from previous action BEFORE rendering the selectbox
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

# Ensure valid label
if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = cumulative.get("last_hour", hour_range_list()[0])

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge)
# --------------------------
with st.expander("🏗️ Crane Moves", expanded=True):
    with st.expander("📦 Load", expanded=False):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, key="hr_poop_load")
    with st.expander("📤 Discharge", expanded=False):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch")

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows", expanded=False):
    with st.expander("📦 Load", expanded=False):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")
    with st.expander("📤 Discharge", expanded=False):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves", expanded=False):
    with st.expander("🔓 Open", expanded=False):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close", expanded=False):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

# --------------------------
# Gearbox (hour-only) — as requested: single line input, hour-only and shown on template but NOT cumulative
# --------------------------
with st.expander("⚙️ Gearbox (Hour-only)", expanded=False):
    st.number_input("Gearboxes this hour (total)", min_value=0, key="hr_gearbox")
    # display hour gearbox total (non-persistent across hours)
    st.write("Gearbox moves shown on hourly template only — will not be added to cumulative totals.")

# --------------------------
# Idle / Delays
# --------------------------
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
    # Not a widget key — safe to assign directly
    st.session_state["idle_entries"] = entries

# --------------------------
# End of PART 2 (next: Part 3 will contain Hourly totals (split-only), hourly WhatsApp template & generate logic)
# --------------------------
```0
# WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# Hourly Totals Tracker (split only, accumulates by hour)
# --------------------------
def accumulate_hourly_splits():
    """Accumulate hourly splits into session state running totals"""
    if "hourly_accumulated" not in st.session_state:
        st.session_state["hourly_accumulated"] = {
            "load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "hatch_open": {"FWD": 0, "MID": 0, "AFT": 0},
            "hatch_close": {"FWD": 0, "MID": 0, "AFT": 0},
            "gearbox": 0,
        }

    acc = st.session_state["hourly_accumulated"]
    acc["load"]["FWD"] += st.session_state["hr_fwd_load"]
    acc["load"]["MID"] += st.session_state["hr_mid_load"]
    acc["load"]["AFT"] += st.session_state["hr_aft_load"]
    acc["load"]["POOP"] += st.session_state["hr_poop_load"]

    acc["disch"]["FWD"] += st.session_state["hr_fwd_disch"]
    acc["disch"]["MID"] += st.session_state["hr_mid_disch"]
    acc["disch"]["AFT"] += st.session_state["hr_aft_disch"]
    acc["disch"]["POOP"] += st.session_state["hr_poop_disch"]

    acc["restow_load"]["FWD"] += st.session_state["hr_fwd_restow_load"]
    acc["restow_load"]["MID"] += st.session_state["hr_mid_restow_load"]
    acc["restow_load"]["AFT"] += st.session_state["hr_aft_restow_load"]
    acc["restow_load"]["POOP"] += st.session_state["hr_poop_restow_load"]

    acc["restow_disch"]["FWD"] += st.session_state["hr_fwd_restow_disch"]
    acc["restow_disch"]["MID"] += st.session_state["hr_mid_restow_disch"]
    acc["restow_disch"]["AFT"] += st.session_state["hr_aft_restow_disch"]
    acc["restow_disch"]["POOP"] += st.session_state["hr_poop_restow_disch"]

    acc["hatch_open"]["FWD"] += st.session_state["hr_hatch_fwd_open"]
    acc["hatch_open"]["MID"] += st.session_state["hr_hatch_mid_open"]
    acc["hatch_open"]["AFT"] += st.session_state["hr_hatch_aft_open"]

    acc["hatch_close"]["FWD"] += st.session_state["hr_hatch_fwd_close"]
    acc["hatch_close"]["MID"] += st.session_state["hr_hatch_mid_close"]
    acc["hatch_close"]["AFT"] += st.session_state["hr_hatch_aft_close"]

    acc["gearbox"] += st.session_state["hr_gearbox"]

with st.expander("🧮 Hourly Totals (Accumulated Splits)"):
    if "hourly_accumulated" not in st.session_state:
        st.session_state["hourly_accumulated"] = {
            "load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "hatch_open": {"FWD": 0, "MID": 0, "AFT": 0},
            "hatch_close": {"FWD": 0, "MID": 0, "AFT": 0},
            "gearbox": 0,
        }

    acc = st.session_state["hourly_accumulated"]
    st.write(f"**Load**       — FWD {acc['load']['FWD']} | MID {acc['load']['MID']} | AFT {acc['load']['AFT']} | POOP {acc['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {acc['disch']['FWD']} | MID {acc['disch']['MID']} | AFT {acc['disch']['AFT']} | POOP {acc['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {acc['restow_load']['FWD']} | MID {acc['restow_load']['MID']} | AFT {acc['restow_load']['AFT']} | POOP {acc['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {acc['restow_disch']['FWD']} | MID {acc['restow_disch']['MID']} | AFT {acc['restow_disch']['AFT']} | POOP {acc['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {acc['hatch_open']['FWD']} | MID {acc['hatch_open']['MID']} | AFT {acc['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {acc['hatch_close']['FWD']} | MID {acc['hatch_close']['MID']} | AFT {acc['hatch_close']['AFT']}")
    st.write(f"**Gearboxes Total:** {acc['gearbox']}")

# --------------------------
# WhatsApp Hourly Report
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    remaining_load  = max(0, st.session_state["planned_load"] - cumulative["done_load"])
    remaining_disch = max(0, st.session_state["planned_disch"] - cumulative["done_disch"])
    remaining_restow_load  = max(0, st.session_state["planned_restow_load"] - cumulative["done_restow_load"])
    remaining_restow_disch = max(0, st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"])

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift: {st.session_state['first_lift']}
Last Lift: {st.session_state['last_lift']}

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
*Gearboxes*
Total     {st.session_state['hr_gearbox']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl
    # WhatsApp_Report.py  — PART 4 / 5

# --------------------------
# Hourly Generate & Reset
# --------------------------
def on_generate_hourly():
    # Apply opening balances ONCE to cumulative
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # Add this hour’s moves
    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]
    hour_gearbox = st.session_state["hr_gearbox"]

    # Update cumulative totals
    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_restow_load)
    cumulative["done_restow_disch"] += int(hour_restow_disch)
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)
    cumulative["done_gearbox"] = cumulative.get("done_gearbox", 0) + int(hour_gearbox)

    # Never let done > plan; adjust plan if needed
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    # Save meta
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "first_lift": st.session_state["first_lift"],
        "last_lift": st.session_state["last_lift"],
        "planned_load": st.session_state["planned_load"],
        "planned_disch": st.session_state["planned_disch"],
        "planned_restow_load": st.session_state["planned_restow_load"],
        "planned_restow_disch": st.session_state["planned_restow_disch"],
        "opening_load": st.session_state["opening_load"],
        "opening_disch": st.session_state["opening_disch"],
        "opening_restow_load": st.session_state["opening_restow_load"],
        "opening_restow_disch": st.session_state["opening_restow_disch"],
        "last_hour": st.session_state["hourly_time"],
    })
    save_db(cumulative)

    # Add this hour to splits and 4H
    accumulate_hourly_splits()
    add_current_hour_to_4h()

    # Auto-advance hour
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    return generate_hourly_template()

# Generate Hourly button
if st.button("✅ Generate Hourly Template & Update Totals"):
    txt = on_generate_hourly()
    st.code(txt, language="text")

# WhatsApp send (hourly)
if st.button("📤 Open WhatsApp (Hourly)"):
    txt = generate_hourly_template()
    wa_text = f"```{txt}```"
    if st.session_state.get("wa_num_hour"):
        link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_hour"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
    else:
        st.info("Enter a WhatsApp number or group link to send.")

# Reset hourly
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)

# --------------------------
# 4-Hourly Tracker & Report
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

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
        "gearbox": sum_list(tr.get("gearbox", [])),
    }
    # WhatsApp_Report.py  — PART 5 / 5

# --------------------------
# 4-Hourly Template & Actions
# --------------------------
def generate_4h_template():
    vals = computed_4h()
    return f"""
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift @ {st.session_state['first_lift']}
Last Lift @ {st.session_state['last_lift']}

{st.session_state['fourh_block']}
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
Load   F:{vals['fwd_load']}  M:{vals['mid_load']}  A:{vals['aft_load']}  P:{vals['poop_load']}
Disch  F:{vals['fwd_disch']}  M:{vals['mid_disch']}  A:{vals['aft_disch']}  P:{vals['poop_disch']}

*Restows*
Load   F:{vals['fwd_restow_load']}  M:{vals['mid_restow_load']}  A:{vals['aft_restow_load']}  P:{vals['poop_restow_load']}
Disch  F:{vals['fwd_restow_disch']}  M:{vals['mid_restow_disch']}  A:{vals['aft_restow_disch']}  P:{vals['poop_restow_disch']}

*Hatch Covers*
Open   F:{vals['hatch_fwd_open']}  M:{vals['hatch_mid_open']}  A:{vals['hatch_aft_open']}
Close  F:{vals['hatch_fwd_close']}  M:{vals['hatch_mid_close']}  A:{vals['hatch_aft_close']}

*Gearboxes*
Total: {vals['gearbox']}

*Totals*
Planned Load: {st.session_state['planned_load']} | Done: {cumulative['done_load']} | Remain: {st.session_state['planned_load'] - cumulative['done_load']}
Planned Disch: {st.session_state['planned_disch']} | Done: {cumulative['done_disch']} | Remain: {st.session_state['planned_disch'] - cumulative['done_disch']}
Planned Rst Load: {st.session_state['planned_restow_load']} | Done: {cumulative['done_restow_load']} | Remain: {st.session_state['planned_restow_load'] - cumulative['done_restow_load']}
Planned Rst Disch: {st.session_state['planned_restow_disch']} | Done: {cumulative['done_restow_disch']} | Remain: {st.session_state['planned_restow_disch'] - cumulative['done_restow_disch']}
"""

# Generate 4H Button
if st.button("✅ Generate 4-Hourly Template"):
    txt = generate_4h_template()
    st.code(txt, language="text")

# WhatsApp send (4H)
if st.button("📤 Open WhatsApp (4H)"):
    txt = generate_4h_template()
    wa_text = f"```{txt}```"
    if st.session_state.get("wa_num_4h"):
        link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_4h"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
    else:
        st.info("Enter a WhatsApp number or group link to send.")

# Reset 4H
def reset_4h_inputs():
    for k in st.session_state["fourh"]:
        st.session_state["fourh"][k] = []
    save_db(cumulative)

st.button("🔄 Reset 4-Hourly Totals", on_click=reset_4h_inputs)

# --------------------------
# Master Reset
# --------------------------
def master_reset():
    # Reset all session + cumulative
    for k in list(st.session_state.keys()):
        if k not in ["wa_num_hour","wa_grp_hour","wa_num_4h","wa_grp_4h"]:
            del st.session_state[k]
    init_session_state()
    global cumulative
    cumulative = {
        "done_load": 0, "done_disch": 0,
        "done_restow_load": 0, "done_restow_disch": 0,
        "done_hatch_open": 0, "done_hatch_close": 0,
        "done_gearbox": 0,
        "_openings_applied": False
    }
    save_db(cumulative)

st.button("⚠️ MASTER RESET (Everything)", on_click=master_reset)

# --------------------------
# Footer
# --------------------------
st.markdown("---")
st.caption("Vessel Hourly & 4-Hourly WhatsApp Report — Powered by Streamlit + SQLite")
