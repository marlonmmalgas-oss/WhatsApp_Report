import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Initialize or Load Data ---
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        try:
            cumulative = json.load(f)
        except json.JSONDecodeError:
            cumulative = {}
else:
    cumulative = {}

# Default cumulative structure
default_cumulative = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "hourly_records": [],
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

# Merge default with loaded
for key, val in default_cumulative.items():
    cumulative.setdefault(key, val)

# --- South African Time ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift Time", "18h25")
last_lift = st.text_input("Last Lift Time", "10h31")

# --- Plan & Opening Balance (internal only) ---
st.header("Plan Totals & Opening Balance (Internal Only)")
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
st.header("Hourly Time")
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves Input ---
st.header(f"Hourly Moves Input ({hourly_time})")

# Crane section grouped
st.subheader("Crane Moves")
col_fwd, col_mid, col_aft, col_poop = st.columns(4)
with col_fwd:
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
with col_mid:
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
with col_aft:
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
with col_poop:
    poop_load = st.number_input("POOP Load", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)

# Restows
st.subheader("Restows")
col_fwd, col_mid, col_aft, col_poop = st.columns(4)
with col_fwd:
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
with col_mid:
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
with col_aft:
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
with col_poop:
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# Hatch Moves
st.subheader("Hatch Moves")
col_hatch_fwd, col_hatch_mid, col_hatch_aft = st.columns(3)
with col_hatch_fwd:
    hatch_fwd_open = st.number_input("FWD Open", min_value=0, value=0)
    hatch_fwd_close = st.number_input("FWD Close", min_value=0, value=0)
with col_hatch_mid:
    hatch_mid_open = st.number_input("MID Open", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Close", min_value=0, value=0)
with col_hatch_aft:
    hatch_aft_open = st.number_input("AFT Open", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Close", min_value=0, value=0)

# --- WhatsApp Section (Hourly Report) ---
st.header("Send Hourly Report to WhatsApp")
wa_number = st.text_input("WhatsApp Number / Group Link")

# --- Submit Hourly Moves ---
if st.button("Submit Hourly Moves"):

    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save cumulative editable fields
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

    # Add hourly record for 4-hourly calculations
    cumulative.setdefault("hourly_records", []).append({
        "fwd_load": fwd_load, "mid_load": mid_load, "aft_load": aft_load, "poop_load": poop_load,
        "fwd_disch": fwd_disch, "mid_disch": mid_disch, "aft_disch": aft_disch, "poop_disch": poop_disch,
        "fwd_restow_load": fwd_restow_load, "mid_restow_load": mid_restow_load, "aft_restow_load": aft_restow_load, "poop_restow_load": poop_restow_load,
        "fwd_restow_disch": fwd_restow_disch, "mid_restow_disch": mid_restow_disch, "aft_restow_disch": aft_restow_disch, "poop_restow_disch": poop_restow_disch,
        "hatch_fwd_open": hatch_fwd_open, "hatch_fwd_close": hatch_fwd_close,
        "hatch_mid_open": hatch_mid_open, "hatch_mid_close": hatch_mid_close,
        "hatch_aft_open": hatch_aft_open, "hatch_aft_close": hatch_aft_close
    })

    # Save to JSON
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Calculate remaining
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # WhatsApp template (aligned)
    template = f"""\
{vessel_name}
Berthed {berthed_date}

First Lift @ {first_lift}
Last Lift @ {last_lift}

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
# --- Show Hourly Template ---
    st.subheader("Hourly Report Template")
    st.code(template)

    # --- WhatsApp Link for Hourly Report ---
    if wa_number:
        wa_template = f"```{template}```"
        if wa_number.startswith("http"):  # Group link
            st.markdown(f"[Open WhatsApp Group]({wa_number})", unsafe_allow_html=True)
        else:
            wa_link = f"https://wa.me/{wa_number}?text={urllib.parse.quote(wa_template)}"
            st.markdown(f"[Open WhatsApp Private]({wa_link})", unsafe_allow_html=True)

# --- 4-Hourly Report Section ---
st.header("4-Hourly Report")
four_hour_options = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
selected_4h = st.selectbox("Select 4-Hour Block", four_hour_options)

def get_4h_indices(block_label):
    mapping = {
        "06h00 - 10h00": [0,1,2,3],
        "10h00 - 14h00": [4,5,6,7],
        "14h00 - 18h00": [8,9,10,11],
        "18h00 - 22h00": [12,13,14,15],
        "22h00 - 02h00": [16,17,18,19],
        "02h00 - 06h00": [20,21,22,23]
    }
    return mapping.get(block_label, [])

indices = get_4h_indices(selected_4h)
records = [cumulative["hourly_records"][i] for i in indices if i < len(cumulative["hourly_records"])]

if records:
    # Aggregate totals for 4-hour block
    def sum_field(field):
        return sum(r[field] for r in records)
    
    total_fwd_load = sum_field("fwd_load")
    total_mid_load = sum_field("mid_load")
    total_aft_load = sum_field("aft_load")
    total_poop_load = sum_field("poop_load")
    
    total_fwd_disch = sum_field("fwd_disch")
    total_mid_disch = sum_field("mid_disch")
    total_aft_disch = sum_field("aft_disch")
    total_poop_disch = sum_field("poop_disch")
    
    total_fwd_restow_load = sum_field("fwd_restow_load")
    total_mid_restow_load = sum_field("mid_restow_load")
    total_aft_restow_load = sum_field("aft_restow_load")
    total_poop_restow_load = sum_field("poop_restow_load")
    
    total_fwd_restow_disch = sum_field("fwd_restow_disch")
    total_mid_restow_disch = sum_field("mid_restow_disch")
    total_aft_restow_disch = sum_field("aft_restow_disch")
    total_poop_restow_disch = sum_field("poop_restow_disch")
    
    total_hatch_fwd_open = sum_field("hatch_fwd_open")
    total_hatch_fwd_close = sum_field("hatch_fwd_close")
    total_hatch_mid_open = sum_field("hatch_mid_open")
    total_hatch_mid_close = sum_field("hatch_mid_close")
    total_hatch_aft_open = sum_field("hatch_aft_open")
    total_hatch_aft_close = sum_field("hatch_aft_close")
    
    # 4-Hourly Template
    template_4h = f"""\
4-Hourly Report: {selected_4h}

*Crane Moves*
           Load   Disch
FWD        {total_fwd_load:>5}     {total_fwd_disch:>5}
MID        {total_mid_load:>5}     {total_mid_disch:>5}
AFT        {total_aft_load:>5}     {total_aft_disch:>5}
POOP       {total_poop_load:>5}     {total_poop_disch:>5}

*Restows*
           Load   Disch
FWD        {total_fwd_restow_load:>5}     {total_fwd_restow_disch:>5}
MID        {total_mid_restow_load:>5}     {total_mid_restow_disch:>5}
AFT        {total_aft_restow_load:>5}     {total_aft_restow_disch:>5}
POOP       {total_poop_restow_load:>5}     {total_poop_restow_disch:>5}

*Hatch Moves*
           Open   Close
FWD        {total_hatch_fwd_open:>5}     {total_hatch_fwd_close:>5}
MID        {total_hatch_mid_open:>5}     {total_hatch_mid_close:>5}
AFT        {total_hatch_aft_open:>5}     {total_hatch_aft_close:>5}
"""

    st.code(template_4h)

    # WhatsApp input for 4-hourly report
    st.subheader("Send 4-Hourly Report to WhatsApp")
    wa_4h_number = st.text_input("Enter WhatsApp Number or Group Link for 4-Hourly Report")

    if st.button("Send 4-Hourly Report"):
        if wa_4h_number.startswith("http"):
            st.markdown(f"[Open WhatsApp Group]({wa_4h_number})", unsafe_allow_html=True)
        else:
            wa_4h_link = f"https://wa.me/{wa_4h_number}?text={urllib.parse.quote(f'```{template_4h}```')}"
            st.markdown(f"[Open WhatsApp Private]({wa_4h_link})", unsafe_allow_html=True)
else:
    st.write("Not enough data yet for this 4-hour block.")