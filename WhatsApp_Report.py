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
TZ = pytz.timezone("Africa/Johannesburg")

# default cumulative (keeps templates identical to your original)
DEFAULT_CUMULATIVE = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    # breakdown by position (so we can display hourly split accum)
    "done_fwd_load": 0, "done_mid_load": 0, "done_aft_load": 0, "done_poop_load": 0,
    "done_fwd_disch": 0, "done_mid_disch": 0, "done_aft_disch": 0, "done_poop_disch": 0,
    "done_fwd_restow_load": 0, "done_mid_restow_load": 0, "done_aft_restow_load": 0, "done_poop_restow_load": 0,
    "done_fwd_restow_disch": 0, "done_mid_restow_disch": 0, "done_aft_restow_disch": 0, "done_poop_restow_disch": 0,
    "done_hatch_fwd_open": 0, "done_hatch_mid_open": 0, "done_hatch_aft_open": 0,
    "done_hatch_fwd_close": 0, "done_hatch_mid_close": 0, "done_hatch_aft_close": 0,

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
    # flag to indicate we've already applied opening balances to 'done' counts
    "_openings_applied": False
}

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
# SQLITE helpers
# --------------------------
def init_db_if_needed():
    conn = sqlite3.connect(SAVE_DB, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS meta (id INTEGER PRIMARY KEY, json TEXT);")
    conn.commit()
    cur.close()
    conn.close()

def load_db():
    init_db_if_needed()
    conn = sqlite3.connect(SAVE_DB, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    if row:
        try:
            obj = json.loads(row[0])
            cur.close()
            conn.close()
            return obj
        except Exception:
            cur.close()
            conn.close()
            return None
    cur.close()
    conn.close()
    return None

def save_db(obj: dict):
    init_db_if_needed()
    conn = sqlite3.connect(SAVE_DB, check_same_thread=False)
    cur = conn.cursor()
    payload = json.dumps(obj)
    cur.execute("SELECT 1 FROM meta WHERE id=1;")
    if cur.fetchone():
        cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (payload,))
    else:
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (payload,))
    conn.commit()
    cur.close()
    conn.close()

# --------------------------
# SESSION STATE INIT
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# create initial four-hour tracker structure
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
    }

# ensure all keys used later are initialized
# date & labels
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", DEFAULT_CUMULATIVE["vessel_name"])
init_key("berthed_date", DEFAULT_CUMULATIVE["berthed_date"])
init_key("first_lift", "")   # first lift input
init_key("last_lift", "")    # last lift input

# plans & openings (editable)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, DEFAULT_CUMULATIVE[k])

# Hourly inputs (do not assign widget return to session_state; use keys on widgets)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox"  # hourly gearbox count (transient)
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", DEFAULT_CUMULATIVE.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker
init_key("fourh", empty_tracker())
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

# load DB (if exists) and populate cumulative & fourh
db_obj = load_db()
if db_obj and isinstance(db_obj, dict):
    # db_obj expected shape: {"cumulative": {...}, "fourh": {...}}
    loaded_cum = db_obj.get("cumulative", {})
    # overlay loaded values into session/defaults
    cumulative = DEFAULT_CUMULATIVE.copy()
    cumulative.update(loaded_cum)
    st.session_state["vessel_name"] = cumulative.get("vessel_name", st.session_state["vessel_name"])
    st.session_state["berthed_date"] = cumulative.get("berthed_date", st.session_state["berthed_date"])
    # plans/openings
    for k in ["planned_load","planned_disch","planned_restow_load","planned_restow_disch",
              "opening_load","opening_disch","opening_restow_load","opening_restow_disch"]:
        st.session_state[k] = cumulative.get(k, st.session_state[k])
    # last hour
    st.session_state["hourly_time"] = cumulative.get("last_hour", st.session_state["hourly_time"])
    # fourh
    st.session_state["fourh"] = db_obj.get("fourh", st.session_state["fourh"])
else:
    cumulative = DEFAULT_CUMULATIVE.copy()
    # save fresh DB
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})
    st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel (inputs)
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # widget keys are already in session_state, so simply create inputs
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    # first / last lift inputs (you asked these back)
    st.text_input("First Lift (optional)", key="first_lift")
    st.text_input("Last Lift (optional)", key="last_lift")
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
# apply any pending override (we set this during callbacks to avoid widget-assignment during render)
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

# ensure valid label
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
# Gearbox (hour-only transient)
# --------------------------
with st.expander("🔧 Gearbox (hour total - transient)"):
    st.number_input("Total Gearboxes this hour", min_value=0, key="hr_gearbox", help="This amount is shown on hourly template only and not cumulative.")

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

# --------------------------
# WhatsApp (Hourly) – original monospace template (including gearbox + first/last lift)
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    # compute remaining after applying cumulative (cumulative already updated before calling this)
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift: {st.session_state.get('first_lift','')}
Last Lift: {st.session_state.get('last_lift','')}

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
*Gearbox Moves (hourly only)*
Total Gearboxes: {st.session_state['hr_gearbox']}
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

# --------------------------
# CORE: generate hourly (updates cumulative, DB, 4h-tracker) — used as on_click callback
# --------------------------
def on_generate_hourly_callback():
    global cumulative

    # --- ensure all hr keys exist before usage ---
    hr_keys_defaults = {
        "hr_fwd_load": 0, "hr_mid_load": 0, "hr_aft_load": 0, "hr_poop_load": 0,
        "hr_fwd_disch": 0, "hr_mid_disch": 0, "hr_aft_disch": 0, "hr_poop_disch": 0,
        "hr_fwd_restow_load": 0, "hr_mid_restow_load": 0, "hr_aft_restow_load": 0, "hr_poop_restow_load": 0,
        "hr_fwd_restow_disch": 0, "hr_mid_restow_disch": 0, "hr_aft_restow_disch": 0, "hr_poop_restow_disch": 0,
        "hr_hatch_fwd_open": 0, "hr_hatch_mid_open": 0, "hr_hatch_aft_open": 0,
        "hr_hatch_fwd_close": 0, "hr_hatch_mid_close": 0, "hr_hatch_aft_close": 0,
        "hr_gearbox": 0
    }
    for k, v in hr_keys_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # ------------------------------------------------

    # First ensure openings applied once
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # now safe to build hr dictionary
    hr = {
        "fwd_load": int(st.session_state["hr_fwd_load"]),
        "mid_load": int(st.session_state["hr_mid_load"]),
        "aft_load": int(st.session_state["hr_aft_load"]),
        "poop_load": int(st.session_state["hr_poop_load"]),
        "fwd_disch": int(st.session_state["hr_fwd_disch"]),
        "mid_disch": int(st.session_state["hr_mid_disch"]),
        "aft_disch": int(st.session_state["hr_aft_disch"]),
        "poop_disch": int(st.session_state["hr_poop_disch"]),
        "fwd_restow_load": int(st.session_state["hr_fwd_restow_load"]),
        "mid_restow_load": int(st.session_state["hr_mid_restow_load"]),
        "aft_restow_load": int(st.session_state["hr_aft_restow_load"]),
        "poop_restow_load": int(st.session_state["hr_poop_restow_load"]),
        "fwd_restow_disch": int(st.session_state["hr_fwd_restow_disch"]),
        "mid_restow_disch": int(st.session_state["hr_mid_restow_disch"]),
        "aft_restow_disch": int(st.session_state["hr_aft_restow_disch"]),
        "poop_restow_disch": int(st.session_state["hr_poop_restow_disch"]),
        "hatch_fwd_open": int(st.session_state["hr_hatch_fwd_open"]),
        "hatch_mid_open": int(st.session_state["hr_hatch_mid_open"]),
        "hatch_aft_open": int(st.session_state["hr_hatch_aft_open"]),
        "hatch_fwd_close": int(st.session_state["hr_hatch_fwd_close"]),
        "hatch_mid_close": int(st.session_state["hr_hatch_mid_close"]),
        "hatch_aft_close": int(st.session_state["hr_hatch_aft_close"]),
    }

    # update cumulative breakdowns (per position)
    cumulative["done_fwd_load"] += hr["fwd_load"]
    cumulative["done_mid_load"] += hr["mid_load"]
    cumulative["done_aft_load"] += hr["aft_load"]
    cumulative["done_poop_load"] += hr["poop_load"]

    cumulative["done_fwd_disch"] += hr["fwd_disch"]
    cumulative["done_mid_disch"] += hr["mid_disch"]
    cumulative["done_aft_disch"] += hr["aft_disch"]
    cumulative["done_poop_disch"] += hr["poop_disch"]

    cumulative["done_fwd_restow_load"] += hr["fwd_restow_load"]
    cumulative["done_mid_restow_load"] += hr["mid_restow_load"]
    cumulative["done_aft_restow_load"] += hr["aft_restow_load"]
    cumulative["done_poop_restow_load"] += hr["poop_restow_load"]

    cumulative["done_fwd_restow_disch"] += hr["fwd_restow_disch"]
    cumulative["done_mid_restow_disch"] += hr["mid_restow_disch"]
    cumulative["done_aft_restow_disch"] += hr["aft_restow_disch"]
    cumulative["done_poop_restow_disch"] += hr["poop_restow_disch"]

    cumulative["done_hatch_fwd_open"] += hr["hatch_fwd_open"]
    cumulative["done_hatch_mid_open"] += hr["hatch_mid_open"]
    cumulative["done_hatch_aft_open"] += hr["hatch_aft_open"]

    cumulative["done_hatch_fwd_close"] += hr["hatch_fwd_close"]
    cumulative["done_hatch_mid_close"] += hr["hatch_mid_close"]
    cumulative["done_hatch_aft_close"] += hr["hatch_aft_close"]

    # aggregate totals (keep in sync)
    cumulative["done_load"] = (
        cumulative["done_fwd_load"] + cumulative["done_mid_load"] + cumulative["done_aft_load"] + cumulative["done_poop_load"]
    )
    cumulative["done_disch"] = (
        cumulative["done_fwd_disch"] + cumulative["done_mid_disch"] + cumulative["done_aft_disch"] + cumulative["done_poop_disch"]
    )
    cumulative["done_restow_load"] = (
        cumulative["done_fwd_restow_load"] + cumulative["done_mid_restow_load"] + cumulative["done_aft_restow_load"] + cumulative["done_poop_restow_load"]
    )
    cumulative["done_restow_disch"] = (
        cumulative["done_fwd_restow_disch"] + cumulative["done_mid_restow_disch"] + cumulative["done_aft_restow_disch"] + cumulative["done_poop_restow_disch"]
    )
    cumulative["done_hatch_open"] = (
        cumulative["done_hatch_fwd_open"] + cumulative["done_hatch_mid_open"] + cumulative["done_hatch_aft_open"]
    )
    cumulative["done_hatch_close"] = (
        cumulative["done_hatch_fwd_close"] + cumulative["done_hatch_mid_close"] + cumulative["done_hatch_aft_close"]
    )

    # Prevent negative remain: if done > plan, bump plan up to match done
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    # persist meta
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
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})

    # push this hour into rolling 4-hour tracker
    tr = st.session_state["fourh"]
    tr["fwd_load"].append(hr["fwd_load"])
    tr["mid_load"].append(hr["mid_load"])
    tr["aft_load"].append(hr["aft_load"])
    tr["poop_load"].append(hr["poop_load"])

    tr["fwd_disch"].append(hr["fwd_disch"])
    tr["mid_disch"].append(hr["mid_disch"])
    tr["aft_disch"].append(hr["aft_disch"])
    tr["poop_disch"].append(hr["poop_disch"])

    tr["fwd_restow_load"].append(hr["fwd_restow_load"])
    tr["mid_restow_load"].append(hr["mid_restow_load"])
    tr["aft_restow_load"].append(hr["aft_restow_load"])
    tr["poop_restow_load"].append(hr["poop_restow_load"])

    tr["fwd_restow_disch"].append(hr["fwd_restow_disch"])
    tr["mid_restow_disch"].append(hr["mid_restow_disch"])
    tr["aft_restow_disch"].append(hr["aft_restow_disch"])
    tr["poop_restow_disch"].append(hr["poop_restow_disch"])

    tr["hatch_fwd_open"].append(hr["hatch_fwd_open"])
    tr["hatch_mid_open"].append(hr["hatch_mid_open"])
    tr["hatch_aft_open"].append(hr["hatch_aft_open"])

    tr["hatch_fwd_close"].append(hr["hatch_fwd_close"])
    tr["hatch_mid_close"].append(hr["hatch_mid_close"])
    tr["hatch_aft_close"].append(hr["hatch_aft_close"])

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

    # save DB after updating fourh
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})

    # store last generated template text for immediate display after callback
    st.session_state["last_hourly_text"] = generate_hourly_template_text()

    # advance hour safely on next render
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    st.success("Hourly template generated and totals updated.")

# Single button only (no preview). Render the last generated template (if exists)
if st.button("✅ Generate Hourly Template & Update Totals", on_click=on_generate_hourly_callback):
    pass

# display last generated template if available
if st.session_state.get("last_hourly_text"):
    st.code(st.session_state["last_hourly_text"], language="text")

# Open WhatsApp button (uses last generated text)
def open_whatsapp_hourly():
    txt = st.session_state.get("last_hourly_text", generate_hourly_template_text())
    wa_text = f"```{txt}```"
    if st.session_state.get("wa_num_hour"):
        link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_hour"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
    else:
        st.info("Enter a WhatsApp number or group link to send.")

st.button("📤 Open WhatsApp (Hourly)", on_click=open_whatsapp_hourly)

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
    # advance to next hour on next render
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
    st.success("Hourly inputs reset and hour advanced.")

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
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

# Populate manual 4H fields from computed 4H tracker
def populate_4h_from_tracker():
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
    # persist manual values
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})

st.button("⏬ Populate 4-Hourly from Hourly Tracker", on_click=populate_4h_from_tracker)

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template_text():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

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

# display 4H template and expose buttons
if st.button("👁️ Preview 4-Hourly Template Only"):
    st.code(generate_4h_template_text(), language="text")

def open_whatsapp_4h():
    t = generate_4h_template_text()
    wa_text = f"```{t}```"
    if st.session_state.get("wa_num_4h"):
        link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_4h"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
    else:
        st.info("Enter a WhatsApp number or group link to send.")

st.button("📤 Open WhatsApp (4-Hourly)", on_click=open_whatsapp_4h)

def reset_4h_and_save():
    st.session_state["fourh"] = empty_tracker()
    # also clear manual inputs
    for k in ["m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
              "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
              "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
              "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
              "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
              "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close"]:
        st.session_state[k] = 0
    st.session_state["fourh_manual_override"] = False
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})
    st.success("4-hourly tracker reset.")

st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)", on_click=reset_4h_and_save)
st.markdown("---")

# --------------------------
# MASTER RESET (clears DB + session minimal)
# --------------------------
def master_reset():
    # reset session-state items
    keys_to_reset = [
        # hourly inputs + gearbox + idle
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox", "idle_entries", "num_idle_entries",
        # manual 4h inputs
        "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
        "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
        "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
        "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
        "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
        "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            st.session_state[k] = 0 if isinstance(st.session_state.get(k), int) else ""
    # reset fourh
    st.session_state["fourh"] = empty_tracker()
    st.session_state["fourh_manual_override"] = False

    # remove DB file to clear persistent state
    if os.path.exists(SAVE_DB):
        os.remove(SAVE_DB)

    # restore cumulative to defaults
    global cumulative
    cumulative = DEFAULT_CUMULATIVE.copy()
    save_db({"cumulative": cumulative, "fourh": st.session_state["fourh"]})
    st.success("Master reset completed. App returned to defaults.")

st.button("⚠️ MASTER RESET (clear everything)", on_click=master_reset)

st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Populate 4H** if you want to force the 4-hour inputs from the last 4 hourly entries. "
    "• Resets: Hourly / 4-Hourly / Master Reset are available. "
    "• Opening balances are applied once (they show in Done immediately)."
)
