import streamlit as st
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & DB
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY,
            json TEXT
        );
    """)
    conn.commit()
    # insert default row if empty
    cur.execute("SELECT COUNT(*) FROM meta;")
    if cur.fetchone()[0] == 0:
        default = {
            "done_load": 0,
            "done_disch": 0,
            "done_restow_load": 0,
            "done_restow_disch": 0,
            "done_hatch_open": 0,
            "done_hatch_close": 0,
            "done_gearbox": 0,
            "last_hour": "06h00 - 07h00",
            "vessel_name": "MSC NILA",
            "berthed_date": "",
            "first_lift": "",
            "last_lift": "",
            "planned_load": 0,
            "planned_disch": 0,
            "planned_restow_load": 0,
            "planned_restow_disch": 0,
            "opening_load": 0,
            "opening_disch": 0,
            "opening_restow_load": 0,
            "opening_restow_disch": 0,
            "_openings_applied": False,
        }
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (json.dumps(default),))
        conn.commit()
    conn.close()

def load_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def save_db(data: dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json=? WHERE id=1;", (json.dumps(data),))
    conn.commit()
    conn.close()

init_db()

# --------------------------
# LOAD STATE ONCE
# --------------------------
if "cumulative" not in st.session_state:
    st.session_state["cumulative"] = load_db()

cumulative = st.session_state["cumulative"]

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
# SESSION STATE INIT
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# Vessel info
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", "MSC NILA"))
init_key("berthed_date", cumulative.get("berthed_date", ""))
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

# Plans & openings
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, cumulative.get(k, 0))

# HOURLY inputs
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox"
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.text_input("First Lift", key="first_lift")
    st.text_input("Last Lift", key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date")

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load")
        st.number_input("Planned Discharge", min_value=0, key="planned_disch")
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load")
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch")
    with c2:
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load")
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch")

# --------------------------
# Hour selector (24h) with safe override handoff
# --------------------------
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = cumulative.get("last_hour", hour_range_list()[0])

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves (Load & Discharge)
# --------------------------
with st.expander("🏗️ Crane Moves"):
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

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load")
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load")
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load")
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close")

# --------------------------
# Gearbox Moves (new section)
# --------------------------
with st.expander("⚙️ Gearbox Moves"):
    st.number_input("Total Gearbox Moves", min_value=0, key="hr_gearbox")

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
    st.session_state["idle_entries"] = entries
    # --------------------------
# Hourly Totals (Splits Only)
# --------------------------
st.subheader("📊 Hourly Totals (Splits)")

# Calculate current hour moves
hour_moves = {
    "load": st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"],
    "disch": st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"],
    "restow_load": st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"],
    "restow_disch": st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"],
    "hatch": st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"] +
             st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"],
    "gearbox": st.session_state["hr_gearbox"],
}

# Function to enforce done ≤ plan and adjust if needed
def clamp_done_to_plan(plan, done):
    if done > plan:
        plan = done
    remain = max(plan - done, 0)
    return plan, remain

# --------------------------
# Generate Hourly Template
# --------------------------
def on_generate_hourly():
    global cumulative
    hr = st.session_state["hourly_time"]

    # Update cumulative
    cumulative["done_load"]      += hour_moves["load"]
    cumulative["done_disch"]     += hour_moves["disch"]
    cumulative["done_restow_load"]  += hour_moves["restow_load"]
    cumulative["done_restow_disch"] += hour_moves["restow_disch"]
    cumulative["done_hatch"]     += hour_moves["hatch"]
    cumulative["done_gearbox"]   += hour_moves["gearbox"]

    # Opening balances applied once
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"]      += st.session_state["opening_load"]
        cumulative["done_disch"]     += st.session_state["opening_disch"]
        cumulative["done_restow_load"]  += st.session_state["opening_restow_load"]
        cumulative["done_restow_disch"] += st.session_state["opening_restow_disch"]
        cumulative["_openings_applied"] = True

    # Clamp done to planned
    cumulative["plan_load"], remain_load = clamp_done_to_plan(st.session_state["planned_load"], cumulative["done_load"])
    cumulative["plan_disch"], remain_disch = clamp_done_to_plan(st.session_state["planned_disch"], cumulative["done_disch"])
    cumulative["plan_restow_load"], remain_rload = clamp_done_to_plan(st.session_state["planned_restow_load"], cumulative["done_restow_load"])
    cumulative["plan_restow_disch"], remain_rdisch = clamp_done_to_plan(st.session_state["planned_restow_disch"], cumulative["done_restow_disch"])

    # Save last hour
    cumulative["last_hour"] = hr

    # Persist cumulative + vessel info to SQLite
    cumulative["vessel_name"] = st.session_state["vessel_name"]
    cumulative["berthed_date"] = st.session_state["berthed_date"]
    cumulative["first_lift"] = st.session_state["first_lift"]
    cumulative["last_lift"] = st.session_state["last_lift"]

    save_db(cumulative)

    # Build WhatsApp text
    txt = []
    txt.append(f"{st.session_state['vessel_name']}")
    txt.append(f"Berthed {st.session_state['berthed_date']}")
    txt.append(f"First Lift @ {st.session_state['first_lift']}")
    txt.append(f"Last Lift @ {st.session_state['last_lift']}")
    txt.append("")
    txt.append(f"{st.session_state['report_date']} {hr}")
    txt.append("_________________________")
    txt.append("   *HOURLY MOVES*")
    txt.append("_________________________")
    txt.append("*Crane Moves*")
    txt.append(f"Load: {hour_moves['load']}   Disch: {hour_moves['disch']}")
    txt.append("*Restows*")
    txt.append(f"Load: {hour_moves['restow_load']}   Disch: {hour_moves['restow_disch']}")
    txt.append("*Hatch*")
    txt.append(f"Moves: {hour_moves['hatch']}")
    txt.append("*Gearbox*")
    txt.append(f"Total: {hour_moves['gearbox']}")
    txt.append("")

    # Totals
    txt.append("*Totals*")
    txt.append(f"Load - Plan: {cumulative['plan_load']} | Done: {cumulative['done_load']} | Remain: {remain_load}")
    txt.append(f"Disch - Plan: {cumulative['plan_disch']} | Done: {cumulative['done_disch']} | Remain: {remain_disch}")
    txt.append(f"Restow Load - Plan: {cumulative['plan_restow_load']} | Done: {cumulative['done_restow_load']} | Remain: {remain_rload}")
    txt.append(f"Restow Disch - Plan: {cumulative['plan_restow_disch']} | Done: {cumulative['done_restow_disch']} | Remain: {remain_rdisch}")
    txt.append("")

    # Idle
    if st.session_state["idle_entries"]:
        txt.append("*Idle / Delays*")
        for entry in st.session_state["idle_entries"]:
            txt.append(f"Crane {entry['crane']} {entry['start']}-{entry['end']} {entry['delay']}")

    return "\n".join(txt)

# Button to trigger hourly template
if st.button("✅ Generate Hourly Template"):
    txt = on_generate_hourly()
    st.text_area("WhatsApp Hourly Report", txt, height=300)
    wa = st.text_input("Enter WhatsApp Number (SA format 27...)", key="wa_hourly")
    if wa:
        wa_url = f"https://wa.me/{wa}?text={txt.replace(' ', '%20')}"
        st.markdown(f"[Send to WhatsApp Hourly]({wa_url})", unsafe_allow_html=True)
        # --------------------------
# 4-Hourly Totals & Summary
# --------------------------
st.subheader("⏱️ 4-Hourly Totals & Summary")

# Function to calculate last 4-hour block
def get_last_4h_summary():
    # Collect last 4 hours from cumulative tracker
    if "4h_blocks" not in cumulative:
        cumulative["4h_blocks"] = []

    return cumulative["4h_blocks"]

def on_generate_4hourly():
    global cumulative
    hr = st.session_state["hourly_time"]

    # Build totals for this 4-hour block
    block = {
        "time": hr,
        "load": cumulative["done_load"],
        "disch": cumulative["done_disch"],
        "restow_load": cumulative["done_restow_load"],
        "restow_disch": cumulative["done_restow_disch"],
        "hatch": cumulative["done_hatch"],
        "gearbox": cumulative["done_gearbox"],
    }

    cumulative.setdefault("4h_blocks", []).append(block)

    # Save to DB
    save_db(cumulative)

    # Build WhatsApp text
    txt = []
    txt.append(f"{st.session_state['vessel_name']}")
    txt.append(f"Berthed {st.session_state['berthed_date']}")
    txt.append(f"First Lift @ {st.session_state['first_lift']}")
    txt.append(f"Last Lift @ {st.session_state['last_lift']}")
    txt.append("")
    txt.append(f"{st.session_state['report_date']} {hr}")
    txt.append("_________________________")
    txt.append("   *4-HOURLY MOVES*")
    txt.append("_________________________")
    txt.append("*Crane Moves*")
    txt.append(f"Load: {block['load']}   Disch: {block['disch']}")
    txt.append("*Restows*")
    txt.append(f"Load: {block['restow_load']}   Disch: {block['restow_disch']}")
    txt.append("*Hatch*")
    txt.append(f"Moves: {block['hatch']}")
    txt.append("*Gearbox*")
    txt.append(f"Total: {block['gearbox']}")
    txt.append("")

    # Totals
    txt.append("*Cumulative Totals*")
    txt.append(f"Load - Plan: {cumulative['plan_load']} | Done: {cumulative['done_load']} | Remain: {max(cumulative['plan_load'] - cumulative['done_load'],0)}")
    txt.append(f"Disch - Plan: {cumulative['plan_disch']} | Done: {cumulative['done_disch']} | Remain: {max(cumulative['plan_disch'] - cumulative['done_disch'],0)}")
    txt.append(f"Restow Load - Plan: {cumulative['plan_restow_load']} | Done: {cumulative['done_restow_load']} | Remain: {max(cumulative['plan_restow_load'] - cumulative['done_restow_load'],0)}")
    txt.append(f"Restow Disch - Plan: {cumulative['plan_restow_disch']} | Done: {cumulative['done_restow_disch']} | Remain: {max(cumulative['plan_restow_disch'] - cumulative['done_restow_disch'],0)}")
    txt.append("")

    # Last 4-hour blocks summary
    txt.append("*Last 4-Hourly Splits*")
    for b in cumulative["4h_blocks"][-4:]:
        txt.append(f"{b['time']} → L:{b['load']} D:{b['disch']} Rl:{b['restow_load']} Rd:{b['restow_disch']} H:{b['hatch']} G:{b['gearbox']}")

    return "\n".join(txt)

# Button to trigger 4-hourly template
if st.button("✅ Generate 4-Hourly Template"):
    txt4h = on_generate_4hourly()
    st.text_area("WhatsApp 4-Hourly Report", txt4h, height=300)
    wa4 = st.text_input("Enter WhatsApp Number (SA format 27...)", key="wa_4h")
    if wa4:
        wa4_url = f"https://wa.me/{wa4}?text={txt4h.replace(' ', '%20')}"
        st.markdown(f"[Send to WhatsApp 4-Hourly]({wa4_url})", unsafe_allow_html=True)
        # --------------------------
# Reset Controls
# --------------------------
st.markdown("---")
st.subheader("♻️ Reset Controls")

# Reset Hourly
if st.button("🔄 Reset Hourly Tracker"):
    cumulative["hourly"] = []
    save_db(cumulative)
    st.success("Hourly tracker reset.")

# Reset 4-Hourly
if st.button("🔄 Reset 4-Hourly Tracker"):
    cumulative["4h_blocks"] = []
    save_db(cumulative)
    st.success("4-hourly tracker reset.")

# Master Reset (everything including gearboxes + inputs)
if st.button("🧨 Master Reset (Everything)"):
    cumulative = {
        "plan_load": 0,
        "plan_disch": 0,
        "plan_restow_load": 0,
        "plan_restow_disch": 0,
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch": 0,
        "done_gearbox": 0,
        "hourly": [],
        "4h_blocks": []
    }
    # Reset session state inputs too
    for k in list(st.session_state.keys()):
        if isinstance(st.session_state[k], (int, float)):
            st.session_state[k] = 0
        elif isinstance(st.session_state[k], str):
            if k in ["vessel_name", "berthed_date", "first_lift", "last_lift"]:
                st.session_state[k] = ""
    save_db(cumulative)
    st.success("⚠️ Master reset completed. All data cleared!")

# --------------------------
# Footer Notes
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to update done totals. \n"
    "• 4-Hourly: Updates when pressing **Generate 4-Hourly Template**. \n"
    "• Opening balances are applied to done totals at first generate. \n"
    "• Gearbox totals appear only for the active hour — they are not cumulative. \n"
    "• Resets: Hourly / 4-Hourly / Master Reset (all data)."
)
