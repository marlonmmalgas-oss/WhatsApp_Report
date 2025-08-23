# WhatsApp_Report.py  (Part 1/5)

import streamlit as st
import json, os, urllib.parse
from datetime import datetime, date
import pytz

SAVE_FILE = "vessel_report.json"
SA_TZ = pytz.timezone("Africa/Johannesburg")

# ---------- Helpers ----------
def today_sa_str() -> str:
    return datetime.now(SA_TZ).strftime("%d/%m/%Y")

def ensure_state_defaults():
    # Vessel, plan, opening, times
    defaults = {
        "vessel_name": "MSC NILA",
        "berthed_date": "14/08/2025 @ 10H55",
        "first_lift_time": "18h25",
        "last_lift_time": "10h31",
        "report_date": today_sa_str(),

        # Planned & opening (deductions)
        "planned_load": 687,
        "planned_disch": 38,
        "planned_restow_load": 13,
        "planned_restow_disch": 13,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0,

        # Cumulative DONE totals
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,

        # Hour index & last hour label
        "hour_idx": 0,
        "last_hour": "06h00 - 07h00",

        # Hourly inputs
        "hr_fwd_load": 0, "hr_mid_load": 0, "hr_aft_load": 0, "hr_poop_load": 0,
        "hr_fwd_disch": 0, "hr_mid_disch": 0, "hr_aft_disch": 0, "hr_poop_disch": 0,

        "hr_rst_fwd_load": 0, "hr_rst_mid_load": 0, "hr_rst_aft_load": 0, "hr_rst_poop_load": 0,
        "hr_rst_fwd_disch": 0, "hr_rst_mid_disch": 0, "hr_rst_aft_disch": 0, "hr_rst_poop_disch": 0,

        "hr_hat_fwd_open": 0, "hr_hat_mid_open": 0, "hr_hat_aft_open": 0,
        "hr_hat_fwd_close": 0, "hr_hat_mid_close": 0, "hr_hat_aft_close": 0,

        # Idle
        "idle_count": 1,
        "idle_entries": [],   # list of dicts

        # WhatsApp targets
        "wa_number": "",
        "wa_group_link": "",

        # HISTORY of hourly submissions (for audit reference if needed)
        "history": [],

        # 4-hour tracker store (per-date per-block)
        # key = f"{report_date}|{block_label}" -> dict of counters
        "block_store": {},

        # 4-hour manual override on/off and values
        "use_4h_manual": False,
        "ovr_4h": {
            "fwd_load": 0, "mid_load": 0, "aft_load": 0, "poop_load": 0,
            "fwd_disch": 0, "mid_disch": 0, "aft_disch": 0, "poop_disch": 0,
            "rst_fwd_load": 0, "rst_mid_load": 0, "rst_aft_load": 0, "rst_poop_load": 0,
            "rst_fwd_disch": 0, "rst_mid_disch": 0, "rst_aft_disch": 0, "rst_poop_disch": 0,
            "hat_fwd_open": 0, "hat_mid_open": 0, "hat_aft_open": 0,
            "hat_fwd_close": 0, "hat_mid_close": 0, "hat_aft_close": 0,
        },

        # selected 4h block
        "four_block": "06h00 - 10h00",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def hours_sequence_6_to_5():
    seq = []
    for h in list(range(6, 24)) + list(range(0, 6)):
        seq.append(f"{h:02d}h00 - {((h+1)%24):02d}h00")
    return seq

def get_block_label_from_hour_label(hour_label: str) -> str:
    # map an hour to its 4-hour block label
    blocks = [
        (6, 10), (10, 14), (14, 18),
        (18, 22), (22, 2), (2, 6)
    ]
    try:
        start_h = int(hour_label[:2])
    except:
        return "06h00 - 10h00"
    for s, e in blocks:
        if s < e and (start_h >= s and start_h < e):
            return f"{s:02d}h00 - {e:02d}h00"
        if s > e:  # wrap
            if (start_h >= s and start_h <= 23) or (start_h >= 0 and start_h < e):
                return f"{s:02d}h00 - {e:02d}h00"
    return "06h00 - 10h00"

def save_json():
    data = {k: st.session_state[k] for k in st.session_state.keys()}
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_json_into_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            for k, v in data.items():
                st.session_state[k] = v
        except Exception:
            pass

# ---------- Start App ----------
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Tracker", layout="centered")
load_json_into_state()
ensure_state_defaults()

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --- Vessel Info (kept simple & editable; persists) ---
with st.expander("⛴️ Vessel Info", expanded=True):
    st.session_state["vessel_name"] = st.text_input("Vessel Name", st.session_state["vessel_name"], key="vessel_name_input")
    st.session_state["berthed_date"] = st.text_input("Berthed Date", st.session_state["berthed_date"], key="berthed_date_input")

    c1, c2 = st.columns(2)
    with c1:
        # SA date by default + picker
        try:
            dparts = [int(x) for x in st.session_state["report_date"].split("/")]  # dd/mm/yyyy
            default_d = date(dparts[2], dparts[1], dparts[0])
        except Exception:
            default_d = date.today()
        new_date = st.date_input("Report Date", value=default_d, key="report_date_picker")
        st.session_state["report_date"] = new_date.strftime("%d/%m/%Y")
    with c2:
        st.session_state["first_lift_time"] = st.text_input("First Lift (time only)", st.session_state["first_lift_time"], key="first_lift_time_input")
        st.session_state["last_lift_time"] = st.text_input("Last Lift (time only)", st.session_state["last_lift_time"], key="last_lift_time_input")

# --- Plan & Opening (Internal Only) ---
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["planned_load"]  = st.number_input("Planned Load", value=int(st.session_state["planned_load"]), min_value=0, key="planned_load")
        st.session_state["planned_disch"] = st.number_input("Planned Discharge", value=int(st.session_state["planned_disch"]), min_value=0, key="planned_disch")
        st.session_state["planned_restow_load"]  = st.number_input("Planned Restow Load", value=int(st.session_state["planned_restow_load"]), min_value=0, key="planned_restow_load")
        st.session_state["planned_restow_disch"] = st.number_input("Planned Restow Discharge", value=int(st.session_state["planned_restow_disch"]), min_value=0, key="planned_restow_disch")
    with col2:
        st.session_state["opening_load"]  = st.number_input("Opening Load (Deduction)", value=int(st.session_state["opening_load"]), min_value=0, key="opening_load")
        st.session_state["opening_disch"] = st.number_input("Opening Discharge (Deduction)", value=int(st.session_state["opening_disch"]), min_value=0, key="opening_disch")
        st.session_state["opening_restow_load"]  = st.number_input("Opening Restow Load (Deduction)", value=int(st.session_state["opening_restow_load"]), min_value=0, key="opening_restow_load")
        st.session_state["opening_restow_disch"] = st.number_input("Opening Restow Discharge (Deduction)", value=int(st.session_state["opening_restow_disch"]), min_value=0, key="opening_restow_disch")

save_json()
# WhatsApp_Report.py  (Part 2/5)  -- append below Part 1

# --- Hour selection (06 → 05 sequence) ---
hours_list = hours_sequence_6_to_5()

# trusted default index
try:
    if st.session_state.get("last_hour") in hours_list:
        default_idx = hours_list.index(st.session_state["last_hour"])
    else:
        default_idx = st.session_state.get("hour_idx", 0)
        if default_idx < 0 or default_idx >= len(hours_list):
            default_idx = 0
except Exception:
    default_idx = 0

hourly_time = st.selectbox("⏱ Select Hourly Time", options=hours_list, index=default_idx, key="hourly_time_select")

st.header(f"Hourly Moves Input ({hourly_time})")

# --- Crane Moves (collapsible with sub-groups) ---
with st.expander("🛠️ Crane Moves", expanded=True):
    with st.expander("Load", expanded=False):
        st.session_state["hr_fwd_load"]  = st.number_input("FWD Load",  min_value=0, value=int(st.session_state["hr_fwd_load"]),  key="hr_fwd_load")
        st.session_state["hr_mid_load"]  = st.number_input("MID Load",  min_value=0, value=int(st.session_state["hr_mid_load"]),  key="hr_mid_load")
        st.session_state["hr_aft_load"]  = st.number_input("AFT Load",  min_value=0, value=int(st.session_state["hr_aft_load"]),  key="hr_aft_load")
        st.session_state["hr_poop_load"] = st.number_input("POOP Load", min_value=0, value=int(st.session_state["hr_poop_load"]), key="hr_poop_load")
    with st.expander("Discharge", expanded=False):
        st.session_state["hr_fwd_disch"]  = st.number_input("FWD Discharge",  min_value=0, value=int(st.session_state["hr_fwd_disch"]),  key="hr_fwd_disch")
        st.session_state["hr_mid_disch"]  = st.number_input("MID Discharge",  min_value=0, value=int(st.session_state["hr_mid_disch"]),  key="hr_mid_disch")
        st.session_state["hr_aft_disch"]  = st.number_input("AFT Discharge",  min_value=0, value=int(st.session_state["hr_aft_disch"]),  key="hr_aft_disch")
        st.session_state["hr_poop_disch"] = st.number_input("POOP Discharge", min_value=0, value=int(st.session_state["hr_poop_disch"]), key="hr_poop_disch")

# --- Restows (collapsible with sub-groups) ---
with st.expander("🔁 Restows", expanded=False):
    with st.expander("Load", expanded=False):
        st.session_state["hr_rst_fwd_load"]  = st.number_input("FWD Restow Load",  min_value=0, value=int(st.session_state["hr_rst_fwd_load"]),  key="hr_rst_fwd_load")
        st.session_state["hr_rst_mid_load"]  = st.number_input("MID Restow Load",  min_value=0, value=int(st.session_state["hr_rst_mid_load"]),  key="hr_rst_mid_load")
        st.session_state["hr_rst_aft_load"]  = st.number_input("AFT Restow Load",  min_value=0, value=int(st.session_state["hr_rst_aft_load"]),  key="hr_rst_aft_load")
        st.session_state["hr_rst_poop_load"] = st.number_input("POOP Restow Load", min_value=0, value=int(st.session_state["hr_rst_poop_load"]), key="hr_rst_poop_load")
    with st.expander("Discharge", expanded=False):
        st.session_state["hr_rst_fwd_disch"]  = st.number_input("FWD Restow Discharge",  min_value=0, value=int(st.session_state["hr_rst_fwd_disch"]),  key="hr_rst_fwd_disch")
        st.session_state["hr_rst_mid_disch"]  = st.number_input("MID Restow Discharge",  min_value=0, value=int(st.session_state["hr_rst_mid_disch"]),  key="hr_rst_mid_disch")
        st.session_state["hr_rst_aft_disch"]  = st.number_input("AFT Restow Discharge",  min_value=0, value=int(st.session_state["hr_rst_aft_disch"]),  key="hr_rst_aft_disch")
        st.session_state["hr_rst_poop_disch"] = st.number_input("POOP Restow Discharge", min_value=0, value=int(st.session_state["hr_rst_poop_disch"]), key="hr_rst_poop_disch")

# --- Hatch Moves (collapsible with sub-groups) ---
with st.expander("🪤 Hatch Moves", expanded=False):
    with st.expander("Open", expanded=False):
        st.session_state["hr_hat_fwd_open"] = st.number_input("FWD Hatch Open", min_value=0, value=int(st.session_state["hr_hat_fwd_open"]), key="hr_hat_fwd_open")
        st.session_state["hr_hat_mid_open"] = st.number_input("MID Hatch Open", min_value=0, value=int(st.session_state["hr_hat_mid_open"]), key="hr_hat_mid_open")
        st.session_state["hr_hat_aft_open"] = st.number_input("AFT Hatch Open", min_value=0, value=int(st.session_state["hr_hat_aft_open"]), key="hr_hat_aft_open")
    with st.expander("Close", expanded=False):
        st.session_state["hr_hat_fwd_close"] = st.number_input("FWD Hatch Close", min_value=0, value=int(st.session_state["hr_hat_fwd_close"]), key="hr_hat_fwd_close")
        st.session_state["hr_hat_mid_close"] = st.number_input("MID Hatch Close", min_value=0, value=int(st.session_state["hr_hat_mid_close"]), key="hr_hat_mid_close")
        st.session_state["hr_hat_aft_close"] = st.number_input("AFT Hatch Close", min_value=0, value=int(st.session_state["hr_hat_aft_close"]), key="hr_hat_aft_close")

# --- Idle / Delays (collapsible with variable count) ---
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

with st.expander("🕒 Idle / Delays", expanded=False):
    st.session_state["idle_count"] = st.number_input("Number of Idle Entries", min_value=1, max_value=10, value=int(st.session_state["idle_count"]), key="idle_count_input")
    entries = []
    for i in range(st.session_state["idle_count"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        with c1:
            crane = st.text_input(f"Crane {i+1}", key=f"id_crane_{i}", value=(st.session_state.get("idle_entries", [{}]*st.session_state["idle_count"])[i].get("crane","") if len(st.session_state.get("idle_entries",[]))>i else ""))
        with c2:
            start_t = st.text_input(f"Start {i+1}", key=f"id_start_{i}", value=(st.session_state.get("idle_entries", [{}]*st.session_state["idle_count"])[i].get("start","") if len(st.session_state.get("idle_entries",[]))>i else ""))
        with c3:
            end_t = st.text_input(f"End {i+1}", key=f"id_end_{i}", value=(st.session_state.get("idle_entries", [{}]*st.session_state["idle_count"])[i].get("end","") if len(st.session_state.get("idle_entries",[]))>i else ""))
        with c4:
            sel = st.selectbox(f"Delay {i+1}", options=idle_options, key=f"id_sel_{i}", index=0)
        custom = st.text_input(f"Custom Delay {i+1} (optional)", key=f"id_cus_{i}", value=(st.session_state.get("idle_entries", [{}]*st.session_state["idle_count"])[i].get("custom","") if len(st.session_state.get("idle_entries",[]))>i else ""))
        entries.append({"crane": crane, "start": start_t, "end": end_t, "delay": custom if custom else sel, "custom": custom})
    st.session_state["idle_entries"] = entries

save_json()
# WhatsApp_Report.py  (Part 3/5)  -- append below Part 2

# --- WhatsApp targets ---
with st.expander("📤 Send Hourly Report to WhatsApp", expanded=False):
    st.session_state["wa_number"] = st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", st.session_state["wa_number"], key="wa_number_input")
    st.session_state["wa_group_link"] = st.text_input("Or enter WhatsApp Group Link (optional)", st.session_state["wa_group_link"], key="wa_group_link_input")

# --- Compute planned remaining (live preview for UI context only) ---
def compute_remaining():
    rem_load  = int(st.session_state["planned_load"])  - int(st.session_state["done_load"])         - int(st.session_state["opening_load"])
    rem_disch = int(st.session_state["planned_disch"]) - int(st.session_state["done_disch"])        - int(st.session_state["opening_disch"])
    rem_rl    = int(st.session_state["planned_restow_load"])  - int(st.session_state["done_restow_load"])  - int(st.session_state["opening_restow_load"])
    rem_rd    = int(st.session_state["planned_restow_disch"]) - int(st.session_state["done_restow_disch"]) - int(st.session_state["opening_restow_disch"])
    return rem_load, rem_disch, rem_rl, rem_rd

# --- Add this hour into 4-hour tracker store ---
def add_to_block_store(hour_label: str):
    block = get_block_label_from_hour_label(hour_label)
    key = f"{st.session_state['report_date']}|{block}"
    bs = st.session_state["block_store"].get(key, None)
    if not bs:
        bs = {
            "fwd_load":0,"mid_load":0,"aft_load":0,"poop_load":0,
            "fwd_disch":0,"mid_disch":0,"aft_disch":0,"poop_disch":0,
            "rst_fwd_load":0,"rst_mid_load":0,"rst_aft_load":0,"rst_poop_load":0,
            "rst_fwd_disch":0,"rst_mid_disch":0,"rst_aft_disch":0,"rst_poop_disch":0,
            "hat_fwd_open":0,"hat_mid_open":0,"hat_aft_open":0,
            "hat_fwd_close":0,"hat_mid_close":0,"hat_aft_close":0,
            "hours_count":0
        }
    # accumulate this hour
    bs["fwd_load"]  += int(st.session_state["hr_fwd_load"])
    bs["mid_load"]  += int(st.session_state["hr_mid_load"])
    bs["aft_load"]  += int(st.session_state["hr_aft_load"])
    bs["poop_load"] += int(st.session_state["hr_poop_load"])

    bs["fwd_disch"]  += int(st.session_state["hr_fwd_disch"])
    bs["mid_disch"]  += int(st.session_state["hr_mid_disch"])
    bs["aft_disch"]  += int(st.session_state["hr_aft_disch"])
    bs["poop_disch"] += int(st.session_state["hr_poop_disch"])

    bs["rst_fwd_load"]  += int(st.session_state["hr_rst_fwd_load"])
    bs["rst_mid_load"]  += int(st.session_state["hr_rst_mid_load"])
    bs["rst_aft_load"]  += int(st.session_state["hr_rst_aft_load"])
    bs["rst_poop_load"] += int(st.session_state["hr_rst_poop_load"])

    bs["rst_fwd_disch"]  += int(st.session_state["hr_rst_fwd_disch"])
    bs["rst_mid_disch"]  += int(st.session_state["hr_rst_mid_disch"])
    bs["rst_aft_disch"]  += int(st.session_state["hr_rst_aft_disch"])
    bs["rst_poop_disch"] += int(st.session_state["hr_rst_poop_disch"])

    bs["hat_fwd_open"] += int(st.session_state["hr_hat_fwd_open"])
    bs["hat_mid_open"] += int(st.session_state["hr_hat_mid_open"])
    bs["hat_aft_open"] += int(st.session_state["hr_hat_aft_open"])

    bs["hat_fwd_close"] += int(st.session_state["hr_hat_fwd_close"])
    bs["hat_mid_close"] += int(st.session_state["hr_hat_mid_close"])
    bs["hat_aft_close"] += int(st.session_state["hr_hat_aft_close"])

    bs["hours_count"] += 1
    st.session_state["block_store"][key] = bs

def hourly_template_str(hour_label: str):
    remL, remD, remRL, remRD = compute_remaining()
    v = st.session_state
    L = "_________________________"
    template = f"""\
{v['vessel_name']}
Berthed {v['berthed_date']}

First Lift @ {v['first_lift_time']}
Last lift @  {v['last_lift_time']}

{v['report_date']}
{hour_label}
{L}
   *HOURLY MOVES*
{L}
*Crane Moves*
           Load   Discharge
FWD       {int(v['hr_fwd_load']):>5}     {int(v['hr_fwd_disch']):>5}
MID       {int(v['hr_mid_load']):>5}     {int(v['hr_mid_disch']):>5}
AFT       {int(v['hr_aft_load']):>5}     {int(v['hr_aft_disch']):>5}
POOP      {int(v['hr_poop_load']):>5}     {int(v['hr_poop_disch']):>5}
{L}
*Restows*
           Load   Discharge
FWD       {int(v['hr_rst_fwd_load']):>5}     {int(v['hr_rst_fwd_disch']):>5}
MID       {int(v['hr_rst_mid_load']):>5}     {int(v['hr_rst_mid_disch']):>5}
AFT       {int(v['hr_rst_aft_load']):>5}     {int(v['hr_rst_aft_disch']):>5}
POOP      {int(v['hr_rst_poop_load']):>5}     {int(v['hr_rst_poop_disch']):>5}
{L}
      *CUMULATIVE*
{L}
           Load   Disch
Plan       {int(v['planned_load']):>5}      {int(v['planned_disch']):>5}
Done       {int(v['done_load']):>5}      {int(v['done_disch']):>5}
Remain     {int(remL):>5}      {int(remD):>5}
{L}
*Restows*
           Load   Disch
Plan       {int(v['planned_restow_load']):>5}      {int(v['planned_restow_disch']):>5}
Done       {int(v['done_restow_load']):>5}      {int(v['done_restow_disch']):>5}
Remain     {int(remRL):>5}      {int(remRD):>5}
{L}
*Hatch Moves*
           Open   Close
FWD       {int(v['hr_hat_fwd_open']):>5}      {int(v['hr_hat_fwd_close']):>5}
MID       {int(v['hr_hat_mid_open']):>5}      {int(v['hr_hat_mid_close']):>5}
AFT       {int(v['hr_hat_aft_open']):>5}      {int(v['hr_hat_aft_close']):>5}
{L}
*Gear boxes* 

{L}
*Idle*
"""
    for i, idle in enumerate(v["idle_entries"], start=1):
        if idle.get("crane") or idle.get("start") or idle.get("end") or idle.get("delay"):
            template += f"{i}. {idle.get('crane','')} {idle.get('start','')}-{idle.get('end','')} : {idle.get('delay','')}\n"
    return template

# --- Action buttons row ---
cA, cB, cC = st.columns([1,1,1])
with cA:
    gen_hourly = st.button("✅ Generate Hourly Template")
with cB:
    reset_hourly = st.button("♻️ Reset Hourly Inputs")
with cC:
    pass

# --- Handle Hourly Generate ---
if gen_hourly:
    # Update cumulative DONE
    st.session_state["done_load"]  += int(st.session_state["hr_fwd_load"]) + int(st.session_state["hr_mid_load"]) + int(st.session_state["hr_aft_load"]) + int(st.session_state["hr_poop_load"])
    st.session_state["done_disch"] += int(st.session_state["hr_fwd_disch"]) + int(st.session_state["hr_mid_disch"]) + int(st.session_state["hr_aft_disch"]) + int(st.session_state["hr_poop_disch"])
    st.session_state["done_restow_load"]  += int(st.session_state["hr_rst_fwd_load"]) + int(st.session_state["hr_rst_mid_load"]) + int(st.session_state["hr_rst_aft_load"]) + int(st.session_state["hr_rst_poop_load"])
    st.session_state["done_restow_disch"] += int(st.session_state["hr_rst_fwd_disch"]) + int(st.session_state["hr_rst_mid_disch"]) + int(st.session_state["hr_rst_aft_disch"]) + int(st.session_state["hr_rst_poop_disch"])
    st.session_state["done_hatch_open"]  += int(st.session_state["hr_hat_fwd_open"]) + int(st.session_state["hr_hat_mid_open"]) + int(st.session_state["hr_hat_aft_open"])
    st.session_state["done_hatch_close"] += int(st.session_state["hr_hat_fwd_close"]) + int(st.session_state["hr_hat_mid_close"]) + int(st.session_state["hr_hat_aft_close"])

    # Append to history (optional record)
    st.session_state["history"].append({
        "date": st.session_state["report_date"],
        "hour": hourly_time,
        "fwd_load": int(st.session_state["hr_fwd_load"]),
        "mid_load": int(st.session_state["hr_mid_load"]),
        "aft_load": int(st.session_state["hr_aft_load"]),
        "poop_load": int(st.session_state["hr_poop_load"]),
        "fwd_disch": int(st.session_state["hr_fwd_disch"]),
        "mid_disch": int(st.session_state["hr_mid_disch"]),
        "aft_disch": int(st.session_state["hr_aft_disch"]),
        "poop_disch": int(st.session_state["hr_poop_disch"]),
        "rst_fwd_load": int(st.session_state["hr_rst_fwd_load"]),
        "rst_mid_load": int(st.session_state["hr_rst_mid_load"]),
        "rst_aft_load": int(st.session_state["hr_rst_aft_load"]),
        "rst_poop_load": int(st.session_state["hr_rst_poop_load"]),
        "rst_fwd_disch": int(st.session_state["hr_rst_fwd_disch"]),
        "rst_mid_disch": int(st.session_state["hr_rst_mid_disch"]),
        "rst_aft_disch": int(st.session_state["hr_rst_aft_disch"]),
        "rst_poop_disch": int(st.session_state["hr_rst_poop_disch"]),
        "hat_fwd_open": int(st.session_state["hr_hat_fwd_open"]),
        "hat_mid_open": int(st.session_state["hr_hat_mid_open"]),
        "hat_aft_open": int(st.session_state["hr_hat_aft_open"]),
        "hat_fwd_close": int(st.session_state["hr_hat_fwd_close"]),
        "hat_mid_close": int(st.session_state["hr_hat_mid_close"]),
        "hat_aft_close": int(st.session_state["hr_hat_aft_close"]),
        "idles": st.session_state["idle_entries"],
    })

    # Update 4-hour block counters
    add_to_block_store(hourly_time)

    # Save last hour & advance to next hour index automatically
    st.session_state["last_hour"] = hourly_time
    idx = hours_list.index(hourly_time)
    next_idx = (idx + 1) % len(hours_list)
    st.session_state["hour_idx"] = next_idx  # used to show next default on next open
    st.success(f"Hourly recorded. Next hour selected will be: {hours_list[next_idx]}")

    # Build & show template (monospace)
    txt = hourly_template_str(hourly_time)
    st.code(txt, language="text")

    # WhatsApp link
    wa_text = f"```{txt}```"
    if st.session_state["wa_number"]:
        wa_link = f"https://wa.me/{st.session_state['wa_number']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp to Private Number]({wa_link})", unsafe_allow_html=True)
    elif st.session_state["wa_group_link"]:
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_group_link']})", unsafe_allow_html=True)

    save_json()

# --- Handle Hourly Reset button: zero input fields only ---
if reset_hourly:
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_rst_fwd_load","hr_rst_mid_load","hr_rst_aft_load","hr_rst_poop_load",
        "hr_rst_fwd_disch","hr_rst_mid_disch","hr_rst_aft_disch","hr_rst_poop_disch",
        "hr_hat_fwd_open","hr_hat_mid_open","hr_hat_aft_open",
        "hr_hat_fwd_close","hr_hat_mid_close","hr_hat_aft_close"
    ]:
        st.session_state[k] = 0
    st.info("Hourly input fields reset.")
    save_json()
    # WhatsApp_Report.py  (Part 4/5)  -- append below Part 3

st.header("4-Hourly Report")

# Define the six 4h blocks
four_blocks = [
    "06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00",
    "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"
]
# Select block
st.session_state["four_block"] = st.selectbox("Select 4-Hour Block", options=four_blocks, index=four_blocks.index(st.session_state.get("four_block","06h00 - 10h00")), key="four_block_select")

# --- Show tracker (auto) for selected block ---
key_block = f"{st.session_state['report_date']}|{st.session_state['four_block']}"
auto_bs = st.session_state["block_store"].get(key_block, {
    "fwd_load":0,"mid_load":0,"aft_load":0,"poop_load":0,
    "fwd_disch":0,"mid_disch":0,"aft_disch":0,"poop_disch":0,
    "rst_fwd_load":0,"rst_mid_load":0,"rst_aft_load":0,"rst_poop_load":0,
    "rst_fwd_disch":0,"rst_mid_disch":0,"rst_aft_disch":0,"rst_poop_disch":0,
    "hat_fwd_open":0,"hat_mid_open":0,"hat_aft_open":0,
    "hat_fwd_close":0,"hat_mid_close":0,"hat_aft_close":0,
    "hours_count":0
})

with st.expander("📈 4-Hourly Tracker (auto totals)", expanded=True):
    st.caption(f"Counts accumulated for {st.session_state['four_block']} (hours recorded: {auto_bs.get('hours_count',0)})")
    # Crane Moves
    st.markdown("**Crane Moves (Totals over block)**")
    st.text(f"FWD  Load {auto_bs['fwd_load']:>5}   Disch {auto_bs['fwd_disch']:>5}")
    st.text(f"MID  Load {auto_bs['mid_load']:>5}   Disch {auto_bs['mid_disch']:>5}")
    st.text(f"AFT  Load {auto_bs['aft_load']:>5}   Disch {auto_bs['aft_disch']:>5}")
    st.text(f"POOP Load {auto_bs['poop_load']:>5}   Disch {auto_bs['poop_disch']:>5}")
    # Restows
    st.markdown("**Restows (Totals over block)**")
    st.text(f"FWD  Load {auto_bs['rst_fwd_load']:>5}   Disch {auto_bs['rst_fwd_disch']:>5}")
    st.text(f"MID  Load {auto_bs['rst_mid_load']:>5}   Disch {auto_bs['rst_mid_disch']:>5}")
    st.text(f"AFT  Load {auto_bs['rst_aft_load']:>5}   Disch {auto_bs['rst_aft_disch']:>5}")
    st.text(f"POOP Load {auto_bs['rst_poop_load']:>5}   Disch {auto_bs['rst_poop_disch']:>5}")
    # Hatch
    st.markdown("**Hatch Moves (Totals over block)**")
    st.text(f"FWD  Open {auto_bs['hat_fwd_open']:>5}   Close {auto_bs['hat_fwd_close']:>5}")
    st.text(f"MID  Open {auto_bs['hat_mid_open']:>5}   Close {auto_bs['hat_mid_close']:>5}")
    st.text(f"AFT  Open {auto_bs['hat_aft_open']:>5}   Close {auto_bs['hat_aft_close']:>5}")

# --- Manual override (same grouping) ---
with st.expander("✏️ Edit 4-Hourly Totals Manually (optional)", expanded=False):
    st.session_state["use_4h_manual"] = st.checkbox("Use manual values instead of auto tracker", value=bool(st.session_state["use_4h_manual"]), key="use_4h_manual_chk")

    o = st.session_state["ovr_4h"]
    with st.expander("Crane Moves ➜ Load", expanded=False):
        o["fwd_load"]  = st.number_input("FWD Load (4H)",  min_value=0, value=int(o["fwd_load"]),  key="ovr_fwd_load")
        o["mid_load"]  = st.number_input("MID Load (4H)",  min_value=0, value=int(o["mid_load"]),  key="ovr_mid_load")
        o["aft_load"]  = st.number_input("AFT Load (4H)",  min_value=0, value=int(o["aft_load"]),  key="ovr_aft_load")
        o["poop_load"] = st.number_input("POOP Load (4H)", min_value=0, value=int(o["poop_load"]), key="ovr_poop_load")
    with st.expander("Crane Moves ➜ Discharge", expanded=False):
        o["fwd_disch"]  = st.number_input("FWD Discharge (4H)",  min_value=0, value=int(o["fwd_disch"]),  key="ovr_fwd_disch")
        o["mid_disch"]  = st.number_input("MID Discharge (4H)",  min_value=0, value=int(o["mid_disch"]),  key="ovr_mid_disch")
        o["aft_disch"]  = st.number_input("AFT Discharge (4H)",  min_value=0, value=int(o["aft_disch"]),  key="ovr_aft_disch")
        o["poop_disch"] = st.number_input("POOP Discharge (4H)", min_value=0, value=int(o["poop_disch"]), key="ovr_poop_disch")

    with st.expander("Restows ➜ Load", expanded=False):
        o["rst_fwd_load"]  = st.number_input("FWD Restow Load (4H)",  min_value=0, value=int(o["rst_fwd_load"]),  key="ovr_rst_fwd_load")
        o["rst_mid_load"]  = st.number_input("MID Restow Load (4H)",  min_value=0, value=int(o["rst_mid_load"]),  key="ovr_rst_mid_load")
        o["rst_aft_load"]  = st.number_input("AFT Restow Load (4H)",  min_value=0, value=int(o["rst_aft_load"]),  key="ovr_rst_aft_load")
        o["rst_poop_load"] = st.number_input("POOP Restow Load (4H)", min_value=0, value=int(o["rst_poop_load"]), key="ovr_rst_poop_load")
    with st.expander("Restows ➜ Discharge", expanded=False):
        o["rst_fwd_disch"]  = st.number_input("FWD Restow Discharge (4H)",  min_value=0, value=int(o["rst_fwd_disch"]),  key="ovr_rst_fwd_disch")
        o["rst_mid_disch"]  = st.number_input("MID Restow Discharge (4H)",  min_value=0, value=int(o["rst_mid_disch"]),  key="ovr_rst_mid_disch")
        o["rst_aft_disch"]  = st.number_input("AFT Restow Discharge (4H)",  min_value=0, value=int(o["rst_aft_disch"]),  key="ovr_rst_aft_disch")
        o["rst_poop_disch"] = st.number_input("POOP Restow Discharge (4H)", min_value=0, value=int(o["rst_poop_disch"]), key="ovr_rst_poop_disch")

    with st.expander("Hatch Moves ➜ Open/Close", expanded=False):
        o["hat_fwd_open"]  = st.number_input("FWD Hatch Open (4H)",  min_value=0, value=int(o["hat_fwd_open"]),  key="ovr_hat_fwd_open")
        o["hat_mid_open"]  = st.number_input("MID Hatch Open (4H)",  min_value=0, value=int(o["hat_mid_open"]),  key="ovr_hat_mid_open")
        o["hat_aft_open"]  = st.number_input("AFT Hatch Open (4H)",  min_value=0, value=int(o["hat_aft_open"]),  key="ovr_hat_aft_open")
        o["hat_fwd_close"] = st.number_input("FWD Hatch Close (4H)", min_value=0, value=int(o["hat_fwd_close"]), key="ovr_hat_fwd_close")
        o["hat_mid_close"] = st.number_input("MID Hatch Close (4H)", min_value=0, value=int(o["hat_mid_close"]), key="ovr_hat_mid_close")
        o["hat_aft_close"] = st.number_input("AFT Hatch Close (4H)", min_value=0, value=int(o["hat_aft_close"]), key="ovr_hat_aft_close")

st.session_state["ovr_4h"] = o
save_json()

# Use auto tracker or manual
def current_4h_values():
    if st.session_state["use_4h_manual"]:
        return st.session_state["ovr_4h"]
    return auto_bs

def four_hour_template_str():
    v = st.session_state
    x = current_4h_values()
    remL, remD, remRL, remRD = compute_remaining()
    L = "_________________________"
    # Same structure as hourly, but with Date & 4-hour block line
    t = f"""\
{v['vessel_name']}
Berthed {v['berthed_date']}

Date: {v['report_date']}
4-Hour Block: {v['four_block']}
{L}
   *HOURLY MOVES*
{L}
*Crane Moves*
           Load   Discharge
FWD       {int(x['fwd_load']):>5}     {int(x['fwd_disch']):>5}
MID       {int(x['mid_load']):>5}     {int(x['mid_disch']):>5}
AFT       {int(x['aft_load']):>5}     {int(x['aft_disch']):>5}
POOP      {int(x['poop_load']):>5}     {int(x['poop_disch']):>5}
{L}
*Restows*
           Load   Discharge
FWD       {int(x['rst_fwd_load']):>5}     {int(x['rst_fwd_disch']):>5}
MID       {int(x['rst_mid_load']):>5}     {int(x['rst_mid_disch']):>5}
AFT       {int(x['rst_aft_load']):>5}     {int(x['rst_aft_disch']):>5}
POOP      {int(x['rst_poop_load']):>5}     {int(x['rst_poop_disch']):>5}
{L}
      *CUMULATIVE*
{L}
           Load   Disch
Plan       {int(v['planned_load']):>5}      {int(v['planned_disch']):>5}
Done       {int(v['done_load']):>5}      {int(v['done_disch']):>5}
Remain     {int(remL):>5}      {int(remD):>5}
{L}
*Restows*
           Load   Disch
Plan       {int(v['planned_restow_load']):>5}      {int(v['planned_restow_disch']):>5}
Done       {int(v['done_restow_load']):>5}      {int(v['done_restow_disch']):>5}
Remain     {int(remRL):>5}      {int(remRD):>5}
{L}
*Hatch Moves*
           Open   Close
FWD       {int(x['hat_fwd_open']):>5}      {int(x['hat_fwd_close']):>5}
MID       {int(x['hat_mid_open']):>5}      {int(x['hat_mid_close']):>5}
AFT       {int(x['hat_aft_open']):>5}      {int(x['hat_aft_close']):>5}
{L}
*Gear boxes* 

{L}
*Idle*
"""
    # Use the same idle entries as current hourly list (you can change to a separate 4h idle if desired)
    for i, idle in enumerate(v["idle_entries"], start=1):
        if idle.get("crane") or idle.get("start") or idle.get("end") or idle.get("delay"):
            t += f"{i}. {idle.get('crane','')} {idle.get('start','')}-{idle.get('end','')} : {idle.get('delay','')}\n"
    return t

# Show preview + send controls
four_txt = four_hour_template_str()
st.code(four_txt, language="text")

c4, c5 = st.columns([1,1])
with c4:
    send_4h = st.button("✅ Send 4-Hourly Template")
with c5:
    reset_block = st.button("♻️ Reset Current 4-Hour Counters")

if send_4h:
    wa_text_4h = f"```{four_txt}```"
    if st.session_state["wa_number"]:
        wa_link4 = f"https://wa.me/{st.session_state['wa_number']}?text={urllib.parse.quote(wa_text_4h)}"
        st.markdown(f"[Open WhatsApp (4H, Private)]({wa_link4})", unsafe_allow_html=True)
    elif st.session_state["wa_group_link"]:
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_group_link']})", unsafe_allow_html=True)

if reset_block:
    st.warning("4-Hour counters cleared for selected block (does not affect cumulative DONE).")
    # Zero the auto counters and hour count for this block key
    st.session_state["block_store"][key_block] = {
        "fwd_load":0,"mid_load":0,"aft_load":0,"poop_load":0,
        "fwd_disch":0,"mid_disch":0,"aft_disch":0,"poop_disch":0,
        "rst_fwd_load":0,"rst_mid_load":0,"rst_aft_load":0,"rst_poop_load":0,
        "rst_fwd_disch":0,"rst_mid_disch":0,"rst_aft_disch":0,"rst_poop_disch":0,
        "hat_fwd_open":0,"hat_mid_open":0,"hat_aft_open":0,
        "hat_fwd_close":0,"hat_mid_close":0,"hat_aft_close":0,
        "hours_count":0
    }
    save_json()
    # WhatsApp_Report.py  (Part 5/5)  -- append below Part 4

# Simple live remaining preview (not in template) to help operators
with st.expander("🔎 Live Remaining Preview", expanded=False):
    rL, rD, rRL, rRD = compute_remaining()
    st.text(f"Load  Remaining: {rL}")
    st.text(f"Disch Remaining: {rD}")
    st.text(f"Restow Load  Remaining: {rRL}")
    st.text(f"Restow Disch Remaining: {rRD}")

# Final save
save_json()