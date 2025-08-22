import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Load or initialize cumulative data ---
if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as f:
            cumulative = json.load(f)
    except json.JSONDecodeError:
        cumulative = {}
else:
    cumulative = {}

# Default cumulative if empty
cumulative = {**{
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
}, **cumulative}

# --- Current South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift Time", value="06h00")
last_lift = st.text_input("Last Lift Time", value="18h00")

# --- Plan Totals & Opening Balance ---
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

# --- Hourly Time Dropdown ---
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves ---
st.header(f"Hourly Moves Input ({hourly_time})")

# Crane Load
with st.expander("Load"):
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    poop_load = st.number_input("POOP Load", min_value=0, value=0)

# Crane Discharge
with st.expander("Discharge"):
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)

# Restow Load
with st.expander("Restow Load"):
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)

# Restow Discharge
with st.expander("Restow Discharge"):
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# Hatch Cover Open
with st.expander("Hatch Cover Open"):
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)

# Hatch Cover Close
with st.expander("Hatch Cover Close"):
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle Section ---
st.header("Idle / Delays")
idle_options = [
    "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
    "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
    "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
    "Crane break down/ boom limit", "Crane break down", "Vessel listing",
    "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
]
idle_entries = []
for i in range(5):  # Allow up to 5 idle entries
    col1, col2, col3 = st.columns([2,2,3])
    with col1:
        crane_idle = st.selectbox(f"Crane (Idle) {i+1}", ["FWD","MID","AFT","POOP"])
    with col2:
        idle_time = st.text_input(f"Time From-To {i+1}", value="00h00 - 00h00")
    with col3:
        idle_type = st.selectbox(f"Delay Type {i+1}", idle_options)
        custom_delay = st.text_input(f"Custom Delay {i+1}", value="")
    idle_entries.append({
        "crane": crane_idle,
        "time": idle_time,
        "delay": custom_delay if custom_delay else idle_type
    })

# --- WhatsApp Section ---
st.header("Send to WhatsApp")
wa_method = st.radio("Send via:", ["Private Number", "Group Invite Link"])
if wa_method == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
else:
    group_link = st.text_input("Enter WhatsApp Group Invite Link")

# --- Submit Button ---
if st.button("Update Template & Save"):

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

    # --- Generate Hourly WhatsApp Template ---
    hourly_template = f"""
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
Hourly Block: {hourly_time}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD        {fwd_load}         {fwd_disch}
MID        {mid_load}         {mid_disch}
AFT        {aft_load}         {aft_disch}
POOP       {poop_load}         {poop_disch}
_________________________
*Restows*
           Load    Discharge
FWD        {fwd_restow_load}         {fwd_restow_disch}
MID        {mid_restow_load}         {mid_restow_disch}
AFT        {aft_restow_load}         {aft_restow_disch}
POOP       {poop_restow_load}         {poop_restow_disch}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Discharge
Plan       {planned_load}        {planned_disch}
Done       {cumulative['done_load']}          {cumulative['done_disch']}
Remain     {remaining_load}          {remaining_disch}
_________________________
*Restows*
           Load    Discharge
Plan       {planned_restow_load}         {planned_restow_disch}
Done       {cumulative['done_restow_load']}          {cumulative['done_restow_disch']}
Remain     {remaining_restow_load}          {remaining_restow_disch}
_________________________
*Hatch Moves*
             Open         Close
FWD        {hatch_fwd_open}          {hatch_fwd_close}
MID        {hatch_mid_open}          {hatch_mid_close}
AFT        {hatch_aft_open}          {hatch_aft_close}
_________________________
*Idle*
"""

    for idle in idle_entries:
        if idle["delay"]:
            hourly_template += f"{idle['crane']} {idle['time']} {idle['delay']}\n"

    st.text_area("Hourly WhatsApp Template", value=hourly_template, height=600)

    # --- 4-Hourly Report Section ---
    st.header("4-Hourly Report")
    four_hour_blocks = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
    four_hour_time = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

    st.subheader(f"4-Hourly Moves Input ({four_hour_time})")

    # Replicating collapsible groups for 4-hourly report
    with st.expander("Load"):
        fwd_load_4h = st.number_input("FWD Load (4h)", min_value=0, value=0)
        mid_load_4h = st.number_input("MID Load (4h)", min_value=0, value=0)
        aft_load_4h = st.number_input("AFT Load (4h)", min_value=0, value=0)
        poop_load_4h = st.number_input("POOP Load (4h)", min_value=0, value=0)

    with st.expander("Discharge"):
        fwd_disch_4h = st.number_input("FWD Discharge (4h)", min_value=0, value=0)
        mid_disch_4h = st.number_input("MID Discharge (4h)", min_value=0, value=0)
        aft_disch_4h = st.number_input("AFT Discharge (4h)", min_value=0, value=0)
        poop_disch_4h = st.number_input("POOP Discharge (4h)", min_value=0, value=0)

    with st.expander("Restow Load"):
        fwd_restow_load_4h = st.number_input("FWD Restow Load (4h)", min_value=0, value=0)
        mid_restow_load_4h = st.number_input("MID Restow Load (4h)", min_value=0, value=0)
        aft_restow_load_4h = st.number_input("AFT Restow Load (4h)", min_value=0, value=0)
        poop_restow_load_4h = st.number_input("POOP Restow Load (4h)", min_value=0, value=0)

    with st.expander("Restow Discharge"):
        fwd_restow_disch_4h = st.number_input("FWD Restow Discharge (4h)", min_value=0, value=0)
        mid_restow_disch_4h = st.number_input("MID Restow Discharge (4h)", min_value=0, value=0)
        aft_restow_disch_4h = st.number_input("AFT Restow Discharge (4h)", min_value=0, value=0)
        poop_restow_disch_4h = st.number_input("POOP Restow Discharge (4h)", min_value=0, value=0)

    with st.expander("Hatch Cover Open"):
        hatch_fwd_open_4h = st.number_input("FWD Hatch Open (4h)", min_value=0, value=0)
        hatch_mid_open_4h = st.number_input("MID Hatch Open (4h)", min_value=0, value=0)
        hatch_aft_open_4h = st.number_input("AFT Hatch Open (4h)", min_value=0, value=0)

    with st.expander("Hatch Cover Close"):
        hatch_fwd_close_4h = st.number_input("FWD Hatch Close (4h)", min_value=0, value=0)
        hatch_mid_close_4h = st.number_input("MID Hatch Close (4h)", min_value=0, value=0)
        hatch_aft_close_4h = st.number_input("AFT Hatch Close (4h)", min_value=0, value=0)

    # --- 4-Hourly WhatsApp Template ---
    four_hour_template = f"""
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_time}
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD        {fwd_load_4h}         {fwd_disch_4h}
MID        {mid_load_4h}         {mid_disch_4h}
AFT        {aft_load_4h}         {aft_disch_4h}
POOP       {poop_load_4h}         {poop_disch_4h}
_________________________
*Restows*
           Load    Discharge
FWD        {fwd_restow_load_4h}         {fwd_restow_disch_4h}
MID        {mid_restow_load_4h}         {mid_restow_disch_4h}
AFT        {aft_restow_load_4h}         {aft_restow_disch_4h}
POOP       {poop_restow_load_4h}         {poop_restow_disch_4h}
_________________________
*Hatch Moves*
             Open         Close
FWD        {hatch_fwd_open_4h}          {hatch_fwd_close_4h}
MID        {hatch_mid_open_4h}          {hatch_mid_close_4h}
AFT        {hatch_aft_open_4h}          {hatch_aft_close_4h}
"""

    st.text_area("4-Hourly WhatsApp Template", value=four_hour_template, height=600)

    # Optional: create WhatsApp link ready to open
    if wa_method == "Private Number" and whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(hourly_template)}"
        st.markdown(f"[Send Hourly to WhatsApp]({wa_link})", unsafe_allow_html=True)
        wa_link_4h = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(four_hour_template)}"
        st.markdown(f"[Send 4-Hourly to WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
    elif wa_method == "Group Invite Link" and group_link:
        st.markdown(f"[Copy Group Link for WhatsApp]({group_link})", unsafe_allow_html=True)