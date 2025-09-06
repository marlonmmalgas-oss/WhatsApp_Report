import streamlit as st
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import pytz
import os

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# --------------------------
# DATABASE FUNCTIONS
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vessel (
            id INTEGER PRIMARY KEY,
            vessel_name TEXT,
            berthed_date TEXT,
            report_date TEXT,
            planned_load INTEGER,
            planned_disch INTEGER,
            planned_restow_load INTEGER,
            planned_restow_disch INTEGER,
            opening_load INTEGER,
            opening_disch INTEGER,
            opening_restow_load INTEGER,
            opening_restow_disch INTEGER,
            done_load INTEGER,
            done_disch INTEGER,
            done_restow_load INTEGER,
            done_restow_disch INTEGER,
            done_hatch_open INTEGER,
            done_hatch_close INTEGER,
            last_hour TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM vessel WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "vessel_name": row[1],
            "berthed_date": row[2],
            "report_date": row[3],
            "planned_load": row[4],
            "planned_disch": row[5],
            "planned_restow_load": row[6],
            "planned_restow_disch": row[7],
            "opening_load": row[8],
            "opening_disch": row[9],
            "opening_restow_load": row[10],
            "opening_restow_disch": row[11],
            "done_load": row[12],
            "done_disch": row[13],
            "done_restow_load": row[14],
            "done_restow_disch": row[15],
            "done_hatch_open": row[16],
            "done_hatch_close": row[17],
            "last_hour": row[18],
        }
    return {
        "vessel_name": "MSC NILA",
        "berthed_date": "14/08/2025 @ 10h55",
        "report_date": datetime.now(TZ).strftime("%Y-%m-%d"),
        "planned_load": 687,
        "planned_disch": 38,
        "planned_restow_load": 13,
        "planned_restow_disch": 13,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0,
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "last_hour": "06h00 - 07h00",
    }

def save_data(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM vessel WHERE id=1")
    c.execute("""
        INSERT INTO vessel VALUES (1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        1,
        data["vessel_name"], data["berthed_date"], data["report_date"],
        data["planned_load"], data["planned_disch"],
        data["planned_restow_load"], data["planned_restow_disch"],
        data["opening_load"], data["opening_disch"],
        data["opening_restow_load"], data["opening_restow_disch"],
        data["done_load"], data["done_disch"],
        data["done_restow_load"], data["done_restow_disch"],
        data["done_hatch_open"], data["done_hatch_close"],
        data["last_hour"]
    ))
    conn.commit()
    conn.close()

init_db()
cumulative = load_data()
# --------------------------
# HELPERS
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

def sum_list(lst):
    return int(sum(lst)) if lst else 0

# --------------------------
# SESSION STATE INIT
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# Vessel info
init_key("vessel_name", cumulative["vessel_name"])
init_key("berthed_date", cumulative["berthed_date"])
init_key("report_date", datetime.strptime(cumulative["report_date"], "%Y-%m-%d").date())

# Plan totals & opening balances
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative[k])

# HOURLY inputs
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
]:
    init_key(k, 0)

# idle
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# hourly time
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# 4-hour tracker
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

# --------------------------
# UI: Title & Vessel
# --------------------------
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
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
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

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
# Crane Moves
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
# Restows
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
# Hatch Moves
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
# Hourly Totals Tracker (splits accumulate)
# --------------------------
def get_hourly_splits_accumulated():
    if "hourly_splits_accum" not in st.session_state:
        st.session_state["hourly_splits_accum"] = {
            "load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_load": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "restow_disch": {"FWD": 0, "MID": 0, "AFT": 0, "POOP": 0},
            "hatch_open": {"FWD": 0, "MID": 0, "AFT": 0},
            "hatch_close": {"FWD": 0, "MID": 0, "AFT": 0},
        }
    return st.session_state["hourly_splits_accum"]

def update_hourly_splits_accum():
    acc = get_hourly_splits_accumulated()
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

with st.expander("🧮 Hourly Totals (accumulated splits only)"):
    acc = get_hourly_splits_accumulated()
    st.write(f"**Load**       — FWD {acc['load']['FWD']} | MID {acc['load']['MID']} | AFT {acc['load']['AFT']} | POOP {acc['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {acc['disch']['FWD']} | MID {acc['disch']['MID']} | AFT {acc['disch']['AFT']} | POOP {acc['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {acc['restow_load']['FWD']} | MID {acc['restow_load']['MID']} | AFT {acc['restow_load']['AFT']} | POOP {acc['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {acc['restow_disch']['FWD']} | MID {acc['restow_disch']['MID']} | AFT {acc['restow_disch']['AFT']} | POOP {acc['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {acc['hatch_open']['FWD']} | MID {acc['hatch_open']['MID']} | AFT {acc['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {acc['hatch_close']['FWD']} | MID {acc['hatch_close']['MID']} | AFT {acc['hatch_close']['AFT']}")

# --------------------------
# WhatsApp (Hourly) – template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

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

def on_generate_hourly():
    # update cumulative totals
    cumulative["done_load"] += st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    cumulative["done_disch"] += st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    cumulative["done_restow_load"] += st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    cumulative["done_restow_disch"] += st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    cumulative["done_hatch_open"] += st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    cumulative["done_hatch_close"] += st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # persist settings
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
    save_cumulative(cumulative)

    # update hourly splits accumulator
    update_hourly_splits_accum()

    # push to 4-hour tracker
    add_current_hour_to_4h()

    # auto-advance
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

if st.button("✅ Generate Hourly Template & Update Totals"):
    st.code(generate_hourly_template(), language="text")
    on_generate_hourly()

# Reset HOURLY inputs
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
# --------------------------
# 4-Hourly Tracker & Report
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block safely
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox(
    "Select 4-Hour Block",
    options=block_opts,
    index=block_opts.index(st.session_state["fourh_block"]),
    key="fourh_block"
)

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

# Final chosen totals
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

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
             Open   Close
FWD          {vals4h['hatch_fwd_open']:>5}    {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}    {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}    {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

# Show last 4 hourly splits summary
with st.expander("📝 Last 4 Hourly Splits Summary"):
    acc = get_hourly_splits_accumulated()
    st.write("**Accumulated Hourly Splits (last 4 entries tracked):**")
    st.json(acc)

# Buttons for 4-hourly actions
if st.button("✅ Generate 4-Hourly Template & Update"):
    st.code(generate_4h_template(), language="text")

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

if st.button("🔄 Reset 4-Hourly Tracker"):
    reset_4h_tracker()
    st.success("4-hourly tracker reset.")

# --------------------------
# Footer Instructions
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Press **Generate Hourly Template** to accumulate into hourly splits & 4-hour tracker.\n"
    "• 4-Hourly: Press **Generate 4-Hourly Template** to output summary.\n"
    "• Resets clear values but do not loop back.\n"
    "• Hour auto-advances after each hourly generate/reset."
)