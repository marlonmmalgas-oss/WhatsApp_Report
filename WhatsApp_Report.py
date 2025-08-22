# Part 1/5
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

# ---------- Config & persistence ----------
SAVE_FILE = "vessel_report.json"

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
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "last_hour": "06h00 - 07h00",
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

# South Africa timezone date default
sa_tz = pytz.timezone("Africa/Johannesburg")
today_sa = datetime.now(sa_tz).date()

# Streamlit page config
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves Tracker", layout="wide")
st.title("⚓ Vessel Hourly & 4-Hourly Moves Tracker")

# ---------- Vessel & Plan info ----------
st.header("📋 Vessel Info")
vessel_name = st.text_input("Vessel Name", value=cumulative.get("vessel_name", ""))
berthed_date = st.text_input("Berthed Date", value=cumulative.get("berthed_date", ""))

with st.expander("📝 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        planned_load = st.number_input("Planned Load", value=cumulative.get("planned_load", 0), key="planned_load")
        planned_disch = st.number_input("Planned Discharge", value=cumulative.get("planned_disch", 0), key="planned_disch")
        planned_restow_load = st.number_input("Planned Restow Load", value=cumulative.get("planned_restow_load", 0), key="planned_restow_load")
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=cumulative.get("planned_restow_disch", 0), key="planned_restow_disch")
    with col2:
        opening_load = st.number_input("Opening Load (Deduction)", value=cumulative.get("opening_load", 0), key="opening_load")
        opening_disch = st.number_input("Opening Discharge (Deduction)", value=cumulative.get("opening_disch", 0), key="opening_disch")
        opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=cumulative.get("opening_restow_load", 0), key="opening_restow_load")
        opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=cumulative.get("opening_restow_disch", 0), key="opening_restow_disch")

# ---------- Hours list ----------
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
if default_hour not in hours_list:
    default_hour = "06h00 - 07h00"

# Date pickers for hourly and 4-hourly reports (auto today, editable)
if "hourly_date" not in st.session_state:
    st.session_state["hourly_date"] = today_sa
if "four_hour_date" not in st.session_state:
    st.session_state["four_hour_date"] = today_sa

hourly_date = st.date_input("Report Date (Hourly)", value=st.session_state["hourly_date"], key="hourly_date")
four_hour_date = st.date_input("Report Date (4-Hourly)", value=st.session_state["four_hour_date"], key="four_hour_date")
# Part 2/5
st.header("⏱ Hourly Moves")

# initialize hourly_time in session_state if missing
if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = default_hour

# selectbox bound to session_state key 'hourly_time' (editable)
hourly_time = st.selectbox("Select Hourly Time", hours_list, index=hours_list.index(st.session_state["hourly_time"]), key="hourly_time")

# Ensure hourly session_state keys exist (prevents NameError on reset)
hr_keys = [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close"
]
for k in hr_keys:
    if k not in st.session_state:
        st.session_state[k] = 0

# Hourly inputs grouped and given explicit, unique keys
with st.expander("🏗 Crane Moves (Hourly)", expanded=True):
    with st.container():
        st.session_state["hr_fwd_load"] = st.number_input("FWD Load (hour)", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
        st.session_state["hr_mid_load"] = st.number_input("MID Load (hour)", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
        st.session_state["hr_aft_load"] = st.number_input("AFT Load (hour)", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
        st.session_state["hr_poop_load"] = st.number_input("POOP Load (hour)", min_value=0, value=st.session_state["hr_poop_load"], key="hr_poop_load")
    with st.container():
        st.session_state["hr_fwd_disch"] = st.number_input("FWD Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_disch"], key="hr_fwd_disch")
        st.session_state["hr_mid_disch"] = st.number_input("MID Discharge (hour)", min_value=0, value=st.session_state["hr_mid_disch"], key="hr_mid_disch")
        st.session_state["hr_aft_disch"] = st.number_input("AFT Discharge (hour)", min_value=0, value=st.session_state["hr_aft_disch"], key="hr_aft_disch")
        st.session_state["hr_poop_disch"] = st.number_input("POOP Discharge (hour)", min_value=0, value=st.session_state["hr_poop_disch"], key="hr_poop_disch")

with st.expander("🔄 Restows (Hourly)", expanded=False):
    st.session_state["hr_fwd_restow_load"] = st.number_input("FWD Restow Load (hour)", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
    st.session_state["hr_mid_restow_load"] = st.number_input("MID Restow Load (hour)", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
    st.session_state["hr_aft_restow_load"] = st.number_input("AFT Restow Load (hour)", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
    st.session_state["hr_poop_restow_load"] = st.number_input("POOP Restow Load (hour)", min_value=0, value=st.session_state["hr_poop_restow_load"], key="hr_poop_restow_load")

    st.session_state["hr_fwd_restow_disch"] = st.number_input("FWD Restow Disch (hour)", min_value=0, value=st.session_state["hr_fwd_restow_disch"], key="hr_fwd_restow_disch")
    st.session_state["hr_mid_restow_disch"] = st.number_input("MID Restow Disch (hour)", min_value=0, value=st.session_state["hr_mid_restow_disch"], key="hr_mid_restow_disch")
    st.session_state["hr_aft_restow_disch"] = st.number_input("AFT Restow Disch (hour)", min_value=0, value=st.session_state["hr_aft_restow_disch"], key="hr_aft_restow_disch")
    st.session_state["hr_poop_restow_disch"] = st.number_input("POOP Restow Disch (hour)", min_value=0, value=st.session_state["hr_poop_restow_disch"], key="hr_poop_restow_disch")

with st.expander("🗃 Hatch Moves (Hourly)", expanded=False):
    st.session_state["hr_hatch_fwd_open"] = st.number_input("FWD Hatch Open (hour)", min_value=0, value=st.session_state["hr_hatch_fwd_open"], key="hr_hatch_fwd_open")
    st.session_state["hr_hatch_mid_open"] = st.number_input("MID Hatch Open (hour)", min_value=0, value=st.session_state["hr_hatch_mid_open"], key="hr_hatch_mid_open")
    st.session_state["hr_hatch_aft_open"] = st.number_input("AFT Hatch Open (hour)", min_value=0, value=st.session_state["hr_hatch_aft_open"], key="hr_hatch_aft_open")
    st.session_state["hr_hatch_fwd_close"] = st.number_input("FWD Hatch Close (hour)", min_value=0, value=st.session_state["hr_hatch_fwd_close"], key="hr_hatch_fwd_close")
    st.session_state["hr_hatch_mid_close"] = st.number_input("MID Hatch Close (hour)", min_value=0, value=st.session_state["hr_hatch_mid_close"], key="hr_hatch_mid_close")
    st.session_state["hr_hatch_aft_close"] = st.number_input("AFT Hatch Close (hour)", min_value=0, value=st.session_state["hr_hatch_aft_close"], key="hr_hatch_aft_close")

# Initialize 4-hour accumulator in session_state (per crane)
if "four_hour_totals" not in st.session_state:
    st.session_state.four_hour_totals = {
        "load": {"FWD":0, "MID":0, "AFT":0, "POOP":0},
        "disch": {"FWD":0, "MID":0, "AFT":0, "POOP":0},
        "restow_load": {"FWD":0, "MID":0, "AFT":0, "POOP":0},
        "restow_disch": {"FWD":0, "MID":0, "AFT":0, "POOP":0},
        "hatch_open": {"FWD":0, "MID":0, "AFT":0},
        "hatch_close": {"FWD":0, "MID":0, "AFT":0}
    }

# Hourly totals (visible)
hourly_total_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
hourly_total_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
hourly_total_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
hourly_total_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
hourly_total_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
hourly_total_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

c1, c2, c3 = st.columns(3)
c1.metric("Load (this hour)", hourly_total_load)
c1.metric("Discharge (this hour)", hourly_total_disch)
c2.metric("Restow Load (this hour)", hourly_total_restow_load)
c2.metric("Restow Disch (this hour)", hourly_total_restow_disch)
c3.metric("Hatch Open (this hour)", hourly_total_hatch_open)
c3.metric("Hatch Close (this hour)", hourly_total_hatch_close)

with st.expander("🔎 Hourly Tracker — per crane (FWD / MID / AFT / POOP)", expanded=False):
    st.write(f"FWD:  Load {st.session_state['hr_fwd_load']}  |  Disch {st.session_state['hr_fwd_disch']}  |  RLoad {st.session_state['hr_fwd_restow_load']}  |  RDisch {st.session_state['hr_fwd_restow_disch']}  |  HOpen {st.session_state['hr_hatch_fwd_open']}  |  HClose {st.session_state['hr_hatch_fwd_close']}")
    st.write(f"MID:  Load {st.session_state['hr_mid_load']}  |  Disch {st.session_state['hr_mid_disch']}  |  RLoad {st.session_state['hr_mid_restow_load']}  |  RDisch {st.session_state['hr_mid_restow_disch']}  |  HOpen {st.session_state['hr_hatch_mid_open']}  |  HClose {st.session_state['hr_hatch_mid_close']}")
    st.write(f"AFT:  Load {st.session_state['hr_aft_load']}  |  Disch {st.session_state['hr_aft_disch']}  |  RLoad {st.session_state['hr_aft_restow_load']}  |  RDisch {st.session_state['hr_aft_restow_disch']}  |  HOpen {st.session_state['hr_hatch_aft_open']}  |  HClose {st.session_state['hr_hatch_aft_close']}")
    st.write(f"POOP: Load {st.session_state['hr_poop_load']}  |  Disch {st.session_state['hr_poop_disch']}  |  RLoad {st.session_state['hr_poop_restow_load']}  |  RDisch {st.session_state['hr_poop_restow_disch']}")
    # Part 3/5
st.header("⏸ Idle / Delays")
num_idles = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=1, key="num_idles")
idle_entries = []
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
    "Spreader difficulties"
]

with st.expander("📝 Idle Entries (optional)", expanded=False):
    for i in range(num_idles):
        crane_name = st.text_input(f"Crane Name {i+1}", key=f"idle_crane_{i}")
        start_time = st.text_input(f"Start Time {i+1} (e.g. 12h30)", key=f"idle_start_{i}")
        end_time = st.text_input(f"End Time {i+1} (e.g. 12h40)", key=f"idle_end_{i}")
        selected_delay = st.selectbox(f"Select Delay {i+1}", options=idle_options, key=f"idle_select_{i}")
        custom_delay = st.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}")
        idle_entries.append({
            "crane": crane_name,
            "start": start_time,
            "end": end_time,
            "delay": custom_delay if custom_delay else selected_delay
        })

# WhatsApp inputs
st.header("📲 Send Hourly Report to WhatsApp")
whatsapp_number = st.text_input("WhatsApp Number (country code, e.g. 2776...)", key="wa_number_hourly")
whatsapp_group_link = st.text_input("Or WhatsApp Group Link (optional)", key="wa_group_hourly")

# Reset hourly inputs (safe)
if st.button("🔄 Reset Hourly Inputs (clear only current hour inputs)"):
    for k in hr_keys:
        st.session_state[k] = 0
    st.success("Hourly inputs cleared (current hour).")
    st.experimental_rerun()

# Generate & Send Hourly Template
if st.button("✅ Generate & Send Hourly Template"):
    # Update persistent cumulative totals
    cumulative["done_load"] += hourly_total_load
    cumulative["done_disch"] += hourly_total_disch
    cumulative["done_restow_load"] += hourly_total_restow_load
    cumulative["done_restow_disch"] += hourly_total_restow_disch
    cumulative["done_hatch_open"] += hourly_total_hatch_open
    cumulative["done_hatch_close"] += hourly_total_hatch_close
    cumulative["last_hour"] = st.session_state["hourly_time"]

    # Accumulate current hourly inputs into 4-hour totals per crane
    st.session_state.four_hour_totals["load"]["FWD"] += st.session_state["hr_fwd_load"]
    st.session_state.four_hour_totals["load"]["MID"] += st.session_state["hr_mid_load"]
    st.session_state.four_hour_totals["load"]["AFT"] += st.session_state["hr_aft_load"]
    st.session_state.four_hour_totals["load"]["POOP"] += st.session_state["hr_poop_load"]

    st.session_state.four_hour_totals["disch"]["FWD"] += st.session_state["hr_fwd_disch"]
    st.session_state.four_hour_totals["disch"]["MID"] += st.session_state["hr_mid_disch"]
    st.session_state.four_hour_totals["disch"]["AFT"] += st.session_state["hr_aft_disch"]
    st.session_state.four_hour_totals["disch"]["POOP"] += st.session_state["hr_poop_disch"]

    st.session_state.four_hour_totals["restow_load"]["FWD"] += st.session_state["hr_fwd_restow_load"]
    st.session_state.four_hour_totals["restow_load"]["MID"] += st.session_state["hr_mid_restow_load"]
    st.session_state.four_hour_totals["restow_load"]["AFT"] += st.session_state["hr_aft_restow_load"]
    st.session_state.four_hour_totals["restow_load"]["POOP"] += st.session_state["hr_poop_restow_load"]

    st.session_state.four_hour_totals["restow_disch"]["FWD"] += st.session_state["hr_fwd_restow_disch"]
    st.session_state.four_hour_totals["restow_disch"]["MID"] += st.session_state["hr_mid_restow_disch"]
    st.session_state.four_hour_totals["restow_disch"]["AFT"] += st.session_state["hr_aft_restow_disch"]
    st.session_state.four_hour_totals["restow_disch"]["POOP"] += st.session_state["hr_poop_restow_disch"]

    st.session_state.four_hour_totals["hatch_open"]["FWD"] += st.session_state["hr_hatch_fwd_open"]
    st.session_state.four_hour_totals["hatch_open"]["MID"] += st.session_state["hr_hatch_mid_open"]
    st.session_state.four_hour_totals["hatch_open"]["AFT"] += st.session_state["hr_hatch_aft_open"]

    st.session_state.four_hour_totals["hatch_close"]["FWD"] += st.session_state["hr_hatch_fwd_close"]
    st.session_state.four_hour_totals["hatch_close"]["MID"] += st.session_state["hr_hatch_mid_close"]
    st.session_state.four_hour_totals["hatch_close"]["AFT"] += st.session_state["hr_hatch_aft_close"]

    # Persist cumulative
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Build hourly template (monospace)
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    hourly_template = f"""\
{vessel_name}
Berthed {berthed_date}

{st.session_state.get('hourly_date').strftime('%d/%m/%Y')}
{st.session_state['hourly_time']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {st.session_state['hr_fwd_load']:>5}     {st.session_state['hr_fwd_disch']:>5}
MID       {st.session_state['hr_mid_load']:>5}     {st.session_state['hr_mid_disch']:>5}
AFT       {st.session_state['hr_aft_load']:>5}     {st.session_state['hr_aft_disch']:>5}
POOP      {st.session_state['hr_poop_load']:>5}     {st.session_state['hr_poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {st.session_state['hr_fwd_restow_load']:>5}     {st.session_state['hr_fwd_restow_disch']:>5}
MID       {st.session_state['hr_mid_restow_load']:>5}     {st.session_state['hr_mid_restow_disch']:>5}
AFT       {st.session_state['hr_aft_restow_load']:>5}     {st.session_state['hr_aft_restow_disch']:>5}
POOP      {st.session_state['hr_poop_restow_load']:>5}     {st.session_state['hr_poop_restow_disch']:>5}
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
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(idle_entries):
        hourly_template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

    st.code(hourly_template, language="text")

    # Provide WhatsApp link(s)
    if whatsapp_number:
        wa_template = f"```{hourly_template}```"
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif whatsapp_group_link:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link})", unsafe_allow_html=True)

    # Auto-advance hourly_time in session_state and persist to cumulative
    current_idx = hours_list.index(st.session_state["hourly_time"])
    next_idx = (current_idx + 1) % len(hours_list)
    st.session_state["hourly_time"] = hours_list[next_idx]
    cumulative["last_hour"] = hours_list[next_idx]
    # Persist cumulative update
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    st.success("Hourly template generated. Hour advanced and 4-hour totals updated.")
    # Part 4/5
st.header("⏱ 4-Hourly Report Tracker")

# Display the current 4-hour accumulated totals (per crane) — these are sums of hourly entries
with st.expander("📊 Current 4-Hour Totals (per crane)", expanded=True):
    st.write("Format: Load | Disch | Restow Load | Restow Disch | Hatch Open | Hatch Close")
    st.write("FWD:", f"{st.session_state.four_hour_totals['load']['FWD']} | {st.session_state.four_hour_totals['disch']['FWD']} | {st.session_state.four_hour_totals['restow_load']['FWD']} | {st.session_state.four_hour_totals['restow_disch']['FWD']} | {st.session_state.four_hour_totals['hatch_open']['FWD']} | {st.session_state.four_hour_totals['hatch_close']['FWD']}")
    st.write("MID:", f"{st.session_state.four_hour_totals['load']['MID']} | {st.session_state.four_hour_totals['disch']['MID']} | {st.session_state.four_hour_totals['restow_load']['MID']} | {st.session_state.four_hour_totals['restow_disch']['MID']} | {st.session_state.four_hour_totals['hatch_open']['MID']} | {st.session_state.four_hour_totals['hatch_close']['MID']}")
    st.write("AFT:", f"{st.session_state.four_hour_totals['load']['AFT']} | {st.session_state.four_hour_totals['disch']['AFT']} | {st.session_state.four_hour_totals['restow_load']['AFT']} | {st.session_state.four_hour_totals['restow_disch']['AFT']} | {st.session_state.four_hour_totals['hatch_open']['AFT']} | {st.session_state.four_hour_totals['hatch_close']['AFT']}")
    st.write("POOP:", f"{st.session_state.four_hour_totals['load']['POOP']} | {st.session_state.four_hour_totals['disch']['POOP']} | {st.session_state.four_hour_totals['restow_load']['POOP']} | {st.session_state.four_hour_totals['restow_disch']['POOP']}")

# Manual override for 4-hour totals (collapsible)
with st.expander("✏️ Edit / Override 4-Hour Totals (per crane)", expanded=False):
    for pos in ["FWD","MID","AFT","POOP"]:
        st.session_state.four_hour_totals["load"][pos] = st.number_input(f"4H Load {pos}", min_value=0, value=st.session_state.four_hour_totals["load"][pos], key=f"4h_load_{pos}")
        st.session_state.four_hour_totals["disch"][pos] = st.number_input(f"4H Disch {pos}", min_value=0, value=st.session_state.four_hour_totals["disch"][pos], key=f"4h_disch_{pos}")
        st.session_state.four_hour_totals["restow_load"][pos] = st.number_input(f"4H Restow Load {pos}", min_value=0, value=st.session_state.four_hour_totals["restow_load"][pos], key=f"4h_restow_load_{pos}")
        st.session_state.four_hour_totals["restow_disch"][pos] = st.number_input(f"4H Restow Disch {pos}", min_value=0, value=st.session_state.four_hour_totals["restow_disch"][pos], key=f"4h_restow_disch_{pos}")
    for pos in ["FWD","MID","AFT"]:
        st.session_state.four_hour_totals["hatch_open"][pos] = st.number_input(f"4H Hatch Open {pos}", min_value=0, value=st.session_state.four_hour_totals["hatch_open"][pos], key=f"4h_hopen_{pos}")
        st.session_state.four_hour_totals["hatch_close"][pos] = st.number_input(f"4H Hatch Close {pos}", min_value=0, value=st.session_state.four_hour_totals["hatch_close"][pos], key=f"4h_hclose_{pos}")

# Reset 4-hour totals safely (button)
if st.button("🔄 Reset 4-Hour Totals (clear accumulated 4H counts)"):
    for s in st.session_state.four_hour_totals:
        for p in st.session_state.four_hour_totals[s]:
            st.session_state.four_hour_totals[s][p] = 0
    st.success("4-Hour accumulated totals cleared.")
    st.experimental_rerun()
    # Part 5/5
st.header("📩 4-Hourly WhatsApp Template & Send")

# Build the 4-hour template using the session_state four_hour_totals
f = st.session_state.four_hour_totals

four_hour_template = f"""\
{vessel_name}
Berthed {berthed_date}

{st.session_state.get('four_hour_date').strftime('%d/%m/%Y')}
4-Hour Block: {st.selectbox('Choose 4-hour block', ['06h00 - 10h00','10h00 - 14h00','14h00 - 18h00','18h00 - 22h00','22h00 - 02h00','02h00 - 06h00'], index=0, key='four_block')}
_________________________
*4-HOUR TOTALS (per crane)*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {f['load']['FWD']:>5}     {f['disch']['FWD']:>5}
MID       {f['load']['MID']:>5}     {f['disch']['MID']:>5}
AFT       {f['load']['AFT']:>5}     {f['disch']['AFT']:>5}
POOP      {f['load']['POOP']:>5}     {f['disch']['POOP']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {f['restow_load']['FWD']:>5}     {f['restow_disch']['FWD']:>5}
MID       {f['restow_load']['MID']:>5}     {f['restow_disch']['MID']:>5}
AFT       {f['restow_load']['AFT']:>5}     {f['restow_disch']['AFT']:>5}
POOP      {f['restow_load']['POOP']:>5}     {f['restow_disch']['POOP']:>5}
_________________________
*CUMULATIVE (persistent Done totals)*
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {planned_load - cumulative['done_load']:>5}      {planned_disch - cumulative['done_disch']:>5}
_________________________
*Restows*
           Load    Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {planned_restow_load - cumulative['done_restow_load']:>5}      {planned_restow_disch - cumulative['done_restow_disch']:>5}
_________________________
*Hatch Moves (4H totals)*
             Open      Close
FWD          {f['hatch_open']['FWD']:>5}      {f['hatch_close']['FWD']:>5}
MID          {f['hatch_open']['MID']:>5}      {f['hatch_close']['MID']:>5}
AFT          {f['hatch_open']['AFT']:>5}      {f['hatch_close']['AFT']:>5}
_________________________
*Idle / Delays*
"""

# Append idle entries if present
for i, idle in enumerate(idle_entries):
    four_hour_template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

st.code(four_hour_template, language="text")

# Send 4-hourly
st.header("📲 Send 4-Hourly Report")
whatsapp_number_4h = st.text_input("WhatsApp Number for 4H (with country code)", key="wa_4h_number")
whatsapp_group_link_4h = st.text_input("Or WhatsApp Group Link (4H)", key="wa_4h_group")

if st.button("📤 Send 4-Hourly Template"):
    if whatsapp_number_4h:
        wa_template = f"```{four_hour_template}```"
        wa_link = f"https://wa.me/{whatsapp_number_4h}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
        st.success("4-Hourly template ready to send.")
    elif whatsapp_group_link_4h:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link_4h})", unsafe_allow_html=True)
        st.success("4-Hourly template ready to send.")
    else:
        st.warning("Enter WhatsApp number or group link to send the 4-hourly template.")

# Manual advance button (no auto loop)
if st.button("⏭ Advance Hour (manual)"):
    current_idx = hours_list.index(st.session_state["hourly_time"])
    st.session_state["hourly_time"] = hours_list[(current_idx + 1) % len(hours_list)]
    cumulative["last_hour"] = st.session_state["hourly_time"]
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)
    st.success(f"Hour advanced to {st.session_state['hourly_time']}")
    st.experimental_rerun()

st.markdown("---")
st.info("Tips: Templates include the report date (auto = today). You can override the date using the date pickers at the top. Use Reset buttons to clear hourly or 4-hour accumulations.")