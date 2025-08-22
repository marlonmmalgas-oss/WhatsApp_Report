import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Load or initialize persistent data ---
if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as f:
            cumulative = json.load(f)
    except json.JSONDecodeError:
        cumulative = {}
else:
    cumulative = {}

# --- Initialize default values if not present ---
def init_value(key, default):
    if key not in cumulative:
        cumulative[key] = default
    return cumulative[key]

vessel_name = init_value("vessel_name", "MSC NILA")
berthed_date = init_value("berthed_date", "14/08/2025 @ 10H55")
first_lift = init_value("first_lift", "18h25")
last_lift = init_value("last_lift", "10h31")

planned_load = init_value("planned_load", 687)
planned_disch = init_value("planned_disch", 38)
planned_restow_load = init_value("planned_restow_load", 13)
planned_restow_disch = init_value("planned_restow_disch", 13)

opening_load = init_value("opening_load", 0)
opening_disch = init_value("opening_disch", 0)
opening_restow_load = init_value("opening_restow_load", 0)
opening_restow_disch = init_value("opening_restow_disch", 0)

# --- Hourly totals ---
hourly_totals = init_value("hourly_totals", {
    "Load_FWD":0, "Load_MID":0, "Load_AFT":0, "Load_POOP":0,
    "Disch_FWD":0, "Disch_MID":0, "Disch_AFT":0, "Disch_POOP":0,
    "Restow_Load_FWD":0, "Restow_Load_MID":0, "Restow_Load_AFT":0, "Restow_Load_POOP":0,
    "Restow_Disch_FWD":0, "Restow_Disch_MID":0, "Restow_Disch_AFT":0, "Restow_Disch_POOP":0,
    "Hatch_Open_FWD":0, "Hatch_Open_MID":0, "Hatch_Open_AFT":0,
    "Hatch_Close_FWD":0, "Hatch_Close_MID":0, "Hatch_Close_AFT":0
})

# --- 4-Hourly totals ---
four_hourly_totals = init_value("four_hourly_totals", hourly_totals.copy())

# --- South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", vessel_name)
berthed_date = st.text_input("Berthed Date", berthed_date)
first_lift = st.text_input("First Lift (time only)", first_lift)
last_lift = st.text_input("Last Lift (time only)", last_lift)

# --- Collapsible Plan & Opening Balance ---
with st.expander("Plan & Opening Balance (Internal)"):
    col1, col2 = st.columns(2)
    with col1:
        planned_load = st.number_input("Planned Load", value=planned_load)
        planned_disch = st.number_input("Planned Discharge", value=planned_disch)
        planned_restow_load = st.number_input("Planned Restow Load", value=planned_restow_load)
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=planned_restow_disch)
    with col2:
        opening_load = st.number_input("Opening Load (Deduction)", value=opening_load)
        opening_disch = st.number_input("Opening Discharge (Deduction)", value=opening_disch)
        opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=opening_restow_load)
        opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=opening_restow_disch)

# --- Hourly Time Dropdown ---
st.header("Hourly Time")
hours_list = []
for h in range(24):
    start_hour = h
    end_hour = (h + 1) % 24
    hours_list.append(f"{str(start_hour).zfill(2)}h00 - {str(end_hour).zfill(2)}h00")
hourly_time = st.selectbox("Select Hourly Time", hours_list, index=hours_list.index(init_value("last_hour","06h00 - 07h00")))

# --- Collapsible Hourly Input Groups ---
with st.expander("Hourly Moves Input"):
    st.subheader("Crane Moves")
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    poop_load = st.number_input("POOP Load", min_value=0, value=0)
    
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)
    
    st.subheader("Restows")
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)
    
    st.subheader("Hatch Moves")
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
    
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle Section ---
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
    "Other"
]
st.header("Idle / Delays")
selected_idle = st.selectbox("Select Delay", idle_options)
custom_idle = st.text_input("Custom Delay (if 'Other' selected)", "")

idle_crane = st.text_input("Crane")
idle_start = st.text_input("Start Time")
idle_end = st.text_input("End Time")

# --- Submit Hourly ---
if st.button("Submit Hourly"):
    # Update cumulative
    hourly_totals["Load_FWD"] += fwd_load
    hourly_totals["Load_MID"] += mid_load
    hourly_totals["Load_AFT"] += aft_load
    hourly_totals["Load_POOP"] += poop_load
    
    hourly_totals["Disch_FWD"] += fwd_disch
    hourly_totals["Disch_MID"] += mid_disch
    hourly_totals["Disch_AFT"] += aft_disch
    hourly_totals["Disch_POOP"] += poop_disch
    
    hourly_totals["Restow_Load_FWD"] += fwd_restow_load
    hourly_totals["Restow_Load_MID"] += mid_restow_load
    hourly_totals["Restow_Load_AFT"] += aft_restow_load
    hourly_totals["Restow_Load_POOP"] += poop_restow_load
    
    hourly_totals["Restow_Disch_FWD"] += fwd_restow_disch
    hourly_totals["Restow_Disch_MID"] += mid_restow_disch
    hourly_totals["Restow_Disch_AFT"] += aft_restow_disch
    hourly_totals["Restow_Disch_POOP"] += poop_restow_disch
    
    hourly_totals["Hatch_Open_FWD"] += hatch_fwd_open
    hourly_totals["Hatch_Open_MID"] += hatch_mid_open
    hourly_totals["Hatch_Open_AFT"] += hatch_aft_open
    
    hourly_totals["Hatch_Close_FWD"] += hatch_fwd_close
    hourly_totals["Hatch_Close_MID"] += hatch_mid_close
    hourly_totals["Hatch_Close_AFT"] += hatch_aft_close
    
    cumulative.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date,
        "first_lift": first_lift,
        "last_lift": last_lift,
        "planned_load": planned_load,
        "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load,
        "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load,
        "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load,
        "opening_restow_disch": opening_restow_disch,
        "hourly_totals": hourly_totals,
        "last_hour": hourly_time
    })

    # Save to file
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    st.success("Hourly moves submitted successfully!")

# --- 4-Hourly Dropdown ---
st.header("4-Hourly Time Block")
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
four_hour_block = st.selectbox("Select 4-Hourly Block", four_hour_blocks, index=0)

# --- Collapsible 4-Hourly Input Groups ---
with st.expander("4-Hourly Moves Input"):
    st.subheader("Crane Moves")
    fwd_load_4h = st.number_input("FWD Load", min_value=0, value=0, key="4h_fwd_load")
    mid_load_4h = st.number_input("MID Load", min_value=0, value=0, key="4h_mid_load")
    aft_load_4h = st.number_input("AFT Load", min_value=0, value=0, key="4h_aft_load")
    poop_load_4h = st.number_input("POOP Load", min_value=0, value=0, key="4h_poop_load")
    
    fwd_disch_4h = st.number_input("FWD Discharge", min_value=0, value=0, key="4h_fwd_disch")
    mid_disch_4h = st.number_input("MID Discharge", min_value=0, value=0, key="4h_mid_disch")
    aft_disch_4h = st.number_input("AFT Discharge", min_value=0, value=0, key="4h_aft_disch")
    poop_disch_4h = st.number_input("POOP Discharge", min_value=0, value=0, key="4h_poop_disch")
    
    st.subheader("Restows")
    fwd_restow_load_4h = st.number_input("FWD Restow Load", min_value=0, value=0, key="4h_fwd_restow_load")
    mid_restow_load_4h = st.number_input("MID Restow Load", min_value=0, value=0, key="4h_mid_restow_load")
    aft_restow_load_4h = st.number_input("AFT Restow Load", min_value=0, value=0, key="4h_aft_restow_load")
    poop_restow_load_4h = st.number_input("POOP Restow Load", min_value=0, value=0, key="4h_poop_restow_load")
    
    fwd_restow_disch_4h = st.number_input("FWD Restow Discharge", min_value=0, value=0, key="4h_fwd_restow_disch")
    mid_restow_disch_4h = st.number_input("MID Restow Discharge", min_value=0, value=0, key="4h_mid_restow_disch")
    aft_restow_disch_4h = st.number_input("AFT Restow Discharge", min_value=0, value=0, key="4h_aft_restow_disch")
    poop_restow_disch_4h = st.number_input("POOP Restow Discharge", min_value=0, value=0, key="4h_poop_restow_disch")
    
    st.subheader("Hatch Moves")
    hatch_fwd_open_4h = st.number_input("FWD Hatch Open", min_value=0, value=0, key="4h_hatch_fwd_open")
    hatch_mid_open_4h = st.number_input("MID Hatch Open", min_value=0, value=0, key="4h_hatch_mid_open")
    hatch_aft_open_4h = st.number_input("AFT Hatch Open", min_value=0, value=0, key="4h_hatch_aft_open")
    
    hatch_fwd_close_4h = st.number_input("FWD Hatch Close", min_value=0, value=0, key="4h_hatch_fwd_close")
    hatch_mid_close_4h = st.number_input("MID Hatch Close", min_value=0, value=0, key="4h_hatch_mid_close")
    hatch_aft_close_4h = st.number_input("AFT Hatch Close", min_value=0, value=0, key="4h_hatch_aft_close")

# --- Submit 4-Hourly ---
if st.button("Submit 4-Hourly"):
    four_hourly_totals.update({
        "Load_FWD": fwd_load_4h,
        "Load_MID": mid_load_4h,
        "Load_AFT": aft_load_4h,
        "Load_POOP": poop_load_4h,
        "Disch_FWD": fwd_disch_4h,
        "Disch_MID": mid_disch_4h,
        "Disch_AFT": aft_disch_4h,
        "Disch_POOP": poop_disch_4h,
        "Restow_Load_FWD": fwd_restow_load_4h,
        "Restow_Load_MID": mid_restow_load_4h,
        "Restow_Load_AFT": aft_restow_load_4h,
        "Restow_Load_POOP": poop_restow_load_4h,
        "Restow_Disch_FWD": fwd_restow_disch_4h,
        "Restow_Disch_MID": mid_restow_disch_4h,
        "Restow_Disch_AFT": aft_restow_disch_4h,
        "Restow_Disch_POOP": poop_restow_disch_4h,
        "Hatch_Open_FWD": hatch_fwd_open_4h,
        "Hatch_Open_MID": hatch_mid_open_4h,
        "Hatch_Open_AFT": hatch_aft_open_4h,
        "Hatch_Close_FWD": hatch_fwd_close_4h,
        "Hatch_Close_MID": hatch_mid_close_4h,
        "Hatch_Close_AFT": hatch_aft_close_4h
    })
    cumulative["four_hourly_totals"] = four_hourly_totals
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)
    st.success("4-Hourly moves submitted successfully!")

# --- WhatsApp Section ---
st.header("Send Reports to WhatsApp")
wa_type = st.radio("Choose WhatsApp Type", ["Private Number", "Group Link"])

whatsapp_number = ""
if wa_type == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
else:
    whatsapp_group_link = st.text_input("Enter WhatsApp Group Link")

st.markdown("**Hourly Template Preview:**")
hourly_template = f"""\
{vessel_name}
Berthed {berthed_date}

First Lift @ {first_lift}
Last Lift @ {last_lift}

Date: {today_date}
Hourly Block: {hourly_time}
_________________________
*HOURLY MOVES*
_________________________
Load FWD: {hourly_totals['Load_FWD']}, MID: {hourly_totals['Load_MID']}, AFT: {hourly_totals['Load_AFT']}, POOP: {hourly_totals['Load_POOP']}
Disch FWD: {hourly_totals['Disch_FWD']}, MID: {hourly_totals['Disch_MID']}, AFT: {hourly_totals['Disch_AFT']}, POOP: {hourly_totals['Disch_POOP']}
Restow Load FWD: {hourly_totals['Restow_Load_FWD']}, MID: {hourly_totals['Restow_Load_MID']}, AFT: {hourly_totals['Restow_Load_AFT']}, POOP: {hourly_totals['Restow_Load_POOP']}
Restow Disch FWD: {hourly_totals['Restow_Disch_FWD']}, MID: {hourly_totals['Restow_Disch_MID']}, AFT: {hourly_totals['Restow_Disch_AFT']}, POOP: {hourly_totals['Restow_Disch_POOP']}
Hatch Open FWD: {hourly_totals['Hatch_Open_FWD']}, MID: {hourly_totals['Hatch_Open_MID']}, AFT: {hourly_totals['Hatch_Open_AFT']}
Hatch Close FWD: {hourly_totals['Hatch_Close_FWD']}, MID: {hourly_totals['Hatch_Close_MID']}, AFT: {hourly_totals['Hatch_Close_AFT']}
Idle: {selected_idle} {custom_idle}
"""

st.code(hourly_template)

# --- 4-Hourly Template Preview ---
st.markdown("**4-Hourly Template Preview:**")
four_hourly_template = f"""\
{vessel_name}
Berthed {berthed_date}

4-Hour Block: {four_hour_block}
_________________________
*HOURLY MOVES*
_________________________
Load FWD: {four_hourly_totals['Load_FWD']}, MID: {four_hourly_totals['Load_MID']}, AFT: {four_hourly_totals['Load_AFT']}, POOP: {four_hourly_totals['Load_POOP']}
Disch FWD: {four_hourly_totals['Disch_FWD']}, MID: {four_hourly_totals['Disch_MID']}, AFT: {four_hourly_totals['Disch_AFT']}, POOP: {four_hourly_totals['Disch_POOP']}
Restow Load FWD: {four_hourly_totals['Restow_Load_FWD']}, MID: {four_hourly_totals['Restow_Load_MID']}, AFT: {four_hourly_totals['Restow_Load_AFT']}, POOP: {four_hourly_totals['Restow_Load_POOP']}
Restow Disch FWD: {four_hourly_totals['Restow_Disch_FWD']}, MID: {four_hourly_totals['Restow_Disch_MID']}, AFT: {four_hourly_totals['Restow_Disch_AFT']}, POOP: {four_hourly_totals['Restow_Disch_POOP']}
Hatch Open FWD: {four_hourly_totals['Hatch_Open_FWD']}, MID: {four_hourly_totals['Hatch_Open_MID']}, AFT: {four_hourly_totals['Hatch_Open_AFT']}
Hatch Close FWD: {four_hourly_totals['Hatch_Close_FWD']}, MID: {four_hourly_totals['Hatch_Close_MID']}, AFT: {four_hourly_totals['Hatch_Close_AFT']}
Idle: {selected_idle} {custom_idle}
"""

st.code(four_hourly_template)

# --- WhatsApp Link Generation ---
if st.button("Generate WhatsApp Link for Hourly Report"):
    msg = urllib.parse.quote(hourly_template)
    if wa_type == "Private Number":
        wa_link = f"https://wa.me/{whatsapp_number}?text={msg}"
    else:
        wa_link = f"{whatsapp_group_link}?text={msg}"
    st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)

if st.button("Generate WhatsApp Link for 4-Hourly Report"):
    msg = urllib.parse.quote(four_hourly_template)
    if wa_type == "Private Number":
        wa_link = f"https://wa.me/{whatsapp_number}?text={msg}"
    else:
        wa_link = f"{whatsapp_group_link}?text={msg}"
    st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)