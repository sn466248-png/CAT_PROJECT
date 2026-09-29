import numpy as np
import pandas as pd


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Cleans raw industrial energy telemetry:

    - Ensures datetime parsing and sorting
    - Replaces negative power values with 0.0
    - Detects missing readings and logs cleaning interventions
    - Returns cleaned DataFrame and cleaning audit report
    """
    clean_df = df.copy()

    # Datetime conversion
    if "datetime" not in clean_df.columns:
        if "timestamp" in clean_df.columns:
            clean_df["datetime"] = pd.to_datetime(
                clean_df["timestamp"], errors="coerce"
            )
        else:
            raise KeyError("Neither 'datetime' nor 'timestamp' found in dataset")

    # Sort chronologically
    clean_df = clean_df.sort_values("datetime").reset_index(drop=True)

    cleaning_report = {
        "total_records": len(clean_df),
        "missing_timestamps": int(clean_df["datetime"].isna().sum()),
        "negative_kw_clipped": 0,
        "missing_values_per_col": {},
    }

    # Count missing values
    for col in clean_df.columns:
        n_missing = int(clean_df[col].isna().sum())
        if n_missing > 0:
            cleaning_report["missing_values_per_col"][col] = n_missing

    # Non-negative power enforcement
    power_cols = [
        "total_kw",
        "hvac_kw",
        "process_kw",
        "lighting_kw",
        "aux_kw",
        "total_kwh",
    ]
    for col in power_cols:
        if col in clean_df.columns:
            neg_mask = clean_df[col] < 0
            n_neg = int(neg_mask.sum())
            if n_neg > 0:
                cleaning_report["negative_kw_clipped"] += n_neg
                clean_df.loc[neg_mask, col] = 0.0

    return clean_df, cleaning_report


def detect_outliers(
    df: pd.DataFrame,
    column: str = "total_kw",
    threshold_sigma: float = 3.5,
    max_physical_kw: float = 800.0,
) -> tuple[pd.Series, pd.DataFrame]:
    """Detects unexpected extreme meter spikes/outliers (Part 6 Case 5).

    Flagged if value deviates by > threshold_sigma standard deviations from the rolling mean
    or exceeds the physical facility electrical capacity limit (max_physical_kw).
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in dataframe")

    series = df[column].astype(float)
    rolling_mean = (
        series.rolling(window=96, min_periods=8, center=True)
        .mean()
        .bfill()
        .ffill()
    )
    rolling_std = (
        series.rolling(window=96, min_periods=8, center=True)
        .std()
        .bfill()
        .ffill()
    )
    rolling_std = rolling_std.replace(0, 1e-6)

    z_scores = (series - rolling_mean).abs() / rolling_std

    statistical_outliers = z_scores > threshold_sigma
    physical_outliers = series > max_physical_kw

    outlier_mask = statistical_outliers | physical_outliers

    flagged_records = df[outlier_mask].copy()
    if not flagged_records.empty:
        flagged_records["z_score"] = z_scores[outlier_mask].round(2)
        flagged_records["outlier_reason"] = np.where(
            physical_outliers[outlier_mask],
            f"Exceeds Physical Capacity ({max_physical_kw} kW)",
            f"Statistical Spike (Z-Score > {threshold_sigma})",
        )

    return outlier_mask, flagged_records


def detect_schedule_mismatch(
    df: pd.DataFrame,
    hvac_threshold: float = 75.0,
    lighting_threshold: float = 35.0,
    process_threshold: float = 80.0,
) -> pd.DataFrame:
    """Detects equipment operational schedule mismatches (Part 6 Case 4).

    Identifies intervals where equipment is scheduled OFF but draws significant load.
    """
    mismatches = []

    if (
        "hvac_scheduled" in df.columns
        and "hvac_kw" in df.columns
        and "is_intervention" in df.columns
    ):
        hvac_leak = (df["hvac_scheduled"] == 0) & (
            df["hvac_kw"] > hvac_threshold
        )
        if hvac_leak.any():
            for idx in df[hvac_leak].index:
                mismatches.append(
                    {
                        "index": idx,
                        "timestamp": str(df.loc[idx, "timestamp"]),
                        "equipment": "HVAC System",
                        "draw_kw": float(df.loc[idx, "hvac_kw"]),
                        "threshold_kw": hvac_threshold,
                        "scheduled_status": "OFF (0)",
                        "severity": (
                            "HIGH"
                            if df.loc[idx, "hvac_kw"] > 110.0
                            else "MEDIUM"
                        ),
                    }
                )

    if "lighting_scheduled" in df.columns and "lighting_kw" in df.columns:
        light_leak = (df["lighting_scheduled"] == 0) & (
            df["lighting_kw"] > lighting_threshold
        )
        if light_leak.any():
            for idx in df[light_leak].index:
                mismatches.append(
                    {
                        "index": idx,
                        "timestamp": str(df.loc[idx, "timestamp"]),
                        "equipment": "Lighting Systems",
                        "draw_kw": float(df.loc[idx, "lighting_kw"]),
                        "threshold_kw": lighting_threshold,
                        "scheduled_status": "OFF (0)",
                        "severity": (
                            "HIGH"
                            if df.loc[idx, "lighting_kw"] > 55.0
                            else "MEDIUM"
                        ),
                    }
                )

    return pd.DataFrame(mismatches)


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Generates features for supervised ML / NILM disaggregation without forward data leakage:

    - Temporal & cyclical sine/cosine encodings
    - Backward-looking lag variables (15 min, 1 hour)
    - Rolling window statistics (mean, std)
    - Weather & occupancy interaction variables
    """
    feat_df = df.copy()

    if "datetime" not in feat_df.columns:
        feat_df["datetime"] = pd.to_datetime(feat_df["timestamp"])

    # Temporal components
    feat_df["hour"] = feat_df["datetime"].dt.hour
    feat_df["minute"] = feat_df["datetime"].dt.minute
    feat_df["decimal_hour"] = feat_df["hour"] + feat_df["minute"] / 60.0
    feat_df["day_of_week"] = feat_df["datetime"].dt.dayofweek
    feat_df["is_weekend"] = (feat_df["day_of_week"] >= 5).astype(int)

    # Cyclical encodings (smooth representations of time)
    feat_df["sin_hour"] = np.sin(2 * np.pi * feat_df["decimal_hour"] / 24.0)
    feat_df["cos_hour"] = np.cos(2 * np.pi * feat_df["decimal_hour"] / 24.0)
    feat_df["sin_dow"] = np.sin(2 * np.pi * feat_df["day_of_week"] / 7.0)
    feat_df["cos_dow"] = np.cos(2 * np.pi * feat_df["day_of_week"] / 7.0)

    # Lags & Rolling Statistics on aggregate meter (Strictly backward-looking)
    if "total_kw" in feat_df.columns:
        feat_df["total_kw_lag1"] = (
            feat_df["total_kw"].shift(1).bfill()
        )  # 15-min prior
        feat_df["total_kw_lag4"] = (
            feat_df["total_kw"].shift(4).bfill()
        )  # 1-hour prior
        feat_df["total_kw_rolling_mean_4"] = (
            feat_df["total_kw"]
            .rolling(window=4, min_periods=1)
            .mean()
            .bfill()
        )
        feat_df["total_kw_rolling_std_4"] = (
            feat_df["total_kw"]
            .rolling(window=4, min_periods=1)
            .std()
            .fillna(0.0)
        )

    # Ambient temperature features & cooling degree hours (ASHRAE base 18.3°C / 65°F)
    if "ambient_temp_c" in feat_df.columns:
        feat_df["cdh_18_3"] = np.maximum(0.0, feat_df["ambient_temp_c"] - 18.3)
        feat_df["temp_rolling_mean_4"] = (
            feat_df["ambient_temp_c"]
            .rolling(window=4, min_periods=1)
            .mean()
            .bfill()
        )
    else:
        feat_df["cdh_18_3"] = 0.0
        feat_df["temp_rolling_mean_4"] = 22.0

    # Occupancy interaction
    if "occupancy_pct" in feat_df.columns:
        feat_df["occupancy_norm"] = feat_df["occupancy_pct"].fillna(0.0) / 100.0
        if "ambient_temp_c" in feat_df.columns:
            feat_df["temp_occupancy_interaction"] = (
                feat_df["ambient_temp_c"].fillna(22.0)
                * feat_df["occupancy_norm"]
            )
        else:
            feat_df["temp_occupancy_interaction"] = (
                22.0 * feat_df["occupancy_norm"]
            )
    else:
        feat_df["occupancy_norm"] = 0.5
        feat_df["temp_occupancy_interaction"] = 11.0

    # Tariff peak flag
    if "tariff_period" in feat_df.columns:
        feat_df["is_peak_tariff"] = (feat_df["tariff_period"] == "Peak").astype(
            int
        )
    else:
        feat_df["is_peak_tariff"] = (
            (feat_df["decimal_hour"] >= 18.0)
            & (feat_df["decimal_hour"] < 22.0)
            & (feat_df["is_weekend"] == 0)
        ).astype(int)

    return feat_df


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    baseline_only: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits dataset strictly chronologically to prevent time-series data leakage.

    If baseline_only=True, splits the pre-intervention period (is_intervention == 0)
    into Train, Validation, and Test sets, preserving the post-intervention period for M&V.
    """
    if baseline_only and "is_intervention" in df.columns:
        work_df = df[df["is_intervention"] == 0].copy()
    else:
        work_df = df.copy()

    if "datetime" not in work_df.columns and "timestamp" in work_df.columns:
        work_df["datetime"] = pd.to_datetime(work_df["timestamp"])

    work_df = work_df.sort_values("datetime").reset_index(drop=True)
    n = len(work_df)

    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_df = work_df.iloc[:n_train].copy().reset_index(drop=True)
    val_df = (
        work_df.iloc[n_train : n_train + n_val].copy().reset_index(drop=True)
    )
    test_df = work_df.iloc[n_train + n_val :].copy().reset_index(drop=True)

    return train_df, val_df, test_df
