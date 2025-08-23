# Part 1/5
import streamlit as st
import json
import os
import urllib.parse
import re
from datetime import datetime, timedelta
import pytz

# ---------- files ----------
SAVE_FILE = "vessel_report.json"
SAVE_FILE_4H = "vessel_report_4h.json"

# ---------- helpers ----------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ---------- defaults ----------
default_cumulative = {
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
    "first_lift": "",
    "last_lift": "",
    "planned_load": 687,
    "planned_disch": 38,
    "planned_restow_load": 13,
    "planned_restow_disch": 13,
    "opening_load": 0,
    "opening_disch": 0,
    "opening_restow_load": 0,
    "opening_restow_disch": 0,
    # cumulative done totals (persisted)
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": None
}

default_4h = {
    "fwd_load": 0, "mid_load": 0, "aft_load": 0, "poop_load": 0,
    "fwd_disch": 0, "mid_disch": 0, "aft_disch": 0, "poop_disch": 0,
    "fwd_restow_load": 0, "mid_restow_load": 0, "aft_restow_load": 0, "poop_restow_load": 0,
    "fwd_restow_disch": 0, "mid_restow_disch": 0, "aft_restow_disch": 0, "poop_restow_disch": 0,
    "fwd_hatch_open": 0, "mid_hatch_open": 0, "aft_hatch_open": 0,
    "fwd_hatch_close": 0, "mid_hatch_close": 0, "aft_hatch_close": 0,
    "last_4h_block": None
}

# ---------- load persisted ----------
cumulative = load_json(SAVE_FILE, default_cumulative)
cumulative_4h = load_json(SAVE_FILE_4H, default_4h)

# ---------- timezone & date ----------
sa_tz = pytz.timezone("Africa/Johannesburg")
now_sa = datetime.now(sa_tz)
today_str = now_sa.strftime("%d/%m/%Y")

# ---------- streamlit page ----------
st.set_page_config(page_title="Vessel Moves Tracker", layout="wide")
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# ---------- Vessel info (editable, persistent) ----------
st.header("Vessel Info (editable)")
vessel_name = st.text_input("Vessel Name", value=cumulative.get("vessel_name", ""))
berthed_date = st.text_input("Berthed Date (as in template)", value=cumulative.get("berthed_date", ""))
first_lift = st.text_input("First Lift (time only, e.g. 18h25)", value=cumulative.get("first_lift", ""))
last_lift = st.text_input("Last Lift (time only, e.g. 10h31)", value=cumulative.get("last_lift", ""))

# ---------- plan & opening (collapsible) ----------
with st.expander("Plan Totals & Opening Balance (internal only)"):
    planned_load = st.number_input("Planned Load", value=cumulative.get("planned_load", 0))
    planned_disch = st.number_input("Planned Discharge", value=cumulative.get("planned_disch", 0))
    planned_restow_load = st.number_input("Planned Restow Load", value=cumulative.get("planned_restow_load", 0))
    planned_restow_disch = st.number_input("Planned Restow Discharge", value=cumulative.get("planned_restow_disch", 0))

    opening_load = st.number_input("Opening Load (deduction)", value=cumulative.get("opening_load", 0))
    opening_disch = st.number_input("Opening Discharge (deduction)", value=cumulative.get("opening_disch", 0))
    opening_restow_load = st.number_input("Opening Restow Load (deduction)", value=cumulative.get("opening_restow_load", 0))
    opening_restow_disch = st.number_input("Opening Restow Discharge (deduction)", value=cumulative.get("opening_restow_disch", 0))

# ---------- Safe hourly time selectbox ----------
hours_list = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
raw_last = cumulative.get("last_hour")

# Try exact match first
default_hour = raw_last if isinstance(raw_last, str) and raw_last in hours_list else None

# Heuristic: extract starting hour number if stored differently
if default_hour is None and isinstance(raw_last, str):
    m = re.search(r'(\d{1,2})', raw_last)
    if m:
        h = int(m.group(1)) % 24
        candidate = f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00"
        if candidate in hours_list:
            default_hour = candidate

if default_hour is None:
    default_hour = "06h00 - 07h00"

# keep hourly_time in session_state so we can auto-advance safely
if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = default_hour

hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(st.session_state["hourly_time"]))
# whenever user manually selects, update session_state
st.session_state["hourly_time"] = hourly_time

# ---------- persist vessel/plan basic edits immediately ----------
cumulative["vessel_name"] = vessel_name
cumulative["berthed_date"] = berthed_date
cumulative["first_lift"] = first_lift
cumulative["last_lift"] = last_lift
cumulative["planned_load"] = planned_load
cumulative["planned_disch"] = planned_disch
cumulative["planned_restow_load"] = planned_restow_load
cumulative["planned_restow_disch"] = planned_restow_disch
cumulative["opening_load"] = opening_load
cumulative["opening_disch"] = opening_disch
cumulative["opening_restow_load"] = opening_restow_load
cumulative["opening_restow_disch"] = opening_restow_disch
cumulative["last_hour"] = st.session_state["hourly_time"]

save_json(SAVE_FILE, cumulative)
save_json(SAVE_FILE_4H, cumulative_4h)
# Part 2/5

st.header(f"Hourly Moves Input ({st.session_state['hourly_time']})")

# ensure all hourly keys exist in session_state
hourly_keys = [
    "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
    "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
    "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
    "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
    "hr_hatch_fwd_open", "hr_hatch_mid_open", "hr_hatch_aft_open",
    "hr_hatch_fwd_close", "hr_hatch_mid_close", "hr_hatch_aft_close"
]
for k in hourly_keys:
    if k not in st.session_state:
        st.session_state[k] = 0

# Crane Moves - Load & Discharge grouped visually like template
with st.expander("Crane Moves (Hourly)", expanded=True):
    st.markdown("**Load**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.session_state["hr_fwd_load"] = st.number_input("FWD Load", min_value=0, value=st.session_state["hr_fwd_load"], key="in_hr_fwd_load")
    with c2:
        st.session_state["hr_mid_load"] = st.number_input("MID Load", min_value=0, value=st.session_state["hr_mid_load"], key="in_hr_mid_load")
    with c3:
        st.session_state["hr_aft_load"] = st.number_input("AFT Load", min_value=0, value=st.session_state["hr_aft_load"], key="in_hr_aft_load")
    with c4:
        st.session_state["hr_poop_load"] = st.number_input("POOP Load", min_value=0, value=st.session_state["hr_poop_load"], key="in_hr_poop_load")

    st.markdown("**Discharge**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.session_state["hr_fwd_disch"] = st.number_input("FWD Discharge", min_value=0, value=st.session_state["hr_fwd_disch"], key="in_hr_fwd_disch")
    with c2:
        st.session_state["hr_mid_disch"] = st.number_input("MID Discharge", min_value=0, value=st.session_state["hr_mid_disch"], key="in_hr_mid_disch")
    with c3:
        st.session_state["hr_aft_disch"] = st.number_input("AFT Discharge", min_value=0, value=st.session_state["hr_aft_disch"], key="in_hr_aft_disch")
    with c4:
        st.session_state["hr_poop_disch"] = st.number_input("POOP Discharge", min_value=0, value=st.session_state["hr_poop_disch"], key="in_hr_poop_disch")

# Restows
with st.expander("Restows (Hourly)", expanded=False):
    st.markdown("**Restow Load**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.session_state["hr_fwd_restow_load"] = st.number_input("FWD Restow Load", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="in_hr_fwd_restow_load")
    with c2:
        st.session_state["hr_mid_restow_load"] = st.number_input("MID Restow Load", min_value=0, value=st.session_state["hr_mid_restow_load"], key="in_hr_mid_restow_load")
    with c3:
        st.session_state["hr_aft_restow_load"] = st.number_input("AFT Restow Load", min_value=0, value=st.session_state["hr_aft_restow_load"], key="in_hr_aft_restow_load")
    with c4:
        st.session_state["hr_poop_restow_load"] = st.number_input("POOP Restow Load", min_value=0, value=st.session_state["hr_poop_restow_load"], key="in_hr_poop_restow_load")

    st.markdown("**Restow Discharge**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.session_state["hr_fwd_restow_disch"] = st.number_input("FWD Restow Disch", min_value=0, value=st.session_state["hr_fwd_restow_disch"], key="in_hr_fwd_restow_disch")
    with c2:
        st.session_state["hr_mid_restow_disch"] = st.number_input("MID Restow Disch", min_value=0, value=st.session_state["hr_mid_restow_disch"], key="in_hr_mid_restow_disch")
    with c3:
        st.session_state["hr_aft_restow_disch"] = st.number_input("AFT Restow Disch", min_value=0, value=st.session_state["hr_aft_restow_disch"], key="in_hr_aft_restow_disch")
    with c4:
        st.session_state["hr_poop_restow_disch"] = st.number_input("POOP Restow Disch", min_value=0, value=st.session_state["hr_poop_restow_disch"], key="in_hr_poop_restow_disch")

# Hatch Moves (Open / Close) - note: no POOP hatch, only FWD MID AFT
with st.expander("Hatch Moves (Hourly)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["hr_hatch_fwd_open"] = st.number_input("FWD Hatch Open", min_value=0, value=st.session_state["hr_hatch_fwd_open"], key="in_hr_hatch_fwd_open")
    with c2:
        st.session_state["hr_hatch_mid_open"] = st.number_input("MID Hatch Open", min_value=0, value=st.session_state["hr_hatch_mid_open"], key="in_hr_hatch_mid_open")
    with c3:
        st.session_state["hr_hatch_aft_open"] = st.number_input("AFT Hatch Open", min_value=0, value=st.session_state["hr_hatch_aft_open"], key="in_hr_hatch_aft_open")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["hr_hatch_fwd_close"] = st.number_input("FWD Hatch Close", min_value=0, value=st.session_state["hr_hatch_fwd_close"], key="in_hr_hatch_fwd_close")
    with c2:
        st.session_state["hr_hatch_mid_close"] = st.number_input("MID Hatch Close", min_value=0, value=st.session_state["hr_hatch_mid_close"], key="in_hr_hatch_mid_close")
    with c3:
        st.session_state["hr_hatch_aft_close"] = st.number_input("AFT Hatch Close", min_value=0, value=st.session_state["hr_hatch_aft_close"], key="in_hr_hatch_aft_close")

# Idle / Delays (multiple)
st.header("Idle / Delays")
if "idle_entries" not in st.session_state:
    st.session_state["idle_entries"] = []
idle_crane = st.selectbox("Crane (or free text)", options=["FWD","MID","AFT","POOP","Other"], index=0)
idle_start = st.text_input("Start time (e.g. 12h30)")
idle_end = st.text_input("End time (e.g. 12h40)")
idle_choice = st.selectbox("Delay reason", options=[
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
    "Custom..."
])
idle_custom = ""
if idle_choice == "Custom...":
    idle_custom = st.text_input("Custom delay reason")
if st.button("Add Idle Entry"):
    reason = idle_custom if idle_choice == "Custom..." else idle_choice
    st.session_state["idle_entries"].append({"crane": idle_crane, "start": idle_start, "end": idle_end, "reason": reason})
    st.success("Idle entry added.")
if st.session_state["idle_entries"]:
    for i, e in enumerate(st.session_state["idle_entries"]):
        st.write(f"{i+1}. {e['crane']} {e['start']} - {e['end']} : {e['reason']}")
    if st.button("Clear Idle Entries"):
        st.session_state["idle_entries"] = []
        st.experimental_rerun()
        # Part 3/5

st.header("Generate / Save Hourly Report")

def compute_hourly_sums():
    load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]
    return load, disch, restow_load, restow_disch, hatch_open, hatch_close

def add_hour_to_cumulative_and_4h():
    load, disch, restow_load, restow_disch, hatch_open, hatch_close = compute_hourly_sums()
    # cumulative (persisted)
    cumulative["done_load"] = cumulative.get("done_load",0) + load
    cumulative["done_disch"] = cumulative.get("done_disch",0) + disch
    cumulative["done_restow_load"] = cumulative.get("done_restow_load",0) + restow_load
    cumulative["done_restow_disch"] = cumulative.get("done_restow_disch",0) + restow_disch
    cumulative["done_hatch_open"] = cumulative.get("done_hatch_open",0) + hatch_open
    cumulative["done_hatch_close"] = cumulative.get("done_hatch_close",0) + hatch_close
    cumulative["last_hour"] = st.session_state["hourly_time"]

    # 4-hour cumulative (persisted)
    cumulative_4h["fwd_load"] += st.session_state["hr_fwd_load"]
    cumulative_4h["mid_load"] += st.session_state["hr_mid_load"]
    cumulative_4h["aft_load"] += st.session_state["hr_aft_load"]
    cumulative_4h["poop_load"] += st.session_state["hr_poop_load"]

    cumulative_4h["fwd_disch"] += st.session_state["hr_fwd_disch"]
    cumulative_4h["mid_disch"] += st.session_state["hr_mid_disch"]
    cumulative_4h["aft_disch"] += st.session_state["hr_aft_disch"]
    cumulative_4h["poop_disch"] += st.session_state["hr_poop_disch"]

    cumulative_4h["fwd_restow_load"] += st.session_state["hr_fwd_restow_load"]
    cumulative_4h["mid_restow_load"] += st.session_state["hr_mid_restow_load"]
    cumulative_4h["aft_restow_load"] += st.session_state["hr_aft_restow_load"]
    cumulative_4h["poop_restow_load"] += st.session_state["hr_poop_restow_load"]

    cumulative_4h["fwd_restow_disch"] += st.session_state["hr_fwd_restow_disch"]
    cumulative_4h["mid_restow_disch"] += st.session_state["hr_mid_restow_disch"]
    cumulative_4h["aft_restow_disch"] += st.session_state["hr_aft_restow_disch"]
    cumulative_4h["poop_restow_disch"] += st.session_state["hr_poop_restow_disch"]

    cumulative_4h["fwd_hatch_open"] += st.session_state["hr_hatch_fwd_open"]
    cumulative_4h["mid_hatch_open"] += st.session_state["hr_hatch_mid_open"]
    cumulative_4h["aft_hatch_open"] += st.session_state["hr_hatch_aft_open"]

    cumulative_4h["fwd_hatch_close"] += st.session_state["hr_hatch_fwd_close"]
    cumulative_4h["mid_hatch_close"] += st.session_state["hr_hatch_mid_close"]
    cumulative_4h["aft_hatch_close"] += st.session_state["hr_hatch_aft_close"]

    # persist to disk
    save_json(SAVE_FILE, cumulative)
    save_json(SAVE_FILE_4H, cumulative_4h)

def compute_remaining():
    rem_load = cumulative.get("planned_load",0) - cumulative.get("done_load",0) - cumulative.get("opening_load",0)
    rem_disch = cumulative.get("planned_disch",0) - cumulative.get("done_disch",0) - cumulative.get("opening_disch",0)
    rem_restow_load = cumulative.get("planned_restow_load",0) - cumulative.get("done_restow_load",0) - cumulative.get("opening_restow_load",0)
    rem_restow_disch = cumulative.get("planned_restow_disch",0) - cumulative.get("done_restow_disch",0) - cumulative.get("opening_restow_disch",0)
    return rem_load, rem_disch, rem_restow_load, rem_restow_disch

# Button to generate & save hourly (updates cumulative and 4h)
if st.button("Submit Hourly Moves (update cumulative & 4h)"):
    add_hour_to_cumulative_and_4h()
    st.success("Hourly numbers added to cumulative and 4-hour totals.")
    # auto-advance hourly time to next slot
    try:
        cur = st.session_state["hourly_time"]
        # parse first two digits for hour
        m = re.match(r"(\d{2})h00 - (\d{2})h00", cur)
        if m:
            start_h = int(m.group(1))
            next_index = (start_h + 1) % 24
            new_hour = f"{str(next_index).zfill(2)}h00 - {str((next_index+1)%24).zfill(2)}h00"
            st.session_state["hourly_time"] = new_hour
        else:
            # fallback rotate index
            idx = hours_list.index(cur) if cur in hours_list else 0
            new_idx = (idx + 1) % len(hours_list)
            st.session_state["hourly_time"] = hours_list[new_idx]
    except Exception:
        pass
    st.experimental_rerun()

# Show cumulative small summary
st.subheader("Cumulative (persisted)")
rem_load, rem_disch, rem_rload, rem_rdisch = compute_remaining()
col1, col2 = st.columns(2)
with col1:
    st.write("Load: Plan", cumulative.get("planned_load"), "Done", cumulative.get("done_load"), "Remain", rem_load)
    st.write("Discharge: Plan", cumulative.get("planned_disch"), "Done", cumulative.get("done_disch"), "Remain", rem_disch)
with col2:
    st.write("Restow Load: Plan", cumulative.get("planned_restow_load"), "Done", cumulative.get("done_restow_load"), "Remain", rem_rload)
    st.write("Restow Disch: Plan", cumulative.get("planned_restow_disch"), "Done", cumulative.get("done_restow_disch"), "Remain", rem_rdisch)
    # Part 4/5

st.header("WhatsApp Template (Hourly)")

# Build the hourly template EXACTLY like your original (monospace)
def build_hourly_template():
    # Use variables from current inputs (not cumulative unless required)
    date_str = st.session_state.get("report_date_str", datetime.now().strftime("%d/%m/%Y"))
    ht = st.session_state["hourly_time"]
    # per crane hourly values (use current hourly session_state values)
    fwd_l = st.session_state["hr_fwd_load"]
    mid_l = st.session_state["hr_mid_load"]
    aft_l = st.session_state["hr_aft_load"]
    poop_l = st.session_state["hr_poop_load"]

    fwd_d = st.session_state["hr_fwd_disch"]
    mid_d = st.session_state["hr_mid_disch"]
    aft_d = st.session_state["hr_aft_disch"]
    poop_d = st.session_state["hr_poop_disch"]

    fwd_rl = st.session_state["hr_fwd_restow_load"]
    mid_rl = st.session_state["hr_mid_restow_load"]
    aft_rl = st.session_state["hr_aft_restow_load"]
    poop_rl = st.session_state["hr_poop_restow_load"]

    fwd_rd = st.session_state["hr_fwd_restow_disch"]
    mid_rd = st.session_state["hr_mid_restow_disch"]
    aft_rd = st.session_state["hr_aft_restow_disch"]
    poop_rd = st.session_state["hr_poop_restow_disch"]

    # cumulative done values (persisted)
    c_done_load = cumulative.get("done_load",0)
    c_done_disch = cumulative.get("done_disch",0)
    c_done_rl = cumulative.get("done_restow_load",0)
    c_done_rd = cumulative.get("done_restow_disch",0)

    # plan and remain (use opening as deduction)
    plan_load = cumulative.get("planned_load",0)
    plan_disch = cumulative.get("planned_disch",0)
    remain_load = plan_load - c_done_load - cumulative.get("opening_load",0)
    remain_disch = plan_disch - c_done_disch - cumulative.get("opening_disch",0)

    plan_rl = cumulative.get("planned_restow_load",0)
    plan_rd = cumulative.get("planned_restow_disch",0)
    remain_rl = plan_rl - c_done_rl - cumulative.get("opening_restow_load",0)
    remain_rd = plan_rd - c_done_rd - cumulative.get("opening_restow_disch",0)

    # Hatch hourly values (current)
    hf_fwd_o = st.session_state["hr_hatch_fwd_open"]
    hf_mid_o = st.session_state["hr_hatch_mid_open"]
    hf_aft_o = st.session_state["hr_hatch_aft_open"]
    hf_fwd_c = st.session_state["hr_hatch_fwd_close"]
    hf_mid_c = st.session_state["hr_hatch_mid_close"]
    hf_aft_c = st.session_state["hr_hatch_aft_close"]

    # build template matching the user's original lines and spacing.
    tpl = (
f"{cumulative.get('vessel_name')}\n"
f"Berthed {cumulative.get('berthed_date')}\n\n"
f"First Lift @ {cumulative.get('first_lift')}\n"
f"Last Lift @  {cumulative.get('last_lift')}\n\n"
f"{date_str}\n"
f"{ht}\n"
"_________________________\n"
"   *HOURLY MOVES*\n"
"_________________________\n"
"*Crane Moves*\n"
"           Load      Discharge   \n"
f"FWD      {fwd_l:>6}       {fwd_d:>6}\n"
f"MID      {mid_l:>6}       {mid_d:>6}\n"
f"AFT      {aft_l:>6}       {aft_d:>6}\n"
f"POOP     {poop_l:>6}       {poop_d:>6}\n"
"_______________________\n"
"*Restows*\n\n"
"          Load      Discharge   \n"
f"FWD      {fwd_rl:>6}       {fwd_rd:>6}\n"
f"MID      {mid_rl:>6}       {mid_rd:>6}\n"
f"AFT      {aft_rl:>6}       {aft_rd:>6}\n"
f"POOP     {poop_rl:>6}       {poop_rd:>6}\n\n"
"_______________________\n"
"      *CUMULATIVE* ________________________\n"
"                Load      Disch \n"
f"Plan.        {plan_load:>6}       {plan_disch:>6}\n"
f"Done        {c_done_load:>6}       {c_done_disch:>6}\n"
f"Remain     {remain_load:>6}       {remain_disch:>6}\n"
"________________________    \n"
"  *Restows*\n"
"               Load     Disch\n"
f"Plan         {plan_rl:>6}       {plan_rd:>6} \n"
f"Done        {c_done_rl:>6}       {c_done_rd:>6}\n"
f"Remain     {remain_rl:>6}       {remain_rd:>6}\n"
"_______________________\n"
"*Hatch Moves*\n"
"            Open    Close\n"
f"FWD     {hf_fwd_o:>6}       {hf_fwd_c:>6}\n"
f"MID     {hf_mid_o:>6}       {hf_mid_c:>6}\n"
f"AFT     {hf_aft_o:>6}       {hf_aft_c:>6}\n"
"                       \n"
"_________________________\n"
"*Gear boxes* \n\n"
"________________________\n"
"*Idle*\n"
)
    # Append idle entries
    if st.session_state.get("idle_entries"):
        tpl += "\n"
        for e in st.session_state["idle_entries"]:
            tpl += f"{e['crane']} {e['start']} - {e['end']}  {e['reason']}\n"

    return tpl

# show template in monospace so it copies straight
hourly_template = build_hourly_template()
# allow user to edit the template before sending
if st.checkbox("Edit template before sending (show editor)", value=False):
    edited_template = st.text_area("Edit WhatsApp template (monospace preserved)", value=hourly_template, height=300)
else:
    edited_template = hourly_template
    st.code(hourly_template, language="text")

# Send options
st.markdown("**Send to WhatsApp**")
wa_number = st.text_input("WhatsApp private number (with country code, e.g. 27761234567)")
wa_group = st.text_input("Or WhatsApp Group link (optional)")

if st.button("Open WhatsApp (private)"):
    if wa_number:
        wa_text = urllib.parse.quote(edited_template)
        wa_link = f"https://wa.me/{wa_number}?text={wa_text}"
        st.markdown(f"[Open WhatsApp link]({wa_link})", unsafe_allow_html=True)
    else:
        st.warning("Enter a WhatsApp number first.")

if st.button("Open WhatsApp Group (open link)"):
    if wa_group:
        st.markdown(f"[Open group link]({wa_group})", unsafe_allow_html=True)
    else:
        st.warning("Enter a WhatsApp group link first.")
        # Part 5/5

st.header("4-Hourly Report & Final Controls")

# allow manual edits of 4-hourly counts if needed (but they auto-accumulate from Submit Hourly)
with st.expander("4-Hourly counts (editable)"):
    # ensure keys exist in cumulative_4h
    for k in default_4h.keys():
        if k not in cumulative_4h:
            cumulative_4h[k] = 0

    c1, c2 = st.columns(2)
    with c1:
        cumulative_4h["fwd_load"] = st.number_input("FWD Load (4h)", value=cumulative_4h.get("fwd_load",0), key="in_4h_fwd_load")
        cumulative_4h["mid_load"] = st.number_input("MID Load (4h)", value=cumulative_4h.get("mid_load",0), key="in_4h_mid_load")
        cumulative_4h["aft_load"] = st.number_input("AFT Load (4h)", value=cumulative_4h.get("aft_load",0), key="in_4h_aft_load")
        cumulative_4h["poop_load"] = st.number_input("POOP Load (4h)", value=cumulative_4h.get("poop_load",0), key="in_4h_poop_load")
    with c2:
        cumulative_4h["fwd_disch"] = st.number_input("FWD Disch (4h)", value=cumulative_4h.get("fwd_disch",0), key="in_4h_fwd_disch")
        cumulative_4h["mid_disch"] = st.number_input("MID Disch (4h)", value=cumulative_4h.get("mid_disch",0), key="in_4h_mid_disch")
        cumulative_4h["aft_disch"] = st.number_input("AFT Disch (4h)", value=cumulative_4h.get("aft_disch",0), key="in_4h_aft_disch")
        cumulative_4h["poop_disch"] = st.number_input("POOP Disch (4h)", value=cumulative_4h.get("poop_disch",0), key="in_4h_poop_disch")

    # restows & hatch in more inputs if needed
    st.markdown("Edit restow and hatch if required (these values also update the 4-hour template).")

    # save manual edits immediately
    save_json(SAVE_FILE_4H, cumulative_4h)

# 4-hour template (use same layout style but indicate it's the 4-hour block)
def build_4h_template():
    date_str = st.session_state.get("report_date_str", datetime.now().strftime("%d/%m/%Y"))
    start = st.session_state.get("hourly_time", "06h00 - 07h00")
    # compute end by parsing first hour
    m = re.match(r"(\d{2})h00 - (\d{2})h00", start)
    if m:
        s = int(m.group(1))
        e = (s + 4) % 24
        end_str = f"{str(e).zfill(2)}h00"
    else:
        end_str = "??h??"
    # use cumulative_4h values
    tpl = (
f"{cumulative.get('vessel_name')}\n"
f"Berthed {cumulative.get('berthed_date')}\n\n"
f"Date: {date_str}\n"
f"4-Hour Block: {start} - {end_str}\n"
"_________________________\n"
"   *HOURLY MOVES*\n"
"_________________________\n"
"*Crane Moves*\n"
"           Load    Discharge\n"
f"FWD       {cumulative_4h['fwd_load']:>6}     {cumulative_4h['fwd_disch']:>6}\n"
f"MID       {cumulative_4h['mid_load']:>6}     {cumulative_4h['mid_disch']:>6}\n"
f"AFT       {cumulative_4h['aft_load']:>6}     {cumulative_4h['aft_disch']:>6}\n"
f"POOP      {cumulative_4h['poop_load']:>6}     {cumulative_4h['poop_disch']:>6}\n"
"_________________________\n"
"*Restows*\n"
"           Load    Discharge\n"
f"FWD       {cumulative_4h['fwd_restow_load']:>6}     {cumulative_4h['fwd_restow_disch']:>6}\n"
f"MID       {cumulative_4h['mid_restow_load']:>6}     {cumulative_4h['mid_restow_disch']:>6}\n"
f"AFT       {cumulative_4h['aft_restow_load']:>6}     {cumulative_4h['aft_restow_disch']:>6}\n"
f"POOP      {cumulative_4h['poop_restow_load']:>6}     {cumulative_4h['poop_restow_disch']:>6}\n\n"
"_________________________\n"
"*CUMULATIVE* (from hourly saved entries)\n"
"_________________________\n"
f"Plan       {cumulative.get('planned_load',0):>6}     {cumulative.get('planned_disch',0):>6}\n"
f"Done       {cumulative.get('done_load',0):>6}     {cumulative.get('done_disch',0):>6}\n"
f"Remain     {cumulative.get('planned_load',0)-cumulative.get('done_load',0)-cumulative.get('opening_load',0):>6}     {cumulative.get('planned_disch',0)-cumulative.get('done_disch',0)-cumulative.get('opening_disch',0):>6}\n"
"_________________________\n"
"*Restows*\n"
f"Plan       {cumulative.get('planned_restow_load',0):>6}     {cumulative.get('planned_restow_disch',0):>6}\n"
f"Done       {cumulative.get('done_restow_load',0):>6}     {cumulative.get('done_restow_disch',0):>6}\n"
f"Remain     {cumulative.get('planned_restow_load',0)-cumulative.get('done_restow_load',0)-cumulative.get('opening_restow_load',0):>6}     {cumulative.get('planned_restow_disch',0)-cumulative.get('done_restow_disch',0)-cumulative.get('opening_restow_disch',0):>6}\n"
"_________________________\n"
"*Hatch Moves*\n"
"            Open    Close\n"
f"FWD     {cumulative_4h['fwd_hatch_open']:>6}     {cumulative_4h['fwd_hatch_close']:>6}\n"
f"MID     {cumulative_4h['mid_hatch_open']:>6}     {cumulative_4h['mid_hatch_close']:>6}\n"
f"AFT     {cumulative_4h['aft_hatch_open']:>6}     {cumulative_4h['aft_hatch_close']:>6}\n"
)
    # append idle entries if any
    if st.session_state.get("idle_entries"):
        tpl += "\nIdle / Delays:\n"
        for e in st.session_state["idle_entries"]:
            tpl += f"{e['crane']} {e['start']} - {e['end']} : {e['reason']}\n"
    return tpl

tpl_4h = build_4h_template()
if st.checkbox("Edit 4-hour template before sending (show editor)", value=False):
    tpl_4h_edited = st.text_area("Edit 4-hour template", value=tpl_4h, height=360)
else:
    tpl_4h_edited = tpl_4h
    st.code(tpl_4h, language="text")

# Send 4-hour via wa
wa_number_4h = st.text_input("WhatsApp number for 4h (with country code, optional)")
wa_group_4h = st.text_input("WhatsApp group link for 4h (optional)")
if st.button("Open WhatsApp (4h private)"):
    if wa_number_4h:
        wa_text = urllib.parse.quote(tpl_4h_edited)
        st.markdown(f"[Open WhatsApp link](https://wa.me/{wa_number_4h}?text={wa_text})", unsafe_allow_html=True)
    else:
        st.warning("Enter number first.")
if st.button("Open WhatsApp Group (4h)"):
    if wa_group_4h:
        st.markdown(f"[Open group link]({wa_group_4h})", unsafe_allow_html=True)
    else:
        st.warning("Enter group link first.")

# final save of 4h edits (if user changed manual input earlier, already saved)
save_json(SAVE_FILE_4H, cumulative_4h)

# final footer note
st.markdown("---")
st.info("Template preserved exactly as original. Use the edit boxes if you want to tweak before sending. Hourly 'Submit' updates cumulative and 4-hour totals and auto-advances the hourly slot. Use reset buttons to clear counters.")
