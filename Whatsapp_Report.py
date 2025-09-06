# WhatsApp_Report.py — PART 1 / 5

import streamlit as st
import sqlite3
import json
import urllib.parse
from datetime import datetime, timedelta
import pytz
import os

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")
TZ = pytz.timezone("Africa/Johannesburg")
DB_FILE = "whatsapp_report.db"

# --------------------------
# DATABASE SETUP
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_state(key, value: dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
    conn.commit()
    conn.close()

def load_state(key, default: dict = None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value FROM state WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return default if default is not None else {}

# --------------------------
# CUMULATIVE SAVE/LOAD HELPERS
# --------------------------
def save_cumulative(cumulative: dict):
    save_state("cumulative_totals", cumulative)

def load_cumulative() -> dict:
    return load_state("cumulative_totals", {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
    })

# --------------------------
# INITIALIZE
# --------------------------
init_db()

if "cumulative" not in st.session_state:
    st.session_state["cumulative"] = load_cumulative()
cumulative = st.session_state["cumulative"]

if "vessel_info" not in st.session_state:
    st.session_state["vessel_info"] = load_state("vessel_info", {
        "vessel_name": "",
        "berthed_date": "",
        "planned_load": 0,
        "planned_disch": 0,
        "planned_restow_load": 0,
        "planned_restow_disch": 0,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0,
    })

# --------------------------
# HELPERS
# --------------------------
def next_hour_label(current: str) -> str:
    try:
        dt = datetime.strptime(current, "%H%M-%H%M")
    except Exception:
        return "0600-0700"
    start = dt + timedelta(hours=1)
    end = start + timedelta(hours=1)
    return f"{start.strftime('%H%M')}-{end.strftime('%H%M')}"

def four_hour_blocks():
    return ["0000-0400","0400-0800","0800-1200","1200-1600","1600-2000","2000-0000"]

def sum_list(lst):
    return sum(lst) if lst else 0

# --------------------------
# META INFO
# --------------------------
st.header("🚢 Vessel Information")
st.text_input("Vessel Name", key="vessel_name")
st.text_input("Berthed Date", key="berthed_date")
st.number_input("Planned Load", min_value=0, key="planned_load")
st.number_input("Planned Discharge", min_value=0, key="planned_disch")
st.number_input("Planned Restow Load", min_value=0, key="planned_restow_load")
st.number_input("Planned Restow Discharge", min_value=0, key="planned_restow_disch")
st.number_input("Opening Load", min_value=0, key="opening_load")
st.number_input("Opening Discharge", min_value=0, key="opening_disch")
st.number_input("Opening Restow Load", min_value=0, key="opening_restow_load")
st.number_input("Opening Restow Discharge", min_value=0, key="opening_restow_disch")

if st.button("💾 Save Vessel Info"):
    st.session_state["vessel_info"] = {
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
    }
    save_state("vessel_info", st.session_state["vessel_info"])
    st.success("Vessel info saved.")
    # WhatsApp_Report.py — PART 2 / 5

st.markdown("---")
st.header("⏱ Hourly Tracker & Report")

# Select report date & hour
st.date_input("Report Date", key="report_date", value=datetime.now(TZ).date())
if "hourly_time" not in st.session_state:
    st.session_state["hourly_time"] = "0600-0700"
st.selectbox("Select Hourly Time", 
             options=[f"{str(h).zfill(2)}00-{str(h+1).zfill(2)}00" for h in range(0,24)],
             index=6, 
             key="hourly_time")

# --------------------------
# HOURLY INPUTS (under collapsibles)
# --------------------------
with st.expander("⚓ Crane Moves"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Load FWD", min_value=0, key="hr_fwd_load")
        st.number_input("Disch FWD", min_value=0, key="hr_fwd_disch")
    with c2:
        st.number_input("Load MID", min_value=0, key="hr_mid_load")
        st.number_input("Disch MID", min_value=0, key="hr_mid_disch")
    with c3:
        st.number_input("Load AFT", min_value=0, key="hr_aft_load")
        st.number_input("Disch AFT", min_value=0, key="hr_aft_disch")
    with c4:
        st.number_input("Load POOP", min_value=0, key="hr_poop_load")
        st.number_input("Disch POOP", min_value=0, key="hr_poop_disch")

with st.expander("📦 Restows"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input("Restow Load FWD", min_value=0, key="hr_fwd_restow_load")
        st.number_input("Restow Disch FWD", min_value=0, key="hr_fwd_restow_disch")
    with c2:
        st.number_input("Restow Load MID", min_value=0, key="hr_mid_restow_load")
        st.number_input("Restow Disch MID", min_value=0, key="hr_mid_restow_disch")
    with c3:
        st.number_input("Restow Load AFT", min_value=0, key="hr_aft_restow_load")
        st.number_input("Restow Disch AFT", min_value=0, key="hr_aft_restow_disch")
    with c4:
        st.number_input("Restow Load POOP", min_value=0, key="hr_poop_restow_load")
        st.number_input("Restow Disch POOP", min_value=0, key="hr_poop_restow_disch")

with st.expander("🔧 Hatch Moves"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Hatch Open FWD", min_value=0, key="hr_hatch_fwd_open")
        st.number_input("Hatch Close FWD", min_value=0, key="hr_hatch_fwd_close")
    with c2:
        st.number_input("Hatch Open MID", min_value=0, key="hr_hatch_mid_open")
        st.number_input("Hatch Close MID", min_value=0, key="hr_hatch_mid_close")
    with c3:
        st.number_input("Hatch Open AFT", min_value=0, key="hr_hatch_aft_open")
        st.number_input("Hatch Close AFT", min_value=0, key="hr_hatch_aft_close")

with st.expander("⏸ Idle / Delays"):
    if "idle_entries" not in st.session_state:
        st.session_state["idle_entries"] = []
    crane = st.text_input("Crane ID")
    start = st.text_input("Start Time")
    end = st.text_input("End Time")
    delay = st.text_input("Reason")
    if st.button("➕ Add Idle/Delay"):
        if crane and start and end and delay:
            st.session_state["idle_entries"].append(
                {"crane": crane, "start": start, "end": end, "delay": delay}
            )
    if st.session_state["idle_entries"]:
        st.table(st.session_state["idle_entries"])
        # WhatsApp_Report.py — PART 3 / 5

# --------------------------
# HOURLY TOTALS (split only)
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
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    if "hourly_accumulated" not in st.session_state:
        st.session_state["hourly_accumulated"] = {
            "load": {"FWD":0,"MID":0,"AFT":0,"POOP":0},
            "disch":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
            "restow_load":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
            "restow_disch":{"FWD":0,"MID":0,"AFT":0,"POOP":0},
            "hatch_open":{"FWD":0,"MID":0,"AFT":0},
            "hatch_close":{"FWD":0,"MID":0,"AFT":0},
        }
    acc = st.session_state["hourly_accumulated"]
    st.write("**Load:**", acc["load"])
    st.write("**Disch:**", acc["disch"])
    st.write("**Restow Load:**", acc["restow_load"])
    st.write("**Restow Disch:**", acc["restow_disch"])
    st.write("**Hatch Open:**", acc["hatch_open"])
    st.write("**Hatch Close:**", acc["hatch_close"])

# --------------------------
# HOURLY TEMPLATE
# --------------------------
def generate_hourly_template():
    ss = st.session_state
    remaining_load  = ss["planned_load"]  - cumulative["done_load"]  - ss["opening_load"]
    remaining_disch = ss["planned_disch"] - cumulative["done_disch"] - ss["opening_disch"]
    remaining_restow_load  = ss["planned_restow_load"]  - cumulative["done_restow_load"]  - ss["opening_restow_load"]
    remaining_restow_disch = ss["planned_restow_disch"] - cumulative["done_restow_disch"] - ss["opening_restow_disch"]

    tmpl = f"""\
{ss['vessel_name']}
Berthed {ss['berthed_date']}

Date: {ss['report_date'].strftime('%d/%m/%Y')}
Hour: {ss['hourly_time']}
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
Plan       {ss['planned_load']:>5}      {ss['planned_disch']:>5}
Done       {cumulative['done_load']:>5}      {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {ss['planned_restow_load']:>5}      {ss['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}      {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {ss['hr_hatch_fwd_open']:>5}      {ss['hr_hatch_fwd_close']:>5}
MID       {ss['hr_hatch_mid_open']:>5}      {ss['hr_hatch_mid_close']:>5}
AFT       {ss['hr_hatch_aft_open']:>5}      {ss['hr_hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(ss["idle_entries"]):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# --------------------------
# GENERATE BUTTON (updates + accumulates immediately)
# --------------------------
def on_generate_hourly():
    ss = st.session_state
    split = hourly_totals_split()

    # accumulate into hourly totals split
    for k in split:
        for pos in split[k]:
            st.session_state["hourly_accumulated"][k][pos] += split[k][pos]

    # update cumulative totals
    cumulative["done_load"] += sum(split["load"].values())
    cumulative["done_disch"] += sum(split["disch"].values())
    cumulative["done_restow_load"] += sum(split["restow_load"].values())
    cumulative["done_restow_disch"] += sum(split["restow_disch"].values())
    cumulative["done_hatch_open"] += sum(split["hatch_open"].values())
    cumulative["done_hatch_close"] += sum(split["hatch_close"].values())

    cumulative["last_hour"] = ss["hourly_time"]
    save_cumulative(cumulative)

    # push into 4-hour tracker
    add_current_hour_to_4h()

    # reset inputs for next hour
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
    ]:
        ss[k] = 0

    # advance hour
    ss["hourly_time"] = next_hour_label(ss["hourly_time"])

if st.button("✅ Generate Hourly Template & Update Totals"):
    hourly_text = generate_hourly_template()
    st.code(hourly_text, language="text")
    on_generate_hourly()
    # WhatsApp_Report.py — PART 4 / 5

st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# --------------------------
# SELECT 4-HOUR BLOCK
# --------------------------
block_opts = four_hour_blocks()
if st.session_state["fourh_block"] not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]

st.selectbox(
    "Select 4-Hour Block",
    options=block_opts,
    index=block_opts.index(st.session_state["fourh_block"]),
    key="fourh_block"
)

# --------------------------
# 4-HOUR TOTALS
# --------------------------
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
    }

# --- AUTO CALCULATED 4H VIEW ---
with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** {calc['fwd_load']} | {calc['mid_load']} | {calc['aft_load']} | {calc['poop_load']}")
    st.write(f"**Crane Moves – Disch:** {calc['fwd_disch']} | {calc['mid_disch']} | {calc['aft_disch']} | {calc['poop_disch']}")
    st.write(f"**Restow Load:** {calc['fwd_restow_load']} | {calc['mid_restow_load']} | {calc['aft_restow_load']} | {calc['poop_restow_load']}")
    st.write(f"**Restow Disch:** {calc['fwd_restow_disch']} | {calc['mid_restow_disch']} | {calc['aft_restow_disch']} | {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** {calc['hatch_fwd_open']} | {calc['hatch_mid_open']} | {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** {calc['hatch_fwd_close']} | {calc['hatch_mid_close']} | {calc['hatch_aft_close']}")

# --- MANUAL OVERRIDE ---
with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto", key="fourh_manual_override")
    cols = st.columns(4)
    labels = ["FWD","MID","AFT","POOP"]
    fields = ["load","disch","restow_load","restow_disch"]
    hatches = ["open","close"]

    for i, pos in enumerate(labels):
        with cols[i]:
            for f in fields:
                st.number_input(f"{pos} {f} 4H", min_value=0, key=f"m4h_{pos.lower()}_{f}")
            if pos != "POOP":
                for h in hatches:
                    st.number_input(f"{pos} Hatch {h} 4H", min_value=0, key=f"m4h_hatch_{pos.lower()}_{h}")

# --------------------------
# FINAL 4H VALUES
# --------------------------
vals4h = manual_4h() if st.session_state["fourh_manual_override"] else computed_4h()

# --------------------------
# 4-HOURLY TEMPLATE
# --------------------------
def generate_4h_template():
    ss = st.session_state
    remaining_load  = ss["planned_load"]  - cumulative["done_load"]  - ss["opening_load"]
    remaining_disch = ss["planned_disch"] - cumulative["done_disch"] - ss["opening_disch"]
    remaining_restow_load  = ss["planned_restow_load"]  - cumulative["done_restow_load"]  - ss["opening_restow_load"]
    remaining_restow_disch = ss["planned_restow_disch"] - cumulative["done_restow_disch"] - ss["opening_restow_disch"]

    t = f"""\
{ss['vessel_name']}
Berthed {ss['berthed_date']}

Date: {ss['report_date'].strftime('%d/%m/%Y')}
4-Hour Block: {ss['fourh_block']}
_________________________
   *4-HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Disch
FWD       {vals4h['fwd_load']:>5}     {vals4h['fwd_disch']:>5}
MID       {vals4h['mid_load']:>5}     {vals4h['mid_disch']:>5}
AFT       {vals4h['aft_load']:>5}     {vals4h['aft_disch']:>5}
POOP      {vals4h['poop_load']:>5}     {vals4h['poop_disch']:>5}
_________________________
*Restows*
           Load   Disch
FWD       {vals4h['fwd_restow_load']:>5}     {vals4h['fwd_restow_disch']:>5}
MID       {vals4h['mid_restow_load']:>5}     {vals4h['mid_restow_disch']:>5}
AFT       {vals4h['aft_restow_load']:>5}     {vals4h['aft_restow_disch']:>5}
POOP      {vals4h['poop_restow_load']:>5}     {vals4h['poop_restow_disch']:>5}
_________________________
   *CUMULATIVE*
_________________________
Plan       {ss['planned_load']:>5}  {ss['planned_disch']:>5}
Done       {cumulative['done_load']:>5}  {cumulative['done_disch']:>5}
Remain     {remaining_load:>5}  {remaining_disch:>5}
_________________________
*Restows*
Plan       {ss['planned_restow_load']:>5}  {ss['planned_restow_disch']:>5}
Done       {cumulative['done_restow_load']:>5}  {cumulative['done_restow_disch']:>5}
Remain     {remaining_restow_load:>5}  {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
FWD   {vals4h['hatch_fwd_open']:>5}   {vals4h['hatch_fwd_close']:>5}
MID   {vals4h['hatch_mid_open']:>5}   {vals4h['hatch_mid_close']:>5}
AFT   {vals4h['hatch_aft_open']:>5}   {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(ss["idle_entries"]):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

st.code(generate_4h_template(), language="text")
# WhatsApp_Report.py — PART 5 / 5

# --------------------------
# SEND 4-HOURLY REPORT
# --------------------------
st.subheader("📱 Send 4-Hourly Report to WhatsApp")

st.text_input("Enter WhatsApp Number (with country code)", key="wa_num_4h")
st.text_input("Or WhatsApp Group Link", key="wa_grp_4h")

c1, c2, c3 = st.columns([1,1,1])

with c1:
    if st.button("✅ Generate & Show 4-Hourly Template"):
        fourh_text = generate_4h_template()
        st.code(fourh_text, language="text")

with c2:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        fourh_text = generate_4h_template()
        wa_text = f"```{fourh_text}```"
        if st.session_state.get("wa_num_4h"):
            link = f"https://wa.me/{st.session_state['wa_num_4h']}?text={urllib.parse.quote(wa_text)}"
            st.markdown(f"[Open WhatsApp]({link})", unsafe_allow_html=True)
        elif st.session_state.get("wa_grp_4h"):
            st.markdown(f"[Open WhatsApp Group]({st.session_state['wa_grp_4h']})", unsafe_allow_html=True)
        else:
            st.info("Enter a WhatsApp number or group link to send.")

with c3:
    if st.button("🔄 Reset 4-Hourly Tracker (clear last 4 hours)"):
        reset_4h_tracker()
        st.success("4-hourly tracker reset.")

# --------------------------
# FOOTER
# --------------------------
st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to update cumulative and push into the 4-hourly tracker. \n"
    "• 4-Hourly: Use **Populate 4-Hourly** if you want manual control, or leave on auto to accumulate hourly inputs. \n"
    "• Opening balances deduct automatically from planned totals when calculating Remaining. \n"
    "• Resets only clear inputs/tracker, they do not affect saved vessel metadata. \n"
    "• Data is persisted in SQLite so it stays across devices/sessions."
)