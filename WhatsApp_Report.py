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

# Initialize default structure
default_data = {
    "done_load": 0, "done_disch": 0, "done_restow_load": 0, "done_restow_disch": 0,
    "done_hatch_open": 0, "done_hatch_close": 0, "last_hour": None,
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "planned_load": 687, "planned_disch": 38,
    "planned_restow_load": 13, "planned_restow_disch": 13,
    "opening_load": 0, "opening_disch": 0,
    "opening_restow_load": 0, "opening_restow_disch": 0,
    "hourly_entries": [],
    "four_hour_entries": []
}

# Merge defaults if missing
for key, value in default_data.items():
    cumulative.setdefault(key, value)

# --- Current South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- First & Last Lift ---
st.header("Lift Times")
first_lift = st.text_input("First Lift Time (HHhMM)", value="06h00")
last_lift = st.text_input("Last Lift Time (HHhMM)", value="10h00")

# --- Hourly Time Dropdown ---
st.header("Hourly Time")
hours_list = []
for h in range(24):
    start_hour = h
    end_hour = (h + 1) % 24
    hours_list.append(f"{str(start_hour).zfill(2)}h00 - {str(end_hour).zfill(2)}h00")

if cumulative.get("last_hour") and cumulative["last_hour"] in hours_list:
    default_hour = cumulative["last_hour"]
else:
    default_hour = "06h00 - 07h00"

hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves Inputs ---
st.header(f"Hourly Moves Input ({hourly_time})")

# Grouping by FWD, MID, AFT, POOP
st.subheader("Crane Moves")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**FWD**")
    fwd_load = st.number_input("Load", min_value=0, value=0, key="hourly_fwd_load")
    fwd_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_fwd_disch")
    st.markdown("**MID**")
    mid_load = st.number_input("Load", min_value=0, value=0, key="hourly_mid_load")
    mid_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_mid_disch")
with col2:
    st.markdown("**AFT**")
    aft_load = st.number_input("Load", min_value=0, value=0, key="hourly_aft_load")
    aft_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_aft_disch")
    st.markdown("**POOP**")
    poop_load = st.number_input("Load", min_value=0, value=0, key="hourly_poop_load")
    poop_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_poop_disch")

# --- Restows ---
st.subheader("Restows")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**FWD**")
    fwd_restow_load = st.number_input("Load", min_value=0, value=0, key="hourly_fwd_restow_load")
    fwd_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_fwd_restow_disch")
    st.markdown("**MID**")
    mid_restow_load = st.number_input("Load", min_value=0, value=0, key="hourly_mid_restow_load")
    mid_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_mid_restow_disch")
with col2:
    st.markdown("**AFT**")
    aft_restow_load = st.number_input("Load", min_value=0, value=0, key="hourly_aft_restow_load")
    aft_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_aft_restow_disch")
    st.markdown("**POOP**")
    poop_restow_load = st.number_input("Load", min_value=0, value=0, key="hourly_poop_restow_load")
    poop_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="hourly_poop_restow_disch")

# --- Hatch Moves ---
st.subheader("Hatch Moves")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**FWD**")
    hatch_fwd_open = st.number_input("Open", min_value=0, value=0, key="hourly_hatch_fwd_open")
    hatch_fwd_close = st.number_input("Close", min_value=0, value=0, key="hourly_hatch_fwd_close")
with col2:
    st.markdown("**MID**")
    hatch_mid_open = st.number_input("Open", min_value=0, value=0, key="hourly_hatch_mid_open")
    hatch_mid_close = st.number_input("Close", min_value=0, value=0, key="hourly_hatch_mid_close")
with col3:
    st.markdown("**AFT**")
    hatch_aft_open = st.number_input("Open", min_value=0, value=0, key="hourly_hatch_aft_open")
    hatch_aft_close = st.number_input("Close", min_value=0, value=0, key="hourly_hatch_aft_close")

# --- WhatsApp Options ---
st.header("WhatsApp Options")
wa_choice = st.selectbox("Send to:", ["Private Number", "Group Link"])
whatsapp_number = st.text_input("WhatsApp Number (with country code, e.g., 27761234567)")
whatsapp_group = st.text_input("WhatsApp Group Link (if Group)")

# --- Submit Hourly ---
if st.button("Submit Hourly"):
    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save hourly entry
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

    # Save persistent editable fields
    cumulative.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date
    })
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    st.success("Hourly data saved!")

# --- Generate Hourly Template for WhatsApp ---
def generate_hourly_template():
    remaining_load = cumulative["planned_load"] - cumulative["done_load"] - cumulative["opening_load"]
    remaining_disch = cumulative["planned_disch"] - cumulative["done_disch"] - cumulative["opening_disch"]
    remaining_restow_load = cumulative["planned_restow_load"] - cumulative["done_restow_load"] - cumulative["opening_restow_load"]
    remaining_restow_disch = cumulative["planned_restow_disch"] - cumulative["done_restow_disch"] - cumulative["opening_restow_disch"]

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
Plan       {cumulative['planned_load']:>5}      {cumulative['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {cumulative['planned_restow_load']:>5}      {cumulative['planned_restow_disch']:>5}
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
    return template

# --- Display Hourly Template ---
st.subheader("Hourly Template Preview")
hourly_template = generate_hourly_template()
st.code(hourly_template)

# --- Send to WhatsApp ---
if st.button("Send Hourly Template to WhatsApp"):
    wa_text = urllib.parse.quote(f"```{hourly_template}```")
    if wa_choice == "Private Number" and whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={wa_text}"
        st.markdown(f"[Open WhatsApp Private]({wa_link})", unsafe_allow_html=True)
    elif wa_choice == "Group Link" and whatsapp_group:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group})", unsafe_allow_html=True)

# ---------------- 4-HOURLY REPORT ----------------
st.header("4-Hourly Report")

# --- 4-Hourly Dropdown ---
four_hour_options = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
four_hour_time = st.selectbox("Select 4-Hour Period", four_hour_options)

# --- Calculate 4-hour totals from hourly entries ---
def calculate_four_hour_totals(period):
    # Filter last 4 hours based on selection
    fwd_load = mid_load = aft_load = poop_load = 0
    fwd_disch = mid_disch = aft_disch = poop_disch = 0
    fwd_restow_load = mid_restow_load = aft_restow_load = poop_restow_load = 0
    fwd_restow_disch = mid_restow_disch = aft_restow_disch = poop_restow_disch = 0
    hatch_fwd_open = hatch_mid_open = hatch_aft_open = 0
    hatch_fwd_close = hatch_mid_close = hatch_aft_close = 0

    for entry in cumulative.get("hourly_entries", []):
        if entry["hour"] in four_hour_time:
            fwd_load += entry["fwd_load"]
            mid_load += entry["mid_load"]
            aft_load += entry["aft_load"]
            poop_load += entry["poop_load"]
            fwd_disch += entry["fwd_disch"]
            mid_disch += entry["mid_disch"]
            aft_disch += entry["aft_disch"]
            poop_disch += entry["poop_disch"]

            fwd_restow_load += entry["fwd_restow_load"]
            mid_restow_load += entry["mid_restow_load"]
            aft_restow_load += entry["aft_restow_load"]
            poop_restow_load += entry["poop_restow_load"]

            fwd_restow_disch += entry["fwd_restow_disch"]
            mid_restow_disch += entry["mid_restow_disch"]
            aft_restow_disch += entry["aft_restow_disch"]
            poop_restow_disch += entry["poop_restow_disch"]

            hatch_fwd_open += entry["hatch_fwd_open"]
            hatch_mid_open += entry["hatch_mid_open"]
            hatch_aft_open += entry["hatch_aft_open"]
            hatch_fwd_close += entry["hatch_fwd_close"]
            hatch_mid_close += entry["hatch_mid_close"]
            hatch_aft_close += entry["hatch_aft_close"]

    return {
        "fwd_load": fwd_load, "mid_load": mid_load, "aft_load": aft_load, "poop_load": poop_load,
        "fwd_disch": fwd_disch, "mid_disch": mid_disch, "aft_disch": aft_disch, "poop_disch": poop_disch,
        "fwd_restow_load": fwd_restow_load, "mid_restow_load": mid_restow_load,
        "aft_restow_load": aft_restow_load, "poop_restow_load": poop_restow_load,
        "fwd_restow_disch": fwd_restow_disch, "mid_restow_disch": mid_restow_disch,
        "aft_restow_disch": aft_restow_disch, "poop_restow_disch": poop_restow_disch,
        "hatch_fwd_open": hatch_fwd_open, "hatch_mid_open": hatch_mid_open, "hatch_aft_open": hatch_aft_open,
        "hatch_fwd_close": hatch_fwd_close, "hatch_mid_close": hatch_mid_close, "hatch_aft_close": hatch_aft_close
    }

four_hour_totals = calculate_four_hour_totals(four_hour_time)

# --- 4-Hourly Template ---
st.subheader("4-Hourly Template Preview")
template_4h = f"""\
{vessel_name}
Berthed {berthed_date}

4-Hour Period: {four_hour_time}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {four_hour_totals['fwd_load']:>5}     {four_hour_totals['fwd_disch']:>5}
MID        {four_hour_totals['mid_load']:>5}     {four_hour_totals['mid_disch']:>5}
AFT        {four_hour_totals['aft_load']:>5}     {four_hour_totals['aft_disch']:>5}
POOP       {four_hour_totals['poop_load']:>5}     {four_hour_totals['poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {four_hour_totals['fwd_restow_load']:>5}     {four_hour_totals['fwd_restow_disch']:>5}
MID        {four_hour_totals['mid_restow_load']:>5}     {four_hour_totals['mid_restow_disch']:>5}
AFT        {four_hour_totals['aft_restow_load']:>5}     {four_hour_totals['aft_restow_disch']:>5}
POOP       {four_hour_totals['poop_restow_load']:>5}     {four_hour_totals['poop_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {four_hour_totals['hatch_fwd_open']:>5}      {four_hour_totals['hatch_fwd_close']:>5}
MID        {four_hour_totals['hatch_mid_open']:>5}      {four_hour_totals['hatch_mid_close']:>5}
AFT        {four_hour_totals['hatch_aft_open']:>5}      {four_hour_totals['hatch_aft_close']:>5}
_________________________
"""

st.code(template_4h)

# --- Send 4-Hourly WhatsApp ---
st.subheader("Send 4-Hourly Template to WhatsApp")
wa_choice_4h = st.selectbox("Send 4-Hourly to:", ["Private Number", "Group Link"], key="wa4h_choice")
whatsapp_number_4h = st.text_input("WhatsApp Number (with country code)", key="wa4h_number")
whatsapp_group_4h = st.text_input("WhatsApp Group Link (if Group)", key="wa4h_group")

if st.button("Send 4-Hourly Template"):
    wa_text_4h = urllib.parse.quote(f"```{template_4h}```")
    if wa_choice_4h == "Private Number" and whatsapp_number_4h:
        wa_link_4h = f"https://wa.me/{whatsapp_number_4h}?text={wa_text_4h}"
        st.markdown(f"[Open WhatsApp Private]({wa_link_4h})", unsafe_allow_html=True)
    elif wa_choice_4h == "Group Link" and whatsapp_group_4h:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_4h})", unsafe_allow_html=True)