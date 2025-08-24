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
        # WhatsApp_Report.py  — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name", value=st.session_state["vessel_name"], key="vessel_name")
    st.text_input("Berthed Date", value=st.session_state["berthed_date"], key="berthed_date")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", value=st.session_state["report_date"], key="report_date")

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  value=int(st.session_state["planned_load"]),  min_value=0, key="planned_load")
        st.number_input("Planned Discharge", value=int(st.session_state["planned_disch"]), min_value=0, key="planned_disch")
        st.number_input("Planned Restow Load",  value=int(st.session_state["planned_restow_load"]),  min_value=0, key="planned_restow_load")
        st.number_input("Planned Restow Discharge", value=int(st.session_state["planned_restow_disch"]), min_value=0, key="planned_restow_disch")
    with c2:
        st.number_input("Opening Load (Deduction)",  value=int(st.session_state["opening_load"]),  min_value=0, key="opening_load")
        st.number_input("Opening Discharge (Deduction)", value=int(st.session_state["opening_disch"]), min_value=0, key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)",  value=int(st.session_state["opening_restow_load"]),  min_value=0, key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)", value=int(st.session_state["opening_restow_disch"]), min_value=0, key="opening_restow_disch")

# --------------------------
# Hour selector (24h) + ensure valid
# --------------------------
def ensure_hour_in_state():
    if st.session_state.get("hourly_time") not in hours_list:
        st.session_state["hourly_time"] = cumulative.get("last_hour", hours_list[0])

ensure_hour_in_state()
st.selectbox("⏱ Select Hourly Time", options=hours_list,
             index=hours_list.index(st.session_state["hourly_time"]),
             key="hourly_time")

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge)
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, key="hr_poop_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch")

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

# --------------------------
# Idle / Delays
# --------------------------
st.subheader("⏸️ Idle / Delays")
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
    "Spreader difficulties",
]
with st.expander("🛑 Idle Entries", expanded=False):
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries")
    entries = []
    for i in range(st.session_state["num_idle_entries"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30")
        end   = c3.text_input(f"End {i+1}",   key=f"idle_end_{i}",   placeholder="e.g., 12h40")
        sel   = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}")
        entries.append({
            "crane": (crane or "").strip(),
            "start": (start or "").strip(),
            "end": (end or "").strip(),
            "delay": (custom or "").strip() if (custom or "").strip() else sel
        })
    # this key is NOT a widget key, safe to assign:
    st.session_state["idle_entries"] = entries
    # WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# Derived Hourly Totals (visible – split per position as requested)
# --------------------------
with st.expander("🧮 Hourly Totals Tracker (per position)"):
    # Crane Load (FWD/MID/AFT/POOP)
    st.write("**Crane Moves — Load (per position)**")
    st.write(f"FWD: {st.session_state['hr_fwd_load']}  |  MID: {st.session_state['hr_mid_load']}  |  AFT: {st.session_state['hr_aft_load']}  |  POOP: {st.session_state['hr_poop_load']}")
    # Crane Discharge (FWD/MID/AFT/POOP)
    st.write("**Crane Moves — Discharge (per position)**")
    st.write(f"FWD: {st.session_state['hr_fwd_disch']}  |  MID: {st.session_state['hr_mid_disch']}  |  AFT: {st.session_state['hr_aft_disch']}  |  POOP: {st.session_state['hr_poop_disch']}")
    # Restow Load (FWD/MID/AFT/POOP)
    st.write("**Restow — Load (per position)**")
    st.write(f"FWD: {st.session_state['hr_fwd_restow_load']}  |  MID: {st.session_state['hr_mid_restow_load']}  |  AFT: {st.session_state['hr_aft_restow_load']}  |  POOP: {st.session_state['hr_poop_restow_load']}")
    # Restow Discharge (FWD/MID/AFT/POOP)
    st.write("**Restow — Discharge (per position)**")
    st.write(f"FWD: {st.session_state['hr_fwd_restow_disch']}  |  MID: {st.session_state['hr_mid_restow_disch']}  |  AFT: {st.session_state['hr_aft_restow_disch']}  |  POOP: {st.session_state['hr_poop_restow_disch']}")
    # Hatch Open (FWD/MID/AFT)
    st.write("**Hatch — Open (per position)**")
    st.write(f"FWD: {st.session_state['hr_hatch_fwd_open']}  |  MID: {st.session_state['hr_hatch_mid_open']}  |  AFT: {st.session_state['hr_hatch_aft_open']}")
    # Hatch Close (FWD/MID/AFT)
    st.write("**Hatch — Close (per position)**")
    st.write(f"FWD: {st.session_state['hr_hatch_fwd_close']}  |  MID: {st.session_state['hr_hatch_mid_close']}  |  AFT: {st.session_state['hr_hatch_aft_close']}")

# --------------------------
# WhatsApp (Hourly) – original monospace template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
Hour: {st.session_state['hourly_time']}
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
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
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
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

def on_generate_hourly():
    # update cumulative
    cumulative["done_load"]  += st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    cumulative["done_disch"] += st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    cumulative["done_restow_load"]  += st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    cumulative["done_restow_disch"] += st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    cumulative["done_hatch_open"]  += st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    cumulative["done_hatch_close"] += st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # persist basics
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "planned_load": st.session_state["planned_load"],
        "planned_disch": st.session_state["planned_disch"],
        "planned_restow_load": st.session_state["planned_restow_load"],
        "planned_restow_disch": st.session_state["planned_restow_disch"],
        "opening_load": st.session_state["opening_load"],
        "opening_disch": st.session_state["opening_disch"],
        "opening_restow_load": st.session_state["opening_restow_load"],
        "opening_restow_disch": st.session_state["opening_restow_disch"],
        "last_hour": st.session_state["hourly_time"],
    })
    save_cumulative(cumulative)

    # add this hour to the 4h rolling tracker
    add_current_hour_to_4h()

    # auto-advance hour (safe)
    safe_advance_hour()

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        hourly_text = generate_hourly_template()
        st.code(hourly_text, language="text")
        on_generate_hourly()

with colB:
    if st.button("👁️ Preview Hourly Template Only"):
        st.code(generate_hourly_template(), language="text")

with colC:
    if st.button("📤 Open WhatsApp (Hourly)"):
        hourly_text = generate_hourly_template()
        wa_text = f"```{hourly_text}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")

# Reset HOURLY inputs (no experimental_rerun)
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    ]:
        st.session_state[k] = 0
    safe_advance_hour()

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
# WhatsApp_Report.py  — PART 4 / 5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"], "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"], "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"], "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"], "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"], "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"], "hatch_aft_close": ss["m4h_hatch_aft_close"],
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")

with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto-calculated", key="fourh_manual_override")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("FWD Load 4H", min_value=0, key="m4h_fwd_load")
        st.number_input("FWD Disch 4H", min_value=0, key="m4h_fwd_disch")
        st.number_input("FWD Rst Load 4H", min_value=0, key="m4h_fwd_restow_load")
        st.number_input("FWD Rst Disch 4H", min_value=0, key="m4h_fwd_restow_disch")
        st.number_input("FWD Hatch Open 4H", min_value=0, key="m4h_hatch_fwd_open")
        st.number_input("FWD Hatch Close 4H", min_value=0, key="m4h_hatch_fwd_close")
    with c2:
        st.number_input("MID Load 4H", min_value=0, key="m4h_mid_load")
        st.number_input("MID Disch 4H", min_value=0, key="m4h_mid_disch")
        st.number_input("MID Rst Load 4H", min_value=0, key="m4h_mid_restow_load")
        st.number_input("MID Rst Disch 4H", min_value=0, key="m4h_mid_restow_disch")
        st.number_input("MID Hatch Open 4H", min_value=0, key="m4h_hatch_mid_open")
        st.number_input("MID Hatch Close 4H", min_value=0, key="m4h_hatch_mid_close")
    with c3:
        st.number_input("AFT Load 4H", min_value=0, key="m4h_aft_load")
        st.number_input("AFT Disch 4H", min_value=0, key="m4h_aft_disch")
        st.number_input("AFT Rst Load 4H", min_value=0, key="m4h_aft_restow_load")
        st.number_input("AFT Rst Disch 4H", min_value=0, key="m4h_aft_restow_disch")
        st.number_input("AFT Hatch Open 4H", min_value=0, key="m4h_hatch_aft_open")
        st.number_input("AFT Hatch Close 4H", min_value=0, key="m4h_hatch_aft_close")
    with c4:
        st.number_input("POOP Load 4H", min_value=0, key="m4h_poop_load")
        st.number_input("POOP Disch 4H", min_value=0, key="m4h_poop_disch")
        st.number_input("POOP Rst Load 4H", min_value=0, key="m4h_poop_restow_load")
        st.number_input("POOP Rst Disch 4H", min_value=0, key="m4h_poop_restow_disch")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {vals4h['fwd_load']:>5}     {vals4h['fwd_disch']:>5}
MID       {vals4h['mid_load']:>5}     {vals4h['mid_disch']:>5}
AFT       {vals4h['aft_load']:>5}     {vals4h['aft_disch']:>5}
POOP      {vals4h['poop_load']:>5}     {vals4h['poop_disch']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {vals4h['fwd_restow_load']:>5}     {vals4h['fwd_restow_disch']:>5}
MID       {vals4h['mid_restow_load']:>5}     {vals4h['mid_restow_disch']:>5}
AFT       {vals4h['aft_restow_load']:>5}     {vals4h['aft_restow_disch']:>5}
POOP      {vals4h['poop_restow_load']:>5}     {vals4h['poop_restow_disch']:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template(), language="text")

st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB, cC = st.columns([1,1,1])
with cA:
    if st.button("👁️ Preview 4-Hourly Template Only"):
        st.code(generate_4h_template(), language="text")
with cB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template()
        wa_text = f"```{t}```"
        if st.session_state.get("wa_num_4h"):
            link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_4h"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")
with cC:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")
        # WhatsApp_Report.py  — PART 5 / 5

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs."
)