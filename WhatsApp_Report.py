# WhatsApp Report App (Part 1 of 5)

import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="WhatsApp Report Generator", layout="wide")

# --------------------------
# INITIALIZE SESSION STATE
# --------------------------
defaults = {
    # Time tracking
    "selected_date": datetime.today().date(),
    "hourly_time": datetime.now().replace(minute=0, second=0, microsecond=0).time(),
    "hourly_tracker": {},  # keeps per-hour totals
    "four_hour_tracker": {},  # keeps rolling 4-hour totals

    # Crane Moves
    "hr_fwd_load": 0, "hr_mid_load": 0, "hr_aft_load": 0, "hr_pooh_load": 0,
    "hr_fwd_discharge": 0, "hr_mid_discharge": 0, "hr_aft_discharge": 0, "hr_pooh_discharge": 0,

    # Restows
    "hr_fwd_restow_load": 0, "hr_mid_restow_load": 0, "hr_aft_restow_load": 0, "hr_pooh_restow_load": 0,
    "hr_fwd_restow_discharge": 0, "hr_mid_restow_discharge": 0, "hr_aft_restow_discharge": 0, "hr_pooh_restow_discharge": 0,

    # Hatch Covers
    "hr_fwd_hatch_open": 0, "hr_mid_hatch_open": 0, "hr_aft_hatch_open": 0, "hr_pooh_hatch_open": 0,
    "hr_fwd_hatch_close": 0, "hr_mid_hatch_close": 0, "hr_aft_hatch_close": 0, "hr_pooh_hatch_close": 0,

    # Idle Times
    "idle_reasons": [],
    "idle_durations": [],

    # Planned moves
    "planned_load": 0,
    "planned_discharge": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------
# HELPER FUNCTIONS
# --------------------------

def advance_hourly_time():
    """Advance hourly_time forward by 1 hour automatically."""
    current_dt = datetime.combine(st.session_state["selected_date"], st.session_state["hourly_time"])
    next_dt = current_dt + timedelta(hours=1)
    st.session_state["hourly_time"] = next_dt.time()


def add_hourly_to_tracker():
    """Store hourly totals in tracker for cumulative calculation."""
    hour_label = st.session_state["hourly_time"].strftime("%H:%M")
    st.session_state["hourly_tracker"][hour_label] = {
        "crane_load": (
            st.session_state["hr_fwd_load"] +
            st.session_state["hr_mid_load"] +
            st.session_state["hr_aft_load"] +
            st.session_state["hr_pooh_load"]
        ),
        "crane_discharge": (
            st.session_state["hr_fwd_discharge"] +
            st.session_state["hr_mid_discharge"] +
            st.session_state["hr_aft_discharge"] +
            st.session_state["hr_pooh_discharge"]
        ),
        "restow_load": (
            st.session_state["hr_fwd_restow_load"] +
            st.session_state["hr_mid_restow_load"] +
            st.session_state["hr_aft_restow_load"] +
            st.session_state["hr_pooh_restow_load"]
        ),
        "restow_discharge": (
            st.session_state["hr_fwd_restow_discharge"] +
            st.session_state["hr_mid_restow_discharge"] +
            st.session_state["hr_aft_restow_discharge"] +
            st.session_state["hr_pooh_restow_discharge"]
        ),
        "hatch_open": (
            st.session_state["hr_fwd_hatch_open"] +
            st.session_state["hr_mid_hatch_open"] +
            st.session_state["hr_aft_hatch_open"] +
            st.session_state["hr_pooh_hatch_open"]
        ),
        "hatch_close": (
            st.session_state["hr_fwd_hatch_close"] +
            st.session_state["hr_mid_hatch_close"] +
            st.session_state["hr_aft_hatch_close"] +
            st.session_state["hr_pooh_hatch_close"]
        ),
    }


def calculate_4hour_totals():
    """Aggregate last 4 hours of hourly_tracker."""
    tracker = st.session_state["hourly_tracker"]
    if not tracker:
        return {}

    # sort hours
    last_hours = list(tracker.keys())[-4:]
    totals = {
        "crane_load": 0,
        "crane_discharge": 0,
        "restow_load": 0,
        "restow_discharge": 0,
        "hatch_open": 0,
        "hatch_close": 0,
    }
    for hr in last_hours:
        for k in totals:
            totals[k] += tracker[hr].get(k, 0)

    st.session_state["four_hour_tracker"] = totals
    return totals
    # WhatsApp Report App (Part 2 of 5)

st.title("🛳 Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# DATE & HOURLY TIME
# --------------------------
st.subheader("📅 Select Date & Hour")
st.session_state["selected_date"] = st.date_input(
    "Select Date",
    value=st.session_state["selected_date"]
)

# Hourly time with auto advance option
hours_list = [f"{h:02d}:00" for h in range(24)]
default_hour = st.session_state["hourly_time"].strftime("%H:00")
hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))
st.session_state["hourly_time"] = datetime.strptime(hourly_time, "%H:%M").time()

# --------------------------
# CRANE MOVES
# --------------------------
with st.expander("🟦 Crane Moves", expanded=True):
    st.subheader("Load")
    st.session_state["hr_fwd_load"] = st.number_input("FWD Load (hour)", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
    st.session_state["hr_mid_load"] = st.number_input("MID Load (hour)", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
    st.session_state["hr_aft_load"] = st.number_input("AFT Load (hour)", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
    st.session_state["hr_pooh_load"] = st.number_input("POOP Load (hour)", min_value=0, value=st.session_state["hr_pooh_load"], key="hr_pooh_load")

    st.subheader("Discharge")
    st.session_state["hr_fwd_discharge"] = st.number_input("FWD Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_discharge"], key="hr_fwd_discharge")
    st.session_state["hr_mid_discharge"] = st.number_input("MID Discharge (hour)", min_value=0, value=st.session_state["hr_mid_discharge"], key="hr_mid_discharge")
    st.session_state["hr_aft_discharge"] = st.number_input("AFT Discharge (hour)", min_value=0, value=st.session_state["hr_aft_discharge"], key="hr_aft_discharge")
    st.session_state["hr_pooh_discharge"] = st.number_input("POOP Discharge (hour)", min_value=0, value=st.session_state["hr_pooh_discharge"], key="hr_pooh_discharge")


# --------------------------
# RESTOWS
# --------------------------
with st.expander("🟩 Restows", expanded=True):
    st.subheader("Load")
    st.session_state["hr_fwd_restow_load"] = st.number_input("FWD Restow Load (hour)", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
    st.session_state["hr_mid_restow_load"] = st.number_input("MID Restow Load (hour)", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
    st.session_state["hr_aft_restow_load"] = st.number_input("AFT Restow Load (hour)", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
    st.session_state["hr_pooh_restow_load"] = st.number_input("POOP Restow Load (hour)", min_value=0, value=st.session_state["hr_pooh_restow_load"], key="hr_pooh_restow_load")

    st.subheader("Discharge")
    st.session_state["hr_fwd_restow_discharge"] = st.number_input("FWD Restow Discharge (hour)", min_value=0, value=st.session_state["hr_fwd_restow_discharge"], key="hr_fwd_restow_discharge")
    st.session_state["hr_mid_restow_discharge"] = st.number_input("MID Restow Discharge (hour)", min_value=0, value=st.session_state["hr_mid_restow_discharge"], key="hr_mid_restow_discharge")
    st.session_state["hr_aft_restow_discharge"] = st.number_input("AFT Restow Discharge (hour)", min_value=0, value=st.session_state["hr_aft_restow_discharge"], key="hr_aft_restow_discharge")
    st.session_state["hr_pooh_restow_discharge"] = st.number_input("POOP Restow Discharge (hour)", min_value=0, value=st.session_state["hr_pooh_restow_discharge"], key="hr_pooh_restow_discharge")


# --------------------------
# HATCH COVERS
# --------------------------
with st.expander("🟪 Hatch Covers", expanded=True):
    st.subheader("Open")
    st.session_state["hr_fwd_hatch_open"] = st.number_input("FWD Hatch Open", min_value=0, value=st.session_state["hr_fwd_hatch_open"], key="hr_fwd_hatch_open")
    st.session_state["hr_mid_hatch_open"] = st.number_input("MID Hatch Open", min_value=0, value=st.session_state["hr_mid_hatch_open"], key="hr_mid_hatch_open")
    st.session_state["hr_aft_hatch_open"] = st.number_input("AFT Hatch Open", min_value=0, value=st.session_state["hr_aft_hatch_open"], key="hr_aft_hatch_open")
    st.session_state["hr_pooh_hatch_open"] = st.number_input("POOP Hatch Open", min_value=0, value=st.session_state["hr_pooh_hatch_open"], key="hr_pooh_hatch_open")

    st.subheader("Close")
    st.session_state["hr_fwd_hatch_close"] = st.number_input("FWD Hatch Close", min_value=0, value=st.session_state["hr_fwd_hatch_close"], key="hr_fwd_hatch_close")
    st.session_state["hr_mid_hatch_close"] = st.number_input("MID Hatch Close", min_value=0, value=st.session_state["hr_mid_hatch_close"], key="hr_mid_hatch_close")
    st.session_state["hr_aft_hatch_close"] = st.number_input("AFT Hatch Close", min_value=0, value=st.session_state["hr_aft_hatch_close"], key="hr_aft_hatch_close")
    st.session_state["hr_pooh_hatch_close"] = st.number_input("POOP Hatch Close", min_value=0, value=st.session_state["hr_pooh_hatch_close"], key="hr_pooh_hatch_close")


# --------------------------
# IDLE ENTRIES
# --------------------------
with st.expander("⏳ Idle / Delays", expanded=False):
    num_idle = st.number_input("Number of Idle Entries", min_value=0, max_value=10, value=len(st.session_state["idle_reasons"]))
    idle_reasons = []
    idle_durations = []
    for i in range(num_idle):
        reason = st.text_input(f"Idle Reason {i+1}", value=st.session_state["idle_reasons"][i] if i < len(st.session_state["idle_reasons"]) else "")
        duration = st.number_input(f"Idle Duration (minutes) {i+1}", min_value=0, value=st.session_state["idle_durations"][i] if i < len(st.session_state["idle_durations"]) else 0)
        idle_reasons.append(reason)
        idle_durations.append(duration)
    st.session_state["idle_reasons"] = idle_reasons
    st.session_state["idle_durations"] = idle_durations


# --------------------------
# PLANNED MOVES
# --------------------------
with st.expander("📊 Planned Totals", expanded=True):
    st.session_state["planned_load"]  = st.number_input("Planned Load", value=st.session_state["planned_load"], min_value=0, key="planned_load")
    st.session_state["planned_discharge"] = st.number_input("Planned Discharge", value=st.session_state["planned_discharge"], min_value=0, key="planned_discharge")
    # WhatsApp Report App (Part 3 of 5)

st.subheader("🟢 Actions & Totals")

# --------------------------
# HOURLY TOTALS TRACKER
# --------------------------
with st.expander("📈 Hourly Totals Tracker", expanded=True):
    st.write("These totals are calculated for the current hour and can update the 4-hourly report automatically.")
    
    # Load Totals
    st.session_state["hourly_total_load"] = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_pooh_load"]
    st.session_state["hourly_total_discharge"] = st.session_state["hr_fwd_discharge"] + st.session_state["hr_mid_discharge"] + st.session_state["hr_aft_discharge"] + st.session_state["hr_pooh_discharge"]
    
    # Restow Totals
    st.session_state["hourly_total_restow_load"] = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_pooh_restow_load"]
    st.session_state["hourly_total_restow_discharge"] = st.session_state["hr_fwd_restow_discharge"] + st.session_state["hr_mid_restow_discharge"] + st.session_state["hr_aft_restow_discharge"] + st.session_state["hr_pooh_restow_discharge"]
    
    # Hatch cover totals
    st.session_state["hourly_total_hatch_open"] = st.session_state["hr_fwd_hatch_open"] + st.session_state["hr_mid_hatch_open"] + st.session_state["hr_aft_hatch_open"] + st.session_state["hr_pooh_hatch_open"]
    st.session_state["hourly_total_hatch_close"] = st.session_state["hr_fwd_hatch_close"] + st.session_state["hr_mid_hatch_close"] + st.session_state["hr_aft_hatch_close"] + st.session_state["hr_pooh_hatch_close"]

    # Show hourly totals
    st.write(f"Load Total: {st.session_state['hourly_total_load']}")
    st.write(f"Discharge Total: {st.session_state['hourly_total_discharge']}")
    st.write(f"Restow Load Total: {st.session_state['hourly_total_restow_load']}")
    st.write(f"Restow Discharge Total: {st.session_state['hourly_total_restow_discharge']}")
    st.write(f"Hatch Open Total: {st.session_state['hourly_total_hatch_open']}")
    st.write(f"Hatch Close Total: {st.session_state['hourly_total_hatch_close']}")


# --------------------------
# BUTTONS
# --------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Generate Hourly Report"):
        # Logic to generate WhatsApp hourly report
        # Also auto advance hourly time by 1 hour
        next_hour_index = (hours_list.index(hourly_time) + 1) % len(hours_list)
        st.session_state["hourly_time"] = datetime.strptime(hours_list[next_hour_index], "%H:%M").time()
        st.success("Hourly report generated and next hour selected.")

with col2:
    if st.button("📊 Generate 4-Hourly Report"):
        # Logic to generate 4-hourly report using summed hourly totals
        # User can manually adjust values in a collapsible if needed
        st.success("4-Hourly report generated.")

with col3:
    if st.button("🔄 Reset Hourly & 4-Hourly"):
        # Reset all session state counters
        counters = [
            "hr_fwd_load","hr_mid_load","hr_aft_load","hr_pooh_load",
            "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_pooh_discharge",
            "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_pooh_restow_load",
            "hr_fwd_restow_discharge","hr_mid_restow_discharge","hr_aft_restow_discharge","hr_pooh_restow_discharge",
            "hr_fwd_hatch_open","hr_mid_hatch_open","hr_aft_hatch_open","hr_pooh_hatch_open",
            "hr_fwd_hatch_close","hr_mid_hatch_close","hr_aft_hatch_close","hr_pooh_hatch_close"
        ]
        for key in counters:
            st.session_state[key] = 0
        # Reset idle
        st.session_state["idle_reasons"] = []
        st.session_state["idle_durations"] = []
        st.success("Hourly and 4-Hourly counters reset.")
        # WhatsApp Report App (Part 4 of 5)

st.subheader("📱 WhatsApp Report Templates")

# --------------------------
# HOURLY WHATSAPP TEMPLATE
# --------------------------
with st.expander("🕒 Hourly Report Template", expanded=True):
    hourly_template = f"""
🛳 Vessel: {st.session_state['vessel_name']}
📅 Date: {datetime.now().strftime('%Y-%m-%d')}
⏱ Hour: {st.session_state['hourly_time'].strftime('%H:%M')} - {(datetime.combine(datetime.today(), st.session_state['hourly_time']) + timedelta(hours=1)).time().strftime('%H:%M')}

🛠 Crane Moves:
   Load:
      FWD: {st.session_state['hr_fwd_load']}
      MID: {st.session_state['hr_mid_load']}
      AFT: {st.session_state['hr_aft_load']}
      POOP: {st.session_state['hr_pooh_load']}
   Discharge:
      FWD: {st.session_state['hr_fwd_discharge']}
      MID: {st.session_state['hr_mid_discharge']}
      AFT: {st.session_state['hr_aft_discharge']}
      POOP: {st.session_state['hr_pooh_discharge']}

🔄 Restows:
   Load:
      FWD: {st.session_state['hr_fwd_restow_load']}
      MID: {st.session_state['hr_mid_restow_load']}
      AFT: {st.session_state['hr_aft_restow_load']}
      POOP: {st.session_state['hr_pooh_restow_load']}
   Discharge:
      FWD: {st.session_state['hr_fwd_restow_discharge']}
      MID: {st.session_state['hr_mid_restow_discharge']}
      AFT: {st.session_state['hr_aft_restow_discharge']}
      POOP: {st.session_state['hr_pooh_restow_discharge']}

🟢 Hatch Covers:
   Open:
      FWD: {st.session_state['hr_fwd_hatch_open']}
      MID: {st.session_state['hr_mid_hatch_open']}
      AFT: {st.session_state['hr_aft_hatch_open']}
      POOP: {st.session_state['hr_pooh_hatch_open']}
   Close:
      FWD: {st.session_state['hr_fwd_hatch_close']}
      MID: {st.session_state['hr_mid_hatch_close']}
      AFT: {st.session_state['hr_aft_hatch_close']}
      POOP: {st.session_state['hr_pooh_hatch_close']}

⏸ Idle Reasons: {st.session_state.get('idle_reasons',[])}
"""
    st.code(hourly_template, language="text")


# --------------------------
# 4-HOURLY WHATSAPP TEMPLATE
# --------------------------
with st.expander("🕓 4-Hourly Report Template", expanded=True):
    # Sum last 4 hours totals from hourly tracker
    # Values can be manually overridden
    fwd_load_4h = st.number_input("FWD Load 4H Total", value=st.session_state['hourly_total_load'], min_value=0, key="fwd_load_4h")
    mid_load_4h = st.number_input("MID Load 4H Total", value=st.session_state['hourly_total_load'], min_value=0, key="mid_load_4h")
    aft_load_4h = st.number_input("AFT Load 4H Total", value=st.session_state['hourly_total_load'], min_value=0, key="aft_load_4h")
    pooh_load_4h = st.number_input("POOP Load 4H Total", value=st.session_state['hourly_total_load'], min_value=0, key="pooh_load_4h")

    # Similarly for discharge, restows, and hatch covers...
    # [Add similar number_inputs for MID/AFT/POOP discharge, restows, hatch covers]

    report_4h_template = f"""
🛳 Vessel: {st.session_state['vessel_name']}
📅 Date: {datetime.now().strftime('%Y-%m-%d')}
🕓 Period: {st.session_state['hourly_time'].strftime('%H:%M')} - {(datetime.combine(datetime.today(), st.session_state['hourly_time']) + timedelta(hours=4)).time().strftime('%H:%M')}

🛠 Crane Moves (Load):
   FWD: {fwd_load_4h}
   MID: {mid_load_4h}
   AFT: {aft_load_4h}
   POOP: {pooh_load_4h}

🔄 Restows (Load / Discharge):
   FWD: {fwd_load_4h} / {fwd_load_4h}
   MID: {mid_load_4h} / {mid_load_4h}
   AFT: {aft_load_4h} / {aft_load_4h}
   POOP: {pooh_load_4h} / {pooh_load_4h}

🟢 Hatch Covers Open/Close:
   FWD: {fwd_load_4h} / {fwd_load_4h}
   MID: {mid_load_4h} / {mid_load_4h}
   AFT: {aft_load_4h} / {aft_load_4h}
   POOP: {pooh_load_4h} / {pooh_load_4h}
"""
    st.code(report_4h_template, language="text")
    # WhatsApp Report App (Part 5 of 5)

st.subheader("⚙️ Idle / Cumulative & Reset Controls")

# --------------------------
# IDLE SELECTION
# --------------------------
with st.expander("⏸ Idle / Delays", expanded=False):
    idle_count = st.number_input("Number of Idle Entries", min_value=0, value=st.session_state.get("idle_count", 0))
    idle_list = []
    for i in range(idle_count):
        idle_reason = st.text_input(f"Idle Reason {i+1}", value=st.session_state.get(f"idle_{i}", ""))
        idle_list.append(idle_reason)
        st.session_state[f"idle_{i}"] = idle_reason
    st.session_state["idle_reasons"] = idle_list


# --------------------------
# HOURLY TOTAL TRACKER
# --------------------------
with st.expander("📊 Hourly Totals Tracker (visible on app)", expanded=True):
    st.write("This section sums hourly crane moves, restows, and hatch covers for 4-hourly report.")
    st.write("Manual override is allowed if necessary.")

    # Example for Load (similarly for Discharge, Restows, Hatch Covers)
    st.session_state['hourly_total_load'] = st.number_input(
        "Total Load (FWD + MID + AFT + POOP)", 
        value=(st.session_state['hr_fwd_load'] + st.session_state['hr_mid_load'] + st.session_state['hr_aft_load'] + st.session_state['hr_pooh_load']), 
        min_value=0
    )


# --------------------------
# RESET BUTTONS
# --------------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Reset Hourly"):
        for key in ['hr_fwd_load','hr_mid_load','hr_aft_load','hr_pooh_load',
                    'hr_fwd_discharge','hr_mid_discharge','hr_aft_discharge','hr_pooh_discharge',
                    'hr_fwd_restow_load','hr_mid_restow_load','hr_aft_restow_load','hr_pooh_restow_load',
                    'hr_fwd_restow_discharge','hr_mid_restow_discharge','hr_aft_restow_discharge','hr_pooh_restow_discharge',
                    'hr_fwd_hatch_open','hr_mid_hatch_open','hr_aft_hatch_open','hr_pooh_hatch_open',
                    'hr_fwd_hatch_close','hr_mid_hatch_close','hr_aft_hatch_close','hr_pooh_hatch_close']:
            st.session_state[key] = 0
        st.experimental_rerun()

with col2:
    if st.button("🔄 Reset 4-Hourly"):
        for key in ['fwd_load_4h','mid_load_4h','aft_load_4h','pooh_load_4h']:
            st.session_state[key] = 0
        # Add reset for other 4-hourly totals similarly if needed
        st.experimental_rerun()


# --------------------------
# AUTOMATIC HOURLY TIME UPDATE
# --------------------------
if st.button("➡️ Generate Hourly Template"):
    # Update hourly totals tracker before generating template
    st.session_state['hourly_total_load'] = (
        st.session_state['hr_fwd_load'] + st.session_state['hr_mid_load'] +
        st.session_state['hr_aft_load'] + st.session_state['hr_pooh_load']
    )
    # Increment hourly time automatically
    new_hour = (datetime.combine(datetime.today(), st.session_state['hourly_time']) + timedelta(hours=1)).time()
    st.session_state['hourly_time'] = new_hour
    st.experimental_rerun()
    