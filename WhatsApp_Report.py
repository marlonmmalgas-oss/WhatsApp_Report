# WhatsApp_Report.py  — PART 1 / 5
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz
import sqlite3

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE
# --------------------------
SAVE_DB = "vessel_report.db"
SAVE_FILE = "vessel_report.json"  # kept for backwards compatibility if needed
TZ = pytz.timezone("Africa/Johannesburg")

# Default cumulative/meta structure (used if no DB record exists)
DEFAULT_CUMULATIVE = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "_openings_applied": False,  # internal flag to ensure openings applied once
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
    "opening_restow_disch": 0
}

# --------------------------
# SQLITE DB HELPERS
# --------------------------
def get_db_conn():
    # ensure directory exists (if path includes folders)
    db_path = os.path.abspath(SAVE_DB)
    dirname = os.path.dirname(db_path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Create tables if missing and ensure a single meta row exists to store JSON-encoded cumulative.
    This function is idempotent and safe to call on each run.
    """
    conn = get_db_conn()
    cur = conn.cursor()
    # meta table for key/value (store cumulative as JSON under key 'cumulative')
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # hourly_history - store past hourly entries (optional, for auditing)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hourly_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            hour_label TEXT,
            data_json TEXT
        );
    """)
    conn.commit()

    # ensure cumulative exists
    cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
    row = cur.fetchone()
    if row is None:
        # insert default cumulative JSON
        cur.execute("INSERT INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(DEFAULT_CUMULATIVE)))
        conn.commit()
    conn.close()

def load_cumulative_from_db() -> dict:
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
    row = cur.fetchone()
    if not row:
        conn.close()
        return DEFAULT_CUMULATIVE.copy()
    try:
        data = json.loads(row["value"])
    except Exception:
        data = DEFAULT_CUMULATIVE.copy()
    conn.close()
    # ensure missing keys exist
    for k, v in DEFAULT_CUMULATIVE.items():
        if k not in data:
            data[k] = v
    return data

def save_cumulative_to_db(data: dict):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(data)))
    conn.commit()
    conn.close()

# initialize DB and load cumulative
init_db()
cumulative = load_cumulative_from_db()

# --------------------------
# HOUR HELPERS
# --------------------------
def hour_range_list():
    return [f"{h:02d}h00 - {(h+1)%24:02d}h00" for h in range(24)]

def next_hour_label(current_label: str):
    hours = hour_range_list()
    try:
        idx = hours.index(current_label)
    except ValueError:
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
# SESSION STATE INIT
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# date & labels (persisted metadata comes from DB)
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"]))
init_key("berthed_date", cumulative.get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"]))

# plans & openings (from DB, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, DEFAULT_CUMULATIVE.get(k, 0)))

# HOURLY inputs - initialize keys (including gearbox hourly-only input)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_first_lift","hr_last_lift",             # first & last lift inputs (hourly)
    "hr_gearbox"                                # gearbox hourly total (non-cumulative)
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker (lists roll up to 4 most recent generated hours)
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "first_lift": [], "last_lift": [], "gearbox": [],
        "count_hours": 0,
    }

init_key("fourh", cumulative.get("fourh", empty_tracker()))
init_key("fourh_manual_override", False)

for k in [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
    "m4h_first_lift","m4h_last_lift","m4h_gearbox"
]:
    init_key(k, cumulative.get(k, 0))

init_key("fourh_block", cumulative.get("fourh_block", four_hour_blocks()[0]))

# --------------------------
# SMALL HELPERS
# --------------------------
def sum_list(lst):
    return int(sum(lst)) if lst else 0

def add_current_hour_to_4h():
    tr = st.session_state["fourh"]
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

    # first/last lifts and gearbox for that hour (gearbox is hourly-only, not cumulative)
    tr["first_lift"].append(st.session_state.get("hr_first_lift", ""))
    tr["last_lift"].append(st.session_state.get("hr_last_lift", ""))
    tr["gearbox"].append(int(st.session_state.get("hr_gearbox", 0)))

    # keep only last 4 hours
    for k in list(tr.keys()):
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr.get("count_hours", 0) + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    # optional: persist to DB so other devices get empty tracker if master reset is used later
    cumulative["fourh"] = st.session_state["fourh"]
    save_cumulative_to_db(cumulative)

# Persist cumulative to DB helper
def persist_cumulative():
    # make a shallow copy to avoid accidental session_state linkage
    cumulative_copy = dict(cumulative)
    cumulative_copy["fourh"] = st.session_state.get("fourh", cumulative_copy.get("fourh", {}))
    cumulative_copy["fourh_block"] = st.session_state.get("fourh_block", cumulative_copy.get("fourh_block"))
    save_cumulative_to_db(cumulative_copy)

# End of PART 1 / 5
# WhatsApp_Report.py  — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Persistence callbacks
# --------------------------
def persist_meta():
    """
    Called when a top-level meta field is changed (vessel name, berthed_date, planned/opening values).
    Updates the cumulative dict and saves to DB so other devices see the change.
    """
    # Update cumulative with current session_state values for persistent fields
    for k in ["vessel_name", "berthed_date", "planned_load", "planned_disch",
              "planned_restow_load", "planned_restow_disch",
              "opening_load", "opening_disch", "opening_restow_load", "opening_restow_disch",
              "fourh_block"]:
        cumulative[k] = st.session_state.get(k, cumulative.get(k))
    # Ensure last_hour persists too
    cumulative["last_hour"] = st.session_state.get("hourly_time", cumulative.get("last_hour"))
    save_cumulative_to_db(cumulative)

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # Use on_change to persist edits immediately
    st.text_input("Vessel Name", key="vessel_name", on_change=persist_meta)
    st.text_input("Berthed Date", key="berthed_date", on_change=persist_meta)
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date")

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load", on_change=persist_meta)
        st.number_input("Planned Discharge", min_value=0, key="planned_disch", on_change=persist_meta)
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load", on_change=persist_meta)
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch", on_change=persist_meta)
    with c2:
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load", on_change=persist_meta)
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch", on_change=persist_meta)
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load", on_change=persist_meta)
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch", on_change=persist_meta)

# --------------------------
# Hour selector (24h) with safe override handoff
# --------------------------
# If an override was scheduled by previous action, apply it BEFORE rendering selectbox
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
    key="hourly_time",
    on_change=persist_meta
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge)
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

# --------------------------
# Restows (Load & Discharge)
# --------------------------
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

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

# --------------------------
# First/Last Lift and Gearbox (hourly-only)
# --------------------------
with st.expander("⛏️ Lifts & Gearbox (hourly)"):
    st.text_input("First Lift (e.g., container ID/time)", key="hr_first_lift")
    st.text_input("Last Lift (e.g., container ID/time)", key="hr_last_lift")
    st.number_input("Gearbox Total (hourly)", min_value=0, key="hr_gearbox",
                    help="One-off hourly gearbox total (not cumulative); will appear on hourly template only.")

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
    # Not a widget key — safe to assign directly to session_state
    st.session_state["idle_entries"] = entries
    # WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# Hourly Totals Tracker (split only — no combined)
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

# --------------------------
# WhatsApp (Hourly) – template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    # adjust plan dynamically so remain never negative
    plan_load  = max(st.session_state["planned_load"],  cumulative["done_load"])
    plan_disch = max(st.session_state["planned_disch"], cumulative["done_disch"])
    plan_rl    = max(st.session_state["planned_restow_load"],  cumulative["done_restow_load"])
    plan_rd    = max(st.session_state["planned_restow_disch"], cumulative["done_restow_disch"])

    remaining_load  = plan_load  - cumulative["done_load"]
    remaining_disch = plan_disch - cumulative["done_disch"]
    remaining_rl    = plan_rl    - cumulative["done_restow_load"]
    remaining_rd    = plan_rd    - cumulative["done_restow_disch"]

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
Plan       {plan_load:>5}      {plan_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {plan_rl:>5}      {plan_rd:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_rl:>5}      {remaining_rd:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearbox*
Total     {st.session_state['hr_gearbox']:>5}
_________________________
*First/Last Lift*
First     {st.session_state['hr_first_lift']}
Last      {st.session_state['hr_last_lift']}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

def on_generate_hourly():
    # apply this hour’s moves immediately
    hour_load = (st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] +
                 st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"])
    hour_disch = (st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] +
                  st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"])
    hour_rl = (st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] +
               st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"])
    hour_rd = (st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] +
               st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"])
    hour_ho = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hc = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # add opening balances only once at very first run
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # now add current hour’s
    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_rl)
    cumulative["done_restow_disch"] += int(hour_rd)
    cumulative["done_hatch_open"] += int(hour_ho)
    cumulative["done_hatch_close"] += int(hour_hc)

    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
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
    save_cumulative_to_db(cumulative)

    # push into 4-hour rolling tracker
    add_current_hour_to_4h()

    # advance hour for next run
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    return generate_hourly_template()

# One single button to generate & update
if st.button("✅ Generate Hourly Template & Update Totals"):
    txt = on_generate_hourly()
    st.code(txt, language="text")

# Reset HOURLY inputs (plus safe hour advance)
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox","hr_first_lift","hr_last_lift"
    ]:
        st.session_state[k] = 0 if isinstance(st.session_state.get(k), int) else ""
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
# WhatsApp_Report.py  — PART 4 / 5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]),
        "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]),
        "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]),
        "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]),
        "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]),
        "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]),
        "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
        "gearbox": sum_list(tr.get("gearbox", [])),
        "first_lift": st.session_state.get("hr_first_lift", ""),
        "last_lift": st.session_state.get("hr_last_lift", "")
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"], "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"], "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"], "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"], "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"], "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "m4h_hatch_mid_close": ss["m4h_hatch_mid_close"], "hatch_aft_close": ss["m4h_hatch_aft_close"],
        "gearbox": ss.get("m4h_gearbox", 0),
        "first_lift": ss.get("m4h_first_lift", ""),
        "last_lift": ss.get("m4h_last_lift", "")
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    st.write(f"**Gearbox Total:** {calc['gearbox']}")
    st.write(f"**First Lift:** {calc['first_lift']} | **Last Lift:** {calc['last_lift']}")

# --- Button to copy hourly tracker into manual 4H
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    vals = computed_4h()
    st.session_state["m4h_fwd_load"] = vals["fwd_load"]
    st.session_state["m4h_mid_load"] = vals["mid_load"]
    st.session_state["m4h_aft_load"] = vals["aft_load"]
    st.session_state["m4h_poop_load"] = vals["poop_load"]
    st.session_state["m4h_fwd_disch"] = vals["fwd_disch"]
    st.session_state["m4h_mid_disch"] = vals["mid_disch"]
    st.session_state["m4h_aft_disch"] = vals["aft_disch"]
    st.session_state["m4h_poop_disch"] = vals["poop_disch"]
    st.session_state["m4h_fwd_restow_load"] = vals["fwd_restow_load"]
    st.session_state["m4h_mid_restow_load"] = vals["mid_restow_load"]
    st.session_state["m4h_aft_restow_load"] = vals["aft_restow_load"]
    st.session_state["m4h_poop_restow_load"] = vals["poop_restow_load"]
    st.session_state["m4h_fwd_restow_disch"] = vals["fwd_restow_disch"]
    st.session_state["m4h_mid_restow_disch"] = vals["mid_restow_disch"]
    st.session_state["m4h_aft_restow_disch"] = vals["aft_restow_disch"]
    st.session_state["m4h_poop_restow_disch"] = vals["poop_restow_disch"]
    st.session_state["m4h_hatch_fwd_open"] = vals["hatch_fwd_open"]
    st.session_state["m4h_hatch_mid_open"] = vals["hatch_mid_open"]
    st.session_state["m4h_hatch_aft_open"] = vals["hatch_aft_open"]
    st.session_state["m4h_hatch_fwd_close"] = vals["hatch_fwd_close"]
    st.session_state["m4h_hatch_mid_close"] = vals["hatch_mid_close"]
    st.session_state["m4h_hatch_aft_close"] = vals["hatch_aft_close"]
    st.session_state["m4h_gearbox"] = vals["gearbox"]
    st.session_state["m4h_first_lift"] = vals["first_lift"]
    st.session_state["m4h_last_lift"] = vals["last_lift"]
    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    plan_load  = max(st.session_state["planned_load"],  cumulative["done_load"])
    plan_disch = max(st.session_state["planned_disch"], cumulative["done_disch"])
    plan_rl    = max(st.session_state["planned_restow_load"],  cumulative["done_restow_load"])
    plan_rd    = max(st.session_state["planned_restow_disch"], cumulative["done_restow_disch"])

    remaining_load  = plan_load  - cumulative["done_load"]
    remaining_disch = plan_disch - cumulative["done_disch"]
    remaining_rl    = plan_rl    - cumulative["done_restow_load"]
    remaining_rd    = plan_rd    - cumulative["done_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *4-HOURLY MOVES*
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
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {plan_load:>5}      {plan_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {plan_rl:>5}      {plan_rd:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_rl:>5}      {remaining_rd:>5}
_________________________
*Hatch Moves*
             Open   Close
FWD          {vals4h['hatch_fwd_open']:>5}   {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}   {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}   {vals4h['hatch_aft_close']:>5}
_________________________
*Gearbox*
Total     {vals4h['gearbox']:>5}
_________________________
*First/Last Lift*
First     {vals4h['first_lift']}
Last      {vals4h['last_lift']}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template(), language="text")
# WhatsApp_Report.py  — PART 5 / 5

# ============================
#   BUTTONS & WHATSAPP OUTPUT
# ============================

def on_generate_hourly():
    txt = generate_hourly_template()
    st.session_state["last_hourly_txt"] = txt
    save_db(cumulative)
    return txt

def on_generate_4h():
    txt = generate_4h_template()
    st.session_state["last_4h_txt"] = txt
    save_db(cumulative)
    return txt

# --- Hourly Buttons
if st.button("📄 Generate Hourly Report"):
    txt = on_generate_hourly()
    st.code(txt, language="text")

# --- 4-Hourly Buttons
if st.button("📄 Generate 4-Hourly Report"):
    txt = on_generate_4h()
    st.code(txt, language="text")

# --- WhatsApp Send (Hourly)
st.subheader("📲 Send Hourly Report via WhatsApp")
st.text_input("Enter WhatsApp Number (e.g. +27...)", key="wa_hourly")
if st.button("Send Hourly Report"):
    if st.session_state.get("last_hourly_txt", ""):
        st.success("Hourly report ready to copy/paste into WhatsApp.")
        st.code(st.session_state["last_hourly_txt"], language="text")
    else:
        st.warning("Generate Hourly Report first.")

# --- WhatsApp Send (4-Hourly)
st.subheader("📲 Send 4-Hourly Report via WhatsApp")
st.text_input("Enter WhatsApp Number (e.g. +27...)", key="wa_4h")
if st.button("Send 4-Hourly Report"):
    if st.session_state.get("last_4h_txt", ""):
        st.success("4-Hourly report ready to copy/paste into WhatsApp.")
        st.code(st.session_state["last_4h_txt"], language="text")
    else:
        st.warning("Generate 4-Hourly Report first.")

# ============================
#   RESET BUTTONS
# ============================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Reset Hourly"):
        for key in st.session_state.keys():
            if key.startswith("hr_"):
                st.session_state[key] = 0
        st.success("Hourly inputs reset.")

with col2:
    if st.button("🔄 Reset 4-Hourly"):
        for key in st.session_state.keys():
            if key.startswith("m4h_") or key.startswith("fourh"):
                st.session_state[key] = 0
        st.success("4-Hourly inputs reset.")

with col3:
    if st.button("🧨 Master Reset (All)"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        reset_cumulative()
        st.success("All data reset — fresh start.")

# ============================
#   LOAD LAST SESSION
# ============================

cumulative = load_db()

# Ensure planned totals never less than done totals
if cumulative["done_load"] > st.session_state["planned_load"]:
    st.session_state["planned_load"] = cumulative["done_load"]
if cumulative["done_disch"] > st.session_state["planned_disch"]:
    st.session_state["planned_disch"] = cumulative["done_disch"]
if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
    st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
    st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

# ============================
#   FOOTER
# ============================

st.markdown("---")
st.caption("⚓ Vessel Report Generator | Data saved with SQLite | Built for uninterrupted multi-device use.")
