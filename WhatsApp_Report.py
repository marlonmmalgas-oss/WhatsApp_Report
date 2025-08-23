import streamlit as st
from datetime import datetime, timedelta

# -------------------------
# Session State Initialization
# -------------------------
def init_session_state():
    # Hourly crane moves
    keys_hourly = [
        "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
        "hr_fwd_discharge", "hr_mid_discharge", "hr_aft_discharge", "hr_poop_discharge",
        "hr_restow_load", "hr_restow_discharge",
        "hr_hatch_open", "hr_hatch_close",
    ]
    for key in keys_hourly:
        if key not in st.session_state:
            st.session_state[key] = 0

    # 4-hourly totals
    keys_4h = [
        "tot_fwd_load", "tot_mid_load", "tot_aft_load", "tot_poop_load",
        "tot_fwd_discharge", "tot_mid_discharge", "tot_aft_discharge", "tot_poop_discharge",
        "tot_restow_load", "tot_restow_discharge",
        "tot_hatch_open", "tot_hatch_close",
    ]
    for key in keys_4h:
        if key not in st.session_state:
            st.session_state[key] = 0

    # Other
    if "hourly_index" not in st.session_state:
        st.session_state["hourly_index"] = 0
    if "planned_load" not in st.session_state:
        st.session_state["planned_load"] = 0
    if "planned_discharge" not in st.session_state:
        st.session_state["planned_discharge"] = 0

init_session_state()

# -------------------------
# Vessel Info
# -------------------------
st.title("🛳 Vessel Hourly & 4-Hourly Moves Tracker")

vessel_name = st.text_input("Vessel Name", "")
berthed_date = st.date_input("Berthed Date", datetime.today())

st.write("---")

# -------------------------
# Select Hourly Time
# -------------------------
hours_list = [f"{h:02d}:00" for h in range(24)]
default_hour = hours_list[st.session_state["hourly_index"] % 24]
hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))
hourly_time_end_4h_index = (st.session_state["hourly_index"] + 4) % 24
hourly_time_end_4h = hours_list[hourly_time_end_4h_index]
st.write("## ⏱ Hourly Moves Input")

# -------------------------
# Crane Moves Collapsible
# -------------------------
with st.expander("🛠 Crane Moves"):
    st.subheader("Load")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state["hr_fwd_load"] = st.number_input("FWD Load (hour)", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
    with col2:
        st.session_state["hr_mid_load"] = st.number_input("MID Load (hour)", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
    with col3:
        st.session_state["hr_aft_load"] = st.number_input("AFT Load (hour)", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
    with col4:
        st.session_state["hr_poop_load"] = st.number_input("POOP Load (hour)", min_value=0, value=st.session_state["hr_poop_load"], key="hr_poop_load")

    st.subheader("Discharge")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state["hr_fwd_discharge"] = st.number_input("FWD Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_discharge"], key="hr_fwd_discharge")
    with col2:
        st.session_state["hr_mid_discharge"] = st.number_input("MID Discharge (hour)", min_value=0, value=st.session_state["hr_mid_discharge"], key="hr_mid_discharge")
    with col3:
        st.session_state["hr_aft_discharge"] = st.number_input("AFT Discharge (hour)", min_value=0, value=st.session_state["hr_aft_discharge"], key="hr_aft_discharge")
    with col4:
        st.session_state["hr_poop_discharge"] = st.number_input("POOP Discharge (hour)", min_value=0, value=st.session_state["hr_poop_discharge"], key="hr_poop_discharge")

# -------------------------
# Restows Collapsible
# -------------------------
with st.expander("🔄 Restows"):
    st.session_state["hr_restow_load"] = st.number_input("Restow Load (hour)", min_value=0, value=st.session_state["hr_restow_load"], key="hr_restow_load")
    st.session_state["hr_restow_discharge"] = st.number_input("Restow Discharge (hour)", min_value=0, value=st.session_state["hr_restow_discharge"], key="hr_restow_discharge")

# -------------------------
# Hatch Covers Collapsible
# -------------------------
with st.expander("🧰 Hatch Covers"):
    st.session_state["hr_hatch_open"] = st.number_input("Hatch Open (hour)", min_value=0, value=st.session_state["hr_hatch_open"], key="hr_hatch_open")
    st.session_state["hr_hatch_close"] = st.number_input("Hatch Close (hour)", min_value=0, value=st.session_state["hr_hatch_close"], key="hr_hatch_close")

# -------------------------
# Idle / Delays
# -------------------------
with st.expander("⏸ Idle / Delays"):
    num_idle = st.number_input("Number of Idle Entries", min_value=0, value=0)
    idle_entries = []
    for i in range(num_idle):
        entry = st.text_input(f"Idle Entry {i+1}", "")
        idle_entries.append(entry)
        st.write("## 📊 4-Hourly Totals")

# Function to calculate totals
def calculate_4h_totals():
    totals = {
        "fwd_load": st.session_state["hr_fwd_load"],
        "mid_load": st.session_state["hr_mid_load"],
        "aft_load": st.session_state["hr_aft_load"],
        "poop_load": st.session_state["hr_poop_load"],
        "fwd_discharge": st.session_state["hr_fwd_discharge"],
        "mid_discharge": st.session_state["hr_mid_discharge"],
        "aft_discharge": st.session_state["hr_aft_discharge"],
        "poop_discharge": st.session_state["hr_poop_discharge"],
        "restow_load": st.session_state["hr_restow_load"],
        "restow_discharge": st.session_state["hr_restow_discharge"],
        "hatch_open": st.session_state["hr_hatch_open"],
        "hatch_close": st.session_state["hr_hatch_close"]
    }
    return totals

# Collapsible to show totals
with st.expander("📈 4-Hourly Counts (Editable)"):
    totals_4h = calculate_4h_totals()
    for key, value in totals_4h.items():
        totals_4h[key] = st.number_input(f"{key.replace('_',' ').title()} (4h)", min_value=0, value=value, key=f"4h_{key}")

# -------------------------
# Reset Buttons
# -------------------------
st.write("## 🔄 Reset Options")
col_reset1, col_reset2 = st.columns(2)

with col_reset1:
    if st.button("Reset Hourly Inputs"):
        for key in ["hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
                    "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_poop_discharge",
                    "hr_restow_load","hr_restow_discharge","hr_hatch_open","hr_hatch_close"]:
            st.session_state[key] = 0
        st.experimental_rerun()

with col_reset2:
    if st.button("Reset 4-Hourly Totals"):
        for key in totals_4h.keys():
            st.session_state[f"4h_{key}"] = 0
        st.experimental_rerun()
        st.write("## 📱 WhatsApp Report Generator")

from datetime import datetime, timedelta

# Automatic date with picker
default_date = datetime.today()
report_date = st.date_input("Select Report Date", value=default_date)

# Automatic hourly time update
if "hour_index" not in st.session_state:
    st.session_state.hour_index = 0
hours_list = [f"{str(h).zfill(2)}h00" for h in range(24)]
hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=st.session_state.hour_index)

# Update next hour automatically after generating template
def increment_hour_index():
    st.session_state.hour_index = (st.session_state.hour_index + 1) % 24

# Generate Hourly WhatsApp Template
if st.button("Generate Hourly Template"):
    hour_template = f"""
🛳 Vessel Hourly Report
📅 Date: {report_date.strftime('%Y-%m-%d')}
🕓 Hour: {hourly_time}

Crane Moves:
FWD Load: {st.session_state['hr_fwd_load']}
MID Load: {st.session_state['hr_mid_load']}
AFT Load: {st.session_state['hr_aft_load']}
POOP Load: {st.session_state['hr_poop_load']}

FWD Discharge: {st.session_state['hr_fwd_discharge']}
MID Discharge: {st.session_state['hr_mid_discharge']}
AFT Discharge: {st.session_state['hr_aft_discharge']}
POOP Discharge: {st.session_state['hr_poop_discharge']}

Restow Load: {st.session_state['hr_restow_load']}
Restow Discharge: {st.session_state['hr_restow_discharge']}

Hatch Covers Open: {st.session_state['hr_hatch_open']}
Hatch Covers Close: {st.session_state['hr_hatch_close']}
"""
    st.text_area("Hourly WhatsApp Template", value=hour_template, height=400)
    increment_hour_index()

# Generate 4-Hourly WhatsApp Template
if st.button("Generate 4-Hourly Template"):
    four_hour_template = f"""
🛳 Vessel 4-Hourly Report
📅 Date: {report_date.strftime('%Y-%m-%d')}
🕓 Period: {hourly_time} - {hours_list[(st.session_state.hour_index-1)%24]}

Crane Moves (Total 4h):
FWD Load: {st.session_state['4h_fwd_load']}
MID Load: {st.session_state['4h_mid_load']}
AFT Load: {st.session_state['4h_aft_load']}
POOP Load: {st.session_state['4h_poop_load']}

FWD Discharge: {st.session_state['4h_fwd_discharge']}
MID Discharge: {st.session_state['4h_mid_discharge']}
AFT Discharge: {st.session_state['4h_aft_discharge']}
POOP Discharge: {st.session_state['4h_poop_discharge']}

Restow Load: {st.session_state['4h_restow_load']}
Restow Discharge: {st.session_state['4h_restow_discharge']}

Hatch Covers Open: {st.session_state['4h_hatch_open']}
Hatch Covers Close: {st.session_state['4h_hatch_close']}
"""
    st.text_area("4-Hourly WhatsApp Template", value=four_hour_template, height=500)
    st.write("## ⏸ Idle / Delays Tracker")

# Idle entries (collapsible)
with st.expander("Idle / Delays"):
    if "idle_entries" not in st.session_state:
        st.session_state.idle_entries = []

    num_idle = st.number_input("Number of Idle Entries", min_value=0, value=len(st.session_state.idle_entries), step=1)
    
    # Adjust list size if changed
    while len(st.session_state.idle_entries) < num_idle:
        st.session_state.idle_entries.append({"reason": "", "duration": 0})
    while len(st.session_state.idle_entries) > num_idle:
        st.session_state.idle_entries.pop()

    for i in range(num_idle):
        st.session_state.idle_entries[i]["reason"] = st.text_input(f"Idle Reason {i+1}", value=st.session_state.idle_entries[i]["reason"])
        st.session_state.idle_entries[i]["duration"] = st.number_input(f"Idle Duration {i+1} (min)", min_value=0, value=st.session_state.idle_entries[i]["duration"])

# Reset buttons for hourly and 4-hourly
def reset_hourly():
    for section in ["hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
                    "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_poop_discharge",
                    "hr_restow_load","hr_restow_discharge","hr_hatch_open","hr_hatch_close"]:
        st.session_state[section] = 0

def reset_4hourly():
    for section in ["4h_fwd_load","4h_mid_load","4h_aft_load","4h_poop_load",
                    "4h_fwd_discharge","4h_mid_discharge","4h_aft_discharge","4h_poop_discharge",
                    "4h_restow_load","4h_restow_discharge","4h_hatch_open","4h_hatch_close"]:
        st.session_state[section] = 0

if st.button("Reset Hourly"):
    reset_hourly()

if st.button("Reset 4-Hourly"):
    reset_4hourly()

# Hourly totals tracker (collapsible)
with st.expander("Hourly Totals Tracker (4h)"):
    st.write("This section tracks hourly totals across cranes for 4-hour aggregation.")
    for section in ["fwd_load","mid_load","aft_load","poop_load",
                    "fwd_discharge","mid_discharge","aft_discharge","poop_discharge",
                    "restow_load","restow_discharge",
                    "hatch_open","hatch_close"]:
        key = f"track_{section}"
        if key not in st.session_state:
            st.session_state[key] = 0
        st.session_state[key] = st.number_input(f"Total {section.replace('_',' ').title()} (4h)", min_value=0, value=st.session_state[key])
        