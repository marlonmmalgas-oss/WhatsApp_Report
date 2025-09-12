# WhatsApp_Report.py  — PART 1 / 5
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz
import sqlite3

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

SAVE_FILE = "vessel_report.json"
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

def db_connect():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
    row = cur.fetchone()
    if row is None:
        initial = load_cumulative_file_fallback()
        cur.execute("INSERT INTO meta (key, value) VALUES ('cumulative', ?);", (json.dumps(initial),))
        conn.commit()
    conn.close()

def load_cumulative_db():
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key = 'cumulative';")
        row = cur.fetchone()
        conn.close()
        if row:
            return json.loads(row["value"])
    except Exception:
        pass
    return None

def save_cumulative_db(data: dict):
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("REPLACE INTO meta (key, value) VALUES ('cumulative', ?);", (json.dumps(data),))
        conn.commit()
        conn.close()
    except Exception:
        pass

def load_cumulative_file_fallback():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
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

def save_cumulative_file(data: dict):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

init_db()
cumulative = load_cumulative_db() or load_cumulative_file_fallback()

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

def init_key(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

init_key("report_date", datetime.now(TZ).date())
init_key("vessel_name", cumulative.get("vessel_name", "MSC NILA"))
init_key("berthed_date", cumulative.get("berthed_date", cumulative.get("berthed_date", "")))
init_key("first_lift", cumulative.get("first_lift", ""))
init_key("last_lift", cumulative.get("last_lift", ""))

for k in [
    "planned_load","planned_disch","planned_restow_load","planned_restow_disch",
    "opening_load","opening_disch","opening_restow_load","opening_restow_disch"
]:
    init_key(k, int(cumulative.get(k, 0)))

for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    "hr_gearbox_total"
]:
    init_key(k, 0)

init_key("num_idle_entries", 0)
init_key("idle_entries", [])

hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "gearbox": [], "count_hours": 0,
    }

init_key("fourh", empty_tracker())
init_key("fourh_manual_override", False)

for k in [
    "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
    "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
    "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
    "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
    "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
    "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
    "m4h_gearbox_total"
]:
    init_key(k, 0)

init_key("fourh_block", four_hour_blocks()[0])

def sum_list(lst):
    return int(sum(lst)) if lst else 0

def add_current_hour_to_4h():
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

    tr["gearbox"].append(st.session_state.get("hr_gearbox_total", 0))

    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    for k in [
        "m4h_fwd_load","m4h_mid_load","m4h_aft_load","m4h_poop_load",
        "m4h_fwd_disch","m4h_mid_disch","m4h_aft_disch","m4h_poop_disch",
        "m4h_fwd_restow_load","m4h_mid_restow_load","m4h_aft_restow_load","m4h_poop_restow_load",
        "m4h_fwd_restow_disch","m4h_mid_restow_disch","m4h_aft_restow_disch","m4h_poop_restow_disch",
        "m4h_hatch_fwd_open","m4h_hatch_mid_open","m4h_hatch_aft_open",
        "m4h_hatch_fwd_close","m4h_hatch_mid_close","m4h_hatch_aft_close",
        "m4h_gearbox_total"
    ]:
        st.session_state[k] = 0
        # WhatsApp_Report.py  — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Date & Vessel
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    # Keep as widgets but not reassigning them to session_state directly
    st.text_input("Vessel Name", key="vessel_name")
    st.text_input("Berthed Date", key="berthed_date")
    st.text_input("First Lift (optional)", key="first_lift")
    st.text_input("Last Lift (optional)", key="last_lift")
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

# persist meta when user edits vessel/plan fields (button)
if st.button("💾 Save Vessel / Plan Metadata"):
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "first_lift": st.session_state.get("first_lift", ""),
        "last_lift": st.session_state.get("last_lift", ""),
        "planned_load": int(st.session_state["planned_load"]),
        "planned_disch": int(st.session_state["planned_disch"]),
        "planned_restow_load": int(st.session_state["planned_restow_load"]),
        "planned_restow_disch": int(st.session_state["planned_restow_disch"]),
        "opening_load": int(st.session_state["opening_load"]),
        "opening_disch": int(st.session_state["opening_disch"]),
        "opening_restow_load": int(st.session_state["opening_restow_load"]),
        "opening_restow_disch": int(st.session_state["opening_restow_disch"]),
    })
    # save both DB and file fallback
    save_cumulative_db(cumulative)
    save_cumulative_file(cumulative)
    st.success("Metadata and plan saved to persistent storage. You can open the app on other devices with same DB file (or same server).")

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
# Crane Moves (Load & Discharge) - keep collapsibles as requested
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
# Gearbox (hourly, not cumulative)
# --------------------------
with st.expander("⚙️ Gearbox (Hourly Only)"):
    st.number_input("Gearbox Total (this hour only)", min_value=0, key="hr_gearbox_total")

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
    # WhatsApp_Report.py  — PART 3 / 5

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
        "gearbox": ss.get("hr_gearbox_total", 0)
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearbox (this hour only):** {split['gearbox']}")

# --------------------------
# WhatsApp (Hourly) – original monospace template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template_text():
    # compute remaining taking opening into account (opening is already included into cumulative on first apply logic)
    done_load = cumulative.get("done_load", 0)
    done_disch = cumulative.get("done_disch", 0)
    done_restow_load = cumulative.get("done_restow_load", 0)
    done_restow_disch = cumulative.get("done_restow_disch", 0)

    # combine with current session hour values so template shows what will be after pressing Generate
    ss = st.session_state
    hour_load = ss["hr_fwd_load"] + ss["hr_mid_load"] + ss["hr_aft_load"] + ss["hr_poop_load"]
    hour_disch = ss["hr_fwd_disch"] + ss["hr_mid_disch"] + ss["hr_aft_disch"] + ss["hr_poop_disch"]
    hour_restow_load = ss["hr_fwd_restow_load"] + ss["hr_mid_restow_load"] + ss["hr_aft_restow_load"] + ss["hr_poop_restow_load"]
    hour_restow_disch = ss["hr_fwd_restow_disch"] + ss["hr_mid_restow_disch"] + ss["hr_aft_restow_disch"] + ss["hr_poop_restow_disch"]
    hour_hatch_open = ss["hr_hatch_fwd_open"] + ss["hr_hatch_mid_open"] + ss["hr_hatch_aft_open"]
    hour_hatch_close = ss["hr_hatch_fwd_close"] + ss["hr_hatch_mid_close"] + ss["hr_hatch_aft_close"]

    future_done_load = done_load + hour_load
    future_done_disch = done_disch + hour_disch
    future_done_restow_load = done_restow_load + hour_restow_load
    future_done_restow_disch = done_restow_disch + hour_restow_disch

    # ensure plan/remaining logic (if done > plan, adjust plan)
    planned_load = st.session_state["planned_load"]
    planned_disch = st.session_state["planned_disch"]
    planned_restow_load = st.session_state["planned_restow_load"]
    planned_restow_disch = st.session_state["planned_restow_disch"]

    if future_done_load > planned_load:
        planned_load = future_done_load
    if future_done_disch > planned_disch:
        planned_disch = future_done_disch
    if future_done_restow_load > planned_restow_load:
        planned_restow_load = future_done_restow_load
    if future_done_restow_disch > planned_restow_disch:
        planned_restow_disch = future_done_restow_disch

    remain_load = planned_load - future_done_load
    remain_disch = planned_disch - future_done_disch
    remain_restow_load = planned_restow_load - future_done_restow_load
    remain_restow_disch = planned_restow_disch - future_done_restow_disch

    # format template (keep same style as original)
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
FWD       {ss['hr_fwd_load']:>5}     {ss['hr_fwd_disch']:>5}
MID       {ss['hr_mid_load']:>5}     {ss['hr_mid_disch']:>5}
AFT       {ss['hr_aft_load']:>5}     {ss['hr_aft_disch']:>5}
POOP      {ss['hr_poop_load']:>5}     {ss['hr_poop_disch']:>5}
_________________________
*Restows*
           Load   Discharge
FWD       {ss['hr_fwd_restow_load']:>5}     {ss['hr_fwd_restow_disch']:>5}
MID       {ss['hr_mid_restow_load']:>5}     {ss['hr_mid_restow_disch']:>5}
AFT       {ss['hr_aft_restow_load']:>5}     {ss['hr_aft_restow_disch']:>5}
POOP      {ss['hr_poop_restow_load']:>5}     {ss['hr_poop_restow_disch']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {future_done_load:>5}      {future_done_disch:>5}
Remain     {remain_load:>5}      {remain_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {future_done_restow_load:>5}      {future_done_restow_disch:>5}
Remain     {remain_restow_load:>5}      {remain_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {ss['hr_hatch_fwd_open']:>5}      {ss['hr_hatch_fwd_close']:>5}
MID       {ss['hr_hatch_mid_open']:>5}      {ss['hr_hatch_mid_close']:>5}
AFT       {ss['hr_hatch_aft_open']:>5}      {ss['hr_hatch_aft_close']:>5}
_________________________
*Gearbox*
Total     {ss.get('hr_gearbox_total',0):>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# Generate Hourly (single button)
# --------------------------
def on_generate_hourly():
    ss = st.session_state

    # compute hour totals (int safety)
    hour = {
        "fwd_load": int(ss["hr_fwd_load"]), "mid_load": int(ss["hr_mid_load"]),
        "aft_load": int(ss["hr_aft_load"]), "poop_load": int(ss["hr_poop_load"]),
        "fwd_disch": int(ss["hr_fwd_disch"]), "mid_disch": int(ss["hr_mid_disch"]),
        "aft_disch": int(ss["hr_aft_disch"]), "poop_disch": int(ss["hr_poop_disch"]),
        "fwd_restow_load": int(ss["hr_fwd_restow_load"]), "mid_restow_load": int(ss["hr_mid_restow_load"]),
        "aft_restow_load": int(ss["hr_aft_restow_load"]), "poop_restow_load": int(ss["hr_poop_restow_load"]),
        "fwd_restow_disch": int(ss["hr_fwd_restow_disch"]), "mid_restow_disch": int(ss["hr_mid_restow_disch"]),
        "aft_restow_disch": int(ss["hr_aft_restow_disch"]), "poop_restow_disch": int(ss["hr_poop_restow_disch"]),
        "hatch_fwd_open": int(ss["hr_hatch_fwd_open"]), "hatch_mid_open": int(ss["hr_hatch_mid_open"]), "hatch_aft_open": int(ss["hr_hatch_aft_open"]),
        "hatch_fwd_close": int(ss["hr_hatch_fwd_close"]), "hatch_mid_close": int(ss["hr_hatch_mid_close"]), "hatch_aft_close": int(ss["hr_hatch_aft_close"]),
        "gearbox": int(ss.get("hr_gearbox_total", 0))
    }

    # apply opening balances only once per cumulative record
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] = cumulative.get("done_load", 0) + int(ss.get("opening_load", 0))
        cumulative["done_disch"] = cumulative.get("done_disch", 0) + int(ss.get("opening_disch", 0))
        cumulative["done_restow_load"] = cumulative.get("done_restow_load", 0) + int(ss.get("opening_restow_load", 0))
        cumulative["done_restow_disch"] = cumulative.get("done_restow_disch", 0) + int(ss.get("opening_restow_disch", 0))
        cumulative["_openings_applied"] = True

    # update cumulative with hour values
    cumulative["done_load"] = cumulative.get("done_load", 0) + (hour["fwd_load"] + hour["mid_load"] + hour["aft_load"] + hour["poop_load"])
    cumulative["done_disch"] = cumulative.get("done_disch", 0) + (hour["fwd_disch"] + hour["mid_disch"] + hour["aft_disch"] + hour["poop_disch"])
    cumulative["done_restow_load"] = cumulative.get("done_restow_load", 0) + (hour["fwd_restow_load"] + hour["mid_restow_load"] + hour["aft_restow_load"] + hour["poop_restow_load"])
    cumulative["done_restow_disch"] = cumulative.get("done_restow_disch", 0) + (hour["fwd_restow_disch"] + hour["mid_restow_disch"] + hour["aft_restow_disch"] + hour["poop_restow_disch"])
    cumulative["done_hatch_open"] = cumulative.get("done_hatch_open", 0) + (hour["hatch_fwd_open"] + hour["hatch_mid_open"] + hour["hatch_aft_open"])
    cumulative["done_hatch_close"] = cumulative.get("done_hatch_close", 0) + (hour["hatch_fwd_close"] + hour["hatch_mid_close"] + hour["hatch_aft_close"])

    # keep cumulative never less than opening (sanity)
    for key in ["done_load","done_disch","done_restow_load","done_restow_disch","done_hatch_open","done_hatch_close"]:
        cumulative[key] = max(0, int(cumulative.get(key, 0)))

    # enforce plan vs done: if done > plan adjust plan (so remain never negative)
    if cumulative["done_load"] > ss["planned_load"]:
        ss["planned_load"] = cumulative["done_load"]
    if cumulative["done_disch"] > ss["planned_disch"]:
        ss["planned_disch"] = cumulative["done_disch"]
    if cumulative["done_restow_load"] > ss["planned_restow_load"]:
        ss["planned_restow_load"] = cumulative["done_restow_load"]
    if cumulative["done_restow_disch"] > ss["planned_restow_disch"]:
        ss["planned_restow_disch"] = cumulative["done_restow_disch"]

    # persist cumulative/meta
    cumulative.update({
        "vessel_name": ss["vessel_name"],
        "berthed_date": ss["berthed_date"],
        "planned_load": int(ss["planned_load"]),
        "planned_disch": int(ss["planned_disch"]),
        "planned_restow_load": int(ss["planned_restow_load"]),
        "planned_restow_disch": int(ss["planned_restow_disch"]),
        "opening_load": int(ss["opening_load"]),
        "opening_disch": int(ss["opening_disch"]),
        "opening_restow_load": int(ss["opening_restow_load"]),
        "opening_restow_disch": int(ss["opening_restow_disch"]),
        "first_lift": ss.get("first_lift",""),
        "last_lift": ss.get("last_lift",""),
        "last_hour": ss["hourly_time"]
    })
    save_cumulative_db(cumulative)
    save_cumulative_file(cumulative)

    # add hour to 4h rolling tracker and persist that in session only
    add_current_hour_to_4h()

    # auto-advance hour safely
    st.session_state["hourly_time_override"] = next_hour_label(ss["hourly_time"])

    # return the text so caller can show it
    return generate_hourly_template_text()

# Single Generate button (no preview)
colA, colB = st.columns([1,2])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        txt = on_generate_hourly()
        st.code(txt, language="text")
with colB:
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

# Reset HOURLY inputs + safe hour advance
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "hr_gearbox_total"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)
# WhatsApp_Report.py  — PART 4 / 5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts,
             index=block_opts.index(st.session_state["fourh_block"]),
             key="fourh_block")

def computed_4h():
    tr = st.session_state["fourh"]
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
        "gearbox": sum_list(tr["gearbox"])
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
        "gearbox": ss.get("m4h_gearbox_total", 0)
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    st.write(f"**Gearbox total (last 4 hrs summed):** {calc['gearbox']}")

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
        st.number_input("4H Gearbox Total (manual)", min_value=0, key="m4h_gearbox_total")

# Populate manual 4H from hourly tracker
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    calc_vals = computed_4h()
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

    st.session_state["m4h_gearbox_total"] = calc_vals["gearbox"]

    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template_text():
    ss = st.session_state
    remaining_load  = ss["planned_load"]  - cumulative.get("done_load", 0) - ss.get("opening_load", 0)
    remaining_disch = ss["planned_disch"] - cumulative.get("done_disch", 0) - ss.get("opening_disch", 0)
    remaining_restow_load  = ss["planned_restow_load"]  - cumulative.get("done_restow_load", 0) - ss.get("opening_restow_load", 0)
    remaining_restow_disch = ss["planned_restow_disch"] - cumulative.get("done_restow_disch", 0) - ss.get("opening_restow_disch", 0)

    t = f"""\
{ss['vessel_name']}
Berthed {ss['berthed_date']}

Date: {ss['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {ss['fourh_block']}
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
Plan       {ss['planned_load']:>5}      {ss['planned_disch']:>5}
Done       {cumulative.get('done_load',0):>5}      {cumulative.get('done_disch',0):>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load    Disch
Plan       {ss['planned_restow_load']:>5}      {ss['planned_restow_disch']:>5}
Done       {cumulative.get('done_restow_load',0):>5}      {cumulative.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Gearbox*
Total       {vals4h.get('gearbox',0):>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(ss["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template_text(), language="text")

st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB, cC = st.columns([1,1,1])
with cA:
    if st.button("👁️ Preview 4-Hourly Template Only"):
        st.code(generate_4h_template_text(), language="text")
with cB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template_text()
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
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")
        # WhatsApp_Report.py  — PART 5 / 5

st.markdown("---")

# Master reset: resets everything including DB meta back to default fallback values
if st.button("⚠️ MASTER RESET (clear all cumulative & trackers)"):
    # reset session values
    for k in list(st.session_state.keys()):
        # preserve UI controls keys that shouldn't be wiped? We'll just clear all related keys we manage:
        pass
    # clear our DB meta and file fallback to initial
    initial = load_cumulative_file_fallback()
    try:
        save_cumulative_db(initial)
        save_cumulative_file(initial)
    except Exception:
        pass
    # re-initialize in-memory cumulative
    cumulative.clear()
    cumulative.update(initial)
    # reset session state keys to reflect initial
    st.experimental_rerun()

st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs."
)

# On app load ensure session reflects DB cumulative (so device switching retains last save on same server)
# We load DB meta again to update UI if DB changed externally.
latest = load_cumulative_db()
if latest:
    # update session state but avoid overwriting user's current edits in-session.
    # Only update the persistent meta fields
    for fld in ["vessel_name","berthed_date","planned_load","planned_disch","planned_restow_load","planned_restow_disch","opening_load","opening_disch","opening_restow_load","opening_restow_disch","first_lift","last_lift","last_hour"]:
        if fld in latest:
            # only update session if different from session (user hasn't just edited it)
            if st.session_state.get(fld) != latest.get(fld):
                st.session_state[fld] = latest.get(fld)

# small final save to keep DB and file in sync
save_cumulative_db(cumulative)
save_cumulative_file(cumulative)
