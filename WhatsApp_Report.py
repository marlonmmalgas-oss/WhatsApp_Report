# WhatsApp_Report.py — PART 1 / 5

import streamlit as st
import sqlite3
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# --------------------------
# DATABASE HELPERS (SQLite)
# --------------------------
def init_db():
    need_init = not os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS meta (
               id INTEGER PRIMARY KEY,
               json TEXT
           );"""
    )
    # insert initial meta row if missing
    cur.execute("SELECT COUNT(*) FROM meta WHERE id = 1;")
    if cur.fetchone()[0] == 0:
        initial = {
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
            "done_load": 0,
            "done_disch": 0,
            "done_restow_load": 0,
            "done_restow_disch": 0,
            "done_hatch_open": 0,
            "done_hatch_close": 0,
            "last_hour": "06h00 - 07h00",
            "first_lift": "",
            "last_lift": "",
            "gearbox_hourly": 0,
            "_openings_applied": False
        }
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (json.dumps(initial),))
    conn.commit()
    conn.close()

def load_meta():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id = 1;")
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

def save_meta(data: dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (json.dumps(data),))
    conn.commit()
    conn.close()

# --------------------------
# INITIALIZE DB & LOAD META
# --------------------------
init_db()
cumulative = load_meta()

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

# date & labels (persisted meta used as defaults)
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", ""))
init_key("berthed_date", cumulative.get("berthed_date", ""))

# plans & openings (from DB meta)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, 0))

# hourly inputs
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

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
init_key("hourly_time", cumulative.get("last_hour", hour_range_list()[0]))

# four-hour tracker (rolling lists)
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "gearbox_hourly": [],
        "count_hours": 0,
    }

init_key("fourh", empty_tracker())
init_key("fourh_manual_override", False)
init_key("fourh_block", four_hour_blocks()[0])

# small helpers
def sum_list(lst):
    return int(sum(lst)) if lst else 0

def add_current_hour_to_4h():
    tr = st.session_state["fourh"]
    tr["fwd_load"].append(st.session_state["hr_fwd_load"])
    tr["mid_load"].append(st.session_state["hr_mid_load"])
    tr["aft_load"].append(st.session_state["hr_aft_load"])
    tr["poop_load"].append(st.session_state["hr_poop_load"])

    tr["fwd_disch"].append(st.session_state["hr_fwd_disch"])
    tr["mid_disch"].append(st.session_state["hr_mid_disch"])
    tr["aft_disch"].append(st.session_state["hr_aft_disch"])
    tr["poop_disch"].append(st.session_state["hr_poop_disch"])

    tr["fwd_restow_load"].append(st.session_state["hr_fwd_restow_load"])
    tr["mid_restow_load"].append(st.session_state["hr_mid_restow_load"])
    tr["aft_restow_load"].append(st.session_state["hr_aft_restow_load"])
    tr["poop_restow_load"].append(st.session_state["hr_poop_restow_load"])

    tr["fwd_restow_disch"].append(st.session_state["hr_fwd_restow_disch"])
    tr["mid_restow_disch"].append(st.session_state["hr_mid_restow_disch"])
    tr["aft_restow_disch"].append(st.session_state["hr_aft_restow_disch"])
    tr["poop_restow_disch"].append(st.session_state["hr_poop_restow_disch"])

    tr["hatch_fwd_open"].append(st.session_state["hr_hatch_fwd_open"])
    tr["hatch_mid_open"].append(st.session_state["hr_hatch_mid_open"])
    tr["hatch_aft_open"].append(st.session_state["hr_hatch_aft_open"])

    tr["hatch_fwd_close"].append(st.session_state["hr_hatch_fwd_close"])
    tr["hatch_mid_close"].append(st.session_state["hr_hatch_mid_close"])
    tr["hatch_aft_close"].append(st.session_state["hr_hatch_aft_close"])

    # gearbox for the hour (not cumulative)
    tr["gearbox_hourly"].append(st.session_state.get("hr_gearbox_total", 0))

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    # WhatsApp_Report.py — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
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
# Gearbox Moves (NEW, per hour only)
# --------------------------
with st.expander("⚙️ Gearbox Moves"):
    st.number_input("Total Gearbox Moves", min_value=0, key="hr_gearbox_total")

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
    # WhatsApp_Report.py — PART 3 / 5

# --------------------------
# Hourly Template Generator
# --------------------------
def generate_hourly_template():
    # Opening balances applied once
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += st.session_state["opening_load"]
        cumulative["done_disch"] += st.session_state["opening_disch"]
        cumulative["done_restow_load"] += st.session_state["opening_restow_load"]
        cumulative["done_restow_disch"] += st.session_state["opening_restow_disch"]
        cumulative["_openings_applied"] = True

    # Add current hourly moves into cumulative
    cumulative["done_load"] += (
        st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] +
        st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    )
    cumulative["done_disch"] += (
        st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] +
        st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    )
    cumulative["done_restow_load"] += (
        st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] +
        st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    )
    cumulative["done_restow_disch"] += (
        st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] +
        st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    )

    # Gearbox moves (hourly only, not cumulative)
    gearbox_total = st.session_state["hr_gearbox_total"]

    # Prevent done > plan (adjust plan if exceeded)
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

    # Build hourly report text
    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift @ {st.session_state['first_lift']}
Last Lift  @ {st.session_state['last_lift']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
Hour: {st.session_state['hourly_time']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {st.session_state['hr_fwd_load']:>5}     {st.session_state['hr_fwd_disch']:>5}
MID       {st.session_state['hr_mid_load']:>5}     {st.session_state['hr_mid_disch']:>5}
AFT       {st.session_state['hr_aft_load']:>5}     {st.session_state['hr_aft_disch']:>5}
POOP      {st.session_state['hr_poop_load']:>5}     {st.session_state['hr_poop_disch']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {st.session_state['hr_fwd_restow_load']:>5}     {st.session_state['hr_fwd_restow_disch']:>5}
MID       {st.session_state['hr_mid_restow_load']:>5}     {st.session_state['hr_mid_restow_disch']:>5}
AFT       {st.session_state['hr_aft_restow_load']:>5}     {st.session_state['hr_aft_restow_disch']:>5}
POOP      {st.session_state['hr_poop_restow_load']:>5}     {st.session_state['hr_poop_restow_disch']:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {st.session_state['hr_hatch_fwd_open']:>5}          {st.session_state['hr_hatch_fwd_close']:>5}
MID          {st.session_state['hr_hatch_mid_open']:>5}          {st.session_state['hr_hatch_mid_close']:>5}
AFT          {st.session_state['hr_hatch_aft_open']:>5}          {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearbox Moves*
Total        {gearbox_total:>5}
_________________________
      *CUMULATIVE TOTALS*
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
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

    return t

# --------------------------
# Hourly Report Actions
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for hourly report (optional)", key="wa_num_hr")
st.text_input("Or enter WhatsApp Group Link for hourly report (optional)", key="wa_grp_hr")

if st.button("📤 Generate & Send Hourly Report"):
    txt = generate_hourly_template()
    wa_text = f"```{txt}```"

    # Save hour into cumulative history
    save_db(cumulative)

    if st.session_state.get("wa_num_hr"):
        link = f"https://wa.me/{st.session_state['wa_num_hr']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_hr"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hr']})", unsafe_allow_html=True)
    else:
        st.code(txt, language="text")

    # Advance to next hour automatically
    hr_list = hour_range_list()
    curr = st.session_state["hourly_time"]
    next_idx = (hr_list.index(curr) + 1) % len(hr_list)
    st.session_state["hourly_time"] = hr_list[next_idx]
    # WhatsApp_Report.py — PART 4 / 5

# --------------------------
# 4-Hourly Tracker
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

def push_to_4h():
    """Push latest hourly entries into rolling 4-hour tracker."""
    if "fourh" not in cumulative:
        cumulative["fourh"] = []
    cumulative["fourh"].append({
        "time": st.session_state["hourly_time"],
        "fwd_load": st.session_state["hr_fwd_load"],
        "mid_load": st.session_state["hr_mid_load"],
        "aft_load": st.session_state["hr_aft_load"],
        "poop_load": st.session_state["hr_poop_load"],
        "fwd_disch": st.session_state["hr_fwd_disch"],
        "mid_disch": st.session_state["hr_mid_disch"],
        "aft_disch": st.session_state["hr_aft_disch"],
        "poop_disch": st.session_state["hr_poop_disch"],
        "fwd_restow_load": st.session_state["hr_fwd_restow_load"],
        "mid_restow_load": st.session_state["hr_mid_restow_load"],
        "aft_restow_load": st.session_state["hr_aft_restow_load"],
        "poop_restow_load": st.session_state["hr_poop_restow_load"],
        "fwd_restow_disch": st.session_state["hr_fwd_restow_disch"],
        "mid_restow_disch": st.session_state["hr_mid_restow_disch"],
        "aft_restow_disch": st.session_state["hr_aft_restow_disch"],
        "poop_restow_disch": st.session_state["hr_poop_restow_disch"],
        "hatch_fwd_open": st.session_state["hr_hatch_fwd_open"],
        "hatch_mid_open": st.session_state["hr_hatch_mid_open"],
        "hatch_aft_open": st.session_state["hr_hatch_aft_open"],
        "hatch_fwd_close": st.session_state["hr_hatch_fwd_close"],
        "hatch_mid_close": st.session_state["hr_hatch_mid_close"],
        "hatch_aft_close": st.session_state["hr_hatch_aft_close"],
        "gearbox_total": st.session_state["hr_gearbox_total"],
    })
    # Keep only last 4
    if len(cumulative["fourh"]) > 4:
        cumulative["fourh"].pop(0)
    save_db(cumulative)

def sum_last_4h():
    if "fourh" not in cumulative or not cumulative["fourh"]:
        return {}
    last4 = cumulative["fourh"][-4:]
    keys = last4[0].keys()
    totals = {k: 0 for k in keys if k != "time"}
    for entry in last4:
        for k, v in entry.items():
            if k != "time":
                totals[k] += v
    return totals

def generate_4h_template():
    vals = sum_last_4h()
    if not vals:
        return "No 4-hourly data available yet."

    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift @ {st.session_state['first_lift']}
Last Lift  @ {st.session_state['last_lift']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Summary (last 4 hours)
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {vals['fwd_load']:>5}     {vals['fwd_disch']:>5}
MID       {vals['mid_load']:>5}     {vals['mid_disch']:>5}
AFT       {vals['aft_load']:>5}     {vals['aft_disch']:>5}
POOP      {vals['poop_load']:>5}     {vals['poop_disch']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {vals['fwd_restow_load']:>5}     {vals['fwd_restow_disch']:>5}
MID       {vals['mid_restow_load']:>5}     {vals['mid_restow_disch']:>5}
AFT       {vals['aft_restow_load']:>5}     {vals['aft_restow_disch']:>5}
POOP      {vals['poop_restow_load']:>5}     {vals['poop_restow_disch']:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals['hatch_fwd_open']:>5}          {vals['hatch_fwd_close']:>5}
MID          {vals['hatch_mid_open']:>5}          {vals['hatch_mid_close']:>5}
AFT          {vals['hatch_aft_open']:>5}          {vals['hatch_aft_close']:>5}
_________________________
*Gearbox Moves*
Total        {vals['gearbox_total']:>5}
_________________________
      *CUMULATIVE TOTALS*
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
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

# --------------------------
# 4-Hourly Actions
# --------------------------
st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

if st.button("📤 Generate & Send 4-Hourly Report"):
    txt4 = generate_4h_template()
    wa_text = f"```{txt4}```"

    if st.session_state.get("wa_num_4h"):
        link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_4h"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
    else:
        st.code(txt4, language="text")
        # WhatsApp_Report.py — PART 5 / 5

# --------------------------
# Master Reset
# --------------------------
def master_reset():
    """Completely reset everything for a fresh start."""
    st.session_state.clear()

    # Reset cumulative DB too
    base = {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "fourh": [],
    }
    save_db(base)
    st.success("✅ Master Reset done. All values cleared.")

st.markdown("---")
st.subheader("⚠️ Master Reset")
st.button("🗑️ Reset Everything (Full Master Reset)", on_click=master_reset)

# --------------------------
# Footer Notes
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker.\n"
    "• 4-Hourly: Uses the last 4 hourly splits automatically. Use **Generate & Send 4-Hourly Report** for WhatsApp.\n"
    "• Opening Balance is automatically applied as part of 'Done' when first Generate is pressed.\n"
    "• Remain never goes negative — if Done exceeds Plan, Plan is adjusted upwards to match.\n"
    "• Gearbox totals apply only for the current hour, not cumulative.\n"
    "• Use Master Reset for a completely fresh start."
)
