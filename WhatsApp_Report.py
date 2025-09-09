import streamlit as st
import json
import os
import sqlite3
from datetime import datetime, timedelta
import pytz
import urllib.parse

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")
TZ = pytz.timezone("Africa/Johannesburg")
DB_FILE = "vessel_report.db"

# --------------------------
# DATABASE HELPERS
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY,
            json TEXT
        )
    """)
    conn.commit()
    # if no row, insert defaults
    cur.execute("SELECT COUNT(*) FROM meta")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?)", (json.dumps(default_cumulative()),))
        conn.commit()
    conn.close()

def load_cumulative():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return default_cumulative()
    return default_cumulative()

def save_cumulative(data: dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json=? WHERE id=1", (json.dumps(data),))
    conn.commit()
    conn.close()

# --------------------------
# DEFAULTS
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
        "berthed_date": "",
        "first_lift": "",
        "last_lift": "",
        "planned_load": 0,
        "planned_disch": 0,
        "planned_restow_load": 0,
        "planned_restow_disch": 0,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0,
    }

init_db()
cumulative = load_cumulative()

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

init_key("report_date", datetime.now(TZ).date())
for k in [
    "vessel_name","berthed_date","first_lift","last_lift",
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, "" if "date" in k else 0))

# Hourly input keys
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox_total"
]:
    init_key(k, 0)

# Idle
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# Hour tracking
init_key("hourly_time", cumulative.get("last_hour", hour_range_list()[0]))

# 4-hour tracker
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "gearbox_total": [],
        "count_hours": 0,
    }

init_key("fourh", empty_tracker())
init_key("fourh_manual_override", False)
init_key("fourh_block", four_hour_blocks()[0])
# --------------------------
# UI - Header / Vessel info
# --------------------------
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # use keys only (do not reassign to session_state)
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.text_input("First Lift", key="first_lift")
    st.text_input("Last Lift", key="last_lift")
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
# Crane Moves (Load & Discharge) — keep collapsibles as-is
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
with st.expander("⚙️ Gearbox (hourly)"):
    st.number_input("Total Gearboxes this Hour", min_value=0, key="hr_gearbox_total")
    st.caption("Gearbox total is hourly-only (not cumulative). It will be included in the hourly template and 4H tracker but not stored as cumulative.")

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
        "gearbox":    ss["hr_gearbox_total"],
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearbox (hourly only):** {split['gearbox']}")

# --------------------------
# WhatsApp (Hourly) – template
# --------------------------
def generate_hourly_template():
    # Effective “done” includes opening balance as already done
    done_load  = cumulative["done_load"]  + st.session_state["opening_load"]
    done_disch = cumulative["done_disch"] + st.session_state["opening_disch"]
    done_restow_load  = cumulative["done_restow_load"]  + st.session_state["opening_restow_load"]
    done_restow_disch = cumulative["done_restow_disch"] + st.session_state["opening_restow_disch"]

    remaining_load  = max(0, st.session_state["planned_load"]  - done_load)
    remaining_disch = max(0, st.session_state["planned_disch"] - done_disch)
    remaining_restow_load  = max(0, st.session_state["planned_restow_load"]  - done_restow_load)
    remaining_restow_disch = max(0, st.session_state["planned_restow_disch"] - done_restow_disch)

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift @ {st.session_state['first_lift']}
Last Lift @ {st.session_state['last_lift']}

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
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearboxes*
Total     {st.session_state['hr_gearbox_total']:>5}
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
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# Hourly Generate Logic
# --------------------------
def on_generate_hourly():
    # Sum this hour
    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # Update cumulative, but cap at plan
    cumulative["done_load"] = min(st.session_state["planned_load"], cumulative["done_load"] + int(hour_load))
    cumulative["done_disch"] = min(st.session_state["planned_disch"], cumulative["done_disch"] + int(hour_disch))
    cumulative["done_restow_load"] = min(st.session_state["planned_restow_load"], cumulative["done_restow_load"] + int(hour_restow_load))
    cumulative["done_restow_disch"] = min(st.session_state["planned_restow_disch"], cumulative["done_restow_disch"] + int(hour_restow_disch))
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)

    # Adjust plan totals if done exceeds plan (to avoid negatives)
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    # Persist meta/settings
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
    save_cumulative(cumulative)
    save_db(cumulative)

    # Push this hour into rolling 4-hour tracker
    add_current_hour_to_4h()

    # AUTO-ADVANCE hour on next render
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

# --------------------------
# Generate Button
# --------------------------
if st.button("✅ Generate Hourly Template & Update Totals"):
    hourly_text = generate_hourly_template()
    st.code(hourly_text, language="text")
    on_generate_hourly()

# Reset HOURLY
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox_total"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
# --------------------------
# 4-Hourly Tracker (accumulate last 4 hours)
# --------------------------
if "four_hour_tracker" not in cumulative:
    cumulative["four_hour_tracker"] = []

def add_current_hour_to_4h():
    split = hourly_totals_split()
    entry = {
        "hour": st.session_state["hourly_time"],
        "load": split["load"],
        "disch": split["disch"],
        "restow_load": split["restow_load"],
        "restow_disch": split["restow_disch"],
        "hatch_open": split["hatch_open"],
        "hatch_close": split["hatch_close"],
        "gearbox": split["gearbox"],
    }
    cumulative["four_hour_tracker"].append(entry)
    # Keep only last 4
    if len(cumulative["four_hour_tracker"]) > 4:
        cumulative["four_hour_tracker"].pop(0)
    save_cumulative(cumulative)
    save_db(cumulative)

def generate_4h_template():
    tracker = cumulative.get("four_hour_tracker", [])
    if not tracker:
        return "No 4-hour data yet."

    # Sum up last 4 entries
    total = {
        "load": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "disch":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "restow_load":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "restow_disch":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "hatch_open":{"FWD":0,"MID":0,"AFT":0},
        "hatch_close":{"FWD":0,"MID":0,"AFT":0},
        "gearbox":0,
    }
    for e in tracker:
        for pos in ["FWD","MID","AFT","POOP"]:
            total["load"][pos] += e["load"][pos]
            total["disch"][pos] += e["disch"][pos]
            total["restow_load"][pos] += e["restow_load"][pos]
            total["restow_disch"][pos] += e["restow_disch"][pos]
            if pos in ["FWD","MID","AFT"]:
                total["hatch_open"][pos] += e["hatch_open"][pos]
                total["hatch_close"][pos] += e["hatch_close"][pos]
        total["gearbox"] += e["gearbox"]

    tmpl = f"""\
{st.session_state['vessel_name']}
4-Hourly Summary (last 4 hours up to {tracker[-1]['hour']})
_________________________
*Crane Moves*
           Load   Disch
FWD       {total['load']['FWD']:>5}   {total['disch']['FWD']:>5}
MID       {total['load']['MID']:>5}   {total['disch']['MID']:>5}
AFT       {total['load']['AFT']:>5}   {total['disch']['AFT']:>5}
POOP      {total['load']['POOP']:>5}   {total['disch']['POOP']:>5}
_________________________
*Restows*
           Load   Disch
FWD       {total['restow_load']['FWD']:>5}   {total['restow_disch']['FWD']:>5}
MID       {total['restow_load']['MID']:>5}   {total['restow_disch']['MID']:>5}
AFT       {total['restow_load']['AFT']:>5}   {total['restow_disch']['AFT']:>5}
POOP      {total['restow_load']['POOP']:>5}   {total['restow_disch']['POOP']:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {total['hatch_open']['FWD']:>5}   {total['hatch_close']['FWD']:>5}
MID       {total['hatch_open']['MID']:>5}   {total['hatch_close']['MID']:>5}
AFT       {total['hatch_open']['AFT']:>5}   {total['hatch_close']['AFT']:>5}
_________________________
*Gearboxes (last 4h)*
Total     {total['gearbox']:>5}
_________________________
"""
    return tmpl

# --------------------------
# 4-Hourly Display
# --------------------------
with st.expander("⏳ 4-Hourly Tracker & Template"):
    st.markdown("### Last 4-Hour Entries")
    for e in cumulative.get("four_hour_tracker", []):
        st.write(f"{e['hour']} — Load {sum(e['load'].values())}, Disch {sum(e['disch'].values())}, Gearbox {e['gearbox']}")

    if st.button("📊 Generate 4-Hourly Template"):
        st.code(generate_4h_template(), language="text")

# Reset 4-Hourly
def reset_4h_inputs():
    cumulative["four_hour_tracker"] = []
    save_cumulative(cumulative)
    save_db(cumulative)

st.button("🔄 Reset 4-Hourly Tracker", on_click=reset_4h_inputs)
# --------------------------
# Master Reset (everything)
# --------------------------
def master_reset():
    # Clear session_state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # Reset cumulative structure
    global cumulative
    cumulative = {
        "last_hour": hour_range_list()[0],
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "done_gearbox": 0,
        "four_hour_tracker": []
    }

    save_cumulative(cumulative)
    save_db(cumulative)
    st.success("✅ Master reset completed. All data cleared.")

st.markdown("---")
st.subheader("⚠️ Master Reset")
st.button("🧹 Reset EVERYTHING (Full Reset)", on_click=master_reset)

# --------------------------
# Footer / Notes
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and feed the 4-hour tracker. \n"
    "• 4-Hourly: Generates summary of last 4 hourly splits. \n"
    "• Gearboxes: Counted only for the current hour or last 4h block. No cumulative carry-over. \n"
    "• Opening Balance: Deducts from plan and adds to done automatically in templates. \n"
    "• Totals: Done will never exceed Plan. If it does, Plan auto-adjusts upward to balance. \n"
    "• Resets: Hourly and 4-hourly resets are separate. Master reset clears everything including vessel info."
)
