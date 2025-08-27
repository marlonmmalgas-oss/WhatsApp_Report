# =========================
# WhatsApp Report Generator
# =========================

import streamlit as st
import datetime
import json
import urllib.parse
from typing import Dict, Any

# =========================
# Session State Initialization
# =========================

def init_session_state():
    defaults = {
        "vessel_name": "",
        "berth_datetime": datetime.datetime.now().strftime("%d/%m/%Y %Hh%M"),
        "hourly_time": "06h00 - 07h00",
        "cumulative_load_fwd": 0,
        "cumulative_load_mid": 0,
        "cumulative_load_aft": 0,
        "cumulative_load_poops": 0,
        "cumulative_discharge_fwd": 0,
        "cumulative_discharge_mid": 0,
        "cumulative_discharge_aft": 0,
        "cumulative_discharge_poops": 0,
        "cumulative_restow_load_fwd": 0,
        "cumulative_restow_load_mid": 0,
        "cumulative_restow_load_aft": 0,
        "cumulative_restow_load_poops": 0,
        "cumulative_restow_discharge_fwd": 0,
        "cumulative_restow_discharge_mid": 0,
        "cumulative_restow_discharge_aft": 0,
        "cumulative_restow_discharge_poops": 0,
        "cumulative_hatch_open_fwd": 0,
        "cumulative_hatch_open_mid": 0,
        "cumulative_hatch_open_aft": 0,
        "cumulative_hatch_close_fwd": 0,
        "cumulative_hatch_close_mid": 0,
        "cumulative_hatch_close_aft": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =========================
# Query Params Persistence
# =========================

def load_from_query_params():
    """Load persistent state from query params."""
    params = st.query_params
    for key, value in params.items():
        if key in st.session_state:
            try:
                # Convert numeric fields back to int
                st.session_state[key] = int(value[0]) if value[0].isdigit() else value[0]
            except Exception:
                st.session_state[key] = value[0]

def save_to_query_params():
    """Save persistent state into query params."""
    params = {}
    for key, value in st.session_state.items():
        if isinstance(value, (int, float, str)):
            params[key] = str(value)
    st.query_params.update(params)

load_from_query_params()

# =========================
# Page Layout - Header
# =========================

st.title("📊 WhatsApp Report Generator")

# Vessel & Berth Inputs
st.session_state["vessel_name"] = st.text_input(
    "Vessel Name",
    value=st.session_state["vessel_name"],
    key="vessel_name_input"
)
st.session_state["berth_datetime"] = st.text_input(
    "Berth Date & Time",
    value=st.session_state["berth_datetime"],
    key="berth_datetime_input"
)

# Save persistence whenever values change
save_to_query_params()
# =========================
# Hourly Report Template
# =========================

st.subheader("⏱ Hourly Report Inputs")

# Hourly Time Range
st.session_state["hourly_time"] = st.text_input(
    "Hourly Range",
    value=st.session_state["hourly_time"],
    key="hourly_time_input"
)

# -------- Crane Moves (Hourly Splits) --------
with st.expander("🟢 Crane Moves - Load"):
    st.session_state["hr_load_fwd"] = st.number_input("Load FWD", value=0, step=1, key="hr_load_fwd")
    st.session_state["hr_load_mid"] = st.number_input("Load MID", value=0, step=1, key="hr_load_mid")
    st.session_state["hr_load_aft"] = st.number_input("Load AFT", value=0, step=1, key="hr_load_aft")
    st.session_state["hr_load_poops"] = st.number_input("Load POOP", value=0, step=1, key="hr_load_poops")

with st.expander("🔵 Crane Moves - Discharge"):
    st.session_state["hr_discharge_fwd"] = st.number_input("Discharge FWD", value=0, step=1, key="hr_discharge_fwd")
    st.session_state["hr_discharge_mid"] = st.number_input("Discharge MID", value=0, step=1, key="hr_discharge_mid")
    st.session_state["hr_discharge_aft"] = st.number_input("Discharge AFT", value=0, step=1, key="hr_discharge_aft")
    st.session_state["hr_discharge_poops"] = st.number_input("Discharge POOP", value=0, step=1, key="hr_discharge_poops")

# -------- Restows --------
with st.expander("🟠 Restow - Load"):
    st.session_state["hr_restow_load_fwd"] = st.number_input("Restow Load FWD", value=0, step=1, key="hr_restow_load_fwd")
    st.session_state["hr_restow_load_mid"] = st.number_input("Restow Load MID", value=0, step=1, key="hr_restow_load_mid")
    st.session_state["hr_restow_load_aft"] = st.number_input("Restow Load AFT", value=0, step=1, key="hr_restow_load_aft")
    st.session_state["hr_restow_load_poops"] = st.number_input("Restow Load POOP", value=0, step=1, key="hr_restow_load_poops")

with st.expander("🟣 Restow - Discharge"):
    st.session_state["hr_restow_discharge_fwd"] = st.number_input("Restow Discharge FWD", value=0, step=1, key="hr_restow_discharge_fwd")
    st.session_state["hr_restow_discharge_mid"] = st.number_input("Restow Discharge MID", value=0, step=1, key="hr_restow_discharge_mid")
    st.session_state["hr_restow_discharge_aft"] = st.number_input("Restow Discharge AFT", value=0, step=1, key="hr_restow_discharge_aft")
    st.session_state["hr_restow_discharge_poops"] = st.number_input("Restow Discharge POOP", value=0, step=1, key="hr_restow_discharge_poops")

# -------- Hatch Covers --------
with st.expander("⚫ Hatch Covers - Open"):
    st.session_state["hr_hatch_open_fwd"] = st.number_input("Hatch Open FWD", value=0, step=1, key="hr_hatch_open_fwd")
    st.session_state["hr_hatch_open_mid"] = st.number_input("Hatch Open MID", value=0, step=1, key="hr_hatch_open_mid")
    st.session_state["hr_hatch_open_aft"] = st.number_input("Hatch Open AFT", value=0, step=1, key="hr_hatch_open_aft")

with st.expander("⚪ Hatch Covers - Close"):
    st.session_state["hr_hatch_close_fwd"] = st.number_input("Hatch Close FWD", value=0, step=1, key="hr_hatch_close_fwd")
    st.session_state["hr_hatch_close_mid"] = st.number_input("Hatch Close MID", value=0, step=1, key="hr_hatch_close_mid")
    st.session_state["hr_hatch_close_aft"] = st.number_input("Hatch Close AFT", value=0, step=1, key="hr_hatch_close_aft")
    # =========================
# Hourly Totals Tracker
# =========================

st.subheader("📊 Hourly Totals Tracker (Split)")

# --- Load Totals ---
with st.expander("🟢 Load Totals (FWD/MID/AFT/POOP)"):
    st.write("Load totals auto-update based on Hourly Inputs")
    st.session_state["hr_total_load_fwd"] = st.session_state.get("hr_total_load_fwd", 0) + st.session_state["hr_load_fwd"]
    st.session_state["hr_total_load_mid"] = st.session_state.get("hr_total_load_mid", 0) + st.session_state["hr_load_mid"]
    st.session_state["hr_total_load_aft"] = st.session_state.get("hr_total_load_aft", 0) + st.session_state["hr_load_aft"]
    st.session_state["hr_total_load_poops"] = st.session_state.get("hr_total_load_poops", 0) + st.session_state["hr_load_poops"]

    st.write(f"FWD: {st.session_state['hr_total_load_fwd']}")
    st.write(f"MID: {st.session_state['hr_total_load_mid']}")
    st.write(f"AFT: {st.session_state['hr_total_load_aft']}")
    st.write(f"POOP: {st.session_state['hr_total_load_poops']}")

# --- Discharge Totals ---
with st.expander("🔵 Discharge Totals (FWD/MID/AFT/POOP)"):
    st.session_state["hr_total_discharge_fwd"] = st.session_state.get("hr_total_discharge_fwd", 0) + st.session_state["hr_discharge_fwd"]
    st.session_state["hr_total_discharge_mid"] = st.session_state.get("hr_total_discharge_mid", 0) + st.session_state["hr_discharge_mid"]
    st.session_state["hr_total_discharge_aft"] = st.session_state.get("hr_total_discharge_aft", 0) + st.session_state["hr_discharge_aft"]
    st.session_state["hr_total_discharge_poops"] = st.session_state.get("hr_total_discharge_poops", 0) + st.session_state["hr_discharge_poops"]

    st.write(f"FWD: {st.session_state['hr_total_discharge_fwd']}")
    st.write(f"MID: {st.session_state['hr_total_discharge_mid']}")
    st.write(f"AFT: {st.session_state['hr_total_discharge_aft']}")
    st.write(f"POOP: {st.session_state['hr_total_discharge_poops']}")

# --- Restow Load Totals ---
with st.expander("🟠 Restow Load Totals (FWD/MID/AFT/POOP)"):
    st.session_state["hr_total_restow_load_fwd"] = st.session_state.get("hr_total_restow_load_fwd", 0) + st.session_state["hr_restow_load_fwd"]
    st.session_state["hr_total_restow_load_mid"] = st.session_state.get("hr_total_restow_load_mid", 0) + st.session_state["hr_restow_load_mid"]
    st.session_state["hr_total_restow_load_aft"] = st.session_state.get("hr_total_restow_load_aft", 0) + st.session_state["hr_restow_load_aft"]
    st.session_state["hr_total_restow_load_poops"] = st.session_state.get("hr_total_restow_load_poops", 0) + st.session_state["hr_restow_load_poops"]

    st.write(f"FWD: {st.session_state['hr_total_restow_load_fwd']}")
    st.write(f"MID: {st.session_state['hr_total_restow_load_mid']}")
    st.write(f"AFT: {st.session_state['hr_total_restow_load_aft']}")
    st.write(f"POOP: {st.session_state['hr_total_restow_load_poops']}")

# --- Restow Discharge Totals ---
with st.expander("🟣 Restow Discharge Totals (FWD/MID/AFT/POOP)"):
    st.session_state["hr_total_restow_discharge_fwd"] = st.session_state.get("hr_total_restow_discharge_fwd", 0) + st.session_state["hr_restow_discharge_fwd"]
    st.session_state["hr_total_restow_discharge_mid"] = st.session_state.get("hr_total_restow_discharge_mid", 0) + st.session_state["hr_restow_discharge_mid"]
    st.session_state["hr_total_restow_discharge_aft"] = st.session_state.get("hr_total_restow_discharge_aft", 0) + st.session_state["hr_restow_discharge_aft"]
    st.session_state["hr_total_restow_discharge_poops"] = st.session_state.get("hr_total_restow_discharge_poops", 0) + st.session_state["hr_restow_discharge_poops"]

    st.write(f"FWD: {st.session_state['hr_total_restow_discharge_fwd']}")
    st.write(f"MID: {st.session_state['hr_total_restow_discharge_mid']}")
    st.write(f"AFT: {st.session_state['hr_total_restow_discharge_aft']}")
    st.write(f"POOP: {st.session_state['hr_total_restow_discharge_poops']}")

# --- Hatch Cover Totals ---
with st.expander("⚫⚪ Hatch Cover Totals (Open/Close - FWD/MID/AFT)"):
    st.session_state["hr_total_hatch_open_fwd"] = st.session_state.get("hr_total_hatch_open_fwd", 0) + st.session_state["hr_hatch_open_fwd"]
    st.session_state["hr_total_hatch_open_mid"] = st.session_state.get("hr_total_hatch_open_mid", 0) + st.session_state["hr_hatch_open_mid"]
    st.session_state["hr_total_hatch_open_aft"] = st.session_state.get("hr_total_hatch_open_aft", 0) + st.session_state["hr_hatch_open_aft"]

    st.session_state["hr_total_hatch_close_fwd"] = st.session_state.get("hr_total_hatch_close_fwd", 0) + st.session_state["hr_hatch_close_fwd"]
    st.session_state["hr_total_hatch_close_mid"] = st.session_state.get("hr_total_hatch_close_mid", 0) + st.session_state["hr_hatch_close_mid"]
    st.session_state["hr_total_hatch_close_aft"] = st.session_state.get("hr_total_hatch_close_aft", 0) + st.session_state["hr_hatch_close_aft"]

    st.write(f"Open FWD: {st.session_state['hr_total_hatch_open_fwd']} | Close FWD: {st.session_state['hr_total_hatch_close_fwd']}")
    st.write(f"Open MID: {st.session_state['hr_total_hatch_open_mid']} | Close MID: {st.session_state['hr_total_hatch_close_mid']}")
    st.write(f"Open AFT: {st.session_state['hr_total_hatch_open_aft']} | Close AFT: {st.session_state['hr_total_hatch_close_aft']}")
    # =========================
# 4-Hourly Totals Tracker
# =========================
st.subheader("⏰ 4-Hourly Totals Tracker")

# --- Load Totals ---
with st.expander("🟢 Load Totals (FWD/MID/AFT/POOP)"):
    st.write("Totals for the past 4 hours")
    st.write(f"FWD: {st.session_state.get('hr_total_load_fwd',0)}")
    st.write(f"MID: {st.session_state.get('hr_total_load_mid',0)}")
    st.write(f"AFT: {st.session_state.get('hr_total_load_aft',0)}")
    st.write(f"POOP: {st.session_state.get('hr_total_load_poops',0)}")

# --- Discharge Totals ---
with st.expander("🔵 Discharge Totals (FWD/MID/AFT/POOP)"):
    st.write(f"FWD: {st.session_state.get('hr_total_discharge_fwd',0)}")
    st.write(f"MID: {st.session_state.get('hr_total_discharge_mid',0)}")
    st.write(f"AFT: {st.session_state.get('hr_total_discharge_aft',0)}")
    st.write(f"POOP: {st.session_state.get('hr_total_discharge_poops',0)}")

# --- Restow Load Totals ---
with st.expander("🟠 Restow Load Totals (FWD/MID/AFT/POOP)"):
    st.write(f"FWD: {st.session_state.get('hr_total_restow_load_fwd',0)}")
    st.write(f"MID: {st.session_state.get('hr_total_restow_load_mid',0)}")
    st.write(f"AFT: {st.session_state.get('hr_total_restow_load_aft',0)}")
    st.write(f"POOP: {st.session_state.get('hr_total_restow_load_poops',0)}")

# --- Restow Discharge Totals ---
with st.expander("🟣 Restow Discharge Totals (FWD/MID/AFT/POOP)"):
    st.write(f"FWD: {st.session_state.get('hr_total_restow_discharge_fwd',0)}")
    st.write(f"MID: {st.session_state.get('hr_total_restow_discharge_mid',0)}")
    st.write(f"AFT: {st.session_state.get('hr_total_restow_discharge_aft',0)}")
    st.write(f"POOP: {st.session_state.get('hr_total_restow_discharge_poops',0)}")

# --- Hatch Cover Totals ---
with st.expander("⚫⚪ Hatch Cover Totals (Open/Close - FWD/MID/AFT)"):
    st.write(f"Open FWD: {st.session_state.get('hr_total_hatch_open_fwd',0)} | Close FWD: {st.session_state.get('hr_total_hatch_close_fwd',0)}")
    st.write(f"Open MID: {st.session_state.get('hr_total_hatch_open_mid',0)} | Close MID: {st.session_state.get('hr_total_hatch_close_mid',0)}")
    st.write(f"Open AFT: {st.session_state.get('hr_total_hatch_open_aft',0)} | Close AFT: {st.session_state.get('hr_total_hatch_close_aft',0)}")


# --- Sync Buttons ---
col1, col2 = st.columns(2)

with col1:
    if st.button("⬆️ Populate 4-Hourly with Hourly Totals"):
        st.session_state["four_hourly"] = {
            "load": {
                "fwd": st.session_state.get("hr_total_load_fwd", 0),
                "mid": st.session_state.get("hr_total_load_mid", 0),
                "aft": st.session_state.get("hr_total_load_aft", 0),
                "poop": st.session_state.get("hr_total_load_poops", 0),
            },
            "discharge": {
                "fwd": st.session_state.get("hr_total_discharge_fwd", 0),
                "mid": st.session_state.get("hr_total_discharge_mid", 0),
                "aft": st.session_state.get("hr_total_discharge_aft", 0),
                "poop": st.session_state.get("hr_total_discharge_poops", 0),
            },
            "restow_load": {
                "fwd": st.session_state.get("hr_total_restow_load_fwd", 0),
                "mid": st.session_state.get("hr_total_restow_load_mid", 0),
                "aft": st.session_state.get("hr_total_restow_load_aft", 0),
                "poop": st.session_state.get("hr_total_restow_load_poops", 0),
            },
            "restow_discharge": {
                "fwd": st.session_state.get("hr_total_restow_discharge_fwd", 0),
                "mid": st.session_state.get("hr_total_restow_discharge_mid", 0),
                "aft": st.session_state.get("hr_total_restow_discharge_aft", 0),
                "poop": st.session_state.get("hr_total_restow_discharge_poops", 0),
            },
            "hatch": {
                "open": {
                    "fwd": st.session_state.get("hr_total_hatch_open_fwd", 0),
                    "mid": st.session_state.get("hr_total_hatch_open_mid", 0),
                    "aft": st.session_state.get("hr_total_hatch_open_aft", 0),
                },
                "close": {
                    "fwd": st.session_state.get("hr_total_hatch_close_fwd", 0),
                    "mid": st.session_state.get("hr_total_hatch_close_mid", 0),
                    "aft": st.session_state.get("hr_total_hatch_close_aft", 0),
                }
            }
        }
        st.success("✅ 4-Hourly totals populated from Hourly Tracker!")

with col2:
    if st.button("🔄 Reset 4-Hourly Totals"):
        st.session_state["four_hourly"] = {}
        st.success("✅ 4-Hourly totals reset for the next cycle!")
        # =========================
# Cumulative Totals Section
# =========================
st.subheader("📊 Cumulative Totals (Auto-Synced)")

if "cumulative" not in st.session_state:
    st.session_state["cumulative"] = {
        "load": {"fwd": 0, "mid": 0, "aft": 0, "poop": 0},
        "discharge": {"fwd": 0, "mid": 0, "aft": 0, "poop": 0},
        "restow_load": {"fwd": 0, "mid": 0, "aft": 0, "poop": 0},
        "restow_discharge": {"fwd": 0, "mid": 0, "aft": 0, "poop": 0},
        "hatch": {"open": {"fwd": 0, "mid": 0, "aft": 0},
                  "close": {"fwd": 0, "mid": 0, "aft": 0}}
    }

# --- Sync cumulative with 4-hourly updates ---
if "four_hourly" in st.session_state and st.session_state["four_hourly"]:
    for section, values in st.session_state["four_hourly"].items():
        if isinstance(values, dict):
            for pos, val in values.items():
                if isinstance(val, dict):  # hatch open/close
                    for subpos, subval in val.items():
                        st.session_state["cumulative"][section][pos][subpos] += subval
                else:
                    st.session_state["cumulative"][section][pos] += val

# --- Display cumulative totals neatly ---
with st.expander("📦 Load Cumulative"):
    st.write(st.session_state["cumulative"]["load"])

with st.expander("📤 Discharge Cumulative"):
    st.write(st.session_state["cumulative"]["discharge"])

with st.expander("♻️ Restow Load Cumulative"):
    st.write(st.session_state["cumulative"]["restow_load"])

with st.expander("♻️ Restow Discharge Cumulative"):
    st.write(st.session_state["cumulative"]["restow_discharge"])

with st.expander("⚙️ Hatch Cover Cumulative"):
    st.write(st.session_state["cumulative"]["hatch"])


# =========================
# Persistence with Query Params
# =========================
# Save key session state into query params so it survives refresh/device switch
params = {
    "vessel_name": st.session_state.get("vessel_name", ""),
    "berth_date": st.session_state.get("berth_date", ""),
    "cumulative": str(st.session_state["cumulative"])  # serialize dict
}

st.query_params.update(params)

# On load, restore state from query params
qp = st.query_params
if qp:
    if "vessel_name" in qp:
        st.session_state["vessel_name"] = qp["vessel_name"]
    if "berth_date" in qp:
        st.session_state["berth_date"] = qp["berth_date"]
    if "cumulative" in qp:
        import ast
        st.session_state["cumulative"] = ast.literal_eval(qp["cumulative"])
