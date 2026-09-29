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
    y_true = np.array([100.0, 150.0, 200.0, 250.0])
    y_pred = np.array([100.0, 150.0, 200.0, 250.0])
    
    assert calculate_mae(y_true, y_pred) == 0.0
    assert calculate_rmse(y_true, y_pred) == 0.0
    assert calculate_r2(y_true, y_pred) == 1.0
    assert calculate_nmbe(y_true, y_pred, p=1) == 0.0
    assert calculate_cv_rmse(y_true, y_pred, p=1) == 0.0

def test_nmbe_sign_and_formula():
    # If model consistently underpredicts (y_true > y_pred), NMBE is positive
    y_true = np.array([110.0, 120.0, 130.0, 140.0])
    y_pred = np.array([100.0, 110.0, 120.0, 130.0])
    # diff = 10 for each. sum = 40. mean(y_true) = 125. n = 4, p = 1.
    # NMBE = (40 / (3 * 125)) * 100 = (40 / 375) * 100 = 10.67%
    nmbe = calculate_nmbe(y_true, y_pred, p=1)
    assert nmbe > 0
    assert np.isclose(nmbe, 10.67, atol=0.05)

def test_cv_rmse_formula():
    y_true = np.array([100.0, 200.0, 300.0, 400.0])
    y_pred = np.array([110.0, 190.0, 310.0, 390.0])
    # diff = [-10, 10, -10, 10], sq = [100, 100, 100, 100], sum_sq = 400
    # n=4, p=1 -> n-p=3. sqrt(400/3) = 11.547. mean=250.
    # CV(RMSE) = (11.547 / 250) * 100 = 4.62%
    cv_rmse = calculate_cv_rmse(y_true, y_pred, p=1)
    assert np.isclose(cv_rmse, 4.62, atol=0.05)

def test_ashrae14_compliance_evaluation():
    # Compliant case (hourly: |NMBE| <= 10%, CV(RMSE) <= 30%)
    res_pass = evaluate_ashrae14_compliance(nmbe=2.5, cv_rmse=18.0, time_resolution="hourly")
    assert res_pass["is_compliant"] is True
    assert "PASS" in res_pass["status_label"]
    
    # Non-compliant due to high NMBE
    res_fail_nmbe = evaluate_ashrae14_compliance(nmbe=12.5, cv_rmse=18.0, time_resolution="hourly")
    assert res_fail_nmbe["is_compliant"] is False
    assert res_fail_nmbe["nmbe_pass"] is False
    assert "FAIL" in res_fail_nmbe["status_label"]
    
    # Non-compliant due to high CV(RMSE)
    res_fail_cv = evaluate_ashrae14_compliance(nmbe=3.0, cv_rmse=35.0, time_resolution="hourly")
    assert res_fail_cv["is_compliant"] is False
    assert res_fail_cv["cv_pass"] is False

def test_compute_all_metrics_dict():
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
