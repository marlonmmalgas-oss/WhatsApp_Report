# PART 1/5
import streamlit as st
import json
import os
import urllib.parse
import sqlite3
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE
# --------------------------
SAVE_DB = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# Default cumulative (used only if DB empty)
DEFAULT_CUMULATIVE = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "_openings_applied": False,   # internal flag to avoid re-applying opening balances
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
# SQLite helpers
# --------------------------
def get_conn():
    return sqlite3.connect(SAVE_DB, timeout=10, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # initialize cumulative and fourh if not present
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(DEFAULT_CUMULATIVE)))
    cur.execute("SELECT value FROM meta WHERE key='fourh';")
    row = cur.fetchone()
    if not row:
        # empty 4h tracker preserves per-position lists and hours list
        empty_fourh = {
            "hours": [],
            "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
            "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
            "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
            "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
            "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
            "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
            "count_hours": 0,
        }
        cur.execute("INSERT INTO meta (key, value) VALUES (?, ?);", ("fourh", json.dumps(empty_fourh)))
    conn.commit()
    conn.close()

def load_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    cumulative = DEFAULT_CUMULATIVE.copy()
    if row:
        try:
            cumulative.update(json.loads(row[0]))
        except Exception:
            pass
    cur.execute("SELECT value FROM meta WHERE key='fourh';")
    row = cur.fetchone()
    fourh = None
    if row:
        try:
            fourh = json.loads(row[0])
        except Exception:
            fourh = None
    conn.close()
    if fourh is None:
        # fallback
        fourh = {
            "hours": [],
            "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
            "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
            "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
            "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
            "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
            "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
            "count_hours": 0,
        }
    return cumulative, fourh

def save_db_cumulative(cumulative):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?);", ("cumulative", json.dumps(cumulative)))
    conn.commit()
    conn.close()

def save_db_fourh(fourh):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?);", ("fourh", json.dumps(fourh)))
    conn.commit()
    conn.close()

# ensure DB exists and load
init_db()
cumulative_db, fourh_db = load_db()

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
    # PART 2/5
# --------------------------
# SESSION STATE INIT (use DB values as defaults)
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# date & labels
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative_db.get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"]))
init_key("berthed_date", cumulative_db.get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"]))

# plans & openings (from DB, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative_db.get(k, DEFAULT_CUMULATIVE[k]))

# also keep cumulative done values in memory (read-only in UI)
init_key("done_load", cumulative_db.get("done_load", 0))
init_key("done_disch", cumulative_db.get("done_disch", 0))
init_key("done_restow_load", cumulative_db.get("done_restow_load", 0))
init_key("done_restow_disch", cumulative_db.get("done_restow_disch", 0))
init_key("done_hatch_open", cumulative_db.get("done_hatch_open", 0))
init_key("done_hatch_close", cumulative_db.get("done_hatch_close", 0))

# HOURLY inputs (default 0 or empty)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    # new hourly-only inputs:
    "hr_gearbox",    # numeric: hourly gearbox total (not cumulative)
    "hr_first_lift",  # string / time
    "hr_last_lift",   # string / time
]:
    init_key(k, 0 if "hr_" in k and ("load" in k or "disch" in k or "gearbox" in k or "hatch" in k) else "")

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly) - use DB last_hour default
hours_list = hour_range_list()
init_key("hourly_time", cumulative_db.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker: load DB value into session_state["fourh"]
init_key("fourh", fourh_db)
init_key("fourh_manual_override", False)

# manual 4h override inputs
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

# --------------------------
# Small helpers (same semantics)
# --------------------------
def sum_list(lst):
    return int(sum(lst)) if lst else 0

def empty_tracker():
    return {
        "hours": [],
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
    }

def add_current_hour_to_4h():
    tr = st.session_state["fourh"]
    # append label for auditing
    tr["hours"].append(st.session_state["hourly_time"])
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
    for k in list(tr.keys()):
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)
    # persist to DB
    save_db_fourh(tr)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    save_db_fourh(st.session_state["fourh"])

def master_reset():
    # Reset everything including DB meta to defaults
    save_db_cumulative(DEFAULT_CUMULATIVE.copy())
    save_db_fourh(empty_tracker())
    # reset session_state keys to defaults (but don't crash if missing)
    for k, v in DEFAULT_CUMULATIVE.items():
        st.session_state[k] = v
    st.session_state["done_load"] = DEFAULT_CUMULATIVE["done_load"]
    st.session_state["done_disch"] = DEFAULT_CUMULATIVE["done_disch"]
    st.session_state["done_restow_load"] = DEFAULT_CUMULATIVE["done_restow_load"]
    st.session_state["done_restow_disch"] = DEFAULT_CUMULATIVE["done_restow_disch"]
    st.session_state["done_hatch_open"] = DEFAULT_CUMULATIVE["done_hatch_open"]
    st.session_state["done_hatch_close"] = DEFAULT_CUMULATIVE["done_hatch_close"]
    st.session_state["fourh"] = empty_tracker()
    st.success("Master reset performed. Application state persisted.")
    # PART 3/5
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel (inputs use keys only)
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
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

# Hour selector (with safe override handoff)
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = cumulative_db.get("last_hour", hour_range_list()[0])

st.selectbox("⏱ Select Hourly Time", options=hour_range_list(),
             index=hour_range_list().index(st.session_state["hourly_time"]),
             key="hourly_time")

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge) — keep collapsibles as original
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

# Gearbox + first/last lift (hourly inputs)
with st.expander("⚙️ Gearbox / Lifts (Hourly)"):
    st.number_input("Gearbox Total (hourly, transient)", min_value=0, key="hr_gearbox")
    st.text_input("First Lift (e.g., 06h10)", key="hr_first_lift")
    st.text_input("Last Lift (e.g., 06h58)", key="hr_last_lift")

# Idle / Delays
st.subheader("⏸️ Idle / Delays")
idle_options = [
    "Stevedore tea time/shift change","Awaiting cargo","Awaiting AGL operations","Awaiting FPT gang",
    "Awaiting Crane driver","Awaiting onboard stevedores","Windbound","Crane break down/ wipers",
    "Crane break down/ lights","Crane break down/ boom limit","Crane break down","Vessel listing",
    "Struggling to load container","Cell guide struggles","Spreader difficulties",
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
    # PART 4/5
# --------------------------
# Hourly Totals Tracker (split by position)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": int(ss.get("hr_fwd_load",0)), "MID": int(ss.get("hr_mid_load",0)), "AFT": int(ss.get("hr_aft_load",0)), "POOP": int(ss.get("hr_poop_load",0))},
        "disch":      {"FWD": int(ss.get("hr_fwd_disch",0)), "MID": int(ss.get("hr_mid_disch",0)), "AFT": int(ss.get("hr_aft_disch",0)), "POOP": int(ss.get("hr_poop_disch",0))},
        "restow_load":{"FWD": int(ss.get("hr_fwd_restow_load",0)), "MID": int(ss.get("hr_mid_restow_load",0)), "AFT": int(ss.get("hr_aft_restow_load",0)), "POOP": int(ss.get("hr_poop_restow_load",0))},
        "restow_disch":{"FWD": int(ss.get("hr_fwd_restow_disch",0)), "MID": int(ss.get("hr_mid_restow_disch",0)), "AFT": int(ss.get("hr_aft_restow_disch",0)), "POOP": int(ss.get("hr_poop_restow_disch",0))},
        "hatch_open": {"FWD": int(ss.get("hr_hatch_fwd_open",0)), "MID": int(ss.get("hr_hatch_mid_open",0)), "AFT": int(ss.get("hr_hatch_aft_open",0))},
        "hatch_close":{"FWD": int(ss.get("hr_hatch_fwd_close",0)), "MID": int(ss.get("hr_hatch_mid_close",0)), "AFT": int(ss.get("hr_hatch_aft_close",0))},
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
# WhatsApp (Hourly) template (single Generate button behaviour)
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    # current split + gearbox + lifts will be embedded
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
FWD       {int(st.session_state.get('hr_fwd_load',0)):>5}     {int(st.session_state.get('hr_fwd_disch',0)):>5}
MID       {int(st.session_state.get('hr_mid_load',0)):>5}     {int(st.session_state.get('hr_mid_disch',0)):>5}
AFT       {int(st.session_state.get('hr_aft_load',0)):>5}     {int(st.session_state.get('hr_aft_disch',0)):>5}
POOP      {int(st.session_state.get('hr_poop_load',0)):>5}     {int(st.session_state.get('hr_poop_disch',0)):>5}
_________________________
*Restows*
           Load   Discharge
FWD       {int(st.session_state.get('hr_fwd_restow_load',0)):>5}     {int(st.session_state.get('hr_fwd_restow_disch',0)):>5}
MID       {int(st.session_state.get('hr_mid_restow_load',0)):>5}     {int(st.session_state.get('hr_mid_restow_disch',0)):>5}
AFT       {int(st.session_state.get('hr_aft_restow_load',0)):>5}     {int(st.session_state.get('hr_aft_restow_disch',0)):>5}
POOP      {int(st.session_state.get('hr_poop_restow_load',0)):>5}     {int(st.session_state.get('hr_poop_restow_disch',0)):>5}
_________________________
*Gearbox*
Total (this hour): {int(st.session_state.get('hr_gearbox',0))}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {int(st.session_state['planned_load']):>5}      {int(st.session_state['planned_disch']):>5}
Done       {int(st.session_state['done_load']):>5}      {int(st.session_state['done_disch']):>5}
Remain     {max(0, int(st.session_state['planned_load']) - int(st.session_state['done_load'])):>5}      {max(0, int(st.session_state['planned_disch']) - int(st.session_state['done_disch'])):>5}
_________________________
*Restows*
           Load   Disch
Plan       {int(st.session_state['planned_restow_load']):>5}      {int(st.session_state['planned_restow_disch']):>5}
Done       {int(st.session_state['done_restow_load']):>5}      {int(st.session_state['done_restow_disch']):>5}
Remain     {max(0, int(st.session_state['planned_restow_load']) - int(st.session_state['done_restow_load'])):>5}      {max(0, int(st.session_state['planned_restow_disch']) - int(st.session_state['done_restow_disch'])):>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {int(st.session_state.get('hr_hatch_fwd_open',0)):>5}      {int(st.session_state.get('hr_hatch_fwd_close',0)):>5}
MID       {int(st.session_state.get('hr_hatch_mid_open',0)):>5}      {int(st.session_state.get('hr_hatch_mid_close',0)):>5}
AFT       {int(st.session_state.get('hr_hatch_aft_open',0)):>5}      {int(st.session_state.get('hr_hatch_aft_close',0)):>5}
_________________________
*First / Last Lift*
First Lift: {st.session_state.get('hr_first_lift','')}
Last Lift:  {st.session_state.get('hr_last_lift','')}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# Core: on_generate_hourly does all updates (cumulative, 4h tracker, apply opening once, save DB, and advance hour)
def on_generate_hourly():
    # 1) apply openings ONCE to cumulative_db if not applied
    if not cumulative_db.get("_openings_applied", False):
        cumulative_db["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative_db["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative_db["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative_db["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative_db["_openings_applied"] = True

    # 2) sum this hour's inputs
    hour_load = int(st.session_state.get("hr_fwd_load",0)) + int(st.session_state.get("hr_mid_load",0)) + int(st.session_state.get("hr_aft_load",0)) + int(st.session_state.get("hr_poop_load",0))
    hour_disch = int(st.session_state.get("hr_fwd_disch",0)) + int(st.session_state.get("hr_mid_disch",0)) + int(st.session_state.get("hr_aft_disch",0)) + int(st.session_state.get("hr_poop_disch",0))
    hour_restow_load = int(st.session_state.get("hr_fwd_restow_load",0)) + int(st.session_state.get("hr_mid_restow_load",0)) + int(st.session_state.get("hr_aft_restow_load",0)) + int(st.session_state.get("hr_poop_restow_load",0))
    hour_restow_disch = int(st.session_state.get("hr_fwd_restow_disch",0)) + int(st.session_state.get("hr_mid_restow_disch",0)) + int(st.session_state.get("hr_aft_restow_disch",0)) + int(st.session_state.get("hr_poop_restow_disch",0))
    hour_hatch_open = int(st.session_state.get("hr_hatch_fwd_open",0)) + int(st.session_state.get("hr_hatch_mid_open",0)) + int(st.session_state.get("hr_hatch_aft_open",0))
    hour_hatch_close = int(st.session_state.get("hr_hatch_fwd_close",0)) + int(st.session_state.get("hr_hatch_mid_close",0)) + int(st.session_state.get("hr_hatch_aft_close",0))

    # 3) update cumulative_db
    cumulative_db["done_load"] += hour_load
    cumulative_db["done_disch"] += hour_disch
    cumulative_db["done_restow_load"] += hour_restow_load
    cumulative_db["done_restow_disch"] += hour_restow_disch
    cumulative_db["done_hatch_open"] += hour_hatch_open
    cumulative_db["done_hatch_close"] += hour_hatch_close

    # 4) enforce done <= plan by bumping plan if done > plan (so remain never negative)
    if cumulative_db["done_load"] > int(st.session_state.get("planned_load", cumulative_db["planned_load"])):
        cumulative_db["planned_load"] = cumulative_db["done_load"]
    if cumulative_db["done_disch"] > int(st.session_state.get("planned_disch", cumulative_db["planned_disch"])):
        cumulative_db["planned_disch"] = cumulative_db["done_disch"]
    if cumulative_db["done_restow_load"] > int(st.session_state.get("planned_restow_load", cumulative_db["planned_restow_load"])):
        cumulative_db["planned_restow_load"] = cumulative_db["done_restow_load"]
    if cumulative_db["done_restow_disch"] > int(st.session_state.get("planned_restow_disch", cumulative_db["planned_restow_disch"])):
        cumulative_db["planned_restow_disch"] = cumulative_db["done_restow_disch"]

    # 5) persist user-editable meta (vessel, berthed, plans, openings, last_hour)
    cumulative_db.update({
        "vessel_name": st.session_state.get("vessel_name", cumulative_db.get("vessel_name")),
        "berthed_date": st.session_state.get("berthed_date", cumulative_db.get("berthed_date")),
        "planned_load": int(st.session_state.get("planned_load", cumulative_db.get("planned_load"))),
        "planned_disch": int(st.session_state.get("planned_disch", cumulative_db.get("planned_disch"))),
        "planned_restow_load": int(st.session_state.get("planned_restow_load", cumulative_db.get("planned_restow_load"))),
        "planned_restow_disch": int(st.session_state.get("planned_restow_disch", cumulative_db.get("planned_restow_disch"))),
        "opening_load": int(st.session_state.get("opening_load", cumulative_db.get("opening_load"))),
        "opening_disch": int(st.session_state.get("opening_disch", cumulative_db.get("opening_disch"))),
        "opening_restow_load": int(st.session_state.get("opening_restow_load", cumulative_db.get("opening_restow_load"))),
        "opening_restow_disch": int(st.session_state.get("opening_restow_disch", cumulative_db.get("opening_restow_disch"))),
        "last_hour": st.session_state["hourly_time"],
    })
    # Save cumulative to DB
    save_db_cumulative(cumulative_db)

    # 6) copy cumulative values into session_state read-only mirrors (so template shows updated Done immediately)
    st.session_state["done_load"] = cumulative_db["done_load"]
    st.session_state["done_disch"] = cumulative_db["done_disch"]
    st.session_state["done_restow_load"] = cumulative_db["done_restow_load"]
    st.session_state["done_restow_disch"] = cumulative_db["done_restow_disch"]
    st.session_state["done_hatch_open"] = cumulative_db["done_hatch_open"]
    st.session_state["done_hatch_close"] = cumulative_db["done_hatch_close"]

    # 7) push this hour into rolling 4-hour tracker & persist
    add_current_hour_to_4h()

    # 8) advance hour (safe override so selectbox won't be overwritten during render)
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    # 9) return the generated text so caller can display
    return generate_hourly_template_text()

# Buttons: single generate (no preview button)
colA, colB = st.columns([1,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        txt = on_generate_hourly()
        st.code(txt, language="text")
        # persist session-level copies of cumulative to DB (already saved)
with colB:
    if st.button("📤 Open WhatsApp (Hourly)"):
        # open last generated template (generate fresh to ensure latest)
        txt = generate_hourly_template_text()
        wa_text = f"```{txt}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")
            # PART 5/5
# Reset HOURLY inputs + safe hour advance
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox","hr_first_lift","hr_last_lift",
    ]:
        # reset widget-backed keys
        st.session_state[k] = 0 if isinstance(st.session_state.get(k, 0), int) else ""
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)

# --------------------------
# 4-Hourly Tracker & Report
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

def computed_4h():
    tr = st.session_state["fourh"]
    return {
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

# Manual override inputs (collapsed)
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

# Populate button: map computed 4H into manual fields
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
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

# Generate 4H template text
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template_text():
    remaining_load  = st.session_state["planned_load"]  - st.session_state["done_load"]
    remaining_disch = st.session_state["planned_disch"] - st.session_state["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - st.session_state["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - st.session_state["done_restow_disch"]

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
Done       {st.session_state['done_load']:>5}      {st.session_state['done_disch']:>5}
Remain     {max(0, st.session_state['planned_load'] - st.session_state['done_load']):>5}      {max(0, st.session_state['planned_disch'] - st.session_state['done_disch']):>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {st.session_state['done_restow_load']:>5}      {st.session_state['done_restow_disch']:>5}
Remain     {max(0, st.session_state['planned_restow_load'] - st.session_state['done_restow_load']):>5}      {max(0, st.session_state['planned_restow_disch'] - st.session_state['done_restow_disch']):>5}
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

# 4H WhatsApp/send and reset
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
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")

# show last 4 hourly splits summary (human readable)
with st.expander("📜 Last 4 hourly splits summary (audit)"):
    tr = st.session_state["fourh"]
    hours = tr.get("hours", [])
    for i, label in enumerate(hours):
        st.write(f"Hour: {label}")
        st.write(f"  Load — FWD {tr['fwd_load'][i]} | MID {tr['mid_load'][i]} | AFT {tr['aft_load'][i]} | POOP {tr['poop_load'][i]}")
        st.write(f"  Disch— FWD {tr['fwd_disch'][i]} | MID {tr['mid_disch'][i]} | AFT {tr['aft_disch'][i]} | POOP {tr['poop_disch'][i]}")
        st.write("---")

# Master reset button
if st.button("⚠️ Master Reset (resets everything)"):
    master_reset()

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs."
    )
