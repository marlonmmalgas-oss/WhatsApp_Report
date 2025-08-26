# WhatsApp_Report.py - PART 1/5
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS
# --------------------------
TZ = pytz.timezone("Africa/Johannesburg")

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

# Initialize all session state variables
def init_session_state():
    # Get query parameters
    query_params = st.experimental_get_query_params()
    
    # Date & vessel info
    init_key("report_date", datetime.now(TZ).date())
    init_key("vessel_name", query_params.get("vessel_name", ["MSC NILA"])[0])
    init_key("berthed_date", query_params.get("berthed_date", ["14/08/2025 @ 10h55"])[0])
    
    # Plans & openings
    init_key("planned_load", int(query_params.get("planned_load", [687])[0]))
    init_key("planned_disch", int(query_params.get("planned_disch", [38])[0]))
    init_key("planned_restow_load", int(query_params.get("planned_restow_load", [13])[0]))
    init_key("planned_restow_disch", int(query_params.get("planned_restow_disch", [13])[0]))
    init_key("opening_load", int(query_params.get("opening_load", [0])[0]))
    init_key("opening_disch", int(query_params.get("opening_disch", [0])[0]))
    init_key("opening_restow_load", int(query_params.get("opening_restow_load", [0])[0]))
    init_key("opening_restow_disch", int(query_params.get("opening_restow_disch", [0])[0]))
    
    # Cumulative totals
    init_key("done_load", int(query_params.get("done_load", [0])[0]))
    init_key("done_disch", int(query_params.get("done_disch", [0])[0]))
    init_key("done_restow_load", int(query_params.get("done_restow_load", [0])[0]))
    init_key("done_restow_disch", int(query_params.get("done_restow_disch", [0])[0]))
    init_key("done_hatch_open", int(query_params.get("done_hatch_open", [0])[0]))
    init_key("done_hatch_close", int(query_params.get("done_hatch_close", [0])[0]))
    
    # HOURLY inputs
    for k in [
        "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
        "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
        "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
        "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
        "hr_hatch_fwd_open", "hr_hatch_mid_open", "hr_hatch_aft_open",
        "hr_hatch_fwd_close", "hr_hatch_mid_close", "hr_hatch_aft_close",
    ]:
        init_key(k, 0)
    
    # Idle entries
    init_key("num_idle_entries", 0)
    init_key("idle_entries", [])
    
    # Time selection
    hours_list = hour_range_list()
    init_key("hourly_time", query_params.get("hourly_time", [hours_list[0]])[0])
    
    # FOUR-HOUR tracker
    init_key("fourh", empty_tracker())
    init_key("fourh_manual_override", False)
    
    # Manual 4-hour inputs
    for k in [
        "m4h_fwd_load", "m4h_mid_load", "m4h_aft_load", "m4h_poop_load",
        "m4h_fwd_disch", "m4h_mid_disch", "m4h_aft_disch", "m4h_poop_disch",
        "m4h_fwd_restow_load", "m4h_mid_restow_load", "m4h_aft_restow_load", "m4h_poop_restow_load",
        "m4h_fwd_restow_disch", "m4h_mid_restow_disch", "m4h_aft_restow_disch", "m4h_poop_restow_disch",
        "m4h_hatch_fwd_open", "m4h_hatch_mid_open", "m4h_hatch_aft_open",
        "m4h_hatch_fwd_close", "m4h_hatch_mid_close", "m4h_hatch_aft_close",
    ]:
        init_key(k, 0)
    
    init_key("fourh_block", four_hour_blocks()[0])
    
    # WhatsApp numbers
    init_key("wa_num_hour", "")
    init_key("wa_grp_hour", "")
    init_key("wa_num_4h", "")
    init_key("wa_grp_4h", "")

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

# Initialize session state
init_session_state()

# --------------------------
# SMALL HELPERS
# --------------------------
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

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    st.success("4-hour tracker has been reset!")

# --------------------------
# UPDATE QUERY PARAMS
# --------------------------
def update_query_params():
    params = {
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "planned_load": str(st.session_state["planned_load"]),
        "planned_disch": str(st.session_state["planned_disch"]),
        "planned_restow_load": str(st.session_state["planned_restow_load"]),
        "planned_restow_disch": str(st.session_state["planned_restow_disch"]),
        "opening_load": str(st.session_state["opening_load"]),
        "opening_disch": str(st.session_state["opening_disch"]),
        "opening_restow_load": str(st.session_state["opening_restow_load"]),
        "opening_restow_disch": str(st.session_state["opening_restow_disch"]),
        "done_load": str(st.session_state["done_load"]),
        "done_disch": str(st.session_state["done_disch"]),
        "done_restow_load": str(st.session_state["done_restow_load"]),
        "done_restow_disch": str(st.session_state["done_restow_disch"]),
        "done_hatch_open": str(st.session_state["done_hatch_open"]),
        "done_hatch_close": str(st.session_state["done_hatch_close"]),
        "hourly_time": st.session_state["hourly_time"],
    }
    st.experimental_set_query_params(**params)

# --------------------------
# UI STARTS HERE
# --------------------------
st.title("🚢 Vessel Hourly & 4-Hourly Moves Tracker")
# WhatsApp_Report.py - PART 2/5

# --------------------------
# Date & Vessel
# --------------------------
st.header("Vessel Information")
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Vessel Details")
    st.text_input("Vessel Name", key="vessel_name", help="Enter the vessel name", on_change=update_query_params)
    st.text_input("Berthed Date", key="berthed_date", help="Format: DD/MM/YYYY @ HHhMM", on_change=update_query_params)
with col2:
    st.subheader("Report Date")
    st.date_input("Select Report Date", key="report_date")

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    st.info("These values are used for cumulative calculations and WhatsApp templates")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load", min_value=0, key="planned_load", help="Total planned load moves", on_change=update_query_params)
        st.number_input("Planned Discharge", min_value=0, key="planned_disch", help="Total planned discharge moves", on_change=update_query_params)
        st.number_input("Planned Restow Load", min_value=0, key="planned_restow_load", help="Total planned restow load moves", on_change=update_query_params)
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch", help="Total planned restow discharge moves", on_change=update_query_params)
    with c2:
        st.number_input("Opening Load (Deduction)", min_value=0, key="opening_load", help="Opening balance for load moves", on_change=update_query_params)
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch", help="Opening balance for discharge moves", on_change=update_query_params)
        st.number_input("Opening Restow Load (Deduction)", min_value=0, key="opening_restow_load", help="Opening balance for restow load moves", on_change=update_query_params)
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch", help="Opening balance for restow discharge moves", on_change=update_query_params)

# --------------------------
# Hour selector
# --------------------------
st.header("Hourly Moves Input")
st.subheader("Select Time Period")

# Apply pending hour change from previous action BEFORE rendering the selectbox
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

# Ensure valid label
if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = hour_range_list()[0]

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time",
    on_change=update_query_params
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge)
# --------------------------
with st.expander("🏗️ Crane Moves", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📦 Load Moves")
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, key="hr_poop_load")
    with col2:
        st.markdown("#### 📤 Discharge Moves")
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch")

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📦 Restow Load")
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")
    with col2:
        st.markdown("#### 📤 Restow Discharge")
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, extreme_value=0, key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔓 Hatch Open")
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with col2:
        st.markdown("#### 🔒 Hatch Close")
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", extreme_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")
        # WhatsApp_Report.py - PART 3/5

# --------------------------
# Idle / Delays
# --------------------------
st.subheader("⏸️ Idle / Delays")
idle_options = [
    "Tea Time",
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
    "On stanby due to",
]

with st.expander("🛑 Idle Entries", expanded=False):
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries", 
                   help="How many idle/delay events occurred in this hour?")
    
    entries = []
    for i in range(st.session_state["num_idle_entries"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, extreme_value, c4 = st.columns([1, 1, 1, 2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}", placeholder="Crane #")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30")
        end = extreme_value.text_input(f"End {i+1}", key=f"idle_end_{i}", placeholder="e.g., 12h40")
        sel = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}", 
                              placeholder="Enter custom delay reason")
        entries.append({
            "crane": (crane or "").strip(),
            extreme_value: (start or "").strip(),
            "end": (end or "").strip(),
            "delay": (custom or "").strip() if (custom or "").strip() else sel
        })
    
    st.session_state["idle_entries"] = entries

# --------------------------
# Hourly Totals Tracker
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load": {"FWD": ss["hr_fwd_load"], "MID": ss["hr_mid_load"], "AFT": ss["hr_aft_load"], "POOP": ss["hr_poop_load"]},
        "disch": {"FWD": ss["hr_fwd_disch"], "MID": ss["hr_mid_disch"], "AFT": ss["hr_aft_disch"], "POOP": extreme_value["hr_poop_disch"]},
        "restow_load": {"FWD": ss["hr_fwd_restow_load"], "MID": ss["hr_mid_restow_load"], "AFT": ss["hr_aft_restow_load"], "POOP": ss["hr_poop_restow_load"]},
        "restow_disch": {"FWD": ss["hr_fwd_restow_disch"], "MID": ss["hr_mid_restow_disch"], "AFT": ss["hr_aft_restow_disch"], "POOP": ss["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": ss["hr_hatch_fwd_open"], "MID": ss["hr_hatch_mid_open"], "AFT": ss["hr_hatch_aft_open"]},
        "hatch_close": {"FWD": ss["hr_hatch_fwd_close"], "MID": ss["hr_hatch_mid_close"], "AFT": ss["hr_hatch_aft_close"]},
    }

with st.expander("🧮 Hourly Totals (Preview)", expanded=True):
    split = hourly_totals_split()
    
    st.subheader("Split by Position")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 📦 Load Moves")
        st.write(f"FWD: {split['load']['FWD']} | MID: {split['load']['MID']} | AFT: {split['load']['AFT']} | POOP: {split['load']['POOP']}")
        st.markdown("##### 📤 Discharge Moves")
        st.write(f"FWD: {split['disch']['FWD']} | MID: {split['disch']['MID']} | AFT: {split['disch']['AFT']} | POOP: {split['disch']['POOP']}")
    with col2:
        st.markdown("##### 🔄 Restow Load")
        st.write(f"FWD: {split['restow_load']['FWD']} | MID: {split['restow_load']['MID']} | AFT: {split['restow_load']['AFT']} | POOP: {split['restow_load']['POOP']}")
        st.markdown("##### 🔄 Restow Discharge")
        st.write(f"FWD: extreme_value{split['restow_disch']['FWD']} | MID: {split['restow_disch']['MID']} | AFT: {split['restow_disch']['AFT']} | POOP: {split['restow_disch']['POOP']}")
    
    st.markdown("---")
    st.subheader("Hatch Moves")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 🔓 Hatch Open")
        st.write(f"FWD: {split['hatch_open']['FWD']} | MID: {split['hatch_open']['MID']} | AFT: {split['hatch_open']['AFT']}")
    with col2:
        st.markdown("##### 🔒 Hatch Close")
        st.write(f"FWD: {split['hatch_close']['FWD']} | MID: {split['hatch_close']['MID']} | AFT: {split['hatch_close']['AFT']}")
        # WhatsApp_Report.py - PART 4/5

# --------------------------
# WhatsApp Hourly Template
# --------------------------
def generate_hourly_template():
    remaining_load = st.session_state["planned_load"] - st.session_state["done_load"] - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - st.session_state["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load = st.session_state["planned_restow_load"] - st.session_state["done_restow_load"] - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - st.session_state["done_restow_disch"] - st.session_state["opering_restow_disch"]

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
           Load   Discharge
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {st.session_state['done_load']:>5}      {st.session_state['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Discharge
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {st.session_state['done_restow_load']:>5}      {st.session_state['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open    Close
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
# Submit Hourly Report
# --------------------------
def submit_hourly_report():
    # Add current hour to 4-hour tracker
    add_current_hour_to_4h()
    
    # Update cumulative totals
    split = hourly_totals_split()
    
    # Calculate totals from split
    total_load = split["load"]["FWD"] + split["load"]["MID"] + split["load"]["AFT"] + split["load"]["POOP"]
    total_disch = split["disch"]["FWD"] + split["disch"]["MID"] + split["disch"]["AFT"] + split["disch"]["POOP"]
    total_restow_load = split["restow_load"]["FWD"] + split["restow_load"]["MID"] + split["restow_load"]["AFT"] + split["restow_load"]["POOP"]
    total_restow_disch = split["restow_disch"]["FWD"] + split["restow_disch"]["MID"] + split["restow_disch"]["AFT"] + split["restow_disch"]["POOP"]
    total_hatch_open = split["hatch_open"]["FWD"] + split["hatch_open"]["MID"] + split["hatch_open"]["AFT"]
    total_hatch_close = split["hatch_close"]["FWD"] + split["hatch_close"]["MID"] + split["hatch_close"]["AFT"]
    
    st.session_state["done_load"] += total_load
    st.session_state["done_disch"] += total_disch
    st.session_state["done_restow_load"] += total_restow_load
    st.session_state["done_restow_disch"] += total_restow_disch
    st.session_state["done_hatch_open"] += total_hatch_open
    st.session_state["done_hatch_close"] += total_hatch_close
    
    # Update query params
    update_query_params()
    
    # Move to next hour
    next_hour = next_hour_label(st.session_state["hourly_time"])
    st.session_state["hourly_time_override"] = next_hour
    
    # Reset hourly inputs
    for k in [
        "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
        "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
        "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
        "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
        "hr_hatch_fwd_open", "hr_hatch_mid_open", "hr_hatch_aft_open",
        "hr_hatch_fwd_close", "hr_hatch_mid_close", "hr_hatch_aft_close",
    ]:
        st.session_state[k] = 0
    
    # Reset idle entries
    st.session_state["num_idle_entries"] = 0
    st.session_state["idle_entries"] = []
    
    st.success(f"Hourly report submitted! Moved to next hour: {next_hour}")

# --------------------------
# Hourly WhatsApp Section
# --------------------------
st.header("📱 WhatsApp Hourly Report")
hourly_template = generate_hourly_template()
st.text_area("Hourly WhatsApp Template", value=hourly_template, height=400)

col1, col2 = st.columns(2)
with col1:
    st.text_input("WhatsApp Number (Hourly)", key="wa_num_hour", placeholder="e.g., 27721234567")
with extreme_value:
    st.text_input("WhatsApp Group ID (Hourly)", key="wa_grp_hour", placeholder="Group ID if sending to group")

if st.button("💾 Submit Hourly Report & Generate WhatsApp Link", type="primary"):
    submit_hourly_report()
    st.rerun()

if st.session_state["wa_num_hour"] or st.session_state["wa_grp_hour"]:
    # Create WhatsApp link
    phone_param = st.session_state["wa_num_hour"] if st.session_state["wa_num_hour"] else ""
    group_param = st.session_state["wa_grp_hour"] if st.session_state["wa_grp_hour"] else ""
    
    encoded_text = urllib.parse.quote(hourly_template)
    if phone_param:
        whatsapp_url = f"https://wa.me/{phone_param}?text={encoded_text}"
    elif group_param:
        whatsapp_url = f"https://chat.whatsapp.com/{group_param}?text={encoded_text}"
    else:
        whatsapp_url = f"https://web.whatsapp.com/send?text={encoded_text}"
    
    st.markdown(f"[📤 Open WhatsApp with Template]({whatsapp_url})", unsafe_allow_html=True)
    # WhatsApp_Report.py - PART 5/5

# --------------------------
# 4-Hourly Report Section
# --------------------------
st.header("⏱ 4-Hourly Report")

# --------------------------
# 4-Hour Block Selector
# --------------------------
st.subheader("Select 4-Hour Block")
st.selectbox(
    "4-Hour Block",
    options=four_hour_blocks(),
    key="fourh_block"
)

# --------------------------
# Populate 4-Hourly from Hourly Totals Button
# --------------------------
if st.button("📊 Populate 4-Hourly Report from Hourly Totals"):
    tr = st.session_state["fourh"]
    
    # Load moves
    st.session_state["m4h_fwd_load"] = sum_list(tr["fwd_load"])
    st.session_state["m4h_mid_load"] = sum_list(tr["mid_load"])
    st.session_state["m4h_aft_load"] = sum_list(tr["aft_load"])
    st.session_state["m4h_poop_load"] = sum_list(tr["poop_load"])
    
    # Discharge moves
    st.session_state["m4h_fwd_disch"] = sum_list(tr["fwd_disch"])
    st.session_state["m4h_mid_disch"] = sum_list(tr["mid_disch"])
    st.session_state["m4h_aft_disch"] = sum_list(tr["aft_disch"])
    st.session_state["m4h_poop_disch"] = sum_list(tr["poop_disch"])
    
    # Restow load
    st.session_state["m4h_fwd_restow_load"] = sum_list(tr["fwd_restow_load"])
    st.session_state["m4h_mid_restow_load"] = sum_list(tr["mid_restow_load"])
    st.session_state["m4h_aft_restow_load"] = sum_list(tr["aft_restow_load"])
    st.session_state["m4h_poop_restow_load"] = sum_list(tr["poop_restow_load"])
    
    # Restow discharge
    st.session_state["m4h_fwd_restow_disch"] = extreme_value(tr["fwd_restow_disch"])
    st.session_state["m4h_mid_restow_disch"] = sum_list(tr["mid_restow_disch"])
    st.session_state["m4h_aft_restow_disch"] = sum_list(tr["aft_restow_disch"])
    st.session_state["m4h_poop_restow_disch"] = sum_list(tr["poop_restow_disch"])
    
    # Hatch open
    st.session_state["m4h_hatch_fwd_open"] = sum_list(tr["hatch_fwd_open"])
    st.session_state["m4h_hatch_mid_open"] = sum_list(tr["hatch_mid_open"])
    st.session_state["m4h_hatch_aft_open"] = sum_list(tr["hatch_aft_open"])
    
    # Hatch close
    st.session_state["m4h_hatch_fwd_close"] = sum_list(tr["hatch_fwd_close"])
    st.session_state["m4h_hatch_mid_close"] = sum_list(tr["hatch_mid_close"])
    st.session_state["m4h_hatch_aft_close"] = sum_list(tr["hatch_aft_close"])
    
    st.success("4-hourly report populated from hourly totals!")

# --------------------------
# 4-Hour Tracker Display
# --------------------------
with st.expander("📊 4-Hour Tracker Summary", expanded=True):
    tr = st.session_state["fourh"]
    st.write(f"Hours tracked: {tr['count_hours']}/4")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📦 Load Moves")
        st.write(f"FWD: {sum_list(tr['fwd_load'])}")
        st.write(f"MID: {sum_list(tr['mid_load'])}")
        st.write(f"AFT: {sum_list(tr['aft_load'])}")
        st.write(f"POOP: {sum_list(tr['poop_load'])}")
        st.markdown("**Total Load:** " + str(sum_list(tr['fwd_load']) + sum_list(tr['mid_load']) + 
                                           sum_list(tr['aft_load']) + sum_list(tr['poop_load'])))
        
        st.markdown("#### 🔄 Restow Load")
        st.write(f"FWD: {sum_list(tr['fwd_restow_load'])}")
        st.write(f"MID: {sum_list(tr['mid_restow_load'])}")
        st.write(f"AFT: {sum_list(tr['aft_restow_load'])}")
        st.write(f"POOP: {sum_list(tr['poop_restow_load'])}")
        st.markdown("**Total Restow Load:** " + str(sum_list(tr['fwd_restow_load']) + sum_list(tr['mid_restow_load']) + 
                                                 sum_list(tr['aft_restow_load']) + sum_list(tr['poop_restow_load'])))
        
        st.markdown("#### 🔓 Hatch Open")
        st.write(f"FWD: {sum_list(tr['hatch_fwd_open'])}")
        st.write(f"MID: {sum_list(tr['hatch_mid_open'])}")
        st.write(f"AFT: {sum_list(tr['hatch_aft_open'])}")
        st.markdown("**Total Hatch Open:** " + str(sum_list(tr['hatch_fwd_open']) + sum_list(tr['hatch_mid_open']) + 
                                                sum_list(tr['hatch_aft_open'])))
    
    with col2:
        st.markdown("#### 📤 Discharge Moves")
        st.write(f"FWD: {sum_list(tr['fwd_disch'])}")
        st.write(f"MID: {sum_list(tr['mid_disch'])}")
        st.write(f"AFT: {sum_list(tr['aft_disch'])}")
        st.write(f"POOP: {sum_list(tr['poop_disch'])}")
        st.markdown("**Total Discharge:** " + str(sum_list(tr['fwd_disch']) + sum_list(tr['mid_disch']) + 
                                               sum_list(tr['aft_disch']) + sum_list(tr['poop_disch'])))
        
        st.markdown("#### 🔄 Restow Discharge")
        st.write(f"FWD: {sum_list(tr['fwd_restow_disch'])}")
        st.write(f"MID: {sum_list(tr['mid_restow_disch'])}")
        st.write(f"AFT: {sum_list(tr['aft_restow_disch'])}")
        st.write(f"POOP: {sum_list(tr['poop_restow_disch'])}")
        st.markdown("**Total Restow Discharge:** " + str(sum_list(tr['fwd_restow_disch']) + sum_list(tr['mid_restow_disch']) + 
                                                     sum_list(tr['aft_restow_disch']) + sum_list(tr['poop_restow_disch'])))
        
        st.markdown("#### 🔒 Hatch Close")
        st.write(f"FWD: {sum_list(tr['hatch_fwd_close'])}")
        st.write(f"MID: {sum_list(tr['hatch_mid_close'])}")
        st.write(f"AFT: {sum_list(tr['hatch_aft_close'])}")
        st.markdown("**Total Hatch Close:** " + str(sum_list(tr['hatch_fwd_close']) + sum_list(tr['hatch_mid_close']) + 
                                                 extreme_value(tr['hatch_aft_close'])))

# --------------------------
# 4-Hour WhatsApp Template
# --------------------------
def generate_4h_template():
    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {st.session_state['m4h_fwd_load']:>5}     {st.session_state['m4h_fwd_disch']:>5}
MID       {st.session_state['m4h_mid_load']:>5}     {st.session_state['m4h_mid_disch']:>5}
AFT       {st.session_state['m4h_aft_load']:>5}     {st.session_state['m4h_aft_disch']:>5}
POOP      {st.session_state['m4h_poop_load']:>5}     {st.session_state['m4h_poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {st.session_state['m4h_fwd_restow_load']:>5}     {st.session_state['m4h_fwd_restow_disch']:>5}
MID       {st.session_state['m4h_mid_restow_load']:>5}     {st.session_state['m4h_mid_restow_disch']:>5}
AFT       {st.session_state['m4h_aft_restow_load']:>5}     {st.session_state['m4h_aft_restow_disch']:>5}
POOP      {st.session_state['m4h_poop_restow_load']:>5}     {st.session_state['m4h_poop_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open    Close
FWD       {st.session_state['m4h_hatch_fwd_open']:>5}      {st.session_state['m4h_hatch_fwd_close']:>5}
MID       {st.session_state['m4h_hatch_mid_open']:>5}      {st.session_state['m4h_hatch_mid_close']:>5}
AFT       {st.session_state['m4h_hatch_aft_open']:>5}      {st.session_state['m4h_hatch_aft_close']:>5}
_________________________
"""
    return tmpl

st.subheader("📱 WhatsApp 4-Hourly Template")
fourh_template = generate_4h_template()
st.text_area("4-Hourly WhatsApp Template", value=fourh_template, height=300)

col1, col2 = st.columns(2)
with col1:
    st.text_input("WhatsApp Number (4-Hourly)", key="wa_num_4h", placeholder="e.g., 27721234567")
with col2:
    st.text_input("WhatsApp Group ID (4-Hourly)", key="wa_grp_4h", placeholder="Group ID if sending to group")

if st.session_state["wa_num_4h"] or st.session_state["wa_grp_4h"]:
    # Create WhatsApp link
    phone_param = st.session_state["wa_num_4h"] if st.session_state["wa_num_4h"] else ""
    group_param = st.session_state["wa_grp_4h"] if st.session_state["wa_grp_4h"] else ""
    
    encoded_text = urllib.parse.quote(fourh_template)
    if phone_param:
        whatsapp_url = f"https://wa.me/{phone_param}?text={encoded_text}"
    elif group_param:
        whatsapp_url = f"https://chat.whatsapp.com/{group_param}?text={encoded_text}"
    else:
        whatsapp_url = extreme_value"https://web.whatsapp.com/send?text={encoded_text}"
    
    st.markdown(f"[📤 Open WhatsApp with 4-Hour Template]({whatsapp_url})", unsafe_allow_html=True)

# --------------------------
# Reset Button
# --------------------------
if st.button("🔄 Reset 4-Hour Tracker"):
    reset_4h_tracker()
    st.rerun()

# --------------------------
# Footer
# --------------------------
st.markdown("---")
st.markdown("### 📊 Cumulative Totals")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Load Done", st.session_state["done_load"])
    st.metric("Total Discharge Done", st.session_state["done_disch"])
    st.metric("Total Restow Load Done", st.session_state["done_restow_load"])
with col2:
    st.metric("Total Restow Discharge Done", st.session_state["done_restow_disch"])
    st.metric("Total Hatch Open Done", st.session_state["done_hatch_open"])
    st.metric("Total Hatch Close Done", st.session_state["done_hatch_close"])
    
