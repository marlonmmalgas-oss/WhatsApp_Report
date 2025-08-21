# report_app.py
import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date
import pytz

# --------- Config & Helpers ----------
SAVE_FILE = "vessel_report.json"
SA_TZ = pytz.timezone("Africa/Johannesburg")

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
    # "06h00 - 10h00" -> [6,7,8,9]
    left, right = block_label.split(" - ")
    s = int(left[:2])
    e = int(right[:2])
    if s < e:
        return list(range(s, e))
    else:
        # wrap-around e.g. 22 - 02
        return list(range(s, 24)) + list(range(0, e))

def now_iso():
    return datetime.now(SA_TZ).isoformat()

# --------- Load / initialize data ----------
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
    "hourly_records": [],      # saved hourly entries
    "four_hour_reports": [],   # saved 4-hour reports
    "hourly_last_saved": None
}
for k, v in defaults.items():
    data.setdefault(k, v)
save_data(data)  # ensure file exists & defaults written

# --------- Streamlit UI ----------
st.set_page_config(page_title="Hourly & 4-Hourly Report", layout="centered")
st.title("Vessel Hourly & 4-Hourly Moves Tracker")

# ----- Vessel & Plan (persistent editable) -----
st.header("Vessel Info (editable)")
c1, c2 = st.columns(2)
with c1:
    vessel_name = st.text_input("Vessel Name", value=data["vessel_name"])
    berthed_date = st.text_input("Berthed Date", value=data["berthed_date"])
with c2:
    first_lift = st.text_input("First Lift (time only)", value=data.get("first_lift", "18h25"))
    last_lift = st.text_input("Last Lift (time only)", value=data.get("last_lift", "10h31"))

st.header("Plan Totals & Opening Balances (internal only)")
p1, p2 = st.columns(2)
with p1:
    planned_load = st.number_input("Planned Load", value=int(data["planned_load"]))
    planned_disch = st.number_input("Planned Discharge", value=int(data["planned_disch"]))
    planned_restow_load = st.number_input("Planned Restow Load", value=int(data["planned_restow_load"]))
    planned_restow_disch = st.number_input("Planned Restow Discharge", value=int(data["planned_restow_disch"]))
with p2:
    opening_load = st.number_input("Opening Load (Deduction)", value=int(data["opening_load"]))
    opening_disch = st.number_input("Opening Discharge (Deduction)", value=int(data["opening_disch"]))
    opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=int(data["opening_restow_load"]))
    opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=int(data["opening_restow_disch"]))

# persist changes immediately
data.update({
    "vessel_name": vessel_name,
    "berthed_date": berthed_date,
    "first_lift": first_lift,
    "last_lift": last_lift,
    "planned_load": planned_load,
    "planned_disch": planned_disch,
    "planned_restow_load": planned_restow_load,
    "planned_restow_disch": planned_restow_disch,
    "opening_load": opening_load,
    "opening_disch": opening_disch,
    "opening_restow_load": opening_restow_load,
    "opening_restow_disch": opening_restow_disch
})
save_data(data)

# ----- Hourly input -----
st.header("Hourly Inputs")
hours = [f"{str(h).zfill(2)}h00 - {str((h+1)%24).zfill(2)}h00" for h in range(24)]
default_hour = data.get("hourly_last_saved") or "06h00 - 07h00"
hour_label = st.selectbox("Select hourly time", hours, index=hours.index(default_hour))

st.markdown("Enter moves for this hourly slot and press **Save Hourly Entry**. Saved hourly entries update the cumulative totals used in templates.")
colf, colm, cola, colp = st.columns(4)
with colf:
    h_fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="h_fwd_load")
    h_fwd_disch = st.number_input("FWD Disch", min_value=0, value=0, key="h_fwd_disch")
with colm:
    h_mid_load = st.number_input("MID Load", min_value=0, value=0, key="h_mid_load")
    h_mid_disch = st.number_input("MID Disch", min_value=0, value=0, key="h_mid_disch")
with cola:
    h_aft_load = st.number_input("AFT Load", min_value=0, value=0, key="h_aft_load")
    h_aft_disch = st.number_input("AFT Disch", min_value=0, value=0, key="h_aft_disch")
with colp:
    h_poop_load = st.number_input("POOP Load", min_value=0, value=0, key="h_poop_load")
    h_poop_disch = st.number_input("POOP Disch", min_value=0, value=0, key="h_poop_disch")

st.subheader("Restows (hourly)")
r1, r2 = st.columns(2)
with r1:
    h_fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="h_fwd_restow_load")
    h_fwd_restow_disch = st.number_input("FWD Restow Disch", min_value=0, value=0, key="h_fwd_restow_disch")
    h_mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="h_mid_restow_load")
    h_mid_restow_disch = st.number_input("MID Restow Disch", min_value=0, value=0, key="h_mid_restow_disch")
with r2:
    h_aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="h_aft_restow_load")
    h_aft_restow_disch = st.number_input("AFT Restow Disch", min_value=0, value=0, key="h_aft_restow_disch")
    h_poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="h_poop_restow_load")
    h_poop_restow_disch = st.number_input("POOP Restow Disch", min_value=0, value=0, key="h_poop_restow_disch")

st.subheader("Hatch Moves (hourly)")
hc1, hc2, hc3 = st.columns(3)
with hc1:
    h_hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="h_hatch_fwd_open")
    h_hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="h_hatch_fwd_close")
with hc2:
    h_hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="h_hatch_mid_open")
    h_hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="h_hatch_mid_close")
with hc3:
    h_hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="h_hatch_aft_open")
    h_hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="h_hatch_aft_close")

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

# ----- Hourly Template (always visible) -----
st.header("Hourly Template (preview)")
# prefer last-saved values for preview if available
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
    # show last saved values in preview (keeps template straight after save)
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
           Load   Disch
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {pv['hatch_fwd_open']:>5}      {pv['hatch_fwd_close']:>5}
MID        {pv['hatch_mid_open']:>5}      {pv['hatch_mid_close']:>5}
AFT        {pv['hatch_aft_open']:>5}      {pv['hatch_aft_close']:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""
st.code(hourly_template)

# ---------- WhatsApp (Hourly) ----------
st.subheader("Send Hourly Template")
wa_mode_hour = st.selectbox("Choose send mode", ["Private Number", "Group Link"], key="wa_mode_hour")
if wa_mode_hour == "Private Number":
    wa_number_hour = st.text_input("WhatsApp number (country code, e.g. 2776...)", key="wa_number_hour")
else:
    wa_group_hour = st.text_input("WhatsApp group link (chat.whatsapp.com/...)", key="wa_group_hour")

if st.button("Open WhatsApp (Hourly)"):
    wa_payload = urllib.parse.quote(f"```{hourly_template}```")
    if wa_mode_hour == "Private Number" and wa_number_hour:
        wa_url = f"https://wa.me/{wa_number_hour}?text={wa_payload}"
        st.markdown(f"[Open WhatsApp]({wa_url})", unsafe_allow_html=True)
    elif wa_mode_hour == "Group Link" and wa_group_hour:
        st.markdown(f"[Open WhatsApp Group]({wa_group_hour})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid WhatsApp number or group link.")

# ---------- 4-HOURLY SECTION (visible + editable) ----------
st.header("4-Hourly Template (visible & editable)")
four_blocks = ["06h00 - 10h00", "10h00 - 14h00", "14h00 - 18h00", "18h00 - 22h00", "22h00 - 02h00", "02h00 - 06h00"]
sel_block = st.selectbox("Select 4-hour block", four_blocks, index=0)
sel_date = st.date_input("Select date for this 4-hour block", value=datetime.now(SA_TZ).date())
include_used = st.checkbox("Include hourly entries already used in previous 4-hour reports (tick to include)", value=False)

# find matched hourly records for that date & block
required_hours = parse_block_hours(sel_block)
sel_date_str = sel_date.strftime("%Y-%m-%d")
matched = []
missing = []
for h in required_hours:
    candidates = [r for r in data.get("hourly_records", []) if r["date"] == sel_date_str and r["start_hour"] == h]
    if not include_used:
        candidates = [r for r in candidates if not r.get("used_in_4h", False)]
    if candidates:
        matched.append(candidates[-1])  # latest for that hour
    else:
        missing.append(h)

if missing:
    st.info(f"Missing hourly entries for hours: {', '.join(str(x).zfill(2) for x in missing)} — 4-hour sums are based on available saved hourly entries and can be edited below.")
else:
    st.success("4-hour sums loaded from hourly entries (you may edit below).")

def sum_from_matched(field):
    return sum(rec.get(field, 0) for rec in matched)

# computed defaults
auto = {
    "fwd_load": sum_from_matched("fwd_load"),
    "mid_load": sum_from_matched("mid_load"),
    "aft_load": sum_from_matched("aft_load"),
    "poop_load": sum_from_matched("poop_load"),
    "fwd_disch": sum_from_matched("fwd_disch"),
    "mid_disch": sum_from_matched("mid_disch"),
    "aft_disch": sum_from_matched("aft_disch"),
    "poop_disch": sum_from_matched("poop_disch"),
    "fwd_restow_load": sum_from_matched("fwd_restow_load"),
    "mid_restow_load": sum_from_matched("mid_restow_load"),
    "aft_restow_load": sum_from_matched("aft_restow_load"),
    "poop_restow_load": sum_from_matched("poop_restow_load"),
    "fwd_restow_disch": sum_from_matched("fwd_restow_disch"),
    "mid_restow_disch": sum_from_matched("mid_restow_disch"),
    "aft_restow_disch": sum_from_matched("aft_restow_disch"),
    "poop_restow_disch": sum_from_matched("poop_restow_disch"),
    "hatch_fwd_open": sum_from_matched("hatch_fwd_open"),
    "hatch_mid_open": sum_from_matched("hatch_mid_open"),
    "hatch_aft_open": sum_from_matched("hatch_aft_open"),
    "hatch_fwd_close": sum_from_matched("hatch_fwd_close"),
    "hatch_mid_close": sum_from_matched("hatch_mid_close"),
    "hatch_aft_close": sum_from_matched("hatch_aft_close"),
}

# editable inputs prefilled with computed sums
st.subheader("4-Hourly Inputs (prefilled, can edit)")
c1, c2 = st.columns(2)
with c1:
    fwd_load_4h = st.number_input("FWD Load (4H)", min_value=0, value=int(auto["fwd_load"]), key="fwd_load_4h")
    mid_load_4h = st.number_input("MID Load (4H)", min_value=0, value=int(auto["mid_load"]), key="mid_load_4h")
    aft_load_4h = st.number_input("AFT Load (4H)", min_value=0, value=int(auto["aft_load"]), key="aft_load_4h")
    poop_load_4h = st.number_input("POOP Load (4H)", min_value=0, value=int(auto["poop_load"]), key="poop_load_4h")
with c2:
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
    hatch_fwd_open_4h = st.number_input("FWD Hatch Open (4H)", min_value=0, value=int(auto["hatch_fwd_open"]), key="hatch_fwd_open_4h")
    hatch_fwd_close_4h = st.number_input("FWD Hatch Close (4H)", min_value=0, value=int(auto["hatch_fwd_close"]), key="hatch_fwd_close_4h")
with hh2:
    hatch_mid_open_4h = st.number_input("MID Hatch Open (4H)", min_value=0, value=int(auto["hatch_mid_open"]), key="hatch_mid_open_4h")
    hatch_mid_close_4h = st.number_input("MID Hatch Close (4H)", min_value=0, value=int(auto["hatch_mid_close"]), key="hatch_mid_close_4h")
with hh3:
    hatch_aft_open_4h = st.number_input("AFT Hatch Open (4H)", min_value=0, value=int(auto["hatch_aft_open"]), key="hatch_aft_open_4h")
    hatch_aft_close_4h = st.number_input("AFT Hatch Close (4H)", min_value=0, value=int(auto["hatch_aft_close"]), key="hatch_aft_close_4h")

# Recalculate totals check (helpful for debugging/add reassurance)
calc_load_sum = fwd_load_4h + mid_load_4h + aft_load_4h + poop_load_4h
calc_disch_sum = fwd_disch_4h + mid_disch_4h + aft_disch_4h + poop_disch_4h
st.markdown(f"**4H Totals** — Load: {calc_load_sum}  |  Disch: {calc_disch_sum}")

# 4-hourly template (same look as hourly, same cumulative block)
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
           Load   Disch
FWD        {fwd_restow_load_4h:>5}     {fwd_restow_disch_4h:>5}
MID        {mid_restow_load_4h:>5}     {mid_restow_disch_4h:>5}
AFT        {aft_restow_load_4h:>5}     {aft_restow_disch_4h:>5}
POOP       {poop_restow_load_4h:>5}     {poop_restow_disch_4h:>5}
_________________________
      *CUMULATIVE* (from hourly saved entries)
_________________________
           Load   Disch
Plan       {data['planned_load']:>5}      {data['planned_disch']:>5}
Done       {data.get('done_load',0):>5}      {data.get('done_disch',0):>5}
Remain     {remaining_load_now:>5}      {remaining_disch_now:>5}
_________________________
*Restows*
           Load   Disch
Plan       {data['planned_restow_load']:>5}      {data['planned_restow_disch']:>5}
Done       {data.get('done_restow_load',0):>5}      {data.get('done_restow_disch',0):>5}
Remain     {remaining_restow_load_now:>5}      {remaining_restow_disch_now:>5}
_________________________
*Hatch Moves*
           Open   Close
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

# Save 4-hourly report
if st.button("Save 4-Hourly Report (mark matched hourly entries as used)"):
    report = {
        "date": sel_date_str,
        "block": sel_block,
        "ts": now_iso(),
        "fwd_load": int(fwd_load_4h),
        "mid_load": int(mid_load_4h),
        "aft_load": int(aft_load_4h),
        "poop_load": int(poop_load_4h),
        "fwd_disch": int(fwd_disch_4h),
        "mid_disch": int(mid_disch_4h),
        "aft_disch": int(aft_disch_4h),
        "poop_disch": int(poop_disch_4h),
        "fwd_restow_load": int(fwd_restow_load_4h),
        "mid_restow_load": int(mid_restow_load_4h),
        "aft_restow_load": int(aft_restow_load_4h),
        "poop_restow_load": int(poop_restow_load_4h),
        "fwd_restow_disch": int(fwd_restow_disch_4h),
        "mid_restow_disch": int(mid_restow_disch_4h),
        "aft_restow_disch": int(aft_restow_disch_4h),
        "poop_restow_disch": int(poop_restow_disch_4h),
        "hatch_fwd_open": int(hatch_fwd_open_4h),
        "hatch_mid_open": int(hatch_mid_open_4h),
        "hatch_aft_open": int(hatch_aft_open_4h),
        "hatch_fwd_close": int(hatch_fwd_close_4h),
        "hatch_mid_close": int(hatch_mid_close_4h),
        "hatch_aft_close": int(hatch_aft_close_4h)
    }
    data.setdefault("four_hour_reports", []).append(report)

    # mark matched hourly entries as used (only those we matched earlier)
    for rec in matched:
        # find and set used_in_4h True for that record in data['hourly_records']
        for orig in data.get("hourly_records", []):
            if orig.get("ts") == rec.get("ts"):
                orig["used_in_4h"] = True

    save_data(data)
    st.success("4-hourly report saved and matched hourly entries (if any) marked as used.")

# Reset used flag
if st.button("Reset all 'used_in_4h' flags (allow re-using hourly entries)"):
    for rec in data.get("hourly_records", []):
        rec["used_in_4h"] = False
    save_data(data)
    st.success("All 'used_in_4h' flags reset.")

# Send 4-hourly via WhatsApp
st.subheader("Send 4-Hourly Template")
wa_mode_4h = st.selectbox("Choose send mode (4H)", ["Private Number", "Group Link"], key="wa_mode_4h")
if wa_mode_4h == "Private Number":
    wa_number_4h = st.text_input("WhatsApp number (country code)", key="wa_number_4h")
else:
    wa_group_4h = st.text_input("WhatsApp group link", key="wa_group_4h")

if st.button("Open WhatsApp (4H)"):
    wa_payload = urllib.parse.quote(f"```{template_4h}```")
    if wa_mode_4h == "Private Number" and wa_number_4h:
        url = f"https://wa.me/{wa_number_4h}?text={wa_payload}"
        st.markdown(f"[Open WhatsApp]({url})", unsafe_allow_html=True)
    elif wa_mode_4h == "Group Link" and wa_group_4h:
        st.markdown(f"[Open WhatsApp Group]({wa_group_4h})", unsafe_allow_html=True)
    else:
        st.warning("Enter a valid WhatsApp number or group link.")

st.markdown("---")
st.caption("Templates are monospace and aligned for copying to WhatsApp. 4-hourly sums come from saved hourly entries (if available) but are editable. Cumulative totals come from saved hourly entries and do not change when editing 4-hourly inputs.")