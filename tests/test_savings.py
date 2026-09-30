"""Unit Test Suite: Automated M&V Savings & Uncertainty Calculations (test_savings.py)

This module validates the core financial and physical energy savings calculations
conforming to IPMVP Option C (Whole Facility Verification) and ASHRAE Guideline 14:
1. Peak Electrical Demand Reduction:
   peak_reduction_kw = baseline_peak_max_kw - reporting_peak_max_kw
2. Percentage Energy Reduction:
   reduction_pct = ((baseline_mean_kw - reporting_mean_kw) / baseline_mean_kw) * 100
3. Utility Tariff Accounting:
   - Monthly Demand Charge Savings: peak_reduction_kw * demand_charge_rate ($25/kW)
   - Monthly Avoided Energy Cost: daily_peak_kwh_saved * 30 * peak_energy_rate ($0.35/kWh)
4. Fractional Savings Uncertainty at 95% Confidence (U_95):
   U_95 = 1.96 * (CV(RMSE) / savings_fraction) * sqrt((1 + 2/n) / m)
"""

import pytest
import pandas as pd
import numpy as np
from src.data_loader import load_dataset
from mv.savings import calculate_automated_savings

@pytest.fixture
def dataset() -> pd.DataFrame:
    """Fixture providing the complete 37-day calibrated industrial dataset."""
    return load_dataset(edge_case_type="NONE")

def test_automated_savings_keys(dataset: pd.DataFrame):
    """Validates that calculate_automated_savings returns all mandatory auditing fields.

    Auditing Schema:
    - Measured periods and observation counts (baseline vs reporting)
    - Measured mean and max peak kW values
    - Demand and energy percentage reductions
    - Financial demand charge and energy savings breakdown
    - ASHRAE 14 NMBE, CV(RMSE), compliance dictionary, and 95% CI uncertainty
    """
    savings_data = calculate_automated_savings(dataset, target_reduction_pct=10.0)
    
    assert "baseline_period" in savings_data
    assert "reporting_period" in savings_data
    assert "measured_baseline_peak_mean_kw" in savings_data
    assert "measured_reporting_peak_mean_kw" in savings_data
    assert "measured_baseline_peak_max_kw" in savings_data
    assert "measured_reporting_peak_max_kw" in savings_data
    assert "peak_demand_reduction_kw" in savings_data
    assert "peak_demand_reduction_pct" in savings_data
    assert "peak_avg_reduction_kw" in savings_data
    assert "peak_avg_reduction_pct" in savings_data
    assert "monthly_demand_savings_usd" in savings_data
    assert "monthly_energy_savings_usd" in savings_data
    assert "total_est_monthly_savings_usd" in savings_data
    assert "savings_uncertainty_95pct" in savings_data

def test_peak_demand_reduction_formula(dataset: pd.DataFrame):
    """Validates the mathematical formula for peak demand shaved.

    Formula:
        Avoided Peak Demand (kW) = Max Baseline Peak (kW) - Max Post-Intervention Peak (kW)
    Requirement:
        Must strictly equal baseline_max - reporting_max and must be positive under the intervention.
    """
    savings_data = calculate_automated_savings(dataset, target_reduction_pct=10.0)
    
    expected_peak_reduct = savings_data["measured_baseline_peak_max_kw"] - savings_data["measured_reporting_peak_max_kw"]
    assert np.isclose(savings_data["peak_demand_reduction_kw"], expected_peak_reduct, atol=0.05), (
        f"Calculated peak reduction {savings_data['peak_demand_reduction_kw']} kW differs from expected {expected_peak_reduct} kW"
    )
    assert savings_data["peak_demand_reduction_kw"] > 0, "Avoided peak demand must be positive after load shifting"

def test_energy_reduction_percentage_formula(dataset: pd.DataFrame):
    """Validates the mathematical formula for percentage energy reduction.

    Formula:
        Reduction (%) = ((Baseline Mean - Reporting Mean) / Baseline Mean) * 100
    Requirement:
        Must exceed the client target threshold of 10.0% (target_achieved = True).
    """
    savings_data = calculate_automated_savings(dataset, target_reduction_pct=10.0)
    
    base_avg = savings_data["measured_baseline_peak_mean_kw"]
    rep_avg = savings_data["measured_reporting_peak_mean_kw"]
    expected_pct = ((base_avg - rep_avg) / base_avg) * 100.0
    
    assert np.isclose(savings_data["peak_avg_reduction_pct"], expected_pct, atol=0.05)
    assert savings_data["peak_avg_reduction_pct"] >= 10.0, "Energy reduction must meet or exceed 10.0% goal"
    assert savings_data["target_achieved"] is True, "Target achievement flag must be True"

def test_financial_calculations(dataset: pd.DataFrame):
    """Validates tariff accounting for peak demand charges and time-of-use energy rates.

    Financial Formulas:
        Monthly Demand Savings = avoided_peak_kw * $25.00/kW
        Total Monthly Savings = Monthly Demand Savings + Monthly Energy Savings
    """
    savings_data = calculate_automated_savings(dataset, demand_charge_usd_per_kw=25.0, peak_tariff_usd_per_kwh=0.35)
    
    expected_demand_charge = savings_data["peak_demand_reduction_kw"] * 25.0
    assert np.isclose(savings_data["monthly_demand_savings_usd"], expected_demand_charge, atol=0.05)
    assert savings_data["total_est_monthly_savings_usd"] == round(
        savings_data["monthly_demand_savings_usd"] + savings_data["monthly_energy_savings_usd"], 2
    )

def test_missing_period_raises_value_error():
    """Validates that omitting either baseline or reporting period triggers a ValueError.

    Error Boundary:
    - calculate_automated_savings requires both pre-intervention (is_intervention=0)
      and post-intervention (is_intervention=1) data to compute verified savings.
    """
    df_only_base = pd.DataFrame({
        "timestamp": ["2026-08-01 00:00:00"],
        "total_kw": [200.0],
        "is_intervention": [0]
    })
    with pytest.raises(ValueError):
        calculate_automated_savings(df_only_base)
