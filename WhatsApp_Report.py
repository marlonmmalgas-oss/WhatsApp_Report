# Part 1/5

import streamlit as st
from datetime import datetime, timedelta

# -------------------------------
# Session State Initialization
# -------------------------------

if "date_today" not in st.session_state:
    st.session_state.date_today = datetime.now().date()

if "hours_list" not in st.session_state:
    st.session_state.hours_list = [f"{h:02d}:00" for h in range(24)]

# Default hourly selection
default_hour = datetime.now().replace(minute=0, second=0, microsecond=0).strftime("%H:00")
if "hourly_time" not in st.session_state:
    st.session_state.hourly_time = default_hour

# Initialize hourly counters
hourly_fields = [
    "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_pooped_load",
    "hr_fwd_discharge", "hr_mid_discharge", "hr_aft_discharge", "hr_pooped_discharge",
    "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_pooped_restow_load",
    "hr_fwd_restow_discharge", "hr_mid_restow_discharge", "hr_aft_restow_discharge", "hr_pooped_restow_discharge",
    "hr_fwd_hatch_open", "hr_mid_hatch_open", "hr_aft_hatch_open",
    "hr_fwd_hatch_close", "hr_mid_hatch_close", "hr_aft_hatch_close"
]

for field in hourly_fields:
    if field not in st.session_state:
        st.session_state[field] = 0

# Initialize 4-hourly counters (cumulative)
four_hourly_fields = [
    "4hr_fwd_load", "4hr_mid_load", "4hr_aft_load", "4hr_pooped_load",
    "4hr_fwd_discharge", "4hr_mid_discharge", "4hr_aft_discharge", "4hr_pooped_discharge",
    "4hr_fwd_restow_load", "4hr_mid_restow_load", "4hr_aft_restow_load", "4hr_pooped_restow_load",
    "4hr_fwd_restow_discharge", "4hr_mid_restow_discharge", "4hr_aft_restow_discharge", "4hr_pooped_restow_discharge",
    "4hr_fwd_hatch_open", "4hr_mid_hatch_open", "4hr_aft_hatch_open",
    "4hr_fwd_hatch_close", "4hr_mid_hatch_close", "4hr_aft_hatch_close"
]

for field in four_hourly_fields:
    if field not in st.session_state:
        st.session_state[field] = 0

# Default planned totals
if "planned_load" not in st.session_state:
    st.session_state.planned_load = 0
if "planned_discharge" not in st.session_state:
    st.session_state.planned_discharge = 0
    # Part 2/5

st.title("Vessel Hourly & 4-Hourly Moves Tracker ⛴️")

# -------------------------------
# Date Picker
# -------------------------------
st.subheader("📅 Select Date")
st.session_state.date_today = st.date_input("Date", value=st.session_state.date_today)

# -------------------------------
# Hourly Time Selector
# -------------------------------
st.subheader("⏱ Hourly Time")
hourly_time_index = st.session_state.hours_list.index(st.session_state.hourly_time)
st.session_state.hourly_time = st.selectbox(
    "Select Hourly Time",
    options=st.session_state.hours_list,
    index=hourly_time_index
)

# -------------------------------
# Hourly Crane Moves Input
# -------------------------------
st.subheader("🛠️ Crane Moves (Hourly)")

with st.expander("Load / Discharge"):
    st.session_state.hr_fwd_load = st.number_input("FWD Load (hour)", min_value=0, value=st.session_state.hr_fwd_load, key="hr_fwd_load")
    st.session_state.hr_mid_load = st.number_input("MID Load (hour)", min_value=0, value=st.session_state.hr_mid_load, key="hr_mid_load")
    st.session_state.hr_aft_load = st.number_input("AFT Load (hour)", min_value=0, value=st.session_state.hr_aft_load, key="hr_aft_load")
    st.session_state.hr_pooped_load = st.number_input("POOPED Load (hour)", min_value=0, value=st.session_state.hr_pooped_load, key="hr_pooped_load")

    st.session_state.hr_fwd_discharge = st.number_input("FWD Discharge (hour)", min_value=0, value=st.session_state.hr_fwd_discharge, key="hr_fwd_discharge")
    st.session_state.hr_mid_discharge = st.number_input("MID Discharge (hour)", min_value=0, value=st.session_state.hr_mid_discharge, key="hr_mid_discharge")
    st.session_state.hr_aft_discharge = st.number_input("AFT Discharge (hour)", min_value=0, value=st.session_state.hr_aft_discharge, key="hr_aft_discharge")
    st.session_state.hr_pooped_discharge = st.number_input("POOPED Discharge (hour)", min_value=0, value=st.session_state.hr_pooped_discharge, key="hr_pooped_discharge")

with st.expander("Restow Load / Discharge"):
    st.session_state.hr_fwd_restow_load = st.number_input("FWD Restow Load (hour)", min_value=0, value=st.session_state.hr_fwd_restow_load, key="hr_fwd_restow_load")
    st.session_state.hr_mid_restow_load = st.number_input("MID Restow Load (hour)", min_value=0, value=st.session_state.hr_mid_restow_load, key="hr_mid_restow_load")
    st.session_state.hr_aft_restow_load = st.number_input("AFT Restow Load (hour)", min_value=0, value=st.session_state.hr_aft_restow_load, key="hr_aft_restow_load")
    st.session_state.hr_pooped_restow_load = st.number_input("POOPED Restow Load (hour)", min_value=0, value=st.session_state.hr_pooped_restow_load, key="hr_pooped_restow_load")

    st.session_state.hr_fwd_restow_discharge = st.number_input("FWD Restow Discharge (hour)", min_value=0, value=st.session_state.hr_fwd_restow_discharge, key="hr_fwd_restow_discharge")
    st.session_state.hr_mid_restow_discharge = st.number_input("MID Restow Discharge (hour)", min_value=0, value=st.session_state.hr_mid_restow_discharge, key="hr_mid_restow_discharge")
    st.session_state.hr_aft_restow_discharge = st.number_input("AFT Restow Discharge (hour)", min_value=0, value=st.session_state.hr_aft_restow_discharge, key="hr_aft_restow_discharge")
    st.session_state.hr_pooped_restow_discharge = st.number_input("POOPED Restow Discharge (hour)", min_value=0, value=st.session_state.hr_pooped_restow_discharge, key="hr_pooped_restow_discharge")

with st.expander("Hatch Covers Open / Close"):
    st.session_state.hr_fwd_hatch_open = st.number_input("FWD Hatch Open (hour)", min_value=0, value=st.session_state.hr_fwd_hatch_open, key="hr_fwd_hatch_open")
    st.session_state.hr_mid_hatch_open = st.number_input("MID Hatch Open (hour)", min_value=0, value=st.session_state.hr_mid_hatch_open, key="hr_mid_hatch_open")
    st.session_state.hr_aft_hatch_open = st.number_input("AFT Hatch Open (hour)", min_value=0, value=st.session_state.hr_aft_hatch_open, key="hr_aft_hatch_open")

    st.session_state.hr_fwd_hatch_close = st.number_input("FWD Hatch Close (hour)", min_value=0, value=st.session_state.hr_fwd_hatch_close, key="hr_fwd_hatch_close")
    st.session_state.hr_mid_hatch_close = st.number_input("MID Hatch Close (hour)", min_value=0, value=st.session_state.hr_mid_hatch_close, key="hr_mid_hatch_close")
    st.session_state.hr_aft_hatch_close = st.number_input("AFT Hatch Close (hour)", min_value=0, value=st.session_state.hr_aft_hatch_close, key="hr_aft_hatch_close")

# -------------------------------
# Idle / Delays
# -------------------------------
st.subheader("⏸️ Idle / Delays")
idle_count = st.number_input("Number of Idle Entries", min_value=0, value=0)
idle_entries = []
for i in range(idle_count):
    idle_entries.append(st.text_input(f"Idle Entry {i+1}", key=f"idle_{i}"))

# -------------------------------
# Reset Hourly Button
# -------------------------------
if st.button("🔄 Reset Hourly"):
    for field in hourly_fields:
        st.session_state[field] = 0
    st.experimental_rerun()
    # Part 3/5

st.subheader("🕓 4-Hourly Cumulative Tracker")

# Calculate 4-hourly totals automatically
def calculate_4h_total(field_list):
    return sum([st.session_state[field] for field in field_list])

with st.expander("Crane Moves Load / Discharge"):
    st.session_state.total_4h_fwd_load = st.number_input(
        "FWD Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_load"]), 
        key="total_4h_fwd_load"
    )
    st.session_state.total_4h_mid_load = st.number_input(
        "MID Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_load"]), 
        key="total_4h_mid_load"
    )
    st.session_state.total_4h_aft_load = st.number_input(
        "AFT Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_load"]), 
        key="total_4h_aft_load"
    )
    st.session_state.total_4h_pooped_load = st.number_input(
        "POOPED Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_pooped_load"]), 
        key="total_4h_pooped_load"
    )

    st.session_state.total_4h_fwd_discharge = st.number_input(
        "FWD Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_discharge"]), 
        key="total_4h_fwd_discharge"
    )
    st.session_state.total_4h_mid_discharge = st.number_input(
        "MID Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_discharge"]), 
        key="total_4h_mid_discharge"
    )
    st.session_state.total_4h_aft_discharge = st.number_input(
        "AFT Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_discharge"]), 
        key="total_4h_aft_discharge"
    )
    st.session_state.total_4h_pooped_discharge = st.number_input(
        "POOPED Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_pooped_discharge"]), 
        key="total_4h_pooped_discharge"
    )

with st.expander("Restow Load / Discharge"):
    st.session_state.total_4h_fwd_restow_load = st.number_input(
        "FWD Restow Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_restow_load"]), 
        key="total_4h_fwd_restow_load"
    )
    st.session_state.total_4h_mid_restow_load = st.number_input(
        "MID Restow Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_restow_load"]), 
        key="total_4h_mid_restow_load"
    )
    st.session_state.total_4h_aft_restow_load = st.number_input(
        "AFT Restow Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_restow_load"]), 
        key="total_4h_aft_restow_load"
    )
    st.session_state.total_4h_pooped_restow_load = st.number_input(
        "POOPED Restow Load (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_pooped_restow_load"]), 
        key="total_4h_pooped_restow_load"
    )

    st.session_state.total_4h_fwd_restow_discharge = st.number_input(
        "FWD Restow Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_restow_discharge"]), 
        key="total_4h_fwd_restow_discharge"
    )
    st.session_state.total_4h_mid_restow_discharge = st.number_input(
        "MID Restow Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_restow_discharge"]), 
        key="total_4h_mid_restow_discharge"
    )
    st.session_state.total_4h_aft_restow_discharge = st.number_input(
        "AFT Restow Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_restow_discharge"]), 
        key="total_4h_aft_restow_discharge"
    )
    st.session_state.total_4h_pooped_restow_discharge = st.number_input(
        "POOPED Restow Discharge (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_pooped_restow_discharge"]), 
        key="total_4h_pooped_restow_discharge"
    )

with st.expander("Hatch Covers Open / Close"):
    st.session_state.total_4h_fwd_hatch_open = st.number_input(
        "FWD Hatch Open (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_hatch_open"]), 
        key="total_4h_fwd_hatch_open"
    )
    st.session_state.total_4h_mid_hatch_open = st.number_input(
        "MID Hatch Open (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_hatch_open"]), 
        key="total_4h_mid_hatch_open"
    )
    st.session_state.total_4h_aft_hatch_open = st.number_input(
        "AFT Hatch Open (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_hatch_open"]), 
        key="total_4h_aft_hatch_open"
    )

    st.session_state.total_4h_fwd_hatch_close = st.number_input(
        "FWD Hatch Close (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_fwd_hatch_close"]), 
        key="total_4h_fwd_hatch_close"
    )
    st.session_state.total_4h_mid_hatch_close = st.number_input(
        "MID Hatch Close (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_mid_hatch_close"]), 
        key="total_4h_mid_hatch_close"
    )
    st.session_state.total_4h_aft_hatch_close = st.number_input(
        "AFT Hatch Close (4h total)", 
        min_value=0, 
        value=calculate_4h_total(["hr_aft_hatch_close"]), 
        key="total_4h_aft_hatch_close"
    )

# -------------------------------
# Reset 4-Hourly Button
# -------------------------------
if st.button("🔄 Reset 4-Hourly"):
    for field in four_hourly_fields:
        st.session_state[field] = 0
    st.experimental_rerun()
    # Part 4/5

st.subheader("📲 WhatsApp Template")

# Automatic date
today_date = st.date_input("Select Date", value=datetime.date.today())

# Hourly time
st.session_state.hourly_time_end = (datetime.datetime.strptime(st.session_state.hourly_time, "%H:%M") + datetime.timedelta(hours=1)).strftime("%H:%M")
st.session_state.hourly_time_end_4h = (datetime.datetime.strptime(st.session_state.hourly_time, "%H:%M") + datetime.timedelta(hours=4)).strftime("%H:%M")

# WhatsApp number or group link
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code) or Group Link", "")

# Hourly Template
hourly_template = f"""
*🛳 Vessel: {st.session_state.vessel_name}*
*📅 Date: {today_date}*
*⏱ Hourly Period: {st.session_state.hourly_time} - {st.session_state.hourly_time_end}*

```Load / Discharge
FWD Load: {st.session_state.hr_fwd_load}
MID Load: {st.session_state.hr_mid_load}
AFT Load: {st.session_state.hr_aft_load}
POOPED Load: {st.session_state.hr_pooped_load}

FWD Discharge: {st.session_state.hr_fwd_discharge}
MID Discharge: {st.session_state.hr_mid_discharge}
AFT Discharge: {st.session_state.hr_aft_discharge}
POOPED Discharge: {st.session_state.hr_pooped_discharge}```

```Restow Load / Discharge
FWD Restow Load: {st.session_state.hr_fwd_restow_load}
MID Restow Load: {st.session_state.hr_mid_restow_load}
AFT Restow Load: {st.session_state.hr_aft_restow_load}
POOPED Restow Load: {st.session_state.hr_pooped_restow_load}

FWD Restow Discharge: {st.session_state.hr_fwd_restow_discharge}
MID Restow Discharge: {st.session_state.hr_mid_restow_discharge}
AFT Restow Discharge: {st.session_state.hr_aft_restow_discharge}
POOPED Restow Discharge: {st.session_state.hr_pooped_restow_discharge}```

```Hatch Covers Open / Close
FWD Hatch Open: {st.session_state.hr_fwd_hatch_open}
MID Hatch Open: {st.session_state.hr_mid_hatch_open}
AFT Hatch Open: {st.session_state.hr_aft_hatch_open}

FWD Hatch Close: {st.session_state.hr_fwd_hatch_close}
MID Hatch Close: {st.session_state.hr_mid_hatch_close}
AFT Hatch Close: {st.session_state.hr_aft_hatch_close}```
"""

# 4-Hourly Template
four_hour_template = f"""
*🛳 Vessel: {st.session_state.vessel_name}*
*📅 Date: {today_date}*
*🕓 Period: {st.session_state.hourly_time} - {st.session_state.hourly_time_end_4h}*

```Load / Discharge
FWD Load: {st.session_state.total_4h_fwd_load}
MID Load: {st.session_state.total_4h_mid_load}
AFT Load: {st.session_state.total_4h_aft_load}
POOPED Load: {st.session_state.total_4h_pooped_load}

FWD Discharge: {st.session_state.total_4h_fwd_discharge}
MID Discharge: {st.session_state.total_4h_mid_discharge}
AFT Discharge: {st.session_state.total_4h_aft_discharge}
POOPED Discharge: {st.session_state.total_4h_pooped_discharge}```

```Restow Load / Discharge
FWD Restow Load: {st.session_state.total_4h_fwd_restow_load}
MID Restow Load: {st.session_state.total_4h_mid_restow_load}
AFT Restow Load: {st.session_state.total_4h_aft_restow_load}
POOPED Restow Load: {st.session_state.total_4h_pooped_restow_load}

FWD Restow Discharge: {st.session_state.total_4h_fwd_restow_discharge}
MID Restow Discharge: {st.session_state.total_4h_mid_restow_discharge}
AFT Restow Discharge: {st.session_state.total_4h_aft_restow_discharge}
POOPED Restow Discharge: {st.session_state.total_4h_pooped_restow_discharge}```

```Hatch Covers Open / Close
FWD Hatch Open: {st.session_state.total_4h_fwd_hatch_open}
MID Hatch Open: {st.session_state.total_4h_mid_hatch_open}
AFT Hatch Open: {st.session_state.total_4h_aft_hatch_open}

FWD Hatch Close: {st.session_state.total_4h_fwd_hatch_close}
MID Hatch Close: {st.session_state.total_4h_mid_hatch_close}
AFT Hatch Close: {st.session_state.total_4h_aft_hatch_close}```
"""

# Display templates
st.text_area("Hourly Template", hourly_template, height=400)
st.text_area("4-Hourly Template", four_hour_template, height=400)

# Optional: Send to WhatsApp (integration can be done via API)
if st.button("📤 Send Hourly Report to WhatsApp"):
    st.success(f"Hourly report ready to send to {whatsapp_number}")

if st.button("📤 Send 4-Hourly Report to WhatsApp"):
    st.success(f"4-Hourly report ready to send to {whatsapp_number}")
    # Part 5/5

st.subheader("⏸ Idle / Delays")

# Number of idle entries
num_idle = st.number_input("Number of Idle Entries", min_value=0, value=st.session_state.get("num_idle", 0))
st.session_state.num_idle = num_idle

# Collapsible Idle Entries
with st.expander("📝 Enter Idle Entries"):
    idle_entries = []
    for i in range(num_idle):
        entry = st.text_input(f"Idle Entry {i+1}", st.session_state.get(f"idle_{i}", ""))
        st.session_state[f"idle_{i}"] = entry
        idle_entries.append(entry)

# Reset Buttons
st.subheader("🔄 Reset Counters")

if st.button("Reset Hourly Counters"):
    # Reset all hourly counters
    hourly_keys = [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_pooped_load",
        "hr_fwd_discharge","hr_mid_discharge","hr_aft_discharge","hr_pooped_discharge",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_pooped_restow_load",
        "hr_fwd_restow_discharge","hr_mid_restow_discharge","hr_aft_restow_discharge","hr_pooped_restow_discharge",
        "hr_fwd_hatch_open","hr_mid_hatch_open","hr_aft_hatch_open",
        "hr_fwd_hatch_close","hr_mid_hatch_close","hr_aft_hatch_close"
    ]
    for key in hourly_keys:
        st.session_state[key] = 0
    st.success("✅ Hourly counters reset.")

if st.button("Reset 4-Hourly Counters"):
    # Reset all 4-hour counters
    four_hour_keys = [
        "total_4h_fwd_load","total_4h_mid_load","total_4h_aft_load","total_4h_pooped_load",
        "total_4h_fwd_discharge","total_4h_mid_discharge","total_4h_aft_discharge","total_4h_pooped_discharge",
        "total_4h_fwd_restow_load","total_4h_mid_restow_load","total_4h_aft_restow_load","total_4h_pooped_restow_load",
        "total_4h_fwd_restow_discharge","total_4h_mid_restow_discharge","total_4h_aft_restow_discharge","total_4h_pooped_restow_discharge",
        "total_4h_fwd_hatch_open","total_4h_mid_hatch_open","total_4h_aft_hatch_open",
        "total_4h_fwd_hatch_close","total_4h_mid_hatch_close","total_4h_aft_hatch_close"
    ]
    for key in four_hour_keys:
        st.session_state[key] = 0
    st.success("✅ 4-Hourly counters reset.")

# Display Hourly Totals Tracker (collapsible)
with st.expander("📊 4-Hour Cumulative Tracker"):
    st.write("Totals calculated automatically from hourly inputs. You can adjust manually if needed.")
    cumulative_keys = [
        "total_4h_fwd_load","total_4h_mid_load","total_4h_aft_load","total_4h_pooped_load",
        "total_4h_fwd_discharge","total_4h_mid_discharge","total_4h_aft_discharge","total_4h_pooped_discharge",
        "total_4h_fwd_restow_load","total_4h_mid_restow_load","total_4h_aft_restow_load","total_4h_pooped_restow_load",
        "total_4h_fwd_restow_discharge","total_4h_mid_restow_discharge","total_4h_aft_restow_discharge","total_4h_pooped_restow_discharge",
        "total_4h_fwd_hatch_open","total_4h_mid_hatch_open","total_4h_aft_hatch_open",
        "total_4h_fwd_hatch_close","total_4h_mid_hatch_close","total_4h_aft_hatch_close"
    ]
    for key in cumulative_keys:
        st.session_state[key] = st.number_input(f"{key}", value=st.session_state.get(key, 0))

# Ensure the hourly time updates automatically after sending hourly report
if st.session_state.get("hourly_time", None):
    current_hour = datetime.datetime.strptime(st.session_state.hourly_time, "%H:%M")
    next_hour = current_hour + datetime.timedelta(hours=1)
    st.session_state.hourly_time = next_hour.strftime("%H:%M")
    