# ===============================
# Part 1: Imports, Initialization, Vessel Info
# ===============================

# --------------------------
# IMPORTS
# --------------------------
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import math
import re
import os
import sys

# --------------------------
# INITIALIZATION
# --------------------------
# Initialize all hourly counters
hourly_keys = [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_poop_discharge",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_discharge","hr_mid_restow_discharge","hr_aft_restow_discharge","hr_poop_restow_discharge",
    "hr_fwd_hatch","hr_mid_hatch","hr_aft_hatch"
]

for key in hourly_keys:
    if key not in st.session_state:
        st.session_state[key] = 0

# Initialize idle entries
if "num_idle_entries" not in st.session_state:
    st.session_state["num_idle_entries"] = 0
if "idle_entries" not in st.session_state:
    st.session_state["idle_entries"] = []

# Initialize vessel info
if "vessel_name" not in st.session_state:
    st.session_state["vessel_name"] = ""
if "report_date" not in st.session_state:
    st.session_state["report_date"] = datetime.today().strftime("%Y-%m-%d")

# Initialize 4-hourly totals
four_hour_keys = [
    "fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
    "fwd_discharge_4h","mid_discharge_4h","aft_discharge_4h","poop_discharge_4h",
    "fwd_restow_load_4h","mid_restow_load_4h","aft_restow_load_4h","poop_restow_load_4h",
    "fwd_restow_discharge_4h","mid_restow_discharge_4h","aft_restow_discharge_4h","poop_restow_discharge_4h",
    "fwd_hatch_4h","mid_hatch_4h","aft_hatch_4h"
]

for key in four_hour_keys:
    if key not in st.session_state:
        st.session_state[key] = 0

# --------------------------
# DATE & TIME
# --------------------------
today = datetime.today()
st.date_input("Select Report Date", key="report_date_picker", value=today)

# --------------------------
# VESSEL INFO
# --------------------------
st.header("🚢 Vessel Info")
st.session_state["vessel_name"] = st.text_input("Vessel Name", value=st.session_state["vessel_name"], key="vessel_name")
berthed_date = st.date_input("Berthed Date", value=today)
plan_totals = st.number_input("Plan Totals & Opening Balance", min_value=0, value=0)

# --------------------------
# HOURLY TIME SELECTION
# --------------------------
hours_list = [f"{h:02d}:00" for h in range(24)]
default_hour = datetime.now().hour
if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = hours_list[default_hour]

hourly_time = st.selectbox(
    "⏱ Select Hourly Time",
    options=hours_list,
    index=hours_list.index(st.session_state["hourly_time"])
)
# ===============================
# Part 2: Hourly Inputs – Crane Moves, Restow, Hatch Covers
# ===============================

st.header("📊 Hourly Moves Input")

# --------------------------
# CRANE MOVES
# --------------------------
with st.expander("🏗️ Crane Moves"):
    # Load
    with st.expander("📦 Load"):
        st.session_state["hr_fwd_load"] = st.number_input(
            "FWD Load (hour)", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
        st.session_state["hr_mid_load"] = st.number_input(
            "MID Load (hour)", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
        st.session_state["hr_aft_load"] = st.number_input(
            "AFT Load (hour)", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
        st.session_state["hr_poop_load"] = st.number_input(
            "POOP Load (hour)", min_value=0, value=st.session_state["hr_poop_load"], key="hr_poop_load")

    # Discharge
    with st.expander("📦 Discharge"):
        st.session_state["hr_fwd_discharge"] = st.number_input(
            "FWD Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_discharge"], key="hr_fwd_discharge")
        st.session_state["hr_mid_discharge"] = st.number_input(
            "MID Discharge (hour)", min_value=0, value=st.session_state["hr_mid_discharge"], key="hr_mid_discharge")
        st.session_state["hr_aft_discharge"] = st.number_input(
            "AFT Discharge (hour)", min_value=0, value=st.session_state["hr_aft_discharge"], key="hr_aft_discharge")
        st.session_state["hr_poop_discharge"] = st.number_input(
            "POOP Discharge (hour)", min_value=0, value=st.session_state["hr_poop_discharge"], key="hr_poop_discharge")

# --------------------------
# RESTOW MOVES
# --------------------------
with st.expander("🔄 Restow Moves"):
    # Load
    with st.expander("📦 Load"):
        st.session_state["hr_fwd_restow_load"] = st.number_input(
            "FWD Restow Load (hour)", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
        st.session_state["hr_mid_restow_load"] = st.number_input(
            "MID Restow Load (hour)", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
        st.session_state["hr_aft_restow_load"] = st.number_input(
            "AFT Restow Load (hour)", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
        st.session_state["hr_poop_restow_load"] = st.number_input(
            "POOP Restow Load (hour)", min_value=0, value=st.session_state["hr_poop_restow_load"], key="hr_poop_restow_load")

    # Discharge
    with st.expander("📦 Discharge"):
        st.session_state["hr_fwd_restow_discharge"] = st.number_input(
            "FWD Restow Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_restow_discharge"], key="hr_fwd_restow_discharge")
        st.session_state["hr_mid_restow_discharge"] = st.number_input(
            "MID Restow Discharge (hour)", min_value=0, value=st.session_state["hr_mid_restow_discharge"], key="hr_mid_restow_discharge")
        st.session_state["hr_aft_restow_discharge"] = st.number_input(
            "AFT Restow Discharge (hour)", min_value=0, value=st.session_state["hr_aft_restow_discharge"], key="hr_aft_restow_discharge")
        st.session_state["hr_poop_restow_discharge"] = st.number_input(
            "POOP Restow Discharge (hour)", min_value=0, value=st.session_state["hr_poop_restow_discharge"], key="hr_poop_restow_discharge")

# --------------------------
# HATCH COVERS
# --------------------------
with st.expander("🛡️ Hatch Covers Open & Close"):
    st.session_state["hr_fwd_hatch"] = st.number_input(
        "FWD Hatch Open/Close (hour)", min_value=0, value=st.session_state["hr_fwd_hatch"], key="hr_fwd_hatch")
    st.session_state["hr_mid_hatch"] = st.number_input(
        "MID Hatch Open/Close (hour)", min_value=0, value=st.session_state["hr_mid_hatch"], key="hr_mid_hatch")
    st.session_state["hr_aft_hatch"] = st.number_input(
        "AFT Hatch Open/Close (hour)", min_value=0, value=st.session_state["hr_aft_hatch"], key="hr_aft_hatch")

# --------------------------
# IDLE ENTRIES
# --------------------------
st.header("⏸️ Idle / Delays")
with st.expander("🛑 Idle Entries"):
    num_idle_entries = st.number_input(
        "Number of Idle Entries", min_value=0,
        value=st.session_state.get("num_idle_entries", 0),
        key="num_idle_entries")
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

    # Crane Moves - Load
    crane_load_fwd = st.session_state["hr_fwd_load"]
    crane_load_mid = st.session_state["hr_mid_load"]
    crane_load_aft = st.session_state["hr_aft_load"]
    crane_load_poop = st.session_state["hr_poop_load"]
    st.write("📦 Crane Load Totals:")
    st.write(f"FWD: {crane_load_fwd} | MID: {crane_load_mid} | AFT: {crane_load_aft} | POOP: {crane_load_poop}")

    # Crane Moves - Discharge
    crane_discharge_fwd = st.session_state["hr_fwd_discharge"]
    crane_discharge_mid = st.session_state["hr_mid_discharge"]
    crane_discharge_aft = st.session_state["hr_aft_discharge"]
    crane_discharge_poop = st.session_state["hr_poop_discharge"]
    st.write("📦 Crane Discharge Totals:")
    st.write(f"FWD: {crane_discharge_fwd} | MID: {crane_discharge_mid} | AFT: {crane_discharge_aft} | POOP: {crane_discharge_poop}")

    # Restow Moves - Load
    restow_load_fwd = st.session_state["hr_fwd_restow_load"]
    restow_load_mid = st.session_state["hr_mid_restow_load"]
    restow_load_aft = st.session_state["hr_aft_restow_load"]
    restow_load_poop = st.session_state["hr_poop_restow_load"]
    st.write("🔄 Restow Load Totals:")
    st.write(f"FWD: {restow_load_fwd} | MID: {restow_load_mid} | AFT: {restow_load_aft} | POOP: {restow_load_poop}")

    # Restow Moves - Discharge
    restow_discharge_fwd = st.session_state["hr_fwd_restow_discharge"]
    restow_discharge_mid = st.session_state["hr_mid_restow_discharge"]
    restow_discharge_aft = st.session_state["hr_aft_restow_discharge"]
    restow_discharge_poop = st.session_state["hr_poop_restow_discharge"]
    st.write("🔄 Restow Discharge Totals:")
    st.write(f"FWD: {restow_discharge_fwd} | MID: {restow_discharge_mid} | AFT: {restow_discharge_aft} | POOP: {restow_discharge_poop}")

    # Hatch Covers Open/Close
    hatch_fwd = st.session_state["hr_fwd_hatch"]
    hatch_mid = st.session_state["hr_mid_hatch"]
    hatch_aft = st.session_state["hr_aft_hatch"]
    st.write("🛡️ Hatch Covers Open/Close Totals:")
    st.write(f"FWD: {hatch_fwd} | MID: {hatch_mid} | AFT: {hatch_aft}")

    # --------------------------
    # Update 4-Hourly Aggregation
    # --------------------------
    st.session_state["fwd_load_4h"] = st.session_state.get("fwd_load_4h", 0) + crane_load_fwd
    st.session_state["mid_load_4h"] = st.session_state.get("mid_load_4h", 0) + crane_load_mid
    st.session_state["aft_load_4h"] = st.session_state.get("aft_load_4h", 0) + crane_load_aft
    st.session_state["poop_load_4h"] = st.session_state.get("poop_load_4h", 0) + crane_load_poop

    st.session_state["fwd_discharge_4h"] = st.session_state.get("fwd_discharge_4h", 0) + crane_discharge_fwd
    st.session_state["mid_discharge_4h"] = st.session_state.get("mid_discharge_4h", 0) + crane_discharge_mid
    st.session_state["aft_discharge_4h"] = st.session_state.get("aft_discharge_4h", 0) + crane_discharge_aft
    st.session_state["poop_discharge_4h"] = st.session_state.get("poop_discharge_4h", 0) + crane_discharge_poop

    st.session_state["fwd_restow_load_4h"] = st.session_state.get("fwd_restow_load_4h", 0) + restow_load_fwd
    st.session_state["mid_restow_load_4h"] = st.session_state.get("mid_restow_load_4h", 0) + restow_load_mid
    st.session_state["aft_restow_load_4h"] = st.session_state.get("aft_restow_load_4h", 0) + restow_load_aft
    st.session_state["poop_restow_load_4h"] = st.session_state.get("poop_restow_load_4h", 0) + restow_load_poop

    st.session_state["fwd_restow_discharge_4h"] = st.session_state.get("fwd_restow_discharge_4h", 0) + restow_discharge_fwd
    st.session_state["mid_restow_discharge_4h"] = st.session_state.get("mid_restow_discharge_4h", 0) + restow_discharge_mid
    st.session_state["aft_restow_discharge_4h"] = st.session_state.get("aft_restow_discharge_4h", 0) + restow_discharge_aft
    st.session_state["poop_restow_discharge_4h"] = st.session_state.get("poop_restow_discharge_4h", 0) + restow_discharge_poop

    st.session_state["fwd_hatch_4h"] = st.session_state.get("fwd_hatch_4h", 0) + hatch_fwd
    st.session_state["mid_hatch_4h"] = st.session_state.get("mid_hatch_4h", 0) + hatch_mid
    st.session_state["aft_hatch_4h"] = st.session_state.get("aft_hatch_4h", 0) + hatch_aft
    # --------------------------
# AUTOMATIC HOURLY INCREMENT & GENERATE WHATSAPP TEMPLATE
# --------------------------
st.header("📱 WhatsApp Template & Hourly Controls")

def next_hour_label(current_label):
    index = hours_list.index(current_label)
    next_index = (index + 1) % len(hours_list)
    return hours_list[next_index]

def on_generate_hourly():
    # Increment to next hour
    st.session_state["hourly_time"] = next_hour_label(st.session_state.get("hourly_time", hours_list[0]))
    st.experimental_rerun()

st.button("✅ Generate Hourly Template", on_click=on_generate_hourly)

# --------------------------
# WhatsApp Template Preview
# --------------------------
with st.expander("📄 WhatsApp Template Preview"):
    whatsapp_text = f"""
*Vessel Hourly Moves Report*
🛳 Vessel: {st.session_state.get("vessel_name", "Unknown")}
📅 Date: {st.session_state.get("report_date", datetime.today().strftime("%Y-%m-%d"))}
🕓 Hour: {st.session_state.get("hourly_time", "00:00")}

*Load (FWD | MID | AFT | POOP):*
{st.session_state["hr_fwd_load"]} | {st.session_state["hr_mid_load"]} | {st.session_state["hr_aft_load"]} | {st.session_state["hr_poop_load"]}

*Discharge (FWD | MID | AFT | POOP):*
{st.session_state["hr_fwd_discharge"]} | {st.session_state["hr_mid_discharge"]} | {st.session_state["hr_aft_discharge"]} | {st.session_state["hr_poop_discharge"]}

*Restow Load (FWD | MID | AFT | POOP):*
{st.session_state["hr_fwd_restow_load"]} | {st.session_state["hr_mid_restow_load"]} | {st.session_state["hr_aft_restow_load"]} | {st.session_state["hr_poop_restow_load"]}

*Restow Discharge (FWD | MID | AFT | POOP):*
{st.session_state["hr_fwd_restow_discharge"]} | {st.session_state["hr_mid_restow_discharge"]} | {st.session_state["hr_aft_restow_discharge"]} | {st.session_state["hr_poop_restow_discharge"]}

*Hatch Covers Open/Close (FWD | MID | AFT):*
{st.session_state["hr_fwd_hatch"]} | {st.session_state["hr_mid_hatch"]} | {st.session_state["hr_aft_hatch"]}
"""
    st.text_area("WhatsApp Report", value=whatsapp_text, height=400)
    # --------------------------
# 4-HOURLY TOTALS AGGREGATION
# --------------------------
st.header("⏱ 4-Hourly Totals")

with st.expander("📊 4-Hourly Totals"):
    fwd_load_4h = sum(st.session_state.get(f"hr_fwd_load_{h}", st.session_state["hr_fwd_load"]) for h in range(4))
    mid_load_4h = sum(st.session_state.get(f"hr_mid_load_{h}", st.session_state["hr_mid_load"]) for h in range(4))
    aft_load_4h = sum(st.session_state.get(f"hr_aft_load_{h}", st.session_state["hr_aft_load"]) for h in range(4))
    poop_load_4h = sum(st.session_state.get(f"hr_poop_load_{h}", st.session_state["hr_poop_load"]) for h in range(4))

    fwd_discharge_4h = sum(st.session_state.get(f"hr_fwd_discharge_{h}", st.session_state["hr_fwd_discharge"]) for h in range(4))
    mid_discharge_4h = sum(st.session_state.get(f"hr_mid_discharge_{h}", st.session_state["hr_mid_discharge"]) for h in range(4))
    aft_discharge_4h = sum(st.session_state.get(f"hr_aft_discharge_{h}", st.session_state["hr_aft_discharge"]) for h in range(4))
    poop_discharge_4h = sum(st.session_state.get(f"hr_poop_discharge_{h}", st.session_state["hr_poop_discharge"]) for h in range(4))

    fwd_restow_load_4h = sum(st.session_state.get(f"hr_fwd_restow_load_{h}", st.session_state["hr_fwd_restow_load"]) for h in range(4))
    mid_restow_load_4h = sum(st.session_state.get(f"hr_mid_restow_load_{h}", st.session_state["hr_mid_restow_load"]) for h in range(4))
    aft_restow_load_4h = sum(st.session_state.get(f"hr_aft_restow_load_{h}", st.session_state["hr_aft_restow_load"]) for h in range(4))
    poop_restow_load_4h = sum(st.session_state.get(f"hr_poop_restow_load_{h}", st.session_state["hr_poop_restow_load"]) for h in range(4))

    fwd_restow_discharge_4h = sum(st.session_state.get(f"hr_fwd_restow_discharge_{h}", st.session_state["hr_fwd_restow_discharge"]) for h in range(4))
    mid_restow_discharge_4h = sum(st.session_state.get(f"hr_mid_restow_discharge_{h}", st.session_state["hr_mid_restow_discharge"]) for h in range(4))
    aft_restow_discharge_4h = sum(st.session_state.get(f"hr_aft_restow_discharge_{h}", st.session_state["hr_aft_restow_discharge"]) for h in range(4))
    poop_restow_discharge_4h = sum(st.session_state.get(f"hr_poop_restow_discharge_{h}", st.session_state["hr_poop_restow_discharge"]) for h in range(4))

    fwd_hatch_4h = sum(st.session_state.get(f"hr_fwd_hatch_{h}", st.session_state["hr_fwd_hatch"]) for h in range(4))
    mid_hatch_4h = sum(st.session_state.get(f"hr_mid_hatch_{h}", st.session_state["hr_mid_hatch"]) for h in range(4))
    aft_hatch_4h = sum(st.session_state.get(f"hr_aft_hatch_{h}", st.session_state["hr_aft_hatch"]) for h in range(4))

    st.write("📦 Load 4-Hour Totals:")
    st.write(f"FWD: {fwd_load_4h} | MID: {mid_load_4h} | AFT: {aft_load_4h} | POOP: {poop_load_4h}")

    st.write("📦 Discharge 4-Hour Totals:")
    st.write(f"FWD: {fwd_discharge_4h} | MID: {mid_discharge_4h} | AFT: {aft_discharge_4h} | POOP: {poop_discharge_4h}")

    st.write("🔄 Restow Load 4-Hour Totals:")
    st.write(f"FWD: {fwd_restow_load_4h} | MID: {mid_restow_load_4h} | AFT: {aft_restow_load_4h} | POOP: {poop_restow_load_4h}")

    st.write("🔄 Restow Discharge 4-Hour Totals:")
    st.write(f"FWD: {fwd_restow_discharge_4h} | MID: {mid_restow_discharge_4h} | AFT: {aft_restow_discharge_4h} | POOP: {poop_restow_discharge_4h}")

    st.write("🛡 Hatch Covers 4-Hour Totals:")
    st.write(f"FWD: {fwd_hatch_4h} | MID: {mid_hatch_4h} | AFT: {aft_hatch_4h}")

# --------------------------
# RESET BUTTONS
# --------------------------
st.header("⚙️ Reset Options")

def reset_hourly_inputs():
    for key in st.session_state.keys():
        if key.startswith("hr_"):
            st.session_state[key] = 0
    st.experimental_rerun()

def reset_4hourly_totals():
    for key in ["fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
                "fwd_discharge_4h","mid_discharge_4h","aft_discharge_4h","poop_discharge_4h",
                "fwd_restow_load_4h","mid_restow_load_4h","aft_restow_load_4h","poop_restow_load_4h",
                "fwd_restow_discharge_4h","mid_restow_discharge_4h","aft_restow_discharge_4h","poop_restow_discharge_4h",
                "fwd_hatch_4h","mid_hatch_4h","aft_hatch_4h"]:
        if key in st.session_state:
            st.session_state[key] = 0
    st.experimental_rerun()

st.button("🔄 Reset Hourly Inputs", on_click=reset_hourly_inputs)
st.button("🔄 Reset 4-Hourly Totals", on_click=reset_4hourly_totals)

# --------------------------
# MANUAL OVERRIDES
# --------------------------
with st.expander("✏️ Manual Overrides"):
    st.write("Manually adjust 4-hour totals if needed (updates WhatsApp template automatically):")
    for key in ["fwd_load_4h","mid_load_4h","aft_load_4h","poop_load_4h",
                "fwd_discharge_4h","mid_discharge_4h","aft_discharge_4h","poop_discharge_4h",
                "fwd_restow_load_4h","mid_restow_load_4h","aft_restow_load_4h","poop_restow_load_4h",
                "fwd_restow_discharge_4h","mid_restow_discharge_4h","aft_restow_discharge_4h","poop_restow_discharge_4h",
                "fwd_hatch_4h","mid_hatch_4h","aft_hatch_4h"]:
        st.session_state[key] = st.number_input(f"{key.replace('_',' ').title()}", value=st.session_state.get(key,0), min_value=0)