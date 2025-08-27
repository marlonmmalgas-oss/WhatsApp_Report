# WhatsApp Report Script
# --- PART 1 OF 5 ---

import streamlit as st
import datetime
import urllib.parse
import json
import os
import time

# =============================
# QUERY PARAM PERSISTENCE
# =============================

def load_from_query_params():
    """Load persistent state (like vessel, berth, cumulative totals) from query params."""
    query_params = st.experimental_get_query_params()
    for key, value in query_params.items():
        if len(value) == 1:
            try:
                st.session_state[key] = json.loads(value[0])
            except:
                st.session_state[key] = value[0]

def save_to_query_params():
    """Save current state into query params so it's kept across sessions/devices."""
    state_to_save = {
        "vessel_name": st.session_state.get("vessel_name", ""),
        "berth_number": st.session_state.get("berth_number", ""),
        "date": st.session_state.get("date", str(datetime.date.today())),
        "cumulative_load": st.session_state.get("cumulative_load", 0),
        "cumulative_discharge": st.session_state.get("cumulative_discharge", 0),
        "cumulative_restow": st.session_state.get("cumulative_restow", 0),
        "cumulative_hatch": st.session_state.get("cumulative_hatch", 0),
        "hourly_time": st.session_state.get("hourly_time", "06h00 - 07h00")
    }
    query_params = {k: json.dumps(v) for k, v in state_to_save.items()}
    st.experimental_set_query_params(**query_params)

# =============================
# SESSION STATE INITIALIZATION
# =============================

if "initialized" not in st.session_state:
    load_from_query_params()

    # Vessel details (persisted)
    st.session_state.setdefault("vessel_name", "")
    st.session_state.setdefault("berth_number", "")
    st.session_state.setdefault("date", str(datetime.date.today()))
    st.session_state.setdefault("hourly_time", "06h00 - 07h00")

    # Cumulative totals (persisted)
    st.session_state.setdefault("cumulative_load", 0)
    st.session_state.setdefault("cumulative_discharge", 0)
    st.session_state.setdefault("cumulative_restow", 0)
    st.session_state.setdefault("cumulative_hatch", 0)

    # Hourly inputs (reset every reload)
    st.session_state.setdefault("hr_fwd_load", 0)
    st.session_state.setdefault("hr_mid_load", 0)
    st.session_state.setdefault("hr_aft_load", 0)
    st.session_state.setdefault("hr_poop_load", 0)

    st.session_state.setdefault("hr_fwd_discharge", 0)
    st.session_state.setdefault("hr_mid_discharge", 0)
    st.session_state.setdefault("hr_aft_discharge", 0)
    st.session_state.setdefault("hr_poop_discharge", 0)

    st.session_state.setdefault("hr_fwd_restow_load", 0)
    st.session_state.setdefault("hr_mid_restow_load", 0)
    st.session_state.setdefault("hr_aft_restow_load", 0)
    st.session_state.setdefault("hr_poop_restow_load", 0)

    st.session_state.setdefault("hr_fwd_restow_discharge", 0)
    st.session_state.setdefault("hr_mid_restow_discharge", 0)
    st.session_state.setdefault("hr_aft_restow_discharge", 0)
    st.session_state.setdefault("hr_poop_restow_discharge", 0)

    st.session_state.setdefault("hr_fwd_hatch_open", 0)
    st.session_state.setdefault("hr_mid_hatch_open", 0)
    st.session_state.setdefault("hr_aft_hatch_open", 0)

    st.session_state.setdefault("hr_fwd_hatch_close", 0)
    st.session_state.setdefault("hr_mid_hatch_close", 0)
    st.session_state.setdefault("hr_aft_hatch_close", 0)

    # 4-Hourly inputs (reset manually)
    st.session_state.setdefault("four_hourly_load", 0)
    st.session_state.setdefault("four_hourly_discharge", 0)
    st.session_state.setdefault("four_hourly_restow", 0)
    st.session_state.setdefault("four_hourly_hatch", 0)

    st.session_state["initialized"] = True

# Save state on each run
save_to_query_params()

st.title("📲 WhatsApp Report Generator")
# --- PART 2 OF 5 ---

# =============================
# VESSEL INFORMATION
# =============================

st.markdown("### ⚓ Vessel Information")

st.session_state["vessel_name"] = st.text_input(
    "Vessel Name",
    value=st.session_state.get("vessel_name", ""),
    key="vessel_name_input"
)

st.session_state["berth_number"] = st.text_input(
    "Berth Number",
    value=st.session_state.get("berth_number", ""),
    key="berth_number_input"
)

st.session_state["date"] = st.date_input(
    "Date",
    value=datetime.datetime.strptime(st.session_state["date"], "%Y-%m-%d").date()
)

st.session_state["hourly_time"] = st.text_input(
    "Hourly Window",
    value=st.session_state.get("hourly_time", "06h00 - 07h00"),
    key="hourly_time_input"
)

# =============================
# HOURLY INPUTS SECTION
# =============================

st.markdown("### 🕐 Hourly Crane Moves")

# --- Load ---
with st.expander("⬆️ Crane Moves: Load"):
    st.session_state["hr_fwd_load"] = st.number_input("FWD Load", min_value=0, value=st.session_state["hr_fwd_load"])
    st.session_state["hr_mid_load"] = st.number_input("MID Load", min_value=0, value=st.session_state["hr_mid_load"])
    st.session_state["hr_aft_load"] = st.number_input("AFT Load", min_value=0, value=st.session_state["hr_aft_load"])
    st.session_state["hr_poop_load"] = st.number_input("POOP Load", min_value=0, value=st.session_state["hr_poop_load"])

# --- Discharge ---
with st.expander("⬇️ Crane Moves: Discharge"):
    st.session_state["hr_fwd_discharge"] = st.number_input("FWD Discharge", min_value=0, value=st.session_state["hr_fwd_discharge"])
    st.session_state["hr_mid_discharge"] = st.number_input("MID Discharge", min_value=0, value=st.session_state["hr_mid_discharge"])
    st.session_state["hr_aft_discharge"] = st.number_input("AFT Discharge", min_value=0, value=st.session_state["hr_aft_discharge"])
    st.session_state["hr_poop_discharge"] = st.number_input("POOP Discharge", min_value=0, value=st.session_state["hr_poop_discharge"])

# --- Restow Load ---
with st.expander("🔄 Restow: Load"):
    st.session_state["hr_fwd_restow_load"] = st.number_input("FWD Restow Load", min_value=0, value=st.session_state["hr_fwd_restow_load"])
    st.session_state["hr_mid_restow_load"] = st.number_input("MID Restow Load", min_value=0, value=st.session_state["hr_mid_restow_load"])
    st.session_state["hr_aft_restow_load"] = st.number_input("AFT Restow Load", min_value=0, value=st.session_state["hr_aft_restow_load"])
    st.session_state["hr_poop_restow_load"] = st.number_input("POOP Restow Load", min_value=0, value=st.session_state["hr_poop_restow_load"])

# --- Restow Discharge ---
with st.expander("🔄 Restow: Discharge"):
    st.session_state["hr_fwd_restow_discharge"] = st.number_input("FWD Restow Discharge", min_value=0, value=st.session_state["hr_fwd_restow_discharge"])
    st.session_state["hr_mid_restow_discharge"] = st.number_input("MID Restow Discharge", min_value=0, value=st.session_state["hr_mid_restow_discharge"])
    st.session_state["hr_aft_restow_discharge"] = st.number_input("AFT Restow Discharge", min_value=0, value=st.session_state["hr_aft_restow_discharge"])
    st.session_state["hr_poop_restow_discharge"] = st.number_input("POOP Restow Discharge", min_value=0, value=st.session_state["hr_poop_restow_discharge"])

# --- Hatch Covers ---
with st.expander("🪛 Hatch Covers: Open/Close"):
    st.session_state["hr_fwd_hatch_open"] = st.number_input("FWD Hatch Open", min_value=0, value=st.session_state["hr_fwd_hatch_open"])
    st.session_state["hr_mid_hatch_open"] = st.number_input("MID Hatch Open", min_value=0, value=st.session_state["hr_mid_hatch_open"])
    st.session_state["hr_aft_hatch_open"] = st.number_input("AFT Hatch Open", min_value=0, value=st.session_state["hr_aft_hatch_open"])

    st.session_state["hr_fwd_hatch_close"] = st.number_input("FWD Hatch Close", min_value=0, value=st.session_state["hr_fwd_hatch_close"])
    st.session_state["hr_mid_hatch_close"] = st.number_input("MID Hatch Close", min_value=0, value=st.session_state["hr_mid_hatch_close"])
    st.session_state["hr_aft_hatch_close"] = st.number_input("AFT Hatch Close", min_value=0, value=st.session_state["hr_aft_hatch_close"])
    # --- PART 3 OF 5 ---

st.markdown("### 📊 Hourly Totals Tracker (Split)")

# --- Load Totals ---
with st.expander("⬆️ Load Totals"):
    st.write(f"**FWD Load:** {st.session_state['hr_fwd_load']}")
    st.write(f"**MID Load:** {st.session_state['hr_mid_load']}")
    st.write(f"**AFT Load:** {st.session_state['hr_aft_load']}")
    st.write(f"**POOP Load:** {st.session_state['hr_poop_load']}")
    st.write(f"**Total Load:** {st.session_state['hr_fwd_load'] + st.session_state['hr_mid_load'] + st.session_state['hr_aft_load'] + st.session_state['hr_poop_load']}")

# --- Discharge Totals ---
with st.expander("⬇️ Discharge Totals"):
    st.write(f"**FWD Discharge:** {st.session_state['hr_fwd_discharge']}")
    st.write(f"**MID Discharge:** {st.session_state['hr_mid_discharge']}")
    st.write(f"**AFT Discharge:** {st.session_state['hr_aft_discharge']}")
    st.write(f"**POOP Discharge:** {st.session_state['hr_poop_discharge']}")
    st.write(f"**Total Discharge:** {st.session_state['hr_fwd_discharge'] + st.session_state['hr_mid_discharge'] + st.session_state['hr_aft_discharge'] + st.session_state['hr_poop_discharge']}")

# --- Restow Load Totals ---
with st.expander("🔄 Restow Load Totals"):
    st.write(f"**FWD Restow Load:** {st.session_state['hr_fwd_restow_load']}")
    st.write(f"**MID Restow Load:** {st.session_state['hr_mid_restow_load']}")
    st.write(f"**AFT Restow Load:** {st.session_state['hr_aft_restow_load']}")
    st.write(f"**POOP Restow Load:** {st.session_state['hr_poop_restow_load']}")
    st.write(f"**Total Restow Load:** {st.session_state['hr_fwd_restow_load'] + st.session_state['hr_mid_restow_load'] + st.session_state['hr_aft_restow_load'] + st.session_state['hr_poop_restow_load']}")

# --- Restow Discharge Totals ---
with st.expander("🔄 Restow Discharge Totals"):
    st.write(f"**FWD Restow Discharge:** {st.session_state['hr_fwd_restow_discharge']}")
    st.write(f"**MID Restow Discharge:** {st.session_state['hr_mid_restow_discharge']}")
    st.write(f"**AFT Restow Discharge:** {st.session_state['hr_aft_restow_discharge']}")
    st.write(f"**POOP Restow Discharge:** {st.session_state['hr_poop_restow_discharge']}")
    st.write(f"**Total Restow Discharge:** {st.session_state['hr_fwd_restow_discharge'] + st.session_state['hr_mid_restow_discharge'] + st.session_state['hr_aft_restow_discharge'] + st.session_state['hr_poop_restow_discharge']}")

# --- Hatch Covers Totals ---
with st.expander("🪛 Hatch Covers Totals"):
    st.write(f"**FWD Hatch Open:** {st.session_state['hr_fwd_hatch_open']}")
    st.write(f"**MID Hatch Open:** {st.session_state['hr_mid_hatch_open']}")
    st.write(f"**AFT Hatch Open:** {st.session_state['hr_aft_hatch_open']}")
    st.write(f"**FWD Hatch Close:** {st.session_state['hr_fwd_hatch_close']}")
    st.write(f"**MID Hatch Close:** {st.session_state['hr_mid_hatch_close']}")
    st.write(f"**AFT Hatch Close:** {st.session_state['hr_aft_hatch_close']}")
    st.write(f"**Total Hatch Open:** {st.session_state['hr_fwd_hatch_open'] + st.session_state['hr_mid_hatch_open'] + st.session_state['hr_aft_hatch_open']}")
    st.write(f"**Total Hatch Close:** {st.session_state['hr_fwd_hatch_close'] + st.session_state['hr_mid_hatch_close'] + st.session_state['hr_aft_hatch_close']}")
    # --- PART 4 OF 5 ---

st.markdown("## ⏱ 4-Hourly Report Template")

# --- Manual 4-Hourly Inputs (Collapsed like Hourly) ---
with st.expander("⬆️ 4-Hourly Load Totals"):
    st.session_state['hr4_fwd_load'] = st.number_input("FWD Load (4H)", min_value=0, value=st.session_state.get('hr4_fwd_load', 0))
    st.session_state['hr4_mid_load'] = st.number_input("MID Load (4H)", min_value=0, value=st.session_state.get('hr4_mid_load', 0))
    st.session_state['hr4_aft_load'] = st.number_input("AFT Load (4H)", min_value=0, value=st.session_state.get('hr4_aft_load', 0))
    st.session_state['hr4_poop_load'] = st.number_input("POOP Load (4H)", min_value=0, value=st.session_state.get('hr4_poop_load', 0))

with st.expander("⬇️ 4-Hourly Discharge Totals"):
    st.session_state['hr4_fwd_discharge'] = st.number_input("FWD Discharge (4H)", min_value=0, value=st.session_state.get('hr4_fwd_discharge', 0))
    st.session_state['hr4_mid_discharge'] = st.number_input("MID Discharge (4H)", min_value=0, value=st.session_state.get('hr4_mid_discharge', 0))
    st.session_state['hr4_aft_discharge'] = st.number_input("AFT Discharge (4H)", min_value=0, value=st.session_state.get('hr4_aft_discharge', 0))
    st.session_state['hr4_poop_discharge'] = st.number_input("POOP Discharge (4H)", min_value=0, value=st.session_state.get('hr4_poop_discharge', 0))

with st.expander("🔄 4-Hourly Restow Load Totals"):
    st.session_state['hr4_fwd_restow_load'] = st.number_input("FWD Restow Load (4H)", min_value=0, value=st.session_state.get('hr4_fwd_restow_load', 0))
    st.session_state['hr4_mid_restow_load'] = st.number_input("MID Restow Load (4H)", min_value=0, value=st.session_state.get('hr4_mid_restow_load', 0))
    st.session_state['hr4_aft_restow_load'] = st.number_input("AFT Restow Load (4H)", min_value=0, value=st.session_state.get('hr4_aft_restow_load', 0))
    st.session_state['hr4_poop_restow_load'] = st.number_input("POOP Restow Load (4H)", min_value=0, value=st.session_state.get('hr4_poop_restow_load', 0))

with st.expander("🔄 4-Hourly Restow Discharge Totals"):
    st.session_state['hr4_fwd_restow_discharge'] = st.number_input("FWD Restow Discharge (4H)", min_value=0, value=st.session_state.get('hr4_fwd_restow_discharge', 0))
    st.session_state['hr4_mid_restow_discharge'] = st.number_input("MID Restow Discharge (4H)", min_value=0, value=st.session_state.get('hr4_mid_restow_discharge', 0))
    st.session_state['hr4_aft_restow_discharge'] = st.number_input("AFT Restow Discharge (4H)", min_value=0, value=st.session_state.get('hr4_aft_restow_discharge', 0))
    st.session_state['hr4_poop_restow_discharge'] = st.number_input("POOP Restow Discharge (4H)", min_value=0, value=st.session_state.get('hr4_poop_restow_discharge', 0))

with st.expander("🪛 4-Hourly Hatch Covers"):
    st.session_state['hr4_fwd_hatch_open'] = st.number_input("FWD Hatch Open (4H)", min_value=0, value=st.session_state.get('hr4_fwd_hatch_open', 0))
    st.session_state['hr4_mid_hatch_open'] = st.number_input("MID Hatch Open (4H)", min_value=0, value=st.session_state.get('hr4_mid_hatch_open', 0))
    st.session_state['hr4_aft_hatch_open'] = st.number_input("AFT Hatch Open (4H)", min_value=0, value=st.session_state.get('hr4_aft_hatch_open', 0))
    st.session_state['hr4_fwd_hatch_close'] = st.number_input("FWD Hatch Close (4H)", min_value=0, value=st.session_state.get('hr4_fwd_hatch_close', 0))
    st.session_state['hr4_mid_hatch_close'] = st.number_input("MID Hatch Close (4H)", min_value=0, value=st.session_state.get('hr4_mid_hatch_close', 0))
    st.session_state['hr4_aft_hatch_close'] = st.number_input("AFT Hatch Close (4H)", min_value=0, value=st.session_state.get('hr4_aft_hatch_close', 0))

# --- Button to populate 4-Hourly from Hourly Totals Tracker ---
if st.button("📥 Update 4-Hourly from Hourly Tracker"):
    st.session_state['hr4_fwd_load'] = st.session_state['hr_fwd_load']
    st.session_state['hr4_mid_load'] = st.session_state['hr_mid_load']
    st.session_state['hr4_aft_load'] = st.session_state['hr_aft_load']
    st.session_state['hr4_poop_load'] = st.session_state['hr_poop_load']

    st.session_state['hr4_fwd_discharge'] = st.session_state['hr_fwd_discharge']
    st.session_state['hr4_mid_discharge'] = st.session_state['hr_mid_discharge']
    st.session_state['hr4_aft_discharge'] = st.session_state['hr_aft_discharge']
    st.session_state['hr4_poop_discharge'] = st.session_state['hr_poop_discharge']

    st.session_state['hr4_fwd_restow_load'] = st.session_state['hr_fwd_restow_load']
    st.session_state['hr4_mid_restow_load'] = st.session_state['hr_mid_restow_load']
    st.session_state['hr4_aft_restow_load'] = st.session_state['hr_aft_restow_load']
    st.session_state['hr4_poop_restow_load'] = st.session_state['hr_poop_restow_load']

    st.session_state['hr4_fwd_restow_discharge'] = st.session_state['hr_fwd_restow_discharge']
    st.session_state['hr4_mid_restow_discharge'] = st.session_state['hr_mid_restow_discharge']
    st.session_state['hr4_aft_restow_discharge'] = st.session_state['hr_aft_restow_discharge']
    st.session_state['hr4_poop_restow_discharge'] = st.session_state['hr_poop_restow_discharge']

    st.session_state['hr4_fwd_hatch_open'] = st.session_state['hr_fwd_hatch_open']
    st.session_state['hr4_mid_hatch_open'] = st.session_state['hr_mid_hatch_open']
    st.session_state['hr4_aft_hatch_open'] = st.session_state['hr_aft_hatch_open']
    st.session_state['hr4_fwd_hatch_close'] = st.session_state['hr_fwd_hatch_close']
    st.session_state['hr4_mid_hatch_close'] = st.session_state['hr_mid_hatch_close']
    st.session_state['hr4_aft_hatch_close'] = st.session_state['hr_aft_hatch_close']

    st.success("✅ 4-Hourly Template updated from Hourly Tracker!")

# --- Reset Button for 4-Hourly ---
if st.button("♻️ Reset 4-Hourly Inputs"):
    for key in list(st.session_state.keys()):
        if key.startswith("hr4_"):
            st.session_state[key] = 0
    st.success("✅ 4-Hourly Inputs Reset")
    # --- PART 5 OF 5 ---

st.markdown("## 📊 Cumulative Totals")

# --- Auto-update Cumulative from Hourly + 4-Hourly ---
st.session_state['cum_fwd_load'] = st.session_state.get('cum_fwd_load', 0) + st.session_state['hr_fwd_load']
st.session_state['cum_mid_load'] = st.session_state.get('cum_mid_load', 0) + st.session_state['hr_mid_load']
st.session_state['cum_aft_load'] = st.session_state.get('cum_aft_load', 0) + st.session_state['hr_aft_load']
st.session_state['cum_poop_load'] = st.session_state.get('cum_poop_load', 0) + st.session_state['hr_poop_load']

st.session_state['cum_fwd_discharge'] = st.session_state.get('cum_fwd_discharge', 0) + st.session_state['hr_fwd_discharge']
st.session_state['cum_mid_discharge'] = st.session_state.get('cum_mid_discharge', 0) + st.session_state['hr_mid_discharge']
st.session_state['cum_aft_discharge'] = st.session_state.get('cum_aft_discharge', 0) + st.session_state['hr_aft_discharge']
st.session_state['cum_poop_discharge'] = st.session_state.get('cum_poop_discharge', 0) + st.session_state['hr_poop_discharge']

st.session_state['cum_fwd_restow_load'] = st.session_state.get('cum_fwd_restow_load', 0) + st.session_state['hr_fwd_restow_load']
st.session_state['cum_mid_restow_load'] = st.session_state.get('cum_mid_restow_load', 0) + st.session_state['hr_mid_restow_load']
st.session_state['cum_aft_restow_load'] = st.session_state.get('cum_aft_restow_load', 0) + st.session_state['hr_aft_restow_load']
st.session_state['cum_poop_restow_load'] = st.session_state.get('cum_poop_restow_load', 0) + st.session_state['hr_poop_restow_load']

st.session_state['cum_fwd_restow_discharge'] = st.session_state.get('cum_fwd_restow_discharge', 0) + st.session_state['hr_fwd_restow_discharge']
st.session_state['cum_mid_restow_discharge'] = st.session_state.get('cum_mid_restow_discharge', 0) + st.session_state['hr_mid_restow_discharge']
st.session_state['cum_aft_restow_discharge'] = st.session_state.get('cum_aft_restow_discharge', 0) + st.session_state['hr_aft_restow_discharge']
st.session_state['cum_poop_restow_discharge'] = st.session_state.get('cum_poop_restow_discharge', 0) + st.session_state['hr_poop_restow_discharge']

st.session_state['cum_fwd_hatch_open'] = st.session_state.get('cum_fwd_hatch_open', 0) + st.session_state['hr_fwd_hatch_open']
st.session_state['cum_mid_hatch_open'] = st.session_state.get('cum_mid_hatch_open', 0) + st.session_state['hr_mid_hatch_open']
st.session_state['cum_aft_hatch_open'] = st.session_state.get('cum_aft_hatch_open', 0) + st.session_state['hr_aft_hatch_open']
st.session_state['cum_fwd_hatch_close'] = st.session_state.get('cum_fwd_hatch_close', 0) + st.session_state['hr_fwd_hatch_close']
st.session_state['cum_mid_hatch_close'] = st.session_state.get('cum_mid_hatch_close', 0) + st.session_state['hr_mid_hatch_close']
st.session_state['cum_aft_hatch_close'] = st.session_state.get('cum_aft_hatch_close', 0) + st.session_state['hr_aft_hatch_close']

# --- Preview Template ---
st.markdown("## 📝 Preview WhatsApp Template")

preview_text = f"""
📢 *Vessel Update*
Vessel: {st.session_state.get("vessel_name", "")}
Berth: {st.session_state.get("berth", "")}
Date: {st.session_state.get("date", "")}
Hour: {st.session_state.get("hourly_time", "")}

⬆️ *Load (Hourly / Cumulative)*  
FWD: {st.session_state['hr_fwd_load']} / {st.session_state['cum_fwd_load']}  
MID: {st.session_state['hr_mid_load']} / {st.session_state['cum_mid_load']}  
AFT: {st.session_state['hr_aft_load']} / {st.session_state['cum_aft_load']}  
POOP: {st.session_state['hr_poop_load']} / {st.session_state['cum_poop_load']}  

⬇️ *Discharge (Hourly / Cumulative)*  
FWD: {st.session_state['hr_fwd_discharge']} / {st.session_state['cum_fwd_discharge']}  
MID: {st.session_state['hr_mid_discharge']} / {st.session_state['cum_mid_discharge']}  
AFT: {st.session_state['hr_aft_discharge']} / {st.session_state['cum_aft_discharge']}  
POOP: {st.session_state['hr_poop_discharge']} / {st.session_state['cum_poop_discharge']}  

🔄 *Restow Load (Hourly / Cumulative)*  
FWD: {st.session_state['hr_fwd_restow_load']} / {st.session_state['cum_fwd_restow_load']}  
MID: {st.session_state['hr_mid_restow_load']} / {st.session_state['cum_mid_restow_load']}  
AFT: {st.session_state['hr_aft_restow_load']} / {st.session_state['cum_aft_restow_load']}  
POOP: {st.session_state['hr_poop_restow_load']} / {st.session_state['cum_poop_restow_load']}  

🔄 *Restow Discharge (Hourly / Cumulative)*  
FWD: {st.session_state['hr_fwd_restow_discharge']} / {st.session_state['cum_fwd_restow_discharge']}  
MID: {st.session_state['hr_mid_restow_discharge']} / {st.session_state['cum_mid_restow_discharge']}  
AFT: {st.session_state['hr_aft_restow_discharge']} / {st.session_state['cum_aft_restow_discharge']}  
POOP: {st.session_state['hr_poop_restow_discharge']} / {st.session_state['cum_poop_restow_discharge']}  

🪛 *Hatch Covers (Hourly / Cumulative)*  
FWD Open/Close: {st.session_state['hr_fwd_hatch_open']} / {st.session_state['cum_fwd_hatch_open']} | {st.session_state['hr_fwd_hatch_close']} / {st.session_state['cum_fwd_hatch_close']}  
MID Open/Close: {st.session_state['hr_mid_hatch_open']} / {st.session_state['cum_mid_hatch_open']} | {st.session_state['hr_mid_hatch_close']} / {st.session_state['cum_mid_hatch_close']}  
AFT Open/Close: {st.session_state['hr_aft_hatch_open']} / {st.session_state['cum_aft_hatch_open']} | {st.session_state['hr_aft_hatch_close']} / {st.session_state['cum_aft_hatch_close']}  
"""

st.text_area("Preview Message", preview_text, height=600)
