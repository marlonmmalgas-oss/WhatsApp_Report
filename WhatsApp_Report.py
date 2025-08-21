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

# Initialize default values if not present
defaults = {
    "done_load": 0, "done_disch": 0,
    "done_restow_load": 0, "done_restow_disch": 0,
    "done_hatch_open": 0, "done_hatch_close": 0,
    "last_hour": None, "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "planned_load": 687, "planned_disch": 38,
    "planned_restow_load": 13, "planned_restow_disch": 13,
    "opening_load": 0, "opening_disch": 0,
    "opening_restow_load": 0, "opening_restow_disch": 0,
    "hourly_entries": []
}
for key, val in defaults.items():
    cumulative.setdefault(key, val)

# --- South African date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Plan Totals & Opening Balance (internal only) ---
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
hours_list = []
for h in range(24):
    start_hour = h
    end_hour = (h + 1) % 24
    hours_list.append(f"{str(start_hour).zfill(2)}h00 - {str(end_hour).zfill(2)}h00")

default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves Input ---
st.header(f"Hourly Moves Input ({hourly_time})")

# FWD
st.subheader("FWD Moves")
fwd_load = st.number_input("Load", min_value=0, value=0, key="fwd_load")
fwd_disch = st.number_input("Discharge", min_value=0, value=0, key="fwd_disch")
fwd_restow_load = st.number_input("Restow Load", min_value=0, value=0, key="fwd_restow_load")
fwd_restow_disch = st.number_input("Restow Discharge", min_value=0, value=0, key="fwd_restow_disch")

# MID
st.subheader("MID Moves")
mid_load = st.number_input("Load", min_value=0, value=0, key="mid_load")
mid_disch = st.number_input("Discharge", min_value=0, value=0, key="mid_disch")
mid_restow_load = st.number_input("Restow Load", min_value=0, value=0, key="mid_restow_load")
mid_restow_disch = st.number_input("Restow Discharge", min_value=0, value=0, key="mid_restow_disch")

# AFT
st.subheader("AFT Moves")
aft_load = st.number_input("Load", min_value=0, value=0, key="aft_load")
aft_disch = st.number_input("Discharge", min_value=0, value=0, key="aft_disch")
aft_restow_load = st.number_input("Restow Load", min_value=0, value=0, key="aft_restow_load")
aft_restow_disch = st.number_input("Restow Discharge", min_value=0, value=0, key="aft_restow_disch")

# POOP
st.subheader("POOP Moves")
poop_load = st.number_input("Load", min_value=0, value=0, key="poop_load")
poop_disch = st.number_input("Discharge", min_value=0, value=0, key="poop_disch")
poop_restow_load = st.number_input("Restow Load", min_value=0, value=0, key="poop_restow_load")
poop_restow_disch = st.number_input("Restow Discharge", min_value=0, value=0, key="poop_restow_disch")

# Hatch Moves
st.subheader("Hatch Moves")
hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- WhatsApp Section ---
st.header("Send to WhatsApp")
wa_choice = st.radio("Send via", ["Private Number", "Group Link"])
if wa_choice == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
else:
    whatsapp_group = st.text_input("Enter WhatsApp Group Invite Link")
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

    # Save hourly entry for 4-hour calculation
    cumulative.setdefault("hourly_entries", []).append({
        "hour": hourly_time,
        "fwd_load": fwd_load, "mid_load": mid_load, "aft_load": aft_load, "poop_load": poop_load,
        "fwd_disch": fwd_disch, "mid_disch": mid_disch, "aft_disch": aft_disch, "poop_disch": poop_disch,
        "fwd_restow_load": fwd_restow_load, "mid_restow_load": mid_restow_load,
        "aft_restow_load": aft_restow_load, "poop_restow_load": poop_restow_load,
        "fwd_restow_disch": fwd_restow_disch, "mid_restow_disch": mid_restow_disch,
        "aft_restow_disch": aft_restow_disch, "poop_restow_disch": poop_restow_disch,
        "hatch_fwd_open": hatch_fwd_open, "hatch_fwd_close": hatch_fwd_close,
        "hatch_mid_open": hatch_mid_open, "hatch_mid_close": hatch_mid_close,
        "hatch_aft_open": hatch_aft_open, "hatch_aft_close": hatch_aft_close
    })

    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Calculate remaining totals
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # --- Hourly WhatsApp Template ---
    hourly_template = f"""\
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

    st.subheader("Hourly WhatsApp Template")
    st.code(hourly_template)

    # --- Send via WhatsApp ---
    if wa_choice == "Private Number" and whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(hourly_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif wa_choice == "Group Link" and whatsapp_group:
        wa_link = f"{whatsapp_group}?text={urllib.parse.quote(hourly_template)}"
        st.markdown(f"[Open WhatsApp Group]({wa_link})", unsafe_allow_html=True)