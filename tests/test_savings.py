import pytest
import pandas as pd
import numpy as np
from src.data_loader import load_dataset
from mv.savings import calculate_automated_savings

@pytest.fixture
def dataset():
    return load_dataset(edge_case_type="NONE")

def test_automated_savings_keys(dataset):
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

def test_peak_demand_reduction_formula(dataset):
    savings_data = calculate_automated_savings(dataset, target_reduction_pct=10.0)
    
    expected_peak_reduct = savings_data["measured_baseline_peak_max_kw"] - savings_data["measured_reporting_peak_max_kw"]
    assert np.isclose(savings_data["peak_demand_reduction_kw"], expected_peak_reduct, atol=0.05)
    assert savings_data["peak_demand_reduction_kw"] > 0

def test_energy_reduction_percentage_formula(dataset):
    savings_data = calculate_automated_savings(dataset, target_reduction_pct=10.0)
    
    base_avg = savings_data["measured_baseline_peak_mean_kw"]
    rep_avg = savings_data["measured_reporting_peak_mean_kw"]
    expected_pct = ((base_avg - rep_avg) / base_avg) * 100.0
    
    assert np.isclose(savings_data["peak_avg_reduction_pct"], expected_pct, atol=0.05)
    assert savings_data["peak_avg_reduction_pct"] >= 10.0
    assert savings_data["target_achieved"] is True

def test_financial_calculations(dataset):
    savings_data = calculate_automated_savings(dataset, demand_charge_usd_per_kw=25.0, peak_tariff_usd_per_kwh=0.35)
    
    expected_demand_charge = savings_data["peak_demand_reduction_kw"] * 25.0
    assert np.isclose(savings_data["monthly_demand_savings_usd"], expected_demand_charge, atol=0.05)
    assert savings_data["total_est_monthly_savings_usd"] == round(savings_data["monthly_demand_savings_usd"] + savings_data["monthly_energy_savings_usd"], 2)

def test_missing_period_raises_value_error():
    df_only_base = pd.DataFrame({
        "timestamp": ["2026-08-01 00:00:00"],
        "total_kw": [200.0],
        "is_intervention": [0]
    })
    with pytest.raises(ValueError):
        calculate_automated_savings(df_only_base)
