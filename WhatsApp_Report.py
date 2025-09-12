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
# CONSTANTS & PERSISTENCE
# --------------------------
DB_FILE = "vessel_report.db"
SAVE_FILE = "vessel_report.json"  # kept for compatibility/backups if needed
TZ = pytz.timezone("Africa/Johannesburg")

# default cumulative (used when DB empty)
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
    "last_lift": "",
    "_openings_applied": False
}

# --------------------------
# SQLITE DB helpers
# --------------------------
def init_db():
    """Initialize DB and meta row for cumulative if missing."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # ensure cumulative exists
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO meta (key, value) VALUES ('cumulative', ?);", (json.dumps(DEFAULT_CUMULATIVE),))
        conn.commit()
    conn.close()

def load_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return DEFAULT_CUMULATIVE.copy()
    return DEFAULT_CUMULATIVE.copy()

def save_db(cumulative_obj):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("REPLACE INTO meta (key, value) VALUES ('cumulative', ?);", (json.dumps(cumulative_obj),))
    conn.commit()
    conn.close()

# ensure DB exists before loading cumulative
init_db()
cumulative = load_db()
# protect against missing fields
for k, v in DEFAULT_CUMULATIVE.items():
    if k not in cumulative:
        cumulative[k] = v

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

# date & labels (only initialize if not already set in session)
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"]))
init_key("berthed_date", cumulative.get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"]))
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

# plans & openings (from DB, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, DEFAULT_CUMULATIVE.get(k, 0)))

# HOURLY inputs (hourly-only gearbox included)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox"   # hourly gearbox number (does not accumulate)
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
        "count_hours": 0,
        "snapshots": []  # keep last N snapshots (for summary)
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
]:
    init_key(k, 0)

init_key("fourh_block", four_hour_blocks()[0])

# --------------------------
# SMALL HELPERS
# --------------------------
def sum_list(lst):
    return int(sum(lst)) if lst else 0

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

    # snapshot for summary (store split snapshot)
    snapshot = {
        "hour": st.session_state["hourly_time"],
        "load": {"FWD": st.session_state["hr_fwd_load"], "MID": st.session_state["hr_mid_load"], "AFT": st.session_state["hr_aft_load"], "POOP": st.session_state["hr_poop_load"]},
        "disch": {"FWD": st.session_state["hr_fwd_disch"], "MID": st.session_state["hr_mid_disch"], "AFT": st.session_state["hr_aft_disch"], "POOP": st.session_state["hr_poop_disch"]},
        "restow_load": {"FWD": st.session_state["hr_fwd_restow_load"], "MID": st.session_state["hr_mid_restow_load"], "AFT": st.session_state["hr_aft_restow_load"], "POOP": st.session_state["hr_poop_restow_load"]},
        "restow_disch": {"FWD": st.session_state["hr_fwd_restow_disch"], "MID": st.session_state["hr_mid_restow_disch"], "AFT": st.session_state["hr_aft_restow_disch"], "POOP": st.session_state["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": st.session_state["hr_hatch_fwd_open"], "MID": st.session_state["hr_hatch_mid_open"], "AFT": st.session_state["hr_hatch_aft_open"]},
        "hatch_close": {"FWD": st.session_state["hr_hatch_fwd_close"], "MID": st.session_state["hr_hatch_mid_close"], "AFT": st.session_state["hr_hatch_aft_close"]},
    }

    tr["snapshots"].append(snapshot)

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    # persist to DB as well
    cumulative["fourh"] = st.session_state["fourh"]
    save_db(cumulative)
    # WhatsApp_Report.py  — PART 2 / 5 (UI top / inputs)

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # DO NOT assign back into session_state; widget keys only (we update DB via 'Save Settings')
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.text_input("First Lift (optional)", key="first_lift")
    st.text_input("Last Lift (optional)", key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date")

# Save settings button to persist vessel/plan/opening/first/last etc to DB immediately
if st.button("💾 Save Settings (persist to DB)"):
    # copy session values to cumulative and persist
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "planned_load": int(st.session_state.get("planned_load", 0)),
        "planned_disch": int(st.session_state.get("planned_disch", 0)),
        "planned_restow_load": int(st.session_state.get("planned_restow_load", 0)),
        "planned_restow_disch": int(st.session_state.get("planned_restow_disch", 0)),
        "opening_load": int(st.session_state.get("opening_load", 0)),
        "opening_disch": int(st.session_state.get("opening_disch", 0)),
        "opening_restow_load": int(st.session_state.get("opening_restow_load", 0)),
        "opening_restow_disch": int(st.session_state.get("opening_restow_disch", 0)),
        "first_lift": st.session_state.get("first_lift", ""),
        "last_lift": st.session_state.get("last_lift", ""),
    })
    save_db(cumulative)
    st.success("Settings saved to DB. These will persist across devices.")

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
# Gearbox (hourly only)
# --------------------------
with st.expander("⚙️ Gearbox (hourly total only)"):
    st.number_input("Gearbox Total (this hour only)", min_value=0, key="hr_gearbox")
    # WhatsApp_Report.py  — PART 3 / 5 (Hourly totals split + WhatsApp hourly template)

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
# Hourly Totals Tracker (split by position only)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": int(ss["hr_fwd_load"]),       "MID": int(ss["hr_mid_load"]),       "AFT": int(ss["hr_aft_load"]),       "POOP": int(ss["hr_poop_load"])},
        "disch":      {"FWD": int(ss["hr_fwd_disch"]),      "MID": int(ss["hr_mid_disch"]),      "AFT": int(ss["hr_aft_disch"]),      "POOP": int(ss["hr_poop_disch"])},
        "restow_load":{"FWD": int(ss["hr_fwd_restow_load"]), "MID": int(ss["hr_mid_restow_load"]), "AFT": int(ss["hr_aft_restow_load"]), "POOP": int(ss["hr_poop_restow_load"])},
        "restow_disch":{"FWD": int(ss["hr_fwd_restow_disch"]), "MID": int(ss["hr_mid_restow_disch"]), "AFT": int(ss["hr_aft_restow_disch"]), "POOP": int(ss["hr_poop_restow_disch"])},
        "hatch_open": {"FWD": int(ss["hr_hatch_fwd_open"]), "MID": int(ss["hr_hatch_mid_open"]), "AFT": int(ss["hr_hatch_aft_open"])},
        "hatch_close":{"FWD": int(ss["hr_hatch_fwd_close"]), "MID": int(ss["hr_hatch_mid_close"]), "AFT": int(ss["hr_hatch_aft_close"])},
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
# WhatsApp (Hourly) – original monospace template — Generate updates DB first then displays updated template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    # compute remaining using current cumulative (which is up-to-date)
    remaining_load  = int(st.session_state["planned_load"])  - cumulative["done_load"]
    remaining_disch = int(st.session_state["planned_disch"]) - cumulative["done_disch"]
    remaining_restow_load  = int(st.session_state["planned_restow_load"])  - cumulative["done_restow_load"]
    remaining_restow_disch = int(st.session_state["planned_restow_disch"]) - cumulative["done_restow_disch"]

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift: {st.session_state.get('first_lift','')}
Last Lift:  {st.session_state.get('last_lift','')}

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
*Gearboxes (this hour only)*: {st.session_state['hr_gearbox']}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

def apply_openings_once():
    # apply opening balances to cumulative on the first generate after load
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

        # ensure Done never > Plan; if so, increase plan to match
        if cumulative["done_load"] > int(st.session_state.get("planned_load", 0)):
            st.session_state["planned_load"] = cumulative["done_load"]
            cumulative["planned_load"] = cumulative["done_load"]
        if cumulative["done_disch"] > int(st.session_state.get("planned_disch", 0)):
            st.session_state["planned_disch"] = cumulative["done_disch"]
            cumulative["planned_disch"] = cumulative["done_disch"]
        if cumulative["done_restow_load"] > int(st.session_state.get("planned_restow_load", 0)):
            st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
            cumulative["planned_restow_load"] = cumulative["done_restow_load"]
        if cumulative["done_restow_disch"] > int(st.session_state.get("planned_restow_disch", 0)):
            st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]
            cumulative["planned_restow_disch"] = cumulative["done_restow_disch"]

def on_generate_hourly():
    # 1) Apply opening balances once (so they count as done before we add this hour moves)
    apply_openings_once()

    # 2) Sum current hour inputs
    hour_load = int(st.session_state["hr_fwd_load"]) + int(st.session_state["hr_mid_load"]) + int(st.session_state["hr_aft_load"]) + int(st.session_state["hr_poop_load"])
    hour_disch = int(st.session_state["hr_fwd_disch"]) + int(st.session_state["hr_mid_disch"]) + int(st.session_state["hr_aft_disch"]) + int(st.session_state["hr_poop_disch"])
    hour_restow_load = (
        int(st.session_state["hr_fwd_restow_load"]) + int(st.session_state["hr_mid_restow_load"]) +
        int(st.session_state["hr_aft_restow_load"]) + int(st.session_state["hr_poop_restow_load"])
    )
    hour_restow_disch = (
        int(st.session_state["hr_fwd_restow_disch"]) + int(st.session_state["hr_mid_restow_disch"]) +
        int(st.session_state["hr_aft_restow_disch"]) + int(st.session_state["hr_poop_restow_disch"])
    )
    hour_hatch_open = int(st.session_state["hr_hatch_fwd_open"]) + int(st.session_state["hr_hatch_mid_open"]) + int(st.session_state["hr_hatch_aft_open"])
    hour_hatch_close = int(st.session_state["hr_hatch_fwd_close"]) + int(st.session_state["hr_hatch_mid_close"]) + int(st.session_state["hr_hatch_aft_close"])

    # 3) Update cumulative totals immediately (so template will reflect this)
    cumulative["done_load"] += hour_load
    cumulative["done_disch"] += hour_disch
    cumulative["done_restow_load"] += hour_restow_load
    cumulative["done_restow_disch"] += hour_restow_disch
    cumulative["done_hatch_open"] += hour_hatch_open
    cumulative["done_hatch_close"] += hour_hatch_close

    # if done exceeds plan, adjust plan upward to avoid negative remain
    if cumulative["done_load"] > int(st.session_state.get("planned_load", 0)):
        st.session_state["planned_load"] = cumulative["done_load"]
        cumulative["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > int(st.session_state.get("planned_disch", 0)):
        st.session_state["planned_disch"] = cumulative["done_disch"]
        cumulative["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > int(st.session_state.get("planned_restow_load", 0)):
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
        cumulative["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > int(st.session_state.get("planned_restow_disch", 0)):
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]
        cumulative["planned_restow_disch"] = cumulative["done_restow_disch"]

    # 4) Persist meta/settings as well (so changes survive devices)
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "planned_load": int(st.session_state.get("planned_load", 0)),
        "planned_disch": int(st.session_state.get("planned_disch", 0)),
        "planned_restow_load": int(st.session_state.get("planned_restow_load", 0)),
        "planned_restow_disch": int(st.session_state.get("planned_restow_disch", 0)),
        "opening_load": int(st.session_state.get("opening_load", 0)),
        "opening_disch": int(st.session_state.get("opening_disch", 0)),
        "opening_restow_load": int(st.session_state.get("opening_restow_load", 0)),
        "opening_restow_disch": int(st.session_state.get("opening_restow_disch", 0)),
        "first_lift": st.session_state.get("first_lift", ""),
        "last_lift": st.session_state.get("last_lift", ""),
        "last_hour": st.session_state["hourly_time"],
        "fourh": st.session_state["fourh"]
    })
    save_db(cumulative)

    # 5) add current hour to 4h rolling tracker (and snapshot)
    add_current_hour_to_4h()
    cumulative["fourh"] = st.session_state["fourh"]
    save_db(cumulative)

    # 6) Prepare next-hour advance (safe override so we don't write widget during render)
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    # 7) After updating DB, return the text for display (template will show updated cumulative)
    return generate_hourly_template_text()

colA, colB = st.columns([1,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        # call on_generate_hourly first to update cumulative then show updated template
        txt = on_generate_hourly()
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

# Reset HOURLY inputs + safe hour advance (no experimental_rerun)
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
# WhatsApp_Report.py  — PART 4 / 5 (4-hourly tracker & template)

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
        "fwd_load": int(ss["m4h_fwd_load"]), "mid_load": int(ss["m4h_mid_load"]), "aft_load": int(ss["m4h_aft_load"]), "poop_load": int(ss["m4h_poop_load"]),
        "fwd_disch": int(ss["m4h_fwd_disch"]), "mid_disch": int(ss["m4h_mid_disch"]), "aft_disch": int(ss["m4h_aft_disch"]), "poop_disch": int(ss["m4h_poop_disch"]),
        "fwd_restow_load": int(ss["m4h_fwd_restow_load"]), "mid_restow_load": int(ss["m4h_mid_restow_load"]), "aft_restow_load": int(ss["m4h_aft_restow_load"]), "poop_restow_load": int(ss["m4h_poop_restow_load"]),
        "fwd_restow_disch": int(ss["m4h_fwd_restow_disch"]), "mid_restow_disch": int(ss["m4h_mid_restow_disch"]), "aft_restow_disch": int(ss["m4h_aft_restow_disch"]), "poop_restow_disch": int(ss["m4h_poop_restow_disch"]),
        "hatch_fwd_open": int(ss["m4h_hatch_fwd_open"]), "hatch_mid_open": int(ss["m4h_hatch_mid_open"]), "hatch_aft_open": int(ss["m4h_hatch_aft_open"]),
        "hatch_fwd_close": int(ss["m4h_hatch_fwd_close"]), "hatch_mid_close": int(ss["m4h_hatch_mid_close"]), "hatch_aft_close": int(ss["m4h_hatch_aft_close"]),
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")

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

# --- NEW BUTTON: populate manual 4H fields from computed 4H tracker ---
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

    # enable manual override so template will use these values
    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    remaining_load  = int(st.session_state["planned_load"])  - cumulative["done_load"]
    remaining_disch = int(st.session_state["planned_disch"]) - cumulative["done_disch"]
    remaining_restow_load  = int(st.session_state["planned_restow_load"])  - cumulative["done_restow_load"]
    remaining_restow_disch = int(st.session_state["planned_restow_disch"]) - cumulative["done_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift: {st.session_state.get('first_lift','')}
Last Lift:  {st.session_state.get('last_lift','')}

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
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
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

# Render 4H template and buttons
st.code(generate_4h_template(), language="text")

st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB, cC = st.columns([1,1,1])
with cA:
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
with cB:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        reset_4h_tracker()
        cumulative["fourh"] = st.session_state["fourh"]
        save_db(cumulative)
        st.success("4-hourly tracker reset.")
with cC:
    # Master reset - resets DB + session_state values (use with caution)
    if st.button("⚠️ Master Reset (clear everything)"):
        # Reset cumulative to defaults and clear DB entry
        cumulative.clear()
        cumulative.update(DEFAULT_CUMULATIVE.copy())
        save_db(cumulative)
        # clear session keys (preserve UI by reloading values)
        for k in list(st.session_state.keys()):
            # keep built-in Streamlit keys
            if k.startswith("run_") or k.startswith("page_"):
                continue
            try:
                del st.session_state[k]
            except Exception:
                pass
        st.experimental_rerun()
        # WhatsApp_Report.py  — PART 5 / 5 (footer, notes, sync)

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Populate 4-Hourly from Hourly Tracker** if you want to copy the last 4 hours into manual 4H inputs (then edit if required). "
    "• Gearbox is hourly-only and is shown on the hourly template (not cumulative). "
    "• Opening balances are applied once when you first generate (they appear as Done). "
    "• Press **Save Settings** to persist vessel name / berthed date / planned / opening / first/last lift across devices."
)

# Ensure DB and session sync on load (persist session to DB when user navigates)
# Save cumulative every so often to keep DB in sync with session (best-effort)
def sync_session_to_db():
    # keep cumulative in sync with editable session values that are persistent
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
        "first_lift": st.session_state.get("first_lift", cumulative.get("first_lift", "")),
        "last_lift": st.session_state.get("last_lift", cumulative.get("last_lift", "")),
        "last_hour": st.session_state.get("hourly_time", cumulative.get("last_hour", hour_range_list()[0])),
        "fourh": st.session_state.get("fourh", cumulative.get("fourh", empty_tracker())),
        "_openings_applied": cumulative.get("_openings_applied", False),
        "done_load": cumulative.get("done_load", 0),
        "done_disch": cumulative.get("done_disch", 0),
        "done_restow_load": cumulative.get("done_restow_load", 0),
        "done_restow_disch": cumulative.get("done_restow_disch", 0),
        "done_hatch_open": cumulative.get("done_hatch_open", 0),
        "done_hatch_close": cumulative.get("done_hatch_close", 0),
    })
    save_db(cumulative)

# offer a small button to sync current session values to DB (useful if you changed fields)
if st.button("🔁 Sync Session -> DB (persist current inputs)"):
    sync_session_to_db()
    st.success("Session values persisted to DB.")

# On load, ensure session reflects latest DB (useful if opened from another device)
# We only set session keys if missing to avoid overwriting in-progress edits
db_latest = load_db()
for k, v in db_latest.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Final minor guard: keep cumulative and session consistent
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
    "first_lift": st.session_state.get("first_lift", cumulative.get("first_lift", "")),
    "last_lift": st.session_state.get("last_lift", cumulative.get("last_lift", "")),
    "last_hour": st.session_state.get("hourly_time", cumulative.get("last_hour", hour_range_list()[0])),
    "fourh": st.session_state.get("fourh", cumulative.get("fourh", empty_tracker())),
})
save_db(cumulative)
