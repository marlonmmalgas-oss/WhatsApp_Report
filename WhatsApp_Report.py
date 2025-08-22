import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Initialize session state
if "hourly_data" not in st.session_state:
    st.session_state.hourly_data = []
if "four_hour_data" not in st.session_state:
    st.session_state.four_hour_data = []
if "cumulative" not in st.session_state:
    st.session_state.cumulative = {
        "planned": 0, "done": 0, "variance": 0
    }
if "last_reset" not in st.session_state:
    st.session_state.last_reset = datetime.now()

# Function: Reset every 4 hours
def reset_four_hour_data():
    st.session_state.four_hour_data = []
    st.session_state.last_reset = datetime.now()

# Function: Update cumulative totals
def update_cumulative(planned, done):
    st.session_state.cumulative["planned"] += planned
    st.session_state.cumulative["done"] += done
    st.session_state.cumulative["variance"] = (
        st.session_state.cumulative["done"] - st.session_state.cumulative["planned"]
    )
    # Function: Add hourly entry
def add_hourly_entry(group, planned, done):
    variance = done - planned
    timestamp = datetime.now().strftime("%H:%M")

    entry = {
        "group": group,
        "planned": planned,
        "done": done,
        "variance": variance,
        "time": timestamp
    }
    st.session_state.hourly_data.append(entry)

    # Update cumulative
    update_cumulative(planned, done)

    # Update 4-hour block
    st.session_state.four_hour_data.append(entry)

# UI Layout
st.title("📊 WhatsApp Report System")

# Collapsible input
with st.expander("➕ Add Hourly Report"):
    group = st.text_input("Enter Group Name", "Group A")
    planned = st.number_input("Planned Moves", 0, 10000, 0)
    done = st.number_input("Done Moves", 0, 10000, 0)

    if st.button("➕ Add Hourly Data"):
        add_hourly_entry(group, planned, done)
        st.success(f"Added entry for {group} at {datetime.now().strftime('%H:%M')}")
        # Show hourly reports
st.subheader("⏱ Hourly Reports")
if st.session_state.hourly_data:
    df_hourly = pd.DataFrame(st.session_state.hourly_data)
    st.dataframe(df_hourly)
else:
    st.info("No hourly reports yet.")

# Show 4-hourly reports with accumulated totals
st.subheader("🕓 4-Hourly Reports (Accumulative)")
if st.session_state.four_hour_data:
    df_4hr = pd.DataFrame(st.session_state.four_hour_data)
    df_4hr["cumulative_planned"] = df_4hr["planned"].cumsum()
    df_4hr["cumulative_done"] = df_4hr["done"].cumsum()
    df_4hr["cumulative_variance"] = df_4hr["cumulative_done"] - df_4hr["cumulative_planned"]
    st.dataframe(df_4hr)
else:
    st.info("No 4-hour reports yet.")
    # Show cumulative totals (always updated)
st.subheader("📈 Cumulative Totals")
st.metric("Planned", st.session_state.cumulative["planned"])
st.metric("Done", st.session_state.cumulative["done"])
st.metric("Variance", st.session_state.cumulative["variance"])

# Reset button every 4 hours
time_since_reset = datetime.now() - st.session_state.last_reset
if time_since_reset > timedelta(hours=4):
    st.warning("⚠️ It's been more than 4 hours since last reset!")

if st.button("🔄 Reset 4-Hour Data"):
    reset_four_hour_data()
    st.success("4-hour data has been reset!")
    st.markdown("### 4-Hourly Report")

        # Collapse for 4-hourly inputs
        with st.expander("Edit 4-Hourly Inputs", expanded=False):
            four_hourly_data = {}
            for group in groups:
                st.subheader(f"{group} (4-Hourly)")
                four_hourly_data[group] = []
                for idx in range(1, 5):
                    with st.container():
                        st.markdown(f"**Hour {idx} (within 4-hour block)**")
                        planned = st.number_input(f"{group} Hour {idx} Plan (4h)", min_value=0, step=1, key=f"{group}_4h_plan_{idx}")
                        done = st.number_input(f"{group} Hour {idx} Done (4h)", min_value=0, step=1, key=f"{group}_4h_done_{idx}")

                        four_hourly_data[group].append({
                            "planned": planned,
                            "done": done
                        })

            if st.button("Reset 4-Hourly Report"):
                for group in groups:
                    for idx in range(1, 5):
                        st.session_state[f"{group}_4h_plan_{idx}"] = 0
                        st.session_state[f"{group}_4h_done_{idx}"] = 0
                st.success("4-hourly report reset!")

        # Calculate cumulative for 4-hourly
        cumulative_4h = {}
        for group in groups:
            cumulative_4h[group] = {"planned": 0, "done": 0}
            for entry in four_hourly_data[group]:
                cumulative_4h[group]["planned"] += entry["planned"]
                cumulative_4h[group]["done"] += entry["done"]

        st.markdown("### 4-Hourly Summary")
        for group in groups:
            st.write(f"**{group}**")
            st.text(
                f"Planned (4h cumulative): {cumulative_4h[group]['planned']:>5}\n"
                f"Done    (4h cumulative): {cumulative_4h[group]['done']:>5}\n"
            )

        st.markdown("---")
        st.markdown("### Final WhatsApp Report")

        # Compile final report message
        final_message = []
        final_message.append("📊 *WhatsApp Report* 📊\n")

        # Hourly section
        final_message.append("⏰ *Hourly Report*")
        for group in groups:
            final_message.append(f"*{group}*")
            for idx, entry in enumerate(hourly_data[group], start=1):
                final_message.append(
                    f"Hour {idx}: Plan {entry['planned']} | Done {entry['done']}"
                )
            final_message.append(
                f"Cumulative: Plan {cumulative[group]['planned']} | Done {cumulative[group]['done']}\n"
            )

        # 4-Hourly section
        final_message.append("🕓 *4-Hourly Report*")
        for group in groups:
            final_message.append(f"*{group}*")
            for idx, entry in enumerate(four_hourly_data[group], start=1):
                final_message.append(
                    f"H{idx}: Plan {entry['planned']} | Done {entry['done']}"
                )
            final_message.append(
                f"4h Cumulative: Plan {cumulative_4h[group]['planned']} | Done {cumulative_4h[group]['done']}\n"
            )

        # Combine into final string
        final_message_str = "\n".join(final_message)
        st.text_area("Generated WhatsApp Report", value=final_message_str, height=400)
        # =========================
#  Part 4/4
# =========================

# ------------- Display Report Section -------------
if st.session_state.cumulative["hours"]:
    st.markdown("## 📊 Report Summary")

    cumulative = st.session_state.cumulative
    hours = cumulative["hours"]

    # ---- Hourly Summary (Grouped) ----
    st.subheader("⏱ Hourly Summary by Group")
    for group_name, group_hours in hours.items():
        with st.expander(f"📌 {group_name}"):
            for hour_label, data in group_hours.items():
                st.write(
                    f"**{hour_label}** | "
                    f"Planned: {data['plan']} | "
                    f"Done: {data['done']} | "
                    f"Variance: {data['done'] - data['plan']}"
                )

    # ---- 4-Hour Accumulated Indicator ----
    st.subheader("🔄 4-Hour Accumulated Totals")
    four_hour_data = cumulative["4_hour"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Planned (4h)", four_hour_data["plan"])
    col2.metric("Done (4h)", four_hour_data["done"])
    col3.metric("Variance (4h)", four_hour_data["done"] - four_hour_data["plan"])
    col4.metric("Hours Counted", four_hour_data["counter"])

    # Reset button
    if st.button("♻️ Reset 4-Hour Cycle"):
        st.session_state.cumulative["4_hour"] = {"plan": 0, "done": 0, "counter": 0}
        st.success("4-hour cycle reset!")

    # ---- Cumulative Totals (Daily) ----
    st.subheader("📈 Daily Totals (Cumulative)")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Planned", cumulative["planned_load"])
    col2.metric("Total Done", cumulative["done_load"])
    col3.metric("Total Variance", cumulative["done_load"] - cumulative["planned_load"])

# =========================
#  End of Script
# =========================