import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# --- Load or initialize cumulative data ---
if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as f:
            cumulative = json.load(f)
    except json.JSONDecodeError:
        cumulative = {}  # Start fresh if file is corrupt
else:
    cumulative = {}

# --- Default cumulative structure ---
default_cumulative = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": None,
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

# Merge defaults with loaded cumulative
for key, value in default_cumulative.items():
    if key not in cumulative:
        cumulative[key] = value

# --- Current South African Date ---
sa_tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(sa_tz).strftime("%d/%m/%Y")

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info ---
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])

# --- Collapsible Plan Totals & Opening Balance ---
with st.expander("Plan Totals & Opening Balance (Internal Only)", expanded=False):
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
        # --- Hourly Time Dropdown (full 24h) ---
st.header("Hourly Time")
hours_list = []
for h in range(24):
    start_hour = h
    end_hour = (h + 1) % 24
    hours_list.append(f"{str(start_hour).zfill(2)}h00 - {str(end_hour).zfill(2)}h00")

default_hour = cumulative.get("last_hour", "06h00 - 07h00")
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# --- Hourly Moves Groups ---
st.header(f"Hourly Moves Input ({hourly_time})")

with st.expander("Crane Moves (Load / Discharge)"):
    st.subheader("FWD")
    fwd_load = st.number_input("Load", min_value=0, value=0, key="fwd_load")
    fwd_disch = st.number_input("Discharge", min_value=0, value=0, key="fwd_disch")

    st.subheader("MID")
    mid_load = st.number_input("Load", min_value=0, value=0, key="mid_load")
    mid_disch = st.number_input("Discharge", min_value=0, value=0, key="mid_disch")

    st.subheader("AFT")
    aft_load = st.number_input("Load", min_value=0, value=0, key="aft_load")
    aft_disch = st.number_input("Discharge", min_value=0, value=0, key="aft_disch")

    st.subheader("POOP")
    poop_load = st.number_input("Load", min_value=0, value=0, key="poop_load")
    poop_disch = st.number_input("Discharge", min_value=0, value=0, key="poop_disch")

with st.expander("Restows (Load / Discharge)"):
    st.subheader("FWD")
    fwd_restow_load = st.number_input("Load", min_value=0, value=0, key="fwd_restow_load")
    fwd_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="fwd_restow_disch")

    st.subheader("MID")
    mid_restow_load = st.number_input("Load", min_value=0, value=0, key="mid_restow_load")
    mid_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="mid_restow_disch")

    st.subheader("AFT")
    aft_restow_load = st.number_input("Load", min_value=0, value=0, key="aft_restow_load")
    aft_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="aft_restow_disch")

    st.subheader("POOP")
    poop_restow_load = st.number_input("Load", min_value=0, value=0, key="poop_restow_load")
    poop_restow_disch = st.number_input("Discharge", min_value=0, value=0, key="poop_restow_disch")

with st.expander("Hatch Moves (Open / Close)"):
    st.subheader("FWD")
    hatch_fwd_open = st.number_input("Open", min_value=0, value=0, key="hatch_fwd_open")
    hatch_fwd_close = st.number_input("Close", min_value=0, value=0, key="hatch_fwd_close")

    st.subheader("MID")
    hatch_mid_open = st.number_input("Open", min_value=0, value=0, key="hatch_mid_open")
    hatch_mid_close = st.number_input("Close", min_value=0, value=0, key="hatch_mid_close")

    st.subheader("AFT")
    hatch_aft_open = st.number_input("Open", min_value=0, value=0, key="hatch_aft_open")
    hatch_aft_close = st.number_input("Close", min_value=0, value=0, key="hatch_aft_close")

# --- Idle Section ---
idle_options = [
    "Stevedore tea time/shift change", "Awaiting cargo", "Awaiting AGL operations",
    "Awaiting FPT gang", "Awaiting Crane driver", "Awaiting onboard stevedores",
    "Windbound", "Crane break down/ wipers", "Crane break down/ lights",
    "Crane break down/ boom limit", "Crane break down", "Vessel listing",
    "Struggling to load container", "Cell guide struggles", "Spreader difficulties"
]

st.header("Idle / Delay Entries")
with st.expander("Add Idle Delays", expanded=False):
    num_idles = st.number_input("Number of idle entries", min_value=1, max_value=10, value=3)
    idle_entries = []
    for i in range(num_idles):
        st.subheader(f"Idle {i+1}")
        crane = st.text_input(f"Crane Name {i+1}", key=f"idle_crane_{i}")
        start_time = st.text_input(f"Start Time {i+1} (HH:MM)", key=f"idle_start_{i}")
        end_time = st.text_input(f"End Time {i+1} (HH:MM)", key=f"idle_end_{i}")
        delay_select = st.selectbox(f"Select Delay {i+1}", options=idle_options + ["Other"], key=f"idle_type_{i}")
        if delay_select == "Other":
            custom_delay = st.text_input(f"Custom Delay {i+1}", key=f"idle_custom_{i}")
        else:
            custom_delay = ""
        idle_entries.append({
            "crane": crane,
            "start": start_time,
            "end": end_time,
            "type": delay_select,
            "custom": custom_delay
        })

# --- WhatsApp Number Input ---
st.header("Send to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp Number or Group Link (with country code if number)")

# --- Submit Button ---
if st.button("Submit Hourly Moves"):
    # --- Update cumulative totals ---
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    cumulative["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    cumulative["last_hour"] = hourly_time

    # Save persistent editable fields
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

    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

    # --- Calculate remaining totals ---
    remaining_load = planned_load - cumulative["done_load"] - opening_load
    remaining_disch = planned_disch - cumulative["done_disch"] - opening_disch
    remaining_restow_load = planned_restow_load - cumulative["done_restow_load"] - opening_restow_load
    remaining_restow_disch = planned_restow_disch - cumulative["done_restow_disch"] - opening_restow_disch
    # --- WhatsApp Template (Hourly) ---
    template_lines = [
        f"{vessel_name}",
        f"Berthed {berthed_date}",
        f"{today_date}",
        f"{hourly_time}",
        "_________________________",
        "   *HOURLY MOVES*",
        "_________________________",
        "*Crane Moves*",
        "           Load   Discharge",
        f"FWD        {fwd_load:>5}     {fwd_disch:>5}",
        f"MID        {mid_load:>5}     {mid_disch:>5}",
        f"AFT        {aft_load:>5}     {aft_disch:>5}",
        f"POOP       {poop_load:>5}     {poop_disch:>5}",
        "_________________________",
        "*Restows*",
        "           Load   Discharge",
        f"FWD        {fwd_restow_load:>5}     {fwd_restow_disch:>5}",
        f"MID        {mid_restow_load:>5}     {mid_restow_disch:>5}",
        f"AFT        {aft_restow_load:>5}     {aft_restow_disch:>5}",
        f"POOP       {poop_restow_load:>5}     {poop_restow_disch:>5}",
        "_________________________",
        "      *CUMULATIVE*",
        "_________________________",
        "           Load   Disch",
        f"Plan       {planned_load:>5}      {planned_disch:>5}",
        f"Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}",
        f"Remain     {remaining_load:>5}      {remaining_disch:>5}",
        "_________________________",
        "*Restows*",
        "           Load   Disch",
        f"Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}",
        f"Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}",
        f"Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}",
        "_________________________",
        "*Hatch Moves*",
        "           Open   Close",
        f"FWD        {hatch_fwd_open:>5}      {hatch_fwd_close:>5}",
        f"MID        {hatch_mid_open:>5}      {hatch_mid_close:>5}",
        f"AFT        {hatch_aft_open:>5}      {hatch_aft_close:>5}",
        "_________________________",
        "*Idle*"
    ]

    # Add idle entries to template
    for idle in idle_entries:
        delay_text = idle['custom'] if idle['type'] == "Other" else idle['type']
        template_lines.append(f"{idle['crane']} {idle['start']} - {idle['end']} {delay_text}")

    template_text = "\n".join(template_lines)

    # --- Display in monospace ---
    st.code(template_text)

    # --- WhatsApp Link ---
    if whatsapp_number:
        wa_template = f"```{template_text}```"
        if whatsapp_number.startswith("https://") or whatsapp_number.startswith("wa.me"):
            wa_link = whatsapp_number
        else:
            wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_template)}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)

# --- 4-Hourly Template ---
st.header("4-Hourly Report")
four_hour_blocks = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
selected_4hour = st.selectbox("Select 4-Hour Block", options=four_hour_blocks)

with st.expander("4-Hourly Moves", expanded=True):
    # Pre-fill 4-hourly totals from hourly cumulative or last 4-hour
    fwd_4h = st.number_input("FWD Load Total (4H)", min_value=0, value=fwd_load, key="fwd_4h")
    mid_4h = st.number_input("MID Load Total (4H)", min_value=0, value=mid_load, key="mid_4h")
    aft_4h = st.number_input("AFT Load Total (4H)", min_value=0, value=aft_load, key="aft_4h")
    poop_4h = st.number_input("POOP Load Total (4H)", min_value=0, value=poop_load, key="poop_4h")

    # Restow 4H totals
    fwd_restow_4h = st.number_input("FWD Restow Total (4H)", min_value=0, value=fwd_restow_load, key="fwd_restow_4h")
    mid_restow_4h = st.number_input("MID Restow Total (4H)", min_value=0, value=mid_restow_load, key="mid_restow_4h")
    aft_restow_4h = st.number_input("AFT Restow Total (4H)", min_value=0, value=aft_restow_load, key="aft_restow_4h")
    poop_restow_4h = st.number_input("POOP Restow Total (4H)", min_value=0, value=poop_restow_load, key="poop_restow_4h")

    # Hatch covers 4H totals
    hatch_fwd_4h_open = st.number_input("FWD Hatch Open Total (4H)", min_value=0, value=hatch_fwd_open, key="hatch_fwd_4h_open")
    hatch_mid_4h_open = st.number_input("MID Hatch Open Total (4H)", min_value=0, value=hatch_mid_open, key="hatch_mid_4h_open")
    hatch_aft_4h_open = st.number_input("AFT Hatch Open Total (4H)", min_value=0, value=hatch_aft_open, key="hatch_aft_4h_open")

    hatch_fwd_4h_close = st.number_input("FWD Hatch Close Total (4H)", min_value=0, value=hatch_fwd_close, key="hatch_fwd_4h_close")
    hatch_mid_4h_close = st.number_input("MID Hatch Close Total (4H)", min_value=0, value=hatch_mid_close, key="hatch_mid_4h_close")
    hatch_aft_4h_close = st.number_input("AFT Hatch Close Total (4H)", min_value=0, value=hatch_aft_close, key="hatch_aft_4h_close")

# --- WhatsApp Template for 4-Hourly Report ---
template_4hourly = f"""\
{vessel_name}
Berthed {berthed_date}

Date: {today_date}
4-Hour Block: {four_hour_block}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {fwd_load_4h:>5}     {fwd_disch_4h:>5}
MID        {mid_load_4h:>5}     {mid_disch_4h:>5}
AFT        {aft_load_4h:>5}     {aft_disch_4h:>5}
POOP       {poop_load_4h:>5}     {poop_disch_4h:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {fwd_restow_load_4h:>5}     {fwd_restow_disch_4h:>5}
MID        {mid_restow_load_4h:>5}     {mid_restow_disch_4h:>5}
AFT        {aft_restow_load_4h:>5}     {aft_restow_disch_4h:>5}
POOP       {poop_restow_load_4h:>5}     {poop_restow_disch_4h:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load_4h:>5}      {remaining_disch_4h:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load_4h:>5}      {remaining_restow_disch_4h:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_open_4h:>5}      {hatch_fwd_close_4h:>5}
MID        {hatch_mid_open_4h:>5}      {hatch_mid_close_4h:>5}
AFT        {hatch_aft_open_4h:>5}      {hatch_aft_close_4h:>5}
_________________________
*Idle*
{idle_entries_4h}
"""
    ]

    # Include idle entries (reuse hourly idle for now)
    for idle in idle_entries:
        delay_text = idle['custom'] if idle['type'] == "Other" else idle['type']
        four_hour_lines.append(f"{idle['crane']} {idle['start']} - {idle['end']} {delay_text}")

    four_hour_text = "\n".join(four_hour_lines)

    # Display in monospace
    st.code(four_hour_text)

    # WhatsApp link
    if whatsapp_number_4h:
        wa_template_4h = f"```{four_hour_text}```"
        if whatsapp_number_4h.startswith("https://") or whatsapp_number_4h.startswith("wa.me"):
            wa_link_4h = whatsapp_number_4h
        else:
            wa_link_4h = f"https://wa.me/{whatsapp_number_4h}?text={urllib.parse.quote(wa_template_4h)}"
        st.markdown(f"[Open 4-Hourly WhatsApp]({wa_link_4h})", unsafe_allow_html=True)