# report_app.py
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

# ----------------- CONFIG -----------------
SAVE_FILE = "vessel_report.json"
SA_TZ = pytz.timezone("Africa/Johannesburg")

# ----------------- UTILITIES -----------------
def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def hour_label_to_start(label):
    # label format "06h00 - 07h00"
    try:
        return int(label.split("h")[0])
    except Exception:
        return None

def block_label_to_hours(block_label):
    # returns list of start hours in the block (e.g. 6..9 for 06-10)
    s = int(block_label[:2])
    e = int(block_label[8:10])
    hours = []
    if s < e:
        hours = list(range(s, e))
    else:  # wrap-around (e.g. 22 - 02)
        hours = list(range(s, 24)) + list(range(0, e))
    return hours

def pretty_now():
    return datetime.now(SA_TZ).isoformat()

# ----------------- INITIALIZE / LOAD -----------------
data = load_data()
defaults = {
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "first_lift": "18h25",
    "last_lift": "10h31",
    "planned_load": 687,
    "planned_disch": 38,
    "planned_restow_load": 13,
    "planned_restow_disch": 13,
    "opening_load": 0,
    "opening_disch": 0,
    "opening_restow_load": 0,
    "opening_restow_disch": 0,
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "hourly_records": [],     # each: {date, start_hour, hour_label, fwd_load, ... , used_in_4h: bool, ts}
    "four_hour_reports": []   # each saved 4-hour report
}
# apply defaults
for k, v in defaults.items():
    data.setdefault(k, v)

# ----------------- PAGE UI -----------------
st.set_page_config(layout="centered", page_title="Hourly & 4-Hourly Report")
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel info (persistent editable) ---
st.header("Vessel Info (editable)")
colA, colB = st.columns(2)
with colA:
    vessel_name = st.text_input("Vessel Name", value=data["vessel_name"])
    berthed_date = st.text_input("Berthed Date", value=data["berthed_date"])
with colB:
    first_lift = st.text_input("First Lift (time only)", value=data.get("first_lift","18h25"))
    last_lift = st.text_input("Last Lift (time only)", value=data.get("last_lift","10h31"))

# --- Plan totals & opening balance (internal only) ---
st.header("Plan Totals & Opening Balances (internal only)")
c1, c2 = st.columns(2)
with c1:
    planned_load = st.number_input("Planned Load", value=int(data["planned_load"]))
    planned_disch = st.number_input("Planned Discharge", value=int(data["planned_disch"]))
    planned_restow_load = st.number_input("Planned Restow Load", value=int(data["planned_restow_load"]))
    planned_restow_disch = st.number_input("Planned Restow Discharge", value=int(data["planned_restow_disch"]))
with c2:
    opening_load = st.number_input("Opening Load (Deduction)", value=int(data["opening_load"]))
    opening_disch = st.number_input("Opening Discharge (Deduction)", value=int(data["opening_disch"]))
    opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=int(data["opening_restow_load"]))
    opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=int(data["opening_restow_disch"]))

# Save editable persistent fields immediately (so they stay)
data.update({
    "vessel_name": vessel_name,
    "berthed_date": berthed_date,
    "first_lift": first_lift,
    "last_lift": last_lift,
    "planned_load": planned_load,
    "planned_disch": planned_disch,
    "planned_restow_load": planned_restow_load,
    "planned_restow_disch": planned_restow_disch,
    "opening_load": opening_load,
    "opening_disch": opening_disch,
    "opening_restow_load": opening_restow_load,
    "opening_restow_disch": opening_restow_disch
})
save_data(data)

# --- Hourly time dropdown ---
st.header("Hourly Time")
hours = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = data.get("hourly_last_saved") or "06h00 - 07h00"
try:
    hourly_time = st.selectbox("Select hourly time", hours, index=hours.index(default_hour))
except Exception:
    hourly_time = st.selectbox("Select hourly time", hours, index=0)

# --- Hourly input sections (separated and clear) ---
st.header(f"Hourly Inputs — {hourly_time}")
st.markdown("Enter numbers for this hourly slot. Press **Save Hourly Entry** when done (this updates cumulative totals).")

col1, col2, col3, col4 = st.columns(4)
with col1:
    h_fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="h_fwd_load")
    h_fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="h_fwd_disch")
with col2:
    h_mid_load = st.number_input("MID Load", min_value=0, value=0, key="h_mid_load")
    h_mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="h_mid_disch")
with col3:
    h_aft_load = st.number_input("AFT Load", min_value=0, value=0, key="h_aft_load")
    h_aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="h_aft_disch")
with col4:
    h_poop_load = st.number_input("POOP Load", min_value=0, value=0, key="h_poop_load")
    h_poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="h_poop_disch")

# Restow row
st.subheader("Restows (this hour)")
r1, r2, r3, r4 = st.columns(4)
with r1:
    h_fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="h_fwd_restow_load")
    h_fwd_restow_disch = st.number_input("FWD Restow Disch", min_value=0, value=0, key="h_fwd_restow_disch")
with r2:
    h_mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="h_mid_restow_load")
    h_mid_restow_disch = st.number_input("MID Restow Disch", min_value=0, value=0, key="h_mid_restow_disch")
with r3:
    h_aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="h_aft_restow_load")
    h_aft_restow_disch = st.number_input("AFT Restow Disch", min_value=0, value=0, key="h_aft_restow_disch")
with r4:
    h_poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="h_poop_restow_load")
    h_poop_restow_disch = st.number_input("POOP Restow Disch", min_value=0, value=0, key="h_poop_restow_disch")

# Hatch moves
st.subheader("Hatch Moves (this hour)")
hc1, hc2, hc3 = st.columns(3)
with hc1:
    h_hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="h_hatch_fwd_open")
    h_hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="h_hatch_fwd_close")
with hc2:
    h_hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="h_hatch_mid_open")
    h_hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="h_hatch_mid_close")
with hc3:
    h_hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="h_hatch_aft_open")
    h_hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="h_hatch_aft_close")

# --- Save hourly entry button ---
if st.button("Save Hourly Entry"):
    start_hour = hour_label_to_start(hourly_time)
    today = datetime.now(SA_TZ).strftime("%Y-%m-%d")
    rec = {
        "date": today,
        "start_hour": start_hour,
        "hour_label": hourly_time,
        "fwd_load": int(h_fwd_load),
        "mid_load": int(h_mid_load),
        "aft_load": int(h_aft_load),
        "poop_load": int(h_poop_load),
        "fwd_disch": int(h_fwd_disch),
        "mid_disch": int(h_mid_disch),
        "aft_disch": int(h_aft_disch),
        "poop_disch": int(h_poop_disch),
        "fwd_restow_load": int(h_fwd_restow_load),
        "mid_restow_load": int(h_mid_restow_load),
        "aft_restow_load": int(h_aft_restow_load),
        "poop_restow_load": int(h_poop_restow_load),
        "fwd_restow_disch": int(h_fwd_restow_disch),
        "mid_restow_disch": int(h_mid_restow_disch),
        "aft_restow_disch": int(h_aft_restow_disch),
        "poop_restow_disch": int(h_poop_restow_disch),
        "hatch_fwd_open": int(h_hatch_fwd_open),
        "hatch_fwd_close": int(h_hatch_fwd_close),
        "hatch_mid_open": int(h_hatch_mid_open),
        "hatch_mid_close": int(h_hatch_mid_close),
        "hatch_aft_open": int(h_hatch_aft_open),
        "hatch_aft_close": int(h_hatch_aft_close),
        "used_in_4h": False,
        "ts": pretty_now()
    }

    # append
    data.setdefault("hourly_records", []).append(rec)

    # update cumulative totals (these reflect all saved hourly entries)
    data["done_load"] = data.get("done_load", 0) + rec["fwd_load"] + rec["mid_load"] + rec["aft_load"] + rec["poop_load"]
    data["done_disch"] = data.get("done_disch", 0) + rec["fwd_disch"] + rec["mid_disch"] + rec["aft_disch"] + rec["poop_disch"]
    data["done_restow_load"] = data.get("done_restow_load", 0) + rec["fwd_restow_load"] + rec["mid_restow_load"] + rec["aft_restow_load"] + rec["poop_restow_load"]
    data["done_restow_disch"] = data.get("done_restow_disch", 0) + rec["fwd_restow_disch"] + rec["mid_restow_disch"] + rec["aft_restow_disch"] + rec["poop_restow_disch"]
    data["done_hatch_open"] = data.get("done_hatch_open", 0) + rec["hatch_fwd_open"] + rec["hatch_mid_open"] + rec["hatch_aft_open"]
    data["done_hatch_close"] = data.get("done_hatch_close", 0) + rec["hatch_fwd_close"] + rec["hatch_mid_close"] + rec["hatch_aft_close"]

    # remember last saved hour
    data["hourly_last_saved"] = hourly_time

    save_data(data)
    st.success("Hourly entry saved and cumulative updated.")

# ----------------- HOURLY TEMPLATE (preview & send) -----------------
st.header("Hourly Template (preview & send)")

# get latest hourly inputs to display (use the last saved entry if exists, else use values currently typed)
latest = data.get("hourly_records", [])[-1] if data.get("hourly_records") else None
display_values = {
    "hour_label": hourly_time,
    "fwd_load": h_fwd_load, "mid_load": h_mid_load, "aft_load": h_aft_load, "poop_load": h_poop_load,
    "fwd_disch": h_fwd_disch, "mid_disch": h_mid_disch, "aft_disch": h_aft_disch, "poop_disch": h_poop_disch,
    "fwd_restow_load": h_fwd_restow_load, "mid_restow_load": h_mid_restow_load, "aft_restow_load": h_aft_restow_load, "poop_restow_load": h_poop_restow_load,
    "fwd_restow_disch": h_fwd_restow_disch, "mid_restow_disch": h_mid_restow_disch, "aft_restow_disch": h_aft_restow_disch, "poop_restow_disch": h_poop_restow_disch,
    "hatch_fwd_open": h_hatch_fwd_open, "hatch_mid_open": h_hatch_mid_open, "hatch_aft_open": h_hatch_aft_open,
    "hatch_fwd_close": h_hatch_fwd_close, "hatch_mid_close": h_hatch_mid_close, "hatch_aft_close": h_hatch_aft_close
}
# if latest saved entry exists, prefer that (so preview shows saved values)
if latest:
    display_values.update({k: latest.get(k, display_values.get(k)) for k in display_values.keys()})

# remaining calculations based on cumulative in data
remaining_load = data["planned_load"] - data.get("done_load", 0) - data["opening_load"]
remaining_disch = data["planned_disch"] - data.get("done_disch", 0) - data["opening_disch"]
remaining_restow_load = data["planned_restow_load"] - data.get("done_restow_load", 0) - data["opening_restow_load"]
remaining_restow_disch = data["planned_restow_disch"] - data.get("done_restow_disch", 0) - data["opening_restow_disch"]

hourly_template = f"""\
{data['vessel_name']}
Berthed {data['berthed_date']}

First Lift @ {data.get('first_lift','')}
Last Lift @ {data.get('last_lift','')}

{datetime.now(SA_TZ).strftime('%d/%m/%Y')}
{display_values['hour_label']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {display_values['fwd_load']:>5}     {display_values['fwd_disch']:>5}
MID        {display_values['mid_load']:>5}     {display_values['mid_disch']:>5}
AFT        {display_values['aft_load']:>5}     {display_values['aft_disch']:>5}
POOP       {display_values['poop_load']:>5}     {display_values['poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {display_values['fwd_restow_load']:>5}     {display_values['fwd_restow_disch']:>5}
MID        {display_values['mid_restow_load']:>5}     {display_values['mid_restow_disch']:>5}
AFT        {display_values['aft_restow_load']:>5}     {display_values['aft_restow_disch']:>5}
POOP       {display_values['poop_restow_load']:>5}     {display_values['poop_restow_disch']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {display_values['hatch_fwd_open']:>5}      {display_values['hatch_fwd_close']:>5}
MID        {display_values['hatch_mid_open']:>5}      {display_values['hatch_mid_close']:>5}
AFT        {display_values['hatch_aft_open']:>5}      {display_values['hatch_aft_close']:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""

st.code(hourly_template)

# WhatsApp sending for hourly (private or group)
st.subheader("Send Hourly Template to WhatsApp")
wa_send_choice = st.selectbox("Send hourly template to", ["Private Number", "Group Link"], key="wa_hourly_choice")
if wa_send_choice == "Private Number":
    wa_hourly_number = st.text_input("WhatsApp Number (with country code)", key="wa_hourly_num")
else:
    wa_hourly_group = st.text_input("WhatsApp Group Link (chat.whatsapp.com/...)", key="wa_hourly_group")

if st.button("Open WhatsApp (Hourly)"):
    wa_text = urllib.parse.quote(f"```{hourly_template}```")
    if wa_send_choice == "Private Number" and wa_hourly_number:
        wa_link = f"https://wa.me/{wa_hourly_number}?text={wa_text}"
        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)
    elif wa_send_choice == "Group Link" and wa_hourly_group:
        # For group we open the group link — group links don't accept ?text param reliably,
        # so we just show the link for user to paste the template.
        st.markdown(f"[Open WhatsApp Group]({wa_hourly_group})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid number or group link.")

# ----------------- 4-HOURLY SECTION -----------------
st.header("4-Hourly Report (same template style)")

four_hour_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
selected_block = st.selectbox("Select 4-hour block", four_hour_blocks, index=0)

# compute required start hours
required_hours = block_label_to_hours(selected_block)
today_str = datetime.now(SA_TZ).strftime("%Y-%m-%d")

# find for each required hour the latest hourly_record for today that is NOT used_in_4h
found_records = []
missing_hours = []
for rh in required_hours:
    # find last record for this hour & date that is not used_in_4h
    candidates = [rec for rec in data.get("hourly_records", []) if rec["date"] == today_str and rec["start_hour"] == rh and not rec.get("used_in_4h", False)]
    if candidates:
        found_records.append(candidates[-1])  # pick the last one
    else:
        missing_hours.append(rh)

# If any missing, show notice but still allow manual editing
if missing_hours:
    st.warning(f"Not enough hourly saved entries for hours: {', '.join(str(h).zfill(2) for h in missing_hours)}. You can still manually edit the 4-hour totals below.")
else:
    st.success("4-hour sums computed from hourly saved entries (you may edit them below).")

# compute sums from found_records (only those found)
def sum_field_from_found(field):
    return sum(rec.get(field, 0) for rec in found_records)

auto_fwd_load = sum_field_from_found("fwd_load")
auto_mid_load = sum_field_from_found("mid_load")
auto_aft_load = sum_field_from_found("aft_load")
auto_poop_load = sum_field_from_found("poop_load")

auto_fwd_disch = sum_field_from_found("fwd_disch")
auto_mid_disch = sum_field_from_found("mid_disch")
auto_aft_disch = sum_field_from_found("aft_disch")
auto_poop_disch = sum_field_from_found("poop_disch")

auto_fwd_restow_load = sum_field_from_found("fwd_restow_load")
auto_mid_restow_load = sum_field_from_found("mid_restow_load")
auto_aft_restow_load = sum_field_from_found("aft_restow_load")
auto_poop_restow_load = sum_field_from_found("poop_restow_load")

auto_fwd_restow_disch = sum_field_from_found("fwd_restow_disch")
auto_mid_restow_disch = sum_field_from_found("mid_restow_disch")
auto_aft_restow_disch = sum_field_from_found("aft_restow_disch")
auto_poop_restow_disch = sum_field_from_found("poop_restow_disch")

auto_hatch_fwd_open = sum_field_from_found("hatch_fwd_open")
auto_hatch_mid_open = sum_field_from_found("hatch_mid_open")
auto_hatch_aft_open = sum_field_from_found("hatch_aft_open")
auto_hatch_fwd_close = sum_field_from_found("hatch_fwd_close")
auto_hatch_mid_close = sum_field_from_found("hatch_mid_close")
auto_hatch_aft_close = sum_field_from_found("hatch_aft_close")

# --- Editable 4-hour inputs (prefilled with computed sums) ---
st.subheader("4-Hourly Inputs (editable)")
col1, col2 = st.columns(2)
with col1:
    fwd_load_4h = st.number_input("FWD Load (4H)", min_value=0, value=int(auto_fwd_load), key="fwd_load_4h")
    mid_load_4h = st.number_input("MID Load (4H)", min_value=0, value=int(auto_mid_load), key="mid_load_4h")
    aft_load_4h = st.number_input("AFT Load (4H)", min_value=0, value=int(auto_aft_load), key="aft_load_4h")
    poop_load_4h = st.number_input("POOP Load (4H)", min_value=0, value=int(auto_poop_load), key="poop_load_4h")
with col2:
    fwd_disch_4h = st.number_input("FWD Disch (4H)", min_value=0, value=int(auto_fwd_disch), key="fwd_disch_4h")
    mid_disch_4h = st.number_input("MID Disch (4H)", min_value=0, value=int(auto_mid_disch), key="mid_disch_4h")
    aft_disch_4h = st.number_input("AFT Disch (4H)", min_value=0, value=int(auto_aft_disch), key="aft_disch_4h")
    poop_disch_4h = st.number_input("POOP Disch (4H)", min_value=0, value=int(auto_poop_disch), key="poop_disch_4h")

st.subheader("4-Hourly Restows (editable)")
colr1, colr2 = st.columns(2)
with colr1:
    fwd_restow_load_4h = st.number_input("FWD Restow Load (4H)", min_value=0, value=int(auto_fwd_restow_load), key="fwd_restow_load_4h")
    mid_restow_load_4h = st.number_input("MID Restow Load (4H)", min_value=0, value=int(auto_mid_restow_load), key="mid_restow_load_4h")
with colr2:
    aft_restow_load_4h = st.number_input("AFT Restow Load (4H)", min_value=0, value=int(auto_aft_restow_load), key="aft_restow_load_4h")
    poop_restow_load_4h = st.number_input("POOP Restow Load (4H)", min_value=0, value=int(auto_poop_restow_load), key="poop_restow_load_4h")

colr3, colr4 = st.columns(2)
with colr3:
    fwd_restow_disch_4h = st.number_input("FWD Restow Disch (4H)", min_value=0, value=int(auto_fwd_restow_disch), key="fwd_restow_disch_4h")
    mid_restow_disch_4h = st.number_input("MID Restow Disch (4H)", min_value=0, value=int(auto_mid_restow_disch), key="mid_restow_disch_4h")
with colr4:
    aft_restow_disch_4h = st.number_input("AFT Restow Disch (4H)", min_value=0, value=int(auto_aft_restow_disch), key="aft_restow_disch_4h")
    poop_restow_disch_4h = st.number_input("POOP Restow Disch (4H)", min_value=0, value=int(auto_poop_restow_disch), key="poop_restow_disch_4h")
st.subheader("4-Hourly Hatch Moves (editable)")
colh1, colh2, colh3 = st.columns(3)
with colh1:
    hatch_fwd_open_4h = st.number_input("FWD Open (4H)", min_value=0, value=int(auto_hatch_fwd_open), key="hatch_fwd_open_4h")
    hatch_fwd_close_4h = st.number_input("FWD Close (4H)", min_value=0, value=int(auto_hatch_fwd_close), key="hatch_fwd_close_4h")
with colh2:
    hatch_mid_open_4h = st.number_input("MID Open (4H)", min_value=0, value=int(auto_hatch_mid_open), key="hatch_mid_open_4h")
    hatch_mid_close_4h = st.number_input("MID Close (4H)", min_value=0, value=int(auto_hatch_mid_close), key="hatch_mid_close_4h")
with colh3:
    hatch_aft_open_4h = st.number_input("AFT Open (4H)", min_value=0, value=int(auto_hatch_aft_open), key="hatch_aft_open_4h")
    hatch_aft_close_4h = st.number_input("AFT Close (4H)", min_value=0, value=int(auto_hatch_aft_close), key="hatch_aft_close_4h")

# --- 4-hourly template (same formatting as hourly) but with block label and 4h numbers ---
remaining_load_current = data["planned_load"] - data.get("done_load", 0) - data["opening_load"]
remaining_disch_current = data["planned_disch"] - data.get("done_disch", 0) - data["opening_disch"]
remaining_restow_load_current = data["planned_restow_load"] - data.get("done_restow_load", 0) - data["opening_restow_load"]
remaining_restow_disch_current = data["planned_restow_disch"] - data.get("done_restow_disch", 0) - data["opening_restow_disch"]

template_4h = f"""\
{data['vessel_name']}
Berthed {data['berthed_date']}

4-Hour Block: {selected_block}
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
           Load   Disch
FWD        {fwd_restow_load_4h:>5}     {fwd_restow_disch_4h:>5}
MID        {mid_restow_load_4h:>5}     {mid_restow_disch_4h:>5}
AFT        {aft_restow_load_4h:>5}     {aft_restow_disch_4h:>5}
POOP       {poop_restow_load_4h:>5}     {poop_restow_disch_4h:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load_current:>5}      {remaining_disch_current:>5}
_________________________
*Restows*
           Load   Disch
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load_current:>5}      {remaining_restow_disch_current:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_open_4h:>5}      {hatch_fwd_close_4h:>5}
MID        {hatch_mid_open_4h:>5}      {hatch_mid_close_4h:>5}
AFT        {hatch_aft_open_4h:>5}      {hatch_aft_close_4h:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""

st.subheader("4-Hourly Template Preview")
st.code(template_4h)

# --- Submit 4-hourly: save report (does not alter cumulative) but mark used hourly_records ---
if st.button("Submit 4-Hourly Report (save & mark used)"):
    # find the relevant records again (unmarked) and mark them if they were found earlier
    matched_records = []
    for rh in required_hours:
        candidates = [rec for rec in data.get("hourly_records", []) if rec["date"] == today_str and rec["start_hour"] == rh and not rec.get("used_in_4h", False)]
        if candidates:
            matched_records.append(candidates[-1])

    # prepare report entry using edited numbers (the inputs above)
    report = {
        "date": today_str,
        "block": selected_block,
        "ts": pretty_now(),
        "fwd_load": int(fwd_load_4h),
        "mid_load": int(mid_load_4h),
        "aft_load": int(aft_load_4h),
        "poop_load": int(poop_load_4h),
        "fwd_disch": int(fwd_disch_4h),
        "mid_disch": int(mid_disch_4h),
        "aft_disch": int(aft_disch_4h),
        "poop_disch": int(poop_disch_4h),
        "fwd_restow_load": int(fwd_restow_load_4h),
        "mid_restow_load": int(mid_restow_load_4h),
        "aft_restow_load": int(aft_restow_load_4h),
        "poop_restow_load": int(poop_restow_load_4h),
        "fwd_restow_disch": int(fwd_restow_disch_4h),
        "mid_restow_disch": int(mid_restow_disch_4h),
        "aft_restow_disch": int(aft_restow_disch_4h),
        "poop_restow_disch": int(poop_restow_disch_4h),
        "hatch_fwd_open": int(hatch_fwd_open_4h),
        "hatch_mid_open": int(hatch_mid_open_4h),
        "hatch_aft_open": int(hatch_aft_open_4h),
        "hatch_fwd_close": int(hatch_fwd_close_4h),
        "hatch_mid_close": int(hatch_mid_close_4h),
        "hatch_aft_close": int(hatch_aft_close_4h)
    }
    # append to saved 4-hour reports
    data.setdefault("four_hour_reports", []).append(report)

    # mark matched hourly records as used_in_4h so they won't be reused for another 4h unless you reset them
    for rec in matched_records:
        # set flag on the original rec stored in data (we have to find by ts)
        for orig in data.get("hourly_records", []):
            if orig.get("ts") == rec.get("ts"):
                orig["used_in_4h"] = True

    save_data(data)
    st.success("4-hourly report saved. Matched hourly records (if any) were marked as used.")

# --- Reset used_in_4h flags button (in case you need to restart counting) ---
if st.button("Reset 'used in 4h' flags (allow re-using hourly entries)"):
    for rec in data.get("hourly_records", []):
        rec["used_in_4h"] = False
    save_data(data)
    st.success("All hourly entries are now available again for 4-hour blocks.")

# --- Send 4-hourly via WhatsApp ---
st.subheader("Send 4-Hourly Template to WhatsApp")
wa_4h_choice = st.selectbox("Send 4-hourly to", ["Private Number", "Group Link"], key="wa4h_choice")
if wa_4h_choice == "Private Number":
    wa_4h_number = st.text_input("WhatsApp Number (with country code)", key="wa_4h_num")
else:
    wa_4h_group = st.text_input("WhatsApp Group Link", key="wa_4h_group")

if st.button("Open WhatsApp (4-hourly)"):
    wa_text_4h = urllib.parse.quote(f"```{template_4h}```")
    if wa_4h_choice == "Private Number" and wa_4h_number:
        wa_link_4h = f"https://wa.me/{wa_4h_number}?text={wa_text_4h}"
        st.markdown(f"[Open WhatsApp]({wa_link_4h})", unsafe_allow_html=True)
    elif wa_4h_choice == "Group Link" and wa_4h_group:
        st.markdown(f"[Open WhatsApp Group]({wa_4h_group})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid number or group link.")

# ----------------- END -----------------
st.markdown("---")
st.caption("Data is stored locally in vessel_report.json in the app folder. 4-hourly sums by default come from the latest hourly entries for the selected block; you can edit them before saving or sending. Marked hourly entries won't be reused for another 4-hour report unless you reset the flags.")