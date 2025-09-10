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
# CONSTANTS & PERSISTENCE (SQLite)
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# Default cumulative state (used when DB empty)
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
    "first_lift": "",
    "last_lift": ""
}

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY,
            state_json TEXT NOT NULL
        )
    """)
    cur.execute("SELECT state_json FROM app_state WHERE id=1")
    row = cur.fetchone()
    if not row:
        initial_state = {
            "cumulative": DEFAULT_CUMULATIVE,
            "fourh": empty_tracker()
        }
        cur.execute("INSERT INTO app_state (id, state_json) VALUES (1, ?)", (json.dumps(initial_state),))
        conn.commit()
    conn.close()

def load_db_state():
    if not os.path.exists(DB_FILE):
        return None
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT state_json FROM app_state WHERE id=1")
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    finally:
        conn.close()
    return None

def save_db_state(state: dict):
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("UPDATE app_state SET state_json = ? WHERE id = 1", (json.dumps(state),))
    conn.commit()
    conn.close()

# --------------------------
# HOUR HELPERS (unchanged)
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
# FOUR-HOUR tracker constructor (includes hour labels)
# --------------------------
def empty_tracker():
    return {
        "hours": [],  # store hourly labels for last 4 saved hours
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
    }

# --------------------------
# Load initial state (DB first, else defaults)
# --------------------------
# We must set up empty_tracker before using init_db/load
init_db()
db_state = load_db_state()
if db_state:
    cumulative = db_state.get("cumulative", DEFAULT_CUMULATIVE.copy())
    fourh_from_db = db_state.get("fourh", empty_tracker())
else:
    cumulative = DEFAULT_CUMULATIVE.copy()
    fourh_from_db = empty_tracker()

# --------------------------
# SESSION STATE INIT (safe)
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# date & labels
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"]))
init_key("berthed_date", cumulative.get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"]))
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

# plans & openings (from DB/cumulative, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, DEFAULT_CUMULATIVE.get(k, 0)))

# HOURLY inputs (including gearbox)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox_moves"  # gearbox hourly only
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker: load from DB into session_state if present
init_key("fourh", fourh_from_db)
init_key("fourh_manual_override", False)

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

# small helper to persist session into DB
def persist_state_to_db():
    state = {
        "cumulative": cumulative,
        "fourh": st.session_state["fourh"]
    }
    save_db_state(state)
    # WhatsApp_Report.py  — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel (widgets are top-level only)
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # Do not assign widget return to session_state; use key only
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.text_input("First Lift (time/notes)", key="first_lift")
    st.text_input("Last Lift (time/notes)", key="last_lift")
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
# Crane Moves (Load & Discharge) — preserved collapsibles
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
# Gearbox moves (hourly only)
# --------------------------
with st.expander("🔧 Gearbox (Hourly)"):
    st.number_input("Gearbox Moves This Hour", min_value=0, key="hr_gearbox_moves")

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
    # WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# Hourly Totals Tracker (split by position) — splits only (no combined display if you removed it)
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
    st.write(f"**Gearbox This Hour:** {st.session_state.get('hr_gearbox_moves', 0)}")

# --------------------------
# WhatsApp (Hourly) – template and generation
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def hourly_done_display(field_done_key, opening_key):
    """Return displayed 'Done' value = cumulative done + opening"""
    base_done = int(cumulative.get(field_done_key, 0))
    opening = int(st.session_state.get(opening_key, 0))
    return base_done + opening

def compute_remaining(plan_key, field_done_key, opening_key):
    done_display = hourly_done_display(field_done_key, opening_key)
    plan = int(st.session_state.get(plan_key, 0))
    remain = plan - done_display
    # If remain negative, adjust plan upward so remain is zero
    if remain < 0:
        st.session_state[plan_key] = done_display
        plan = done_display
        remain = 0
    return plan, done_display, remain

def generate_hourly_template_text():
    # Use cumulative updated values + opening balances in display
    plan_load, done_load_display, remain_load = compute_remaining("planned_load", "done_load", "opening_load")
    plan_disch, done_disch_display, remain_disch = compute_remaining("planned_disch", "done_disch", "opening_disch")
    plan_rst_load, done_rst_load_display, remain_rst_load = compute_remaining("planned_restow_load", "done_restow_load", "opening_restow_load")
    plan_rst_disch, done_rst_disch_display, remain_rst_disch = compute_remaining("planned_restow_disch", "done_restow_disch", "opening_restow_disch")

    # hourly splits snapshot (the latest entered hour)
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
Done       {done_load_display:>5}      {done_disch_display:>5}
Remain     {remain_load:>5}      {remain_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {plan_rst_load:>5}      {plan_rst_disch:>5}
Done       {done_rst_load_display:>5}      {done_rst_disch_display:>5}
Remain     {remain_rst_load:>5}      {remain_rst_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearbox Moves (This Hour)*
Total Gearboxes: {st.session_state.get('hr_gearbox_moves', 0)}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    # first/last lifts
    tmpl += f"_________________________\nFirst Lift: {st.session_state.get('first_lift','')}\nLast Lift: {st.session_state.get('last_lift','')}\n"
    return tmpl

# --------------------------
# on_generate_hourly (callback must not create widgets)
# --------------------------
def add_current_hour_to_4h():
    # already defined earlier but redefine here to ensure local usage — will use st.session_state["fourh"]
    tr = st.session_state["fourh"]
    tr["hours"].append(st.session_state["hourly_time"])
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

    # trim to last 4
    for key in tr.keys():
        if isinstance(tr[key], list):
            tr[key] = tr[key][-4:]
    tr["count_hours"] = min(4, tr.get("count_hours", 0) + 1)
    st.session_state["fourh"] = tr

def on_generate_hourly():
    # Compute hour totals from widget values (all integers)
    hour_load = int(st.session_state["hr_fwd_load"]) + int(st.session_state["hr_mid_load"]) + int(st.session_state["hr_aft_load"]) + int(st.session_state["hr_poop_load"])
    hour_disch = int(st.session_state["hr_fwd_disch"]) + int(st.session_state["hr_mid_disch"]) + int(st.session_state["hr_aft_disch"]) + int(st.session_state["hr_poop_disch"])
    hour_restow_load = int(st.session_state["hr_fwd_restow_load"]) + int(st.session_state["hr_mid_restow_load"]) + int(st.session_state["hr_aft_restow_load"]) + int(st.session_state["hr_poop_restow_load"])
    hour_restow_disch = int(st.session_state["hr_fwd_restow_disch"]) + int(st.session_state["hr_mid_restow_disch"]) + int(st.session_state["hr_aft_restow_disch"]) + int(st.session_state["hr_poop_restow_disch"])
    hour_hatch_open = int(st.session_state["hr_hatch_fwd_open"]) + int(st.session_state["hr_hatch_mid_open"]) + int(st.session_state["hr_hatch_aft_open"])
    hour_hatch_close = int(st.session_state["hr_hatch_fwd_close"]) + int(st.session_state["hr_hatch_mid_close"]) + int(st.session_state["hr_hatch_aft_close"])

    # Update cumulative (in-memory variable)
    cumulative["done_load"] = int(cumulative.get("done_load", 0)) + hour_load
    cumulative["done_disch"] = int(cumulative.get("done_disch", 0)) + hour_disch
    cumulative["done_restow_load"] = int(cumulative.get("done_restow_load", 0)) + hour_restow_load
    cumulative["done_restow_disch"] = int(cumulative.get("done_restow_disch", 0)) + hour_restow_disch
    cumulative["done_hatch_open"] = int(cumulative.get("done_hatch_open", 0)) + hour_hatch_open
    cumulative["done_hatch_close"] = int(cumulative.get("done_hatch_close", 0)) + hour_hatch_close

    # persist meta/settings from current session
    cumulative.update({
        "vessel_name": st.session_state.get("vessel_name", cumulative.get("vessel_name")),
        "berthed_date": st.session_state.get("berthed_date", cumulative.get("berthed_date")),
        "planned_load": int(st.session_state.get("planned_load", cumulative.get("planned_load", 0))),
        "planned_disch": int(st.session_state.get("planned_disch", cumulative.get("planned_disch", 0))),
        "planned_restow_load": int(st.session_state.get("planned_restow_load", cumulative.get("planned_restow_load", 0))),
        "planned_restow_disch": int(st.session_state.get("planned_restow_disch", cumulative.get("planned_restow_disch", 0))),
        "opening_load": int(st.session_state.get("opening_load", cumulative.get("opening_load", 0))),
        "opening_disch": int(st.session_state.get("opening_disch", cumulative.get("opening_disch", 0))),
        "opening_restow_load": int(st.session_state.get("opening_restow_load", cumulative.get("opening_restow_load", 0))),
        "opening_restow_disch": int(st.session_state.get("opening_restow_disch", cumulative.get("opening_restow_disch", 0))),
        "last_hour": st.session_state.get("hourly_time", cumulative.get("last_hour")),
        "first_lift": st.session_state.get("first_lift", cumulative.get("first_lift", "")),
        "last_lift": st.session_state.get("last_lift", cumulative.get("last_lift", ""))
    })

    # Ensure done never > plan: if it is, adjust plan (so remain never negative)
    if cumulative["done_load"] + int(st.session_state.get("opening_load", 0)) > int(st.session_state.get("planned_load", cumulative.get("planned_load", 0))):
        st.session_state["planned_load"] = cumulative["done_load"] + int(st.session_state.get("opening_load", 0))
    if cumulative["done_disch"] + int(st.session_state.get("opening_disch", 0)) > int(st.session_state.get("planned_disch", cumulative.get("planned_disch", 0))):
        st.session_state["planned_disch"] = cumulative["done_disch"] + int(st.session_state.get("opening_disch", 0))
    if cumulative["done_restow_load"] + int(st.session_state.get("opening_restow_load", 0)) > int(st.session_state.get("planned_restow_load", cumulative.get("planned_restow_load", 0))):
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"] + int(st.session_state.get("opening_restow_load", 0))
    if cumulative["done_restow_disch"] + int(st.session_state.get("opening_restow_disch", 0)) > int(st.session_state.get("planned_restow_disch", cumulative.get("planned_restow_disch", 0))):
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"] + int(st.session_state.get("opening_restow_disch", 0))

    # push this hour into rolling 4-hour tracker (in session_state)
    add_current_hour_to_4h()

    # persist to DB
    persist_state_to_db()

    # AUTO-ADVANCE HOUR SAFELY: set an override to be applied on next run before the selectbox renders
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
    # WhatsApp_Report.py  — PART 4 / 5

# Single Generate Button (updates first, then generates template text that reflects new cumulative)
colA, colB = st.columns([1,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        # Run update first (no widgets inside)
        on_generate_hourly()
        # Now render the template (can call widgets / st.code here)
        hourly_text = generate_hourly_template_text()
        st.code(hourly_text, language="text")
with colB:
    if st.button("📤 Open WhatsApp (Hourly)"):
        # Build template from current (already updated) state and open whatsapp link
        hourly_text = generate_hourly_template_text()
        wa_text = f"```{hourly_text}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")

# Reset HOURLY inputs + safe hour advance (no experimental_rerun)
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox_moves"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
    # persist reset into DB
    persist_state_to_db()

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)

# --------------------------
# 4-Hourly Tracker & Report (auto-calculated and manual override)
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def sum_list(lst):
    return int(sum(lst)) if lst else 0

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "hours": tr.get("hours", []),
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
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
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    # show last 4 hourly labels + their splits for trace
    if calc.get("hours"):
        st.write("**Last saved hourly labels:** " + " | ".join(calc["hours"]))
        # WhatsApp_Report.py  — PART 5 / 5

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

# --- Populate 4H from computed tracker (single action button) ---
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    calc_vals = computed_4h()
    # map computed values into manual 4h session keys
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
    # Persist the manual override selection / manual values
    persist_state_to_db()
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template_text():
    remaining_load  = st.session_state["planned_load"]  - (int(cumulative.get("done_load", 0)) + int(st.session_state.get("opening_load", 0)))
    remaining_disch = st.session_state["planned_disch"] - (int(cumulative.get("done_disch", 0)) + int(st.session_state.get("opening_disch", 0)))
    remaining_restow_load  = st.session_state["planned_restow_load"]  - (int(cumulative.get("done_restow_load", 0)) + int(st.session_state.get("opening_restow_load", 0)))
    remaining_restow_disch = st.session_state["planned_restow_disch"] - (int(cumulative.get("done_restow_disch", 0)) + int(st.session_state.get("opening_restow_disch", 0)))

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
Done       {int(cumulative.get('done_load',0)) + int(st.session_state.get('opening_load',0)):>5}      {int(cumulative.get('done_disch',0)) + int(st.session_state.get('opening_disch',0)):>5}
Remain     {max(0, st.session_state['planned_load'] - (int(cumulative.get('done_load',0)) + int(st.session_state.get('opening_load',0)))):>5}      {max(0, st.session_state['planned_disch'] - (int(cumulative.get('done_disch',0)) + int(st.session_state.get('opening_disch',0)))):>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {int(cumulative.get('done_restow_load',0)) + int(st.session_state.get('opening_restow_load',0)):>5}      {int(cumulative.get('done_restow_disch',0)) + int(st.session_state.get('opening_restow_disch',0)):>5}
Remain     {max(0, st.session_state['planned_restow_load'] - (int(cumulative.get('done_restow_load',0)) + int(st.session_state.get('opening_restow_load',0)))):>5}      {max(0, st.session_state['planned_restow_disch'] - (int(cumulative.get('done_restow_disch',0)) + int(st.session_state.get('opening_restow_disch',0)))):>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template_text(), language="text")

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
        persist_state_to_db()
        st.success("4-hourly tracker reset.")

# --------------------------
# MASTER RESET
# --------------------------
def reset_all():
    # reset cumulative to defaults
    for k in list(DEFAULT_CUMULATIVE.keys()):
        cumulative[k] = DEFAULT_CUMULATIVE[k]
    # reset session-state hourly & fourh
    # hourly
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox_moves"
    ]:
        st.session_state[k] = 0
    # fourh
    st.session_state["fourh"] = empty_tracker()
    st.session_state["fourh_manual_override"] = False
    # meta
    st.session_state["vessel_name"] = DEFAULT_CUMULATIVE["vessel_name"]
    st.session_state["berthed_date"] = DEFAULT_CUMULATIVE["berthed_date"]
    st.session_state["planned_load"] = DEFAULT_CUMULATIVE["planned_load"]
    st.session_state["planned_disch"] = DEFAULT_CUMULATIVE["planned_disch"]
    st.session_state["planned_restow_load"] = DEFAULT_CUMULATIVE["planned_restow_load"]
    st.session_state["planned_restow_disch"] = DEFAULT_CUMULATIVE["planned_restow_disch"]
    st.session_state["opening_load"] = DEFAULT_CUMULATIVE["opening_load"]
    st.session_state["opening_disch"] = DEFAULT_CUMULATIVE["opening_disch"]
    st.session_state["opening_restow_load"] = DEFAULT_CUMULATIVE["opening_restow_load"]
    st.session_state["opening_restow_disch"] = DEFAULT_CUMULATIVE["opening_restow_disch"]
    st.session_state["first_lift"] = ""
    st.session_state["last_lift"] = ""
    # persist cleared state
    persist_state_to_db()

st.markdown("---")
st.header("🧹 Master Reset & Notes")
if st.button("⚠️ MASTER RESET (All Data)"):
    reset_all()
    st.success("All vessel data, hourly, 4-hourly, gearboxes and cumulative progress reset completely.")

st.text_area("📝 Notes (optional)", key="notes")
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Gearbox moves are hourly-only and shown on hourly template. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs."
    )
