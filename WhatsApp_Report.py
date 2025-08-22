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
            cumulative = None
else:
    cumulative = None

if cumulative is None:
    cumulative = {
        "done_load": 0, "done_disch": 0,
        "done_restow_load": 0, "done_restow_disch": 0,
        "done_hatch_open": 0, "done_hatch_close": 0,
        "last_hour": None,
        "vessel_name": "MSC NILA",
        "berthed_date": "14/08/2025 @ 10H55",
        "planned_load": 687, "planned_disch": 38,
        "planned_restow_load": 13, "planned_restow_disch": 13,
        "opening_load": 0, "opening_disch": 0,
        "opening_restow_load": 0, "opening_restow_disch": 0
    }

# --- Timezone ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Plan & Opening Balances (Collapsible) ---
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

# --- Hourly Time Dropdown (full 24h) ---
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

st.header(f"Hourly Moves Input ({hourly_time})")

# --- Hourly Crane Moves ---
with st.expander("Crane Moves"):
    with st.expander("Load"):
        fwd_load = st.number_input("FWD Load", min_value=0, value=0)
        mid_load = st.number_input("MID Load", min_value=0, value=0)
        aft_load = st.number_input("AFT Load", min_value=0, value=0)
        poop_load = st.number_input("POOP Load", min_value=0, value=0)
    with st.expander("Discharge"):
        fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
        mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
        aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
        poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)
        # --- Hourly Restows ---
with st.expander("Restows"):
    with st.expander("Load"):
        fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
        mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
        aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
        poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    with st.expander("Discharge"):
        fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
        mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
        aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
        poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# --- Hourly Hatch Moves ---
with st.expander("Hatch Moves"):
    with st.expander("Open"):
        hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
        hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
        hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
    with st.expander("Close"):
        hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
        hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
        hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle / Delays Section (Multiple Entries Collapsible) ---
st.header("Idle / Delays")
num_idles = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=1)
idle_entries = []

idle_options = [
    "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
    "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
    "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
    "Crane break down/ boom limit", "Crane break down", "Vessel listing",
    "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
]

with st.expander("Idle Entries", expanded=False):
    for i in range(num_idles):
        st.subheader(f"Idle Entry {i+1}")
        crane_name = st.text_input(f"Crane Name {i+1}", "")
        start_time = st.text_input(f"Start Time {i+1}", "")
        end_time = st.text_input(f"End Time {i+1}", "")
        selected_delay = st.selectbox(f"Select Delay {i+1}", options=idle_options)
        custom_delay = st.text_input(f"Custom Delay {i+1} (optional)", "")
        idle_entries.append({
            "crane": crane_name,
            "start": start_time,
            "end": end_time,
            "delay": custom_delay if custom_delay else selected_delay
        })

# --- WhatsApp Section for Hourly Report ---
st.header("Send Hourly Report to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
whatsapp_group_link = st.text_input("Or enter WhatsApp Group Link (optional)")

# --- Submit Button for Hourly Report ---
if st.button("Generate & Send Hourly Template"):
    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save persistent fields
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

    # Create monospace template for WhatsApp
    template = f"""\
{vessel_name}
Berthed {berthed_date}

Hour: {hourly_time}
_________________________
*HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {fwd_load:>5}     {fwd_disch:>5}
MID       {mid_load:>5}     {mid_disch:>5}
AFT       {aft_load:>5}     {aft_disch:>5}
POOP      {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {fwd_restow_load:>5}     {fwd_restow_disch:>5}
MID       {mid_restow_load:>5}     {mid_restow_disch:>5}
AFT       {aft_restow_load:>5}     {aft_restow_disch:>5}
POOP      {poop_restow_load:>5}     {poop_restow_disch:>5}
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
FWD       {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID       {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT       {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Idle / Delays*
"""

    for i, idle in enumerate(idle_entries):
        template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

    st.code(template, language="text")

    # Send to WhatsApp
    if whatsapp_number:
        wa_template = f"```{template}```"
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif whatsapp_group_link:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link})", unsafe_allow_html=True)
        # --- Hourly Restows ---
with st.expander("Restows"):
    with st.expander("Load"):
        fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
        mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
        aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
        poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    with st.expander("Discharge"):
        fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
        mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
        aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
        poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# --- Hourly Hatch Moves ---
with st.expander("Hatch Moves"):
    with st.expander("Open"):
        hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
        hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
        hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
    with st.expander("Close"):
        hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
        hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
        hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- Idle / Delays Section (Multiple Entries Collapsible) ---
st.header("Idle / Delays")
num_idles = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=1)
idle_entries = []

idle_options = [
    "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
    "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
    "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
    "Crane break down/ boom limit", "Crane break down", "Vessel listing",
    "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
]

with st.expander("Idle Entries", expanded=False):
    for i in range(num_idles):
        st.subheader(f"Idle Entry {i+1}")
        crane_name = st.text_input(f"Crane Name {i+1}", "")
        start_time = st.text_input(f"Start Time {i+1}", "")
        end_time = st.text_input(f"End Time {i+1}", "")
        selected_delay = st.selectbox(f"Select Delay {i+1}", options=idle_options)
        custom_delay = st.text_input(f"Custom Delay {i+1} (optional)", "")
        idle_entries.append({
            "crane": crane_name,
            "start": start_time,
            "end": end_time,
            "delay": custom_delay if custom_delay else selected_delay
        })

# --- WhatsApp Section for Hourly Report ---
st.header("Send Hourly Report to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
whatsapp_group_link = st.text_input("Or enter WhatsApp Group Link (optional)")

# --- Submit Button for Hourly Report ---
if st.button("Generate & Send Hourly Template"):
    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save persistent fields
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

    # Create monospace template for WhatsApp
    template = f"""\
{vessel_name}
Berthed {berthed_date}

Hour: {hourly_time}
_________________________
*HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {fwd_load:>5}     {fwd_disch:>5}
MID       {mid_load:>5}     {mid_disch:>5}
AFT       {aft_load:>5}     {aft_disch:>5}
POOP      {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {fwd_restow_load:>5}     {fwd_restow_disch:>5}
MID       {mid_restow_load:>5}     {mid_restow_disch:>5}
AFT       {aft_restow_load:>5}     {aft_restow_disch:>5}
POOP      {poop_restow_load:>5}     {poop_restow_disch:>5}
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
FWD       {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID       {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT       {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Idle / Delays*
"""

    for i, idle in enumerate(idle_entries):
        template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

    st.code(template, language="text")

    # Send to WhatsApp
    if whatsapp_number:
        wa_template = f"```{template}```"
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif whatsapp_group_link:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link})", unsafe_allow_html=True)
        # --- 4-Hourly Report Section ---
st.header("4-Hourly Report")

four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]

four_hour_selected = st.selectbox("Select 4-Hour Block", options=four_hour_blocks, index=0)

# --- 4-Hourly Collapsible Inputs ---
with st.expander("Edit 4-Hourly Inputs (Crane, Restows, Hatch)", expanded=False):
    st.subheader("Crane Moves")
    fwd_4h_load = st.number_input("FWD Load 4H", min_value=0, value=0)
    mid_4h_load = st.number_input("MID Load 4H", min_value=0, value=0)
    aft_4h_load = st.number_input("AFT Load 4H", min_value=0, value=0)
    poop_4h_load = st.number_input("POOP Load 4H", min_value=0, value=0)

    fwd_4h_disch = st.number_input("FWD Discharge 4H", min_value=0, value=0)
    mid_4h_disch = st.number_input("MID Discharge 4H", min_value=0, value=0)
    aft_4h_disch = st.number_input("AFT Discharge 4H", min_value=0, value=0)
    poop_4h_disch = st.number_input("POOP Discharge 4H", min_value=0, value=0)

    st.subheader("Restows")
    fwd_4h_restow_load = st.number_input("FWD Restow Load 4H", min_value=0, value=0)
    mid_4h_restow_load = st.number_input("MID Restow Load 4H", min_value=0, value=0)
    aft_4h_restow_load = st.number_input("AFT Restow Load 4H", min_value=0, value=0)
    poop_4h_restow_load = st.number_input("POOP Restow Load 4H", min_value=0, value=0)

    fwd_4h_restow_disch = st.number_input("FWD Restow Discharge 4H", min_value=0, value=0)
    mid_4h_restow_disch = st.number_input("MID Restow Discharge 4H", min_value=0, value=0)
    aft_4h_restow_disch = st.number_input("AFT Restow Discharge 4H", min_value=0, value=0)
    poop_4h_restow_disch = st.number_input("POOP Restow Discharge 4H", min_value=0, value=0)

    st.subheader("Hatch Covers")
    hatch_fwd_4h_open = st.number_input("FWD Hatch Open 4H", min_value=0, value=0)
    hatch_mid_4h_open = st.number_input("MID Hatch Open 4H", min_value=0, value=0)
    hatch_aft_4h_open = st.number_input("AFT Hatch Open 4H", min_value=0, value=0)

    hatch_fwd_4h_close = st.number_input("FWD Hatch Close 4H", min_value=0, value=0)
    hatch_mid_4h_close = st.number_input("MID Hatch Close 4H", min_value=0, value=0)
    hatch_aft_4h_close = st.number_input("AFT Hatch Close 4H", min_value=0, value=0)

# --- Calculate 4-Hourly Cumulative from Hourly Totals ---
cumulative_4h_load = cumulative["done_load"]
cumulative_4h_disch = cumulative["done_disch"]
cumulative_4h_restow_load = cumulative["done_restow_load"]
cumulative_4h_restow_disch = cumulative["done_restow_disch"]

# --- Reset 4-Hourly Cumulative Button ---
if st.button("Reset 4-Hourly Cumulative"):
    cumulative_4h_load = 0
    cumulative_4h_disch = 0
    cumulative_4h_restow_load = 0
    cumulative_4h_restow_disch = 0
    st.success("4-Hourly cumulative totals reset!")

# --- 4-Hourly WhatsApp Template ---
four_hour_template = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_selected}
_________________________
*CRANE MOVES*
           Load    Discharge
FWD       {fwd_4h_load:>5}     {fwd_4h_disch:>5}
MID       {mid_4h_load:>5}     {mid_4h_disch:>5}
AFT       {aft_4h_load:>5}     {aft_4h_disch:>5}
POOP      {poop_4h_load:>5}     {poop_4h_disch:>5}
_________________________
*RESTOWS*
           Load    Discharge
FWD       {fwd_4h_restow_load:>5}     {fwd_4h_restow_disch:>5}
MID       {mid_4h_restow_load:>5}     {mid_4h_restow_disch:>5}
AFT       {aft_4h_restow_load:>5}     {aft_4h_restow_disch:>5}
POOP      {poop_4h_restow_load:>5}     {poop_4h_restow_disch:>5}
_________________________
*CUMULATIVE (from Hourly totals)*
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative_4h_load:>5}      {cumulative_4h_disch:>5}
Remain     {planned_load - cumulative_4h_load:>5}      {planned_disch - cumulative_4h_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative_4h_restow_load:>5}      {cumulative_4h_restow_disch:>5}
Remain     {planned_restow_load - cumulative_4h_restow_load:>5}      {planned_restow_disch - cumulative_4h_restow_disch:>5}
_________________________
*HATCH MOVES*
             Open         Close
FWD          {hatch_fwd_4h_open:>5}          {hatch_fwd_4h_close:>5}
MID          {hatch_mid_4h_open:>5}          {hatch_mid_4h_close:>5}
AFT          {hatch_aft_4h_open:>5}          {hatch_aft_4h_close:>5}
_________________________
*Idle / Delays*
"""

for i, idle in enumerate(idle_entries):
    four_hour_template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

st.code(four_hour_template, language="text")

# --- WhatsApp 4-Hourly Send ---
whatsapp_number_4h = st.text_input("Enter WhatsApp Number for 4H report (optional)")
whatsapp_group_link_4h = st.text_input("Or WhatsApp Group Link for 4H report (optional)")

if st.button("Send 4-Hourly Template"):
    if whatsapp_number_4h:
        wa_4h_template = f"```{four_hour_template}```"
        wa_link_4h = f"https://wa.me/{whatsapp_number_4h}?text={urllib.parse.quote(wa_4h_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
    elif whatsapp_group_link_4h:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link_4h})", unsafe_allow_html=True)
        # --- Sync 4-Hourly Cumulative Automatically with Hourly Changes ---
def sync_4h_with_hourly():
    """Automatically update 4-hourly totals when hourly cumulative changes."""
    global cumulative_4h_load, cumulative_4h_disch, cumulative_4h_restow_load, cumulative_4h_restow_disch
    cumulative_4h_load = cumulative["done_load"]
    cumulative_4h_disch = cumulative["done_disch"]
    cumulative_4h_restow_load = cumulative["done_restow_load"]
    cumulative_4h_restow_disch = cumulative["done_restow_disch"]

sync_4h_with_hourly()

# --- Display Hourly & 4-Hourly Info Side by Side ---
st.header("Summary")
col_hourly, col_4hour = st.columns(2)

with col_hourly:
    st.subheader("Hourly Cumulative")
    st.text(f"Load Done: {cumulative['done_load']}")
    st.text(f"Disch Done: {cumulative['done_disch']}")
    st.text(f"Restow Load Done: {cumulative['done_restow_load']}")
    st.text(f"Restow Disch Done: {cumulative['done_restow_disch']}")

with col_4hour:
    st.subheader("4-Hourly Cumulative")
    st.text(f"Load Done: {cumulative_4h_load}")
    st.text(f"Disch Done: {cumulative_4h_disch}")
    st.text(f"Restow Load Done: {cumulative_4h_restow_load}")
    st.text(f"Restow Disch Done: {cumulative_4h_restow_disch}")

# --- Optional: Save & Reset Buttons for Entire Report ---
st.header("Manage Report Data")

if st.button("Reset Entire Cumulative Data"):
    cumulative = {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "last_hour": None,
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
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)
    st.success("Entire cumulative data reset!")

if st.button("Save Current Cumulative Data"):
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
        "opening_restow_disch": opening_restow_disch,
        "last_hour": hourly_time
    })
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)
    st.success("Cumulative data saved successfully!")

# --- Professional Touches ---
st.markdown("""
<style>
    .stTextInput>div>input {font-family: monospace;}
    .stNumberInput>div>input {font-family: monospace;}
</style>
""", unsafe_allow_html=True)

st.info("✅ All inputs are collapsible and grouped. 4-Hourly cumulative syncs automatically with hourly totals. Idle entries support multiple selections.")
st.info("📌 Use the reset buttons carefully. WhatsApp templates are formatted in monospace for easy copying.")