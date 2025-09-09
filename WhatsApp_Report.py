import streamlit as st
import sqlite3
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz
import json

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# --------------------------
# DATABASE SETUP
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vessel_state (
        id INTEGER PRIMARY KEY,
        vessel_name TEXT,
        berthed_date TEXT,
        first_lift TEXT,
        last_lift TEXT,
        planned_load INTEGER,
        planned_disch INTEGER,
        planned_restow_load INTEGER,
        planned_restow_disch INTEGER,
        opening_load INTEGER,
        opening_disch INTEGER,
        opening_restow_load INTEGER,
        opening_restow_disch INTEGER,
        done_load INTEGER,
        done_disch INTEGER,
        done_restow_load INTEGER,
        done_restow_disch INTEGER,
        done_hatch_open INTEGER,
        done_hatch_close INTEGER,
        last_hour TEXT
    )
    """)
    conn.commit()
    return conn

def load_state(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM vessel_state WHERE id=1")
    row = cur.fetchone()
    if row:
        return dict(zip([c[0] for c in cur.description], row))
    else:
        defaults = {
            "id": 1,
            "vessel_name": "MSC NILA",
            "berthed_date": "14/08/2025 @ 10h55",
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
            "last_hour": "06h00 - 07h00",
        }
        cur.execute("""INSERT INTO vessel_state (
            id,vessel_name,berthed_date,first_lift,last_lift,
            planned_load,planned_disch,planned_restow_load,planned_restow_disch,
            opening_load,opening_disch,opening_restow_load,opening_restow_disch,
            done_load,done_disch,done_restow_load,done_restow_disch,
            done_hatch_open,done_hatch_close,last_hour
        ) VALUES (
            :id,:vessel_name,:berthed_date,:first_lift,:last_lift,
            :planned_load,:planned_disch,:planned_restow_load,:planned_restow_disch,
            :opening_load,:opening_disch,:opening_restow_load,:opening_restow_disch,
            :done_load,:done_disch,:done_restow_load,:done_restow_disch,
            :done_hatch_open,:done_hatch_close,:last_hour
        )""", defaults)
        conn.commit()
        return defaults

def save_state(conn, state):
    cur = conn.cursor()
    cur.execute("""UPDATE vessel_state SET
        vessel_name=:vessel_name, berthed_date=:berthed_date,
        first_lift=:first_lift, last_lift=:last_lift,
        planned_load=:planned_load, planned_disch=:planned_disch,
        planned_restow_load=:planned_restow_load, planned_restow_disch=:planned_restow_disch,
        opening_load=:opening_load, opening_disch=:opening_disch,
        opening_restow_load=:opening_restow_load, opening_restow_disch=:opening_restow_disch,
        done_load=:done_load, done_disch=:done_disch,
        done_restow_load=:done_restow_load, done_restow_disch=:done_restow_disch,
        done_hatch_open=:done_hatch_open, done_hatch_close=:done_hatch_close,
        last_hour=:last_hour
        WHERE id=1
    """, state)
    conn.commit()

# --------------------------
# HOUR HELPERS
# --------------------------
def hour_range_list():
    return [f"{h:02d}h00 - {(h+1)%24:02d}h00" for h in range(24)]

def next_hour_label(current_label: str):
    hours = hour_range_list()
    if current_label in hours:
        idx = hours.index(current_label)
    else:
        idx = 0
    return hours[(idx + 1) % len(hours)]

def four_hour_blocks():
    return [
        "06h00 - 10h00",
        "10h00 - 14h00",
        "14h00 - 18h00",
        "18h00 - 22h00",
        "22h00 - 02h00",
        "02h00 - 06h00",
    ]
    # --------------------------
# APP START & LOAD PERSISTED STATE
# --------------------------
conn = init_db()
persisted = load_state(conn)

# helper to set session_state only when missing (safe during render)
def set_if_missing(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

# persist core values (these survive across devices because we save to sqlite)
set_if_missing("vessel_name", persisted["vessel_name"])
set_if_missing("berthed_date", persisted["berthed_date"])
set_if_missing("first_lift", persisted["first_lift"])
set_if_missing("last_lift", persisted["last_lift"])

set_if_missing("planned_load", int(persisted["planned_load"]))
set_if_missing("planned_disch", int(persisted["planned_disch"]))
set_if_missing("planned_restow_load", int(persisted["planned_restow_load"]))
set_if_missing("planned_restow_disch", int(persisted["planned_restow_disch"]))

set_if_missing("opening_load", int(persisted["opening_load"]))
set_if_missing("opening_disch", int(persisted["opening_disch"]))
set_if_missing("opening_restow_load", int(persisted["opening_restow_load"]))
set_if_missing("opening_restow_disch", int(persisted["opening_restow_disch"]))

set_if_missing("done_load", int(persisted["done_load"]))
set_if_missing("done_disch", int(persisted["done_disch"]))
set_if_missing("done_restow_load", int(persisted["done_restow_load"]))
set_if_missing("done_restow_disch", int(persisted["done_restow_disch"]))
set_if_missing("done_hatch_open", int(persisted["done_hatch_open"]))
set_if_missing("done_hatch_close", int(persisted["done_hatch_close"]))

set_if_missing("last_hour", persisted["last_hour"])

# hourly working inputs (these are transient but we keep in session_state while working)
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "gearbox_total_hour"
]:
    set_if_missing(k, 0)

# hourly meta / UI state
set_if_missing("report_date", datetime.now(TZ).date())
set_if_missing("hourly_time", persisted.get("last_hour", hour_range_list()[0]))
set_if_missing("hourly_time_override", None)

# 4-hour tracker (already init in part1: fourh is present in session_state)
# ensure key exists (when running freshly)
if "fourh" not in st.session_state:
    st.session_state["fourh"] = {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
    }

# idle entries
set_if_missing("num_idle_entries", 0)
set_if_missing("idle_entries", [])

# 4-hour manual fields already initialized in part1; ensure exist
for k in [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
]:
    set_if_missing(k, 0)

set_if_missing("fourh_block", four_hour_blocks()[0])
set_if_missing("fourh_manual_override", False)

# --------------------------
# UI: Vessel / Date / Plan Inputs (NO structural changes)
# --------------------------
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # these write back to session_state automatically
    st.text_input("Vessel Name", value=st.session_state["vessel_name"], key="vessel_name")
    st.text_input("Berthed Date", value=st.session_state["berthed_date"], key="berthed_date")
    st.text_input("First Lift (e.g., 06h05)", value=st.session_state.get("first_lift",""), key="first_lift")
    st.text_input("Last Lift (e.g., 07h05)", value=st.session_state.get("last_lift",""), key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", value=st.session_state["report_date"], key="report_date")

# persist vessel meta to DB when changed (save button)
def persist_meta():
    state = {
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "first_lift": st.session_state.get("first_lift",""),
        "last_lift": st.session_state.get("last_lift",""),
        "planned_load": st.session_state["planned_load"],
        "planned_disch": st.session_state["planned_disch"],
        "planned_restow_load": st.session_state["planned_restow_load"],
        "planned_restow_disch": st.session_state["planned_restow_disch"],
        "opening_load": st.session_state["opening_load"],
        "opening_disch": st.session_state["opening_disch"],
        "opening_restow_load": st.session_state["opening_restow_load"],
        "opening_restow_disch": st.session_state["opening_restow_disch"],
        "done_load": st.session_state["done_load"],
        "done_disch": st.session_state["done_disch"],
        "done_restow_load": st.session_state["done_restow_load"],
        "done_restow_disch": st.session_state["done_restow_disch"],
        "done_hatch_open": st.session_state["done_hatch_open"],
        "done_hatch_close": st.session_state["done_hatch_close"],
        "last_hour": st.session_state.get("last_hour", hour_range_list()[0])
    }
    save_state(conn, state)
    st.success("Vessel meta saved to database (persists across devices).")

st.button("💾 Save Vessel & Plan Info (persist)", on_click=persist_meta)

# --------------------------
# Plan Totals & Opening Balance (Internal Only)
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load", min_value=0, value=st.session_state["planned_load"], key="planned_load")
        st.number_input("Planned Discharge", min_value=0, value=st.session_state["planned_disch"], key="planned_disch")
        st.number_input("Planned Restow Load", min_value=0, value=st.session_state["planned_restow_load"], key="planned_restow_load")
        st.number_input("Planned Restow Discharge", min_value=0, value=st.session_state["planned_restow_disch"], key="planned_restow_disch")
    with c2:
        st.number_input("Opening Load (Deduction)", min_value=0, value=st.session_state["opening_load"], key="opening_load")
        st.number_input("Opening Discharge (Deduction)", min_value=0, value=st.session_state["opening_disch"], key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)", min_value=0, value=st.session_state["opening_restow_load"], key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, value=st.session_state["opening_restow_disch"], key="opening_restow_disch")

# --------------------------
# Hour selector (24h) + safe override handoff
# --------------------------
# Apply pending hour override if exists (set in generate or reset callbacks)
if st.session_state.get("hourly_time_override"):
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    st.session_state["hourly_time_override"] = None

if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = persisted.get("last_hour", hour_range_list()[0])

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge) — keep collapsible structure EXACT as requested
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, value=st.session_state["hr_fwd_load"], key="hr_fwd_load")
        st.number_input("MID Load", min_value=0, value=st.session_state["hr_mid_load"], key="hr_mid_load")
        st.number_input("AFT Load", min_value=0, value=st.session_state["hr_aft_load"], key="hr_aft_load")
        st.number_input("POOP Load", min_value=0, value=st.session_state["hr_poop_load"], key="hr_poop_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, value=st.session_state["hr_fwd_disch"], key="hr_fwd_disch")
        st.number_input("MID Discharge", min_value=0, value=st.session_state["hr_mid_disch"], key="hr_mid_disch")
        st.number_input("AFT Discharge", min_value=0, value=st.session_state["hr_aft_disch"], key="hr_aft_disch")
        st.number_input("POOP Discharge", min_value=0, value=st.session_state["hr_poop_disch"], key="hr_poop_disch")

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, value=st.session_state["hr_fwd_restow_load"], key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, value=st.session_state["hr_mid_restow_load"], key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, value=st.session_state["hr_aft_restow_load"], key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, value=st.session_state["hr_poop_restow_load"], key="hr_poop_restow_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, value=st.session_state["hr_fwd_restow_disch"], key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, value=st.session_state["hr_mid_restow_disch"], key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, value=st.session_state["hr_aft_restow_disch"], key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, value=st.session_state["hr_poop_restow_disch"], key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, value=st.session_state["hr_hatch_fwd_open"], key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, value=st.session_state["hr_hatch_mid_open"], key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, value=st.session_state["hr_hatch_aft_open"], key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, value=st.session_state["hr_hatch_fwd_close"], key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, value=st.session_state["hr_hatch_mid_close"], key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, value=st.session_state["hr_hatch_aft_close"], key="hr_hatch_aft_close")

# --------------------------
# Gearbox (hourly single total, not cumulative)
# --------------------------
with st.expander("⚙️ Gearbox (Hourly)"):
    st.number_input("Total Gearboxes moved this hour", min_value=0, value=st.session_state["gearbox_total_hour"], key="gearbox_total_hour")
    st.caption("Note: gearbox total is only for the current hour and does not accumulate across hours.")

# --------------------------
# Idle / Delays
# --------------------------
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
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30")
        end   = c3.text_input(f"End {i+1}",   key=f"idle_end_{i}",   placeholder="e.g., 12h40")
        sel   = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}")
        entries.append({
            "crane": (crane or "").strip(),
            "start": (start or "").strip(),
            "end": (end or "").strip(),
            "delay": (custom or "").strip() if (custom or "").strip() else sel
        })
    # store non-widget data safely
    st.session_state["idle_entries"] = entries
    # --------------------------
# Hourly Totals Tracker (split by position)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": ss["hr_fwd_load"], "MID": ss["hr_mid_load"], "AFT": ss["hr_aft_load"], "POOP": ss["hr_poop_load"]},
        "disch":      {"FWD": ss["hr_fwd_disch"], "MID": ss["hr_mid_disch"], "AFT": ss["hr_aft_disch"], "POOP": ss["hr_poop_disch"]},
        "restow_load":{"FWD": ss["hr_fwd_restow_load"], "MID": ss["hr_mid_restow_load"], "AFT": ss["hr_aft_restow_load"], "POOP": ss["hr_poop_restow_load"]},
        "restow_disch":{"FWD": ss["hr_fwd_restow_disch"], "MID": ss["hr_mid_restow_disch"], "AFT": ss["hr_aft_restow_disch"], "POOP": ss["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": ss["hr_hatch_fwd_open"], "MID": ss["hr_hatch_mid_open"], "AFT": ss["hr_hatch_aft_open"]},
        "hatch_close":{"FWD": ss["hr_hatch_fwd_close"], "MID": ss["hr_hatch_mid_close"], "AFT": ss["hr_hatch_aft_close"]},
        "gearbox": ss["gearbox_total_hour"]
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearboxes (this hour):** {split['gearbox']}")

# --------------------------
# Generate Hourly Template
# --------------------------
def generate_hourly_template():
    # effective done includes opening balances
    done_load  = st.session_state["done_load"]  + st.session_state["opening_load"]
    done_disch = st.session_state["done_disch"] + st.session_state["opening_disch"]
    done_restow_load  = st.session_state["done_restow_load"]  + st.session_state["opening_restow_load"]
    done_restow_disch = st.session_state["done_restow_disch"] + st.session_state["opening_restow_disch"]

    # adjust plan dynamically if done > plan
    if done_load > st.session_state["planned_load"]:
        st.session_state["planned_load"] = done_load
    if done_disch > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = done_disch
    if done_restow_load > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = done_restow_load
    if done_restow_disch > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = done_restow_disch

    remaining_load  = st.session_state["planned_load"]  - done_load
    remaining_disch = st.session_state["planned_disch"] - done_disch
    remaining_restow_load  = st.session_state["planned_restow_load"]  - done_restow_load
    remaining_restow_disch = st.session_state["planned_restow_disch"] - done_restow_disch

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift: {st.session_state.get('first_lift','')}
Last Lift: {st.session_state.get('last_lift','')}

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
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearboxes*
Total     {st.session_state['gearbox_total_hour']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {done_load:>5}      {done_disch:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {done_restow_load:>5}      {done_restow_disch:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# On Generate Hourly
# --------------------------
def on_generate_hourly():
    # sum for this hour
    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # update cumulative done (without opening, since opening is handled in display)
    st.session_state["done_load"] += int(hour_load)
    st.session_state["done_disch"] += int(hour_disch)
    st.session_state["done_restow_load"] += int(hour_restow_load)
    st.session_state["done_restow_disch"] += int(hour_restow_disch)
    st.session_state["done_hatch_open"] += int(hour_hatch_open)
    st.session_state["done_hatch_close"] += int(hour_hatch_close)

    # push into 4h tracker
    tr = st.session_state["fourh"]
    tr["fwd_load"].append(st.session_state["hr_fwd_load"])
    tr["mid_load"].append(st.session_state["hr_mid_load"])
    tr["aft_load"].append(st.session_state["hr_aft_load"])
    tr["poop_load"].append(st.session_state["hr_poop_load"])
    tr["fwd_disch"].append(st.session_state["hr_fwd_disch"])
    tr["mid_disch"].append(st.session_state["hr_mid_disch"])
    tr["aft_disch"].append(st.session_state["hr_aft_disch"])
    tr["poop_disch"].append(st.session_state["hr_poop_disch"])
    tr["fwd_restow_load"].append(st.session_state["hr_fwd_restow_load"])
    tr["mid_restow_load"].append(st.session_state["hr_mid_restow_load"])
    tr["aft_restow_load"].append(st.session_state["hr_aft_restow_load"])
    tr["poop_restow_load"].append(st.session_state["hr_poop_restow_load"])
    tr["fwd_restow_disch"].append(st.session_state["hr_fwd_restow_disch"])
    tr["mid_restow_disch"].append(st.session_state["hr_mid_restow_disch"])
    tr["aft_restow_disch"].append(st.session_state["hr_aft_restow_disch"])
    tr["poop_restow_disch"].append(st.session_state["hr_poop_restow_disch"])
    tr["hatch_fwd_open"].append(st.session_state["hr_hatch_fwd_open"])
    tr["hatch_mid_open"].append(st.session_state["hr_hatch_mid_open"])
    tr["hatch_aft_open"].append(st.session_state["hr_hatch_aft_open"])
    tr["hatch_fwd_close"].append(st.session_state["hr_hatch_fwd_close"])
    tr["hatch_mid_close"].append(st.session_state["hr_hatch_mid_close"])
    tr["hatch_aft_close"].append(st.session_state["hr_hatch_aft_close"])
    tr["count_hours"] = min(4, tr["count_hours"] + 1)
    # trim to last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]

    # persist updated state
    persist_meta()

    # auto-advance hour
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
    # --------------------------
# Persistence Helpers (JSON + SQLite)
# --------------------------
import sqlite3
from typing import Dict, Any

DB_FILE = "vessel_report.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        json TEXT
    );
    """)
    # ensure single-row exists
    cur.execute("SELECT COUNT(*) FROM meta;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (json.dumps(cumulative),))
    conn.commit()
    conn.close()

def load_from_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {}
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return {}
    return {}

def save_to_db(data: Dict[str, Any]):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (json.dumps(data),))
    conn.commit()
    conn.close()

def persist_meta():
    """
    Persist cumulative/meta to both JSON file (for backup) and sqlite DB (primary).
    Also keep st.session_state consistent for cross-device reopen when URL is used.
    """
    # ensure no negatives / enforce types
    for k in ["done_load","done_disch","done_restow_load","done_restow_disch","done_hatch_open","done_hatch_close"]:
        cumulative[k] = int(max(0, cumulative.get(k, 0)))
    # write JSON backup
    save_cumulative(cumulative)
    # write sqlite
    try:
        save_to_db(cumulative)
    except Exception as e:
        # don't fail the app; show an info message
        st.warning(f"Warning: couldn't save to DB: {e}")

# If DB exists, load and override cumulative loaded from JSON so last-saved DB wins
init_db()
db_data = load_from_db()
if db_data:
    # Prefer DB-stored fields; only replace keys present in db_data
    cumulative.update(db_data)

# Synchronize session_state with cumulative (only meta keys)
meta_keys = [
    "vessel_name","berthed_date","planned_load","planned_disch",
    "planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch",
    "last_hour"
]
for k in meta_keys:
    # Only set session_state if the key exists in cumulative (safe)
    if k in cumulative:
        st.session_state[k] = cumulative[k]

# --------------------------
# UI Buttons: Generate (single) / WhatsApp / Reset / Master Reset
# --------------------------
colA, colB, colC, colD = st.columns([1,1,1,1])

# Single Generate button (replaces separate preview + generate)
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        # Display template, update cumulative, persist and advance hour
        hourly_text = generate_hourly_template()
        st.code(hourly_text, language="text")

        # call the on_generate_hourly logic but ensure we update cumulative dict (not only session_state)
        # We already have on_generate_hourly() defined earlier; reuse it but ensure cumulative is updated
        try:
            on_generate_hourly()
        except Exception as e:
            # fallback: replicate minimal on_generate_hourly if something breaks
            # (should not happen because on_generate_hourly exists)
            st.error(f"Error updating hourly totals: {e}")

        # ensure cumulative dict mirrors session_state counters
        cumulative["done_load"] = int(st.session_state.get("done_load", cumulative.get("done_load", 0)))
        cumulative["done_disch"] = int(st.session_state.get("done_disch", cumulative.get("done_disch", 0)))
        cumulative["done_restow_load"] = int(st.session_state.get("done_restow_load", cumulative.get("done_restow_load", 0)))
        cumulative["done_restow_disch"] = int(st.session_state.get("done_restow_disch", cumulative.get("done_restow_disch", 0)))
        cumulative["done_hatch_open"] = int(st.session_state.get("done_hatch_open", cumulative.get("done_hatch_open", 0)))
        cumulative["done_hatch_close"] = int(st.session_state.get("done_hatch_close", cumulative.get("done_hatch_close", 0)))

        # persist meta to DB + JSON
        persist_meta()

with colB:
    if st.button("📤 Open WhatsApp (Hourly)"):
        hourly_text = generate_hourly_template()
        wa_text = f"```{hourly_text}```"
        if st.session_state.get("wa_num_hour"):
            link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_hour"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")

with colC:
    if st.button("🔄 Reset Hourly Inputs (and advance hour)"):
        # Reset only hourly widget values and gearbox hourly total
        for k in [
            "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
            "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
            "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
            "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
            "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
            "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
            "gearbox_total_hour"
        ]:
            st.session_state[k] = 0
        st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])
        st.success("Hourly inputs reset and hour advanced (override applied on next render).")

with colD:
    if st.button("🧯 Master Reset (clear EVERYTHING)"):
        # Clear cumulative, tracker, hourly inputs, meta in DB/JSON
        # WARNING: master reset will wipe vessel & plan meta as requested
        cumulative.update({
            "done_load": 0,
            "done_disch": 0,
            "done_restow_load": 0,
            "done_restow_disch": 0,
            "done_hatch_open": 0,
            "done_hatch_close": 0,
            "last_hour": hour_range_list()[0],
            "vessel_name": "MSC NILA",
            "berthed_date": "",
            "planned_load": 0,
            "planned_disch": 0,
            "planned_restow_load": 0,
            "planned_restow_disch": 0,
            "opening_load": 0,
            "opening_disch": 0,
            "opening_restow_load": 0,
            "opening_restow_disch": 0
        })
        save_cumulative(cumulative)
        try:
            save_to_db(cumulative)
        except Exception:
            pass

        # clear session_state keys (keep UI stable)
        for k in list(st.session_state.keys()):
            # keep Streamlit internal keys safe by skipping keys that look internal
            if k.startswith("sidebar") or k.startswith("_") or k in ("run_id","session_id"):
                continue
            # allow clearing almost everything
            try:
                del st.session_state[k]
            except Exception:
                pass
        st.experimental_rerun()
        # --------------------------
# 4-Hourly Tracker & Report
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]

st.selectbox(
    "Select 4-Hour Block",
    options=block_opts,
    index=block_opts.index(st.session_state["fourh_block"]),
    key="fourh_block"
)

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

    # Never negative; adjust plan to match done if necessary
    if remaining_load < 0:
        st.session_state["planned_load"] += abs(remaining_load)
        remaining_load = 0
    if remaining_disch < 0:
        st.session_state["planned_disch"] += abs(remaining_disch)
        remaining_disch = 0
    if remaining_restow_load < 0:
        st.session_state["planned_restow_load"] += abs(remaining_restow_load)
        remaining_restow_load = 0
    if remaining_restow_disch < 0:
        st.session_state["planned_restow_disch"] += abs(remaining_restow_disch)
        remaining_restow_disch = 0

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

First Lift: {st.session_state.get('first_lift','')}
Last Lift: {st.session_state.get('last_lift','')}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load    Discharge
FWD       {vals4h['fwd_load']:>5}     {vals4h['fwd_disch']:>5}
MID       {vals4h['mid_load']:>5}     {vals4h['mid_disch']:>5}
AFT       {vals4h['aft_load']:>5}     {vals4h['aft_disch']:>5}
POOP      {vals4h['poop_load']:>5}     {vals4h['poop_disch']:>5}
_________________________
*Restows*
           Load    Discharge
FWD       {vals4h['fwd_restow_load']:>5}     {vals4h['fwd_restow_disch']:>5}
MID       {vals4h['mid_restow_load']:>5}     {vals4h['mid_restow_disch']:>5}
AFT       {vals4h['aft_restow_load']:>5}     {vals4h['aft_restow_disch']:>5}
POOP      {vals4h['poop_restow_load']:>5}     {vals4h['poop_restow_disch']:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries + opening balance)
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']+st.session_state['opening_load']:>5}      {cumulative['done_disch']+st.session_state['opening_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']+st.session_state['opening_restow_load']:>5}      {cumulative['done_restow_disch']+st.session_state['opening_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Gearboxes*
Total Gearboxes: {st.session_state['gearbox_total_hour']}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template(), language="text")

# WhatsApp 4-Hourly section
st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB = st.columns([1,1])
with cA:
    if st.button("✅ Generate & Update 4-Hourly Template"):
        st.code(generate_4h_template(), language="text")
        persist_meta()
with cB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template()
        wa_text = f"```{t}```"
        if st.session_state.get("wa_num_4h"):
            link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_4h"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")

# Reset 4-hour tracker
if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
    reset_4h_tracker()
    st.success("4-hourly tracker reset.")

# --------------------------
# Footer notes
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets: Hourly, 4-Hourly, or Master Reset are available as needed. "
    "• Gearboxes: Only hourly totals shown (no cumulative). "
    "• Opening balances are added to 'Done' automatically to adjust 'Remaining'. "
    "• Plan totals auto-adjust upward if Done ever exceeds Plan."
    )
