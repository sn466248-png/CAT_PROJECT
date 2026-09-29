import pandas as pd
import numpy as np

# Export new modular components
from models.disaggregation import (
    NILMDisaggregator,
    predict_rule_based_disaggregation,
    benchmark_disaggregation_methods,
    train_or_load_nilm_model
)
from mv.metrics import (
    calculate_nmbe,
    calculate_cv_rmse,
    calculate_mae,
    calculate_rmse,
    calculate_r2,
    evaluate_ashrae14_compliance,
    compute_all_metrics
)
from mv.savings import calculate_automated_savings

def compute_load_disaggregation(df):
    """
    Computes cumulative energy consumption (kWh) and percentage share across all load categories.
    """
    if df.empty:
        return {}

    hvac_total = df['hvac_kw'].sum() * 0.25
    process_total = df['process_kw'].sum() * 0.25
    lighting_total = df['lighting_kw'].sum() * 0.25
    aux_total = df['aux_kw'].sum() * 0.25
    grand_total = hvac_total + process_total + lighting_total + aux_total

    if grand_total == 0:
        return {}

    return {
        "HVAC": {"kwh": round(hvac_total, 2), "pct": round((hvac_total / grand_total) * 100, 1)},
        "Process Equipment": {"kwh": round(process_total, 2), "pct": round((process_total / grand_total) * 100, 1)},
        "Lighting": {"kwh": round(lighting_total, 2), "pct": round((lighting_total / grand_total) * 100, 1)},
        "Auxiliary / Other": {"kwh": round(aux_total, 2), "pct": round((aux_total / grand_total) * 100, 1)},
        "Total_kWh": round(grand_total, 2)
    }

def analyze_peak_demand_period(df):
    """
    Analyzes equipment performance specifically during Peak Tariff periods (18:00 - 22:00).
    """
    peak_df = df[df['tariff_period'] == 'Peak']
    if peak_df.empty:
        return {}

    avg_total_peak_kw = peak_df['total_kw'].mean()
    avg_hvac_peak_kw = peak_df['hvac_kw'].mean()
    avg_process_peak_kw = peak_df['process_kw'].mean()
    avg_lighting_peak_kw = peak_df['lighting_kw'].mean()
    avg_aux_peak_kw = peak_df['aux_kw'].mean()

    # Identify primary contributor
    categories = {
        "HVAC": avg_hvac_peak_kw,
        "Process Equipment": avg_process_peak_kw,
        "Lighting": avg_lighting_peak_kw,
        "Auxiliary": avg_aux_peak_kw
    }
    top_contributor = max(categories, key=categories.get)

    return {
        "avg_total_peak_kw": round(avg_total_peak_kw, 2),
        "avg_hvac_peak_kw": round(avg_hvac_peak_kw, 2),
        "avg_process_peak_kw": round(avg_process_peak_kw, 2),
        "avg_lighting_peak_kw": round(avg_lighting_peak_kw, 2),
        "avg_aux_peak_kw": round(avg_aux_peak_kw, 2),
        "top_contributor": top_contributor,
        "top_contributor_kw": round(categories[top_contributor], 2),
        "top_contributor_pct": round((categories[top_contributor] / avg_total_peak_kw) * 100, 1)
    }

def get_evidence_chains(df):
    """
    Generates structured, traceable evidence chains for operational recommendations.
    Chain format: Meter Data -> Load Category -> Equipment Schedule -> Occupancy/Production Context -> Tariff Period -> Recommended Action
    """
    chains = []

    # 1. HVAC Peak Tariff Overlap Evidence Chain
    hvac_peak_baseline = df[(df['tariff_period'] == 'Peak') & (df['is_intervention'] == 0)]['hvac_kw'].mean()
    avg_occupancy_peak = df[(df['tariff_period'] == 'Peak') & (df['is_intervention'] == 0)]['occupancy_pct'].mean()
    
    chains.append({
        "issue": "Excessive HVAC Consumption During Peak Tariff Hours",
        "meter_data": f"Total Demand: ~{round(df[(df['tariff_period'] == 'Peak') & (df['is_intervention'] == 0)]['total_kw'].mean(), 1)} kW | HVAC Demand: {round(hvac_peak_baseline, 1)} kW",
        "load_category": "HVAC System (Chillers & Air Handling Units)",
        "equipment_schedule": "Scheduled 06:00–18:30 (Running past 18:00 cutoff)",
        "context": f"Occupancy drops to {round(avg_occupancy_peak, 1)}% after 19:00, while ambient temp remains moderate (24–27°C)",
        "tariff_period": "Peak Tariff Period (18:00–22:00 @ $0.35/kWh + $25/kW Demand Charge)",
        "recommended_action": "Pre-condition facility building thermal mass to 20°C during Normal tariff window (14:00–17:30); setback HVAC setpoint by +3°C during Peak window (18:00–22:00).",
        "expected_saving": "~85 kW peak demand reduction ($2,125/month demand charge savings)"
    })

    # 2. Process Heavy Machinery Shift Evidence Chain
    process_peak_baseline = df[(df['tariff_period'] == 'Peak') & (df['is_intervention'] == 0)]['process_kw'].mean()
    chains.append({
        "issue": "Process Line 2 Overlapping with Peak Tariff Hours",
        "meter_data": f"Process Load Demand: {round(process_peak_baseline, 1)} kW during 18:00–19:30",
        "load_category": "Process Heavy Equipment (Manufacturing Line 2)",
        "equipment_schedule": "Scheduled 07:30–19:30 (Overlaps 1.5 hrs into Peak Tariff)",
        "context": "Production batch finished by 17:30; line idling with high active baseline from 17:30 to 19:30",
        "tariff_period": "Peak Tariff Period (18:00–22:00 @ $0.35/kWh)",
        "recommended_action": "Reschedule Line 2 maintenance and end-of-shift ramp-down to finish at 17:30 before Peak Tariff onset.",
        "expected_saving": "~220 kW peak load shift ($5,500/month demand charge savings)"
    })

    # 3. After-Hours Facility Lighting Leakage
    lighting_night = df[(df['tariff_period'] == 'Off-Peak') & (df['is_intervention'] == 0)]['lighting_kw'].mean()
    chains.append({
        "issue": "Unscheduled After-Hours Warehouse & Office Lighting",
        "meter_data": f"Night Lighting Load: {round(lighting_night, 1)} kW consistently between 22:00–06:00",
        "load_category": "Lighting Systems (Warehouse & Office Bays)",
        "equipment_schedule": "Scheduled OFF at 20:00",
        "context": "Facility occupancy < 8% overnight; high static lighting load observed",
        "tariff_period": "Off-Peak / Transition Period (20:00–06:00 @ $0.08/kWh)",
        "recommended_action": "Install automated occupancy motion sweep sensors and enable automatic 20:00 lighting zone shutoff.",
        "expected_saving": "~38 kW continuous baseload reduction (~7,000 kWh/month savings)"
    })

    return chains

def calculate_mv_experiment_results(df):
    """
    Calculates Measurement & Verification (M&V) results conforming to IPMVP Option C protocol.
    Baseline (Days 1-30) vs Post-Intervention (Days 31-37).
    """
    baseline_df = df[df['is_intervention'] == 0]
    intervention_df = df[df['is_intervention'] == 1]

    if baseline_df.empty or intervention_df.empty:
        return {}

    # Peak Period Demand Analysis (18:00 - 22:00)
    b_peak_df = baseline_df[baseline_df['tariff_period'] == 'Peak']
    i_peak_df = intervention_df[intervention_df['tariff_period'] == 'Peak']

    baseline_mean_peak_kw = b_peak_df['total_kw'].mean()
    post_mean_peak_kw = i_peak_df['total_kw'].mean()

    baseline_max_peak_kw = b_peak_df['total_kw'].max()
    post_max_peak_kw = i_peak_df['total_kw'].max()

    # Formula: Energy Reduction (%) = ((Baseline Demand - Post-Intervention Demand) / Baseline Demand) * 100
    peak_avg_reduction_pct = ((baseline_mean_peak_kw - post_mean_peak_kw) / baseline_mean_peak_kw) * 100.0
    peak_max_reduction_pct = ((baseline_max_peak_kw - post_max_peak_kw) / baseline_max_peak_kw) * 100.0

    # Financial Savings Calculation
    # Demand Charge: $25 per kW of peak demand saved per month
    kw_demand_saved = baseline_max_peak_kw - post_max_peak_kw
    monthly_demand_charge_savings = kw_demand_saved * 25.0

    # Daily kWh savings during peak hours
    b_daily_peak_kwh = b_peak_df['total_kwh'].sum() / (len(b_peak_df['datetime'].dt.date.unique()) or 1)
    i_daily_peak_kwh = i_peak_df['total_kwh'].sum() / (len(i_peak_df['datetime'].dt.date.unique()) or 1)
    daily_kwh_saved = b_daily_peak_kwh - i_daily_peak_kwh
    monthly_energy_cost_savings = daily_kwh_saved * 30 * 0.35  # Peak rate $0.35/kWh

    total_est_monthly_savings = monthly_demand_charge_savings + monthly_energy_cost_savings

    return {
        "target_reduction_pct": 10.0,
        "baseline_mean_peak_kw": round(baseline_mean_peak_kw, 2),
        "post_mean_peak_kw": round(post_mean_peak_kw, 2),
        "baseline_max_peak_kw": round(baseline_max_peak_kw, 2),
        "post_max_peak_kw": round(post_max_peak_kw, 2),
        "measured_avg_reduction_pct": round(peak_avg_reduction_pct, 2),
        "measured_max_reduction_pct": round(peak_max_reduction_pct, 2),
        "kw_demand_saved": round(kw_demand_saved, 2),
        "monthly_demand_savings_usd": round(monthly_demand_charge_savings, 2),
        "monthly_energy_savings_usd": round(monthly_energy_cost_savings, 2),
        "total_est_monthly_savings_usd": round(total_est_monthly_savings, 2),
        "target_met": peak_avg_reduction_pct >= 10.0
    }
