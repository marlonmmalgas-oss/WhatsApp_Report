import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Load or initialize cumulative data ---
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        try:
            cumulative = json.load(f)
        except json.JSONDecodeError:
            cumulative = {}
else:
    cumulative = {}

# Default cumulative structure
defaults = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": None,
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "planned_load": 687,
    "planned_disch": 38,
    "planned_restow_load": 13,
    "planned_restow_disch": 13,
    "opening_load": 0,
    "opening_disch": 0,
    "opening_restow_load": 0,
    "opening_restow_disch": 0,
    "four_hourly_done_load": 0,
    "four_hourly_done_disch": 0,
    "four_hourly_done_restow_load": 0,
    "four_hourly_done_restow_disch": 0,
    "four_hourly_done_hatch_open": 0,
    "four_hourly_done_hatch_close": 0,
    "four_hour_block": "06h00 - 10h00",
    "idle_logs": []
}

# Merge defaults with loaded cumulative
for k, v in defaults.items():
    cumulative.setdefault(k, v)

# --- Current South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift Time", "18h25")
last_lift = st.text_input("Last Lift Time", "10h31")

# --- Plan Totals & Opening Balance (collapsible) ---
with st.expander("Plan Totals & Opening Balance (Internal Only)", expanded=False):
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

# --- Hourly Time Dropdown ---
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour") or "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Inputs ---
st.header(f"Hourly Moves Input ({hourly_time})")

with st.expander("Crane Moves (Load / Discharge)"):
    fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="fwd_load")
    mid_load = st.number_input("MID Load", min_value=0, value=0, key="mid_load")
    aft_load = st.number_input("AFT Load", min_value=0, value=0, key="aft_load")
    poop_load = st.number_input("POOP Load", min_value=0, value=0, key="poop_load")

    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="fwd_disch")
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="mid_disch")
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="aft_disch")
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="poop_disch")

with st.expander("Restows (Load / Discharge)"):
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="fwd_restow_load")
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="mid_restow_load")
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="aft_restow_load")
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="poop_restow_load")

    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0, key="fwd_restow_disch")
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0, key="mid_restow_disch")
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0, key="aft_restow_disch")
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0, key="poop_restow_disch")

with st.expander("Hatch Moves (Open / Close)"):
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)

    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)
    # --- Idle Section ---
st.header("Idle / Delays")
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
    "Spreader difficulties"
]

with st.expander("Add Idle Entry"):
    idle_crane = st.text_input("Crane", "")
    idle_start = st.text_input("Start Time (HHMM)", "")
    idle_end = st.text_input("End Time (HHMM)", "")
    selected_delay = st.selectbox("Select Delay Type", options=idle_options)
    custom_delay = st.text_input("Or enter custom delay", "")
    
    if st.button("Add Idle"):
        delay = custom_delay if custom_delay.strip() else selected_delay
        cumulative["idle_logs"].append({
            "crane": idle_crane,
            "start": idle_start,
            "end": idle_end,
            "reason": delay
        })
        st.success("Idle logged!")

# --- WhatsApp Number / Group ---
st.header("Send to WhatsApp")
wa_choice = st.radio("Send to:", ["Private Number", "Group Link"])
if wa_choice == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
else:
    whatsapp_group = st.text_input("Enter WhatsApp Group Link")

# --- Submit Button ---
if st.button("Submit Hourly Moves"):

    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save persistent editable fields
    cumulative.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date,
        "planned_load": planned_load,
        "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load,
        "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load,
        "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load,
        "opening_restow_disch": opening_restow_disch
    })

    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Calculate remaining totals
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # --- Hourly Template ---
    template = f"""\
{vessel_name}
Berthed {berthed_date}

First Lift @ {first_lift}
Last Lift @ {last_lift}

Date: {today_date}
Hourly Time: {hourly_time}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {fwd_load:>5}     {fwd_disch:>5}
MID        {mid_load:>5}     {mid_disch:>5}
AFT        {aft_load:>5}     {aft_disch:>5}
POOP       {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {fwd_restow_load:>5}     {fwd_restow_disch:>5}
MID        {mid_restow_load:>5}     {mid_restow_disch:>5}
AFT        {aft_restow_load:>5}     {aft_restow_disch:>5}
POOP       {poop_restow_load:>5}     {poop_restow_disch:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Discharge
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Discharge
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID        {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT        {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""

    st.code(template)

    # --- Send to WhatsApp ---
    wa_template = f"```{template}```"
    if wa_choice == "Private Number" and whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif wa_choice == "Group Link" and whatsapp_group:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group})", unsafe_allow_html=True)
        # --- 4-Hourly Report Section ---
st.header("4-Hourly Report")

# 4-hourly time dropdown
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
four_hour_selected = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

# Editable inputs for 4-hourly counts (grouped)
with st.expander("Crane Moves (4-Hourly)"):
    col1, col2 = st.columns(2)
    with col1:
        fwd_4h_load = st.number_input("FWD Load", min_value=0, value=0)
        mid_4h_load = st.number_input("MID Load", min_value=0, value=0)
        aft_4h_load = st.number_input("AFT Load", min_value=0, value=0)
        poop_4h_load = st.number_input("POOP Load", min_value=0, value=0)
    with col2:
        fwd_4h_disch = st.number_input("FWD Discharge", min_value=0, value=0)
        mid_4h_disch = st.number_input("MID Discharge", min_value=0, value=0)
        aft_4h_disch = st.number_input("AFT Discharge", min_value=0, value=0)
        poop_4h_disch = st.number_input("POOP Discharge", min_value=0, value=0)

with st.expander("Restows (4-Hourly)"):
    col1, col2 = st.columns(2)
    with col1:
        fwd_4h_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
        mid_4h_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
        aft_4h_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
        poop_4h_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    with col2:
        fwd_4h_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
        mid_4h_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
        aft_4h_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
        poop_4h_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

with st.expander("Hatch Moves (4-Hourly)"):
    col1, col2 = st.columns(2)
    with col1:
        hatch_fwd_4h_open = st.number_input("FWD Open", min_value=0, value=0)
        hatch_mid_4h_open = st.number_input("MID Open", min_value=0, value=0)
        hatch_aft_4h_open = st.number_input("AFT Open", min_value=0, value=0)
    with col2:
        hatch_fwd_4h_close = st.number_input("FWD Close", min_value=0, value=0)
        hatch_mid_4h_close = st.number_input("MID Close", min_value=0, value=0)
        hatch_aft_4h_close = st.number_input("AFT Close", min_value=0, value=0)

# --- 4-Hourly Submit and Template ---
st.header("4-Hourly Template")
four_hour_template = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_selected}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {fwd_4h_load:>5}     {fwd_4h_disch:>5}
MID        {mid_4h_load:>5}     {mid_4h_disch:>5}
AFT        {aft_4h_load:>5}     {aft_4h_disch:>5}
POOP       {poop_4h_load:>5}     {poop_4h_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {fwd_4h_restow_load:>5}     {fwd_4h_restow_disch:>5}
MID        {mid_4h_restow_load:>5}     {mid_4h_restow_disch:>5}
AFT        {aft_4h_restow_load:>5}     {aft_4h_restow_disch:>5}
POOP       {poop_4h_restow_load:>5}     {poop_4h_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_4h_open:>5}     {hatch_fwd_4h_close:>5}
MID        {hatch_mid_4h_open:>5}     {hatch_mid_4h_close:>5}
AFT        {hatch_aft_4h_open:>5}     {hatch_aft_4h_close:>5}
"""

st.code(four_hour_template)

# --- WhatsApp Send for 4-Hourly ---
st.header("Send 4-Hourly to WhatsApp")
wa_4h_choice = st.radio("Send 4-Hourly to:", ["Private Number", "Group Link"], key="wa_4h")
if wa_4h_choice == "Private Number":
    wa_4h_number = st.text_input("Enter WhatsApp Number (with country code)", key="wa_4h_num")
    if st.button("Send 4-Hourly to Private", key="send_4h_private"):
        wa_4h_link = f"https://wa.me/{wa_4h_number}?text={urllib.parse.quote(f'```{four_hour_template}```')}"
        st.markdown(f"[Open WhatsApp]({wa_4h_link})", unsafe_allow_html=True)
else:
    wa_4h_group = st.text_input("Enter WhatsApp Group Link", key="wa_4h_group")
    if st.button("Send 4-Hourly to Group", key="send_4h_group"):
        st.markdown(f"[Open WhatsApp Group]({wa_4h_group})", unsafe_allow_html=True)