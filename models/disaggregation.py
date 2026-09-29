import os
import pickle
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from mv.metrics import calculate_cv_rmse, calculate_mae, calculate_nmbe, calculate_r2, calculate_rmse
from preprocessing.clean_data import feature_engineering

FEATURE_COLS = [
    "total_kw",
    "ambient_temp_c",
    "occupancy_pct",
    "hour",
    "day_of_week",
    "is_weekend",
    "sin_hour",
    "cos_hour",
    "sin_dow",
    "cos_dow",
    "total_kw_lag1",
    "total_kw_rolling_mean_4",
    "cdh_18_3",
    "temp_occupancy_interaction",
    "is_peak_tariff",
]

TARGET_COLS = ["hvac_kw", "process_kw", "lighting_kw", "aux_kw"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model.pkl")


def predict_rule_based_disaggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic / rule-based energy disaggregation baseline.

    Applies engineering schedule heuristics and historical load ratios to estimate
    equipment-level loads from aggregate meter telemetry.
    """
    preds = pd.DataFrame(index=df.index)

    if "datetime" not in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"])

    hour = df["datetime"].dt.hour + df["datetime"].dt.minute / 60.0
    is_weekend = (df["datetime"].dt.dayofweek >= 5).astype(int)

    # Heuristic ratio allocations
    hvac_ratio = np.where(
        (is_weekend == 0) & (hour >= 6.0) & (hour < 18.5),
        0.30,
        np.where((is_weekend == 0) & (hour >= 18.5) & (hour < 22.0), 0.35, 0.22),
    )
    process_ratio = np.where(
        (is_weekend == 0) & (hour >= 7.5) & (hour < 18.0),
        0.50,
        np.where(
            (is_weekend == 0) & (hour >= 18.0) & (hour < 19.5), 0.45, 0.20
        ),
    )
    lighting_ratio = np.where(
        (hour >= 6.0) & (hour < 22.0),
        0.12,
        0.25,
    )
    aux_ratio = 0.08

    # Normalize heuristic weights to sum to 1.0
    total_weights = hvac_ratio + process_ratio + lighting_ratio + aux_ratio
    hvac_ratio /= total_weights
    process_ratio /= total_weights
    lighting_ratio /= total_weights
    aux_ratio /= total_weights

    total_meter = df["total_kw"].values
    preds["hvac_kw"] = np.round(total_meter * hvac_ratio, 2)
    preds["process_kw"] = np.round(total_meter * process_ratio, 2)
    preds["lighting_kw"] = np.round(total_meter * lighting_ratio, 2)
    preds["aux_kw"] = np.round(total_meter * aux_ratio, 2)

    return preds


class NILMDisaggregator:
    """Supervised Machine Learning / NILM Disaggregation Engine.

    Decomposes aggregate facility electrical load (total_kw) into equipment-level loads:
    - HVAC
    - Process Equipment
    - Lighting Systems
    - Auxiliary Loads

    Enforces physical conservation of energy: sum(predicted_loads) == total_kw.
    """

    def __init__(self, n_estimators: int = 60, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=14,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=1,
        )
        self.feature_names = FEATURE_COLS
        self.target_names = TARGET_COLS
        self.is_fitted = False

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        feat_df = feature_engineering(df)
        missing = [c for c in self.feature_names if c not in feat_df.columns]
        if missing:
            raise KeyError(f"Missing required feature columns: {missing}")
        return feat_df[self.feature_names].fillna(0.0)

    def fit(self, train_df: pd.DataFrame):
        X = self._prepare_features(train_df)
        for target in self.target_names:
            if target not in train_df.columns:
                raise KeyError(
                    f"Training dataset missing target column '{target}'"
                )
        Y = train_df[self.target_names].values
        self.model.fit(X, Y)
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise RuntimeError(
                "NILM model must be fitted before calling predict()."
            )
        X = self._prepare_features(df)
        raw_preds = self.model.predict(X)
        raw_preds = np.maximum(0.0, raw_preds)

        # Enforce Conservation of Energy:
        # Sum of predicted loads must equal actual total meter kW
        pred_sum = np.sum(raw_preds, axis=1, keepdims=True)
        pred_sum = np.where(pred_sum == 0, 1.0, pred_sum)

        total_kw = df["total_kw"].values.reshape(-1, 1)
        normalized_preds = raw_preds * (total_kw / pred_sum)

        pred_df = pd.DataFrame(
            normalized_preds, columns=self.target_names, index=df.index
        ).round(2)
        return pred_df

    def get_feature_importances(self) -> pd.DataFrame:
        if not self.is_fitted:
            return pd.DataFrame()
        importances = self.model.feature_importances_
        return (
            pd.DataFrame(
                {"Feature": self.feature_names, "Importance": importances}
            )
            .sort_values("Importance", ascending=False)
            .reset_index(drop=True)
        )

    def save(self, filepath: str = MODEL_PATH):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str = MODEL_PATH):
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return pickle.load(f)


def train_or_load_nilm_model(
    train_df: pd.DataFrame, filepath: str = MODEL_PATH, retrain: bool = False
) -> NILMDisaggregator:
    """Loads cached NILM model from disk or trains a new one if not present."""
    if not retrain and os.path.exists(filepath):
        try:
            model = NILMDisaggregator.load(filepath)
            if model is not None and model.is_fitted:
                return model
        except Exception:
            pass

    model = NILMDisaggregator()
    model.fit(train_df)
    try:
        model.save(filepath)
    except Exception:
        pass
    return model


def benchmark_disaggregation_methods(
    test_df: pd.DataFrame,
    nilm_model: NILMDisaggregator,
    rule_based_preds: pd.DataFrame = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Compares the Rule-Based Deterministic Baseline vs Supervised ML/NILM Disaggregation.

    Calculates: MAE, RMSE, R^2, NMBE (%), and CV(RMSE) (%) for each equipment category
    and overall on the unseen test dataset.
    """
    if rule_based_preds is None:
        rule_based_preds = predict_rule_based_disaggregation(test_df)

    ml_preds = nilm_model.predict(test_df)

    categories = [
        ("HVAC", "hvac_kw"),
        ("Process", "process_kw"),
        ("Lighting", "lighting_kw"),
        ("Other / Aux", "aux_kw"),
    ]

    benchmark_rows = []

    for cat_label, col_name in categories:
        y_true = test_df[col_name].values
        y_rule = rule_based_preds[col_name].values
        y_ml = ml_preds[col_name].values

        # Rule-based metrics
        rb_mae = calculate_mae(y_true, y_rule)
        rb_rmse = calculate_rmse(y_true, y_rule)
        rb_r2 = calculate_r2(y_true, y_rule)
        rb_nmbe = calculate_nmbe(y_true, y_rule, p=1)
        rb_cv_rmse = calculate_cv_rmse(y_true, y_rule, p=1)

        # ML / NILM metrics
        ml_mae = calculate_mae(y_true, y_ml)
        ml_rmse = calculate_rmse(y_true, y_ml)
        ml_r2 = calculate_r2(y_true, y_ml)
        ml_nmbe = calculate_nmbe(y_true, y_ml, p=4)
        ml_cv_rmse = calculate_cv_rmse(y_true, y_ml, p=4)

        benchmark_rows.append(
            {
                "Equipment": cat_label,
                "Method": "Rule-Based Baseline",
                "MAE (kW)": rb_mae,
                "RMSE (kW)": rb_rmse,
                "R² Score": rb_r2,
                "NMBE (%)": rb_nmbe,
                "CV(RMSE) (%)": rb_cv_rmse,
            }
        )
        benchmark_rows.append(
            {
                "Equipment": cat_label,
                "Method": "ML / NILM (Random Forest)",
                "MAE (kW)": ml_mae,
                "RMSE (kW)": ml_rmse,
                "R² Score": ml_r2,
                "NMBE (%)": ml_nmbe,
                "CV(RMSE) (%)": ml_cv_rmse,
            }
        )

    benchmark_df = pd.DataFrame(benchmark_rows)

    # Average improvement summary
    rb_mean_mae = benchmark_df[
        benchmark_df["Method"] == "Rule-Based Baseline"
    ]["MAE (kW)"].mean()
    ml_mean_mae = benchmark_df[
        benchmark_df["Method"] == "ML / NILM (Random Forest)"
    ]["MAE (kW)"].mean()
    mae_improvement_pct = (
        ((rb_mean_mae - ml_mean_mae) / rb_mean_mae) * 100.0
        if rb_mean_mae > 0
        else 0.0
    )

    summary = {
        "rule_based_mean_mae": round(rb_mean_mae, 2),
        "nilm_mean_mae": round(ml_mean_mae, 2),
        "mae_improvement_pct": round(mae_improvement_pct, 1),
        "test_records_evaluated": len(test_df),
    }

    return benchmark_df, summary
