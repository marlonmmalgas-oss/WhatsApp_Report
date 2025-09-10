# WhatsApp_Report.py — PART 1 / 5

import streamlit as st
import sqlite3
import json
import urllib.parse
from datetime import datetime, timedelta
import pytz

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")
TZ = pytz.timezone("Africa/Johannesburg")
DB_FILE = "vessel_report.db"

# --------------------------
# DATABASE HANDLERS
# --------------------------
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
    # seed row if empty
    cur.execute("SELECT COUNT(*) FROM meta;")
    if cur.fetchone()[0] == 0:
        base = {
            "vessel_name": "",
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
            "done_load": 0,
            "done_disch": 0,
            "done_restow_load": 0,
            "done_restow_disch": 0,
            "done_hatch_open": 0,
            "done_hatch_close": 0,
            "fourh": {},
            "idle_entries": [],
        }
        cur.execute("INSERT INTO meta (id, json) VALUES (1, ?)", (json.dumps(base),))
        conn.commit()
    conn.close()

def load_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT json FROM meta WHERE id=1;")
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def save_db(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET json=? WHERE id=1;", (json.dumps(data),))
    conn.commit()
    conn.close()

# --------------------------
# INITIALIZE
# --------------------------
init_db()
cumulative = load_db()

if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = "06h00 - 07h00"
if "hourly_time_override" not in st.session_state:
    st.session_state["hourly_time_override"] = None
if "fourh_block" not in st.session_state:
    st.session_state["fourh_block"] = "06h00 - 10h00"
if "fourh_manual_override" not in st.session_state:
    st.session_state["fourh_manual_override"] = False

# --------------------------
# HELPERS
# --------------------------
def next_hour_label(label):
    try:
        start, end = label.split(" - ")
        h1 = int(start.replace("h","").zfill(2)[:2])
        h2 = (h1+1) % 24
        return f"{str(h2).zfill(2)}h00 - {str((h2+1)%24).zfill(2)}h00"
    except:
        return label

def four_hour_blocks():
    return [
        "06h00 - 10h00","10h00 - 14h00","14h00 - 18h00",
        "18h00 - 22h00","22h00 - 02h00","02h00 - 06h00"
    ]

def sum_list(l): return sum(l) if isinstance(l, list) else 0
    # WhatsApp_Report.py — PART 2 / 5

st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Vessel Info Section
# --------------------------
left, right = st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name", key="vessel_name", value=cumulative.get("vessel_name",""))
    st.text_input("Berthed Date", key="berthed_date", value=cumulative.get("berthed_date",""))
    st.text_input("First Lift", key="first_lift", value=cumulative.get("first_lift",""))
    st.text_input("Last Lift", key="last_lift", value=cumulative.get("last_lift",""))
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date", key="report_date", value=datetime.now(TZ).date())

# --------------------------
# Plan Totals & Opening Balance
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Planned Load",  min_value=0, key="planned_load", value=cumulative.get("planned_load",0))
        st.number_input("Planned Discharge", min_value=0, key="planned_disch", value=cumulative.get("planned_disch",0))
        st.number_input("Planned Restow Load",  min_value=0, key="planned_restow_load", value=cumulative.get("planned_restow_load",0))
        st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch", value=cumulative.get("planned_restow_disch",0))
    with c2:
        st.number_input("Opening Load (Deduction)",  min_value=0, key="opening_load", value=cumulative.get("opening_load",0))
        st.number_input("Opening Discharge (Deduction)", min_value=0, key="opening_disch", value=cumulative.get("opening_disch",0))
        st.number_input("Opening Restow Load (Deduction)",  min_value=0, key="opening_restow_load", value=cumulative.get("opening_restow_load",0))
        st.number_input("Opening Restow Discharge (Deduction)", min_value=0, key="opening_restow_disch", value=cumulative.get("opening_restow_disch",0))

# --------------------------
# Hour selector (24h)
# --------------------------
if "hourly_time_override" in st.session_state and st.session_state["hourly_time_override"]:
    st.session_state["hourly_time"] = st.session_state["hourly_time_override"]
    st.session_state["hourly_time_override"] = None

st.selectbox(
    "⏱ Select Hourly Time",
    options=[f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)],
    index=[f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)].index(st.session_state["hourly_time"]),
    key="hourly_time"
)

st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load", min_value=0, key="hr_fwd_load", value=0)
        st.number_input("MID Load", min_value=0, key="hr_mid_load", value=0)
        st.number_input("AFT Load", min_value=0, key="hr_aft_load", value=0)
        st.number_input("POOP Load", min_value=0, key="hr_poop_load", value=0)
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge", min_value=0, key="hr_fwd_disch", value=0)
        st.number_input("MID Discharge", min_value=0, key="hr_mid_disch", value=0)
        st.number_input("AFT Discharge", min_value=0, key="hr_aft_disch", value=0)
        st.number_input("POOP Discharge", min_value=0, key="hr_poop_disch", value=0)

# --------------------------
# Restows
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load", min_value=0, key="hr_fwd_restow_load", value=0)
        st.number_input("MID Restow Load", min_value=0, key="hr_mid_restow_load", value=0)
        st.number_input("AFT Restow Load", min_value=0, key="hr_aft_restow_load", value=0)
        st.number_input("POOP Restow Load", min_value=0, key="hr_poop_restow_load", value=0)
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge", min_value=0, key="hr_fwd_restow_disch", value=0)
        st.number_input("MID Restow Discharge", min_value=0, key="hr_mid_restow_disch", value=0)
        st.number_input("AFT Restow Discharge", min_value=0, key="hr_aft_restow_disch", value=0)
        st.number_input("POOP Restow Discharge", min_value=0, key="hr_poop_restow_disch", value=0)

# --------------------------
# Hatch Moves
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open", min_value=0, key="hr_hatch_fwd_open", value=0)
        st.number_input("MID Hatch Open", min_value=0, key="hr_hatch_mid_open", value=0)
        st.number_input("AFT Hatch Open", min_value=0, key="hr_hatch_aft_open", value=0)
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close", min_value=0, key="hr_hatch_fwd_close", value=0)
        st.number_input("MID Hatch Close", min_value=0, key="hr_hatch_mid_close", value=0)
        st.number_input("AFT Hatch Close", min_value=0, key="hr_hatch_aft_close", value=0)

# --------------------------
# Gearbox Moves (NEW)
# --------------------------
with st.expander("⚙️ Gearbox Moves"):
    st.number_input("Total Gearbox Moves (Hourly)", min_value=0, key="hr_gearbox", value=0)

# --------------------------
# Idle / Delays
# --------------------------
st.subheader("⏸️ Idle / Delays")
idle_options = [
    "Stevedore tea time/shift change","Awaiting cargo","Awaiting AGL operations",
    "Awaiting FPT gang","Awaiting Crane driver","Awaiting onboard stevedores",
    "Windbound","Crane break down/ wipers","Crane break down/ lights",
    "Crane break down/ boom limit","Crane break down","Vessel listing",
    "Struggling to load container","Cell guide struggles","Spreader difficulties",
]
with st.expander("🛑 Idle Entries", expanded=False):
    st.number_input("Number of Idle Entries", min_value=0, max_value=10, key="num_idle_entries", value=0)
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
    # WhatsApp_Report.py — PART 3 / 5

# --------------------------
# Hourly Totals Tracker (split only)
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
        "gearbox": ss["hr_gearbox"],
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")
    st.write(f"**Gearbox Moves:** {split['gearbox']}")

# --------------------------
# WhatsApp (Hourly) – Template
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def generate_hourly_template():
    # Calculate Done including Opening Balance + Hourly moves
    done_load  = cumulative["done_load"] + st.session_state["opening_load"]
    done_disch = cumulative["done_disch"] + st.session_state["opening_disch"]
    done_restow_load  = cumulative["done_restow_load"] + st.session_state["opening_restow_load"]
    done_restow_disch = cumulative["done_restow_disch"] + st.session_state["opening_restow_disch"]

    remain_load  = max(0, st.session_state["planned_load"]  - done_load)
    remain_disch = max(0, st.session_state["planned_disch"] - done_disch)
    remain_restow_load  = max(0, st.session_state["planned_restow_load"]  - done_restow_load)
    remain_restow_disch = max(0, st.session_state["planned_restow_disch"] - done_restow_disch)

    tmpl = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift {st.session_state['first_lift']}
Last Lift {st.session_state['last_lift']}

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
*Gearbox Moves*
Total     {st.session_state['hr_gearbox']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {done_load:>5}      {done_disch:>5}
Remain     {remain_load:>5}      {remain_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {done_restow_load:>5}      {done_restow_disch:>5}
Remain     {remain_restow_load:>5}      {remain_restow_disch:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# Generate Hourly Template & Update
# --------------------------
def on_generate_hourly():
    # Sum up this hour
    hour_load = st.session_state["hr_fwd_load"] + st.session_state["hr_mid_load"] + st.session_state["hr_aft_load"] + st.session_state["hr_poop_load"]
    hour_disch = st.session_state["hr_fwd_disch"] + st.session_state["hr_mid_disch"] + st.session_state["hr_aft_disch"] + st.session_state["hr_poop_disch"]
    hour_restow_load = st.session_state["hr_fwd_restow_load"] + st.session_state["hr_mid_restow_load"] + st.session_state["hr_aft_restow_load"] + st.session_state["hr_poop_restow_load"]
    hour_restow_disch = st.session_state["hr_fwd_restow_disch"] + st.session_state["hr_mid_restow_disch"] + st.session_state["hr_aft_restow_disch"] + st.session_state["hr_poop_restow_disch"]
    hour_hatch_open = st.session_state["hr_hatch_fwd_open"] + st.session_state["hr_hatch_mid_open"] + st.session_state["hr_hatch_aft_open"]
    hour_hatch_close = st.session_state["hr_hatch_fwd_close"] + st.session_state["hr_hatch_mid_close"] + st.session_state["hr_hatch_aft_close"]
    hour_gearbox = st.session_state["hr_gearbox"]

    # Update cumulative immediately
    cumulative["done_load"] += hour_load
    cumulative["done_disch"] += hour_disch
    cumulative["done_restow_load"] += hour_restow_load
    cumulative["done_restow_disch"] += hour_restow_disch
    cumulative["done_hatch_open"] += hour_hatch_open
    cumulative["done_hatch_close"] += hour_hatch_close
    cumulative["done_gearbox"] += hour_gearbox

    # Adjust plan totals if needed (avoid negative remain)
    cumulative["planned_load"] = max(cumulative["planned_load"], cumulative["done_load"] + st.session_state["opening_load"])
    cumulative["planned_disch"] = max(cumulative["planned_disch"], cumulative["done_disch"] + st.session_state["opening_disch"])
    cumulative["planned_restow_load"] = max(cumulative["planned_restow_load"], cumulative["done_restow_load"] + st.session_state["opening_restow_load"])
    cumulative["planned_restow_disch"] = max(cumulative["planned_restow_disch"], cumulative["done_restow_disch"] + st.session_state["opening_restow_disch"])

    # Save vessel meta
    cumulative.update({
        "vessel_name": st.session_state["vessel_name"],
        "berthed_date": st.session_state["berthed_date"],
        "first_lift": st.session_state["first_lift"],
        "last_lift": st.session_state["last_lift"],
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
    save_db(cumulative)

    # Add to rolling 4-hour tracker
    add_current_hour_to_4h()

    # Advance to next hour for next input
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state["hourly_time"])

# Only one button (Generate)
if st.button("✅ Generate Hourly Template & Update Totals"):
    hourly_text = generate_hourly_template()
    st.code(hourly_text, language="text")
    on_generate_hourly()
    # WhatsApp_Report.py — PART 4 / 5

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
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]),
        "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]),
        "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]),
        "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]),
        "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]),
        "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]),
        "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
        "gearbox": sum_list(tr.get("gearbox", [])),
    }

def manual_4h():
    ss = st.session_state
    return {
        "fwd_load": ss["m4h_fwd_load"], "mid_load": ss["m4h_mid_load"],
        "aft_load": ss["m4h_aft_load"], "poop_load": ss["m4h_poop_load"],
        "fwd_disch": ss["m4h_fwd_disch"], "mid_disch": ss["m4h_mid_disch"],
        "aft_disch": ss["m4h_aft_disch"], "poop_disch": ss["m4h_poop_disch"],
        "fwd_restow_load": ss["m4h_fwd_restow_load"], "mid_restow_load": ss["m4h_mid_restow_load"],
        "aft_restow_load": ss["m4h_aft_restow_load"], "poop_restow_load": ss["m4h_poop_restow_load"],
        "fwd_restow_disch": ss["m4h_fwd_restow_disch"], "mid_restow_disch": ss["m4h_mid_restow_disch"],
        "aft_restow_disch": ss["m4h_aft_restow_disch"], "poop_restow_disch": ss["m4h_poop_restow_disch"],
        "hatch_fwd_open": ss["m4h_hatch_fwd_open"], "hatch_mid_open": ss["m4h_hatch_mid_open"],
        "hatch_aft_open": ss["m4h_hatch_aft_open"],
        "hatch_fwd_close": ss["m4h_hatch_fwd_close"], "hatch_mid_close": ss["m4h_hatch_mid_close"],
        "hatch_aft_close": ss["m4h_hatch_aft_close"],
        "gearbox": ss["m4h_gearbox"],
    }

with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    st.write(f"**Gearbox Total (4H):** {calc['gearbox']}")

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
        st.number_input("Gearbox Total 4H", min_value=0, key="m4h_gearbox")

# --- NEW BUTTON: populate manual 4H fields from computed 4H tracker ---
if st.button("⏬ Populate 4-Hourly from Hourly Tracker"):
    calc_vals = computed_4h()
    for k, v in calc_vals.items():
        if f"m4h_{k}" in st.session_state:
            st.session_state[f"m4h_{k}"] = v
    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

def generate_4h_template():
    # Calculate Done including Opening Balance
    done_load  = cumulative["done_load"] + st.session_state["opening_load"]
    done_disch = cumulative["done_disch"] + st.session_state["opening_disch"]
    done_restow_load  = cumulative["done_restow_load"] + st.session_state["opening_restow_load"]
    done_restow_disch = cumulative["done_restow_disch"] + st.session_state["opening_restow_disch"]

    remain_load  = max(0, st.session_state["planned_load"]  - done_load)
    remain_disch = max(0, st.session_state["planned_disch"] - done_disch)
    remain_restow_load  = max(0, st.session_state["planned_restow_load"]  - done_restow_load)
    remain_restow_disch = max(0, st.session_state["planned_restow_disch"] - done_restow_disch)

    t = f"""\
{st.session_state['vessel_name']}
Berthed {st.session_state['berthed_date']}
First Lift {st.session_state['first_lift']}
Last Lift {st.session_state['last_lift']}

Date: {st.session_state['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {st.session_state['fourh_block']}
_________________________
   *4-HOURLY MOVES*
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
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Gearbox Moves*
Total        {vals4h['gearbox']:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {done_load:>5}      {done_disch:>5}
Remain     {remain_load:>5}      {remain_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {st.session_state['planned_restow_load']:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {done_restow_load:>5}      {done_restow_disch:>5}
Remain     {remain_restow_load:>5}      {remain_restow_disch:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
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
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")
        # WhatsApp_Report.py — PART 5 / 5

st.markdown("---")
st.header("🧹 Master Reset & Notes")

# Master reset clears everything: vessel info, hourly, 4-hourly, cumulative, gearboxes
if st.button("⚠️ MASTER RESET (All Data)"):
    reset_all()
    st.success("All vessel data, hourly, 4-hourly, gearboxes and cumulative progress reset completely.")

st.text_area("📝 Notes (optional)", key="notes")

st.markdown("---")
st.caption("Vessel WhatsApp Report Generator — Streamlit App with SQLite Persistence")
