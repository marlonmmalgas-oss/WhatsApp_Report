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
    except json.decoder.JSONDecodeError:
        cumulative = {}
else:
    cumulative = {}

# --- Initialize if empty ---
if not cumulative:
    cumulative = {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "hourly_records": [],
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
    }

# --- South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Plan Totals & Opening Balance ---
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
hourly_time = st.selectbox("Select Hourly Time", hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves Input ---
st.header(f"Hourly Moves Input ({hourly_time})")
st.subheader("FWD / MID / AFT / POOP Crane Moves")
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

# --- WhatsApp Input ---
st.header("Send to WhatsApp")
wa_number = st.text_input("Enter WhatsApp Number or Group Link")

# --- Submit Hourly Moves ---
if st.button("Submit Hourly Moves"):
    # Save hourly record
    record = {
        "hour": hourly_time,
        "fwd_load": fwd_load, "mid_load": mid_load, "aft_load": aft_load, "poop_load": poop_load,
        "fwd_disch": fwd_disch, "mid_disch": mid_disch, "aft_disch": aft_disch, "poop_disch": poop_disch,
        "fwd_restow_load": fwd_restow_load, "mid_restow_load": mid_restow_load, "aft_restow_load": aft_restow_load, "poop_restow_load": poop_restow_load,
        "fwd_restow_disch": fwd_restow_disch, "mid_restow_disch": mid_restow_disch, "aft_restow_disch": aft_restow_disch, "poop_restow_disch": poop_restow_disch,
        "hatch_fwd_open": hatch_fwd_open, "hatch_mid_open": hatch_mid_open, "hatch_aft_open": hatch_aft_open,
        "hatch_fwd_close": hatch_fwd_close, "hatch_mid_close": hatch_mid_close, "hatch_aft_close": hatch_aft_close
    }
    cumulative["hourly_records"].append(record)

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

    # --- Hourly WhatsApp Template ---
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
           Load   Disch
FWD        {fwd_load:>5}     {fwd_disch:>5}
MID        {mid_load:>5}     {mid_disch:>5}
AFT        {aft_load:>5}     {aft_disch:>5}
POOP       {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Disch
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

    st.code(template)

    # --- Send to WhatsApp ---
    if wa_number:
        wa_template = f"```{template}```"
        wa_link = f"https://wa.me/{wa_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)

# --- 4-Hourly Report Section ---
st.header("4-Hourly Report")
four_hour_options = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
four_hour_period = st.selectbox("Select 4-Hour Period", four_hour_options)

# --- Calculate 4-Hour Totals ---
def calculate_4hour_totals(hour_start_idx):
    last4 = cumulative["hourly_records"][hour_start_idx:hour_start_idx+4]
    total = {
        "fwd_load": sum(r["fwd_load"] for r in last4),
        "mid_load": sum(r["mid_load"] for r in last4),
        "aft_load": sum(r["aft_load"] for r in last4),
        "poop_load": sum(r["poop_load"] for r in last4),
        "fwd_disch": sum(r["fwd_disch"] for r in last4),
        "mid_disch": sum(r["mid_disch"] for r in last4),
        "aft_disch": sum(r["aft_disch"] for r in last4),
        "poop_disch": sum(r["poop_disch"] for r in last4),
        "fwd_restow_load": sum(r["fwd_restow_load"] for r in last4),
        "mid_restow_load": sum(r["mid_restow_load"] for r in last4),
        "aft_restow_load": sum(r["aft_restow_load"] for r in last4),
        "poop_restow_load": sum(r["poop_restow_load"] for r in last4),
        "fwd_restow_disch": sum(r["fwd_restow_disch"] for r in last4),
        "mid_restow_disch": sum(r["mid_restow_disch"] for r in last4),
        "aft_restow_disch": sum(r["aft_restow_disch"] for r in last4),
        "poop_restow_disch": sum(r["poop_restow_disch"] for r in last4),
        "hatch_fwd_open": sum(r["hatch_fwd_open"] for r in last4),
        "hatch_mid_open": sum(r["hatch_mid_open"] for r in last4),
        "hatch_aft_open": sum(r["hatch_aft_open"] for r in last4),
        "hatch_fwd_close": sum(r["hatch_fwd_close"] for r in last4),
        "hatch_mid_close": sum(r["hatch_mid_close"] for r in last4),
        "hatch_aft_close": sum(r["hatch_aft_close"] for r in last4),
    }
    return total

# Map 4-hour periods to record indexes (simplified)
period_idx_map = {"06h00 - 10h00":0, "10h00 - 14h00":4, "14h00 - 18h00":8, "18h00 - 22h00":12, "22h00 - 02h00":16, "02h00 - 06h00":20}
start_idx = period_idx_map.get(four_hour_period, 0)
four_hour_totals = calculate_4hour_totals(start_idx) if len(cumulative["hourly_records"]) >= start_idx+4 else {}

# --- 4-Hourly Template ---
if four_hour_totals:
    template_4hour = f"""\
{vessel_name}
Berthed {berthed_date}

{today_date}
{four_hour_period}
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Disch
FWD        {four_hour_totals['fwd_load']:>5}     {four_hour_totals['fwd_disch']:>5}
MID        {four_hour_totals['mid_load']:>5}     {four_hour_totals['mid_disch']:>5}
AFT        {four_hour_totals['aft_load']:>5}     {four_hour_totals['aft_disch']:>5}
POOP       {four_hour_totals['poop_load']:>5}     {four_hour_totals['poop_disch']:>5}
_________________________
*Restows*
           Load   Disch
FWD        {four_hour_totals['fwd_restow_load']:>5}     {four_hour_totals['fwd_restow_disch']:>5}
MID        {four_hour_totals['mid_restow_load']:>5}     {four_hour_totals['mid_restow_disch']:>5}
AFT        {four_hour_totals['aft_restow_load']:>5}     {four_hour_totals['aft_restow_disch']:>5}
POOP       {four_hour_totals['poop_restow_load']:>5}     {four_hour_totals['poop_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {four_hour_totals['hatch_fwd_open']:>5}     {four_hour_totals['hatch_fwd_close']:>5}
MID        {four_hour_totals['hatch_mid_open']:>5}     {four_hour_totals['hatch_mid_close']:>5}
AFT        {four_hour_totals['hatch_aft_open']:>5}     {four_hour_totals['hatch_aft_close']:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""
    st.code(template_4hour)

    # --- Send 4-Hour WhatsApp ---
    wa_number_4h = st.text_input("Enter WhatsApp Number or Group Link for 4-Hourly", key="wa_4h")
    if st.button("Send 4-Hourly Report"):
        if wa_number_4h:
            wa_template_4h = f"```{template_4hour}```"
            wa_link_4h = f"https://wa.me/{wa_number_4h}?text={urllib.parse.quote(wa_template_4h)}"
            st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)