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
        except json.decoder.JSONDecodeError:
            cumulative = {}
else:
    cumulative = {}

# Default values
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
    "opening_restow_disch": 0
}
for key, value in defaults.items():
    cumulative.setdefault(key, value)

# --- Current South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

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
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))
# --- Hourly Moves Input ---
st.header(f"Hourly Moves Input ({hourly_time})")

with st.expander("Crane Moves", expanded=True):
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
    poop_load = st.number_input("POOP Load", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)

with st.expander("Restows", expanded=True):
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

with st.expander("Hatch Moves", expanded=True):
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle Section ---
st.header("Idle / Delay Input")
idle_entries = []
num_idle = st.number_input("Number of Idle Entries", min_value=0, value=0, step=1)
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
for i in range(num_idle):
    st.subheader(f"Idle Entry {i+1}")
    idle_crane = st.selectbox("Select Crane", options=["FWD", "MID", "AFT", "POOP"], key=f"idle_crane_{i}")
    idle_time_from = st.text_input("From Time (e.g., 12h30)", key=f"idle_from_{i}")
    idle_time_to = st.text_input("To Time (e.g., 12h40)", key=f"idle_to_{i}")
    idle_reason = st.selectbox("Select Reason", options=idle_options + ["Other"], key=f"idle_reason_{i}")
    idle_custom = ""
    if idle_reason == "Other":
        idle_custom = st.text_input("Enter custom reason", key=f"idle_custom_{i}")
    idle_entries.append({
        "crane": idle_crane,
        "from": idle_time_from,
        "to": idle_time_to,
        "reason": idle_reason if idle_reason != "Other" else idle_custom
    })

# --- WhatsApp Number Input ---
st.header("Send to WhatsApp")
wa_choice = st.radio("Send via", options=["Private Number", "Group Invite Link"])
if wa_choice == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
else:
    whatsapp_group_link = st.text_input("Enter WhatsApp Group Invite Link")
    # --- Submit Button ---
if st.button("Submit Hourly Moves"):

    # --- Update cumulative totals ---
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

    # --- Calculate remaining totals ---
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # --- Generate WhatsApp Template ---
    template = f"""\
{vessel_name}
Berthed {berthed_date}

First Lift @ 18h25
Last Lift @ 10h31

{today_date}
{hourly_time}
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
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
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

    # Add idle entries
    for idle in idle_entries:
        template += f"{idle['crane']} {idle['from']} - {idle['to']} {idle['reason']}\n"

    # --- Show template ---
    st.code(template)

    # --- WhatsApp link ---
    if wa_choice == "Private Number" and whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif wa_choice == "Group Invite Link" and whatsapp_group_link:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link})", unsafe_allow_html=True)
        # --- 4-Hourly Report ---
st.header("4-Hourly Report")

# --- 4-Hourly Time Dropdown ---
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]

four_hour_time = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

# --- 4-Hourly Input Sections (Collapsible) ---
with st.expander("Crane Moves (4-Hourly)"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fwd_4h_load = st.number_input("FWD Load", min_value=0, value=0, key="fwd4h_load")
        fwd_4h_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="fwd4h_disch")
    with col2:
        mid_4h_load = st.number_input("MID Load", min_value=0, value=0, key="mid4h_load")
        mid_4h_disch = st.number_input("MID Discharge", min_value=0, value=0, key="mid4h_disch")
    with col3:
        aft_4h_load = st.number_input("AFT Load", min_value=0, value=0, key="aft4h_load")
        aft_4h_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="aft4h_disch")
    with col4:
        poop_4h_load = st.number_input("POOP Load", min_value=0, value=0, key="poop4h_load")
        poop_4h_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="poop4h_disch")

with st.expander("Restows (4-Hourly)"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fwd_4h_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="fwd4h_restow_load")
        fwd_4h_restow_disch = st.number_input("FWD Restow Disch", min_value=0, value=0, key="fwd4h_restow_disch")
    with col2:
        mid_4h_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="mid4h_restow_load")
        mid_4h_restow_disch = st.number_input("MID Restow Disch", min_value=0, value=0, key="mid4h_restow_disch")
    with col3:
        aft_4h_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="aft4h_restow_load")
        aft_4h_restow_disch = st.number_input("AFT Restow Disch", min_value=0, value=0, key="aft4h_restow_disch")
    with col4:
        poop_4h_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="poop4h_restow_load")
        poop_4h_restow_disch = st.number_input("POOP Restow Disch", min_value=0, value=0, key="poop4h_restow_disch")

with st.expander("Hatch Moves (4-Hourly)"):
    col1, col2, col3 = st.columns(3)
    with col1:
        hatch_fwd_open_4h = st.number_input("FWD Open", min_value=0, value=0, key="hatch_fwd_open_4h")
        hatch_fwd_close_4h = st.number_input("FWD Close", min_value=0, value=0, key="hatch_fwd_close_4h")
    with col2:
        hatch_mid_open_4h = st.number_input("MID Open", min_value=0, value=0, key="hatch_mid_open_4h")
        hatch_mid_close_4h = st.number_input("MID Close", min_value=0, value=0, key="hatch_mid_close_4h")
    with col3:
        hatch_aft_open_4h = st.number_input("AFT Open", min_value=0, value=0, key="hatch_aft_open_4h")
        hatch_aft_close_4h = st.number_input("AFT Close", min_value=0, value=0, key="hatch_aft_close_4h")

# --- Calculate 4-Hourly Totals ---
total_4h_load = fwd_4h_load + mid_4h_load + aft_4h_load + poop_4h_load
total_4h_disch = fwd_4h_disch + mid_4h_disch + aft_4h_disch + poop_4h_disch
total_4h_restow_load = fwd_4h_restow_load + mid_4h_restow_load + aft_4h_restow_load + poop_4h_restow_load
total_4h_restow_disch = fwd_4h_restow_disch + mid_4h_restow_disch + aft_4h_restow_disch + poop_4h_restow_disch
total_hatch_open_4h = hatch_fwd_open_4h + hatch_mid_open_4h + hatch_aft_open_4h
total_hatch_close_4h = hatch_fwd_close_4h + hatch_mid_close_4h + hatch_aft_close_4h

# --- Generate 4-Hourly Template ---
template_4h = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_time}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD        {fwd_4h_load:>5}     {fwd_4h_disch:>5}
MID        {mid_4h_load:>5}     {mid_4h_disch:>5}
AFT        {aft_4h_load:>5}     {aft_4h_disch:>5}
POOP       {poop_4h_load:>5}     {poop_4h_disch:>5}
_________________________
*Restows*
           Load    Discharge
FWD        {fwd_4h_restow_load:>5}     {fwd_4h_restow_disch:>5}
MID        {mid_4h_restow_load:>5}     {mid_4h_restow_disch:>5}
AFT        {aft_4h_restow_load:>5}     {aft_4h_restow_disch:>5}
POOP       {poop_4h_restow_load:>5}     {poop_4h_restow_disch:>5}
_________________________
*Hatch Moves*
           Open    Close
FWD        {hatch_fwd_open_4h:>5}     {hatch_fwd_close_4h:>5}
MID        {hatch_mid_open_4h:>5}     {hatch_mid_close_4h:>5}
AFT        {hatch_aft_open_4h:>5}     {hatch_aft_close_4h:>5}
_________________________
"""

# --- Show 4-Hourly Template ---
st.code(template_4h)

# --- 4-Hourly WhatsApp ---
wa_4h_number = st.text_input("Enter WhatsApp Number (for 4-Hourly report)", key="wa_4h_number")
if st.button("Send 4-Hourly WhatsApp"):
    if wa_4h_number:
        wa_link_4h = f"https://wa.me/{wa_4h_number}?text={urllib.parse.quote(template_4h)}"
        st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)