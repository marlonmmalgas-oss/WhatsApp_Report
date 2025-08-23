# Part 1/5 - Imports, constants, and loading cumulative data
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

SAVE_FILE = "vessel_report.json"
FOUR_HR_FILE = "vessel_4hr_report.json"

# --- Load or initialize cumulative hourly data ---
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

# --- Load or initialize cumulative 4-hourly data ---
if os.path.exists(FOUR_HR_FILE):
    with open(FOUR_HR_FILE, "r") as f:
        try:
            cumulative_4h = json.load(f)
        except json.JSONDecodeError:
            cumulative_4h = None
else:
    cumulative_4h = None

if cumulative_4h is None:
    cumulative_4h = {
        "fwd_load": 0, "mid_load": 0, "aft_load": 0, "poop_load": 0,
        "fwd_disch": 0, "mid_disch": 0, "aft_disch": 0, "poop_disch": 0,
        "fwd_restow_load": 0, "mid_restow_load": 0, "aft_restow_load": 0, "poop_restow_load": 0,
        "fwd_restow_disch": 0, "mid_restow_disch": 0, "aft_restow_disch": 0, "poop_restow_disch": 0,
        "fwd_hatch_open": 0, "mid_hatch_open": 0, "aft_hatch_open": 0,
        "fwd_hatch_close": 0, "mid_hatch_close": 0, "aft_hatch_close": 0,
        "last_4h_block": None
    }

# --- Timezone and date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves Tracker", layout="wide")
st.title("🛳 Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Plan & Opening Balances (Collapsible) ---
with st.expander("📊 Plan Totals & Opening Balance (Internal Only)"):
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
hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))
# Part 2/5 - Hourly Moves Input & Tracker

st.header("📋 Hourly Moves Input")

with st.expander(f"🕐 Hourly Moves Input ({hourly_time})"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Load")
        hr_fwd_load = st.number_input("FWD Load (hour)", min_value=0, value=cumulative.get("done_load", 0), key="hr_fwd_load")
        hr_mid_load = st.number_input("MID Load (hour)", min_value=0, value=cumulative.get("done_load", 0), key="hr_mid_load")
        hr_aft_load = st.number_input("AFT Load (hour)", min_value=0, value=cumulative.get("done_load", 0), key="hr_aft_load")
        hr_poop_load = st.number_input("POOP Load (hour)", min_value=0, value=cumulative.get("done_load", 0), key="hr_poop_load")

    with col2:
        st.subheader("Discharge")
        hr_fwd_disch = st.number_input("FWD Discharge (hour)", min_value=0, value=cumulative.get("done_disch", 0), key="hr_fwd_disch")
        hr_mid_disch = st.number_input("MID Discharge (hour)", min_value=0, value=cumulative.get("done_disch", 0), key="hr_mid_disch")
        hr_aft_disch = st.number_input("AFT Discharge (hour)", min_value=0, value=cumulative.get("done_disch", 0), key="hr_aft_disch")
        hr_poop_disch = st.number_input("POOP Discharge (hour)", min_value=0, value=cumulative.get("done_disch", 0), key="hr_poop_disch")

    with col3:
        st.subheader("Restow Load / Discharge & Hatch")
        hr_fwd_restow_load = st.number_input("FWD Restow Load (hour)", min_value=0, value=cumulative.get("done_restow_load", 0), key="hr_fwd_restow_load")
        hr_fwd_restow_disch = st.number_input("FWD Restow Disch (hour)", min_value=0, value=cumulative.get("done_restow_disch", 0), key="hr_fwd_restow_disch")
        hr_mid_restow_load = st.number_input("MID Restow Load (hour)", min_value=0, value=cumulative.get("done_restow_load", 0), key="hr_mid_restow_load")
        hr_mid_restow_disch = st.number_input("MID Restow Disch (hour)", min_value=0, value=cumulative.get("done_restow_disch", 0), key="hr_mid_restow_disch")
        hr_aft_restow_load = st.number_input("AFT Restow Load (hour)", min_value=0, value=cumulative.get("done_restow_load", 0), key="hr_aft_restow_load")
        hr_aft_restow_disch = st.number_input("AFT Restow Disch (hour)", min_value=0, value=cumulative.get("done_restow_disch", 0), key="hr_aft_restow_disch")
        hr_poop_restow_load = st.number_input("POOP Restow Load (hour)", min_value=0, value=cumulative.get("done_restow_load", 0), key="hr_poop_restow_load")
        hr_poop_restow_disch = st.number_input("POOP Restow Disch (hour)", min_value=0, value=cumulative.get("done_restow_disch", 0), key="hr_poop_restow_disch")

        hr_fwd_hatch_open = st.number_input("FWD Hatch Open (hour)", min_value=0, value=cumulative.get("done_hatch_open", 0), key="hr_fwd_hatch_open")
        hr_mid_hatch_open = st.number_input("MID Hatch Open (hour)", min_value=0, value=cumulative.get("done_hatch_open", 0), key="hr_mid_hatch_open")
        hr_aft_hatch_open = st.number_input("AFT Hatch Open (hour)", min_value=0, value=cumulative.get("done_hatch_open", 0), key="hr_aft_hatch_open")

        hr_fwd_hatch_close = st.number_input("FWD Hatch Close (hour)", min_value=0, value=cumulative.get("done_hatch_close", 0), key="hr_fwd_hatch_close")
        hr_mid_hatch_close = st.number_input("MID Hatch Close (hour)", min_value=0, value=cumulative.get("done_hatch_close", 0), key="hr_mid_hatch_close")
        hr_aft_hatch_close = st.number_input("AFT Hatch Close (hour)", min_value=0, value=cumulative.get("done_hatch_close", 0), key="hr_aft_hatch_close")

# --- Hourly Tracker: Update cumulative totals ---
cumulative.update({
    "done_load": hr_fwd_load + hr_mid_load + hr_aft_load + hr_poop_load,
    "done_disch": hr_fwd_disch + hr_mid_disch + hr_aft_disch + hr_poop_disch,
    "done_restow_load": hr_fwd_restow_load + hr_mid_restow_load + hr_aft_restow_load + hr_poop_restow_load,
    "done_restow_disch": hr_fwd_restow_disch + hr_mid_restow_disch + hr_aft_restow_disch + hr_poop_restow_disch,
    "done_hatch_open": hr_fwd_hatch_open + hr_mid_hatch_open + hr_aft_hatch_open,
    "done_hatch_close": hr_fwd_hatch_close + hr_mid_hatch_close + hr_aft_hatch_close,
    "last_hour": hourly_time
})

# Save updated cumulative hourly data
with open(SAVE_FILE, "w") as f:
    json.dump(cumulative, f)
    # Part 3/5 - Idle/Delays, Reset Buttons, Automatic Hour Update

st.header("⏱️ Idle / Delays")

num_idle_entries = st.number_input("Number of Idle Entries", min_value=0, value=0, key="num_idle_entries")

idle_entries = []
for i in range(num_idle_entries):
    entry = st.text_input(f"Idle Entry {i+1}", key=f"idle_{i}")
    idle_entries.append(entry)

# --- Reset Buttons ---
st.markdown("### 🔄 Reset Counters")

col_reset_hr, col_reset_4h = st.columns(2)

with col_reset_hr:
    if st.button("Reset Hourly"):
        # Reset all hourly counters
        keys_to_reset = [
            "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
            "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
            "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
            "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
            "hr_fwd_hatch_open", "hr_mid_hatch_open", "hr_aft_hatch_open",
            "hr_fwd_hatch_close", "hr_mid_hatch_close", "hr_aft_hatch_close"
        ]
        for key in keys_to_reset:
            st.session_state[key] = 0
        st.success("✅ Hourly counters reset!")
        # Advance to next hour automatically
        new_hour = (datetime.strptime(hourly_time, "%Hh%M") + timedelta(hours=1)).strftime("%Hh%M")
        st.session_state["hourly_time"] = new_hour
        st.experimental_rerun()

with col_reset_4h:
    if st.button("Reset 4-Hourly"):
        keys_4h_reset = [
            "fwd_load_4h", "mid_load_4h", "aft_load_4h", "poop_load_4h",
            "fwd_disch_4h", "mid_disch_4h", "aft_disch_4h", "poop_disch_4h",
            "fwd_restow_load_4h", "mid_restow_load_4h", "aft_restow_load_4h", "poop_restow_load_4h",
            "fwd_restow_disch_4h", "mid_restow_disch_4h", "aft_restow_disch_4h", "poop_restow_disch_4h",
            "fwd_hatch_open_4h", "mid_hatch_open_4h", "aft_hatch_open_4h",
            "fwd_hatch_close_4h", "mid_hatch_close_4h", "aft_hatch_close_4h"
        ]
        for key in keys_4h_reset:
            st.session_state[key] = 0
        st.success("✅ 4-Hourly counters reset!")
        st.experimental_rerun()

# --- Display Hourly Tracker ---
st.markdown("### 📊 Hourly Tracker")
with st.expander("View Current Hourly Totals"):
    st.write(f"Load Total: {cumulative['done_load']}")
    st.write(f"Discharge Total: {cumulative['done_disch']}")
    st.write(f"Restow Load Total: {cumulative['done_restow_load']}")
    st.write(f"Restow Discharge Total: {cumulative['done_restow_disch']}")
    st.write(f"Hatch Open Total: {cumulative['done_hatch_open']}")
    st.write(f"Hatch Close Total: {cumulative['done_hatch_close']}")
    # Part 4/5 - 4-Hourly Cumulative & WhatsApp Template

st.header("🕓 4-Hourly Summary & WhatsApp Template")

# Calculate 4-hourly cumulative totals
fwd_load_4h = st.session_state.get("fwd_load_4h", 0) + st.session_state.get("hr_fwd_load", 0)
mid_load_4h = st.session_state.get("mid_load_4h", 0) + st.session_state.get("hr_mid_load", 0)
aft_load_4h = st.session_state.get("aft_load_4h", 0) + st.session_state.get("hr_aft_load", 0)
poop_load_4h = st.session_state.get("poop_load_4h", 0) + st.session_state.get("hr_poop_load", 0)

fwd_disch_4h = st.session_state.get("fwd_disch_4h", 0) + st.session_state.get("hr_fwd_disch", 0)
mid_disch_4h = st.session_state.get("mid_disch_4h", 0) + st.session_state.get("hr_mid_disch", 0)
aft_disch_4h = st.session_state.get("aft_disch_4h", 0) + st.session_state.get("hr_aft_disch", 0)
poop_disch_4h = st.session_state.get("poop_disch_4h", 0) + st.session_state.get("hr_poop_disch", 0)

fwd_restow_load_4h = st.session_state.get("fwd_restow_load_4h", 0) + st.session_state.get("hr_fwd_restow_load", 0)
mid_restow_load_4h = st.session_state.get("mid_restow_load_4h", 0) + st.session_state.get("hr_mid_restow_load", 0)
aft_restow_load_4h = st.session_state.get("aft_restow_load_4h", 0) + st.session_state.get("hr_aft_restow_load", 0)
poop_restow_load_4h = st.session_state.get("poop_restow_load_4h", 0) + st.session_state.get("hr_poop_restow_load", 0)

fwd_restow_disch_4h = st.session_state.get("fwd_restow_disch_4h", 0) + st.session_state.get("hr_fwd_restow_disch", 0)
mid_restow_disch_4h = st.session_state.get("mid_restow_disch_4h", 0) + st.session_state.get("hr_mid_restow_disch", 0)
aft_restow_disch_4h = st.session_state.get("aft_restow_disch_4h", 0) + st.session_state.get("hr_aft_restow_disch", 0)
poop_restow_disch_4h = st.session_state.get("poop_restow_disch_4h", 0) + st.session_state.get("hr_poop_restow_disch", 0)

fwd_hatch_open_4h = st.session_state.get("fwd_hatch_open_4h", 0) + st.session_state.get("hr_fwd_hatch_open", 0)
mid_hatch_open_4h = st.session_state.get("mid_hatch_open_4h", 0) + st.session_state.get("hr_mid_hatch_open", 0)
aft_hatch_open_4h = st.session_state.get("aft_hatch_open_4h", 0) + st.session_state.get("hr_aft_hatch_open", 0)

fwd_hatch_close_4h = st.session_state.get("fwd_hatch_close_4h", 0) + st.session_state.get("hr_fwd_hatch_close", 0)
mid_hatch_close_4h = st.session_state.get("mid_hatch_close_4h", 0) + st.session_state.get("hr_mid_hatch_close", 0)
aft_hatch_close_4h = st.session_state.get("aft_hatch_close_4h", 0) + st.session_state.get("hr_aft_hatch_close", 0)

# Update session_state
st.session_state.update({
    "fwd_load_4h": fwd_load_4h, "mid_load_4h": mid_load_4h, "aft_load_4h": aft_load_4h, "poop_load_4h": poop_load_4h,
    "fwd_disch_4h": fwd_disch_4h, "mid_disch_4h": mid_disch_4h, "aft_disch_4h": aft_disch_4h, "poop_disch_4h": poop_disch_4h,
    "fwd_restow_load_4h": fwd_restow_load_4h, "mid_restow_load_4h": mid_restow_load_4h, "aft_restow_load_4h": aft_restow_load_4h, "poop_restow_load_4h": poop_restow_load_4h,
    "fwd_restow_disch_4h": fwd_restow_disch_4h, "mid_restow_disch_4h": mid_restow_disch_4h, "aft_restow_disch_4h": aft_restow_disch_4h, "poop_restow_disch_4h": poop_restow_disch_4h,
    "fwd_hatch_open_4h": fwd_hatch_open_4h, "mid_hatch_open_4h": mid_hatch_open_4h, "aft_hatch_open_4h": aft_hatch_open_4h,
    "fwd_hatch_close_4h": fwd_hatch_close_4h, "mid_hatch_close_4h": mid_hatch_close_4h, "aft_hatch_close_4h": aft_hatch_close_4h
})

# --- WhatsApp Template Generation ---
st.markdown("### 📱 4-Hourly WhatsApp Template")
hourly_time_end_4h = (datetime.strptime(hourly_time, "%Hh%M") + timedelta(hours=4)).strftime("%Hh%M")

whatsapp_msg_4h = f"""
*4-Hourly Report 🕓*
Date: {datetime.today().strftime('%Y-%m-%d')}
Period: {hourly_time} - {hourly_time_end_4h}

*LOAD*:
FWD: {fwd_load_4h} | MID: {mid_load_4h} | AFT: {aft_load_4h} | POOP: {poop_load_4h}
*DISCHARGE*:
FWD: {fwd_disch_4h} | MID: {mid_disch_4h} | AFT: {aft_disch_4h} | POOP: {poop_disch_4h}
*RESTOW LOAD*:
FWD: {fwd_restow_load_4h} | MID: {mid_restow_load_4h} | AFT: {aft_restow_load_4h} | POOP: {poop_restow_load_4h}
*RESTOW DISCHARGE*:
FWD: {fwd_restow_disch_4h} | MID: {mid_restow_disch_4h} | AFT: {aft_restow_disch_4h} | POOP: {poop_restow_disch_4h}
*HATCH COVER OPEN*:
FWD: {fwd_hatch_open_4h} | MID: {mid_hatch_open_4h} | AFT: {aft_hatch_open_4h}
*HATCH COVER CLOSE*:
FWD: {fwd_hatch_close_4h} | MID: {mid_hatch_close_4h} | AFT: {aft_hatch_close_4h}
"""

st.text_area("WhatsApp 4-Hourly Message", value=whatsapp_msg_4h, height=400)
# Part 5/5 - Send WhatsApp, Reset Buttons, Date Picker, Final Layout

st.header("📤 Send Report & Reset")

# --- Date Picker ---
report_date = st.date_input("Select Report Date", datetime.today())
report_date_str = report_date.strftime("%Y-%m-%d")

# --- WhatsApp Number / Group ---
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code)", "")
whatsapp_group = st.text_input("Or enter WhatsApp Group Link (optional)", "")

# --- Send WhatsApp Functionality ---
def send_whatsapp(msg, number=None, group=None):
    if group:
        st.success(f"Message ready to send to group: {group}")
    elif number:
        st.success(f"Message ready to send to number: {number}")
    else:
        st.warning("Please enter a number or group link to send message.")

st.button("Send Hourly WhatsApp", on_click=lambda: send_whatsapp(whatsapp_msg_hourly, whatsapp_number, whatsapp_group))
st.button("Send 4-Hourly WhatsApp", on_click=lambda: send_whatsapp(whatsapp_msg_4h, whatsapp_number, whatsapp_group))

# --- Reset Buttons ---
def reset_hourly():
    keys = ["hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
            "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
            "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
            "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
            "hr_fwd_hatch_open","hr_mid_hatch_open","hr_aft_hatch_open",
            "hr_fwd_hatch_close","hr_mid_hatch_close","hr_aft_hatch_close"]
    for k in keys:
        st.session_state[k] = 0
    st.success("Hourly counts reset successfully!")

def reset_4hourly():
    keys_4h = ["fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
               "fwd_disch_4h","mid_disch_4h","aft_disch_4h","poop_disch_4h",
               "fwd_restow_load_4h","mid_restow_load_4h","aft_restow_load_4h","poop_restow_load_4h",
               "fwd_restow_disch_4h","mid_restow_disch_4h","aft_restow_disch_4h","poop_restow_disch_4h",
               "fwd_hatch_open_4h","mid_hatch_open_4h","aft_hatch_open_4h",
               "fwd_hatch_close_4h","mid_hatch_close_4h","aft_hatch_close_4h"]
    for k in keys_4h:
        st.session_state[k] = 0
    st.success("4-Hourly counts reset successfully!")

st.button("Reset Hourly Counts", on_click=reset_hourly)
st.button("Reset 4-Hourly Counts", on_click=reset_4hourly)

# --- Auto-increment hourly time ---
try:
    next_hour_dt = datetime.strptime(hourly_time, "%Hh%M") + timedelta(hours=1)
    st.session_state["hourly_time"] = next_hour_dt.strftime("%Hh%M")
except Exception:
    st.session_state["hourly_time"] = "08h00"  # default fallback

# --- Collapsible 4-Hourly Tracker ---
with st.expander("4-Hourly Tracker Details"):
    st.write({
        "LOAD": {"FWD": fwd_load_4h, "MID": mid_load_4h, "AFT": aft_load_4h, "POOP": poop_load_4h},
        "DISCHARGE": {"FWD": fwd_disch_4h, "MID": mid_disch_4h, "AFT": aft_disch_4h, "POOP": poop_disch_4h},
        "RESTOW LOAD": {"FWD": fwd_restow_load_4h, "MID": mid_restow_load_4h, "AFT": aft_restow_load_4h, "POOP": poop_restow_load_4h},
        "RESTOW DISCHARGE": {"FWD": fwd_restow_disch_4h, "MID": mid_restow_disch_4h, "AFT": aft_restow_disch_4h, "POOP": poop_restow_disch_4h},
        "HATCH OPEN": {"FWD": fwd_hatch_open_4h, "MID": mid_hatch_open_4h, "AFT": aft_hatch_open_4h},
        "HATCH CLOSE": {"FWD": fwd_hatch_close_4h, "MID": mid_hatch_close_4h, "AFT": aft_hatch_close_4h}
    })

st.success("App fully loaded! Hourly and 4-hourly counts are synced and ready for reporting.")
