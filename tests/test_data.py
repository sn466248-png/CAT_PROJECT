import pytest
import os
import pandas as pd
import numpy as np
from src.data_loader import load_dataset
from preprocessing.clean_data import (
    clean_dataset,
    detect_outliers,
    detect_schedule_mismatch,
    feature_engineering,
    chronological_split
)

@pytest.fixture
def raw_df():
    return load_dataset(edge_case_type="NONE")

def test_load_dataset(raw_df):
    assert not raw_df.empty
    assert len(raw_df) >= 3000
    expected_cols = ["timestamp", "total_kw", "total_kwh", "hvac_kw", "process_kw", "lighting_kw", "aux_kw"]
    for col in expected_cols:
        assert col in raw_df.columns

def test_clean_dataset_negative_clipping(raw_df):
    dirty_df = raw_df.copy()
    dirty_df.loc[10:15, "total_kw"] = -50.0
    cleaned_df, report = clean_dataset(dirty_df)
    
    assert (cleaned_df["total_kw"] >= 0).all()
    assert report["negative_kw_clipped"] >= 5

def test_clean_dataset_sorting():
    df = pd.DataFrame({
        "timestamp": ["2026-08-02 00:00:00", "2026-08-01 00:00:00"],
        "total_kw": [200.0, 150.0]
    })
    cleaned_df, _ = clean_dataset(df)
    assert cleaned_df["datetime"].iloc[0] < cleaned_df["datetime"].iloc[1]

def test_feature_engineering_no_forward_leakage(raw_df):
    feat_df = feature_engineering(raw_df)
    
    # Check created features
    expected_features = [
        "hour", "minute", "day_of_week", "is_weekend",
        "sin_hour", "cos_hour", "sin_dow", "cos_dow",
        "total_kw_lag1", "total_kw_lag4", "total_kw_rolling_mean_4",
        "cdh_18_3", "temp_occupancy_interaction", "is_peak_tariff"
    ]
    for feat in expected_features:
        assert feat in feat_df.columns
        
    # Check lag1 is strictly equal to shifted previous row
    assert np.isclose(feat_df["total_kw_lag1"].iloc[5], feat_df["total_kw"].iloc[4])

def test_chronological_split_preserves_order(raw_df):
    train_df, val_df, test_df = chronological_split(raw_df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, baseline_only=True)
    
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0
    
    # Check strict chronological order without overlap
    assert train_df["datetime"].max() <= val_df["datetime"].min()
    assert val_df["datetime"].max() <= test_df["datetime"].min()
    
    # Total count matches baseline
    baseline_count = len(raw_df[raw_df["is_intervention"] == 0])
    assert len(train_df) + len(val_df) + len(test_df) == baseline_count

def test_partitioned_csv_files_exist():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    assert os.path.exists(os.path.join(data_dir, "industrial_energy_data.csv"))
    assert os.path.exists(os.path.join(data_dir, "meter_data.csv"))
    assert os.path.exists(os.path.join(data_dir, "equipment_schedule.csv"))
    assert os.path.exists(os.path.join(data_dir, "occupancy_data.csv"))
