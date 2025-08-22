import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="WhatsApp Report Generator", layout="wide")

# --- Initialize Session State ---
if "hourly_data" not in st.session_state:
    st.session_state.hourly_data = []

if "cumulative_load" not in st.session_state:
    st.session_state.cumulative_load = 0
if "cumulative_discharge" not in st.session_state:
    st.session_state.cumulative_discharge = 0

if "four_hourly_load" not in st.session_state:
    st.session_state.four_hourly_load = 0
if "four_hourly_discharge" not in st.session_state:
    st.session_state.four_hourly_discharge = 0
if "four_hourly_start" not in st.session_state:
    st.session_state.four_hourly_start = datetime.now()

# Plan values (editable)
if "plan_load" not in st.session_state:
    st.session_state.plan_load = 0
if "plan_discharge" not in st.session_state:
    st.session_state.plan_discharge = 0
if "four_hourly_plan_load" not in st.session_state:
    st.session_state.four_hourly_plan_load = 0
if "four_hourly_plan_discharge" not in st.session_state:
    st.session_state.four_hourly_plan_discharge = 0

st.title("📊 WhatsApp Report Generator")

# --- Reset Functions ---
def reset_hourly():
    st.session_state.hourly_data = []
    st.session_state.cumulative_load = 0
    st.session_state.cumulative_discharge = 0

def reset_four_hourly():
    st.session_state.four_hourly_load = 0
    st.session_state.four_hourly_discharge = 0
    st.session_state.four_hourly_start = datetime.now()
    # --- Hourly Input Section ---
with st.expander("⏱ Edit Hourly Inputs", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        plan_load = st.number_input("Hourly Planned Load", value=st.session_state.plan_load)
    with col2:
        plan_discharge = st.number_input("Hourly Planned Discharge", value=st.session_state.plan_discharge)

    st.session_state.plan_load = plan_load
    st.session_state.plan_discharge = plan_discharge

# --- 4-Hourly Input Section ---
with st.expander("⏳ Edit 4-Hourly Inputs", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        four_hourly_plan_load = st.number_input("4-Hourly Planned Load", value=st.session_state.four_hourly_plan_load)
    with col2:
        four_hourly_plan_discharge = st.number_input("4-Hourly Planned Discharge", value=st.session_state.four_hourly_plan_discharge)

    st.session_state.four_hourly_plan_load = four_hourly_plan_load
    st.session_state.four_hourly_plan_discharge = four_hourly_plan_discharge

# --- Add Hourly Entry ---
with st.form("hourly_entry_form", clear_on_submit=True):
    st.subheader("➕ Add Hourly Report")
    col1, col2, col3 = st.columns(3)
    with col1:
        time_slot = st.text_input("Time Slot (e.g., 10h00 - 11h00)")
    with col2:
        actual_load = st.number_input("Actual Load", min_value=0)
    with col3:
        actual_discharge = st.number_input("Actual Discharge", min_value=0)

    submitted = st.form_submit_button("Add Entry")
    if submitted and time_slot:
        # Save entry
        st.session_state.hourly_data.append({
            "time": time_slot,
            "plan_load": st.session_state.plan_load,
            "plan_discharge": st.session_state.plan_discharge,
            "actual_load": actual_load,
            "actual_discharge": actual_discharge
        })

        # Update cumulative totals
        st.session_state.cumulative_load += actual_load
        st.session_state.cumulative_discharge += actual_discharge

        # Update 4-hourly totals
        st.session_state.four_hourly_load += actual_load
        st.session_state.four_hourly_discharge += actual_discharge
        # --- Hourly Report Table ---
if st.session_state.hourly_data:
    st.subheader("📋 Hourly Report")
    df = pd.DataFrame(st.session_state.hourly_data)
    st.dataframe(df, use_container_width=True)

# --- Totals ---
st.subheader("📊 Totals")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Cumulative Load", st.session_state.cumulative_load)
with col2:
    st.metric("Cumulative Discharge", st.session_state.cumulative_discharge)
with col3:
    st.button("🔄 Reset Hourly Totals", on_click=reset_hourly)

st.subheader("⏳ 4-Hourly Totals")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("4-Hourly Load", st.session_state.four_hourly_load)
with col2:
    st.metric("4-Hourly Discharge", st.session_state.four_hourly_discharge)
with col3:
    st.button("🔄 Reset 4-Hourly", on_click=reset_four_hourly)

# --- WhatsApp Template ---
if st.session_state.hourly_data:
    st.subheader("📱 WhatsApp Report Preview")
    
    report_text = "```"
    report_text += f"\nHOURLY REPORT ({datetime.now().strftime('%d/%m/%Y')})\n"
    report_text += "_________________________\n"
    for row in st.session_state.hourly_data:
        report_text += f"{row['time']} | Load: {row['actual_load']} (Plan {row['plan_load']}) | Disch: {row['actual_discharge']} (Plan {row['plan_discharge']})\n"

    report_text += "_________________________\n"
    report_text += f"Cumulative Load: {st.session_state.cumulative_load}\n"
    report_text += f"Cumulative Disch: {st.session_state.cumulative_discharge}\n"
    report_text += f"4-Hourly Load: {st.session_state.four_hourly_load} (Plan {st.session_state.four_hourly_plan_load})\n"
    report_text += f"4-Hourly Disch: {st.session_state.four_hourly_discharge} (Plan {st.session_state.four_hourly_plan_discharge})\n"
    report_text += "```"

    st.text_area("WhatsApp Message (copy-paste ready)", report_text, height=300)