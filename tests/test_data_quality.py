import pytest
import pandas as pd
import numpy as np
from src.data_loader import load_dataset
from src.edge_cases import evaluate_data_quality
from preprocessing.clean_data import detect_outliers, detect_schedule_mismatch

@pytest.fixture
def clean_df():
    return load_dataset(edge_case_type="NONE")

def test_case1_missing_meter_values(clean_df):
    """CASE 1: Missing meter values."""
    dirty_df = clean_df.copy()
    dirty_df.loc[10:25, "total_kw"] = np.nan
    dirty_df.loc[10:25, "total_kwh"] = np.nan
    
    q_info = evaluate_data_quality(dirty_df, edge_case_type="MISSING_METER_VALUES")
    
    assert q_info["status"] in ["REDUCED CONFIDENCE", "MISSING"]
    assert q_info["confidence_pct"] <= 50.0
    assert q_info["actions_allowed"] is False
    assert q_info["savings_claim_locked"] is True
    assert any("missing meter" in msg.lower() for msg in q_info["messages"])

def test_case2_stale_meter_data():
    """CASE 2: Stale meter data."""
    stale_df = load_dataset(edge_case_type="STALE_DATA")
    q_info = evaluate_data_quality(stale_df, edge_case_type="STALE_DATA")
    
    assert q_info["status"] == "STALE"
    assert q_info["confidence_pct"] <= 50.0
    assert q_info["actions_allowed"] is False
    assert q_info["savings_claim_locked"] is True
    assert any("frozen or delayed" in msg.lower() for msg in q_info["messages"])

def test_case3_missing_occupancy_data():
    """CASE 3: Missing occupancy data."""
    occ_df = load_dataset(edge_case_type="MISSING_OCCUPANCY")
    q_info = evaluate_data_quality(occ_df, edge_case_type="MISSING_OCCUPANCY")
    
    assert q_info["status"] == "MISSING"
    assert q_info["confidence_pct"] < 90.0
    assert any("occupancy" in msg.lower() for msg in q_info["messages"])

def test_case4_equipment_schedule_mismatch(clean_df):
    """CASE 4: Equipment schedule mismatch."""
    mismatch_df = clean_df.copy()
    # Simulate nighttime HVAC running hard when scheduled off
    night_idx = mismatch_df[(mismatch_df["hvac_scheduled"] == 0) & (mismatch_df["is_intervention"] == 0)].index
    mismatch_df.loc[night_idx[:10], "hvac_kw"] = 120.0
    
    deviations = detect_schedule_mismatch(mismatch_df, hvac_threshold=75.0)
    assert not deviations.empty
    assert (deviations["equipment"] == "HVAC System").any()
    
    q_info = evaluate_data_quality(mismatch_df, edge_case_type="SCHEDULE_MISMATCH")
    assert any("unscheduled hours" in msg.lower() or "deviation" in msg.lower() for msg in q_info["messages"])

def test_case5_unexpected_extreme_meter_value(clean_df):
    """CASE 5: Unexpected extreme meter value."""
    spike_df = clean_df.copy()
    spike_idx = spike_df.index[-10]
    spike_df.loc[spike_idx, "total_kw"] = 1650.0  # Massive physical outlier
    
    outlier_mask, flagged = detect_outliers(spike_df, column="total_kw", max_physical_kw=800.0)
    assert outlier_mask.any()
    assert spike_idx in flagged.index
    assert "Exceeds Physical Capacity" in flagged.loc[spike_idx, "outlier_reason"]
    
    q_info = evaluate_data_quality(spike_df, edge_case_type="EXTREME_OUTLIER")
    assert any("extreme meter reading" in msg.lower() for msg in q_info["messages"])
