# WhatsApp_Report.py — PART 1 / 5

import streamlit as st
import sqlite3
import json
import urllib.parse
from datetime import datetime, timedelta
import pytz
import os
import sys

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE
# --------------------------
DB_FILE = "vessel_data.db"
TZ = pytz.timezone("Africa/Johannesburg")

# --------------------------
# INIT DATABASE
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    conn.commit()

    # Ensure cumulative always exists
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    if not row:
        cumulative = {
            "done_load": 0,
            "done_disch": 0,
            "done_restow_load": 0,
            "done_restow_disch": 0,
            "hatch_fwd_open": 0,
            "hatch_fwd_close": 0,
            "hatch_mid_open": 0,
            "hatch_mid_close": 0,
            "hatch_aft_open": 0,
            "hatch_aft_close": 0,
            "gearbox": 0,
        }
        cur.execute(
            "INSERT INTO meta (key, value) VALUES ('cumulative', ?);",
            (json.dumps(cumulative),),
        )
    conn.commit()
    conn.close()


def load_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='cumulative';")
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}


def save_db(cumulative):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO meta (key, value) VALUES ('cumulative', ?);",
        (json.dumps(cumulative),),
    )
    conn.commit()
    conn.close()


# --------------------------
# SESSION STATE INIT
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


cumulative = load_db()

init_key("vessel_name", "NILA")
init_key("berthed_date", "")
init_key("report_date", datetime.now(TZ))
init_key("hourly_time", "06:00–07:00")
init_key("fourh_block", "00:00–04:00")

# restored keys for First / Last lift
init_key("first_lift", "")
init_key("last_lift", "")

# opening balances
init_key("opening_load", 0)
init_key("opening_disch", 0)
init_key("opening_restow_load", 0)
init_key("opening_restow_disch", 0)

# planned totals
init_key("planned_load", 0)
init_key("planned_disch", 0)
init_key("planned_restow_load", 0)
init_key("planned_restow_disch", 0)

# hourly moves
init_key("hr_fwd_load", 0)
init_key("hr_mid_load", 0)
init_key("hr_aft_load", 0)
init_key("hr_poop_load", 0)

init_key("hr_fwd_disch", 0)
init_key("hr_mid_disch", 0)
init_key("hr_aft_disch", 0)
init_key("hr_poop_disch", 0)

init_key("hr_fwd_restow_load", 0)
init_key("hr_mid_restow_load", 0)
init_key("hr_aft_restow_load", 0)
init_key("hr_poop_restow_load", 0)

init_key("hr_fwd_restow_disch", 0)
init_key("hr_mid_restow_disch", 0)
init_key("hr_aft_restow_disch", 0)
init_key("hr_poop_restow_disch", 0)

init_key("hr_hatch_fwd_open", 0)
init_key("hr_hatch_fwd_close", 0)
init_key("hr_hatch_mid_open", 0)
init_key("hr_hatch_mid_close", 0)
init_key("hr_hatch_aft_open", 0)
init_key("hr_hatch_aft_close", 0)

init_key("gearbox", 0)
init_key("idle_entries", [])
init_key("fourh_manual_override", False)
# WhatsApp_Report.py — PART 2 / 5

st.title("📝 Vessel Report Tracker")

with st.expander("⚓ Vessel Details", expanded=True):
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.date_input("Report Date", key="report_date")

with st.expander("🏗️ Crane Moves"):
    # Restored First & Last Lift at original location
    st.text_input("First Lift (e.g., 06h05)", key="first_lift")
    st.text_input("Last Lift (e.g., 06h58)", key="last_lift")

    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, key="hr_poop_load")

    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch")

    with st.expander("🔄 Restows - Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")

    with st.expander("🔄 Restows - Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch")

with st.expander("🛠️ Gearboxes"):
    st.number_input("Total Gearboxes This Hour", min_value=0, key="gearbox")

with st.expander("📊 Opening & Planned Totals"):
    st.number_input("Opening Load", min_value=0, key="opening_load")
    st.number_input("Opening Discharge", min_value=0, key="opening_disch")
    st.number_input("Opening Restow Load", min_value=0, key="opening_restow_load")
    st.number_input("Opening Restow Discharge", min_value=0, key="opening_restow_disch")

    st.number_input("Planned Load", min_value=0, key="planned_load")
    st.number_input("Planned Discharge", min_value=0, key="planned_disch")
    st.number_input("Planned Restow Load", min_value=0, key="planned_restow_load")
    st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch")
    # WhatsApp_Report.py — PART 3 / 5

with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

st.subheader("⏸️ Idle / Delays")
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

with st.expander("🛑 Idle Entries", expanded=False):
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries")
    entries = []
    for i in range(st.session_state["num_idle_entries"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30")
        end = c3.text_input(f"End {i+1}", key=f"idle_end_{i}", placeholder="e.g., 12h40")
        sel = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}")
        entries.append(
            {
                "crane": (crane or "").strip(),
                "start": (start or "").strip(),
                "end": (end or "").strip(),
                "delay": (custom or "").strip() if (custom or "").strip() else sel,
            }
        )
    st.session_state["idle_entries"] = entries


# --------------------------
# FUNCTIONS
# --------------------------
def hour_range_list():
    return [
        f"{h:02d}:00–{(h+1)%24:02d}:00"
        for h in range(24)
    ]


def four_hour_blocks():
    return [
        "00:00–04:00",
        "04:00–08:00",
        "08:00–12:00",
        "12:00–16:00",
        "16:00–20:00",
        "20:00–24:00",
    ]


def reset_hourly_inputs():
    keys = [
        "hr_fwd_load", "hr_mid_load", "hr_aft_load", "hr_poop_load",
        "hr_fwd_disch", "hr_mid_disch", "hr_aft_disch", "hr_poop_disch",
        "hr_fwd_restow_load", "hr_mid_restow_load", "hr_aft_restow_load", "hr_poop_restow_load",
        "hr_fwd_restow_disch", "hr_mid_restow_disch", "hr_aft_restow_disch", "hr_poop_restow_disch",
        "hr_hatch_fwd_open", "hr_hatch_fwd_close", "hr_hatch_mid_open", "hr_hatch_mid_close",
        "hr_hatch_aft_open", "hr_hatch_aft_close",
        "gearbox",
    ]
    for k in keys:
        st.session_state[k] = 0
    st.session_state["idle_entries"] = []


def reset_4h_tracker():
    keys = [
        "fourh_manual_override",
        "m4h_fwd_load", "m4h_mid_load", "m4h_aft_load", "m4h_poop_load",
        "m4h_fwd_disch", "m4h_mid_disch", "m4h_aft_disch", "m4h_poop_disch",
        "m4h_fwd_restow_load", "m4h_mid_restow_load", "m4h_aft_restow_load", "m4h_poop_restow_load",
        "m4h_fwd_restow_disch", "m4h_mid_restow_disch", "m4h_aft_restow_disch", "m4h_poop_restow_disch",
        "m4h_hatch_fwd_open", "m4h_hatch_mid_open", "m4h_hatch_aft_open",
        "m4h_hatch_fwd_close", "m4h_hatch_mid_close", "m4h_hatch_aft_close",
    ]
    for k in keys:
        if k in st.session_state:
            st.session_state[k] = 0
            # WhatsApp_Report.py — PART 4 / 5

def reset_master():
    reset_hourly_inputs()
    reset_4h_tracker()
    for k in [
        "vessel_name", "berthed_date", "planned_load", "planned_disch",
        "planned_restow_load", "planned_restow_disch",
        "opening_load", "opening_disch",
        "opening_restow_load", "opening_restow_disch",
        "first_lift", "last_lift",
    ]:
        st.session_state[k] = "" if isinstance(st.session_state.get(k), str) else 0
    st.session_state["cumulative"] = {
        "done_load": 0, "done_disch": 0,
        "done_restow_load": 0, "done_restow_disch": 0,
        "done_hatch_open": 0, "done_hatch_close": 0,
        "gearbox": 0,
        "last_hour": None,
    }
    save_db(st.session_state["cumulative"])


def add_current_hour_to_4h():
    block = st.session_state["fourh_block"]
    hr_vals = {
        "fwd_load": st.session_state["hr_fwd_load"],
        "mid_load": st.session_state["hr_mid_load"],
        "aft_load": st.session_state["hr_aft_load"],
        "poop_load": st.session_state["hr_poop_load"],
        "fwd_disch": st.session_state["hr_fwd_disch"],
        "mid_disch": st.session_state["hr_mid_disch"],
        "aft_disch": st.session_state["hr_aft_disch"],
        "poop_disch": st.session_state["hr_poop_disch"],
        "fwd_restow_load": st.session_state["hr_fwd_restow_load"],
        "mid_restow_load": st.session_state["hr_mid_restow_load"],
        "aft_restow_load": st.session_state["hr_aft_restow_load"],
        "poop_restow_load": st.session_state["hr_poop_restow_load"],
        "fwd_restow_disch": st.session_state["hr_fwd_restow_disch"],
        "mid_restow_disch": st.session_state["hr_mid_restow_disch"],
        "aft_restow_disch": st.session_state["hr_aft_restow_disch"],
        "poop_restow_disch": st.session_state["hr_poop_restow_disch"],
        "hatch_fwd_open": st.session_state["hr_hatch_fwd_open"],
        "hatch_mid_open": st.session_state["hr_hatch_mid_open"],
        "hatch_aft_open": st.session_state["hr_hatch_aft_open"],
        "hatch_fwd_close": st.session_state["hr_hatch_fwd_close"],
        "hatch_mid_close": st.session_state["hr_hatch_mid_close"],
        "hatch_aft_close": st.session_state["hr_hatch_aft_close"],
        "gearbox": st.session_state["gearbox"],
    }

    for k, v in hr_vals.items():
        st.session_state["fourh"][k].append(v)


def sum_list(lst):
    return sum(lst) if isinstance(lst, list) else 0


def generate_hourly_template():
    cumulative = st.session_state["cumulative"]

    remaining_load = st.session_state["planned_load"] - cumulative["done_load"] - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load = st.session_state["planned_restow_load"] - cumulative["done_restow_load"] - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
Hour: {st.session_state['hourly_time']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD       {st.session_state['hr_fwd_load']:>5}     {st.session_state['hr_fwd_disch']:>5}
MID       {st.session_state['hr_mid_load']:>5}     {st.session_state['hr_mid_disch']:>5}
AFT       {st.session_state['hr_aft_load']:>5}     {st.session_state['hr_aft_disch']:>5}
POOP      {st.session_state['hr_poop_load']:>5}     {st.session_state['hr_poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {st.session_state['hr_fwd_restow_load']:>5}     {st.session_state['hr_fwd_restow_disch']:>5}
MID       {st.session_state['hr_mid_restow_load']:>5}     {st.session_state['hr_mid_restow_disch']:>5}
AFT       {st.session_state['hr_aft_restow_load']:>5}     {st.session_state['hr_aft_restow_disch']:>5}
POOP      {st.session_state['hr_poop_restow_load']:>5}     {st.session_state['hr_poop_restow_disch']:>5}
_________________________
*Gearbox*
Total     {st.session_state['gearbox']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl
    # WhatsApp_Report.py — PART 5 / 5

def on_generate_hourly():
    cumulative = st.session_state["cumulative"]

    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]
    hour_gearbox = st.session_state["gearbox"]

    # Add opening balances once
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_restow_load)
    cumulative["done_restow_disch"] += int(hour_restow_disch)
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)
    cumulative["gearbox"] = int(hour_gearbox)

    # Adjust plan totals so Remain never negative
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]

    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "planned_load": st.session_state["planned_load"],
        "planned_disch": st.session_state["planned_disch"],
        "planned_restow_load": st.session_state["planned_restow_load"],
        "planned_restow_disch": st.session_state["planned_restow_disch"],
        "opening_load": st.session_state["opening_load"],
        "opening_disch": st.session_state["opening_disch"],
        "opening_restow_load": st.session_state["opening_restow_load"],
        "opening_restow_disch": st.session_state["opening_restow_disch"],
        "first_lift": st.session_state["first_lift"],
        "last_lift": st.session_state["last_lift"],
        "last_hour": st.session_state["hourly_time"],
    })

    save_db(cumulative)
    add_current_hour_to_4h()
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
    return generate_hourly_template()


col1, col2 = st.columns([1,1])
with col1:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        txt = on_generate_hourly()
        st.code(txt, language="text")
with col2:
    if st.button("📤 Open WhatsApp (Hourly)"):
        txt = on_generate_hourly()
        wa_text = f"```{txt}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")


st.button("🔄 Reset Hourly Inputs", on_click=reset_hourly_inputs)
st.button("🔄 Reset 4-Hourly Tracker", on_click=reset_4h_tracker)
st.button("⚠️ Master Reset (Everything)", on_click=reset_master)

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Gearbox: Hourly only, resets after generation. "
    "• Resets: Use Hourly/4H reset or Master Reset to clear all data. "
)
