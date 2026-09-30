"""Unit Test Suite: ASHRAE Guideline 14 & M&V Error Metrics (test_mv.py)

This module validates the mathematical formulations and statistical compliance criteria
governing Measurement & Verification (M&V) in accordance with ASHRAE Guideline 14:
1. Normalized Mean Bias Error (NMBE):
   NMBE = [ sum(y_true - y_pred) / ((n - p) * mean(y_true)) ] * 100
2. Coefficient of Variation of Root Mean Square Error (CV(RMSE)):
   CV(RMSE) = [ sqrt( sum((y_true - y_pred)^2) / (n - p) ) / mean(y_true) ] * 100
3. Degree-of-Freedom Penalty (n - p):
   Ensures model complexity (p parameters) is penalized in error calculations.
4. ASHRAE Guideline 14 Compliance Boundaries:
   - Sub-hourly / Hourly interval data: |NMBE| <= 10.0%, CV(RMSE) <= 30.0%
   - Monthly interval data: |NMBE| <= 5.0%, CV(RMSE) <= 15.0%
"""

import pytest
import numpy as np
from mv.metrics import (
    calculate_nmbe,
    calculate_cv_rmse,
    calculate_mae,
    calculate_rmse,
    calculate_r2,
    evaluate_ashrae14_compliance,
    compute_all_metrics
)

def test_perfect_prediction_zero_error():
    """Validates baseline metric behavior under ideal identical predictions.

    Error Boundary:
    - MAE == 0.0, RMSE == 0.0, NMBE == 0.0, CV(RMSE) == 0.0, R^2 == 1.0.
    """
    y_true = np.array([100.0, 150.0, 200.0, 250.0])
    y_pred = np.array([100.0, 150.0, 200.0, 250.0])
    
    assert calculate_mae(y_true, y_pred) == 0.0
    assert calculate_rmse(y_true, y_pred) == 0.0
    assert calculate_r2(y_true, y_pred) == 1.0
    assert calculate_nmbe(y_true, y_pred, p=1) == 0.0
    assert calculate_cv_rmse(y_true, y_pred, p=1) == 0.0

def test_nmbe_sign_and_formula():
    """Validates NMBE sign convention and degrees-of-freedom calculation.

    Mathematical Verification:
    - y_true = [110, 120, 130, 140], mean = 125.0
    - y_pred = [100, 110, 120, 130] (systematic underprediction by 10 kW each)
    - Residuals (y_true - y_pred) = [+10, +10, +10, +10], sum = +40
    - Observations n = 4, Model parameters p = 1 -> Degrees of freedom (n - p) = 3
    - NMBE = (40 / (3 * 125.0)) * 100 = (40 / 375.0) * 100 = 10.667%
    - Positive sign indicates under-estimation by the model according to ASHRAE convention.
    """
    y_true = np.array([110.0, 120.0, 130.0, 140.0])
    y_pred = np.array([100.0, 110.0, 120.0, 130.0])
    
    nmbe = calculate_nmbe(y_true, y_pred, p=1)
    assert nmbe > 0, "NMBE must be positive when model underpredicts"
    assert np.isclose(nmbe, 10.67, atol=0.05), f"Expected NMBE ~10.67%, got {nmbe}%"

def test_cv_rmse_formula():
    """Validates CV(RMSE) formulation against ASHRAE Guideline 14 standards.

    Mathematical Verification:
    - y_true = [100, 200, 300, 400], mean = 250.0
    - y_pred = [110, 190, 310, 390]
    - Residuals = [-10, +10, -10, +10], squared residuals = [100, 100, 100, 100], sum = 400
    - n = 4, p = 1 -> (n - p) = 3
    - Root mean square error = sqrt(400 / 3) = 11.547 kW
    - CV(RMSE) = (11.547 / 250.0) * 100 = 4.619% (~4.62%)
    """
    y_true = np.array([100.0, 200.0, 300.0, 400.0])
    y_pred = np.array([110.0, 190.0, 310.0, 390.0])
    
    cv_rmse = calculate_cv_rmse(y_true, y_pred, p=1)
    assert np.isclose(cv_rmse, 4.62, atol=0.05), f"Expected CV(RMSE) ~4.62%, got {cv_rmse}%"

def test_ashrae14_compliance_evaluation():
    """Validates automated threshold compliance evaluation for hourly/sub-hourly data.

    Compliance Boundaries:
    - PASS: |NMBE| <= 10.0% and CV(RMSE) <= 30.0%
    - FAIL (NMBE): |NMBE| > 10.0% (even if CV(RMSE) is acceptable)
    - FAIL (CV(RMSE)): CV(RMSE) > 30.0% (even if NMBE is acceptable)
    """
    # Compliant case (hourly: |NMBE| <= 10%, CV(RMSE) <= 30%)
    res_pass = evaluate_ashrae14_compliance(nmbe=2.5, cv_rmse=18.0, time_resolution="hourly")
    assert res_pass["is_compliant"] is True
    assert "PASS" in res_pass["status_label"]
    
    # Non-compliant due to high NMBE (> 10%)
    res_fail_nmbe = evaluate_ashrae14_compliance(nmbe=12.5, cv_rmse=18.0, time_resolution="hourly")
    assert res_fail_nmbe["is_compliant"] is False
    assert res_fail_nmbe["nmbe_pass"] is False
    assert "FAIL" in res_fail_nmbe["status_label"]
    
    # Non-compliant due to high CV(RMSE) (> 30%)
    res_fail_cv = evaluate_ashrae14_compliance(nmbe=3.0, cv_rmse=35.0, time_resolution="hourly")
    assert res_fail_cv["is_compliant"] is False
    assert res_fail_cv["cv_pass"] is False
    assert "FAIL" in res_fail_cv["status_label"]

def test_compute_all_metrics_dict():
    """Validates the convenience dictionary containing the complete M&V metric suite.

    Ensures all 6 primary verification keys are returned and correctly typed.
    """
    y_true = np.array([100.0, 150.0, 200.0, 250.0, 300.0])
    y_pred = np.array([102.0, 148.0, 195.0, 252.0, 298.0])
    
    metrics = compute_all_metrics(y_true, y_pred, p=2, time_resolution="15-min")
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    assert "nmbe" in metrics
    assert "cv_rmse" in metrics
    assert "compliance" in metrics
    assert metrics["compliance"]["is_compliant"] is True
