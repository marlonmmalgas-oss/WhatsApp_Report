import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# Load or initialize cumulative data
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        try:
            cumulative = json.load(f)
        except:
            cumulative = {}
else:
    cumulative = {}

# Initialize default values if missing
defaults = {
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
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": None
}
for key, value in defaults.items():
    if key not in cumulative:
        cumulative[key] = value

# South African timezone
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# Vessel info
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift (HHhMM)", "")
last_lift = st.text_input("Last Lift (HHhMM)", "")

# Plan Totals & Opening Balance (collapsible)
with st.expander("Plan Totals & Opening Balance (Internal Only)"):
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

# Hourly Time Dropdown
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative["last_hour"] if cumulative["last_hour"] in hours_list else "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

st.header(f"Hourly Moves Input ({hourly_time})")
# --- Collapsible Groups for Hourly Inputs ---
with st.expander("Crane Load Inputs"):
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    poop_load = st.number_input("POOP Load", min_value=0, value=0)

with st.expander("Crane Discharge Inputs"):
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)

with st.expander("Restow Load Inputs"):
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)

with st.expander("Restow Discharge Inputs"):
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

with st.expander("Hatch Cover Open"):
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)

with st.expander("Hatch Cover Close"):
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle Section (collapsible, multiple entries) ---
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

with st.expander("Idle / Delays (Add multiple)"):
    idle_list = []
    num_idles = st.number_input("Number of idle entries", min_value=1, max_value=10, value=1)
    for i in range(num_idles):
        st.markdown(f"**Idle {i+1}**")
        crane = st.selectbox(f"Crane for Idle {i+1}", ["Crane 1", "Crane 2", "Crane 3", "Crane 4"], key=f"idle_crane_{i}")
        start_time = st.text_input(f"Start Time (HHhMM) Idle {i+1}", "", key=f"idle_start_{i}")
        end_time = st.text_input(f"End Time (HHhMM) Idle {i+1}", "", key=f"idle_end_{i}")
        delay_choice = st.selectbox(f"Select Delay {i+1}", options=idle_options + ["Other (Specify)"], key=f"idle_type_{i}")
        if delay_choice == "Other (Specify)":
            custom_delay = st.text_input(f"Specify custom delay {i+1}", "", key=f"idle_custom_{i}")
            delay_choice = custom_delay
        idle_list.append({"crane": crane, "start": start_time, "end": end_time, "delay": delay_choice})

# --- WhatsApp Number Input ---
st.header("Send to WhatsApp")
wa_choice = st.radio("Send to:", ["Private Number", "Group Link"])
whatsapp_number = st.text_input("Enter Number (with country code) or Group link", "")

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
    # --- Monospace WhatsApp Hourly Template ---
    template_hourly = f"""\
{vessel_name}
Berthed {berthed_date}

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
            Open    Close
FWD        {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID        {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT        {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Idle / Delays*
"""

    for idle_entry in idle_list:
        template_hourly += f"{idle_entry['crane']} {idle_entry['start']} - {idle_entry['end']} {idle_entry['delay']}\n"

    st.subheader("Hourly Template Preview")
    st.code(template_hourly, language="text")

    # --- 4-Hourly Report Section ---
    # --- 4-Hourly Report Section ---
st.header("4-Hourly Report")
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
four_hour_choice = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

# --- Collapsible Inputs for 4-Hourly Section ---
with st.expander("Edit Crane Moves (Load / Discharge)"):
    fwd_load_4h = st.number_input("FWD Load", min_value=0, value=fwd_load)
    mid_load_4h = st.number_input("MID Load", min_value=0, value=mid_load)
    aft_load_4h = st.number_input("AFT Load", min_value=0, value=aft_load)
    poop_load_4h = st.number_input("POOP Load", min_value=0, value=poop_load)

    fwd_disch_4h = st.number_input("FWD Discharge", min_value=0, value=fwd_disch)
    mid_disch_4h = st.number_input("MID Discharge", min_value=0, value=mid_disch)
    aft_disch_4h = st.number_input("AFT Discharge", min_value=0, value=aft_disch)
    poop_disch_4h = st.number_input("POOP Discharge", min_value=0, value=poop_disch)

with st.expander("Edit Restows (Load / Discharge)"):
    fwd_restow_load_4h = st.number_input("FWD Restow Load", min_value=0, value=fwd_restow_load)
    mid_restow_load_4h = st.number_input("MID Restow Load", min_value=0, value=mid_restow_load)
    aft_restow_load_4h = st.number_input("AFT Restow Load", min_value=0, value=aft_restow_load)
    poop_restow_load_4h = st.number_input("POOP Restow Load", min_value=0, value=poop_restow_load)

    fwd_restow_disch_4h = st.number_input("FWD Restow Discharge", min_value=0, value=fwd_restow_disch)
    mid_restow_disch_4h = st.number_input("MID Restow Discharge", min_value=0, value=mid_restow_disch)
    aft_restow_disch_4h = st.number_input("AFT Restow Discharge", min_value=0, value=aft_restow_disch)
    poop_restow_disch_4h = st.number_input("POOP Restow Discharge", min_value=0, value=poop_restow_disch)

with st.expander("Edit Hatch Moves (Open / Close)"):
    hatch_fwd_open_4h = st.number_input("FWD Hatch Open", min_value=0, value=hatch_fwd_open)
    hatch_mid_open_4h = st.number_input("MID Hatch Open", min_value=0, value=hatch_mid_open)
    hatch_aft_open_4h = st.number_input("AFT Hatch Open", min_value=0, value=hatch_aft_open)

    hatch_fwd_close_4h = st.number_input("FWD Hatch Close", min_value=0, value=hatch_fwd_close)
    hatch_mid_close_4h = st.number_input("MID Hatch Close", min_value=0, value=hatch_mid_close)
    hatch_aft_close_4h = st.number_input("AFT Hatch Close", min_value=0, value=hatch_aft_close)

# --- Idle / Delays Section ---
with st.expander("Idle / Delays"):
    idle_entries = []
    for i in range(10):  # Up to 10 idles
        st.subheader(f"Idle Entry {i+1}")
        crane_idle = st.selectbox(f"Crane for Idle {i+1}", ["FWD", "MID", "AFT", "POOP"], key=f"crane_idle_{i}")
        start_idle = st.text_input(f"Start Time {i+1} (hh:mm)", key=f"start_idle_{i}")
        end_idle = st.text_input(f"End Time {i+1} (hh:mm)", key=f"end_idle_{i}")
        delay_options = [
            "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
            "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
            "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
            "Crane break down/ boom limit", "Crane break down", "Vessel listing",
            "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
        ]
        delay_idle = st.selectbox(f"Select Delay {i+1}", delay_options, key=f"delay_idle_{i}")
        custom_delay = st.text_input(f"Or enter custom delay {i+1}", key=f"custom_delay_{i}")
        idle_entries.append({
            "crane": crane_idle,
            "start": start_idle,
            "end": end_idle,
            "delay": custom_delay if custom_delay else delay_idle
        })

# --- Monospace Template with Cumulative ---
template_4hour = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_choice}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
            Load    Discharge
FWD        {fwd_load_4h:>5}     {fwd_disch_4h:>5}
MID        {mid_load_4h:>5}     {mid_disch_4h:>5}
AFT        {aft_load_4h:>5}     {aft_disch_4h:>5}
POOP       {poop_load_4h:>5}     {poop_disch_4h:>5}
_________________________
*Restows*
            Load    Discharge
FWD        {fwd_restow_load_4h:>5}     {fwd_restow_disch_4h:>5}
MID        {mid_restow_load_4h:>5}     {mid_restow_disch_4h:>5}
AFT        {aft_restow_load_4h:>5}     {aft_restow_disch_4h:>5}
POOP       {poop_restow_load_4h:>5}     {poop_restow_disch_4h:>5}
_________________________
      *CUMULATIVE* (from hourly totals)
_________________________
            Load   Discharge
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {planned_load - cumulative['done_load']:>5}      {planned_disch - cumulative['done_disch']:>5}
_________________________
*Restows*
            Load    Discharge
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {planned_restow_load - cumulative['done_restow_load']:>5}      {planned_restow_disch - cumulative['done_restow_disch']:>5}
_________________________
*Hatch Moves*
            Open    Close
FWD        {hatch_fwd_open_4h:>5}      {hatch_fwd_close_4h:>5}
MID        {hatch_mid_open_4h:>5}      {hatch_mid_close_4h:>5}
AFT        {hatch_aft_open_4h:>5}      {hatch_aft_close_4h:>5}
_________________________
*Idle / Delays*
"""

for idle_entry in idle_entries:
    template_4hour += f"{idle_entry['crane']} {idle_entry['start']} - {idle_entry['end']} {idle_entry['delay']}\n"

st.subheader("4-Hourly Template Preview")
st.code(template_4hour, language="text")

    # --- Send to WhatsApp ---
     if whatsapp_number:
        wa_hourly = f"```{hourly_template}```"
        wa_four_hour = f"```{four_hour_template}```"
        if whatsapp_type == "Private Number":
            wa_link_hourly = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_hourly)}"
            wa_link_4h = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_four_hour)}"
        else:
            wa_link_hourly = f"{whatsapp_number}?text={urllib.parse.quote(wa_hourly)}"
            wa_link_4h = f"{whatsapp_number}?text={urllib.parse.quote(wa_four_hour)}"

        st.markdown(f"[Open Hourly WhatsApp]({wa_link_hourly})", unsafe_allow_html=True)
        st.markdown(f"[Open 4-Hourly WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
