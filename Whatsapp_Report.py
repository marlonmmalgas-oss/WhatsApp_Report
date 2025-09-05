import streamlit as st
import sqlite3
import urllib.parse
from datetime import datetime
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# DATABASE SETUP
# --------------------------
DB_FILE = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS report_state (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_state(key, value):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("REPLACE INTO report_state (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def load_state(key, default=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM report_state WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return type(default)(row[0]) if row else default

def save_bulk(state_dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for k, v in state_dict.items():
        cur.execute("REPLACE INTO report_state (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()

def load_bulk(defaults: dict):
    state = {}
    for k, v in defaults.items():
        state[k] = load_state(k, v)
    return state

init_db()

# --------------------------
# DEFAULTS
# --------------------------
DEFAULTS = {
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
}

# load persisted state
cumulative = load_bulk(DEFAULTS)

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

# base info
init_key("report_date", datetime.now(TZ).date())
for k in DEFAULTS.keys():
    init_key(k, cumulative[k])

# HOURLY inputs
for k in [
    "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
    "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
    "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
    "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
    "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
    "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
]:
    init_key(k, 0)

# idle
init_key("num_idle_entries", 0)
init_key("idle_entries", [])

# time selection
hours_list = hour_range_list()
init_key("hourly_time", cumulative.get("last_hour", hours_list[0]))

# 4-hour tracker
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

# --------------------------
# HELPERS
# --------------------------
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

    # keep only last 4 hours
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr["count_hours"] + 1)

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()
    # --------------------------
# UI – VESSEL INFO
# --------------------------
st.title("📝 Vessel Hourly & 4-Hourly WhatsApp Report")

with st.expander("⚓ Vessel Information", expanded=True):
    st.text_input("Vessel Name", key="vessel_name", on_change=lambda: save_state("vessel_name", st.session_state["vessel_name"]))
    st.text_input("Berthed Date & Time", key="berthed_date", on_change=lambda: save_state("berthed_date", st.session_state["berthed_date"]))
    st.date_input("Report Date", key="report_date", on_change=lambda: save_state("report_date", st.session_state["report_date"]))

# --------------------------
# UI – PLANNED TOTALS & OPENING BALANCE
# --------------------------
with st.expander("📦 Planned Totals & Opening Balance", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Planned Load", min_value=0, key="planned_load", on_change=lambda: save_state("planned_load", st.session_state["planned_load"]))
        st.number_input("Opening Load", min_value=0, key="opening_load", on_change=lambda: save_state("opening_load", st.session_state["opening_load"]))
    with c2:
        st.number_input("Planned Discharge", min_value=0, key="planned_disch", on_change=lambda: save_state("planned_disch", st.session_state["planned_disch"]))
        st.number_input("Opening Discharge", min_value=0, key="opening_disch", on_change=lambda: save_state("opening_disch", st.session_state["opening_disch"]))
    with c3:
        st.number_input("Planned Restow Load", min_value=0, key="planned_restow_load", on_change=lambda: save_state("planned_restow_load", st.session_state["planned_restow_load"]))
        st.number_input("Opening Restow Load", min_value=0, key="opening_restow_load", on_change=lambda: save_state("opening_restow_load", st.session_state["opening_restow_load"]))
        st.number_input("Planned Restow Disch", min_value=0, key="planned_restow_disch", on_change=lambda: save_state("planned_restow_disch", st.session_state["planned_restow_disch"]))
        st.number_input("Opening Restow Disch", min_value=0, key="opening_restow_disch", on_change=lambda: save_state("opening_restow_disch", st.session_state["opening_restow_disch"]))

st.markdown("---")

# --------------------------
# UI – HOURLY INPUTS
# --------------------------
st.header("⏱ Hourly Tracker")

st.selectbox("Select Hour", options=hour_range_list(), key="hourly_time",
             index=hour_range_list().index(st.session_state["hourly_time"]),
             on_change=lambda: save_state("last_hour", st.session_state["hourly_time"]))

with st.expander("🧮 Hourly Crane Moves & Restows", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Load FWD", min_value=0, key="hr_fwd_load")
        st.number_input("Disch FWD", min_value=0, key="hr_fwd_disch")
        st.number_input("Rst Load FWD", min_value=0, key="hr_fwd_restow_load")
        st.number_input("Rst Disch FWD", min_value=0, key="hr_fwd_restow_disch")
        st.number_input("Hatch Open FWD", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("Hatch Close FWD", min_value=0, key="hr_hatch_fwd_close")
    with c2:
        st.number_input("Load MID", min_value=0, key="hr_mid_load")
        st.number_input("Disch MID", min_value=0, key="hr_mid_disch")
        st.number_input("Rst Load MID", min_value=0, key="hr_mid_restow_load")
        st.number_input("Rst Disch MID", min_value=0, key="hr_mid_restow_disch")
        st.number_input("Hatch Open MID", min_value=0, key="hr_hatch_mid_open")
        st.number_input("Hatch Close MID", min_value=0, key="hr_hatch_mid_close")
    with c3:
        st.number_input("Load AFT", min_value=0, key="hr_aft_load")
        st.number_input("Disch AFT", min_value=0, key="hr_aft_disch")
        st.number_input("Rst Load AFT", min_value=0, key="hr_aft_restow_load")
        st.number_input("Rst Disch AFT", min_value=0, key="hr_aft_restow_disch")
        st.number_input("Hatch Open AFT", min_value=0, key="hr_hatch_aft_open")
        st.number_input("Hatch Close AFT", min_value=0, key="hr_hatch_aft_close")
    with c4:
        st.number_input("Load POOP", min_value=0, key="hr_poop_load")
        st.number_input("Disch POOP", min_value=0, key="hr_poop_disch")
        st.number_input("Rst Load POOP", min_value=0, key="hr_poop_restow_load")
        st.number_input("Rst Disch POOP", min_value=0, key="hr_poop_restow_disch")

# --------------------------
# UI – IDLE ENTRIES
# --------------------------
with st.expander("⚠️ Idle / Delays", expanded=False):
    st.number_input("How many idle entries?", min_value=0, key="num_idle_entries")
    st.session_state["idle_entries"] = []
    for i in range(st.session_state["num_idle_entries"]):
        crane = st.text_input(f"Crane {i+1}", key=f"idle_crane_{i}")
        start = st.text_input(f"Start {i+1}", key=f"idle_start_{i}")
        end = st.text_input(f"End {i+1}", key=f"idle_end_{i}")
        delay = st.text_input(f"Delay {i+1}", key=f"idle_delay_{i}")
        st.session_state["idle_entries"].append({"crane": crane, "start": start, "end": end, "delay": delay})
        # --------------------------
# Hourly Totals Tracker (split by position only)
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
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)", expanded=True):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")

# --------------------------
# WhatsApp (Hourly) – Template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    # compute remaining (accounting for opening balances)
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
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

def on_generate_hourly():
    # sum up this hour
    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]

    # update cumulative totals immediately
    cumulative["done_load"] += int(hour_load)
    cumulative["done_disch"] += int(hour_disch)
    cumulative["done_restow_load"] += int(hour_restow_load)
    cumulative["done_restow_disch"] += int(hour_restow_disch)
    cumulative["done_hatch_open"] += int(hour_hatch_open)
    cumulative["done_hatch_close"] += int(hour_hatch_close)

    # persist info
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
        "last_hour": st.session_state["hourly_time"],
    })
    save_cumulative(cumulative)

    # push into rolling 4-hour tracker
    add_current_hour_to_4h()

    # advance to next hour
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

    # show template immediately
    st.code(generate_hourly_template(), language="text")

# --------------------------
# Only ONE button for hourly generation
# --------------------------
if st.button("✅ Generate Hourly Template & Update Totals"):
    on_generate_hourly()
    st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
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
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"], "aft_load": ss["m4_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"], "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"], "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"], "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"], "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"], "hatch_aft_close": ss["m4h_hatch_aft_close"],
    }

# --------------------------
# Show 4-hourly totals (auto vs manual)
# --------------------------
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
    # keep your inputs for manual mode (unchanged)
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

# pick values based on mode
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

# --------------------------
# Show summary of last 4 hourly splits
# --------------------------
with st.expander("📋 Summary of Last 4 Hourly Splits", expanded=True):
    tr = st.session_state["fourh"]
    for label in ["fwd_load", "mid_load", "aft_load", "poop_load",
                  "fwd_disch", "mid_disch", "aft_disch", "poop_disch"]:
        st.write(f"{label}: {tr[label][-4:] if tr[label] else []}")

# --------------------------
# 4-hour template generation
# --------------------------
def generate_4h_template():
    remaining_load  = st.session_state["planned_load"]  - cumulative["done_load"]  - st.session_state["opening_load"]
    remaining_disch = st.session_state["planned_disch"] - cumulative["done_disch"] - st.session_state["opening_disch"]
    remaining_restow_load  = st.session_state["planned_restow_load"]  - cumulative["done_restow_load"]  - st.session_state["opening_restow_load"]
    remaining_restow_disch = st.session_state["planned_restow_disch"] - cumulative["done_restow_disch"] - st.session_state["opening_restow_disch"]

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
    return t

# --------------------------
# Button to update 4-hourly template
# --------------------------
if st.button("✅ Update 4-Hourly Template"):
    st.code(generate_4h_template(), language="text")
    st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA, cB = st.columns([1,1])
with cA:
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

with cB:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")

# --------------------------
# Closing notes
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs. "
    "• Opening balances automatically deduct from plans and are counted as already done."
)