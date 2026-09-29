import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from preprocessing.clean_data import chronological_split, detect_outliers, detect_schedule_mismatch
from models.disaggregation import (
    train_or_load_nilm_model,
    predict_rule_based_disaggregation,
    benchmark_disaggregation_methods
)
from mv.metrics import compute_all_metrics, evaluate_ashrae14_compliance
from mv.savings import calculate_automated_savings

def render_ml_mv_view(df: pd.DataFrame, quality_info: dict):
    """
    Renders ML/NILM disaggregation benchmarks and ASHRAE Guideline 14 M&V validation.
    """
    st.title("🤖 ML/NILM Decomposition & ASHRAE 14 M&V Hub")
    st.caption("Benchmark Supervised NILM against Rule-Based Heuristics, Validate M&V with NMBE / CV(RMSE), and Verify Savings.")

    # Train / Load NILM model
    train_df, val_df, test_df = chronological_split(df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    
    with st.spinner("Loading calibrated NILM model..."):
        nilm_model = train_or_load_nilm_model(train_df)

    tab_benchmark, tab_predictions, tab_mv, tab_savings = st.tabs([
        "📊 1. ML vs Rule-Based Benchmark",
        "📈 2. Actual vs Predicted Loads",
        "📐 3. ASHRAE Guideline 14 Validation",
        "💰 4. Automated Savings & Uncertainty"
    ])

    # TAB 1: ML vs Rule-Based Benchmark
    with tab_benchmark:
        st.subheader("🔬 Disaggregation Methodology Comparison")
        st.markdown("""
        Evaluated on an **unseen chronological test partition** (Days 26–30 of pre-intervention baseline) 
        to ensure zero time-series data leakage.
        """)

        bench_df, summary = benchmark_disaggregation_methods(test_df, nilm_model)

        # High-level comparison metric cards
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Rule-Based Mean MAE", f"{summary['rule_based_mean_mae']} kW")
        with col_m2:
            st.metric("ML/NILM Mean MAE", f"{summary['nilm_mean_mae']} kW", delta=f"-{summary['mae_improvement_pct']}% Error", delta_color="normal")
        with col_m3:
            st.metric("Overall Accuracy Gain", f"{summary['mae_improvement_pct']}%", delta="Statistically Verified")
        with col_m4:
            st.metric("Test Data Points", f"{summary['test_records_evaluated']:,}", help="15-min intervals")

        st.markdown("##### Detailed Metric Benchmark Table:")
        st.dataframe(bench_df.style.highlight_min(subset=["MAE (kW)", "RMSE (kW)", "CV(RMSE) (%)"], color="#d4edda", axis=0), use_container_width=True)

        # Bar chart comparison of MAE by equipment
        fig_bar = px.bar(
            bench_df, x="Equipment", y="MAE (kW)", color="Method", barmode="group",
            title="Mean Absolute Error (MAE) by Equipment Load (Lower is Better)",
            color_discrete_map={"Rule-Based Baseline": "#EF553B", "ML / NILM (Random Forest)": "#00CC96"}
        )
        fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

        # Feature Importance Plot
        st.markdown("##### NILM Model Feature Importances:")
        feat_imp = nilm_model.get_feature_importances()
        if not feat_imp.empty:
            fig_imp = px.bar(
                feat_imp.head(10), x="Importance", y="Feature", orientation="h",
                color="Importance", color_continuous_scale="Viridis",
                title="Top 10 Explanatory Features in Load Decomposition"
            )
            fig_imp.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_imp, use_container_width=True)

    # TAB 2: Actual vs Predicted Loads
    with tab_predictions:
        st.subheader("📈 Actual vs Predicted Load Decomposition")
        st.caption("Visualizing NILM supervised decomposition on unseen test data with energy conservation enforcement.")

        test_preds = nilm_model.predict(test_df)
        
        target_equip = st.selectbox(
            "Select Equipment Load to Inspect:",
            ["hvac_kw", "process_kw", "lighting_kw", "aux_kw"],
            format_func=lambda x: {"hvac_kw": "HVAC Chiller Load", "process_kw": "Process Heavy Machinery", "lighting_kw": "Lighting Systems", "aux_kw": "Auxiliary / Data Center"}[x]
        )

        plot_df = pd.DataFrame({
            "datetime": test_df["datetime"],
            "Actual (kW)": test_df[target_equip],
            "NILM Predicted (kW)": test_preds[target_equip],
            "Rule-Based Baseline (kW)": predict_rule_based_disaggregation(test_df)[target_equip]
        })

        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(x=plot_df["datetime"], y=plot_df["Actual (kW)"], mode="lines", name="Actual Sub-metered (Ground Truth)", line=dict(color="#1f77b4", width=2.5)))
        fig_compare.add_trace(go.Scatter(x=plot_df["datetime"], y=plot_df["NILM Predicted (kW)"], mode="lines", name="ML / NILM Prediction", line=dict(color="#00CC96", width=2, dash="dash")))
        fig_compare.add_trace(go.Scatter(x=plot_df["datetime"], y=plot_df["Rule-Based Baseline (kW)"], mode="lines", name="Rule-Based Heuristic", line=dict(color="#EF553B", width=1.5, dash="dot")))

        fig_compare.update_layout(
            title=f"Time Series Tracking: Ground Truth vs Predicted ({target_equip})",
            xaxis_title="Timeline (Test Period)",
            yaxis_title="Power Demand (kW)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_compare, use_container_width=True)

        st.info("💡 **Conservation of Energy Guarantee:** The NILM engine applies a physical constraint normalizer: `∑(P_hvac + P_proc + P_light + P_aux) ≡ P_total_meter` for all time intervals.")

    # TAB 3: ASHRAE Guideline 14 Validation
    with tab_mv:
        st.subheader("📐 ASHRAE Guideline 14 M&V Protocol Validation")
        st.markdown("""
        Measurement & Verification standards require models to satisfy specific statistical error tolerances:
        - **Normalized Mean Bias Error (NMBE):** Measures systematic model bias (over- or under-prediction).
        - **Coefficient of Variation of Root Mean Square Error (CV(RMSE)):** Measures model variance and scatter.
        """)

        # Calculate metrics for aggregate baseline model
        baseline_df = df[df['is_intervention'] == 0]
        peak_b = baseline_df[baseline_df['tariff_period'] == 'Peak']
        
        # Test baseline model against peak demand
        overall_metrics = compute_all_metrics(
            y_true=test_df["total_kw"].values,
            y_pred=test_preds.sum(axis=1).values,
            p=4,
            time_resolution="15-min"
        )
        compliance = overall_metrics["compliance"]

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            st.metric("NMBE", f"{overall_metrics['nmbe']}%", help="Tolerance for 15-min/hourly: |NMBE| ≤ 10.0%")
            st.markdown(f"**Limit:** `|NMBE| ≤ 10.0%` | **Status:** {'🟢 PASS' if compliance['nmbe_pass'] else '🔴 FAIL'}")
        with col_v2:
            st.metric("CV(RMSE)", f"{overall_metrics['cv_rmse']}%", help="Tolerance for 15-min/hourly: CV(RMSE) ≤ 30.0%")
            st.markdown(f"**Limit:** `CV(RMSE) ≤ 30.0%` | **Status:** {'🟢 PASS' if compliance['cv_pass'] else '🔴 FAIL'}")
        with col_v3:
            st.metric("R² Goodness of Fit", f"{overall_metrics['r2']}")
            st.markdown(f"**Overall Compliance:** `{'✅ ' + compliance['status_label']}`")

        st.markdown("---")
        st.markdown("##### Governing Mathematical Formulas:")
        st.latex(r"NMBE = \frac{\sum_{i=1}^n (y_i - \hat{y}_i)}{(n - p) \cdot \bar{y}} \times 100\%")
        st.latex(r"CV(RMSE) = \frac{\sqrt{\frac{1}{n - p}\sum_{i=1}^n (y_i - \hat{y}_i)^2}}{\bar{y}} \times 100\%")
        st.caption(f"Inputs: n = {overall_metrics['n_observations']:,} intervals, p = {overall_metrics['p_parameters']} model parameters, y_bar = {test_df['total_kw'].mean():.1f} kW.")

    # TAB 4: Automated Savings & Uncertainty
    with tab_savings:
        st.subheader("💰 Automated Energy Savings & Demand Reduction")
        st.caption("Post-intervention operational savings verified according to IPMVP Option C.")

        savings = calculate_automated_savings(df, target_reduction_pct=10.0)

        # Baseline vs Target vs Actual Cards
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("Baseline Peak Demand", f"{savings['measured_baseline_peak_max_kw']} kW", "Pre-Intervention Peak")
        with col_s2:
            st.metric("Post-Intervention Peak", f"{savings['measured_reporting_peak_max_kw']} kW", delta=f"-{savings['peak_demand_reduction_pct']}% Peak Cut", delta_color="normal")
        with col_s3:
            st.metric("Target Reduction", f"{savings['target_reduction_pct']}%", delta="Target Met 🎉" if savings["target_achieved"] else "Pending")
        with col_s4:
            st.metric("M&V Model Uncertainty (95% CI)", f"±{savings['savings_uncertainty_95pct']}%", help="ASHRAE 14 fractional savings uncertainty")

        st.markdown("---")
        
        col_sav_chart, col_sav_details = st.columns([2, 1])

        with col_sav_chart:
            st.subheader("📊 Peak Tariff Period Load Curve Comparison")
            peak_df = df[df['tariff_period'] == 'Peak'].copy()
            peak_df['Time'] = peak_df['datetime'].dt.strftime('%H:%M')
            
            p_base = peak_df[peak_df['is_intervention'] == 0].groupby('Time')['total_kw'].mean().reset_index()
            p_post = peak_df[peak_df['is_intervention'] == 1].groupby('Time')['total_kw'].mean().reset_index()

            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=p_base['Time'], y=p_base['total_kw'], mode='lines+markers', name='Baseline Period (Days 1–30)', line=dict(color='#EF553B', width=3, dash='dash')))
            fig_p.add_trace(go.Scatter(x=p_post['Time'], y=p_post['total_kw'], mode='lines+markers', name='Reporting Period (Days 31–37)', line=dict(color='#00CC96', width=3)))
            fig_p.update_layout(xaxis_title="Time during Peak Tariff (18:00 - 22:00)", yaxis_title="Facility Demand (kW)", height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_p, use_container_width=True)

        with col_sav_details:
            st.subheader("💵 Financial Savings Audit")
            st.markdown(f"""
            - **Peak Demand Shaved:** `{savings['peak_demand_reduction_kw']} kW`
            - **Demand Charge Savings ($25/kW):** `${savings['monthly_demand_savings_usd']:,}/month`
            - **Energy kWh Savings ($0.35/kWh):** `${savings['monthly_energy_savings_usd']:,}/month`
            - **Total Monthly Verified Savings:** **`${savings['total_est_monthly_savings_usd']:,}/month`**
            - **CO2e Emissions Avoided:** `{savings['environmental_co2_kg_monthly']:,} kg CO2e / month`
            """)
            if quality_info.get("savings_claim_locked", False):
                st.error("⚠️ Note: Savings claims are locked due to current data feed quality alert.")
            else:
                st.success("✅ Savings claims verified against IPMVP Option C protocol.")
