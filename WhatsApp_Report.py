import streamlit as st
from datetime import datetime, timedelta

# ----------------------------
# INITIAL SETUP & SESSION STATE
# ----------------------------
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves Tracker", layout="wide")

# Initialize session state for all hourly counters if not already present
counters = [
    "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_po_load",
    "hr_fwd_discharge", "hr_mid_discharge", "hr_aft_discharge", "hr_po_discharge",
    "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_po_restow_load",
    "hr_fwd_restow_discharge", "hr_mid_restow_discharge", "hr_aft_restow_discharge", "hr_po_restow_discharge",
    "hr_fwd_hatch", "hr_mid_hatch", "hr_aft_hatch"
]

for counter in counters:
    if counter not in st.session_state:
        st.session_state[counter] = 0

# Initialize 4-hourly totals if not already present
totals_4h = [
    "tot_fwd_load_4h", "tot_mid_load_4h", "tot_aft_load_4h", "tot_po_load_4h",
    "tot_fwd_discharge_4h", "tot_mid_discharge_4h", "tot_aft_discharge_4h", "tot_po_discharge_4h",
    "tot_fwd_restow_load_4h", "tot_mid_restow_load_4h", "tot_aft_restow_load_4h", "tot_po_restow_load_4h",
    "tot_fwd_restow_discharge_4h", "tot_mid_restow_discharge_4h", "tot_aft_restow_discharge_4h", "tot_po_restow_discharge_4h",
    "tot_fwd_hatch_4h", "tot_mid_hatch_4h", "tot_aft_hatch_4h"
]

for total in totals_4h:
    if total not in st.session_state:
        st.session_state[total] = 0

# Default hourly time selection
hours_list = [f"{h:02d}h00" for h in range(24)]
default_hour = datetime.now().hour
if "hour_index" not in st.session_state:
    st.session_state["hour_index"] = default_hour
    # ----------------------------
# VESSEL INFORMATION
# ----------------------------
st.header("🚢 Vessel Info")
vessel_name = st.text_input("Vessel Name", value=st.session_state.get("vessel_name", ""))
st.session_state["vessel_name"] = vessel_name

berthed_date = st.date_input("Berthed Date", value=st.session_state.get("berthed_date", datetime.today()))
st.session_state["berthed_date"] = berthed_date

# ----------------------------
# HOURLY TIME SELECTION
# ----------------------------
hourly_time = st.selectbox(
    "⏱ Select Hourly Time",
    options=hours_list,
    index=st.session_state["hour_index"]
)
st.session_state["hour_index"] = hours_list.index(hourly_time)

# Automatically set next hour for convenience
next_hour_index = (st.session_state["hour_index"] + 1) % 24
hourly_time_end = hours_list[next_hour_index]

# ----------------------------
# HOURLY MOVES INPUT
# ----------------------------
st.subheader("🕐 Hourly Moves Input")

with st.expander("Crane Moves"):
    st.number_input("FWD Load", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
    st.number_input("MID Load", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
    st.number_input("AFT Load", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
    st.number_input("POOP Load", min_value=0, value=st.session_state["hr_po_load"], key="hr_po_load")

    st.number_input("FWD Discharge", min_value=0, value=st.session_state["hr_fwd_discharge"], key="hr_fwd_discharge")
    st.number_input("MID Discharge", min_value=0, value=st.session_state["hr_mid_discharge"], key="hr_mid_discharge")
    st.number_input("AFT Discharge", min_value=0, value=st.session_state["hr_aft_discharge"], key="hr_aft_discharge")
    st.number_input("POOP Discharge", min_value=0, value=st.session_state["hr_po_discharge"], key="hr_po_discharge")

with st.expander("Restow Moves"):
    st.number_input("FWD Restow Load", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
    st.number_input("MID Restow Load", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
    st.number_input("AFT Restow Load", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
    st.number_input("POOP Restow Load", min_value=0, value=st.session_state["hr_po_restow_load"], key="hr_po_restow_load")

    st.number_input("FWD Restow Discharge", min_value=0, value=st.session_state["hr_fwd_restow_discharge"], key="hr_fwd_restow_discharge")
    st.number_input("MID Restow Discharge", min_value=0, value=st.session_state["hr_mid_restow_discharge"], key="hr_mid_restow_discharge")
    st.number_input("AFT Restow Discharge", min_value=0, value=st.session_state["hr_aft_restow_discharge"], key="hr_aft_restow_discharge")
    st.number_input("POOP Restow Discharge", min_value=0, value=st.session_state["hr_po_restow_discharge"], key="hr_po_restow_discharge")

with st.expander("Hatch Covers Open/Close"):
    st.number_input("FWD Hatch Covers", min_value=0, value=st.session_state["hr_fwd_hatch"], key="hr_fwd_hatch")
    st.number_input("MID Hatch Covers", min_value=0, value=st.session_state["hr_mid_hatch"], key="hr_mid_hatch")
    st.number_input("AFT Hatch Covers", min_value=0, value=st.session_state["hr_aft_hatch"], key="hr_aft_hatch")

# ----------------------------
# IDLE / DELAYS
# ----------------------------
st.subheader("⏳ Idle / Delays")
num_idle_entries = st.number_input("Number of Idle Entries", min_value=0, value=st.session_state.get("num_idle_entries", 0), key="num_idle_entries")
st.session_state["num_idle_entries"] = num_idle_entries

idle_entries = []
for i in range(num_idle_entries):
    idle_entries.append(st.text_input(f"Idle Entry {i+1}", value="", key=f"idle_{i}"))
    # ----------------------------
# 4-HOURLY CUMULATIVE TRACKER
# ----------------------------
st.header("🕓 4-Hourly Totals Tracker")

# Function to sum hourly totals for the past 4 hours (or manual input)
def get_4h_total(hour_keys):
    return sum([st.session_state.get(k, 0) for k in hour_keys])

with st.expander("Crane Moves 4-Hour Totals"):
    fwd_load_4h = get_4h_total(["hr_fwd_load", "hr_fwd_load_prev1", "hr_fwd_load_prev2", "hr_fwd_load_prev3"])
    mid_load_4h = get_4h_total(["hr_mid_load", "hr_mid_load_prev1", "hr_mid_load_prev2", "hr_mid_load_prev3"])
    aft_load_4h = get_4h_total(["hr_aft_load", "hr_aft_load_prev1", "hr_aft_load_prev2", "hr_aft_load_prev3"])
    po_load_4h = get_4h_total(["hr_po_load", "hr_po_load_prev1", "hr_po_load_prev2", "hr_po_load_prev3"])

    fwd_dis_4h = get_4h_total(["hr_fwd_discharge", "hr_fwd_discharge_prev1", "hr_fwd_discharge_prev2", "hr_fwd_discharge_prev3"])
    mid_dis_4h = get_4h_total(["hr_mid_discharge", "hr_mid_discharge_prev1", "hr_mid_discharge_prev2", "hr_mid_discharge_prev3"])
    aft_dis_4h = get_4h_total(["hr_aft_discharge", "hr_aft_discharge_prev1", "hr_aft_discharge_prev2", "hr_aft_discharge_prev3"])
    po_dis_4h = get_4h_total(["hr_po_discharge", "hr_po_discharge_prev1", "hr_po_discharge_prev2", "hr_po_discharge_prev3"])

    st.write(f"FWD Load 4H: {fwd_load_4h}")
    st.write(f"MID Load 4H: {mid_load_4h}")
    st.write(f"AFT Load 4H: {aft_load_4h}")
    st.write(f"POOP Load 4H: {po_load_4h}")

    st.write(f"FWD Discharge 4H: {fwd_dis_4h}")
    st.write(f"MID Discharge 4H: {mid_dis_4h}")
    st.write(f"AFT Discharge 4H: {aft_dis_4h}")
    st.write(f"POOP Discharge 4H: {po_dis_4h}")

with st.expander("Restow 4-Hour Totals"):
    fwd_restow_load_4h = get_4h_total(["hr_fwd_restow_load", "hr_fwd_restow_load_prev1", "hr_fwd_restow_load_prev2", "hr_fwd_restow_load_prev3"])
    mid_restow_load_4h = get_4h_total(["hr_mid_restow_load", "hr_mid_restow_load_prev1", "hr_mid_restow_load_prev2", "hr_mid_restow_load_prev3"])
    aft_restow_load_4h = get_4h_total(["hr_aft_restow_load", "hr_aft_restow_load_prev1", "hr_aft_restow_load_prev2", "hr_aft_restow_load_prev3"])
    po_restow_load_4h = get_4h_total(["hr_po_restow_load", "hr_po_restow_load_prev1", "hr_po_restow_load_prev2", "hr_po_restow_load_prev3"])

    fwd_restow_dis_4h = get_4h_total(["hr_fwd_restow_discharge", "hr_fwd_restow_discharge_prev1", "hr_fwd_restow_discharge_prev2", "hr_fwd_restow_discharge_prev3"])
    mid_restow_dis_4h = get_4h_total(["hr_mid_restow_discharge", "hr_mid_restow_discharge_prev1", "hr_mid_restow_discharge_prev2", "hr_mid_restow_discharge_prev3"])
    aft_restow_dis_4h = get_4h_total(["hr_aft_restow_discharge", "hr_aft_restow_discharge_prev1", "hr_aft_restow_discharge_prev2", "hr_aft_restow_discharge_prev3"])
    po_restow_dis_4h = get_4h_total(["hr_po_restow_discharge", "hr_po_restow_discharge_prev1", "hr_po_restow_discharge_prev2", "hr_po_restow_discharge_prev3"])

    st.write(f"FWD Restow Load 4H: {fwd_restow_load_4h}")
    st.write(f"MID Restow Load 4H: {mid_restow_load_4h}")
    st.write(f"AFT Restow Load 4H: {aft_restow_load_4h}")
    st.write(f"POOP Restow Load 4H: {po_restow_load_4h}")

    st.write(f"FWD Restow Discharge 4H: {fwd_restow_dis_4h}")
    st.write(f"MID Restow Discharge 4H: {mid_restow_dis_4h}")
    st.write(f"AFT Restow Discharge 4H: {aft_restow_dis_4h}")
    st.write(f"POOP Restow Discharge 4H: {po_restow_dis_4h}")

# ----------------------------
# RESET BUTTONS
# ----------------------------
st.subheader("🔄 Reset Counters")

if st.button("Reset Hourly Counts"):
    for key in [
        "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_po_load",
        "hr_fwd_discharge", "hr_mid_discharge", "hr_aft_discharge", "hr_po_discharge",
        "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_po_restow_load",
        "hr_fwd_restow_discharge", "hr_mid_restow_discharge", "hr_aft_restow_discharge", "hr_po_restow_discharge",
        "hr_fwd_hatch", "hr_mid_hatch", "hr_aft_hatch"
    ]:
        st.session_state[key] = 0
    st.experimental_rerun()

if st.button("Reset 4-Hourly Counts"):
    for key in [
        "hr_fwd_load_prev1","hr_fwd_load_prev2","hr_fwd_load_prev3",
        "hr_mid_load_prev1","hr_mid_load_prev2","hr_mid_load_prev3",
        "hr_aft_load_prev1","hr_aft_load_prev2","hr_aft_load_prev3",
        "hr_po_load_prev1","hr_po_load_prev2","hr_po_load_prev3",
        # ... Repeat for all discharge, restow load/discharge, hatch covers
    ]:
        st.session_state[key] = 0
    st.experimental_rerun()
    # ----------------------------
# WHATSAPP REPORT TEMPLATES
# ----------------------------
st.header("📱 WhatsApp Report Generator")

# Hourly WhatsApp Template
with st.expander("Hourly Report Template"):
    hourly_report = f"""
    *Vessel: {st.session_state.get('vessel_name', 'N/A')}*
    *Date: {st.session_state.get('report_date', datetime.date.today())}*
    🕓 Hour: {st.session_state.get('hourly_time', '08:00 - 09:00')}
    
    *Crane Moves*
    ─────────────
    FWD Load: {st.session_state.get('hr_fwd_load', 0)}
    MID Load: {st.session_state.get('hr_mid_load', 0)}
    AFT Load: {st.session_state.get('hr_aft_load', 0)}
    POOP Load: {st.session_state.get('hr_po_load', 0)}
    
    FWD Discharge: {st.session_state.get('hr_fwd_discharge', 0)}
    MID Discharge: {st.session_state.get('hr_mid_discharge', 0)}
    AFT Discharge: {st.session_state.get('hr_aft_discharge', 0)}
    POOP Discharge: {st.session_state.get('hr_po_discharge', 0)}
    
    *Restows*
    ─────────
    FWD Load: {st.session_state.get('hr_fwd_restow_load', 0)}
    MID Load: {st.session_state.get('hr_mid_restow_load', 0)}
    AFT Load: {st.session_state.get('hr_aft_restow_load', 0)}
    POOP Load: {st.session_state.get('hr_po_restow_load', 0)}
    
    FWD Discharge: {st.session_state.get('hr_fwd_restow_discharge', 0)}
    MID Discharge: {st.session_state.get('hr_mid_restow_discharge', 0)}
    AFT Discharge: {st.session_state.get('hr_aft_restow_discharge', 0)}
    POOP Discharge: {st.session_state.get('hr_po_restow_discharge', 0)}
    
    *Hatch Covers Open/Close*
    ─────────────
    FWD: {st.session_state.get('hr_fwd_hatch', 0)}
    MID: {st.session_state.get('hr_mid_hatch', 0)}
    AFT: {st.session_state.get('hr_aft_hatch', 0)}
    """
    st.text_area("Copy Hourly Report", value=hourly_report, height=400)

# 4-Hourly WhatsApp Template
with st.expander("4-Hourly Report Template"):
    four_hour_report = f"""
    *Vessel: {st.session_state.get('vessel_name', 'N/A')}*
    *Date: {st.session_state.get('report_date', datetime.date.today())}*
    🕓 Period: {st.session_state.get('hourly_time_start_4h', '08:00')} - {st.session_state.get('hourly_time_end_4h', '12:00')}
    
    *Crane Moves 4H Totals*
    ─────────────
    FWD Load: {fwd_load_4h}
    MID Load: {mid_load_4h}
    AFT Load: {aft_load_4h}
    POOP Load: {po_load_4h}
    
    FWD Discharge: {fwd_dis_4h}
    MID Discharge: {mid_dis_4h}
    AFT Discharge: {aft_dis_4h}
    POOP Discharge: {po_dis_4h}
    
    *Restows 4H Totals*
    ─────────
    FWD Load: {fwd_restow_load_4h}
    MID Load: {mid_restow_load_4h}
    AFT Load: {aft_restow_load_4h}
    POOP Load: {po_restow_load_4h}
    
    FWD Discharge: {fwd_restow_dis_4h}
    MID Discharge: {mid_restow_dis_4h}
    AFT Discharge: {aft_restow_dis_4h}
    POOP Discharge: {po_restow_dis_4h}
    
    *Hatch Covers Open/Close 4H*
    ─────────────
    FWD: {st.session_state.get('hr_fwd_hatch_4h', 0)}
    MID: {st.session_state.get('hr_mid_hatch_4h', 0)}
    AFT: {st.session_state.get('hr_aft_hatch_4h', 0)}
    """
    st.text_area("Copy 4-Hourly Report", value=four_hour_report, height=400)

# Send to WhatsApp section
st.subheader("Send Report to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)")
group_link = st.text_input("Or enter WhatsApp Group Link (optional)")
st.button("Send Hourly Report")
st.button("Send 4-Hourly Report")
# ----------------------------
# HOURLY TIME & DATE MANAGEMENT
# ----------------------------
st.header("⏱ Report Time & Date")

# Report date
if "report_date" not in st.session_state:
    st.session_state["report_date"] = datetime.date.today()

report_date = st.date_input("Select Report Date", value=st.session_state["report_date"])
st.session_state["report_date"] = report_date

# Hourly time selector
hours_list = [f"{h:02d}:00 - {h+1:02d}:00" for h in range(24)]
if "hourly_time_index" not in st.session_state:
    st.session_state["hourly_time_index"] = 8  # Default 08:00-09:00

hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=st.session_state["hourly_time_index"])
st.session_state["hourly_time"] = hourly_time

# Update hourly index automatically when generating hourly template
if st.button("Generate Hourly Template"):
    if st.session_state["hourly_time_index"] < 23:
        st.session_state["hourly_time_index"] += 1
    else:
        st.session_state["hourly_time_index"] = 0
    st.experimental_rerun()

# ----------------------------
# RESET HOURLY & 4-HOURLY COUNTS
# ----------------------------
def reset_hourly_counts():
    keys = [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_po_load",
        "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_po_discharge",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_po_restow_load",
        "hr_fwd_restow_discharge","hr_mid_restow_discharge","hr_aft_restow_discharge","hr_po_restow_discharge",
        "hr_fwd_hatch","hr_mid_hatch","hr_aft_hatch"
    ]
    for k in keys:
        st.session_state[k] = 0

def reset_4hourly_counts():
    keys_4h = [
        "fwd_load_4h","mid_load_4h","aft_load_4h","po_load_4h",
        "fwd_dis_4h","mid_dis_4h","aft_dis_4h","po_dis_4h",
        "fwd_restow_load_4h","mid_restow_load_4h","aft_restow_load_4h","po_restow_load_4h",
        "fwd_restow_dis_4h","mid_restow_dis_4h","aft_restow_dis_4h","po_restow_dis_4h",
        "hr_fwd_hatch_4h","hr_mid_hatch_4h","hr_aft_hatch_4h"
    ]
    for k in keys_4h:
        st.session_state[k] = 0

st.button("Reset Hourly Counts", on_click=reset_hourly_counts)
st.button("Reset 4-Hourly Counts", on_click=reset_4hourly_counts)
