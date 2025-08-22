# report_app.py
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date, timedelta
import pytz
import pandas as pd
import io

# ---------------- CONFIG ----------------
SAVE_FILE = "vessel_report.json"
SA_TZ = pytz.timezone("Africa/Johannesburg")
st.set_page_config(page_title="Vessel Moves Tracker", layout="wide")

# ---------------- HELPERS ----------------
def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(d):
    with open(SAVE_FILE, "w") as f:
        json.dump(d, f, indent=2)

def hour_label_to_start(label):
    # "06h00 - 07h00" -> 6
    try:
        return int(label.split("h")[0])
    except Exception:
        return None

def parse_block_hours(block_label):
    # returns list of start hours in the block (e.g. 06-10 => [6,7,8,9])
    left, right = block_label.split(" - ")
    s = int(left[:2])
    e = int(right[:2])
    if s < e:
        return list(range(s, e))
    else:
        return list(range(s, 24)) + list(range(0, e))

def now_iso():
    return datetime.now(SA_TZ).isoformat()

def minutes_between(start_str, end_str):
    # expects "HHhMM" or "HH:MM" or "HHMM"
    def to_dt(t):
        t = t.replace("h", ":")
        if ":" not in t:
            t = t[:2] + ":" + t[2:]
        return datetime.strptime(t, "%H:%M")
    s = to_dt(start_str)
    e = to_dt(end_str)
    # if end earlier than start, assume next day
    if e < s:
        e += timedelta(days=1)
    return int((e - s).total_seconds() // 60)

# ---------------- LOAD / INIT ----------------
data = load_data()
defaults = {
    "vessel_name": "MSC NILA",
    "berthed_date": "14/08/2025 @ 10H55",
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
    "hourly_records": [],
    "four_hour_reports": [],
    "idle_logs": [],
    "hourly_last_saved": None
}
for k, v in defaults.items():
    data.setdefault(k, v)
save_data(data)

# ---------------- UI ----------------
st.title("⚓ Vessel Hourly & 4-Hourly Moves Tracker")

# ---- Vessel & Plan (collapsible) ----
st.header("Vessel Info")
colA, colB = st.columns(2)
with colA:
    vessel_name = st.text_input("Vessel Name", value=data["vessel_name"])
    berthed_date = st.text_input("Berthed Date", value=data["berthed_date"])
with colB:
    first_lift = st.text_input("First Lift (time only)", value=data.get("first_lift","18h25"))
    last_lift = st.text_input("Last Lift (time only)", value=data.get("last_lift","10h31"))

with st.expander("Plan Totals & Opening Balances (click to expand)", expanded=False):
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        planned_load = st.number_input("Planned Load", value=int(data["planned_load"]))
        planned_disch = st.number_input("Planned Discharge", value=int(data["planned_disch"]))
        planned_restow_load = st.number_input("Planned Restow Load", value=int(data["planned_restow_load"]))
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=int(data["planned_restow_disch"]))
    with pcol2:
        opening_load = st.number_input("Opening Load (deduction)", value=int(data["opening_load"]))
        opening_disch = st.number_input("Opening Discharge (deduction)", value=int(data["opening_disch"]))
        opening_restow_load = st.number_input("Opening Restow Load (deduction)", value=int(data["opening_restow_load"]))
        opening_restow_disch = st.number_input("Opening Restow Discharge (deduction)", value=int(data["opening_restow_disch"]))

# persist vessel & plan fields
data.update({
    "vessel_name": vessel_name,
    "berthed_date": berthed_date,
    "first_lift": first_lift,
    "last_lift": last_lift,
    "planned_load": int(planned_load),
    "planned_disch": int(planned_disch),
    "planned_restow_load": int(planned_restow_load),
    "planned_restow_disch": int(planned_restow_disch),
    "opening_load": int(opening_load),
    "opening_disch": int(opening_disch),
    "opening_restow_load": int(opening_restow_load),
    "opening_restow_disch": int(opening_restow_disch)
})
save_data(data)

# ---- Hourly Entry ----
st.header("Hourly Entry")

hours = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = data.get("hourly_last_saved") or "06h00 - 07h00"
hour_label = st.selectbox("Hourly slot", hours, index=hours.index(default_hour))

st.markdown("**Grouped inputs** — expand each group to enter numbers.")
# groups as expanders for cleaner UI
with st.expander("Load (FWD / MID / AFT / POOP)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h_fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="h_fwd_load")
    with c2:
        h_mid_load = st.number_input("MID Load", min_value=0, value=0, key="h_mid_load")
    with c3:
        h_aft_load = st.number_input("AFT Load", min_value=0, value=0, key="h_aft_load")
    with c4:
        h_poop_load = st.number_input("POOP Load", min_value=0, value=0, key="h_poop_load")

with st.expander("Discharge (FWD / MID / AFT / POOP)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h_fwd_disch = st.number_input("FWD Disch", min_value=0, value=0, key="h_fwd_disch")
    with c2:
        h_mid_disch = st.number_input("MID Disch", min_value=0, value=0, key="h_mid_disch")
    with c3:
        h_aft_disch = st.number_input("AFT Disch", min_value=0, value=0, key="h_aft_disch")
    with c4:
        h_poop_disch = st.number_input("POOP Disch", min_value=0, value=0, key="h_poop_disch")

with st.expander("Restow Load (FWD / MID / AFT / POOP)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h_fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="h_fwd_restow_load")
    with c2:
        h_mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="h_mid_restow_load")
    with c3:
        h_aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="h_aft_restow_load")
    with c4:
        h_poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="h_poop_restow_load")

with st.expander("Restow Discharge (FWD / MID / AFT / POOP)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        h_fwd_restow_disch = st.number_input("FWD Restow Disch", min_value=0, value=0, key="h_fwd_restow_disch")
    with c2:
        h_mid_restow_disch = st.number_input("MID Restow Disch", min_value=0, value=0, key="h_mid_restow_disch")
    with c3:
        h_aft_restow_disch = st.number_input("AFT Restow Disch", min_value=0, value=0, key="h_aft_restow_disch")
    with c4:
        h_poop_restow_disch = st.number_input("POOP Restow Disch", min_value=0, value=0, key="h_poop_restow_disch")

with st.expander("Hatch Cover Open (FWD / MID / AFT)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        h_hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="h_hatch_fwd_open")
    with c2:
        h_hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="h_hatch_mid_open")
    with c3:
        h_hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="h_hatch_aft_open")

with st.expander("Hatch Cover Close (FWD / MID / AFT)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        h_hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="h_hatch_fwd_close")
    with c2:
        h_hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="h_hatch_mid_close")
    with c3:
        h_hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="h_hatch_aft_close")

# ----- Idle logging (hourly) -----
st.subheader("Idle / Delay (log an event for any crane)")
idle_crane = st.selectbox("Crane", ["FWD", "MID", "AFT", "POOP"])
idle_start = st.text_input("Start time (HHhMM or HH:MM)", value="12h30")
idle_end = st.text_input("End time (HHhMM or HH:MM)", value="12h40")
idle_reasons = [
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
    "Other"
]
idle_reason_choice = st.selectbox("Delay reason", idle_reasons)
idle_reason_custom = ""
if idle_reason_choice == "Other":
    idle_reason_custom = st.text_input("Enter custom delay reason")

if st.button("Add Idle Entry"):
    reason = idle_reason_custom.strip() if idle_reason_choice == "Other" and idle_reason_custom.strip() else idle_reason_choice
    try:
        mins = minutes_between(idle_start, idle_end)
    except Exception:
        st.error("Invalid time format for idle start/end. Use HHhMM or HH:MM (e.g., 12h30 or 12:30).")
        mins = None
    if mins is not None:
        rec = {
            "date": datetime.now(SA_TZ).strftime("%Y-%m-%d"),
            "crane": idle_crane,
            "start": idle_start,
            "end": idle_end,
            "mins": mins,
            "reason": reason,
            "ts": now_iso()
        }
        data.setdefault("idle_logs", []).append(rec)
        save_data(data)
        st.success("Idle entry added.")

# show idle log (today)
st.subheader("Idle Log (all entries)")
idle_df = pd.DataFrame(data.get("idle_logs", []))
if not idle_df.empty:
    st.dataframe(idle_df.sort_values("ts", ascending=False).reset_index(drop=True))
    # delete selected entries
    idx_to_delete = st.multiselect("Select rows (index) to delete from idle log (then press Delete selected)", idle_df.index.tolist())
    if st.button("Delete selected idle entries"):
        if idx_to_delete:
            remaining = [r for i, r in enumerate(data.get("idle_logs", [])) if i not in idx_to_delete]
            data["idle_logs"] = remaining
            save_data(data)
            st.experimental_rerun()
        else:
            st.info("No rows selected.")
else:
    st.write("No idle entries saved yet.")

# ---- Save Hourly Entry button ----
if st.button("Save Hourly Entry"):
    start_hour = hour_label_to_start(hour_label)
    today_str = datetime.now(SA_TZ).strftime("%Y-%m-%d")
    rec = {
        "date": today_str,
        "start_hour": start_hour,
        "hour_label": hour_label,
        "fwd_load": int(h_fwd_load), "mid_load": int(h_mid_load), "aft_load": int(h_aft_load), "poop_load": int(h_poop_load),
        "fwd_disch": int(h_fwd_disch), "mid_disch": int(h_mid_disch), "aft_disch": int(h_aft_disch), "poop_disch": int(h_poop_disch),
        "fwd_restow_load": int(h_fwd_restow_load), "mid_restow_load": int(h_mid_restow_load), "aft_restow_load": int(h_aft_restow_load), "poop_restow_load": int(h_poop_restow_load),
        "fwd_restow_disch": int(h_fwd_restow_disch), "mid_restow_disch": int(h_mid_restow_disch), "aft_restow_disch": int(h_aft_restow_disch), "poop_restow_disch": int(h_poop_restow_disch),
        "hatch_fwd_open": int(h_hatch_fwd_open), "hatch_mid_open": int(h_hatch_mid_open), "hatch_aft_open": int(h_hatch_aft_open),
        "hatch_fwd_close": int(h_hatch_fwd_close), "hatch_mid_close": int(h_hatch_mid_close), "hatch_aft_close": int(h_hatch_aft_close),
        "used_in_4h": False,
        "ts": now_iso()
    }
    data.setdefault("hourly_records", []).append(rec)

    # update cumulative totals
    data["done_load"] = data.get("done_load", 0) + rec["fwd_load"] + rec["mid_load"] + rec["aft_load"] + rec["poop_load"]
    data["done_disch"] = data.get("done_disch", 0) + rec["fwd_disch"] + rec["mid_disch"] + rec["aft_disch"] + rec["poop_disch"]
    data["done_restow_load"] = data.get("done_restow_load", 0) + rec["fwd_restow_load"] + rec["mid_restow_load"] + rec["aft_restow_load"] + rec["poop_restow_load"]
    data["done_restow_disch"] = data.get("done_restow_disch", 0) + rec["fwd_restow_disch"] + rec["mid_restow_disch"] + rec["aft_restow_disch"] + rec["poop_restow_disch"]
    data["done_hatch_open"] = data.get("done_hatch_open", 0) + rec["hatch_fwd_open"] + rec["hatch_mid_open"] + rec["hatch_aft_open"]
    data["done_hatch_close"] = data.get("done_hatch_close", 0) + rec["hatch_fwd_close"] + rec["hatch_mid_close"] + rec["hatch_aft_close"]

    data["hourly_last_saved"] = hour_label
    save_data(data)
    st.success("Hourly entry saved and cumulative updated.")

# ---- Hourly Template preview (always visible) ----
st.header("Hourly Template Preview (always visible)")
last_saved = data.get("hourly_records", [])[-1] if data.get("hourly_records") else None
pv = {
    "hour_label": hour_label,
    "fwd_load": h_fwd_load, "mid_load": h_mid_load, "aft_load": h_aft_load, "poop_load": h_poop_load,
    "fwd_disch": h_fwd_disch, "mid_disch": h_mid_disch, "aft_disch": h_aft_disch, "poop_disch": h_poop_disch,
    "fwd_restow_load": h_fwd_restow_load, "mid_restow_load": h_mid_restow_load, "aft_restow_load": h_aft_restow_load, "poop_restow_load": h_poop_restow_load,
    "fwd_restow_disch": h_fwd_restow_disch, "mid_restow_disch": h_mid_restow_disch, "aft_restow_disch": h_aft_restow_disch, "poop_restow_disch": h_poop_restow_disch,
    "hatch_fwd_open": h_hatch_fwd_open, "hatch_mid_open": h_hatch_mid_open, "hatch_aft_open": h_hatch_aft_open,
    "hatch_fwd_close": h_hatch_fwd_close, "hatch_mid_close": h_hatch_mid_close, "hatch_aft_close": h_hatch_aft_close
}
if last_saved:
    for k in pv.keys():
        if k in last_saved:
            pv[k] = last_saved[k]

remaining_load = data["planned_load"] - data.get("done_load", 0) - data["opening_load"]
remaining_disch = data["planned_disch"] - data.get("done_disch", 0) - data["opening_disch"]
remaining_restow_load = data["planned_restow_load"] - data.get("done_restow_load", 0) - data["opening_restow_load"]
remaining_restow_disch = data["planned_restow_disch"] - data.get("done_restow_disch", 0) - data["opening_restow_disch"]

hourly_template = f"""\
{data['vessel_name']}
Berthed {data['berthed_date']}

First Lift @ {data.get('first_lift','')}
Last Lift @ {data.get('last_lift','')}

{datetime.now(SA_TZ).strftime('%d/%m/%Y')}
{pv['hour_label']}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
            Load   Discharge
FWD        {pv['fwd_load']:>5}     {pv['fwd_disch']:>5}
MID        {pv['mid_load']:>5}     {pv['mid_disch']:>5}
AFT        {pv['aft_load']:>5}     {pv['aft_disch']:>5}
POOP       {pv['poop_load']:>5}     {pv['poop_disch']:>5}
_________________________
*Restows*
            Load   Discharge
FWD        {pv['fwd_restow_load']:>5}     {pv['fwd_restow_disch']:>5}
MID        {pv['mid_restow_load']:>5}     {pv['mid_restow_disch']:>5}
AFT        {pv['aft_restow_load']:>5}     {pv['aft_restow_disch']:>5}
POOP       {pv['poop_restow_load']:>5}     {pv['poop_restow_disch']:>5}
_________________________
      *CUMULATIVE*
_________________________
            Load   Discharge
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
            Load   Discharge
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
            Open    Close
FWD        {pv['hatch_fwd_open']:>5}      {pv['hatch_fwd_close']:>5}
MID        {pv['hatch_mid_open']:>5}      {pv['hatch_mid_close']:>5}
AFT        {pv['hatch_aft_open']:>5}      {pv['hatch_aft_close']:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""
st.code(hourly_template)

# WhatsApp send controls for hourly
st.subheader("Send Hourly Template to WhatsApp")
wa_mode_hour = st.selectbox("Send hourly to", ["Private Number", "Group Link"], key="wa_mode_hour")
if wa_mode_hour == "Private Number":
    wa_number_hour = st.text_input("WhatsApp number (country code)", key="wa_number_hour")
else:
    wa_group_hour = st.text_input("WhatsApp group link (chat.whatsapp.com/...)", key="wa_group_hour")

if st.button("Open WhatsApp (Hourly)"):
    payload = urllib.parse.quote(f"```{hourly_template}```")
    if wa_mode_hour == "Private Number" and wa_number_hour:
        url = f"https://wa.me/{wa_number_hour}?text={payload}"
        st.markdown(f"[Open WhatsApp]({url})", unsafe_allow_html=True)
    elif wa_mode_hour == "Group Link" and wa_group_hour:
        st.markdown(f"[Open WhatsApp Group]({wa_group_hour})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid number or group link.")

# ---- 4-HOURLY SECTION ----
st.header("4-Hourly Report (visible & editable)")

four_blocks = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
sel_block = st.selectbox("Select 4-hour block", four_blocks)
sel_date = st.date_input("Date for 4-hour block", value=datetime.now(SA_TZ).date())
include_used = st.checkbox("Include hourly entries that were already used in a 4H report", value=False)

# find matched hourly records
req_hours = parse_block_hours(sel_block)
sel_date_str = sel_date.strftime("%Y-%m-%d")
matched = []
missing = []
for h in req_hours:
    candidates = [r for r in data.get("hourly_records", []) if r["date"] == sel_date_str and r["start_hour"] == h]
    if not include_used:
        candidates = [r for r in candidates if not r.get("used_in_4h", False)]
    if candidates:
        matched.append(candidates[-1])
    else:
        missing.append(h)

if missing:
    st.info(f"Missing hourly entries for: {', '.join(str(x).zfill(2) for x in missing)}. You can manually edit 4H inputs below.")
else:
    st.success("4-hour sums loaded from hourly entries; you can edit values below.")

# compute auto sums from matched records
def sf(field): return sum(r.get(field, 0) for r in matched)
auto = {
    "fwd_load": sf("fwd_load"), "mid_load": sf("mid_load"), "aft_load": sf("aft_load"), "poop_load": sf("poop_load"),
    "fwd_disch": sf("fwd_disch"), "mid_disch": sf("mid_disch"), "aft_disch": sf("aft_disch"), "poop_disch": sf("poop_disch"),
    "fwd_restow_load": sf("fwd_restow_load"), "mid_restow_load": sf("mid_restow_load"), "aft_restow_load": sf("aft_restow_load"), "poop_restow_load": sf("poop_restow_load"),
    "fwd_restow_disch": sf("fwd_restow_disch"), "mid_restow_disch": sf("mid_restow_disch"), "aft_restow_disch": sf("aft_restow_disch"), "poop_restow_disch": sf("poop_restow_disch"),
    "hatch_fwd_open": sf("hatch_fwd_open"), "hatch_mid_open": sf("hatch_mid_open"), "hatch_aft_open": sf("hatch_aft_open"),
    "hatch_fwd_close": sf("hatch_fwd_close"), "hatch_mid_close": sf("hatch_mid_close"), "hatch_aft_close": sf("hatch_aft_close")
}


# editable 4H inputs prefilled with auto sums
st.subheader("4-Hourly Inputs (prefilled from hourly entries; editable)")
col1, col2 = st.columns(2)
with col1:
    fwd_load_4h = st.number_input("FWD Load (4H)", min_value=0, value=int(auto["fwd_load"]), key="fwd_load_4h")
    mid_load_4h = st.number_input("MID Load (4H)", min_value=0, value=int(auto["mid_load"]), key="mid_load_4h")
    aft_load_4h = st.number_input("AFT Load (4H)", min_value=0, value=int(auto["aft_load"]), key="aft_load_4h")
    poop_load_4h = st.number_input("POOP Load (4H)", min_value=0, value=int(auto["poop_load"]), key="poop_load_4h")
with col2:
    fwd_disch_4h = st.number_input("FWD Disch (4H)", min_value=0, value=int(auto["fwd_disch"]), key="fwd_disch_4h")
    mid_disch_4h = st.number_input("MID Disch (4H)", min_value=0, value=int(auto["mid_disch"]), key="mid_disch_4h")
    aft_disch_4h = st.number_input("AFT Disch (4H)", min_value=0, value=int(auto["aft_disch"]), key="aft_disch_4h")
    poop_disch_4h = st.number_input("POOP Disch (4H)", min_value=0, value=int(auto["poop_disch"]), key="poop_disch_4h")

st.subheader("4-Hourly Restows (editable)")
rc1, rc2 = st.columns(2)
with rc1:
    fwd_restow_load_4h = st.number_input("FWD Restow Load (4H)", min_value=0, value=int(auto["fwd_restow_load"]), key="fwd_restow_load_4h")
    mid_restow_load_4h = st.number_input("MID Restow Load (4H)", min_value=0, value=int(auto["mid_restow_load"]), key="mid_restow_load_4h")
    fwd_restow_disch_4h = st.number_input("FWD Restow Disch (4H)", min_value=0, value=int(auto["fwd_restow_disch"]), key="fwd_restow_disch_4h")
    mid_restow_disch_4h = st.number_input("MID Restow Disch (4H)", min_value=0, value=int(auto["mid_restow_disch"]), key="mid_restow_disch_4h")
with rc2:
    aft_restow_load_4h = st.number_input("AFT Restow Load (4H)", min_value=0, value=int(auto["aft_restow_load"]), key="aft_restow_load_4h")
    poop_restow_load_4h = st.number_input("POOP Restow Load (4H)", min_value=0, value=int(auto["poop_restow_load"]), key="poop_restow_load_4h")
    aft_restow_disch_4h = st.number_input("AFT Restow Disch (4H)", min_value=0, value=int(auto["aft_restow_disch"]), key="aft_restow_disch_4h")
    poop_restow_disch_4h = st.number_input("POOP Restow Disch (4H)", min_value=0, value=int(auto["poop_restow_disch"]), key="poop_restow_disch_4h")

st.subheader("4-Hourly Hatch Moves (editable)")
hh1, hh2, hh3 = st.columns(3)
with hh1:
    hatch_fwd_open_4h = st.number_input("FWD Open (4H)", min_value=0, value=int(auto["hatch_fwd_open"]), key="hatch_fwd_open_4h")
    hatch_fwd_close_4h = st.number_input("FWD Close (4H)", min_value=0, value=int(auto["hatch_fwd_close"]), key="hatch_fwd_close_4h")
with hh2:
    hatch_mid_open_4h = st.number_input("MID Open (4H)", min_value=0, value=int(auto["hatch_mid_open"]), key="hatch_mid_open_4h")
    hatch_mid_close_4h = st.number_input("MID Close (4H)", min_value=0, value=int(auto["hatch_mid_close"]), key="hatch_mid_close_4h")
with hh3:
    hatch_aft_open_4h = st.number_input("AFT Open (4H)", min_value=0, value=int(auto["hatch_aft_open"]), key="hatch_aft_open_4h")
    hatch_aft_close_4h = st.number_input("AFT Close (4H)", min_value=0, value=int(auto["hatch_aft_close"]), key="hatch_aft_close_4h")

# show 4h totals quick check
sum_load_4h = fwd_load_4h + mid_load_4h + aft_load_4h + poop_load_4h
sum_disch_4h = fwd_disch_4h + mid_disch_4h + aft_disch_4h + poop_disch_4h
st.markdown(f"**4H Totals check** — Load: {sum_load_4h}  |  Disch: {sum_disch_4h}")

# 4H template preview
remaining_load_now = data["planned_load"] - data.get("done_load", 0) - data["opening_load"]
remaining_disch_now = data["planned_disch"] - data.get("done_disch", 0) - data["opening_disch"]
remaining_restow_load_now = data["planned_restow_load"] - data.get("done_restow_load", 0) - data["opening_restow_load"]
remaining_restow_disch_now = data["planned_restow_disch"] - data.get("done_restow_disch", 0) - data["opening_restow_disch"]

template_4h = f"""\
{data['vessel_name']}
Berthed {data['berthed_date']}

Date: {sel_date.strftime('%d/%m/%Y')}
4-Hour Block: {sel_block}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
            Load   Discharge
FWD        {fwd_load_4h:>5}     {fwd_disch_4h:>5}
MID        {mid_load_4h:>5}     {mid_disch_4h:>5}
AFT        {aft_load_4h:>5}     {aft_disch_4h:>5}
POOP       {poop_load_4h:>5}     {poop_disch_4h:>5}
_________________________
*Restows*
            Load   Discharge
FWD        {fwd_restow_load_4h:>5}     {fwd_restow_disch_4h:>5}
MID        {mid_restow_load_4h:>5}     {mid_restow_disch_4h:>5}
AFT        {aft_restow_load_4h:>5}     {aft_restow_disch_4h:>5}
POOP       {poop_restow_load_4h:>5}     {poop_restow_disch_4h:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
            Load   Discharge
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load_now:>5}      {remaining_disch_now:>5}
_________________________
*Restows*
            Load   Discharge
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load_now:>5}      {remaining_restow_disch_now:>5}
_________________________
*Hatch Moves*
            Open    Close
FWD        {hatch_fwd_open_4h:>5}      {hatch_fwd_close_4h:>5}
MID        {hatch_mid_open_4h:>5}      {hatch_mid_close_4h:>5}
AFT        {hatch_aft_open_4h:>5}      {hatch_aft_close_4h:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""
st.subheader("4-Hourly Template Preview")
st.code(template_4h)

# Save 4-hourly
if st.button("Save 4-Hourly Report (mark matched hourly entries as used)"):
    report = {
        "date": sel_date_str,
        "block": sel_block,
        "ts": now_iso(),
        "fwd_load": int(fwd_load_4h), "mid_load": int(mid_load_4h), "aft_load": int(aft_load_4h), "poop_load": int(poop_load_4h),
        "fwd_disch": int(fwd_disch_4h), "mid_disch": int(mid_disch_4h), "aft_disch": int(aft_disch_4h), "poop_disch": int(poop_disch_4h),
        "fwd_restow_load": int(fwd_restow_load_4h), "mid_restow_load": int(mid_restow_load_4h), "aft_restow_load": int(aft_restow_load_4h), "poop_restow_load": int(poop_restow_load_4h),
        "fwd_restow_disch": int(fwd_restow_disch_4h), "mid_restow_disch": int(mid_restow_disch_4h), "aft_restow_disch": int(aft_restow_disch_4h), "poop_restow_disch": int(poop_restow_disch_4h),
        "hatch_fwd_open": int(hatch_fwd_open_4h), "hatch_mid_open": int(hatch_mid_open_4h), "hatch_aft_open": int(hatch_aft_open_4h),
        "hatch_fwd_close": int(hatch_fwd_close_4h), "hatch_mid_close": int(hatch_mid_close_4h), "hatch_aft_close": int(hatch_aft_close_4h)
    }
    data.setdefault("four_hour_reports", []).append(report)
    # mark matched hourly records as used if they were matched
    for rec in matched:
        for orig in data.get("hourly_records", []):
            if orig.get("ts") == rec.get("ts"):
                orig["used_in_4h"] = True
    save_data(data)
    st.success("4-hourly saved and matched hourly entries (if any) marked used.")

if st.button("Reset all 'used_in_4h' flags"):
    for rec in data.get("hourly_records", []):
        rec["used_in_4h"] = False
    save_data(data)
    st.success("'used_in_4h' flags reset.")

# Send 4-hourly via WhatsApp
st.subheader("Send 4-Hourly Template to WhatsApp")
wa_mode_4h = st.selectbox("Send 4H to", ["Private Number", "Group Link"], key="wa_mode_4h")
if wa_mode_4h == "Private Number":
    wa_number_4h = st.text_input("WhatsApp number (country code) for 4H", key="wa_number_4h")
else:
    wa_group_4h = st.text_input("WhatsApp group link for 4H", key="wa_group_4h")

if st.button("Open WhatsApp (4H)"):
    payload = urllib.parse.quote(f"```{template_4h}```")
    if wa_mode_4h == "Private Number" and wa_number_4h:
        url = f"https://wa.me/{wa_number_4h}?text={payload}"
        st.markdown(f"[Open WhatsApp]({url})", unsafe_allow_html=True)
    elif wa_mode_4h == "Group Link" and wa_group_4h:
        st.markdown(f"[Open WhatsApp Group]({wa_group_4h})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid number or group link.")

# ---- Export / Download data ----
st.header("Export / Download")
if st.button("Download vessel_report.json"):
    with open(SAVE_FILE, "rb") as f:
        st.download_button("Click to download JSON", f, file_name=SAVE_FILE)

# prepare CSV downloads
if data.get("hourly_records"):
    hr_df = pd.DataFrame(data["hourly_records"])
else:
    hr_df = pd.DataFrame()
if data.get("four_hour_reports"):
    fr_df = pd.DataFrame(data["four_hour_reports"])
else:
    fr_df = pd.DataFrame()
if data.get("idle_logs"):
    idle_df = pd.DataFrame(data["idle_logs"])
else:
    idle_df = pd.DataFrame()

def to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()

col_dl1, col_dl2, col_dl3 = st.columns(3)
with col_dl1:
    if not hr_df.empty:
        st.download_button("Download Hourly CSV", to_csv_bytes(hr_df), file_name="hourly_records.csv", mime="text/csv")
with col_dl2:
    if not fr_df.empty:
        st.download_button("Download 4-Hourly CSV", to_csv_bytes(fr_df), file_name="four_hour_reports.csv", mime="text/csv")
with col_dl3:
    if not idle_df.empty:
        st.download_button("Download Idle Log CSV", to_csv_bytes(idle_df), file_name="idle_logs.csv", mime="text/csv")

st.caption("Data is saved in vessel_report.json. 4-hourly sums are prefilled from hourly saved entries but are editable. Cumulative totals come from saved hourly records and remain consistent.")