# Part 1 of 5: Imports, cumulative setup, vessel info, plan & opening balance
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Load or initialize cumulative data ---
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
        "last_hour": "06h00 - 07h00",
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

# --- Timezone and date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

# --- App Title ---
st.title("⚓ Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("📋 Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Plan & Opening Balances (Collapsible) ---
with st.expander("📝 Plan Totals & Opening Balance (Internal Only)"):
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
        # Part 2 of 5: Hourly Time Dropdown, Hourly Moves Inputs, Collapsibles, Idle Entries, Tracker

# --- Hourly Time Dropdown (full 24h) ---
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

st.header(f"🛠 Hourly Moves Input ({hourly_time})")

# --- Hourly Crane Moves ---
with st.expander("🏗 Crane Moves"):
    with st.expander("Load"):
        fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="fwd_load")
        mid_load = st.number_input("MID Load", min_value=0, value=0, key="mid_load")
        aft_load = st.number_input("AFT Load", min_value=0, value=0, key="aft_load")
        poop_load = st.number_input("POOP Load", min_value=0, value=0, key="poop_load")
    with st.expander("Discharge"):
        fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="fwd_disch")
        mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="mid_disch")
        aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="aft_disch")
        poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="poop_disch")

# --- Hourly Restows ---
with st.expander("🔄 Restows"):
    with st.expander("Load"):
        fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="fwd_restow_load")
        mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="mid_restow_load")
        aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="aft_restow_load")
        poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="poop_restow_load")
    with st.expander("Discharge"):
        fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0, key="fwd_restow_disch")
        mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0, key="mid_restow_disch")
        aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0, key="aft_restow_disch")
        poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0, key="poop_restow_disch")

# --- Hourly Hatch Moves ---
with st.expander("🛳 Hatch Moves"):
    with st.expander("Open"):
        hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="hatch_fwd_open")
        hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="hatch_mid_open")
        hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="hatch_aft_open")
    with st.expander("Close"):
        hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="hatch_fwd_close")
        hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="hatch_mid_close")
        hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="hatch_aft_close")

# --- Idle / Delays Section (Collapsible, multiple entries) ---
st.header("⏳ Idle / Delays")
num_idles = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=1)
idle_entries = []

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
    "Spreader difficulties"
]

with st.expander("📝 Idle Entries"):
    for i in range(num_idles):
        st.subheader(f"Idle Entry {i+1}")
        crane_name = st.text_input(f"Crane Name {i+1}", "", key=f"idle_crane_{i}")
        start_time = st.text_input(f"Start Time {i+1}", "", key=f"idle_start_{i}")
        end_time = st.text_input(f"End Time {i+1}", "", key=f"idle_end_{i}")
        selected_delay = st.selectbox(f"Select Delay {i+1}", options=idle_options, key=f"idle_select_{i}")
        custom_delay = st.text_input(f"Custom Delay {i+1} (optional)", "", key=f"idle_custom_{i}")
        idle_entries.append({
            "crane": crane_name,
            "start": start_time,
            "end": end_time,
            "delay": custom_delay if custom_delay else selected_delay
        })

# --- Hourly Tracker Counters ---
st.header("📊 Hourly Tracker Totals (visible on app)")
tracker_table = {
    "FWD": f"{fwd_load} / {fwd_disch} | {fwd_restow_load} / {fwd_restow_disch}",
    "MID": f"{mid_load} / {mid_disch} | {mid_restow_load} / {mid_restow_disch}",
    "AFT": f"{aft_load} / {aft_disch} | {aft_restow_load} / {aft_restow_disch}",
    "POOP": f"{poop_load} / {poop_disch} | {poop_restow_load} / {poop_restow_disch}"
}
st.table(tracker_table)
# Part 3 of 5: Generate & Send Hourly WhatsApp Template, Update Cumulative, Auto-Increment Hourly Time

# --- WhatsApp Section ---
st.header("📩 Send Hourly Report to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_number")
whatsapp_group_link = st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_group_link")

# --- Generate & Send Hourly Template ---
if st.button("Generate & Send Hourly Template"):
    # Update cumulative totals
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save persistent fields
    cumulative.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date,
        "planned_load": planned_load,
        "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load,
        "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load,
        "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load,
        "opening_restow_disch": opening_restow_disch
    })

    # Save cumulative to file
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # Calculate remaining totals
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch

    # Create monospace WhatsApp template
    hourly_template = f"""\
{vessel_name}
Berthed {berthed_date}

Hour: {hourly_time}
_________________________
*HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {fwd_load:>5}     {fwd_disch:>5}
MID       {mid_load:>5}     {mid_disch:>5}
AFT       {aft_load:>5}     {aft_disch:>5}
POOP      {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {fwd_restow_load:>5}     {fwd_restow_disch:>5}
MID       {mid_restow_load:>5}     {mid_restow_disch:>5}
AFT       {aft_restow_load:>5}     {aft_restow_disch:>5}
POOP      {poop_restow_load:>5}     {poop_restow_disch:>5}
_________________________
*CUMULATIVE*
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID       {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT       {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(idle_entries):
        hourly_template += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"

    st.code(hourly_template, language="text")

    # Send to WhatsApp
    if whatsapp_number:
        wa_template = f"```{hourly_template}```"
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif whatsapp_group_link:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link})", unsafe_allow_html=True)

    # Auto-increment hourly time
    current_index = hours_list.index(hourly_time)
    next_index = (current_index + 1) % len(hours_list)
    cumulative["last_hour"] = hours_list[next_index]

    # Save next hour
    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)
        # Part 4 of 5: 4-Hourly Report, Cumulative Sync, Count Tracker, Reset Button

st.header("⏱ 4-Hourly Report")

# 4-Hour Block Selection
four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
four_hour_selected = st.selectbox("Select 4-Hour Block", options=four_hour_blocks, index=0, key="4h_block")

# --- Visible Tracker for 4-Hourly Counts ---
if "four_hour_tracker" not in st.session_state:
    st.session_state.four_hour_tracker = {
        "load": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "disch": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "restow_load": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "restow_disch": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
        "hatch_open":{"FWD":0,"MID":0,"AFT":0},
        "hatch_close":{"FWD":0,"MID":0,"AFT":0}
    }

st.subheader("📊 4-Hourly Counts Tracker")
with st.expander("View & Edit 4-Hourly Counts"):
    for section, positions in st.session_state.four_hour_tracker.items():
        st.markdown(f"**{section.replace('_',' ').title()}**")
        for pos, val in positions.items():
            positions[pos] = st.number_input(f"{section} {pos}", min_value=0, value=val, key=f"4h_{section}_{pos}")

# --- Collapsible Input for Manual 4-Hourly Updates ---
with st.expander("Edit 4-Hourly Moves (Manual Override)"):
    st.markdown("Adjust 4-hourly totals manually if needed.")

# --- Calculate Cumulative for 4-Hourly WhatsApp Template ---
remain_4h_load = sum(st.session_state.four_hour_tracker["load"].values())
remain_4h_disch = sum(st.session_state.four_hour_tracker["disch"].values())
remain_4h_restow_load = sum(st.session_state.four_hour_tracker["restow_load"].values())
remain_4h_restow_disch = sum(st.session_state.four_hour_tracker["restow_disch"].values())

# --- 4-Hourly WhatsApp Template ---
four_hour_template = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_selected}
_________________________
*HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {st.session_state.four_hour_tracker['load']['FWD']:>5}     {st.session_state.four_hour_tracker['disch']['FWD']:>5}
MID       {st.session_state.four_hour_tracker['load']['MID']:>5}     {st.session_state.four_hour_tracker['disch']['MID']:>5}
AFT       {st.session_state.four_hour_tracker['load']['AFT']:>5}     {st.session_state.four_hour_tracker['disch']['AFT']:>5}
POOP      {st.session_state.four_hour_tracker['load']['POOP']:>5}     {st.session_state.four_hour_tracker['disch']['POOP']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {st.session_state.four_hour_tracker['restow_load']['FWD']:>5}     {st.session_state.four_hour_tracker['restow_disch']['FWD']:>5}
MID       {st.session_state.four_hour_tracker['restow_load']['MID']:>5}     {st.session_state.four_hour_tracker['restow_disch']['MID']:>5}
AFT       {st.session_state.four_hour_tracker['restow_load']['AFT']:>5}     {st.session_state.four_hour_tracker['restow_disch']['AFT']:>5}
POOP      {st.session_state.four_hour_tracker['restow_load']['POOP']:>5}     {st.session_state.four_hour_tracker['restow_disch']['POOP']:>5}
_________________________
*CUMULATIVE* (sync with hourly)
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {remain_4h_load:>5}      {remain_4h_disch:>5}
Remain     {planned_load - remain_4h_load:>5}      {planned_disch - remain_4h_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {remain_4h_restow_load:>5}      {remain_4h_restow_disch:>5}
Remain     {planned_restow_load - remain_4h_restow_load:>5}      {planned_restow_disch - remain_4h_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state.four_hour_tracker['hatch_open']['FWD']:>5}      {st.session_state.four_hour_tracker['hatch_close']['FWD']:>5}
MID       {st.session_state.four_hour_tracker['hatch_open']['MID']:>5}      {st.session_state.four_hour_tracker['hatch_close']['MID']:>5}
AFT       {st.session_state.four_hour_tracker['hatch_open']['AFT']:>5}      {st.session_state.four_hour_tracker['hatch_close']['AFT']:>5}
_________________________
"""

st.code(four_hour_template, language="text")

# --- Reset 4-Hourly Tracker Button ---
if st.button("🔄 Reset 4-Hourly Tracker"):
    for section in st.session_state.four_hour_tracker:
        for pos in st.session_state.four_hour_tracker[section]:
            st.session_state.four_hour_tracker[section][pos] = 0
    st.experimental_rerun()
    # Part 5 of 5: Sending 4-Hourly WhatsApp, Final Touches

st.header("📤 Send 4-Hourly Report to WhatsApp")

# Input for WhatsApp number or group link (optional)
whatsapp_number_4h = st.text_input(
    "Enter WhatsApp Number for 4H report (with country code, e.g., 27761234567)",
    key="wa_4h_number"
)
whatsapp_group_link_4h = st.text_input(
    "Or enter WhatsApp Group Link for 4H report (optional)",
    key="wa_4h_group"
)

# Button to send the 4-hourly report
if st.button("📱 Send 4-Hourly Template"):
    if whatsapp_number_4h:
        wa_4h_template = f"```{four_hour_template}```"
        wa_link_4h = f"https://wa.me/{whatsapp_number_4h}?text={urllib.parse.quote(wa_4h_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
        st.success("✅ 4-Hourly report template ready to send!")
    elif whatsapp_group_link_4h:
        st.markdown(f"[Open WhatsApp Group]({whatsapp_group_link_4h})", unsafe_allow_html=True)
        st.success("✅ 4-Hourly report template ready to send!")
    else:
        st.warning("⚠️ Enter a WhatsApp number or group link to send the report.")

# --- Optional: Automatically advance hourly time after generating hourly report ---
if "hour_index" not in st.session_state:
    st.session_state.hour_index = hours_list.index(default_hour)

if st.button("⏭ Advance Hourly Time"):
    st.session_state.hour_index = (st.session_state.hour_index + 1) % len(hours_list)
    st.experimental_rerun()

# Display current hourly selection
st.info(f"🕒 Current Hourly Time: {hours_list[st.session_state.hour_index]}")

# --- Reset Button for Hourly Counts ---
if st.button("🔄 Reset Hourly Tracker"):
    # Reset all hourly crane/restow/hatch inputs
    for section in ["fwd_load","mid_load","aft_load","poop_load",
                    "fwd_disch","mid_disch","aft_disch","poop_disch",
                    "fwd_restow_load","mid_restow_load","aft_restow_load","poop_restow_load",
                    "fwd_restow_disch","mid_restow_disch","aft_restow_disch","poop_restow_disch",
                    "hatch_fwd_open","hatch_mid_open","hatch_aft_open",
                    "hatch_fwd_close","hatch_mid_close","hatch_aft_close"]:
        st.session_state[section] = 0
    st.experimental_rerun()

st.markdown("---")
st.info("💡 Tips for Users: \n"
        "- You can manually adjust hourly or 4-hourly counts if needed.\n"
        "- Use the reset buttons to clear hourly or 4-hourly trackers.\n"
        "- The app automatically syncs cumulative totals between hourly and 4-hourly reports.\n"
        "- Advance the hourly time after generating a template to save time.\n"
        "- Click the WhatsApp link to send your report quickly.\n"
        "- Hover over ⚠️ and ✅ icons for status notifications.")

st.success("🚢 Vessel Hourly & 4-Hourly Tracker Ready for Use!")