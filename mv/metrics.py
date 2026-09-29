import numpy as np
import pandas as pd
from typing import Dict, Any, Union

def calculate_nmbe(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series],
    p: int = 1
) -> float:
    """
    Calculates Normalized Mean Bias Error (NMBE) in percent according to ASHRAE Guideline 14.
    
    Formula:
        NMBE = [ sum(y_true - y_pred) / ((n - p) * mean(y_true)) ] * 100
        
    Parameters:
    - y_true: Actual measured values
    - y_pred: Model predicted / estimated values
    - p: Number of parameters / degrees of freedom in the model (default: 1)
    
    Returns:
    - NMBE in percentage (%)
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    
    # Filter out NaNs
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    y_t = y_t[valid]
    y_p = y_p[valid]
    
    n = len(y_t)
    if n <= p:
        return 0.0
        
    mean_y = np.mean(y_t)
    if mean_y == 0:
        return 0.0
        
    nmbe = (np.sum(y_t - y_p) / ((n - p) * mean_y)) * 100.0
    return float(round(nmbe, 2))

def calculate_cv_rmse(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series],
    p: int = 1
) -> float:
    """
    Calculates Coefficient of Variation of Root Mean Square Error (CV(RMSE)) in percent 
    according to ASHRAE Guideline 14.
    
    Formula:
        CV(RMSE) = [ sqrt( sum((y_true - y_pred)^2) / (n - p) ) / mean(y_true) ] * 100
        
    Parameters:
    - y_true: Actual measured values
    - y_pred: Model predicted / estimated values
    - p: Number of parameters / degrees of freedom in the model (default: 1)
    
    Returns:
    - CV(RMSE) in percentage (%)
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    y_t = y_t[valid]
    y_p = y_p[valid]
    
    n = len(y_t)
    if n <= p:
        return 0.0
        
    mean_y = np.mean(y_t)
    if mean_y == 0:
        return 0.0
        
    rmse_p = np.sqrt(np.sum((y_t - y_p) ** 2) / (n - p))
    cv_rmse = (rmse_p / mean_y) * 100.0
    return float(round(cv_rmse, 2))

def calculate_mae(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series]
) -> float:
    """Calculates Mean Absolute Error (MAE)."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    if np.sum(valid) == 0:
        return 0.0
    return float(round(np.mean(np.abs(y_t[valid] - y_p[valid])), 2))

def calculate_rmse(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series]
) -> float:
    """Calculates standard Root Mean Square Error (RMSE)."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    if np.sum(valid) == 0:
        return 0.0
    return float(round(np.sqrt(np.mean((y_t[valid] - y_p[valid]) ** 2)), 2))

def calculate_r2(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series]
) -> float:
    """Calculates Coefficient of Determination (R^2)."""
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    y_t = y_t[valid]
    y_p = y_p[valid]
    if len(y_t) == 0:
        return 0.0
    ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
    if ss_tot == 0:
        return 0.0
    ss_res = np.sum((y_t - y_p) ** 2)
    return float(round(1.0 - (ss_res / ss_tot), 3))

def evaluate_ashrae14_compliance(
    nmbe: float,
    cv_rmse: float,
    time_resolution: str = "hourly"
) -> Dict[str, Any]:
    """
    Evaluates whether model calibration satisfies ASHRAE Guideline 14 standards.
    
    Criteria:
    - Hourly / Sub-hourly interval data:
        |NMBE| <= 10.0%
        CV(RMSE) <= 30.0%
    - Monthly interval data:
        |NMBE| <= 5.0%
        CV(RMSE) <= 15.0%
    """
    if time_resolution.lower() in ["hourly", "sub-hourly", "15-min", "15min"]:
        nmbe_limit = 10.0
        cv_limit = 30.0
    else:  # monthly
        nmbe_limit = 5.0
        cv_limit = 15.0
        
    nmbe_pass = abs(nmbe) <= nmbe_limit
    cv_pass = cv_rmse <= cv_limit
    is_compliant = nmbe_pass and cv_pass
    
    status_label = "PASS (ASHRAE 14 Compliant)" if is_compliant else "FAIL (Exceeds Limits)"
    
    return {
        "time_resolution": time_resolution,
        "nmbe": nmbe,
        "nmbe_limit": nmbe_limit,
        "nmbe_pass": nmbe_pass,
        "cv_rmse": cv_rmse,
        "cv_rmse_limit": cv_limit,
        "cv_pass": cv_pass,
        "is_compliant": is_compliant,
        "status_label": status_label
    }

def compute_all_metrics(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series],
    p: int = 1,
    time_resolution: str = "15-min"
) -> Dict[str, Any]:
    """
    Convenience function computing the full suite of M&V error metrics.
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    valid = ~np.isnan(y_t) & ~np.isnan(y_p)
    n = int(np.sum(valid))
    
    mae = calculate_mae(y_t, y_p)
    rmse = calculate_rmse(y_t, y_p)
    r2 = calculate_r2(y_t, y_p)
    nmbe = calculate_nmbe(y_t, y_p, p=p)
    cv_rmse = calculate_cv_rmse(y_t, y_p, p=p)
    compliance = evaluate_ashrae14_compliance(nmbe, cv_rmse, time_resolution=time_resolution)
    
    return {
        "n_observations": n,
        "p_parameters": p,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "nmbe": nmbe,
        "cv_rmse": cv_rmse,
        "compliance": compliance
    }
