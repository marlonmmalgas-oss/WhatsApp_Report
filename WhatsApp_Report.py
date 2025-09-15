import streamlit as st
import sqlite3
import json
import os
import urllib.parse
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Vessel Hourly & 4-Hourly Moves", layout="wide")

# --------------------------
# CONSTANTS & DB
# --------------------------
SAVE_DB = "vessel_report.db"
TZ = pytz.timezone("Africa/Johannesburg")

def init_db():
    conn = sqlite3.connect(SAVE_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    # ensure cumulative exists
    cur.execute("SELECT value FROM meta WHERE key='cumulative'")
    row = cur.fetchone()
    if not row:
        initial = {
            "done_load": 0, "done_disch": 0,
            "done_restow_load": 0, "done_restow_disch": 0,
            "done_hatch_open": 0, "done_hatch_close": 0,
            "gearbox": 0,
            "vessel_name": "", "berthed_date": "",
            "planned_load": 0, "planned_disch": 0,
            "planned_restow_load": 0, "planned_restow_disch": 0,
            "opening_load": 0, "opening_disch": 0,
            "opening_restow_load": 0, "opening_restow_disch": 0,
            "first_lift": "", "last_lift": "",
            "last_hour": "06h00-07h00"
        }
        cur.execute("INSERT INTO meta (key,value) VALUES (?,?)",
                    ("cumulative", json.dumps(initial)))
        conn.commit()
    conn.close()

def load_db():
    conn = sqlite3.connect(SAVE_DB)
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key='cumulative'")
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {}

def save_db(cum):
    conn = sqlite3.connect(SAVE_DB)
    cur = conn.cursor()
    cur.execute("UPDATE meta SET value=? WHERE key='cumulative'",
                (json.dumps(cum),))
    conn.commit()
    conn.close()

cumulative = load_db()
init_db()

# --------------------------
# HELPERS
# --------------------------
def hour_range_list():
    base = datetime(2000,1,1,6,0)
    return [(base+timedelta(hours=i)).strftime("%Hh00-%Hh00") for i in range(25)][:-1]

def next_hour_label(current):
    hours = hour_range_list()
    if current in hours:
        idx = hours.index(current)
        if idx+1 < len(hours):
            return hours[idx+1]
    return hours[0]

def four_hour_blocks():
    return [
        "06h00-10h00","10h00-14h00","14h00-18h00",
        "18h00-22h00","22h00-02h00","02h00-06h00"
    ]

def sum_list(lst): return sum(lst) if lst else 0

# --------------------------
# INIT SESSION
# --------------------------
defaults = {
    "vessel_name": cumulative.get("vessel_name",""),
    "berthed_date": cumulative.get("berthed_date",""),
    "report_date": datetime.now(TZ).date(),
    "planned_load": cumulative.get("planned_load",0),
    "planned_disch": cumulative.get("planned_disch",0),
    "planned_restow_load": cumulative.get("planned_restow_load",0),
    "planned_restow_disch": cumulative.get("planned_restow_disch",0),
    "opening_load": cumulative.get("opening_load",0),
    "opening_disch": cumulative.get("opening_disch",0),
    "opening_restow_load": cumulative.get("opening_restow_load",0),
    "opening_restow_disch": cumulative.get("opening_restow_disch",0),
    "first_lift": cumulative.get("first_lift",""),
    "last_lift": cumulative.get("last_lift",""),
    "hourly_time": cumulative.get("last_hour","06h00-07h00"),
    "gearbox": 0,
    "fourh_block": four_hour_blocks()[0]
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v
        st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# --------------------------
# Vessel Info
# --------------------------
left,right=st.columns([2,1])
with left:
    st.subheader("🚢 Vessel Info")
    st.text_input("Vessel Name",key="vessel_name")
    st.text_input("Berthed Date",key="berthed_date")
    st.text_input("First Lift",key="first_lift")
    st.text_input("Last Lift",key="last_lift")
with right:
    st.subheader("📅 Report Date")
    st.date_input("Select Report Date",key="report_date")

# --------------------------
# Plan & Opening
# --------------------------
with st.expander("📋 Plan Totals & Opening Balance (Internal Only)",expanded=False):
    c1,c2=st.columns(2)
    with c1:
        st.number_input("Planned Load",min_value=0,key="planned_load")
        st.number_input("Planned Discharge",min_value=0,key="planned_disch")
        st.number_input("Planned Restow Load",min_value=0,key="planned_restow_load")
        st.number_input("Planned Restow Discharge",min_value=0,key="planned_restow_disch")
    with c2:
        st.number_input("Opening Load (Deduction)",min_value=0,key="opening_load")
        st.number_input("Opening Discharge (Deduction)",min_value=0,key="opening_disch")
        st.number_input("Opening Restow Load (Deduction)",min_value=0,key="opening_restow_load")
        st.number_input("Opening Restow Discharge (Deduction)",min_value=0,key="opening_restow_disch")

# --------------------------
# Hour Selector
# --------------------------
if st.session_state.get("hourly_time") not in hour_range_list():
    st.session_state["hourly_time"]=hour_range_list()[0]
st.selectbox("⏱ Select Hourly Time",options=hour_range_list(),
             index=hour_range_list().index(st.session_state["hourly_time"]),
             key="hourly_time")
st.markdown(f"### 🕐 Hourly Moves Input ({st.session_state['hourly_time']})")

# --------------------------
# Crane Moves
# --------------------------
with st.expander("🏗️ Crane Moves"):
    with st.expander("📦 Load"):
        st.number_input("FWD Load",min_value=0,key="hr_fwd_load")
        st.number_input("MID Load",min_value=0,key="hr_mid_load")
        st.number_input("AFT Load",min_value=0,key="hr_aft_load")
        st.number_input("POOP Load",min_value=0,key="hr_poop_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Discharge",min_value=0,key="hr_fwd_disch")
        st.number_input("MID Discharge",min_value=0,key="hr_mid_disch")
        st.number_input("AFT Discharge",min_value=0,key="hr_aft_disch")
        st.number_input("POOP Discharge",min_value=0,key="hr_poop_disch")

# --------------------------
# Restows
# --------------------------
with st.expander("🔄 Restows"):
    with st.expander("📦 Load"):
        st.number_input("FWD Restow Load",min_value=0,key="hr_fwd_restow_load")
        st.number_input("MID Restow Load",min_value=0,key="hr_mid_restow_load")
        st.number_input("AFT Restow Load",min_value=0,key="hr_aft_restow_load")
        st.number_input("POOP Restow Load",min_value=0,key="hr_poop_restow_load")
    with st.expander("📤 Discharge"):
        st.number_input("FWD Restow Discharge",min_value=0,key="hr_fwd_restow_disch")
        st.number_input("MID Restow Discharge",min_value=0,key="hr_mid_restow_disch")
        st.number_input("AFT Restow Discharge",min_value=0,key="hr_aft_restow_disch")
        st.number_input("POOP Restow Discharge",min_value=0,key="hr_poop_restow_disch")

# --------------------------
# Hatch Moves
# --------------------------
with st.expander("🛡️ Hatch Moves"):
    with st.expander("🔓 Open"):
        st.number_input("FWD Hatch Open",min_value=0,key="hr_hatch_fwd_open")
        st.number_input("MID Hatch Open",min_value=0,key="hr_hatch_mid_open")
        st.number_input("AFT Hatch Open",min_value=0,key="hr_hatch_aft_open")
    with st.expander("🔒 Close"):
        st.number_input("FWD Hatch Close",min_value=0,key="hr_hatch_fwd_close")
        st.number_input("MID Hatch Close",min_value=0,key="hr_hatch_mid_close")
        st.number_input("AFT Hatch Close",min_value=0,key="hr_hatch_aft_close")

# --------------------------
# Gearbox
# --------------------------
with st.expander("⚙️ Gearbox Moves"):
    st.number_input("Total Gearbox Moves",min_value=0,key="gearbox")
    # --------------------------
# Hourly Totals Tracker (split by position)
# --------------------------
def hourly_totals_split():
    ss = st.session_state
    return {
        "load": {
            "FWD": int(ss.get("hr_fwd_load", 0)),
            "MID": int(ss.get("hr_mid_load", 0)),
            "AFT": int(ss.get("hr_aft_load", 0)),
            "POOP": int(ss.get("hr_poop_load", 0)),
        },
        "disch": {
            "FWD": int(ss.get("hr_fwd_disch", 0)),
            "MID": int(ss.get("hr_mid_disch", 0)),
            "AFT": int(ss.get("hr_aft_disch", 0)),
            "POOP": int(ss.get("hr_poop_disch", 0)),
        },
        "restow_load": {
            "FWD": int(ss.get("hr_fwd_restow_load", 0)),
            "MID": int(ss.get("hr_mid_restow_load", 0)),
            "AFT": int(ss.get("hr_aft_restow_load", 0)),
            "POOP": int(ss.get("hr_poop_restow_load", 0)),
        },
        "restow_disch": {
            "FWD": int(ss.get("hr_fwd_restow_disch", 0)),
            "MID": int(ss.get("hr_mid_restow_disch", 0)),
            "AFT": int(ss.get("hr_aft_restow_disch", 0)),
            "POOP": int(ss.get("hr_poop_restow_disch", 0)),
        },
        "hatch_open": {
            "FWD": int(ss.get("hr_hatch_fwd_open", 0)),
            "MID": int(ss.get("hr_hatch_mid_open", 0)),
            "AFT": int(ss.get("hr_hatch_aft_open", 0)),
        },
        "hatch_close": {
            "FWD": int(ss.get("hr_hatch_fwd_close", 0)),
            "MID": int(ss.get("hr_hatch_mid_close", 0)),
            "AFT": int(ss.get("hr_hatch_aft_close", 0)),
        },
    }

with st.expander("🧮 Hourly Totals (split by FWD / MID / AFT / POOP)"):
    split = hourly_totals_split()
    st.write(f"**Load**       — FWD {split['load']['FWD']} | MID {split['load']['MID']} | AFT {split['load']['AFT']} | POOP {split['load']['POOP']}")
    st.write(f"**Discharge**  — FWD {split['disch']['FWD']} | MID {split['disch']['MID']} | AFT {split['disch']['AFT']} | POOP {split['disch']['POOP']}")
    st.write(f"**Restow Load**— FWD {split['restow_load']['FWD']} | MID {split['restow_load']['MID']} | AFT {split['restow_load']['AFT']} | POOP {split['restow_load']['POOP']}")
    st.write(f"**Restow Disch**— FWD {split['restow_disch']['FWD']} | MID {split['restow_disch']['MID']} | AFT {split['restow_disch']['AFT']} | POOP {split['restow_disch']['POOP']}")
    st.write(f"**Hatch Open** — FWD {split['hatch_open']['FWD']} | MID {split['hatch_open']['MID']} | AFT {split['hatch_open']['AFT']}")
    st.write(f"**Hatch Close**— FWD {split['hatch_close']['FWD']} | MID {split['hatch_close']['MID']} | AFT {split['hatch_close']['AFT']}")

# --------------------------
# WhatsApp (Hourly) – template & generation
# --------------------------
st.subheader("📱 Send Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number (with country code, e.g., 27761234567)", key="wa_num_hour")
st.text_input("Or enter WhatsApp Group Link (optional)", key="wa_grp_hour")

def render_remaining_and_done_for_display(cum):
    """
    Return tuples (display_done, display_remain, effective_plan)
    display_done = cumulative done + openings (openings shown as already done on template)
    effective_plan: if cumulative done > planned then increase planned to match done (to avoid negative remain)
    """
    plan_load = int(st.session_state.get("planned_load", 0))
    done_load = int(cum.get("done_load", 0))
    opening_load = int(st.session_state.get("opening_load", 0))
    # display_done includes opening (but opening only added once permanently to cum when processed)
    display_done = done_load + opening_load
    if display_done > plan_load:
        # adjust plan so remain never negative (display only; also update stored plan to keep consistency)
        plan_load = display_done
    remain = plan_load - display_done
    return display_done, remain, plan_load

def generate_hourly_template_text():
    # ensure openings applied once to cumulative BEFORE creating template display:
    # (but we don't apply openings here; openings are shown on template via render function)
    display_done_load, remain_load, eff_plan_load = render_remaining_and_done_for_display(cumulative)
    display_done_restow, remain_restow, eff_plan_restow = (cumulative.get("done_restow_load",0)+int(st.session_state.get("opening_restow_load",0)),
                                                           st.session_state.get("planned_restow_load",0)- (cumulative.get("done_restow_load",0)+int(st.session_state.get("opening_restow_load",0))),
                                                           st.session_state.get("planned_restow_load",0))
    # but keep consistent: if negative, set adjust
    if remain_restow < 0:
        eff_plan_restow = cumulative.get("done_restow_load",0) + int(st.session_state.get("opening_restow_load",0))
        remain_restow = 0

    # build template string (keep exact format you had)
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
Plan       {eff_plan_load:>5}      {st.session_state['planned_disch']:>5}
Done       {display_done_load:>5}      {cumulative.get('done_disch',0):>5}
Remain     {remain_load:>5}      {st.session_state['planned_disch'] - cumulative.get('done_disch',0):>5}
_________________________
*Restows*
           Load   Disch
Plan       {eff_plan_restow:>5}      {st.session_state['planned_restow_disch']:>5}
Done       {cumulative.get('done_restow_load',0)+int(st.session_state.get('opening_restow_load',0)):>5}      {cumulative.get('done_restow_disch',0):>5}
Remain     {max(0, eff_plan_restow - (cumulative.get('done_restow_load',0)+int(st.session_state.get('opening_restow_load',0)))):>5}      {st.session_state['planned_restow_disch'] - cumulative.get('done_restow_disch',0):>5}
_________________________
*Hatch Moves*
           Open   Close
FWD       {st.session_state['hr_hatch_fwd_open']:>5}      {st.session_state['hr_hatch_fwd_close']:>5}
MID       {st.session_state['hr_hatch_mid_open']:>5}      {st.session_state['hr_hatch_mid_close']:>5}
AFT       {st.session_state['hr_hatch_aft_open']:>5}      {st.session_state['hr_hatch_aft_close']:>5}
_________________________
*Gearbox*
Total Gearboxes this hour: {st.session_state.get('gearbox',0)}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state.get("idle_entries", [])):
        tmpl += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return tmpl

# Apply opening balances to cumulative only ONCE (safe operation) when generating first time
def apply_openings_once():
    if not cumulative.get("_openings_applied", False):
        cumulative["done_load"] = cumulative.get("done_load",0) + int(st.session_state.get("opening_load",0))
        cumulative["done_disch"] = cumulative.get("done_disch",0) + int(st.session_state.get("opening_disch",0))
        cumulative["done_restow_load"] = cumulative.get("done_restow_load",0) + int(st.session_state.get("opening_restow_load",0))
        cumulative["done_restow_disch"] = cumulative.get("done_restow_disch",0) + int(st.session_state.get("opening_restow_disch",0))
        cumulative["_openings_applied"] = True
        save_db(cumulative)

# Add current hour to 4h tracker (keeps last 4)
def add_current_hour_to_4h():
    tr = st.session_state.get("fourh", None)
    if tr is None:
        tr = empty_tracker()
    # append splits (integers)
    tr["fwd_load"].append(int(st.session_state.get("hr_fwd_load",0)))
    tr["mid_load"].append(int(st.session_state.get("hr_mid_load",0)))
    tr["aft_load"].append(int(st.session_state.get("hr_aft_load",0)))
    tr["poop_load"].append(int(st.session_state.get("hr_poop_load",0)))

    tr["fwd_disch"].append(int(st.session_state.get("hr_fwd_disch",0)))
    tr["mid_disch"].append(int(st.session_state.get("hr_mid_disch",0)))
    tr["aft_disch"].append(int(st.session_state.get("hr_aft_disch",0)))
    tr["poop_disch"].append(int(st.session_state.get("hr_poop_disch",0)))

    tr["fwd_restow_load"].append(int(st.session_state.get("hr_fwd_restow_load",0)))
    tr["mid_restow_load"].append(int(st.session_state.get("hr_mid_restow_load",0)))
    tr["aft_restow_load"].append(int(st.session_state.get("hr_aft_restow_load",0)))
    tr["poop_restow_load"].append(int(st.session_state.get("hr_poop_restow_load",0)))

    tr["fwd_restow_disch"].append(int(st.session_state.get("hr_fwd_restow_disch",0)))
    tr["mid_restow_disch"].append(int(st.session_state.get("hr_mid_restow_disch",0)))
    tr["aft_restow_disch"].append(int(st.session_state.get("hr_aft_restow_disch",0)))
    tr["poop_restow_disch"].append(int(st.session_state.get("hr_poop_restow_disch",0)))

    tr["hatch_fwd_open"].append(int(st.session_state.get("hr_hatch_fwd_open",0)))
    tr["hatch_mid_open"].append(int(st.session_state.get("hr_hatch_mid_open",0)))
    tr["hatch_aft_open"].append(int(st.session_state.get("hr_hatch_aft_open",0)))

    tr["hatch_fwd_close"].append(int(st.session_state.get("hr_hatch_fwd_close",0)))
    tr["hatch_mid_close"].append(int(st.session_state.get("hr_hatch_mid_close",0)))
    tr["hatch_aft_close"].append(int(st.session_state.get("hr_hatch_aft_close",0)))

    # trim to last 4 and update count
    for k in tr.keys():
        if isinstance(tr[k], list):
            tr[k] = tr[k][-4:]
    tr["count_hours"] = min(4, tr.get("count_hours",0)+1)
    st.session_state["fourh"] = tr

def empty_tracker():
    return {
        "fwd_load": [], "mid_load": [], "aft_load": [], "poop_load": [],
        "fwd_disch": [], "mid_disch": [], "aft_disch": [], "poop_disch": [],
        "fwd_restow_load": [], "mid_restow_load": [], "aft_restow_load": [], "poop_restow_load": [],
        "fwd_restow_disch": [], "mid_restow_disch": [], "aft_restow_disch": [], "poop_restow_disch": [],
        "hatch_fwd_open": [], "hatch_mid_open": [], "hatch_aft_open": [],
        "hatch_fwd_close": [], "hatch_mid_close": [], "hatch_aft_close": [],
        "count_hours": 0
    }

def reset_4h_tracker():
    st.session_state["fourh"] = empty_tracker()

# --------------------------
# Generate Hourly: central action
# --------------------------
def on_generate_hourly():
    # 1) Apply opening balances once
    apply_openings_once()

    # 2) Read hourly sums
    hour_load = int(st.session_state.get("hr_fwd_load",0)) + int(st.session_state.get("hr_mid_load",0)) + int(st.session_state.get("hr_aft_load",0)) + int(st.session_state.get("hr_poop_load",0))
    hour_disch = int(st.session_state.get("hr_fwd_disch",0)) + int(st.session_state.get("hr_mid_disch",0)) + int(st.session_state.get("hr_aft_disch",0)) + int(st.session_state.get("hr_poop_disch",0))
    hour_restow_load = int(st.session_state.get("hr_fwd_restow_load",0)) + int(st.session_state.get("hr_mid_restow_load",0)) + int(st.session_state.get("hr_aft_restow_load",0)) + int(st.session_state.get("hr_poop_restow_load",0))
    hour_restow_disch = int(st.session_state.get("hr_fwd_restow_disch",0)) + int(st.session_state.get("hr_mid_restow_disch",0)) + int(st.session_state.get("hr_aft_restow_disch",0)) + int(st.session_state.get("hr_poop_restow_disch",0))
    hour_hatch_open = int(st.session_state.get("hr_hatch_fwd_open",0)) + int(st.session_state.get("hr_hatch_mid_open",0)) + int(st.session_state.get("hr_hatch_aft_open",0))
    hour_hatch_close = int(st.session_state.get("hr_hatch_fwd_close",0)) + int(st.session_state.get("hr_hatch_mid_close",0)) + int(st.session_state.get("hr_hatch_aft_close",0))

    # 3) Update cumulative (add hourly net to stored cumulative)
    cumulative["done_load"] = cumulative.get("done_load",0) + hour_load
    cumulative["done_disch"] = cumulative.get("done_disch",0) + hour_disch
    cumulative["done_restow_load"] = cumulative.get("done_restow_load",0) + hour_restow_load
    cumulative["done_restow_disch"] = cumulative.get("done_restow_disch",0) + hour_restow_disch
    cumulative["done_hatch_open"] = cumulative.get("done_hatch_open",0) + hour_hatch_open
    cumulative["done_hatch_close"] = cumulative.get("done_hatch_close",0) + hour_hatch_close

    # 4) Prevent done > plan causing negative remain: if done exceeds plan, bump plan to match done (persisted)
    if cumulative["done_load"] + int(st.session_state.get("opening_load",0)) > int(st.session_state.get("planned_load",0)):
        st.session_state["planned_load"] = cumulative["done_load"] + int(st.session_state.get("opening_load",0))
    if cumulative["done_restow_load"] + int(st.session_state.get("opening_restow_load",0)) > int(st.session_state.get("planned_restow_load",0)):
        st.session_state["planned_restow_load"] = cumulative["done_restow_load"] + int(st.session_state.get("opening_restow_load",0))

    # 5) Persist vessel meta + cumulative
    cumulative.update({
        "vessel_name": st.session_state.get("vessel_name",""),
        "berthed_date": st.session_state.get("berthed_date",""),
        "planned_load": int(st.session_state.get("planned_load",0)),
        "planned_disch": int(st.session_state.get("planned_disch",0)),
        "planned_restow_load": int(st.session_state.get("planned_restow_load",0)),
        "planned_restow_disch": int(st.session_state.get("planned_restow_disch",0)),
        "opening_load": int(st.session_state.get("opening_load",0)),
        "opening_disch": int(st.session_state.get("opening_disch",0)),
        "opening_restow_load": int(st.session_state.get("opening_restow_load",0)),
        "opening_restow_disch": int(st.session_state.get("opening_restow_disch",0)),
        "first_lift": st.session_state.get("first_lift",""),
        "last_lift": st.session_state.get("last_lift",""),
        "last_hour": st.session_state.get("hourly_time","06h00-07h00")
    })
    save_db(cumulative)

    # 6) add current hourly splits into 4h tracker
    add_current_hour_to_4h()

    # 7) Advance hour using override so selectbox doesn't try to set widget during render
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state.get("hourly_time","06h00-07h00"))

    # 8) Return generated template text (for showing to user)
    return generate_hourly_template_text()
    # Buttons for hourly actions
colA,colB,colC = st.columns([1,1,1])
with colA:
    if st.button("✅ Generate Hourly Template & Update Totals"):
        txt = on_generate_hourly()
        st.code(txt, language="text")
with colB:
    if st.button("👁️ Preview Hourly Template Only"):
        st.code(generate_hourly_template_text(), language="text")
with colC:
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

# Reset HOURLY inputs + safe hour advance (no experimental_rerun)
def reset_hourly_inputs():
    for k in [
        "hr_fwd_load","hr_mid_load","hr_aft_load","hr_poop_load",
        "hr_fwd_disch","hr_mid_disch","hr_aft_disch","hr_poop_disch",
        "hr_fwd_restow_load","hr_mid_restow_load","hr_aft_restow_load","hr_poop_restow_load",
        "hr_fwd_restow_disch","hr_mid_restow_disch","hr_aft_restow_disch","hr_poop_restow_disch",
        "hr_hatch_fwd_open","hr_hatch_mid_open","hr_hatch_aft_open",
        "hr_hatch_fwd_close","hr_hatch_mid_close","hr_hatch_aft_close",
        "gearbox"
    ]:
        st.session_state[k] = 0
    st.session_state["hourly_time_override"] = next_hour_label(st.session_state.get("hourly_time","06h00-07h00"))

st.button("🔄 Reset Hourly Inputs (and advance hour)", on_click=reset_hourly_inputs)

# --------------------------
# 4-Hourly Tracker & Report
# --------------------------
st.markdown("---")
st.header("📊 4-Hourly Tracker & Report")

# pick 4-hour block label safely
block_opts = four_hour_blocks()
if st.session_state.get("fourh_block") not in block_opts:
    st.session_state["fourh_block"] = block_opts[0]
st.selectbox("Select 4-Hour Block", options=block_opts, index=block_opts.index(st.session_state["fourh_block"]), key="fourh_block")

def computed_4h():
    tr = st.session_state.get("fourh", empty_tracker())
    return {
        "fwd_load": sum_list(tr["fwd_load"]), "mid_load": sum_list(tr["mid_load"]), "aft_load": sum_list(tr["aft_load"]), "poop_load": sum_list(tr["poop_load"]),
        "fwd_disch": sum_list(tr["fwd_disch"]), "mid_disch": sum_list(tr["mid_disch"]), "aft_disch": sum_list(tr["aft_disch"]), "poop_disch": sum_list(tr["poop_disch"]),
        "fwd_restow_load": sum_list(tr["fwd_restow_load"]), "mid_restow_load": sum_list(tr["mid_restow_load"]), "aft_restow_load": sum_list(tr["aft_restow_load"]), "poop_restow_load": sum_list(tr["poop_restow_load"]),
        "fwd_restow_disch": sum_list(tr["fwd_restow_disch"]), "mid_restow_disch": sum_list(tr["mid_restow_disch"]), "aft_restow_disch": sum_list(tr["aft_restow_disch"]), "poop_restow_disch": sum_list(tr["poop_restow_disch"]),
        "hatch_fwd_open": sum_list(tr["hatch_fwd_open"]), "hatch_mid_open": sum_list(tr["hatch_mid_open"]), "hatch_aft_open": sum_list(tr["hatch_aft_open"]),
        "hatch_fwd_close": sum_list(tr["hatch_fwd_close"]), "hatch_mid_close": sum_list(tr["hatch_mid_close"]), "hatch_aft_close": sum_list(tr["hatch_aft_close"]),
        "count_hours": tr.get("count_hours",0)
    }

# manual override inputs (kept collapsed under same look)
with st.expander("✏️ Manual Override 4-Hour Totals", expanded=False):
    st.checkbox("Use manual totals instead of auto-calculated", key="fourh_manual_override")
    c1,c2,c3,c4 = st.columns(4)
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

# populate manual fields from computed tracker
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

    st.session_state["fourh_manual_override"] = True
    st.success("Manual 4-hour inputs populated from hourly tracker; manual override enabled.")

# show auto-calculated 4h
with st.expander("🧮 4-Hour Totals (auto-calculated)"):
    calc = computed_4h()
    st.write(f"**Crane Moves – Load:** FWD {calc['fwd_load']} | MID {calc['mid_load']} | AFT {calc['aft_load']} | POOP {calc['poop_load']}")
    st.write(f"**Crane Moves – Discharge:** FWD {calc['fwd_disch']} | MID {calc['mid_disch']} | AFT {calc['aft_disch']} | POOP {calc['poop_disch']}")
    st.write(f"**Restows – Load:** FWD {calc['fwd_restow_load']} | MID {calc['mid_restow_load']} | AFT {calc['aft_restow_load']} | POOP {calc['poop_restow_load']}")
    st.write(f"**Restows – Discharge:** FWD {calc['fwd_restow_disch']} | MID {calc['mid_restow_disch']} | AFT {calc['aft_restow_disch']} | POOP {calc['poop_restow_disch']}")
    st.write(f"**Hatch Open:** FWD {calc['hatch_fwd_open']} | MID {calc['hatch_mid_open']} | AFT {calc['hatch_aft_open']}")
    st.write(f"**Hatch Close:** FWD {calc['hatch_fwd_close']} | MID {calc['hatch_mid_close']} | AFT {calc['hatch_aft_close']}")
    st.write(f"**Hours in tracker:** {calc.get('count_hours',0)}")

# 4-hour template generator
def generate_4h_template(vals4h):
    # compute remaining same as hourly (plan/ done)
    display_done_load = cumulative.get('done_load',0) + int(st.session_state.get("opening_load",0))
    remain_load = max(0, int(st.session_state.get("planned_load",0)) - display_done_load)
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
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {st.session_state['planned_load']:>5}      {st.session_state['planned_disch']:>5}
Done       {display_done_load:>5}      {cumulative.get('done_disch',0):>5}
Remain     {remain_load:>5}      {st.session_state['planned_disch'] - cumulative.get('done_disch',0):>5}
_________________________
*Hatch Moves*
             Open         Close
FWD          {vals4h['hatch_fwd_open']:>5}          {vals4h['hatch_fwd_close']:>5}
MID          {vals4h['hatch_mid_open']:>5}          {vals4h['hatch_mid_close']:>5}
AFT          {vals4h['hatch_aft_open']:>5}          {vals4h['hatch_aft_close']:>5}
_________________________
*Idle / Delays*
"""
    for i, idle in enumerate(st.session_state.get("idle_entries", [])):
        t += f"{i+1}. {idle['crane']} {idle['start']}-{idle['end']} : {idle['delay']}\n"
    return t

vals4h = manual_4h() if st.session_state.get("fourh_manual_override", False) else computed_4h()
st.code(generate_4h_template(vals4h), language="text")
st.subheader("📱 Send 4-Hourly Report to WhatsApp")
st.text_input("Enter WhatsApp Number for 4H report (optional)", key="wa_num_4h")
st.text_input("Or enter WhatsApp Group Link for 4H report (optional)", key="wa_grp_4h")

cA,cB,cC = st.columns([1,1,1])
with cA:
    if st.button("👁️ Preview 4-Hourly Template Only"):
        st.code(generate_4h_template(vals4h), language="text")
with cB:
    if st.button("📤 Open WhatsApp (4-Hourly)"):
        t = generate_4h_template(vals4h)
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

# --------------------------
# Master Reset (wipe everything)
# --------------------------
def master_reset():
    # clear DB file safely
    try:
        if os.path.exists(SAVE_DB):
            os.remove(SAVE_DB)
    except Exception as e:
        st.error(f"Failed to remove DB: {e}")
        return
    # clear session state keys
    keys = list(st.session_state.keys())
    for k in keys:
        del st.session_state[k]
    # re-init DB and reload defaults
    init_db()
    newcum = load_db()
    for k,v in newcum.items():
        st.session_state[k]=v
    st.success("Master reset completed — app returned to initial state.")

st.markdown("---")
st.caption(
    "• Hourly: Use **Generate Hourly Template** to add the hour to cumulative and the 4-hour tracker. "
    "• 4-Hourly: Use **Manual Override** only if the auto tracker missed something. "
    "• Resets do not loop; they just clear values. "
    "• Hour advances automatically after generating hourly or when you reset hourly inputs."
)

st.button("🧯 MASTER RESET (wipe everything)", on_click=master_reset)
