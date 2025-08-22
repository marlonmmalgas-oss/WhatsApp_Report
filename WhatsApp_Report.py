import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

# --- File to store cumulative and 4-hourly totals ---
SAVE_FILE = "vessel_report.json"

# --- Load or initialize data ---
if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as f:
            S = json.load(f)
    except json.JSONDecodeError:
        S = {}
else:
    S = {}

# --- Default values ---
defaults = {
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10h55",
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
    "last_hour": None,
    # 4-hourly totals
    "four_load_fwd":0, "four_load_mid":0, "four_load_aft":0, "four_load_poop":0,
    "four_disch_fwd":0, "four_disch_mid":0, "four_disch_aft":0, "four_disch_poop":0,
    "four_restow_load_fwd":0, "four_restow_load_mid":0, "four_restow_load_aft":0, "four_restow_load_poop":0,
    "four_restow_disch_fwd":0, "four_restow_disch_mid":0, "four_restow_disch_aft":0, "four_restow_disch_poop":0,
    "four_hatch_open_fwd":0, "four_hatch_open_mid":0, "four_hatch_open_aft":0,
    "four_hatch_close_fwd":0, "four_hatch_close_mid":0, "four_hatch_close_aft":0,
    "idle_entries": []
}

# Merge defaults with saved data
for k,v in defaults.items():
    if k not in S:
        S[k] = v

# --- Time setup ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

# --- Streamlit Layout ---
st.title("Vessel Hourly Moves Tracker")
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", value=S["vessel_name"])
berthed_date = st.text_input("Berthed Date", value=S["berthed_date"])
# --- Collapsible Plan Totals & Opening Balance ---
with st.expander("Plan Totals & Opening Balance (Internal)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        planned_load = st.number_input("Planned Load", value=S["planned_load"])
        planned_disch = st.number_input("Planned Discharge", value=S["planned_disch"])
        planned_restow_load = st.number_input("Planned Restow Load", value=S["planned_restow_load"])
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=S["planned_restow_disch"])
    with col2:
        opening_load = st.number_input("Opening Load", value=S["opening_load"])
        opening_disch = st.number_input("Opening Discharge", value=S["opening_disch"])
        opening_restow_load = st.number_input("Opening Restow Load", value=S["opening_restow_load"])
        opening_restow_disch = st.number_input("Opening Restow Discharge", value=S["opening_restow_disch"])

# --- Hourly Time Selection ---
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = S["last_hour"] if S.get("last_hour") in hours_list else "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Collapsible Hourly Inputs ---
with st.expander(f"Edit Hourly Inputs ({hourly_time})", expanded=True):
    # Crane Moves
    st.markdown("**Crane Moves**")
    col_fwd = st.columns(2)
    hl_fwd = col_fwd[0].number_input("FWD Load", value=0, min_value=0)
    hd_fwd = col_fwd[1].number_input("FWD Discharge", value=0, min_value=0)

    col_mid = st.columns(2)
    hl_mid = col_mid[0].number_input("MID Load", value=0, min_value=0)
    hd_mid = col_mid[1].number_input("MID Discharge", value=0, min_value=0)

    col_aft = st.columns(2)
    hl_aft = col_aft[0].number_input("AFT Load", value=0, min_value=0)
    hd_aft = col_aft[1].number_input("AFT Discharge", value=0, min_value=0)

    col_poop = st.columns(2)
    hl_poop = col_poop[0].number_input("POOP Load", value=0, min_value=0)
    hd_poop = col_poop[1].number_input("POOP Discharge", value=0, min_value=0)

    # Restows
    st.markdown("**Restows**")
    col_fwd = st.columns(2)
    rll_fwd = col_fwd[0].number_input("FWD Restow Load", value=0, min_value=0)
    rld_fwd = col_fwd[1].number_input("FWD Restow Discharge", value=0, min_value=0)

    col_mid = st.columns(2)
    rll_mid = col_mid[0].number_input("MID Restow Load", value=0, min_value=0)
    rld_mid = col_mid[1].number_input("MID Restow Discharge", value=0, min_value=0)

    col_aft = st.columns(2)
    rll_aft = col_aft[0].number_input("AFT Restow Load", value=0, min_value=0)
    rld_aft = col_aft[1].number_input("AFT Restow Discharge", value=0, min_value=0)

    col_poop = st.columns(2)
    rll_poop = col_poop[0].number_input("POOP Restow Load", value=0, min_value=0)
    rld_poop = col_poop[1].number_input("POOP Restow Discharge", value=0, min_value=0)

    # Hatch Moves
    st.markdown("**Hatch Moves**")
    col_fwd = st.columns(2)
    ho_fwd = col_fwd[0].number_input("FWD Hatch Open", value=0, min_value=0)
    hc_fwd = col_fwd[1].number_input("FWD Hatch Close", value=0, min_value=0)

    col_mid = st.columns(2)
    ho_mid = col_mid[0].number_input("MID Hatch Open", value=0, min_value=0)
    hc_mid = col_mid[1].number_input("MID Hatch Close", value=0, min_value=0)

    col_aft = st.columns(2)
    ho_aft = col_aft[0].number_input("AFT Hatch Open", value=0, min_value=0)
    hc_aft = col_aft[1].number_input("AFT Hatch Close", value=0, min_value=0)
    # --- 4-Hourly Block Selection ---
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
four_hour_block = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

# --- Collapsible 4-Hourly Inputs ---
with st.expander(f"Edit 4-Hourly Inputs ({four_hour_block})", expanded=False):
    st.markdown("**Crane Moves (4-Hourly)**")
    col_fwd = st.columns(2)
    four_load_fwd = col_fwd[0].number_input("FWD Load", value=S["four_load_fwd"], min_value=0)
    four_disch_fwd = col_fwd[1].number_input("FWD Discharge", value=S["four_disch_fwd"], min_value=0)

    col_mid = st.columns(2)
    four_load_mid = col_mid[0].number_input("MID Load", value=S["four_load_mid"], min_value=0)
    four_disch_mid = col_mid[1].number_input("MID Discharge", value=S["four_disch_mid"], min_value=0)

    col_aft = st.columns(2)
    four_load_aft = col_aft[0].number_input("AFT Load", value=S["four_load_aft"], min_value=0)
    four_disch_aft = col_aft[1].number_input("AFT Discharge", value=S["four_disch_aft"], min_value=0)

    col_poop = st.columns(2)
    four_load_poop = col_poop[0].number_input("POOP Load", value=S["four_load_poop"], min_value=0)
    four_disch_poop = col_poop[1].number_input("POOP Discharge", value=S["four_disch_poop"], min_value=0)

    st.markdown("**Restows (4-Hourly)**")
    col_fwd = st.columns(2)
    four_restow_load_fwd = col_fwd[0].number_input("FWD Restow Load", value=S["four_restow_load_fwd"], min_value=0)
    four_restow_disch_fwd = col_fwd[1].number_input("FWD Restow Discharge", value=S["four_restow_disch_fwd"], min_value=0)

    col_mid = st.columns(2)
    four_restow_load_mid = col_mid[0].number_input("MID Restow Load", value=S["four_restow_load_mid"], min_value=0)
    four_restow_disch_mid = col_mid[1].number_input("MID Restow Discharge", value=S["four_restow_disch_mid"], min_value=0)

    col_aft = st.columns(2)
    four_restow_load_aft = col_aft[0].number_input("AFT Restow Load", value=S["four_restow_load_aft"], min_value=0)
    four_restow_disch_aft = col_aft[1].number_input("AFT Restow Discharge", value=S["four_restow_disch_aft"], min_value=0)

    col_poop = st.columns(2)
    four_restow_load_poop = col_poop[0].number_input("POOP Restow Load", value=S["four_restow_load_poop"], min_value=0)
    four_restow_disch_poop = col_poop[1].number_input("POOP Restow Discharge", value=S["four_restow_disch_poop"], min_value=0)

    st.markdown("**Hatch Moves (4-Hourly)**")
    col_fwd = st.columns(2)
    four_hatch_open_fwd = col_fwd[0].number_input("FWD Hatch Open", value=S["four_hatch_open_fwd"], min_value=0)
    four_hatch_close_fwd = col_fwd[1].number_input("FWD Hatch Close", value=S["four_hatch_close_fwd"], min_value=0)

    col_mid = st.columns(2)
    four_hatch_open_mid = col_mid[0].number_input("MID Hatch Open", value=S["four_hatch_open_mid"], min_value=0)
    four_hatch_close_mid = col_mid[1].number_input("MID Hatch Close", value=S["four_hatch_close_mid"], min_value=0)

    col_aft = st.columns(2)
    four_hatch_open_aft = col_aft[0].number_input("AFT Hatch Open", value=S["four_hatch_open_aft"], min_value=0)
    four_hatch_close_aft = col_aft[1].number_input("AFT Hatch Close", value=S["four_hatch_close_aft"], min_value=0)

    # --- Reset 4-Hourly Button ---
    if st.button("Reset 4-Hourly Counts"):
        S["four_load_fwd"] = S["four_load_mid"] = S["four_load_aft"] = S["four_load_poop"] = 0
        S["four_disch_fwd"] = S["four_disch_mid"] = S["four_disch_aft"] = S["four_disch_poop"] = 0
        S["four_restow_load_fwd"] = S["four_restow_load_mid"] = S["four_restow_load_aft"] = S["four_restow_load_poop"] = 0
        S["four_restow_disch_fwd"] = S["four_restow_disch_mid"] = S["four_restow_disch_aft"] = S["four_restow_disch_poop"] = 0
        S["four_hatch_open_fwd"] = S["four_hatch_open_mid"] = S["four_hatch_open_aft"] = 0
        S["four_hatch_close_fwd"] = S["four_hatch_close_mid"] = S["four_hatch_close_aft"] = 0
        st.success("4-Hourly counts reset.")

# --- Idle Section ---
with st.expander("Idle / Delays Section", expanded=False):
    max_idle_entries = 10
    idle_entries = []
    delay_options = [
        "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations", 
        "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
        "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
        "Crane break down/ boom limit", "Crane break down", "Vessel listing",
        "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
    ]
    for i in range(max_idle_entries):
        with st.expander(f"Idle Entry {i+1}", expanded=False):
            crane = st.selectbox(f"Crane for Idle {i+1}", ["FWD", "MID", "AFT", "POOP"])
            start_time = st.time_input(f"Start Time {i+1}")
            end_time = st.time_input(f"End Time {i+1}")
            delay_type = st.selectbox(f"Select Delay {i+1}", options=delay_options)
            custom_delay = st.text_input(f"Custom Delay (Optional) {i+1}")
            idle_entries.append({
                "crane": crane,
                "start": start_time.strftime("%H:%M"),
                "end": end_time.strftime("%H:%M"),
                "delay_type": custom_delay if custom_delay else delay_type
            })

S["idle_entries"] = idle_entries
# --- Update cumulative totals for hourly and 4-hourly ---
total_load = fwd_load + mid_load + aft_load + poop_load
total_disch = fwd_disch + mid_disch + aft_disch + poop_disch
total_restow_load = fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
total_restow_disch = fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
total_hatch_open = hatch_fwd_open + hatch_mid_open + hatch_aft_open
total_hatch_close = hatch_fwd_close + hatch_mid_close + hatch_aft_close

# --- 4-Hourly totals add from hourly cumulative ---
S["four_load_total"] = total_load + S.get("four_load_total", 0)
S["four_disch_total"] = total_disch + S.get("four_disch_total", 0)
S["four_restow_load_total"] = total_restow_load + S.get("four_restow_load_total", 0)
S["four_restow_disch_total"] = total_restow_disch + S.get("four_restow_disch_total", 0)
S["four_hatch_open_total"] = total_hatch_open + S.get("four_hatch_open_total", 0)
S["four_hatch_close_total"] = total_hatch_close + S.get("four_hatch_close_total", 0)

# --- WhatsApp Template ---
wa_template_hourly = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
Hourly: {hourly_time}
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
Remain     {planned_load - cumulative['done_load']:>5}      {planned_disch - cumulative['done_disch']:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {planned_restow_load - cumulative['done_restow_load']:>5}      {planned_restow_disch - cumulative['done_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID        {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT        {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Idle*
"""

# Add idle entries to template
for idle in idle_entries:
    wa_template_hourly += f"{idle['crane']} {idle['start']} - {idle['end']} {idle['delay_type']}\n"

# --- 4-Hourly WhatsApp Template ---
wa_template_4hourly = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_block}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {S['four_load_fwd']:>5}     {S['four_disch_fwd']:>5}
MID        {S['four_load_mid']:>5}     {S['four_disch_mid']:>5}
AFT        {S['four_load_aft']:>5}     {S['four_disch_aft']:>5}
POOP       {S['four_load_poop']:>5}     {S['four_disch_poop']:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {S['four_restow_load_fwd']:>5}     {S['four_restow_disch_fwd']:>5}
MID        {S['four_restow_load_mid']:>5}     {S['four_restow_disch_mid']:>5}
AFT        {S['four_restow_load_aft']:>5}     {S['four_restow_disch_aft']:>5}
POOP       {S['four_restow_load_poop']:>5}     {S['four_restow_disch_poop']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {planned_load - cumulative['done_load']:>5}      {planned_disch - cumulative['done_disch']:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {planned_restow_load - cumulative['done_restow_load']:>5}      {planned_restow_disch - cumulative['done_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {S['four_hatch_open_fwd']:>5}      {S['four_hatch_close_fwd']:>5}
MID        {S['four_hatch_open_mid']:>5}      {S['four_hatch_close_mid']:>5}
AFT        {S['four_hatch_open_aft']:>5}      {S['four_hatch_close_aft']:>5}
_________________________
*Idle*
"""

for idle in idle_entries:
    wa_template_4hourly += f"{idle['crane']} {idle['start']} - {idle['end']} {idle['delay_type']}\n"

# --- Show templates in monospace ---
st.subheader("Hourly Template")
st.code(wa_template_hourly)

st.subheader("4-Hourly Template")
st.code(wa_template_4hourly)

# --- WhatsApp Links ---
wa_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
if wa_number:
    wa_link_hourly = f"https://wa.me/{wa_number}?text={urllib.parse.quote(wa_template_hourly)}"
    wa_link_4hourly = f"https://wa.me/{wa_number}?text={urllib.parse.quote(wa_template_4hourly)}"
    st.markdown(f"[Send Hourly to WhatsApp]({wa_link_hourly})")
    st.markdown(f"[Send 4-Hourly to WhatsApp]({wa_link_4hourly})")