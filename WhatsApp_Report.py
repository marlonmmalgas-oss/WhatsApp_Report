import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

# ---------- CONFIG ----------
SAVE_FILE = "vessel_report.json"
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date_default = datetime.now(sa_tz).date()

# ---------- LOAD OR INIT CUMULATIVE DATA ----------
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        try:
            cumulative = json.load(f)
        except json.JSONDecodeError:
            cumulative = None
else:
    cumulative = None

if cumulative is None:
    cumulative = {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "last_hour": "06h00 - 07h00",
        "vessel_name": "MSC NILA",
        "berthed_date": "14/08/2025 @ 10H55",
        "planned_load": 687,
        "planned_disch": 38,
        "planned_restow_load": 13,
        "planned_restow_disch": 13,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0
    }

# ---------- VESSEL INFO ----------
st.title("🛳 Vessel Hourly & 4-Hourly Moves Tracker")
st.header("🚢 Vessel Info")

vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
report_date = st.date_input("Report Date", today_date_default)

# ---------- PLAN & OPENING BALANCES (COLLAPSIBLE) ----------
with st.expander("📊 Plan Totals & Opening Balance (Internal Only)"):
    col1, col2 = st.columns(2)
    with col1:
        planned_load = st.number_input("Planned Load", value=cumulative["planned_load"])
        planned_disch = st.number_input("Planned Discharge", value=cumulative["planned_disch"])
        planned_restow_load = st.number_input("Planned Restow Load", value=cumulative["planned_restow_load"])
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=cumulative["planned_restow_disch"])
    with col2:
        opening_load = st.number_input("Opening Load (Deduction)", value=cumulative["opening_load"])
        opening_disch = st.number_input("Opening Discharge (Deduction)", value=cumulative["opening_disch"])
        opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=cumulative["opening_restow_load"])
        opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=cumulative["opening_restow_disch"])

# ---------- HOURLY TIME ----------
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time ⏰", options=hours_list, index=hours_list.index(default_hour))
# ---------- INITIALIZE SESSION STATE FOR HOURLY TRACKER ----------
hourly_sections = [
    "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
    "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
    "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
    "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
    "hr_hatch_fwd_open", "hr_hatch_mid_open", "hr_hatch_aft_open",
    "hr_hatch_fwd_close", "hr_hatch_mid_close", "hr_hatch_aft_close"
]

for section in hourly_sections:
    if section not in st.session_state:
        st.session_state[section] = 0

# ---------- HOURLY MOVES INPUT ----------
st.header(f"🕒 Hourly Moves Input ({hourly_time})")

with st.expander("🛠 Crane Moves"):
    with st.expander("Load"):
        st.session_state["hr_fwd_load"] = st.number_input("FWD Load", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
        st.session_state["hr_mid_load"] = st.number_input("MID Load", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
        st.session_state["hr_aft_load"] = st.number_input("AFT Load", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
        st.session_state["hr_poop_load"] = st.number_input("POOP Load", min_value=0, value=st.session_state["hr_poop_load"], key="hr_poop_load")
    with st.expander("Discharge"):
        st.session_state["hr_fwd_disch"] = st.number_input("FWD Discharge", min_value=0, value=st.session_state["hr_fwd_disch"], key="hr_fwd_disch")
        st.session_state["hr_mid_disch"] = st.number_input("MID Discharge", min_value=0, value=st.session_state["hr_mid_disch"], key="hr_mid_disch")
        st.session_state["hr_aft_disch"] = st.number_input("AFT Discharge", min_value=0, value=st.session_state["hr_aft_disch"], key="hr_aft_disch")
        st.session_state["hr_poop_disch"] = st.number_input("POOP Discharge", min_value=0, value=st.session_state["hr_poop_disch"], key="hr_poop_disch")

with st.expander("🔄 Restows"):
    with st.expander("Load"):
        st.session_state["hr_fwd_restow_load"] = st.number_input("FWD Restow Load", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
        st.session_state["hr_mid_restow_load"] = st.number_input("MID Restow Load", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
        st.session_state["hr_aft_restow_load"] = st.number_input("AFT Restow Load", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
        st.session_state["hr_poop_restow_load"] = st.number_input("POOP Restow Load", min_value=0, value=st.session_state["hr_poop_restow_load"], key="hr_poop_restow_load")
    with st.expander("Discharge"):
        st.session_state["hr_fwd_restow_disch"] = st.number_input("FWD Restow Discharge", min_value=0, value=st.session_state["hr_fwd_restow_disch"], key="hr_fwd_restow_disch")
        st.session_state["hr_mid_restow_disch"] = st.number_input("MID Restow Discharge", min_value=0, value=st.session_state["hr_mid_restow_disch"], key="hr_mid_restow_disch")
        st.session_state["hr_aft_restow_disch"] = st.number_input("AFT Restow Discharge", min_value=0, value=st.session_state["hr_aft_restow_disch"], key="hr_aft_restow_disch")
        st.session_state["hr_poop_restow_disch"] = st.number_input("POOP Restow Discharge", min_value=0, value=st.session_state["hr_poop_restow_disch"], key="hr_poop_restow_disch")

with st.expander("🟢 Hatch Moves"):
    with st.expander("Open"):
        st.session_state["hr_hatch_fwd_open"] = st.number_input("FWD Hatch Open", min_value=0, value=st.session_state["hr_hatch_fwd_open"], key="hr_hatch_fwd_open")
        st.session_state["hr_hatch_mid_open"] = st.number_input("MID Hatch Open", min_value=0, value=st.session_state["hr_hatch_mid_open"], key="hr_hatch_mid_open")
        st.session_state["hr_hatch_aft_open"] = st.number_input("AFT Hatch Open", min_value=0, value=st.session_state["hr_hatch_aft_open"], key="hr_hatch_aft_open")
    with st.expander("Close"):
        st.session_state["hr_hatch_fwd_close"] = st.number_input("FWD Hatch Close", min_value=0, value=st.session_state["hr_hatch_fwd_close"], key="hr_hatch_fwd_close")
        st.session_state["hr_hatch_mid_close"] = st.number_input("MID Hatch Close", min_value=0, value=st.session_state["hr_hatch_mid_close"], key="hr_hatch_mid_close")
        st.session_state["hr_hatch_aft_close"] = st.number_input("AFT Hatch Close", min_value=0, value=st.session_state["hr_hatch_aft_close"], key="hr_hatch_aft_close")

# ---------- HOURLY TRACKER TOTALS ----------
with st.expander("📈 Hourly Totals Tracker (visible)"):
    st.write("Load Totals:")
    st.write({
        "FWD": st.session_state["hr_fwd_load"],
        "MID": st.session_state["hr_mid_load"],
        "AFT": st.session_state["hr_aft_load"],
        "POOP": st.session_state["hr_poop_load"]
    })
    st.write("Discharge Totals:")
    st.write({
        "FWD": st.session_state["hr_fwd_disch"],
        "MID": st.session_state["hr_mid_disch"],
        "AFT": st.session_state["hr_aft_disch"],
        "POOP": st.session_state["hr_poop_disch"]
    })
    st.write("Restow Load Totals:")
    st.write({
        "FWD": st.session_state["hr_fwd_restow_load"],
        "MID": st.session_state["hr_mid_restow_load"],
        "AFT": st.session_state["hr_aft_restow_load"],
        "POOP": st.session_state["hr_poop_restow_load"]
    })
    st.write("Restow Discharge Totals:")
    st.write({
        "FWD": st.session_state["hr_fwd_restow_disch"],
        "MID": st.session_state["hr_mid_restow_disch"],
        "AFT": st.session_state["hr_aft_restow_disch"],
        "POOP": st.session_state["hr_poop_restow_disch"]
    })
    st.write("Hatch Open/Close Totals:")
    st.write({
        "Open FWD/MID/AFT": [st.session_state["hr_hatch_fwd_open"], st.session_state["hr_hatch_mid_open"], st.session_state["hr_hatch_aft_open"]],
        "Close FWD/MID/AFT": [st.session_state["hr_hatch_fwd_close"], st.session_state["hr_hatch_mid_close"], st.session_state["hr_hatch_aft_close"]]
    })
    # ---------- IDLE / DELAYS ----------
st.header("⏸ Idle / Delays")
if "idle_entries" not in st.session_state:
    st.session_state["idle_entries"] = []

idle_input = st.text_area("Enter Idle Entries (comma separated)", value=", ".join(st.session_state["idle_entries"]))
st.session_state["idle_entries"] = [entry.strip() for entry in idle_input.split(",") if entry.strip()]

# ---------- AUTOMATIC HOURLY TIME INCREMENT ----------
if "hour_index" not in st.session_state:
    st.session_state["hour_index"] = 0

hour_list = [f"{str(h).zfill(2)}h00 - {str(h+1).zfill(2)}h00" for h in range(24)]
hourly_time = st.selectbox("Select Hourly Time", options=hour_list, index=st.session_state["hour_index"])

# ---------- HOURLY WHATSAPP TEMPLATE ----------
st.header("📲 Send Hourly Report to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code)", value="2776xxxxxxx")
restows_total = sum([
    st.session_state["hr_fwd_restow_load"], st.session_state["hr_mid_restow_load"],
    st.session_state["hr_aft_restow_load"], st.session_state["hr_poop_restow_load"],
    st.session_state["hr_fwd_restow_disch"], st.session_state["hr_mid_restow_disch"],
    st.session_state["hr_aft_restow_disch"], st.session_state["hr_poop_restow_disch"]
])

if st.button("Generate Hourly WhatsApp Template"):
    hourly_template = f"""
🛳 Vessel Hourly Report
Date: {st.session_state.get('report_date', dt.today().strftime('%Y-%m-%d'))}
Time: {hourly_time}

📦 Load:
FWD: {st.session_state['hr_fwd_load']} | MID: {st.session_state['hr_mid_load']} | AFT: {st.session_state['hr_aft_load']} | POOP: {st.session_state['hr_poop_load']}

📤 Discharge:
FWD: {st.session_state['hr_fwd_disch']} | MID: {st.session_state['hr_mid_disch']} | AFT: {st.session_state['hr_aft_disch']} | POOP: {st.session_state['hr_poop_disch']}

🔄 Restows Total: {restows_total}
Idle / Delays: {', '.join(st.session_state['idle_entries'])}
"""
    st.text_area("Hourly WhatsApp Template", value=hourly_template, height=350)
    # Increment hour index automatically for next input
    st.session_state["hour_index"] = (st.session_state["hour_index"] + 1) % len(hour_list)

# ---------- RESET HOURLY INPUTS ----------
if st.button("🔄 Reset Hourly Inputs"):
    for section in hourly_sections:
        st.session_state[section] = 0
    st.session_state["idle_entries"] = []
    st.experimental_rerun()
    # ---------- 4-HOURLY TRACKER ----------
st.header("⏱ 4-Hourly Moves Tracker")

# Define 4-hour blocks
four_hour_blocks = [
    "00h00 - 04h00", "04h00 - 08h00", "08h00 - 12h00",
    "12h00 - 16h00", "16h00 - 20h00", "20h00 - 00h00"
]
if "four_hour_index" not in st.session_state:
    st.session_state["four_hour_index"] = 0

selected_4h_block = st.selectbox("Select 4-Hour Block", options=four_hour_blocks, index=st.session_state["four_hour_index"])

# Initialize 4-hourly counts if not exist
four_hour_sections = [
    "fwd_load_4h", "mid_load_4h", "aft_load_4h", "poop_load_4h",
    "fwd_disch_4h", "mid_disch_4h", "aft_disch_4h", "poop_disch_4h",
    "fwd_restow_load_4h", "mid_restow_load_4h", "aft_restow_load_4h", "poop_restow_load_4h",
    "fwd_restow_disch_4h", "mid_restow_disch_4h", "aft_restow_disch_4h", "poop_restow_disch_4h",
    "hatch_fwd_open_4h", "hatch_mid_open_4h", "hatch_aft_open_4h",
    "hatch_fwd_close_4h", "hatch_mid_close_4h", "hatch_aft_close_4h"
]

for section in four_hour_sections:
    if section not in st.session_state:
        st.session_state[section] = 0

# Collapsible section to view/edit counts
with st.expander("🔹 4-Hourly Counts (manual update possible)"):
    for section in four_hour_sections:
        st.session_state[section] = st.number_input(section.replace("_", " ").title(), min_value=0, value=st.session_state[section])

# ---------- CALCULATE 4-HOURLY TOTALS FROM HOURLY TRACKER ----------
# Total per FWD/MID/AFT/POOP across the selected 4-hour block
total_load_4h = (
    st.session_state["fwd_load_4h"] + st.session_state["mid_load_4h"] +
    st.session_state["aft_load_4h"] + st.session_state["poop_load_4h"]
)
total_disch_4h = (
    st.session_state["fwd_disch_4h"] + st.session_state["mid_disch_4h"] +
    st.session_state["aft_disch_4h"] + st.session_state["poop_disch_4h"]
)
total_restow_load_4h = (
    st.session_state["fwd_restow_load_4h"] + st.session_state["mid_restow_load_4h"] +
    st.session_state["aft_restow_load_4h"] + st.session_state["poop_restow_load_4h"]
)
total_restow_disch_4h = (
    st.session_state["fwd_restow_disch_4h"] + st.session_state["mid_restow_disch_4h"] +
    st.session_state["aft_restow_disch_4h"] + st.session_state["poop_restow_disch_4h"]
)
total_hatch_open_4h = (
    st.session_state["hatch_fwd_open_4h"] + st.session_state["hatch_mid_open_4h"] +
    st.session_state["hatch_aft_open_4h"]
)
total_hatch_close_4h = (
    st.session_state["hatch_fwd_close_4h"] + st.session_state["hatch_mid_close_4h"] +
    st.session_state["hatch_aft_close_4h"]
)
st.metric("🟢 Total Load (FWD+MID+AFT+POOP)", total_load_4h)
st.metric("🔵 Total Discharge", total_disch_4h)
st.metric("🔄 Total Restow Load", total_restow_load_4h)
st.metric("🔁 Total Restow Discharge", total_restow_disch_4h)
st.metric("🟡 Hatch Open Total", total_hatch_open_4h)
st.metric("🟠 Hatch Close Total", total_hatch_close_4h)
# ---------- 4-HOURLY WHATSAPP TEMPLATE & SEND ----------
st.header("📩 Generate 4-Hourly WhatsApp Report")

# Date handling: auto-date with optional picker
if "report_date_4h" not in st.session_state:
    st.session_state["report_date_4h"] = datetime.now(sa_tz).date()
report_date_4h = st.date_input("Select Report Date", value=st.session_state["report_date_4h"])
st.session_state["report_date_4h"] = report_date_4h

# Button to reset 4-hourly counts
if st.button("🔄 Reset 4-Hourly Counts"):
    for section in four_hour_sections:
        st.session_state[section] = 0
    st.session_state["four_hour_index"] = 0
    st.experimental_rerun()

# Generate template
four_hour_template = f"""\
{vessel_name}
Berthed {berthed_date}
Date: {report_date_4h.strftime('%d/%m/%Y')}
4-Hour Block: {selected_4h_block}
_________________________
*Crane Moves*
           Load    Discharge
FWD       {st.session_state['fwd_load_4h']:>5}     {st.session_state['fwd_disch_4h']:>5}
MID       {st.session_state['mid_load_4h']:>5}     {st.session_state['mid_disch_4h']:>5}
AFT       {st.session_state['aft_load_4h']:>5}     {st.session_state['aft_disch_4h']:>5}
POOP      {st.session_state['poop_load_4h']:>5}     {st.session_state['poop_disch_4h']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {st.session_state['fwd_restow_load_4h']:>5}     {st.session_state['fwd_restow_disch_4h']:>5}
MID       {st.session_state['mid_restow_load_4h']:>5}     {st.session_state['mid_restow_disch_4h']:>5}
AFT       {st.session_state['aft_restow_load_4h']:>5}     {st.session_state['aft_restow_disch_4h']:>5}
POOP      {st.session_state['poop_restow_load_4h']:>5}     {st.session_state['poop_restow_disch_4h']:>5}
_________________________
*Hatch Moves*
           Open     Close
FWD       {st.session_state['hatch_fwd_open_4h']:>5}     {st.session_state['hatch_fwd_close_4h']:>5}
MID       {st.session_state['hatch_mid_open_4h']:>5}     {st.session_state['hatch_mid_close_4h']:>5}
AFT       {st.session_state['hatch_aft_open_4h']:>5}     {st.session_state['hatch_aft_close_4h']:>5}
_________________________
"""

st.code(four_hour_template, language="text")

# WhatsApp input
whatsapp_number_4h = st.text_input("Enter WhatsApp Number (with country code) for 4H report")
whatsapp_group_link_4h = st.text_input("Or enter WhatsApp Group Link (optional)")

if st.button("📤 Send 4-Hourly Report"):
    wa_4h_template = f"```{four_hour_template}```"
    if whatsapp_number_4h:
        wa_link_4h = f"https://wa.me/{whatsapp_number_4h}?text={urllib.parse.quote(wa_4h_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
    elif whatsapp_group_link_4h:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link_4h})", unsafe_allow_html=True)

# ---------- SYNC HOURLY & 4-HOURLY ----------
# Update cumulative from hourly tracker automatically into 4-hourly counts
st.session_state["fwd_load_4h"] = cumulative["done_load"]  # or sum of FWD hourly loads in block
st.session_state["mid_load_4h"] = cumulative["done_load"]  # same logic for MID/AFT/POOP
st.session_state["aft_load_4h"] = cumulative["done_load"]
st.session_state["poop_load_4h"] = cumulative["done_load"]
# Repeat for discharge, restows, hatch opens/closes as per hourly cumulative