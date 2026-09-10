import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.disaggregation import calculate_mv_experiment_results

def render_executive_view(df, quality_info):
    """
    Renders high-level strategic overview for C-suite and Operations Executives.
    Focuses on macro consumption, peak demand savings, ROI, and carbon emissions.
    """
    st.title("👔 Executive Energy Dashboard")
    st.caption("Strategic demand reduction, operational ROI, and sustainability summary.")

    mv_results = calculate_mv_experiment_results(df)

    if not mv_results:
        st.warning("Insufficient data to compute executive summary metrics.")
        return

    # Metric Row 1: Executive KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Baseline Avg Peak Demand",
            value=f"{mv_results['baseline_mean_peak_kw']} kW",
            delta="Pre-Intervention Baseline"
        )
    with col2:
        st.metric(
            label="Measured Post-Intervention Peak",
            value=f"{mv_results['post_mean_peak_kw']} kW",
            delta=f"-{mv_results['measured_avg_reduction_pct']}% Peak Reduction",
            delta_color="normal"
        )
    with col3:
        st.metric(
            label="Target Reduction",
            value=f"{mv_results['target_reduction_pct']}%",
            delta="Target Achieved 🎉" if mv_results['target_met'] else "Target Pending"
        )
    with col4:
        st.metric(
            label="Est. Monthly Financial Savings",
            value=f"${mv_results['total_est_monthly_savings_usd']:,}",
            delta=f"${mv_results['monthly_demand_savings_usd']:,} Demand + ${mv_results['monthly_energy_savings_usd']:,} Energy"
        )

    st.markdown("---")

    # High-level Peak Demand Comparison Chart
    col_chart, col_roi = st.columns([2, 1])

    with col_chart:
        st.subheader("📈 Peak Demand Reduction (Baseline vs Post-Intervention)")
        
        peak_df = df[df['tariff_period'] == 'Peak'].copy()
        peak_df['Time'] = peak_df['datetime'].dt.strftime('%H:%M')
        
        # Group by time during peak window
        hourly_baseline = peak_df[peak_df['is_intervention'] == 0].groupby('Time')['total_kw'].mean().reset_index()
        hourly_post = peak_df[peak_df['is_intervention'] == 1].groupby('Time')['total_kw'].mean().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_baseline['Time'], y=hourly_baseline['total_kw'],
            mode='lines+markers', name='Baseline Peak Demand (kW)',
            line=dict(color='#EF553B', width=3, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=hourly_post['Time'], y=hourly_post['total_kw'],
            mode='lines+markers', name='Post-Intervention Peak Demand (kW)',
            line=dict(color='#00CC96', width=3)
        ))
        fig.update_layout(
            xaxis_title="Peak Tariff Window (18:00 - 22:00)",
            yaxis_title="Total Facility Demand (kW)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_roi:
        st.subheader("💰 Monthly Savings Breakdown")
        
        savings_data = pd.DataFrame({
            "Category": ["Demand Charge ($25/kW)", "Peak Energy kWh ($0.35/kWh)"],
            "Savings ($)": [mv_results['monthly_demand_savings_usd'], mv_results['monthly_energy_savings_usd']]
        })
        
        fig_pie = px.pie(savings_data, values='Savings ($)', names='Category', color_discrete_sequence=['#636EFA', '#00CC96'], hole=0.4)
        fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)

        st.info(f"**Environmental Impact:** Avoided ~{round(mv_results['kw_demand_saved'] * 0.45, 1)} Metric Tons of CO2e monthly by shedding dirty peak-peaker grid dispatch.")

    st.markdown("---")

    # Strategic Executive Actions
    st.subheader("📋 Executive Strategic Recommendations")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.success("✅ **Approved Action 1: Pre-Cooling Policy**\n\nThermal pre-conditioning building envelope reduced 85 kW peak chiller demand with zero occupant discomfort.")
    with col_b:
        st.success("✅ **Approved Action 2: Process Staggering**\n\nAdjusting Line 2 end-of-shift schedule by 30 mins saved $5,500/mo in peak demand penalties.")
    with col_c:
        st.info("📌 **Next Strategy: Automated Control System**\n\nDeploying smart occupancy sweep sensors will automate after-hours lighting shutoff for an extra $1,200/mo.")
