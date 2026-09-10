import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_facilities_view(df, quality_info):
    """
    Renders operational tools, schedule deviation monitoring, and interactive intervention simulator for Facilities Operators.
    """
    st.title("⚙️ Facilities Operator Dashboard")
    st.caption("Real-time equipment schedules, schedule deviation alerts, and live operational intervention controls.")

    # 1. Equipment Operating Schedule Matrix
    st.subheader("🗓️ Equipment Operating Schedule Matrix")

    schedule_data = [
        {"Equipment": "HVAC Chiller Plant #1", "Scheduled Hours": "06:00 – 18:30", "Current Status": "RUNNING", "Deviation": "None", "Condition": "NORMAL"},
        {"Equipment": "HVAC Chiller Plant #2", "Scheduled Hours": "14:00 – 17:30 (Pre-cool)", "Current Status": "STANDBY", "Deviation": "Pre-cooling Complete", "Condition": "OPTIMIZED"},
        {"Equipment": "Process Mfg Line 1", "Scheduled Hours": "07:30 – 17:30", "Current Status": "RUNNING", "Deviation": "None", "Condition": "NORMAL"},
        {"Equipment": "Process Mfg Line 2", "Scheduled Hours": "07:30 – 17:30", "Current Status": "IDLE / RAMP DOWN", "Deviation": "Shifted Off-Peak", "Condition": "OPTIMIZED"},
        {"Equipment": "Warehouse Bay Lighting", "Scheduled Hours": "06:30 – 20:00", "Current Status": "AUTO SWEEP", "Deviation": "After-hours active (12%)", "Condition": "WARNING"},
        {"Equipment": "Aux Compressor System", "Scheduled Hours": "24 / 7 Baseline", "Current Status": "RUNNING", "Deviation": "None", "Condition": "NORMAL"}
    ]
    st.table(pd.DataFrame(schedule_data))

    st.markdown("---")

    # 2. Schedule Deviations & Unscheduled Operation Alerts
    st.subheader("🚨 Schedule Deviations & Telemetry Alerts")

    # Identify deviations from dataset
    after_hours_hvac = df[(df['hvac_scheduled'] == 0) & (df['hvac_kw'] > 80.0) & (df['is_intervention'] == 0)]
    after_hours_lighting = df[(df['lighting_scheduled'] == 0) & (df['lighting_kw'] > 40.0) & (df['is_intervention'] == 0)]

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.warning(f"**HVAC Schedule Leakage Detected:** {len(after_hours_hvac)} 15-minute intervals where HVAC ran > 80 kW outside scheduled hours during baseline.")
        st.info("💡 **Operator Action:** Verified HVAC setback temperature override active until 22:00. Recommend resetting BMS schedule automation.")

    with col_a2:
        st.warning(f"**Lighting Night Baseline Leakage:** {len(after_hours_lighting)} intervals with high lighting load after 20:00 cutoff.")
        st.info("💡 **Operator Action:** Override manual lighting panel switches in Bay 3 to automatic photocell sweep.")

    st.markdown("---")

    # 3. Interactive Operational Intervention Simulator
    st.subheader("🎛️ Live Operational Intervention Simulator")
    st.caption("Adjust operational parameters below to simulate peak demand shaving in real time.")

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        pre_cool_kw = st.slider("Pre-Cooling Boost (14:00 - 17:30)", min_value=0, max_value=80, value=40, step=5, help="kW added during normal tariff to cool building thermal mass")
    with col_s2:
        hvac_shed_kw = st.slider("HVAC Peak Shedding (18:00 - 22:00)", min_value=0, max_value=120, value=85, step=5, help="kW reduced during peak tariff window")
    with col_s3:
        process_shift_kw = st.slider("Process Line 2 Load Shift", min_value=0, max_value=250, value=220, step=10, help="kW shifted from peak tariff to off-peak hours")

    # Simulate dynamic peak curve
    peak_hours = [f"{h:02d}:00" for h in range(14, 23)]
    
    # Baseline curve
    sim_baseline = [170, 185, 190, 195, 480, 475, 460, 440, 210]
    
    # Adjusted curve based on simulator inputs
    sim_adjusted = []
    for idx, hour_str in enumerate(peak_hours):
        hour_val = int(hour_str.split(':')[0])
        val = sim_baseline[idx]
        if 14 <= hour_val < 18:
            val += pre_cool_kw  # Pre-cooling boost
        elif 18 <= hour_val < 22:
            val -= (hvac_shed_kw + process_shift_kw)  # Peak shedding
        sim_adjusted.append(max(80, val))

    fig_sim = go.Figure()
    fig_sim.add_trace(go.Scatter(x=peak_hours, y=sim_baseline, mode='lines+markers', name='Baseline Load Curve (kW)', line=dict(color='#EF553B', width=3, dash='dash')))
    fig_sim.add_trace(go.Scatter(x=peak_hours, y=sim_adjusted, mode='lines+markers', name='Simulated Adjusted Curve (kW)', line=dict(color='#00CC96', width=3)))

    # Highlight Peak Tariff Box
    fig_sim.add_vrect(x0="18:00", x1="22:00", fillcolor="red", opacity=0.1, line_width=0, annotation_text="PEAK TARIFF WINDOW ($0.35/kWh + $25/kW)", annotation_position="top left")

    fig_sim.update_layout(xaxis_title="Time of Day", yaxis_title="Facility Power Demand (kW)", margin=dict(l=20, r=20, t=30, b=20), height=350)
    st.plotly_chart(fig_sim, use_container_width=True)

    sim_max_base = max(sim_baseline[4:8])
    sim_max_adj = max(sim_adjusted[4:8])
    sim_peak_savings_kw = sim_max_base - sim_max_adj
    sim_cost_savings = sim_peak_savings_kw * 25.0

    st.success(f"🎉 **Simulated Peak Reduction:** `{sim_peak_savings_kw} kW` shaved during peak window! Projected Monthly Demand Charge Savings: **${sim_cost_savings:,.2f}**")
