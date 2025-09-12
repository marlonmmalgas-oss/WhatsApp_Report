# PART 1/5
import streamlit as st
import sqlite3
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any

# Page
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE (SQLite)
# --------------------------
DB_FILE = "vessel_report.db"
SAVE_FILE = "vessel_report.json"  # kept for compatibility/backups if needed
TZ = pytz.timezone("Africa/Johannesburg")

# Keys we expect to always exist in cumulative/meta
REQUIRED_KEYS = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "done_gearbox": 0,     # one-off hourly gearbox count (not cumulative)
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
    "first_lift": "",      # optional
    "last_lift": "",       # optional
    "_openings_applied": False  # internal flag to prevent double-applying openings
}

def connect_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if not present and ensure meta row exists."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY,
            json TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hourly_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour_label TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fourh_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_label TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # ensure meta row id=1 exists
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    if row is None:
        # insert default cumulative (REQUIRED_KEYS with defaults)
        base = dict(REQUIRED_KEYS)
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (json.dumps(base),))
        conn.commit()
    conn.close()

def load_db_meta() -> Dict[str, Any]:
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            data = json.loads(row["json"])
        except Exception:
            data = dict(REQUIRED_KEYS)
    else:
        data = dict(REQUIRED_KEYS)
    # ensure required keys present
    for k, v in REQUIRED_KEYS.items():
        if k not in data:
            data[k] = v
    return data

def save_db_meta(meta: Dict[str, Any]):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (json.dumps(meta),))
    conn.commit()
    conn.close()

# Initialize DB and load cumulative/meta
init_db()
cumulative = load_db_meta()

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
    # keep same blocks as original script
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
def init_key(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default

# date & labels (persisted meta fields should initialize session)
init_key("report_date", datetime.now(TZ).date())
# NOTE: do not set widget values by assigning widget return to session_state
# instead supply key=... to widgets later so Streamlit persists them.
init_key("vessel_name", cumulative.get("vessel_name", REQUIRED_KEYS["vessel_name"]))
init_key("berthed_date", cumulative.get("berthed_date", REQUIRED_KEYS["berthed_date"]))
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

# plans & openings (from DB meta; widgets will use these keys)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, REQUIRED_KEYS.get(k, 0)))

# HOURLY inputs (per-hour numeric widgets)
hourly_keys = [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox"  # hourly gearbox count (one-off; not cumulative)
]
for k in hourly_keys:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))
# safe override mechanism for auto-advancing hour without writing to widgets during render
init_key("hourly_time_override", None)

# FOUR-HOUR tracker (lists roll up to 4 most recent generated hours) stored in session
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "gearbox": [],  # hourly gearbox entries for last 4 hours (not cumulative)
        "count_hours": 0
    }

init_key("fourh", empty_tracker())
init_key("fourh_manual_override", False)

# manual 4h fields (editable when manual override enabled)
manual_4h_keys = [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
    "m4h_gearbox"
]
for k in manual_4h_keys:
    init_key(k, 0)

init_key("fourh_block", four_hour_blocks()[0])

# --------------------------
# SMALL HELPERS
# --------------------------
def sum_list(lst):
    return int(sum(lst)) if lst else 0

def add_current_hour_to_4h():
    """Take the current hourly widget values and append them into the rolling 4h tracker lists.
    Keep only last 4 items for each list."""
    tr = st.session_state["fourh"]
    # append hourly splits (as integers)
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

    # gearbox (hourly one-off)
    tr["gearbox"].append(int(st.session_state.get("hr_gearbox", 0)))

    # keep only last 4 entries for each list
    for k in list(tr.keys()):
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    # clear manual override fields too
    for k in manual_4h_keys:
        st.session_state[k] = 0
    st.session_state["fourh_manual_override"] = False

# End of PART 1
# PART 2/5

st.header("⚓ Vessel Info & Planning")

with st.expander("📝 Vessel & Berth Details", expanded=True):
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date/Time", key="berthed_date")
    st.text_input("First Lift (optional)", key="first_lift")
    st.text_input("Last Lift (optional)", key="last_lift")
    st.date_input("Report Date", value=st.session_state["report_date"], key="report_date")

with st.expander("📊 Planned & Opening Balances", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Planned Load", min_value=0, key="planned_load")
        st.number_input("Opening Load", min_value=0, key="opening_load")
    with c2:
        st.number_input("Planned Discharge", min_value=0, key="planned_disch")
        st.number_input("Opening Discharge", min_value=0, key="opening_disch")
    with c3:
        st.number_input("Planned Restow Load", min_value=0, key="planned_restow_load")
        st.number_input("Opening Restow Load", min_value=0, key="opening_restow_load")
    with c4:
        st.number_input("Planned Restow Disch", min_value=0, key="planned_restow_disch")
        st.number_input("Opening Restow Disch", min_value=0, key="opening_restow_disch")

st.markdown("---")
st.header("⏱️ Hourly Inputs")

# Hour selector
hours_list = hour_range_list()
if st.session_state.get("hourly_time_override"):
    # apply safe override once
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    st.session_state["hourly_time_override"] = None

st.selectbox("Select Hour", options=hours_list,
             index=hours_list.index(st.session_state["hourly_time"]),
             key="hourly_time")

# HOURLY INPUTS grouped into collapsibles
with st.expander("🟦 Crane Moves"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Load FWD", min_value=0, key="hr_fwd_load")
        st.number_input("Discharge FWD", min_value=0, key="hr_fwd_disch")
    with c2:
        st.number_input("Load MID", min_value=0, key="hr_mid_load")
        st.number_input("Discharge MID", min_value=0, key="hr_mid_disch")
    with c3:
        st.number_input("Load AFT", min_value=0, key="hr_aft_load")
        st.number_input("Discharge AFT", min_value=0, key="hr_aft_disch")
    with c4:
        st.number_input("Load POOP", min_value=0, key="hr_poop_load")
        st.number_input("Discharge POOP", min_value=0, key="hr_poop_disch")

with st.expander("🟩 Restows"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Restow Load FWD", min_value=0, key="hr_fwd_restow_load")
        st.number_input("Restow Disch FWD", min_value=0, key="hr_fwd_restow_disch")
    with c2:
        st.number_input("Restow Load MID", min_value=0, key="hr_mid_restow_load")
        st.number_input("Restow Disch MID", min_value=0, key="hr_mid_restow_disch")
    with c3:
        st.number_input("Restow Load AFT", min_value=0, key="hr_aft_restow_load")
        st.number_input("Restow Disch AFT", min_value=0, key="hr_aft_restow_disch")
    with c4:
        st.number_input("Restow Load POOP", min_value=0, key="hr_poop_restow_load")
        st.number_input("Restow Disch POOP", min_value=0, key="hr_poop_restow_disch")

with st.expander("🟨 Hatch Moves"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Hatch FWD Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("Hatch FWD Close", min_value=0, key="hr_hatch_fwd_close")
    with c2:
        st.number_input("Hatch MID Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("Hatch MID Close", min_value=0, key="hr_hatch_mid_close")
    with c3:
        st.number_input("Hatch AFT Open", min_value=0, key="hr_hatch_aft_open")
        st.number_input("Hatch AFT Close", min_value=0, key="hr_hatch_aft_close")

with st.expander("🟥 Gearbox Moves"):
    st.number_input("Total Gearboxes (this hour only)", min_value=0, key="hr_gearbox")

with st.expander("⏸️ Idle / Delays"):
    st.number_input("Number of Idle Entries", min_value=0, key="num_idle_entries")
    idle_entries = []
    for i in range(st.session_state["num_idle_entries"]):
        c1, c2, c3 = st.columns([1,1,2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}")
        end = c2.text_input(f"End {i+1}", key=f"idle_end_{i}")
        delay = c3.text_input(f"Delay {i+1}", key=f"idle_delay_{i}")
        idle_entries.append({"crane": crane, "start": start, "end": end, "delay": delay})
    st.session_state["idle_entries"] = idle_entries

st.markdown("---")
# PART 3/5

st.header("📑 Hourly Totals & Report")

def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": ss["hr_fwd_load"], "MID": ss["hr_mid_load"], "AFT": ss["hr_aft_load"], "POOP": ss["hr_poop_load"]},
        "disch":      {"FWD": ss["hr_fwd_disch"], "MID": ss["hr_mid_disch"], "AFT": ss["hr_aft_disch"], "POOP": ss["hr_poop_disch"]},
        "restow_load":{"FWD": ss["hr_fwd_restow_load"], "MID": ss["hr_mid_restow_load"], "AFT": ss["hr_aft_restow_load"], "POOP": ss["hr_poop_restow_load"]},
        "restow_disch":{"FWD": ss["hr_fwd_restow_disch"], "MID": ss["hr_mid_restow_disch"], "AFT": ss["hr_aft_restow_disch"], "POOP": ss["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": ss["hr_hatch_fwd_open"], "MID": ss["hr_hatch_mid_open"], "AFT": ss["hr_hatch_aft_open"]},
        "hatch_close":{"FWD": ss["hr_hatch_fwd_close"], "MID": ss["hr_hatch_mid_close"], "AFT": ss["hr_hatch_aft_close"]},
        "gearbox": ss["hr_gearbox"],
    }

with st.expander("🧮 Hourly Totals (split)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearboxes** — {split['gearbox']}")

# --------------------------
# Hourly Template
# --------------------------
def generate_hourly_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

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
*Gearboxes*
Total     {st.session_state['hr_gearbox']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl
    # PART 4/5

# --------------------------
# Hourly Actions
# --------------------------
def on_generate_hourly():
    # apply openings only once
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # calculate this hour
    hour_load = (st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] +
                 st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"])
    hour_disch = (st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] +
                  st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"])
    hour_restow_load = (st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] +
                        st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"])
    hour_restow_disch = (st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] +
                         st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"])
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # update cumulative
    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_restow_load)
    cumulative["done_restow_disch"] += int(hour_restow_disch)
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)

    # enforce no overflow past plan totals
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    # persist info
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

    # update 4-hour tracker
    add_current_hour_to_4h()

    # advance hour
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    # return template text
    return generate_hourly_template()

# --- Buttons ---
col1, col2 = st.columns([1,1])
with col1:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        txt = on_generate_hourly()
        st.code(txt, language="text")
with col2:
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

# Reset Hourly
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
# PART 5/5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# 4-hour block selector
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

# --- 4H Calculations ---
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
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"],
        "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"],
        "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"],
        "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"],
        "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"],
        "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"],
        "hatch_aft_close": ss["m4h_hatch_aft_close"],
        "gearbox": ss.get("m4h_gearbox", 0),
    }

# Auto totals
with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    st.write(f"**Gearbox Total:** {calc['gearbox']}")

# Manual override
with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto-calculated", key="fourh_manual_override")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("FWD Load 4H", min_value=0, key="m4h_fwd_load")
        st.number_input("FWD Disch 4H", min_value=0, key="m4h_fwd_disch")
        st.number_input("FWD Rst Load 4H", min_value=0, key="m4h_fwd_restow_load")
        st.number_input("FWD Rst Disch 4H", min_value=0, key="m4h_fwd_restow_disch")
    with c2:
        st.number_input("MID Load 4H", min_value=0, key="m4h_mid_load")
        st.number_input("MID Disch 4H", min_value=0, key="m4h_mid_disch")
        st.number_input("MID Rst Load 4H", min_value=0, key="m4h_mid_restow_load")
        st.number_input("MID Rst Disch 4H", min_value=0, key="m4h_mid_restow_disch")
    with c3:
        st.number_input("AFT Load 4H", min_value=0, key="m4h_aft_load")
        st.number_input("AFT Disch 4H", min_value=0, key="m4h_aft_disch")
        st.number_input("AFT Rst Load 4H", min_value=0, key="m4h_aft_restow_load")
        st.number_input("AFT Rst Disch 4H", min_value=0, key="m4h_aft_restow_disch")
    with c4:
        st.number_input("POOP Load 4H", min_value=0, key="m4h_poop_load")
        st.number_input("POOP Disch 4H", min_value=0, key="m4h_poop_disch")
        st.number_input("POOP Rst Load 4H", min_value=0, key="m4h_poop_restow_load")
        st.number_input("POOP Rst Disch 4H", min_value=0, key="m4h_poop_restow_disch")
        st.number_input("Gearbox 4H", min_value=0, key="m4h_gearbox")

# Select values
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

# --- 4H Template ---
def generate_4h_template():
    remaining_load = st.session_state["planned_load"] - cumulative["done_load"] - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load = st.session_state["planned_restow_load"] - cumulative["done_restow_load"] - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift @ {st.session_state['first_lift']}
Last Lift @ {st.session_state['last_lift']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {vals4h['fwd_load']:>5}     {vals4h['fwd_disch']:>5}
MID       {vals4h['mid_load']:>5}     {vals4h['mid_disch']:>5}
AFT       {vals4h['aft_load']:>5}     {vals4h['aft_disch']:>5}
POOP      {vals4h['poop_load']:>5}    {vals4h['poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {vals4h['fwd_restow_load']:>5}     {vals4h['fwd_restow_disch']:>5}
MID       {vals4h['mid_restow_load']:>5}     {vals4h['mid_restow_disch']:>5}
AFT       {vals4h['aft_restow_load']:>5}     {vals4h['aft_restow_disch']:>5}
POOP      {vals4h['poop_restow_load']:>5}    {vals4h['poop_restow_disch']:>5}
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
FWD       {vals4h['hatch_fwd_open']:>5}      {vals4h['hatch_fwd_close']:>5}
MID       {vals4h['hatch_mid_open']:>5}      {vals4h['hatch_mid_close']:>5}
AFT       {vals4h['hatch_aft_open']:>5}      {vals4h['hatch_aft_close']:>5}
_________________________
*Gearbox*
Total     {vals4h['gearbox']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

# Display template
st.code(generate_4h_template(), language="text")

# WhatsApp
st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("✅ Generate 4-Hourly Template"):
        st.code(generate_4h_template(), language="text")
with colB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template()
        wa_text = f"```{t}```"
        if st.session_state.get("wa_num_4h"):
            link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_4h"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")
with colC:
    if st.button("🔄 Reset 4-Hourly Tracker"):
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")

# --- Master Reset ---
def master_reset():
    st.session_state.clear()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.success("🔄 Master reset complete. All data cleared.")

st.button("🛑 Master Reset (clear everything)", on_click=master_reset)

st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Reset buttons clear values but do not loop. "
    "• Master Reset clears everything including vessel info."
    )
