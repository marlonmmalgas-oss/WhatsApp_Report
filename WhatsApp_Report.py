import streamlit as st
import json
import os
from datetime import datetime
import pytz
import urllib.parse

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

# --- Default values ---
defaults = {
    "done_load": 0, "done_disch": 0,
    "done_restow_load": 0, "done_restow_disch": 0,
    "done_hatch_open": 0, "done_hatch_close": 0,
    "last_hour": None, "last_4h_slot": None,
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "first_lift": "18h25", "last_lift": "10h31",
    "planned_load": 687, "planned_disch": 38,
    "planned_restow_load": 13, "planned_restow_disch": 13,
    "opening_load": 0, "opening_disch": 0,
    "opening_restow_load": 0, "opening_restow_disch": 0,
    "last4_fwd_load": [], "last4_mid_load": [], "last4_aft_load": [], "last4_poop_load": [],
    "last4_fwd_disch": [], "last4_mid_disch": [], "last4_aft_disch": [], "last4_poop_disch": [],
    "last4_fwd_restow_load": [], "last4_mid_restow_load": [], "last4_aft_restow_load": [], "last4_poop_restow_load": [],
    "last4_fwd_restow_disch": [], "last4_mid_restow_disch": [], "last4_aft_restow_disch": [], "last4_poop_restow_disch": []
}

for key, value in defaults.items():
    if key not in cumulative:
        cumulative[key] = value

# --- Timezone ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift Time", cumulative["first_lift"])
last_lift = st.text_input("Last Lift Time", cumulative["last_lift"])

# --- Plan Totals & Opening Balance (internal) ---
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
default_hour = cumulative.get("last_hour") or "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves ---
st.header(f"Hourly Moves Input ({hourly_time})")

st.subheader("FWD Crane")
fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="fwd_load")
fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="fwd_disch")

st.subheader("MID Crane")
mid_load = st.number_input("MID Load", min_value=0, value=0, key="mid_load")
mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="mid_disch")

st.subheader("AFT Crane")
aft_load = st.number_input("AFT Load", min_value=0, value=0, key="aft_load")
aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="aft_disch")

st.subheader("POOP Crane")
poop_load = st.number_input("POOP Load", min_value=0, value=0, key="poop_load")
poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="poop_disch")

st.subheader("Restows")
fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

st.subheader("Hatch Moves")
hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# --- WhatsApp Options ---
st.header("Send to WhatsApp")
wa_option = st.radio("Choose WhatsApp Destination:", ["Private Number", "Group Link"])
if wa_option == "Private Number":
    whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
    wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote('template')}" if whatsapp_number else ""
else:
    group_link = st.text_input("Enter WhatsApp Group Invite Link")
    wa_link = f"{group_link}?text={urllib.parse.quote('template')}" if group_link else ""

# --- Submit Button ---
if st.button("Update & Show Template"):
    # Update cumulative
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    cumulative.update({
        "vessel_name": vessel_name, "berthed_date": berthed_date,
        "first_lift": first_lift, "last_lift": last_lift,
        "planned_load": planned_load, "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load, "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load, "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load, "opening_restow_disch": opening_restow_disch
    })

    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Calculate remaining
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # --- Template ---
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

    st.code(template, language="text")

    if wa_link:
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)