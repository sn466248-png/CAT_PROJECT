import streamlit as st
import pandas as pd

def render_low_bandwidth_view(df, quality_info):
    """
    Displays a minimal, text-only, high-contrast dashboard view optimized for low-bandwidth environments.
    """
    st.title("⚡ Low-Bandwidth / Low-Connectivity View")
    st.caption("Simplified text and table interface. Heavy charts and visual canvas elements are disabled.")

    # Status summary
    st.subheader(f"System Status: {quality_info['badge_icon']} {quality_info['status']}")
    st.text(f"Confidence Level: {quality_info['confidence_pct']}%")

    if quality_info['messages']:
        for msg in quality_info['messages']:
            st.text(f"[ALERT] {msg}")

    st.markdown("---")

    # Recent 10 energy readings table
    st.subheader("📊 Recent Energy Readings (Latest 10 Intervals)")
    recent_df = df.tail(10)[['timestamp', 'total_kw', 'hvac_kw', 'process_kw', 'lighting_kw', 'aux_kw', 'tariff_period']]
    st.table(recent_df)

    st.markdown("---")

    # Equipment Load Summary Table
    st.subheader("💡 Equipment Summary (Averaged Over Baseline vs Post-Intervention)")
    
    baseline_df = df[df['is_intervention'] == 0]
    intervention_df = df[df['is_intervention'] == 1]

    summary_data = [
        {
            "Equipment Category": "HVAC System",
            "Baseline Avg kW": round(baseline_df['hvac_kw'].mean(), 1) if not baseline_df.empty else 0,
            "Post-Intervention Avg kW": round(intervention_df['hvac_kw'].mean(), 1) if not intervention_df.empty else 0,
            "Change (kW)": round((intervention_df['hvac_kw'].mean() - baseline_df['hvac_kw'].mean()), 1) if not baseline_df.empty and not intervention_df.empty else 0
        },
        {
            "Equipment Category": "Process Equipment",
            "Baseline Avg kW": round(baseline_df['process_kw'].mean(), 1) if not baseline_df.empty else 0,
            "Post-Intervention Avg kW": round(intervention_df['process_kw'].mean(), 1) if not intervention_df.empty else 0,
            "Change (kW)": round((intervention_df['process_kw'].mean() - baseline_df['process_kw'].mean()), 1) if not baseline_df.empty and not intervention_df.empty else 0
        },
        {
            "Equipment Category": "Lighting Systems",
            "Baseline Avg kW": round(baseline_df['lighting_kw'].mean(), 1) if not baseline_df.empty else 0,
            "Post-Intervention Avg kW": round(intervention_df['lighting_kw'].mean(), 1) if not intervention_df.empty else 0,
            "Change (kW)": round((intervention_df['lighting_kw'].mean() - baseline_df['lighting_kw'].mean()), 1) if not baseline_df.empty and not intervention_df.empty else 0
        },
        {
            "Equipment Category": "Auxiliary / Data Center",
            "Baseline Avg kW": round(baseline_df['aux_kw'].mean(), 1) if not baseline_df.empty else 0,
            "Post-Intervention Avg kW": round(intervention_df['aux_kw'].mean(), 1) if not intervention_df.empty else 0,
            "Change (kW)": round((intervention_df['aux_kw'].mean() - baseline_df['aux_kw'].mean()), 1) if not baseline_df.empty and not intervention_df.empty else 0
        }
    ]
    st.table(pd.DataFrame(summary_data))

    st.markdown("---")
    st.subheader("📌 Recommended Action Summary")
    st.text("1. Pre-condition HVAC to 20°C from 14:00-17:30 before Peak Tariff onset (18:00).")
    st.text("2. Ramp down Process Line 2 maintenance at 17:30 to eliminate peak load overlap.")
    st.text("3. Enable automatic 20:00 lighting zone shutoff in warehouse bays.")
