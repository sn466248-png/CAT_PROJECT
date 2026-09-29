import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.disaggregation import compute_load_disaggregation, analyze_peak_demand_period, get_evidence_chains, calculate_mv_experiment_results

def render_energy_manager_view(df, quality_info):
    """
    Renders detailed disaggregation, tariff cost analysis, IPMVP M&V experiment, and evidence chain drill-downs for Energy Managers.
    """
    st.title("⚡ Energy Manager Dashboard & Disaggregation Engine")
    st.caption("Load breakdown, peak demand analysis, tariff optimization, and evidence-supported recommendations.")

    # 1. Disaggregation Section
    st.subheader("📊 Energy Disaggregation Breakdown")

    disagg = compute_load_disaggregation(df)

    if disagg:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Energy", f"{disagg['Total_kWh']:,} kWh")
        with col2:
            st.metric("HVAC Load", f"{disagg['HVAC']['kwh']:,} kWh", f"{disagg['HVAC']['pct']}% of total")
        with col3:
            st.metric("Process Load", f"{disagg['Process Equipment']['kwh']:,} kWh", f"{disagg['Process Equipment']['pct']}% of total")
        with col4:
            st.metric("Lighting Load", f"{disagg['Lighting']['kwh']:,} kWh", f"{disagg['Lighting']['pct']}% of total")
        with col5:
            st.metric("Auxiliary Load", f"{disagg['Auxiliary / Other']['kwh']:,} kWh", f"{disagg['Auxiliary / Other']['pct']}% of total")

    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.write("##### Equipment Category Share (Sunburst)")
        sunburst_df = pd.DataFrame([
            {"Category": "Total Campus Energy", "Equipment": "HVAC System", "kWh": disagg['HVAC']['kwh']},
            {"Category": "Total Campus Energy", "Equipment": "Process Equipment", "kWh": disagg['Process Equipment']['kwh']},
            {"Category": "Total Campus Energy", "Equipment": "Lighting Systems", "kWh": disagg['Lighting']['kwh']},
            {"Category": "Total Campus Energy", "Equipment": "Auxiliary / Data Center", "kWh": disagg['Auxiliary / Other']['kwh']}
        ])
        fig_sun = px.sunburst(sunburst_df, path=['Category', 'Equipment'], values='kWh', color='Equipment',
                             color_discrete_map={'HVAC System': '#1f77b4', 'Process Equipment': '#ff7f0e', 'Lighting Systems': '#2ca02c', 'Auxiliary / Data Center': '#d62728'})
        fig_sun.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
        st.plotly_chart(fig_sun, use_container_width=True)

    with col_chart2:
        st.write("##### 24-Hour Load Profile Disaggregation (Average Day)")
        df_copy = df.copy()
        df_copy['hour_min'] = df_copy['datetime'].dt.strftime('%H:%M')
        hourly_disagg = df_copy.groupby('hour_min')[['hvac_kw', 'process_kw', 'lighting_kw', 'aux_kw']].mean().reset_index()

        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(x=hourly_disagg['hour_min'], y=hourly_disagg['aux_kw'], mode='lines', name='Auxiliary', stackgroup='one', line=dict(color='#d62728')))
        fig_area.add_trace(go.Scatter(x=hourly_disagg['hour_min'], y=hourly_disagg['lighting_kw'], mode='lines', name='Lighting', stackgroup='one', line=dict(color='#2ca02c')))
        fig_area.add_trace(go.Scatter(x=hourly_disagg['hour_min'], y=hourly_disagg['hvac_kw'], mode='lines', name='HVAC', stackgroup='one', line=dict(color='#1f77b4')))
        fig_area.add_trace(go.Scatter(x=hourly_disagg['hour_min'], y=hourly_disagg['process_kw'], mode='lines', name='Process', stackgroup='one', line=dict(color='#ff7f0e')))
        fig_area.update_layout(xaxis_title="Time of Day", yaxis_title="Power Demand (kW)", margin=dict(l=20, r=20, t=10, b=20), height=320)
        st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("---")

    # 2. Peak Tariff Analysis & Contributors
    st.subheader("🔥 Peak Tariff Analysis (18:00 – 22:00 Window)")

    peak_analysis = analyze_peak_demand_period(df)
    if peak_analysis:
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            st.info(f"**Top Peak Contributor:**\n### {peak_analysis['top_contributor']}\n"
                    f"**{peak_analysis['top_contributor_kw']} kW** ({peak_analysis['top_contributor_pct']}% of peak load)")
            st.write(f"Average Total Peak Demand: **{peak_analysis['avg_total_peak_kw']} kW**")
            st.write(f"Electricity Tariff: **$0.35 / kWh + $25.00 / kW Peak Demand Charge**")

        with col_p2:
            st.write("##### Peak Period Load Breakdown by Equipment")
            peak_bar_df = pd.DataFrame({
                "Equipment": ["Process Equipment", "HVAC System", "Lighting", "Auxiliary"],
                "Demand (kW)": [peak_analysis['avg_process_peak_kw'], peak_analysis['avg_hvac_peak_kw'], peak_analysis['avg_lighting_peak_kw'], peak_analysis['avg_aux_peak_kw']]
            })
            fig_bar = px.bar(peak_bar_df, x="Equipment", y="Demand (kW)", color="Equipment", text="Demand (kW)",
                             color_discrete_map={"Process Equipment": "#ff7f0e", "HVAC System": "#1f77b4", "Lighting": "#2ca02c", "Auxiliary": "#d62728"})
            fig_bar.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=250)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # 3. Drill-Down Evidence Chains
    st.subheader("🔍 Drill-Down Evidence & Operational Recommendations")
    st.caption("Traceable chain connecting telemetry to actionable interventions.")

    chains = get_evidence_chains(df)

    selected_chain_idx = st.selectbox(
        "Select Problem to Drill Down:",
        options=list(range(len(chains))),
        format_func=lambda i: f"Issue #{i+1}: {chains[i]['issue']}"
    )

    selected_chain = chains[selected_chain_idx]

    st.markdown("#### Traceable Evidence Chain:")
    
    col_c1, col_c2, col_c3, col_c4, col_c5, col_c6 = st.columns(6)
    with col_c1:
        st.info(f"**1. Meter Data**\n\n{selected_chain['meter_data']}")
    with col_c2:
        st.info(f"**2. Load Category**\n\n{selected_chain['load_category']}")
    with col_c3:
        st.info(f"**3. Schedule**\n\n{selected_chain['equipment_schedule']}")
    with col_c4:
        st.info(f"**4. Context**\n\n{selected_chain['context']}")
    with col_c5:
        st.warning(f"**5. Tariff Window**\n\n{selected_chain['tariff_period']}")
    with col_c6:
        st.success(f"**6. Action**\n\n{selected_chain['recommended_action']}")

    st.success(f"💡 **Expected Financial Impact:** {selected_chain['expected_saving']}")

    st.markdown("---")

    # 4. Measurement & Verification (M&V) Baseline Experiment
    st.subheader("🧪 M&V Experiment: Baseline vs Intervention (IPMVP Option C & ASHRAE 14)")

    from mv.savings import calculate_automated_savings
    savings_data = calculate_automated_savings(df, target_reduction_pct=10.0)

    col_mv1, col_mv2, col_mv3, col_mv4 = st.columns(4)
    with col_mv1:
        st.markdown(f"**Baseline Mean Peak:** `{savings_data['measured_baseline_peak_mean_kw']} kW`")
        st.markdown(f"**Baseline Max Peak:** `{savings_data['measured_baseline_peak_max_kw']} kW`")
    with col_mv2:
        st.markdown(f"**Target Reduction:** `{savings_data['target_reduction_pct']}%`")
        st.markdown(f"**Actual Measured Avg Cut:** `{savings_data['peak_avg_reduction_pct']}%`")
    with col_mv3:
        st.markdown(f"**Peak Demand Shaved:** `{savings_data['peak_demand_reduction_kw']} kW`")
        st.markdown(f"**Total Verified Savings:** `${savings_data['total_est_monthly_savings_usd']:,}/mo`")
    with col_mv4:
        st.markdown(f"**ASHRAE 14 NMBE:** `{savings_data['baseline_nmbe_pct']}%`")
        st.markdown(f"**ASHRAE 14 CV(RMSE):** `{savings_data['baseline_cv_rmse_pct']}%`")
        st.markdown(f"**Status:** `{'🟢 ' + savings_data['ashrae_compliance']['status_label']}`")

    st.markdown("##### Verification Protocol Breakdown:")
    st.markdown("""
    - **Baseline Period:** Days 1–30 (Normal facility operational schedule without thermal pre-cooling or load staggering).
    - **Target:** 10.0% reduction in peak-period electrical demand (18:00–22:00).
    - **Operational Intervention:** Pre-cooling building mass (14:00–17:30), shifting Line 2 maintenance (17:30 cutoff), and automated 20:00 lighting sweep.
    - **Measured Result:** **{avg_red}% Average Demand Reduction** and **{max_red}% Peak Load Shaving**, resulting in verified savings of **${savings:,}/mo**.
    - **Model Uncertainty (95% CI):** **±{uncertainty}%** under ASHRAE Guideline 14 fractional savings uncertainty.
    """.format(
        avg_red=savings_data['peak_avg_reduction_pct'],
        max_red=savings_data['peak_demand_reduction_pct'],
        savings=savings_data['total_est_monthly_savings_usd'],
        uncertainty=savings_data['savings_uncertainty_95pct']
    ))
