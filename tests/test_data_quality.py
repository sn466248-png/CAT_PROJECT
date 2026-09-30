"""Unit Test Suite: Data Quality & Fault Resilience Engine (test_data_quality.py)

This module provides exhaustive test coverage for the 5 automated failure modes
and data quality scenarios defined in the platform:
1. Missing Meter Telemetry (NaN / Null intervals)
2. Stale / Frozen Meter Telemetry (>6 hours feed freeze)
3. Missing Occupancy Sensor Telemetry
4. Equipment Schedule Overlap / Mismatch (After-hours leakage)
5. Physical Extreme Surges / Outliers (>800 kW or >3.5 sigma)

Error Boundaries & Behavioral Invariants:
- Any missing meter values or stale data locks financial savings claims (`savings_claim_locked = True`).
- Confidence score drops from 95% (nominal) down to <= 50% for critical data faults.
- Interactive controls and operational setpoint actions are disallowed (`actions_allowed = False`).
- Physical electrical capacity thresholds (800 kW) trigger immediate safety flags.
"""

import pytest
import pandas as pd
import numpy as np
from src.data_loader import load_dataset
from src.edge_cases import evaluate_data_quality
from preprocessing.clean_data import detect_outliers, detect_schedule_mismatch

@pytest.fixture
def clean_df() -> pd.DataFrame:
    """Fixture providing nominal, clean telemetry (15-min intervals, 37 days)."""
    return load_dataset(edge_case_type="NONE")

def test_case1_missing_meter_values(clean_df: pd.DataFrame):
    """CASE 1: Missing Meter Values (Null / NaN Injections).

    Error Boundary & Requirements:
    - Input: Artificially inject NaN values into 'total_kw' and 'total_kwh' across indices 10:25.
    - Detection: System must flag missing values without performing silent/unauthorized imputation.
    - System Response:
      * Status must degrade to 'REDUCED CONFIDENCE' or 'MISSING'.
      * Overall confidence score must drop to <= 50.0%.
      * Action authorization must be revoked (actions_allowed = False).
      * Savings claim verification must be strictly locked (savings_claim_locked = True).
    """
    dirty_df = clean_df.copy()
    dirty_df.loc[10:25, "total_kw"] = np.nan
    dirty_df.loc[10:25, "total_kwh"] = np.nan
    
    q_info = evaluate_data_quality(dirty_df, edge_case_type="MISSING_METER_VALUES")
    
    assert q_info["status"] in ["REDUCED CONFIDENCE", "MISSING"], (
        f"Expected status REDUCED CONFIDENCE or MISSING, got {q_info['status']}"
    )
    assert q_info["confidence_pct"] <= 50.0, (
        f"Confidence {q_info['confidence_pct']}% exceeds maximum allowed threshold of 50%"
    )
    assert q_info["actions_allowed"] is False, "Operational actions must be revoked when meter data is missing"
    assert q_info["savings_claim_locked"] is True, "Savings claims must be locked when meter telemetry contains NaNs"
    assert any("missing meter" in msg.lower() for msg in q_info["messages"]), (
        "Expected descriptive diagnostic message indicating missing meter intervals"
    )

def test_case2_stale_meter_data():
    """CASE 2: Stale / Frozen Meter Telemetry Feed.

    Error Boundary & Requirements:
    - Input: Load dataset with frozen timestamps simulating gateway communication timeout (>6 hours).
    - Detection: Timestamp latency check against current wall-clock / simulation horizon.
    - System Response:
      * Status must display 'STALE'.
      * Confidence score must drop to <= 50.0%.
      * Operational interventions disabled (`actions_allowed = False`).
      * Savings claims locked (`savings_claim_locked = True`).
      * Error log must include delayed/frozen alert.
    """
    stale_df = load_dataset(edge_case_type="STALE_DATA")
    q_info = evaluate_data_quality(stale_df, edge_case_type="STALE_DATA")
    
    assert q_info["status"] == "STALE", f"Expected status STALE, got {q_info['status']}"
    assert q_info["confidence_pct"] <= 50.0, f"Confidence {q_info['confidence_pct']}% exceeds allowed 50%"
    assert q_info["actions_allowed"] is False, "Operational actions must be locked during stale feeds"
    assert q_info["savings_claim_locked"] is True, "Savings claims cannot be verified on stale feeds"
    assert any("frozen or delayed" in msg.lower() for msg in q_info["messages"]), (
        "Diagnostic message must flag frozen or delayed meter telemetry"
    )

def test_case3_missing_occupancy_data():
    """CASE 3: Missing Contextual Occupancy Sensor Telemetry.

    Error Boundary & Requirements:
    - Input: Load dataset where IoT zone occupancy sensors are disconnected (NaN).
    - Detection: Null scan on contextual occupancy columns.
    - System Response:
      * Status flags 'MISSING'.
      * Confidence drops below 90% (moderate penalty because meter power telemetry is still intact).
      * Disaggregation shifts to fallback temperature-only regression without halting basic monitoring.
    """
    occ_df = load_dataset(edge_case_type="MISSING_OCCUPANCY")
    q_info = evaluate_data_quality(occ_df, edge_case_type="MISSING_OCCUPANCY")
    
    assert q_info["status"] == "MISSING", f"Expected status MISSING, got {q_info['status']}"
    assert q_info["confidence_pct"] < 90.0, "Confidence should drop below nominal 95% when occupancy is missing"
    assert any("occupancy" in msg.lower() for msg in q_info["messages"]), (
        "Diagnostic message must inform operator that occupancy sensors are offline"
    )

def test_case4_equipment_schedule_mismatch(clean_df: pd.DataFrame):
    """CASE 4: Equipment Running Outside Authorized Operational Schedule.

    Error Boundary & Requirements:
    - Input: Inject active HVAC operation (120.0 kW) during nighttime intervals when schedule = 0.
    - Threshold: Deadband check against 75.0 kW baseline for after-hours HVAC draw.
    - Detection: detect_schedule_mismatch identifies active equipment during unscheduled blocks.
    - System Response:
      * Deviation dataframe populated with equipment identifier and timestamps.
      * Quality evaluation generates after-hours operational leakage alert.
    """
    mismatch_df = clean_df.copy()
    # Simulate nighttime HVAC running hard when scheduled off (schedule == 0)
    night_idx = mismatch_df[(mismatch_df["hvac_scheduled"] == 0) & (mismatch_df["is_intervention"] == 0)].index
    mismatch_df.loc[night_idx[:10], "hvac_kw"] = 120.0
    
    deviations = detect_schedule_mismatch(mismatch_df, hvac_threshold=75.0)
    assert not deviations.empty, "Schedule mismatch detector must flag nighttime HVAC override"
    assert (deviations["equipment"] == "HVAC System").any(), "Deviations must include HVAC System"
    
    q_info = evaluate_data_quality(mismatch_df, edge_case_type="SCHEDULE_MISMATCH")
    assert any("unscheduled hours" in msg.lower() or "deviation" in msg.lower() for msg in q_info["messages"]), (
        "Diagnostic message must flag equipment draw during unscheduled hours"
    )

def test_case5_unexpected_extreme_meter_value(clean_df: pd.DataFrame):
    """CASE 5: Physical Outlier & Unphysical Electrical Surge Detection.

    Error Boundary & Requirements:
    - Input: Inject electrical surge of 1,650 kW into 'total_kw' (substation rated capacity = 800 kW).
    - Threshold: Upper physical limit of 800.0 kW and statistical z-score > 3.5 sigma.
    - Detection: detect_outliers identifies capacity violation and flags record index.
    - System Response:
      * Anomaly mask flags True at spike index.
      * Reason records 'Exceeds Physical Capacity (>800.0 kW)'.
      * Quality banner alerts operator to unphysical surge requiring engineering inspection.
    """
    spike_df = clean_df.copy()
    spike_idx = spike_df.index[-10]
    spike_df.loc[spike_idx, "total_kw"] = 1650.0  # Massive physical outlier exceeding 800 kW limit
    
    outlier_mask, flagged = detect_outliers(spike_df, column="total_kw", max_physical_kw=800.0)
    assert outlier_mask.any(), "Outlier detector must flag reading exceeding physical capacity"
    assert spike_idx in flagged.index, f"Flagged outliers must contain index {spike_idx}"
    assert "Exceeds Physical Capacity" in flagged.loc[spike_idx, "outlier_reason"], (
        "Flagged reason must indicate physical capacity exceedance"
    )
    
    q_info = evaluate_data_quality(spike_df, edge_case_type="EXTREME_OUTLIER")
    assert any("extreme meter reading" in msg.lower() for msg in q_info["messages"]), (
        "Diagnostic message must alert operator to extreme meter surge reading"
    )
