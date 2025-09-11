# WhatsApp_Report.py  — PART 1 / 5
import streamlit as st
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import pytz

# Page config
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & PERSISTENCE
# --------------------------
SAVE_DB = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

# Default cumulative/settings
DEFAULT_CUMULATIVE = {
    "done_load": 0,
    "done_disch": 0,
    "done_restow_load": 0,
    "done_restow_disch": 0,
    "done_hatch_open": 0,
    "done_hatch_close": 0,
    "last_hour": "06h00 - 07h00",
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10h55",
    "planned_load": 687,
    "planned_disch": 38,
    "planned_restow_load": 13,
    "planned_restow_disch": 13,
    "opening_load": 0,
    "opening_disch": 0,
    "opening_restow_load": 0,
    "opening_restow_disch": 0,
    "first_lift": "",
    "last_lift": ""
}

# --------------------------
# DB helpers
# --------------------------
def get_conn():
    return sqlite3.connect(SAVE_DB, isolation_level=None, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # meta table stores cumulative json
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            json TEXT NOT NULL
        );
    """)
    # settings table for individual keys (easier if you want query params later)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    # fourh table (rolling hours details): store each hour entry as JSON with timestamp
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fourh_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hour_label TEXT,
            json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Ensure meta row exists
    cur.execute("SELECT json FROM meta WHERE id = 1;")
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?);", (json.dumps(DEFAULT_CUMULATIVE),))
    conn.commit()
    conn.close()

def load_cumulative_from_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id = 1;")
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return DEFAULT_CUMULATIVE.copy()
    return DEFAULT_CUMULATIVE.copy()

def save_cumulative_to_db(cum: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (json.dumps(cum),))
    conn.commit()
    conn.close()

def save_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value;", (key, str(value)))
    conn.commit()
    conn.close()

def load_settings_from_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings;")
    rows = cur.fetchall()
    conn.close()
    return {k:v for k,v in rows}

def append_fourh_entry(hour_label: str, data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO fourh_entries (hour_label, json) VALUES (?, ?);", (hour_label, json.dumps(data)))
    # Keep only last 24 entries for safety (optional)
    cur.execute("DELETE FROM fourh_entries WHERE id NOT IN (SELECT id FROM fourh_entries ORDER BY id DESC LIMIT 100);")
    conn.commit()
    conn.close()

def get_last_fourh_entries(n=4):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT hour_label, json FROM fourh_entries ORDER BY id DESC LIMIT ?;", (n,))
    rows = cur.fetchall()
    conn.close()
    # return newest first -> reverse to chronological
    return list(reversed([(r[0], json.loads(r[1])) for r in rows]))

# Initialize DB
init_db()
cumulative = load_cumulative_from_db()
db_settings = load_settings_from_db()

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
# SESSION STATE INIT (safe)
# --------------------------
def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# date & labels - persist across sessions using DB values if present
init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", db_settings.get("vessel_name", cumulative.get("vessel_name", DEFAULT_CUMULATIVE["vessel_name"])))
init_key("berthed_date", db_settings.get("berthed_date", cumulative.get("berthed_date", DEFAULT_CUMULATIVE["berthed_date"])))
init_key("first_lift", db_settings.get("first_lift", cumulative.get("first_lift", "")))
init_key("last_lift", db_settings.get("last_lift", cumulative.get("last_lift", "")))

# plans & openings (from db/meta, editable in UI)
for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, int(db_settings.get(k, cumulative.get(k, DEFAULT_CUMULATIVE.get(k,0)))))

# HOURLY inputs
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hour_gearbox_total"
]:
    init_key(k, 0)

# idle entries
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection (hourly)
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# FOUR-HOUR tracker (lists roll up to 4 most recent generated hours) kept in session to avoid DB reads too much
def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0,
    }

init_key("fourh", empty_tracker())
init_key("fourh_manual_override", False)

# manual 4H fields
for k in [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
]:
    init_key(k, 0)

init_key("fourh_block", four_hour_blocks()[0])
# WhatsApp_Report.py  — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # Use keys only (do not assign widget output to session_state)
    st.text_input("Vessel Name", key="vessel_name", value=st.session_state["vessel_name"])
    st.text_input("Berthed Date", key="berthed_date", value=st.session_state["berthed_date"])
    st.text_input("First Lift", key="first_lift", value=st.session_state["first_lift"])
    st.text_input("Last Lift", key="last_lift", value=st.session_state["last_lift"])
    # Save settings to DB whenever changed (use small callback)
    def save_basic_settings():
        save_setting("vessel_name", st.session_state["vessel_name"])
        save_setting("berthed_date", st.session_state["berthed_date"])
        save_setting("first_lift", st.session_state["first_lift"])
        save_setting("last_lift", st.session_state["last_lift"])
        # also reflect to cumulative meta
        cumulative.update({
            "vessel_name": st.session_state["vessel_name"],
            "berthed_date": st.session_state["berthed_date"],
            "first_lift": st.session_state["first_lift"],
            "last_lift": st.session_state["last_lift"]
        })
        save_cumulative_to_db(cumulative)
    # Wire save callback to inputs using form or on_change: we'll attach to a hidden button to call manually
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date", value=st.session_state["report_date"])

# Provide a small save button to persist settings (avoids writing on every keystroke)
st.button("💾 Save Vessel & Lift Settings", on_click=save_basic_settings)

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load", value=st.session_state["planned_load"])
        st.number_input("Planned Discharge", min_value=0, key="planned_disch", value=st.session_state["planned_disch"])
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load", value=st.session_state["planned_restow_load"])
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch", value=st.session_state["planned_restow_disch"])
    with c2:
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load", value=st.session_state["opening_load"])
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch", value=st.session_state["opening_disch"])
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load", value=st.session_state["opening_restow_load"])
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch", value=st.session_state["opening_restow_disch"])

    # Save plan/opening immediately button
    def save_plan_openings():
        keys = ["planned_load","planned_disch","planned_restow_load","planned_restow_disch",
                "opening_load","opening_disch","opening_restow_load","opening_restow_disch"]
        for kk in keys:
            save_setting(kk, st.session_state[kk])
            cumulative[kk] = int(st.session_state[kk])
        save_cumulative_to_db(cumulative)
        st.success("Plan totals & openings saved.")
    st.button("💾 Save Plan & Opening Balances", on_click=save_plan_openings)

# --------------------------
# Hour selector (24h) with safe override handoff
# --------------------------
# Apply pending hour change from previous action BEFORE rendering the selectbox
if "hourly_time_override" in st.session_state:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    del st.session_state["hourly_time_override"]

# Ensure valid label
if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"] = cumulative.get("last_hour", hour_range_list()[0])

st.selectbox(
    "⏱ Select Hourly Time",
    options=hour_range_list(),
    index=hour_range_list().index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")
# WhatsApp_Report.py  — PART 3 / 5

# --------------------------
# Crane Moves (Load & Discharge) — keep collapsibles exactly as you had
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load", value=st.session_state["hr_fwd_load"])
        st.number_input("MID Load", min_value=0, key="hr_mid_load", value=st.session_state["hr_mid_load"])
        st.number_input("AFT Load", min_value=0, key="hr_aft_load", value=st.session_state["hr_aft_load"])
        st.number_input("POOP Load", min_value=0, key="hr_poop_load", value=st.session_state["hr_poop_load"])
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch", value=st.session_state["hr_fwd_disch"])
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch", value=st.session_state["hr_mid_disch"])
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch", value=st.session_state["hr_aft_disch"])
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch", value=st.session_state["hr_poop_disch"])

# --------------------------
# Restows (Load & Discharge)
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load", value=st.session_state["hr_fwd_restow_load"])
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load", value=st.session_state["hr_mid_restow_load"])
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load", value=st.session_state["hr_aft_restow_load"])
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load", value=st.session_state["hr_poop_restow_load"])
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch", value=st.session_state["hr_fwd_restow_disch"])
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch", value=st.session_state["hr_mid_restow_disch"])
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch", value=st.session_state["hr_aft_restow_disch"])
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch", value=st.session_state["hr_poop_restow_disch"])

# --------------------------
# Hatch Moves (Open & Close)
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open", value=st.session_state["hr_hatch_fwd_open"])
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open", value=st.session_state["hr_hatch_mid_open"])
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open", value=st.session_state["hr_hatch_aft_open"])
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close", value=st.session_state["hr_hatch_fwd_close"])
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close", value=st.session_state["hr_hatch_mid_close"])
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close", value=st.session_state["hr_hatch_aft_close"])

# --------------------------
# Gearbox (hour-only)
# --------------------------
with st.expander("⚙️ Gearbox (hourly total)"):
    st.number_input("Gearbox Total (this hour)", min_value=0, key="hour_gearbox_total", value=st.session_state["hour_gearbox_total"])
    st.caption("This gearbox line is hourly-only and will not be cumulative. It appears on templates for the hour only.")

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
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries", value=st.session_state["num_idle_entries"])
    entries = []
    for i in range(st.session_state["num_idle_entries"]):
        st.markdown(f"**Idle Entry {i+1}**")
        c1, c2, c3, c4 = st.columns([1,1,1,2])
        crane = c1.text_input(f"Crane {i+1}", key=f"idle_crane_{i}", value="")
        start = c2.text_input(f"Start {i+1}", key=f"idle_start_{i}", placeholder="e.g., 12h30", value="")
        end   = c3.text_input(f"End {i+1}",   key=f"idle_end_{i}",   placeholder="e.g., 12h40", value="")
        sel   = c4.selectbox(f"Delay {i+1}", options=idle_options, key=f"idle_sel_{i}")
        custom = c4.text_input(f"Custom Delay {i+1} (optional)", key=f"idle_custom_{i}", value="")
        entries.append({
            "crane": (crane or "").strip(),
            "start": (start or "").strip(),
            "end": (end or "").strip(),
            "delay": (custom or "").strip() if (custom or "").strip() else sel
        })
    # Not a widget key — safe to assign directly
    st.session_state["idle_entries"] = entries

# --------------------------
# Hourly Totals Tracker (split by position)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load":       {"FWD": ss["hr_fwd_load"],       "MID": ss["hr_mid_load"],       "AFT": ss["hr_aft_load"],       "POOP": ss["hr_poop_load"]},
        "disch":      {"FWD": ss["hr_fwd_disch"],      "MID": ss["hr_mid_disch"],      "AFT": ss["hr_aft_disch"],      "POOP": ss["hr_poop_disch"]},
        "restow_load":{"FWD": ss["hr_fwd_restow_load"],"MID": ss["hr_mid_restow_load"],"AFT": ss["hr_aft_restow_load"],"POOP": ss["hr_poop_restow_load"]},
        "restow_disch":{"FWD": ss["hr_fwd_restow_disch"],"MID": ss["hr_mid_restow_disch"],"AFT": ss["hr_aft_restow_disch"],"POOP": ss["hr_poop_restow_disch"]},
        "hatch_open": {"FWD": ss["hr_hatch_fwd_open"], "MID": ss["hr_hatch_mid_open"], "AFT": ss["hr_hatch_aft_open"]},
        "hatch_close":{"FWD": ss["hr_hatch_fwd_close"],"MID": ss["hr_hatch_mid_close"],"AFT": ss["hr_hatch_aft_close"]},
        "gearbox": ss.get("hour_gearbox_total", 0)
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearbox (this hour):** {split['gearbox']}")
    # WhatsApp_Report.py  — PART 4 / 5

# --------------------------
# WhatsApp (Hourly) – original monospace template (unchanged format)
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    # compute remaining using persistent cumulative + opening balances (opening applied once at app start or first generate)
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

    # hour split snapshot
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
Total (this hour): {st.session_state.get('hour_gearbox_total', 0)}
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
    # Add first/last lift info and gearbox lines as previously present in your original template region:
    tmpl += f"_________________________\nFirst Lift: {st.session_state.get('first_lift','')}\nLast Lift: {st.session_state.get('last_lift','')}\n"
    return tmpl

# --------------------------
# Core generate button — single button as requested
# --------------------------
def on_generate_hourly():
    # Take a snapshot of hourly splits
    hour_snapshot = {
        "hr_fwd_load": int(st.session_state["hr_fwd_load"]),
        "hr_mid_load": int(st.session_state["hr_mid_load"]),
        "hr_aft_load": int(st.session_state["hr_aft_load"]),
        "hr_poop_load": int(st.session_state["hr_poop_load"]),
        "hr_fwd_disch": int(st.session_state["hr_fwd_disch"]),
        "hr_mid_disch": int(st.session_state["hr_mid_disch"]),
        "hr_aft_disch": int(st.session_state["hr_aft_disch"]),
        "hr_poop_disch": int(st.session_state["hr_poop_disch"]),
        "hr_fwd_restow_load": int(st.session_state["hr_fwd_restow_load"]),
        "hr_mid_restow_load": int(st.session_state["hr_mid_restow_load"]),
        "hr_aft_restow_load": int(st.session_state["hr_aft_restow_load"]),
        "hr_poop_restow_load": int(st.session_state["hr_poop_restow_load"]),
        "hr_fwd_restow_disch": int(st.session_state["hr_fwd_restow_disch"]),
        "hr_mid_restow_disch": int(st.session_state["hr_mid_restow_disch"]),
        "hr_aft_restow_disch": int(st.session_state["hr_aft_restow_disch"]),
        "hr_poop_restow_disch": int(st.session_state["hr_poop_restow_disch"]),
        "hr_hatch_fwd_open": int(st.session_state["hr_hatch_fwd_open"]),
        "hr_hatch_mid_open": int(st.session_state["hr_hatch_mid_open"]),
        "hr_hatch_aft_open": int(st.session_state["hr_hatch_aft_open"]),
        "hr_hatch_fwd_close": int(st.session_state["hr_hatch_fwd_close"]),
        "hr_hatch_mid_close": int(st.session_state["hr_hatch_mid_close"]),
        "hr_hatch_aft_close": int(st.session_state["hr_hatch_aft_close"]),
        "gearbox": int(st.session_state.get("hour_gearbox_total", 0)),
    }

    # Apply opening balances only once (tracking flag in cumulative). This ensures opening balances are counted as Done.
    if not cumulative.get("_openings_applied", False):
        # Add openings into done counters so they show as Done in first generate
        cumulative["done_load"] += int(st.session_state.get("opening_load", 0))
        cumulative["done_disch"] += int(st.session_state.get("opening_disch", 0))
        cumulative["done_restow_load"] += int(st.session_state.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] += int(st.session_state.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # Update cumulative with this hour's contributions (summing splits)
    hour_load = hour_snapshot["hr_fwd_load"] + hour_snapshot["hr_mid_load"] + hour_snapshot["hr_aft_load"] + hour_snapshot["hr_poop_load"]
    hour_disch = hour_snapshot["hr_fwd_disch"] + hour_snapshot["hr_mid_disch"] + hour_snapshot["hr_aft_disch"] + hour_snapshot["hr_poop_disch"]
    hour_restow_load = hour_snapshot["hr_fwd_restow_load"] + hour_snapshot["hr_mid_restow_load"] + hour_snapshot["hr_aft_restow_load"] + hour_snapshot["hr_poop_restow_load"]
    hour_restow_disch = hour_snapshot["hr_fwd_restow_disch"] + hour_snapshot["hr_mid_restow_disch"] + hour_snapshot["hr_aft_restow_disch"] + hour_snapshot["hr_poop_restow_disch"]
    hour_hatch_open = hour_snapshot["hr_hatch_fwd_open"] + hour_snapshot["hr_hatch_mid_open"] + hour_snapshot["hr_hatch_aft_open"]
    hour_hatch_close = hour_snapshot["hr_hatch_fwd_close"] + hour_snapshot["hr_hatch_mid_close"] + hour_snapshot["hr_hatch_aft_close"]

    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_restow_load)
    cumulative["done_restow_disch"] += int(hour_restow_disch)
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)

    # Ensure Done never exceeds Plan; if it does, bump Plan to keep Remain >= 0
    # For load:
    if cumulative["done_load"] > st.session_state["planned_load"]:
        st.session_state["planned_load"] = cumulative["done_load"]
        save_setting("planned_load", st.session_state["planned_load"])
        cumulative["planned_load"] = st.session_state["planned_load"]
    # For disch:
    if cumulative["done_disch"] > st.session_state["planned_disch"]:
        st.session_state["planned_disch"] = cumulative["done_disch"]
        save_setting("planned_disch", st.session_state["planned_disch"])
        cumulative["planned_disch"] = st.session_state["planned_disch"]
    # For restow load:
    if cumulative["done_restow_load"] > st.session_state["planned_restow_load"]:
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"]
        save_setting("planned_restow_load", st.session_state["planned_restow_load"])
        cumulative["planned_restow_load"] = st.session_state["planned_restow_load"]
    # For restow disch:
    if cumulative["done_restow_disch"] > st.session_state["planned_restow_disch"]:
        st.session_state["planned_restow_disch"] = cumulative["done_restow_disch"]
        save_setting("planned_restow_disch", st.session_state["planned_restow_disch"])
        cumulative["planned_restow_disch"] = st.session_state["planned_restow_disch"]

    # Persist cumulative & settings to DB
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
        "first_lift": st.session_state.get("first_lift", ""),
        "last_lift": st.session_state.get("last_lift", ""),
        "last_hour": st.session_state["hourly_time"]
    })
    save_cumulative_to_db(cumulative)
    # Save individual settings to settings table too
    save_setting("vessel_name", st.session_state["vessel_name"])
    save_setting("berthed_date", st.session_state["berthed_date"])
    save_setting("planned_load", st.session_state["planned_load"])
    save_setting("planned_disch", st.session_state["planned_disch"])
    save_setting("planned_restow_load", st.session_state["planned_restow_load"])
    save_setting("planned_restow_disch", st.session_state["planned_restow_disch"])
    save_setting("opening_load", st.session_state["opening_load"])
    save_setting("opening_disch", st.session_state["opening_disch"])
    save_setting("opening_restow_load", st.session_state["opening_restow_load"])
    save_setting("opening_restow_disch", st.session_state["opening_restow_disch"])
    save_setting("first_lift", st.session_state.get("first_lift",""))
    save_setting("last_lift", st.session_state.get("last_lift",""))

    # Append an entry for rolling 4h (store per-position values)
    hour_entry = {
        "hour_label": st.session_state["hourly_time"],
        "load": {
            "FWD": hour_snapshot["hr_fwd_load"], "MID": hour_snapshot["hr_mid_load"],
            "AFT": hour_snapshot["hr_aft_load"], "POOP": hour_snapshot["hr_poop_load"]
        },
        "disch": {
            "FWD": hour_snapshot["hr_fwd_disch"], "MID": hour_snapshot["hr_mid_disch"],
            "AFT": hour_snapshot["hr_aft_disch"], "POOP": hour_snapshot["hr_poop_disch"]
        },
        "restow_load": {
            "FWD": hour_snapshot["hr_fwd_restow_load"], "MID": hour_snapshot["hr_mid_restow_load"],
            "AFT": hour_snapshot["hr_aft_restow_load"], "POOP": hour_snapshot["hr_poop_restow_load"]
        },
        "restow_disch": {
            "FWD": hour_snapshot["hr_fwd_restow_disch"], "MID": hour_snapshot["hr_mid_restow_disch"],
            "AFT": hour_snapshot["hr_aft_restow_disch"], "POOP": hour_snapshot["hr_poop_restow_disch"]
        },
        "hatch_open": {
            "FWD": hour_snapshot["hr_hatch_fwd_open"], "MID": hour_snapshot["hr_hatch_mid_open"], "AFT": hour_snapshot["hr_hatch_aft_open"]
        },
        "hatch_close": {
            "FWD": hour_snapshot["hr_hatch_fwd_close"], "MID": hour_snapshot["hr_hatch_mid_close"], "AFT": hour_snapshot["hr_hatch_aft_close"]
        },
        "gearbox": hour_snapshot["gearbox"]
    }
    append_fourh_entry(st.session_state["hourly_time"], hour_entry)

    # Also update the in-memory fourh session tracker for quick computed_4h readings
    tr = st.session_state["fourh"]
    tr["fwd_load"].append(hour_snapshot["hr_fwd_load"])
    tr["mid_load"].append(hour_snapshot["hr_mid_load"])
    tr["aft_load"].append(hour_snapshot["hr_aft_load"])
    tr["poop_load"].append(hour_snapshot["hr_poop_load"])
    tr["fwd_disch"].append(hour_snapshot["hr_fwd_disch"])
    tr["mid_disch"].append(hour_snapshot["hr_mid_disch"])
    tr["aft_disch"].append(hour_snapshot["hr_aft_disch"])
    tr["poop_disch"].append(hour_snapshot["hr_poop_disch"])
    tr["fwd_restow_load"].append(hour_snapshot["hr_fwd_restow_load"])
    tr["mid_restow_load"].append(hour_snapshot["hr_mid_restow_load"])
    tr["aft_restow_load"].append(hour_snapshot["hr_aft_restow_load"])
    tr["poop_restow_load"].append(hour_snapshot["hr_poop_restow_load"])
    tr["fwd_restow_disch"].append(hour_snapshot["hr_fwd_restow_disch"])
    tr["mid_restow_disch"].append(hour_snapshot["hr_mid_restow_disch"])
    tr["aft_restow_disch"].append(hour_snapshot["hr_aft_restow_disch"])
    tr["poop_restow_disch"].append(hour_snapshot["hr_poop_restow_disch"])
    tr["hatch_fwd_open"].append(hour_snapshot["hr_hatch_fwd_open"])
    tr["hatch_mid_open"].append(hour_snapshot["hr_hatch_mid_open"])
    tr["hatch_aft_open"].append(hour_snapshot["hr_hatch_aft_open"])
    tr["hatch_fwd_close"].append(hour_snapshot["hr_hatch_fwd_close"])
    tr["hatch_mid_close"].append(hour_snapshot["hr_hatch_mid_close"])
    tr["hatch_aft_close"].append(hour_snapshot["hr_hatch_aft_close"])
    tr["count_hours"] = min(4, tr["count_hours"] + 1)
    # Keep last 4
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]

    # Advance hour safely via override - applied before selectbox rendering next script run
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    # Return template text for immediate display
    return generate_hourly_template_text()

# Single generate button
if st.button("✅ Generate Hourly Template & Update Totals"):
    txt = on_generate_hourly()
    st.code(txt, language="text")

# Offer Open WhatsApp (still optional)
if st.button("📤 Open WhatsApp (Hourly)"):
    txt = generate_hourly_template_text()
    wa_text = f"```{txt}```"
    if st.session_state.get("wa_num_hour"):
        link = f"https://wa.me/{st.session_state['wa_num_hour']}?text={urllib.parse.quote(wa_text)}"
        st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
    elif st.session_state.get("wa_grp_hour"):
        st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_hour']})", unsafe_allow_html=True)
    else:
        st.info("Enter a WhatsApp number or group link to send.")
        # WhatsApp_Report.py  — PART 5 / 5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def sum_list(lst):
    return int(sum(lst)) if lst else 0

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"], "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"], "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"], "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"], "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"], "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"], "hatch_aft_close": ss["m4h_hatch_aft_close"],
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")

with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto-calculated", key="fourh_manual_override")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("FWD Load 4H", min_value=0, key="m4h_fwd_load")
        st.number_input("FWD Disch 4H", min_value=0, key="m4h_fwd_disch")
        st.number_input("FWD Rst Load 4H", min_value=0, key="m4h_fwd_restow_load")
        st.number_input("FWD Rst Disch 4H", min_value=0, key="m4h_fwd_restow_disch")
        st.number_input("FWD Hatch Open 4H", min_value=0, key="m4h_hatch_fwd_open")
        st.number_input("FWD Hatch Close 4H", min_value=0, key="m4h_hatch_fwd_close")
    with c2:
        st.number_input("MID Load 4H", min_value=0, key="m4h_mid_load")
        st.number_input("MID Disch 4H", min_value=0, key="m4h_mid_disch")
        st.number_input("MID Rst Load 4H", min_value=0, key="m4h_mid_restow_load")
        st.number_input("MID Rst Disch 4H", min_value=0, key="m4h_mid_restow_disch")
        st.number_input("MID Hatch Open 4H", min_value=0, key="m4h_hatch_mid_open")
        st.number_input("MID Hatch Close 4H", min_value=0, key="m4h_hatch_mid_close")
    with c3:
        st.number_input("AFT Load 4H", min_value=0, key="m4h_aft_load")
        st.number_input("AFT Disch 4H", min_value=0, key="m4h_aft_disch")
        st.number_input("AFT Rst Load 4H", min_value=0, key="m4h_aft_restow_load")
        st.number_input("AFT Rst Disch 4H", min_value=0, key="m4h_aft_restow_disch")
        st.number_input("AFT Hatch Open 4H", min_value=0, key="m4h_hatch_aft_open")
        st.number_input("AFT Hatch Close 4H", min_value=0, key="m4h_hatch_aft_close")
    with c4:
        st.number_input("POOP Load 4H", min_value=0, key="m4h_poop_load")
        st.number_input("POOP Disch 4H", min_value=0, key="m4h_poop_disch")
        st.number_input("POOP Rst Load 4H", min_value=0, key="m4h_poop_restow_load")
        st.number_input("POOP Rst Disch 4H", min_value=0, key="m4h_poop_restow_disch")

# --- NEW BUTTON: populate manual 4H fields from computed 4H tracker ---
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    calc_vals = computed_4h()
    # map computed values into manual 4h session keys
    st.session_state["m4h_fwd_load"] = calc_vals["fwd_load"]
    st.session_state["m4h_mid_load"] = calc_vals["mid_load"]
    st.session_state["m4h_aft_load"] = calc_vals["aft_load"]
    st.session_state["m4h_poop_load"] = calc_vals["poop_load"]

    st.session_state["m4h_fwd_disch"] = calc_vals["fwd_disch"]
    st.session_state["m4h_mid_disch"] = calc_vals["mid_disch"]
    st.session_state["m4h_aft_disch"] = calc_vals["aft_disch"]
    st.session_state["m4h_poop_disch"] = calc_vals["poop_disch"]

    st.session_state["m4h_fwd_restow_load"] = calc_vals["fwd_restow_load"]
    st.session_state["m4h_mid_restow_load"] = calc_vals["mid_restow_load"]
    st.session_state["m4h_aft_restow_load"] = calc_vals["aft_restow_load"]
    st.session_state["m4h_poop_restow_load"] = calc_vals["poop_restow_load"]

    st.session_state["m4h_fwd_restow_disch"] = calc_vals["fwd_restow_disch"]
    st.session_state["m4h_mid_restow_disch"] = calc_vals["mid_restow_disch"]
    st.session_state["m4h_aft_restow_disch"] = calc_vals["aft_restow_disch"]
    st.session_state["m4h_poop_restow_disch"] = calc_vals["poop_restow_disch"]

    st.session_state["m4h_hatch_fwd_open"] = calc_vals["hatch_fwd_open"]
    st.session_state["m4h_hatch_mid_open"] = calc_vals["hatch_mid_open"]
    st.session_state["m4h_hatch_aft_open"] = calc_vals["hatch_aft_open"]

    st.session_state["m4h_hatch_fwd_close"] = calc_vals["hatch_fwd_close"]
    st.session_state["m4h_hatch_mid_close"] = calc_vals["hatch_mid_close"]
    st.session_state["m4h_hatch_aft_close"] = calc_vals["hatch_aft_close"]

    # enable manual override so template will use these values
    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"]

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}

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
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    t += f"_________________________\nFirst Lift: {st.session_state.get('first_lift','')}\nLast Lift: {st.session_state.get('last_lift','')}\n"
    return t

st.code(generate_4h_template(), language="text")

st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB, cC = st.columns([1,1,1])
with cA:
    if st.button("👁️ Preview 4-Hourly Template Only"):
        st.code(generate_4h_template(), language="text")
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
with cC:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        st.session_state["fourh"] = empty_tracker()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM fourh_entries;")
        conn.commit()
        conn.close()
        st.success("4-hourly tracker reset.")

# --------------------------
# Hourly Reset & Master Reset
# --------------------------
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hour_gearbox_total"
    ]:
        st.session_state[k] = 0
    st.success("Hourly inputs cleared for the next hour.")

st.button("🔄 Reset Hourly Inputs (clear only hourly inputs)", on_click=reset_hourly_inputs)

def master_reset():
    # Reset DB to defaults (meta) and clear settings & fourh entries
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM settings;")
    cur.execute("DELETE FROM fourh_entries;")
    cur.execute("UPDATE meta SET json = ? WHERE id = 1;", (json.dumps(DEFAULT_CUMULATIVE),))
    conn.commit()
    conn.close()
    # Reset session
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()

if st.button("⚠️ Master Reset (clear everything)"):
    st.warning("This will clear all saved settings and cumulative totals. Confirm to proceed.")
    if st.button("Confirm Master Reset — Yes, clear everything"):
        master_reset()

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Populate 4-Hourly** if you want to copy hourly rolling totals into the 4-hour manual input. "
    "• Resets: Hourly reset clears only the hourly inputs. 4-hourly reset clears the 4-hour tracker. Master reset clears everything (DB + session). "
    "• Opening balances are applied once (on first Generate) so they appear as Done and reduce Remain. "
        )
