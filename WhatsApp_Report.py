# Part 1: Imports, Setup, Vessel Info, Plan & Hourly Time
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

SAVE_FILE = "vessel_report.json"

# --- Initialize or load cumulative data ---
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

# --- Timezone & date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz)
formatted_date = today_date.strftime("%d/%m/%Y")

st.title("⛴️ Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("🛳️ Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
report_date = st.date_input("Report Date", today_date)

# --- Plan & Opening Balances (Collapsible) ---
with st.expander("📊 Plan Totals & Opening Balance (Internal Only)", expanded=False):
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
hourly_time = st.selectbox("⏰ Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))
# Part 2: Hourly Moves Input, Restows, Hatch Moves, Idle/Delays, Tracker

st.header(f"⚙️ Hourly Moves Input ({hourly_time})")

# --- Hourly Crane Moves ---
with st.expander("🏗️ Crane Moves", expanded=True):
    with st.expander("Load", expanded=True):
        fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="hr_fwd_load")
        mid_load = st.number_input("MID Load", min_value=0, value=0, key="hr_mid_load")
        aft_load = st.number_input("AFT Load", min_value=0, value=0, key="hr_aft_load")
        poop_load = st.number_input("POOP Load", min_value=0, value=0, key="hr_poop_load")
    with st.expander("Discharge", expanded=True):
        fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="hr_fwd_disch")
        mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="hr_mid_disch")
        aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="hr_aft_disch")
        poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="hr_poop_disch")

# --- Hourly Restows ---
with st.expander("🔄 Restows", expanded=False):
    with st.expander("Load", expanded=True):
        fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="hr_fwd_restow_load")
        mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="hr_mid_restow_load")
        aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="hr_aft_restow_load")
        poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="hr_poop_restow_load")
    with st.expander("Discharge", expanded=True):
        fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0, key="hr_fwd_restow_disch")
        mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0, key="hr_mid_restow_disch")
        aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0, key="hr_aft_restow_disch")
        poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0, key="hr_poop_restow_disch")

# --- Hourly Hatch Moves ---
with st.expander("🗃️ Hatch Moves", expanded=False):
    with st.expander("Open", expanded=True):
        hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="hr_hatch_fwd_open")
        hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="hr_hatch_mid_open")
        hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="hr_hatch_aft_open")
    with st.expander("Close", expanded=True):
        hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="hr_hatch_fwd_close")
        hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="hr_hatch_mid_close")
        hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="hr_hatch_aft_close")

# --- Idle Section ---
st.header("⏱️ Idle / Delays")
num_idles = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=1)
idle_entries = []
idle_options = [
    "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
    "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
    "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
    "Crane break down/ boom limit", "Crane break down", "Vessel listing",
    "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
]
with st.expander("📝 Idle Entries", expanded=False):
    for i in range(num_idles):
        st.subheader(f"Idle Entry {i+1}")
        crane_name = st.text_input(f"Crane Name {i+1}", "")
        start_time = st.text_input(f"Start Time {i+1}", "")
        end_time = st.text_input(f"End Time {i+1}", "")
        selected_delay = st.selectbox(f"Select Delay {i+1}", options=idle_options, key=f"idle_select_{i}")
        custom_delay = st.text_input(f"Custom Delay {i+1} (optional)", "")
        idle_entries.append({
            "crane": crane_name,
            "start": start_time,
            "end": end_time,
            "delay": custom_delay if custom_delay else selected_delay
        })

# --- Hourly Tracker Collapsible ---
with st.expander("📈 Hourly Tracker (Total by Section)", expanded=True):
    st.write("**Load Totals**")
    st.write(f"FWD: {fwd_load} | MID: {mid_load} | AFT: {aft_load} | POOP: {poop_load}")
    st.write("**Discharge Totals**")
    st.write(f"FWD: {fwd_disch} | MID: {mid_disch} | AFT: {aft_disch} | POOP: {poop_disch}")
    st.write("**Restow Load Totals**")
    st.write(f"FWD: {fwd_restow_load} | MID: {mid_restow_load} | AFT: {aft_restow_load} | POOP: {poop_restow_load}")
    st.write("**Restow Discharge Totals**")
    st.write(f"FWD: {fwd_restow_disch} | MID: {mid_restow_disch} | AFT: {aft_restow_disch} | POOP: {poop_restow_disch}")
    st.write("**Hatch Open Totals**")
    st.write(f"FWD: {hatch_fwd_open} | MID: {hatch_mid_open} | AFT: {hatch_aft_open}")
    st.write("**Hatch Close Totals**")
    st.write(f"FWD: {hatch_fwd_close} | MID: {hatch_mid_close} | AFT: {hatch_aft_close}")
    # Part 3: Hourly WhatsApp Template, 4-Hourly Input, Tracker, and Send

st.header("📤 Hourly Report Template")
# --- Automatic Hourly Template for WhatsApp ---
hourly_template = f"""
📅 Date: {report_date.strftime('%Y-%m-%d')}
🕐 Hour: {hourly_time}

🏗️ Crane Moves:
Load - FWD: {fwd_load} | MID: {mid_load} | AFT: {aft_load} | POOP: {poop_load}
Discharge - FWD: {fwd_disch} | MID: {mid_disch} | AFT: {aft_disch} | POOP: {poop_disch}

🔄 Restows:
Load - FWD: {fwd_restow_load} | MID: {mid_restow_load} | AFT: {aft_restow_load} | POOP: {poop_restow_load}
Discharge - FWD: {fwd_restow_disch} | MID: {mid_restow_disch} | AFT: {aft_restow_disch} | POOP: {poop_restow_disch}

🗃️ Hatch Moves:
Open - FWD: {hatch_fwd_open} | MID: {hatch_mid_open} | AFT: {hatch_aft_open}
Close - FWD: {hatch_fwd_close} | MID: {hatch_mid_close} | AFT: {hatch_aft_close}

⏱️ Idle / Delays:
"""
for i, idle in enumerate(idle_entries):
    hourly_template += f"{i+1}. {idle['crane']} | {idle['start']}-{idle['end']} | {idle['delay']}\n"

st.text_area("Hourly WhatsApp Template", value=hourly_template, height=300)

# --- 4-Hourly Input Section ---
st.header("🕓 4-Hourly Moves Input")
with st.expander("4-Hourly Crane Totals", expanded=True):
    # Load
    fwd_load_4h = st.number_input("FWD Load (4h)", min_value=0, value=0, key="4h_fwd_load")
    mid_load_4h = st.number_input("MID Load (4h)", min_value=0, value=0, key="4h_mid_load")
    aft_load_4h = st.number_input("AFT Load (4h)", min_value=0, value=0, key="4h_aft_load")
    poop_load_4h = st.number_input("POOP Load (4h)", min_value=0, value=0, key="4h_poop_load")
    # Discharge
    fwd_disch_4h = st.number_input("FWD Discharge (4h)", min_value=0, value=0, key="4h_fwd_disch")
    mid_disch_4h = st.number_input("MID Discharge (4h)", min_value=0, value=0, key="4h_mid_disch")
    aft_disch_4h = st.number_input("AFT Discharge (4h)", min_value=0, value=0, key="4h_aft_disch")
    poop_disch_4h = st.number_input("POOP Discharge (4h)", min_value=0, value=0, key="4h_poop_disch")
    # Restow Load
    fwd_restow_load_4h = st.number_input("FWD Restow Load (4h)", min_value=0, value=0, key="4h_fwd_restow_load")
    mid_restow_load_4h = st.number_input("MID Restow Load (4h)", min_value=0, value=0, key="4h_mid_restow_load")
    aft_restow_load_4h = st.number_input("AFT Restow Load (4h)", min_value=0, value=0, key="4h_aft_restow_load")
    poop_restow_load_4h = st.number_input("POOP Restow Load (4h)", min_value=0, value=0, key="4h_poop_restow_load")
    # Restow Discharge
    fwd_restow_disch_4h = st.number_input("FWD Restow Discharge (4h)", min_value=0, value=0, key="4h_fwd_restow_disch")
    mid_restow_disch_4h = st.number_input("MID Restow Discharge (4h)", min_value=0, value=0, key="4h_mid_restow_disch")
    aft_restow_disch_4h = st.number_input("AFT Restow Discharge (4h)", min_value=0, value=0, key="4h_aft_restow_disch")
    poop_restow_disch_4h = st.number_input("POOP Restow Discharge (4h)", min_value=0, value=0, key="4h_poop_restow_disch")
    # Hatch Open / Close
    hatch_fwd_open_4h = st.number_input("FWD Hatch Open (4h)", min_value=0, value=0, key="4h_hatch_fwd_open")
    hatch_mid_open_4h = st.number_input("MID Hatch Open (4h)", min_value=0, value=0, key="4h_hatch_mid_open")
    hatch_aft_open_4h = st.number_input("AFT Hatch Open (4h)", min_value=0, value=0, key="4h_hatch_aft_open")
    hatch_fwd_close_4h = st.number_input("FWD Hatch Close (4h)", min_value=0, value=0, key="4h_hatch_fwd_close")
    hatch_mid_close_4h = st.number_input("MID Hatch Close (4h)", min_value=0, value=0, key="4h_hatch_mid_close")
    hatch_aft_close_4h = st.number_input("AFT Hatch Close (4h)", min_value=0, value=0, key="4h_hatch_aft_close")

# --- 4-Hourly Tracker Collapsible ---
with st.expander("📊 4-Hourly Tracker (Total Counts)", expanded=True):
    st.write("**Load Totals (4h)**")
    st.write(f"FWD: {fwd_load_4h} | MID: {mid_load_4h} | AFT: {aft_load_4h} | POOP: {poop_load_4h}")
    st.write("**Discharge Totals (4h)**")
    st.write(f"FWD: {fwd_disch_4h} | MID: {mid_disch_4h} | AFT: {aft_disch_4h} | POOP: {poop_disch_4h}")
    st.write("**Restow Load Totals (4h)**")
    st.write(f"FWD: {fwd_restow_load_4h} | MID: {mid_restow_load_4h} | AFT: {aft_restow_load_4h} | POOP: {poop_restow_load_4h}")
    st.write("**Restow Discharge Totals (4h)**")
    st.write(f"FWD: {fwd_restow_disch_4h} | MID: {mid_restow_disch_4h} | AFT: {aft_restow_disch_4h} | POOP: {poop_restow_disch_4h}")
    st.write("**Hatch Open Totals (4h)**")
    st.write(f"FWD: {hatch_fwd_open_4h} | MID: {hatch_mid_open_4h} | AFT: {hatch_aft_open_4h}")
    st.write("**Hatch Close Totals (4h)**")
    st.write(f"FWD: {hatch_fwd_close_4h} | MID: {hatch_mid_close_4h} | AFT: {hatch_aft_close_4h}")
    # Part 4: 4-Hourly WhatsApp Template, Send, Auto-Hour, Reset

st.header("📤 4-Hourly WhatsApp Template")

# --- Automatic 4-Hourly WhatsApp Template ---
four_hourly_template = f"""
📅 Date: {report_date.strftime('%Y-%m-%d')}
🕓 Period: {hourly_time} - {hourly_time_end_4h}

🏗️ Crane Moves (4h):
Load - FWD: {fwd_load_4h} | MID: {mid_load_4h} | AFT: {aft_load_4h} | POOP: {poop_load_4h}
Discharge - FWD: {fwd_disch_4h} | MID: {mid_disch_4h} | AFT: {aft_disch_4h} | POOP: {poop_disch_4h}

🔄 Restows (4h):
Load - FWD: {fwd_restow_load_4h} | MID: {mid_restow_load_4h} | AFT: {aft_restow_load_4h} | POOP: {poop_restow_load_4h}
Discharge - FWD: {fwd_restow_disch_4h} | MID: {mid_restow_disch_4h} | AFT: {aft_restow_disch_4h} | POOP: {poop_restow_disch_4h}

🗃️ Hatch Moves (4h):
Open - FWD: {hatch_fwd_open_4h} | MID: {hatch_mid_open_4h} | AFT: {hatch_aft_open_4h}
Close - FWD: {hatch_fwd_close_4h} | MID: {hatch_mid_close_4h} | AFT: {hatch_aft_close_4h}

⏱️ Idle / Delays:
"""
for i, idle in enumerate(idle_entries_4h):
    four_hourly_template += f"{i+1}. {idle['crane']} | {idle['start']}-{idle['end']} | {idle['delay']}\n"

st.text_area("4-Hourly WhatsApp Template", value=four_hourly_template, height=350)

# --- Auto Increment Hour ---
if "hour_index" not in st.session_state:
    st.session_state["hour_index"] = 0

hour_options = [f"{str(h).zfill(2)}h00" for h in range(24)]
if st.button("Generate Hourly Template"):
    st.session_state["hour_index"] += 1
    if st.session_state["hour_index"] >= len(hour_options):
        st.session_state["hour_index"] = 0
    st.experimental_rerun()

hourly_time = hour_options[st.session_state["hour_index"]]
hourly_time_end_4h = hour_options[(st.session_state["hour_index"] + 4) % 24]

# --- Reset Buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Reset Hourly"):
        for section in hourly_keys:
            st.session_state[section] = 0
        idle_entries.clear()
        st.experimental_rerun()
with col2:
    if st.button("🔄 Reset 4-Hourly"):
        for section in four_hourly_keys:
            st.session_state[section] = 0
        idle_entries_4h.clear()
        st.experimental_rerun()

# --- Send WhatsApp Options ---
st.header("📱 Send Reports via WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code)", value="")
group_link = st.text_input("Or enter WhatsApp Group Link (optional)", value="")

if st.button("Send Hourly Report"):
    st.write(f"✅ Hourly report ready to send to {whatsapp_number or group_link}")
if st.button("Send 4-Hourly Report"):
    st.write(f"✅ 4-Hourly report ready to send to {whatsapp_number or group_link}")
    # Part 5: Date Picker, Session State Fixes, Footer, Collapsible Trackers

import datetime

st.header("📅 Report Date")
# --- Automatic Date with Picker ---
if "report_date" not in st.session_state:
    st.session_state["report_date"] = datetime.date.today()

report_date = st.date_input("Select Report Date", value=st.session_state["report_date"])
st.session_state["report_date"] = report_date

# --- Collapsible Hourly Tracker ---
with st.expander("🕑 Hourly Tracker Details"):
    st.write("📊 Crane Moves")
    st.write(f"Load - FWD: {st.session_state.get('hr_fwd_load',0)}, MID: {st.session_state.get('hr_mid_load',0)}, AFT: {st.session_state.get('hr_aft_load',0)}, POOP: {st.session_state.get('hr_poop_load',0)}")
    st.write(f"Discharge - FWD: {st.session_state.get('hr_fwd_disch',0)}, MID: {st.session_state.get('hr_mid_disch',0)}, AFT: {st.session_state.get('hr_aft_disch',0)}, POOP: {st.session_state.get('hr_poop_disch',0)}")
    st.write("🔄 Restows")
    st.write(f"Load - FWD: {st.session_state.get('hr_fwd_restow_load',0)}, MID: {st.session_state.get('hr_mid_restow_load',0)}, AFT: {st.session_state.get('hr_aft_restow_load',0)}, POOP: {st.session_state.get('hr_poop_restow_load',0)}")
    st.write(f"Discharge - FWD: {st.session_state.get('hr_fwd_restow_disch',0)}, MID: {st.session_state.get('hr_mid_restow_disch',0)}, AFT: {st.session_state.get('hr_aft_restow_disch',0)}, POOP: {st.session_state.get('hr_poop_restow_disch',0)}")
    st.write("🗃️ Hatch Moves")
    st.write(f"Open - FWD: {st.session_state.get('hr_hatch_fwd_open',0)}, MID: {st.session_state.get('hr_hatch_mid_open',0)}, AFT: {st.session_state.get('hr_hatch_aft_open',0)}")
    st.write(f"Close - FWD: {st.session_state.get('hr_hatch_fwd_close',0)}, MID: {st.session_state.get('hr_hatch_mid_close',0)}, AFT: {st.session_state.get('hr_hatch_aft_close',0)}")

# --- Collapsible 4-Hourly Tracker ---
with st.expander("🕓 4-Hourly Tracker Details"):
    st.write("📊 Crane Moves")
    st.write(f"Load - FWD: {st.session_state.get('fwd_load_4h',0)}, MID: {st.session_state.get('mid_load_4h',0)}, AFT: {st.session_state.get('aft_load_4h',0)}, POOP: {st.session_state.get('poop_load_4h',0)}")
    st.write(f"Discharge - FWD: {st.session_state.get('fwd_disch_4h',0)}, MID: {st.session_state.get('mid_disch_4h',0)}, AFT: {st.session_state.get('aft_disch_4h',0)}, POOP: {st.session_state.get('poop_disch_4h',0)}")
    st.write("🔄 Restows")
    st.write(f"Load - FWD: {st.session_state.get('fwd_restow_load_4h',0)}, MID: {st.session_state.get('mid_restow_load_4h',0)}, AFT: {st.session_state.get('aft_restow_load_4h',0)}, POOP: {st.session_state.get('poop_restow_load_4h',0)}")
    st.write(f"Discharge - FWD: {st.session_state.get('fwd_restow_disch_4h',0)}, MID: {st.session_state.get('mid_restow_disch_4h',0)}, AFT: {st.session_state.get('aft_restow_disch_4h',0)}, POOP: {st.session_state.get('poop_restow_disch_4h',0)}")
    st.write("🗃️ Hatch Moves")
    st.write(f"Open - FWD: {st.session_state.get('hatch_fwd_open_4h',0)}, MID: {st.session_state.get('hatch_mid_open_4h',0)}, AFT: {st.session_state.get('hatch_aft_open_4h',0)}")
    st.write(f"Close - FWD: {st.session_state.get('hatch_fwd_close_4h',0)}, MID: {st.session_state.get('hatch_mid_close_4h',0)}, AFT: {st.session_state.get('hatch_aft_close_4h',0)}")

# --- Footer ---
st.markdown("⚓ **Vessel Hourly & 4-Hourly Moves Tracker** – Built with Streamlit")
st.markdown("© 2025 All rights reserved")
