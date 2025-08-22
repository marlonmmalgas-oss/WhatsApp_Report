import streamlit as st
import datetime
import urllib.parse

# -------------------------
# Session State Defaults
# -------------------------
S = st.session_state

if 'cumulative' not in S:
    S['cumulative'] = {
        'done_load': 0, 'done_disch': 0,
        'done_restow_load': 0, 'done_restow_disch': 0
    }

if 'four_hourly' not in S:
    S['four_hourly'] = {
        'fwd_load': 0, 'mid_load': 0, 'aft_load': 0, 'poop_load': 0,
        'fwd_disch': 0, 'mid_disch': 0, 'aft_disch': 0, 'poop_disch': 0,
        'fwd_restow_load': 0, 'mid_restow_load': 0, 'aft_restow_load': 0, 'poop_restow_load': 0,
        'fwd_restow_disch': 0, 'mid_restow_disch': 0, 'aft_restow_disch': 0, 'poop_restow_disch': 0,
        'fwd_hatch_open': 0, 'mid_hatch_open': 0, 'aft_hatch_open': 0,
        'fwd_hatch_close': 0, 'mid_hatch_close': 0, 'aft_hatch_close': 0
    }

if 'idle_entries' not in S:
    S['idle_entries'] = []

# -------------------------
# Page Setup
# -------------------------
st.set_page_config(page_title="Hourly & 4-Hourly Report", layout="wide")
st.title("Port Operations Report")
today_date = datetime.date.today().strftime("%d/%m/%Y")

# -------------------------
# Hourly Time Selection
# -------------------------
hours_list = [f"{h:02d}h00 - {h+1:02d}h00" for h in range(6, 24)]
default_hour = hours_list[0]
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# -------------------------
# Vessel Info Inputs
# -------------------------
vessel_name = st.text_input("Vessel Name", "MSC Example")
berthed_date = st.text_input("Berthed Date", "14/08/2025")
# -------------------------
# Hourly Input Groups
# -------------------------
with st.expander("Hourly Crane Moves", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fwd_load = st.number_input("FWD Load", value=0, min_value=0)
        fwd_disch = st.number_input("FWD Discharge", value=0, min_value=0)
        fwd_restow_load = st.number_input("FWD Restow Load", value=0, min_value=0)
        fwd_restow_disch = st.number_input("FWD Restow Discharge", value=0, min_value=0)
        fwd_hatch_open = st.number_input("FWD Hatch Open", value=0, min_value=0)
        fwd_hatch_close = st.number_input("FWD Hatch Close", value=0, min_value=0)
    with col2:
        mid_load = st.number_input("MID Load", value=0, min_value=0)
        mid_disch = st.number_input("MID Discharge", value=0, min_value=0)
        mid_restow_load = st.number_input("MID Restow Load", value=0, min_value=0)
        mid_restow_disch = st.number_input("MID Restow Discharge", value=0, min_value=0)
        mid_hatch_open = st.number_input("MID Hatch Open", value=0, min_value=0)
        mid_hatch_close = st.number_input("MID Hatch Close", value=0, min_value=0)
    with col3:
        aft_load = st.number_input("AFT Load", value=0, min_value=0)
        aft_disch = st.number_input("AFT Discharge", value=0, min_value=0)
        aft_restow_load = st.number_input("AFT Restow Load", value=0, min_value=0)
        aft_restow_disch = st.number_input("AFT Restow Discharge", value=0, min_value=0)
        aft_hatch_open = st.number_input("AFT Hatch Open", value=0, min_value=0)
        aft_hatch_close = st.number_input("AFT Hatch Close", value=0, min_value=0)
    with col4:
        poop_load = st.number_input("POOP Load", value=0, min_value=0)
        poop_disch = st.number_input("POOP Discharge", value=0, min_value=0)
        poop_restow_load = st.number_input("POOP Restow Load", value=0, min_value=0)
        poop_restow_disch = st.number_input("POOP Restow Discharge", value=0, min_value=0)

# -------------------------
# Idle / Delay Section
# -------------------------
with st.expander("Idle / Delays", expanded=False):
    max_idles = 10
    delay_options = [
        "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
        "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
        "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
        "Crane break down/ boom limit", "Crane break down", "Vessel listing",
        "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
    ]

    idle_entries = []
    for i in range(max_idles):
        with st.container():
            idle_col1, idle_col2, idle_col3 = st.columns([2, 2, 4])
            with idle_col1:
                crane = st.selectbox(f"Idle Crane {i+1}", ["FWD", "MID", "AFT", "POOP"], key=f"idle_crane_{i}")
            with idle_col2:
                start_time = st.time_input(f"Start Time {i+1}", key=f"idle_start_{i}")
                end_time = st.time_input(f"End Time {i+1}", key=f"idle_end_{i}")
            with idle_col3:
                delay_type = st.selectbox(f"Delay {i+1}", delay_options + ["Other"], key=f"idle_type_{i}")
                if delay_type == "Other":
                    delay_type = st.text_input(f"Custom Delay {i+1}", key=f"idle_custom_{i}")
            if crane and start_time and end_time and delay_type:
                idle_entries.append({"crane": crane, "start": start_time.strftime("%H:%M"),
                                     "end": end_time.strftime("%H:%M"), "delay_type": delay_type})
      # -------------------------
# Calculate Totals
# -------------------------
total_load = fwd_load + mid_load + aft_load + poop_load
total_disch = fwd_disch + mid_disch + aft_disch + poop_disch
total_restow_load = fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
total_restow_disch = fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
total_hatch_open = fwd_hatch_open + mid_hatch_open + aft_hatch_open
total_hatch_close = fwd_hatch_close + mid_hatch_close + aft_hatch_close

# Update cumulative for hourly
S['cumulative']['done_load'] += total_load
S['cumulative']['done_disch'] += total_disch
S['cumulative']['done_restow_load'] += total_restow_load
S['cumulative']['done_restow_disch'] += total_restow_disch

# Update 4-Hourly totals (adds hourly totals, resets every 4 hours manually)
if st.button("Reset 4-Hourly Totals"):
    for key in S['four_hourly']:
        S['four_hourly'][key] = 0

S['four_hourly']['fwd_load'] += fwd_load
S['four_hourly']['mid_load'] += mid_load
S['four_hourly']['aft_load'] += aft_load
S['four_hourly']['poop_load'] += poop_load
S['four_hourly']['fwd_disch'] += fwd_disch
S['four_hourly']['mid_disch'] += mid_disch
S['four_hourly']['aft_disch'] += aft_disch
S['four_hourly']['poop_disch'] += poop_disch
S['four_hourly']['fwd_restow_load'] += fwd_restow_load
S['four_hourly']['mid_restow_load'] += mid_restow_load
S['four_hourly']['aft_restow_load'] += aft_restow_load
S['four_hourly']['poop_restow_load'] += poop_restow_load
S['four_hourly']['fwd_restow_disch'] += fwd_restow_disch
S['four_hourly']['mid_restow_disch'] += mid_restow_disch
S['four_hourly']['aft_restow_disch'] += aft_restow_disch
S['four_hourly']['poop_restow_disch'] += poop_restow_disch
S['four_hourly']['fwd_hatch_open'] += fwd_hatch_open
S['four_hourly']['mid_hatch_open'] += mid_hatch_open
S['four_hourly']['aft_hatch_open'] += aft_hatch_open
S['four_hourly']['fwd_hatch_close'] += fwd_hatch_close
S['four_hourly']['mid_hatch_close'] += mid_hatch_close
S['four_hourly']['aft_hatch_close'] += aft_hatch_close

# -------------------------
# WhatsApp Templates (Monospace)
# -------------------------
hourly_template = f"""\
{vessel_name}
Berthed {berthed_date}
Date: {today_date}
Hourly: {hourly_time}
_________________________
*Crane Moves*
           Load  Discharge
FWD        {fwd_load:>5}  {fwd_disch:>5}
MID        {mid_load:>5}  {mid_disch:>5}
AFT        {aft_load:>5}  {aft_disch:>5}
POOP       {poop_load:>5}  {poop_disch:>5}
_________________________
*Restows*
           Load  Disch
FWD        {fwd_restow_load:>5}  {fwd_restow_disch:>5}
MID        {mid_restow_load:>5}  {mid_restow_disch:>5}
AFT        {aft_restow_load:>5}  {aft_restow_disch:>5}
POOP       {poop_restow_load:>5}  {poop_restow_disch:>5}
_________________________
*CUMULATIVE*
Done Load: {S['cumulative']['done_load']}
Done Disch: {S['cumulative']['done_disch']}
_________________________
*Idle*
"""

for idle in idle_entries:
    hourly_template += f"{idle['crane']} {idle['start']}-{idle['end']} {idle['delay_type']}\n"

st.subheader("Hourly WhatsApp Template")
st.code(hourly_template)

# 4-Hourly Template
four_template = f"""\
{vessel_name}
Berthed {berthed_date}
Date: {today_date}
4-Hour Block
_________________________
*Crane Moves*
           Load  Disch
FWD        {S['four_hourly']['fwd_load']:>5}  {S['four_hourly']['fwd_disch']:>5}
MID        {S['four_hourly']['mid_load']:>5}  {S['four_hourly']['mid_disch']:>5}
AFT        {S['four_hourly']['aft_load']:>5}  {S['four_hourly']['aft_disch']:>5}
POOP       {S['four_hourly']['poop_load']:>5}  {S['four_hourly']['poop_disch']:>5}
_________________________
*Restows*
           Load  Disch
FWD        {S['four_hourly']['fwd_restow_load']:>5}  {S['four_hourly']['fwd_restow_disch']:>5}
MID        {S['four_hourly']['mid_restow_load']:>5}  {S['four_hourly']['mid_restow_disch']:>5}
AFT        {S['four_hourly']['aft_restow_load']:>5}  {S['four_hourly']['aft_restow_disch']:>5}
POOP       {S['four_hourly']['poop_restow_load']:>5}  {S['four_hourly']['poop_restow_disch']:>5}
_________________________
*Hatch Moves*
           Open  Close
FWD        {S['four_hourly']['fwd_hatch_open']:>5}  {S['four_hourly']['fwd_hatch_close']:>5}
MID        {S['four_hourly']['mid_hatch_open']:>5}  {S['four_hourly']['mid_hatch_close']:>5}
AFT        {S['four_hourly']['aft_hatch_open']:>5}  {S['four_hourly']['aft_hatch_close']:>5}
_________________________
*Idle*
"""

for idle in idle_entries:
    four_template += f"{idle['crane']} {idle['start']}-{idle['end']} {idle['delay_type']}\n"

st.subheader("4-Hourly WhatsApp Template")
st.code(four_template)

# -------------------------
# WhatsApp Links
# -------------------------
wa_number = st.text_input("WhatsApp Number (Country code e.g. 27761234567)")
if wa_number:
    wa_link_hourly = f"https://wa.me/{wa_number}?text={urllib.parse.quote(hourly_template)}"
    wa_link_4hourly = f"https://wa.me/{wa_number}?text={urllib.parse.quote(four_template)}"
    st.markdown(f"[Send Hourly to WhatsApp]({wa_link_hourly})")
    st.markdown(f"[Send 4-Hourly to WhatsApp]({wa_link_4hourly})")                               