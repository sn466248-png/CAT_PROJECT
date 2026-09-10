import os
import pandas as pd
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "industrial_energy_data.csv")

def load_dataset(csv_path=DATA_PATH, edge_case_type="NONE"):
    """
    Loads energy monitoring dataset and optionally injects simulated edge case faults:
    - NONE: Clean dataset
    - STALE_DATA: Last 24 hours of data are frozen/delayed (timestamp frozen in past)
    - MISSING_OCCUPANCY: Occupancy column set to NaN / null
    - MISSING_TIMESTAMPS: Timestamp column corrupted with NaNs / missing values
    """
    if not os.path.exists(csv_path):
        from generate_data import generate_industrial_energy_data
        df = generate_industrial_energy_data(filename=csv_path)
    else:
        df = pd.read_csv(csv_path)

    df['datetime'] = pd.to_datetime(df['timestamp'])

    if edge_case_type == "STALE_DATA":
        # Simulate meter feed stopping 6 hours ago; timestamps frozen in past
        stale_cutoff = df['datetime'].iloc[-24]  # 6 hours ago (24 * 15 min)
        df.loc[df['datetime'] > stale_cutoff, 'timestamp'] = stale_cutoff.strftime("%Y-%m-%d %H:%M:%S")
        df['datetime'] = pd.to_datetime(df['timestamp'])

    elif edge_case_type == "MISSING_OCCUPANCY":
        # Simulate occupancy sensor failure
        df['occupancy_pct'] = np.nan

    elif edge_case_type == "MISSING_TIMESTAMPS":
        # Simulate corrupted or missing timestamp entries in recent readings
        indices_to_corrupt = df.index[-40:-10]
        df.loc[indices_to_corrupt, 'timestamp'] = np.nan
        df['datetime'] = pd.to_datetime(df['timestamp'])

    return df

def get_summary_metrics(df):
    """
    Computes key summary statistics distinguishing Baseline vs Post-Intervention.
    """
    baseline_df = df[df['is_intervention'] == 0]
    intervention_df = df[df['is_intervention'] == 1]

    # Average peak period demand (18:00 - 22:00)
    baseline_peak_kw = baseline_df[baseline_df['tariff_period'] == 'Peak']['total_kw'].mean() if not baseline_df.empty else 0
    intervention_peak_kw = intervention_df[intervention_df['tariff_period'] == 'Peak']['total_kw'].mean() if not intervention_df.empty else 0

    max_peak_kw_baseline = baseline_df['total_kw'].max() if not baseline_df.empty else 0
    max_peak_kw_intervention = intervention_df['total_kw'].max() if not intervention_df.empty else 0

    # Total kWh energy consumption
    baseline_kwh = baseline_df['total_kwh'].sum() if not baseline_df.empty else 0
    intervention_kwh = intervention_df['total_kwh'].sum() if not intervention_df.empty else 0

    # Energy reduction percentage on peak demand (kW)
    if baseline_peak_kw > 0:
        peak_demand_reduction_pct = ((baseline_peak_kw - intervention_peak_kw) / baseline_peak_kw) * 100.0
    else:
        peak_demand_reduction_pct = 0.0

    return {
        "baseline_avg_peak_kw": round(baseline_peak_kw, 2),
        "intervention_avg_peak_kw": round(intervention_peak_kw, 2),
        "baseline_max_peak_kw": round(max_peak_kw_baseline, 2),
        "intervention_max_peak_kw": round(max_peak_kw_intervention, 2),
        "peak_demand_reduction_pct": round(peak_demand_reduction_pct, 2),
        "baseline_total_kwh": round(baseline_kwh, 2),
        "intervention_total_kwh": round(intervention_kwh, 2),
    }
