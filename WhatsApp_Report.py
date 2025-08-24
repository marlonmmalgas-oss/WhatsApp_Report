import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json

# --------------------------
# INITIALIZATION
# --------------------------
if "hr_fwd_load" not in st.session_state:
    # Crane Moves - Load
    st.session_state["hr_fwd_load"] = 0
    st.session_state["hr_mid_load"] = 0
    st.session_state["hr_aft_load"] = 0
    st.session_state["hr_poop_load"] = 0
    # Crane Moves - Discharge
    st.session_state["hr_fwd_discharge"] = 0
    st.session_state["hr_mid_discharge"] = 0
    st.session_state["hr_aft_discharge"] = 0
    st.session_state["hr_poop_discharge"] = 0
    # Restow Moves - Load
    st.session_state["hr_fwd_restow_load"] = 0
    st.session_state["hr_mid_restow_load"] = 0
    st.session_state["hr_aft_restow_load"] = 0
    st.session_state["hr_poop_restow_load"] = 0
    # Restow Moves - Discharge
    st.session_state["hr_fwd_restow_discharge"] = 0
    st.session_state["hr_mid_restow_discharge"] = 0
    st.session_state["hr_aft_restow_discharge"] = 0
    st.session_state["hr_poop_restow_discharge"] = 0
    # Hatch Covers
    st.session_state["hr_fwd_hatch"] = 0
    st.session_state["hr_mid_hatch"] = 0
    st.session_state["hr_aft_hatch"] = 0
    # Idle Entries
    st.session_state["num_idle_entries"] = 0
    st.session_state["idle_entries"] = []

# --------------------------
# DATE & TIME
# --------------------------
today = datetime.today()
st.session_state["report_date"] = today.strftime("%Y-%m-%d")
st.date_input("Select Report Date", key="report_date_picker", value=today)

# --------------------------
# VESSEL INFO
# --------------------------
st.header("🚢 Vessel Info")
st.session_state["vessel_name"] = st.text_input(
    "Vessel Name",
    value=st.session_state.get("vessel_name", ""),
    key="vessel_name"
)
st.session_state["berthed_date"] = st.date_input(
    "Berthed Date",
    value=st.session_state.get("berthed_date", today),
    key="berthed_date"
)
st.session_state["plan_totals"] = st.number_input(
    "Plan Totals & Opening Balance",
    min_value=0,
    value=st.session_state.get("plan_totals", 0),
    key="plan_totals"
)

# --------------------------
# HOURLY TIME SELECTION
# --------------------------
hours_list = [f"{h:02d}:00" for h in range(24)]
default_hour = datetime.now().hour
st.session_state["hourly_time"] = st.selectbox(
    "⏱ Select Hourly Time",
    options=hours_list,
    index=hours_list.index(st.session_state.get("hourly_time", f"{default_hour:02d}:00"))
)
# --------------------------
# HOURLY MOVES INPUT
# --------------------------
st.header("📊 Hourly Moves Input")

# --------------------------
# CRANE MOVES
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.session_state["hr_fwd_load"] = st.number_input(
            "FWD Load (hour)", min_value=0,
            value=st.session_state["hr_fwd_load"],
            key="hr_fwd_load"
        )
        st.session_state["hr_mid_load"] = st.number_input(
            "MID Load (hour)", min_value=0,
            value=st.session_state["hr_mid_load"],
            key="hr_mid_load"
        )
        st.session_state["hr_aft_load"] = st.number_input(
            "AFT Load (hour)", min_value=0,
            value=st.session_state["hr_aft_load"],
            key="hr_aft_load"
        )
        st.session_state["hr_poop_load"] = st.number_input(
            "POOP Load (hour)", min_value=0,
            value=st.session_state["hr_poop_load"],
            key="hr_poop_load"
        )

    with st.expander("📦 Discharge"):
        st.session_state["hr_fwd_discharge"] = st.number_input(
            "FWD Discharge (hour)", min_value=0,
            value=st.session_state["hr_fwd_discharge"],
            key="hr_fwd_discharge"
        )
        st.session_state["hr_mid_discharge"] = st.number_input(
            "MID Discharge (hour)", min_value=0,
            value=st.session_state["hr_mid_discharge"],
            key="hr_mid_discharge"
        )
        st.session_state["hr_aft_discharge"] = st.number_input(
            "AFT Discharge (hour)", min_value=0,
            value=st.session_state["hr_aft_discharge"],
            key="hr_aft_discharge"
        )
        st.session_state["hr_poop_discharge"] = st.number_input(
            "POOP Discharge (hour)", min_value=0,
            value=st.session_state["hr_poop_discharge"],
            key="hr_poop_discharge"
        )

# --------------------------
# RESTOW MOVES
# --------------------------
with st.expander("🔄 Restow Moves"):
    with st.expander("📦 Load"):
        st.session_state["hr_fwd_restow_load"] = st.number_input(
            "FWD Restow Load (hour)", min_value=0,
            value=st.session_state["hr_fwd_restow_load"],
            key="hr_fwd_restow_load"
        )
        st.session_state["hr_mid_restow_load"] = st.number_input(
            "MID Restow Load (hour)", min_value=0,
            value=st.session_state["hr_mid_restow_load"],
            key="hr_mid_restow_load"
        )
        st.session_state["hr_aft_restow_load"] = st.number_input(
            "AFT Restow Load (hour)", min_value=0,
            value=st.session_state["hr_aft_restow_load"],
            key="hr_aft_restow_load"
        )
        st.session_state["hr_poop_restow_load"] = st.number_input(
            "POOP Restow Load (hour)", min_value=0,
            value=st.session_state["hr_poop_restow_load"],
            key="hr_poop_restow_load"
        )

    with st.expander("📦 Discharge"):
        st.session_state["hr_fwd_restow_discharge"] = st.number_input(
            "FWD Restow Discharge (hour)", min_value=0,
            value=st.session_state["hr_fwd_restow_discharge"],
            key="hr_fwd_restow_discharge"
        )
        st.session_state["hr_mid_restow_discharge"] = st.number_input(
            "MID Restow Discharge (hour)", min_value=0,
            value=st.session_state["hr_mid_restow_discharge"],
            key="hr_mid_restow_discharge"
        )
        st.session_state["hr_aft_restow_discharge"] = st.number_input(
            "AFT Restow Discharge (hour)", min_value=0,
            value=st.session_state["hr_aft_restow_discharge"],
            key="hr_aft_restow_discharge"
        )
        st.session_state["hr_poop_restow_discharge"] = st.number_input(
            "POOP Restow Discharge (hour)", min_value=0,
            value=st.session_state["hr_poop_restow_discharge"],
            key="hr_poop_restow_discharge"
        )

# --------------------------
# HATCH COVERS
# --------------------------
with st.expander("🛡️ Hatch Covers Open & Close"):
    st.session_state["hr_fwd_hatch"] = st.number_input(
        "FWD Hatch Open/Close (hour)", min_value=0,
        value=st.session_state["hr_fwd_hatch"], key="hr_fwd_hatch"
    )
    st.session_state["hr_mid_hatch"] = st.number_input(
        "MID Hatch Open/Close (hour)", min_value=0,
        value=st.session_state["hr_mid_hatch"], key="hr_mid_hatch"
    )
    st.session_state["hr_aft_hatch"] = st.number_input(
        "AFT Hatch Open/Close (hour)", min_value=0,
        value=st.session_state["hr_aft_hatch"], key="hr_aft_hatch"
    )

# --------------------------
# IDLE ENTRIES
# --------------------------
st.header("⏸️ Idle / Delays")
with st.expander("🛑 Idle Entries"):
    num_idle_entries = st.number_input(
        "Number of Idle Entries",
        min_value=0,
        value=st.session_state.get("num_idle_entries", 0),
        key="num_idle_entries"
    )
    idle_entries = []
    for i in range(num_idle_entries):
        entry = st.text_input(f"Idle Entry {i+1}", key=f"idle_{i}")
        idle_entries.append(entry)
    st.session_state["idle_entries"] = idle_entries
    # --------------------------
# HOURLY TOTALS TRACKER
# --------------------------
st.header("🧮 Hourly Totals Tracker")
with st.expander("View Hourly Totals"):
    st.write("📦 Crane Load Totals:")
    st.write(f"FWD: {st.session_state['hr_fwd_load']}")
    st.write(f"MID: {st.session_state['hr_mid_load']}")
    st.write(f"AFT: {st.session_state['hr_aft_load']}")
    st.write(f"POOP: {st.session_state['hr_poop_load']}")

    st.write("📦 Crane Discharge Totals:")
    st.write(f"FWD: {st.session_state['hr_fwd_discharge']}")
    st.write(f"MID: {st.session_state['hr_mid_discharge']}")
    st.write(f"AFT: {st.session_state['hr_aft_discharge']}")
    st.write(f"POOP: {st.session_state['hr_poop_discharge']}")

    st.write("🔄 Restow Load Totals:")
    st.write(f"FWD: {st.session_state['hr_fwd_restow_load']}")
    st.write(f"MID: {st.session_state['hr_mid_restow_load']}")
    st.write(f"AFT: {st.session_state['hr_aft_restow_load']}")
    st.write(f"POOP: {st.session_state['hr_poop_restow_load']}")

    st.write("🔄 Restow Discharge Totals:")
    st.write(f"FWD: {st.session_state['hr_fwd_restow_discharge']}")
    st.write(f"MID: {st.session_state['hr_mid_restow_discharge']}")
    st.write(f"AFT: {st.session_state['hr_aft_restow_discharge']}")
    st.write(f"POOP: {st.session_state['hr_poop_restow_discharge']}")

    st.write("🛡️ Hatch Covers Totals:")
    st.write(f"FWD: {st.session_state['hr_fwd_hatch']}")
    st.write(f"MID: {st.session_state['hr_mid_hatch']}")
    st.write(f"AFT: {st.session_state['hr_aft_hatch']}")

# --------------------------
# AUTOMATIC HOUR INCREMENT
# --------------------------
hours_list = [f"{h:02d}:00" for h in range(24)]
default_hour = datetime.now().hour
if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = hours_list[default_hour]

def next_hour_label(current_label):
    idx = hours_list.index(current_label)
    return hours_list[(idx + 1) % len(hours_list)]

def on_generate_hourly():
    st.session_state["hourly_time"] = next_hour_label(st.session_state["hourly_time"])
    st.experimental_rerun()

st.button("✅ Generate Hourly Template", on_click=on_generate_hourly)

# --------------------------
# 4-HOURLY AGGREGATION TRACKER
# --------------------------
st.header("📊 4-Hourly Totals")
with st.expander("View 4-Hourly Aggregated Totals"):
    # Compute 4-hour totals (load & discharge)
    st.session_state["fwd_load_4h"] = st.session_state["hr_fwd_load"] + st.session_state.get("fwd_load_4h",0)
    st.session_state["mid_load_4h"] = st.session_state["hr_mid_load"] + st.session_state.get("mid_load_4h",0)
    st.session_state["aft_load_4h"] = st.session_state["hr_aft_load"] + st.session_state.get("aft_load_4h",0)
    st.session_state["poop_load_4h"] = st.session_state["hr_poop_load"] + st.session_state.get("poop_load_4h",0)

    st.session_state["fwd_discharge_4h"] = st.session_state["hr_fwd_discharge"] + st.session_state.get("fwd_discharge_4h",0)
    st.session_state["mid_discharge_4h"] = st.session_state["hr_mid_discharge"] + st.session_state.get("mid_discharge_4h",0)
    st.session_state["aft_discharge_4h"] = st.session_state["hr_aft_discharge"] + st.session_state.get("aft_discharge_4h",0)
    st.session_state["poop_discharge_4h"] = st.session_state["hr_poop_discharge"] + st.session_state.get("poop_discharge_4h",0)

    # Restow 4-hour totals
    st.session_state["restow_load_4h"] = (
        st.session_state["hr_fwd_restow_load"] +
        st.session_state["hr_mid_restow_load"] +
        st.session_state["hr_aft_restow_load"] +
        st.session_state["hr_poop_restow_load"]
    )
    st.session_state["restow_discharge_4h"] = (
        st.session_state["hr_fwd_restow_discharge"] +
        st.session_state["hr_mid_restow_discharge"] +
        st.session_state["hr_aft_restow_discharge"] +
        st.session_state["hr_poop_restow_discharge"]
    )

    # Hatch covers 4-hour total
    st.session_state["hatch_4h"] = (
        st.session_state["hr_fwd_hatch"] +
        st.session_state["hr_mid_hatch"] +
        st.session_state["hr_aft_hatch"]
    )

    # Display all 4-hour totals
    st.write("📦 Load 4-Hour Totals:")
    st.write(f"FWD: {st.session_state['fwd_load_4h']} | MID: {st.session_state['mid_load_4h']} | AFT: {st.session_state['aft_load_4h']} | POOP: {st.session_state['poop_load_4h']}")
    st.write("📦 Discharge 4-Hour Totals:")
    st.write(f"FWD: {st.session_state['fwd_discharge_4h']} | MID: {st.session_state['mid_discharge_4h']} | AFT: {st.session_state['aft_discharge_4h']} | POOP: {st.session_state['poop_discharge_4h']}")
    st.write("🔄 Restow 4-Hour Totals:")
    st.write(f"Load: {st.session_state['restow_load_4h']} | Discharge: {st.session_state['restow_discharge_4h']}")
    st.write("🛡️ Hatch Covers 4-Hour Total:")
    st.write(st.session_state["hatch_4h"])
    # --------------------------
# WHATSAPP TEMPLATE PREVIEW
# --------------------------
st.header("📱 WhatsApp Template Preview")
with st.expander("Preview WhatsApp Report"):
    whatsapp_text = f"""
*Vessel Hourly Moves Report*
🛳 Vessel: {st.session_state.get('vessel_name', 'Unknown')}
📅 Date: {st.session_state.get('report_date', 'Unknown')}
🕓 Period: {st.session_state.get('hourly_time', '00:00')} - {st.session_state.get('hourly_time_end_4h', 'Next 4h')}

*Load (FWD | MID | AFT | POOP):*
{st.session_state['fwd_load_4h']} | {st.session_state['mid_load_4h']} | {st.session_state['aft_load_4h']} | {st.session_state['poop_load_4h']}

*Discharge (FWD | MID | AFT | POOP):*
{st.session_state['fwd_discharge_4h']} | {st.session_state['mid_discharge_4h']} | {st.session_state['aft_discharge_4h']} | {st.session_state['poop_discharge_4h']}

*Restow Load / Discharge (FWD | MID | AFT | POOP):*
{st.session_state['restow_load_4h']} | {st.session_state['restow_discharge_4h']}

*Hatch Covers Open/Close (FWD | MID | AFT):*
{st.session_state['hatch_4h']}
"""
    st.text_area("WhatsApp Report", value=whatsapp_text, height=400)

# --------------------------
# CONTROLS & RESET OPTIONS
# --------------------------
st.header("⚙️ Controls & Reset Options")

# Reset Hourly Inputs
def reset_hourly_inputs():
    keys = [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_poop_discharge",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_discharge","hr_mid_restow_discharge","hr_aft_restow_discharge","hr_poop_restow_discharge",
        "hr_fwd_hatch","hr_mid_hatch","hr_aft_hatch"
    ]
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = 0
    # Move to next hour automatically
    current_index = hours_list.index(st.session_state.get("hourly_time", default_hour))
    next_index = (current_index + 1) % len(hours_list)
    st.session_state["hourly_time"] = hours_list[next_index]
    st.experimental_rerun()

st.button("🔄 Reset Hourly Inputs", on_click=reset_hourly_inputs)

# Reset 4-Hourly Totals
def reset_4hourly_totals():
    keys_4h = [
        "fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
        "fwd_discharge_4h","mid_discharge_4h","aft_discharge_4h","poop_discharge_4h",
        "restow_load_4h","restow_discharge_4h","hatch_4h"
    ]
    for key in keys_4h:
        if key in st.session_state:
            st.session_state[key] = 0
    st.experimental_rerun()

st.button("🔄 Reset 4-Hourly Totals", on_click=reset_4hourly_totals)

# --------------------------
# MANUAL OVERRIDES
# --------------------------
with st.expander("✏️ Manual Overrides"):
    st.write("Manually adjust totals if needed (updates WhatsApp template automatically):")
    override_keys = [
        "fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
        "fwd_discharge_4h","mid_discharge_4h","aft_discharge_4h","poop_discharge_4h",
        "restow_load_4h","restow_discharge_4h","hatch_4h"
    ]
    for key in override_keys:
        st.session_state[key] = st.number_input(
            key.replace("_"," ").title(),
            min_value=0,
            value=st.session_state.get(key, 0)
        )
        # --------------------------
# IDLE / DELAYS TRACKING
# --------------------------
st.header("⏸️ Idle / Delays")
with st.expander("🛑 Idle Entries"):
    num_idle_entries = st.number_input(
        "Number of Idle Entries",
        min_value=0,
        value=st.session_state.get("num_idle_entries", 0),
        key="num_idle_entries"
    )
    idle_entries = []
    for i in range(num_idle_entries):
        entry = st.text_input(f"Idle Entry {i+1}", key=f"idle_{i}")
        idle_entries.append(entry)
    st.session_state["idle_entries"] = idle_entries

# --------------------------
# AUTOMATIC 4-HOURLY AGGREGATION
# --------------------------
def update_4hourly_totals():
    st.session_state["fwd_load_4h"] = st.session_state["hr_fwd_load"]
    st.session_state["mid_load_4h"] = st.session_state["hr_mid_load"]
    st.session_state["aft_load_4h"] = st.session_state["hr_aft_load"]
    st.session_state["poop_load_4h"] = st.session_state["hr_poop_load"]

    st.session_state["fwd_discharge_4h"] = st.session_state["hr_fwd_discharge"]
    st.session_state["mid_discharge_4h"] = st.session_state["hr_mid_discharge"]
    st.session_state["aft_discharge_4h"] = st.session_state["hr_aft_discharge"]
    st.session_state["poop_discharge_4h"] = st.session_state["hr_poop_discharge"]

    st.session_state["restow_load_4h"] = (
        st.session_state["hr_fwd_restow_load"]
        + st.session_state["hr_mid_restow_load"]
        + st.session_state["hr_aft_restow_load"]
        + st.session_state["hr_poop_restow_load"]
    )

    st.session_state["restow_discharge_4h"] = (
        st.session_state["hr_fwd_restow_discharge"]
        + st.session_state["hr_mid_restow_discharge"]
        + st.session_state["hr_aft_restow_discharge"]
        + st.session_state["hr_poop_restow_discharge"]
    )

    st.session_state["hatch_4h"] = (
        st.session_state["hr_fwd_hatch"]
        + st.session_state["hr_mid_hatch"]
        + st.session_state["hr_aft_hatch"]
    )

# Call update automatically after hourly input
update_4hourly_totals()

# --------------------------
# FINAL BUTTONS
# --------------------------
st.button("✅ Generate WhatsApp Template", on_click=update_4hourly_totals)

# --------------------------
# END OF SCRIPT
# --------------------------
