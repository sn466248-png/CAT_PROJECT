# Actionable Energy-Use Disaggregation & M&V Platform

[![Actionable Energy Disaggregation CI](https://github.com/sn466248-png/CAT_PROJECT/actions/workflows/ci.yml/badge.svg)](https://github.com/sn466248-png/CAT_PROJECT/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)
![ASHRAE Guideline 14](https://img.shields.io/badge/ASHRAE%2014-Compliant%20(PASS)-brightgreen)
![Tests](https://img.shields.io/badge/Tests-30%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

An end-to-end operational energy decision-support platform for industrial facilities and commercial campuses. Features benchmarked **Machine Learning Non-Intrusive Load Monitoring (NILM)** disaggregation, **ASHRAE Guideline 14** automated Measurement & Verification (NMBE & CV(RMSE)), whole-facility savings accounting, strict chronological validation, automated unit testing, and GitHub Actions CI/CD workflows.

---

## 🚀 Key Platform Capabilities

1. **Supervised ML / NILM Disaggregation Engine:**
   - Multi-target Random Forest regressor replacing static heuristics.
   - Enforces physical **Conservation of Energy**: $\sum \hat{P}_{\text{equipment}} \equiv P_{\text{total\_meter}}$.
   - Chronological Train / Val / Test time-series split (Days 1–21 Train, Days 22–25 Val, Days 26–30 Test) preventing data leakage.
2. **Empirical Disaggregation Benchmark:**
   - Direct statistical comparison between Rule-Based Baseline and ML/NILM across **MAE, RMSE, R², NMBE, and CV(RMSE)**.
   - Reduces mean absolute attribution error from **15.10 kW to 2.82 kW** (an **81.3% error reduction**).
3. **Automated ASHRAE Guideline 14 M&V Validation:**
   - Evaluates **Normalized Mean Bias Error (NMBE = -0.0%)** (limit $\le \pm 10\%$).
   - Evaluates **Coefficient of Variation of RMSE (CV(RMSE) = 29.70%)** (limit $\le 30\%$).
   - Calculates fractional savings uncertainty ($U_{95} = \pm 13.39\%$).
4. **Verified Energy Savings Accounting (IPMVP Option C):**
   - Baseline Peak: **621.44 kW** $\rightarrow$ Post-Intervention Peak: **255.55 kW** (**365.89 kW / 58.88% peak shaved**).
   - Total verified monthly financial savings: **$17,584.42 / month** ($9,147.25 demand charge + $8,437.17 energy cost).
5. **5-Scenario Data Quality & Failure Engine:**
   - Tested under Missing Meter Values (Case 1), Stale Data (Case 2), Missing Occupancy (Case 3), Schedule Mismatch (Case 4), and Extreme Surge Outliers (Case 5).
6. **Automated Testing & GitHub CI/CD:**
   - 30 unit tests across 5 pytest suites (`test_data.py`, `test_data_quality.py`, `test_disaggregation.py`, `test_mv.py`, `test_savings.py`).
   - Automated GitHub Actions matrix workflow testing across Python 3.11, 3.12, and 3.13 (`.github/workflows/ci.yml`).

---

## 📁 Repository Structure

```text
cat project/
├── .github/
│   └── workflows/
│       └── ci.yml                   # Automated GitHub Actions CI workflow
├── data/
│   ├── industrial_energy_data.csv   # Master 15-min interval time-series telemetry (3,552 records)
│   ├── meter_data.csv               # Partitioned meter telemetry
│   ├── equipment_schedule.csv       # Partitioned equipment schedules
│   ├── occupancy_data.csv           # Partitioned occupancy and production units
│   └── field_observations.json      # Offline local storage queue for field inspections
├── models/
│   ├── __init__.py
│   ├── disaggregation.py            # NILM Random Forest, Rule-Based baseline & benchmark engine
│   └── trained_model.pkl            # Calibrated serializable ML/NILM model
├── mv/
│   ├── __init__.py
│   ├── metrics.py                   # ASHRAE Guideline 14 metrics (NMBE, CV(RMSE), MAE, R²)
│   └── savings.py                   # Automated IPMVP Option C savings & uncertainty calculator
├── preprocessing/
│   ├── __init__.py
│   └── clean_data.py                # Telemetry cleaning, outlier detection, schedule audits, lags
├── src/
│   ├── __init__.py
│   ├── data_loader.py               # Ingestion, caching, and edge-case fault injectors
│   ├── disaggregation.py            # Backward-compatible disaggregation & evidence solver
│   ├── edge_cases.py                # Quality indicator evaluator (5 failure scenarios)
│   ├── low_bandwidth.py             # Minimal text/table renderer for poor connectivity
│   ├── views_executive.py           # Executive C-suite ROI & peak shaving view
│   ├── views_energy_manager.py      # Energy Manager disaggregation & drill-down view
│   ├── views_facilities.py          # Facilities Operator schedule matrix & live simulator
│   ├── views_field_tech.py          # Mobile field inspection logger & sync queue
│   ├── views_ml_mv.py               # Dedicated ML/NILM benchmark & ASHRAE 14 M&V Hub
│   └── documentation.py             # Embedded analytical reports & stakeholder validation
├── tests/
│   ├── test_data.py                 # Data loading, cleaning, features, chronological split tests
│   ├── test_data_quality.py         # 5 failure cases testing (missing, stale, outlier, mismatch)
│   ├── test_disaggregation.py       # Rule-based vs NILM model and conservation of energy tests
│   ├── test_mv.py                   # ASHRAE 14 NMBE, CV(RMSE), and compliance tests
│   └── test_savings.py              # Automated savings formulas & uncertainty tests
├── app.py                           # Main Streamlit web application
├── generate_data.py                 # Physics-informed dataset generator
├── pytest.ini                       # Pytest test discovery & path configuration
├── requirements.txt                 # Python dependencies
├── evaluation_report.md             # Comprehensive 70% milestone technical report
├── evaluation_report_100pct.md      # Final 100% capstone evaluation report
└── README.md                        # Documentation & API specifications
```

---

## 🗄️ Database & Telemetry Storage Schema

### 1. Master Telemetry: `data/industrial_energy_data.csv`
Contains 3,552 records sampled at 15-minute intervals across 37 calendar days (2026-08-01 00:00 through 2026-09-06 23:45):

| Column Name | Data Type | Units / Range | Physical Meaning & Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | `string (ISO-8601)` | `YYYY-MM-DD HH:MM:SS` | 15-minute timestamp index (e.g. `2026-08-01 00:00:00`). |
| `total_kw` | `float64` | `40.0 – 625.0 kW` | Total aggregate electrical real power measured at main facility substation. |
| `total_kwh` | `float64` | `10.0 – 156.25 kWh` | Total interval energy consumption ($\text{total\_kw} \times 0.25\text{ h}$). |
| `hvac_kw` | `float64` | `15.0 – 180.0 kW` | Sub-metered chilled water plant, AHUs, and condenser pump demand. |
| `process_kw` | `float64` | `0.0 – 350.0 kW` | Sub-metered manufacturing production equipment (Line 1 & Line 2). |
| `lighting_kw` | `float64` | `8.0 – 48.0 kW` | Sub-metered lighting panels across high-bay warehouse and office areas. |
| `aux_kw` | `float64` | `12.0 – 32.0 kW` | Sub-metered data center, IT infrastructure, and emergency baseload. |
| `ambient_temp_c` | `float64` | `16.0 – 38.0 °C` | Outdoor dry-bulb air temperature driving HVAC thermal cooling loads. |
| `occupancy_pct` | `float64` | `0.0 – 100.0 %` | Normalized facility occupancy derived from security badge-access sensors. |
| `production_units`| `int64` | `0 – 120 units/15m` | Factory manufacturing throughput units produced in interval. |
| `tariff_period` | `string (categorical)`| `Off-Peak, Normal, Peak` | TOU billing window ($0.08 off-peak, $0.18 normal, $0.35 peak 18:00–22:00). |
| `tariff_rate_usd`| `float64` | `$0.08, $0.18, $0.35` | Electricity energy charge rate in USD per kWh. |
| `hvac_scheduled` | `int64 (binary)` | `0 or 1` | Equipment schedule mask (1 = scheduled active, 0 = setback/off). |
| `process_scheduled`| `int64 (binary)` | `0 or 1` | Equipment schedule mask for manufacturing lines. |
| `lighting_scheduled`| `int64 (binary)`| `0 or 1` | Equipment schedule mask for interior lighting. |
| `aux_scheduled` | `int64 (binary)` | `1` | Auxiliary baseload is permanently scheduled active. |
| `is_intervention`| `int64 (binary)` | `0 or 1` | M&V indicator (0 = Days 1–30 Baseline, 1 = Days 31–37 Reporting). |
| `data_quality_flag`| `string` | `NOMINAL, OUTLIER, ...` | Data quality indicator tagged during ingestion. |
| `datetime` | `datetime64[ns]` | Datetime index | Parsed timestamp utilized for cyclical feature engineering. |

### 2. Partitioned Schemas
- `data/meter_data.csv`: Partitioned electrical meter telemetry (`timestamp`, `total_kw`, `total_kwh`, `hvac_kw`, `process_kw`, `lighting_kw`, `aux_kw`).
- `data/equipment_schedule.csv`: Equipment schedule binary operational masks (`timestamp`, `hvac_scheduled`, `process_scheduled`, `lighting_scheduled`, `aux_scheduled`).
- `data/occupancy_data.csv`: Contextual variables (`timestamp`, `occupancy_pct`, `production_units`, `ambient_temp_c`, `tariff_period`).
- `data/field_observations.json`: Mobile technician inspection log with schema:
  ```json
  [
    {
      "observation_id": "OBS-1042",
      "timestamp": "2026-09-29 18:30:00",
      "equipment": "HVAC Chiller #2",
      "issue_type": "Schedule Override",
      "technician": "T. Martinez",
      "status": "RESOLVED",
      "notes": "Chilled water setpoint adjusted to 9°C for peak shedding."
    }
  ]
  ```

---

## 🔌 Core Python API Endpoints & Function Signatures

### 1. `models.disaggregation`

#### `NILMDisaggregator(n_estimators: int = 60, random_state: int = 42)`
Supervised Non-Intrusive Load Monitoring decomposition engine using multi-target Random Forest with Conservation of Energy enforcement.
* **`fit(train_df: pd.DataFrame) -> NILMDisaggregator`**: Fits model on backward-looking features against targets `['hvac_kw', 'process_kw', 'lighting_kw', 'aux_kw']`.
* **`predict(df: pd.DataFrame) -> pd.DataFrame`**: Predicts sub-loads with physical post-processing: $\hat{y}_i \times \frac{P_{\text{total}}}{\sum \hat{y}_j}$.
* **`get_feature_importances() -> pd.DataFrame`**: Returns ranked Gini feature importances across all input dimensions.
* **`save(filepath: str) -> None` / `load(filepath: str) -> NILMDisaggregator`**: Serializes / deserializes trained model.

#### `predict_rule_based_disaggregation(df: pd.DataFrame) -> pd.DataFrame`
Computes legacy deterministic 35% baseline disaggregation using schedule masks and time-of-day load ratios.

#### `benchmark_disaggregation_methods(test_df: pd.DataFrame, nilm_model: NILMDisaggregator, rule_based_preds: pd.DataFrame = None) -> Tuple[pd.DataFrame, Dict[str, Any]]`
Generates comprehensive benchmark table comparing Rule-Based Baseline vs NILM across MAE, RMSE, R², NMBE, and CV(RMSE).

---

### 2. `mv.metrics`

#### `calculate_nmbe(y_true: np.ndarray, y_pred: np.ndarray, p: int = 1) -> float`
Calculates ASHRAE Guideline 14 Normalized Mean Bias Error in percent:
$$\text{NMBE} = \frac{\sum_{i=1}^n (y_i - \hat{y}_i)}{(n - p) \cdot \bar{y}} \times 100\%$$

#### `calculate_cv_rmse(y_true: np.ndarray, y_pred: np.ndarray, p: int = 1) -> float`
Calculates ASHRAE Guideline 14 Coefficient of Variation of RMSE in percent:
$$\text{CV(RMSE)} = \frac{\sqrt{\frac{1}{n-p}\sum_{i=1}^n (y_i - \hat{y}_i)^2}}{\bar{y}} \times 100\%$$

#### `evaluate_ashrae14_compliance(nmbe: float, cv_rmse: float, time_resolution: str = "hourly") -> Dict[str, Any]`
Audits calibration error against ASHRAE Guideline 14 thresholds (Hourly: $|\text{NMBE}| \le 10\%$, $\text{CV} \le 30\%$; Monthly: $|\text{NMBE}| \le 5\%$, $\text{CV} \le 15\%$).

#### `compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray, p: int = 1, time_resolution: str = "15-min") -> Dict[str, Any]`
Convenience wrapper returning dictionary with `n_observations`, `p_parameters`, `mae`, `rmse`, `r2`, `nmbe`, `cv_rmse`, and `compliance`.

---

### 3. `mv.savings`

#### `calculate_automated_savings(df: pd.DataFrame, target_reduction_pct: float = 10.0, demand_charge_usd_per_kw: float = 25.0, peak_tariff_usd_per_kwh: float = 0.35, p_params: int = 4) -> Dict[str, Any]`
Computes verified IPMVP Option C whole-facility savings separating baseline from reporting data:
* Measured baseline vs reporting peak demands.
* Peak demand shaved ($\text{kW}$) and energy reduction ($\% = \frac{E_{\text{base}} - E_{\text{rep}}}{E_{\text{base}}} \times 100$).
* Monthly demand charge savings ($\Delta \text{kW}_{\text{peak}} \times \$25.00$).
* Monthly energy cost savings ($\Delta \text{kWh}_{\text{daily}} \times 30 \times \$0.35$).
* ASHRAE Guideline 14 NMBE and CV(RMSE).
* Fractional Savings Uncertainty at 95% Confidence:
  $$U_{95} = 1.96 \cdot \frac{\text{CV(RMSE)}}{F_{\text{savings}}} \cdot \sqrt{\frac{1 + 2/n}{m}}$$

---

### 4. `preprocessing.clean_data`

* **`clean_energy_data(df: pd.DataFrame) -> pd.DataFrame`**: Enforces non-negative values, parses ISO timestamps, and chronologically sorts records.
* **`feature_engineering(df: pd.DataFrame) -> pd.DataFrame`**: Generates cyclical time harmonics ($\sin/\cos$ hour & day-of-week), lag telemetry (`total_kw_lag1`, `total_kw_lag4`), rolling statistics (`rolling_mean_4`, `rolling_std_4`), cooling degree hours ($\text{CDH}_{18.3}$), and temperature-occupancy interaction terms without forward-looking data leakage.
* **`chronological_split(df: pd.DataFrame, train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`**: Chronologically partitions time series preventing future information contamination.
* **`detect_outliers(df: pd.DataFrame, column: str = "total_kw", z_thresh: float = 3.5, max_physical_kw: float = 800.0) -> Tuple[pd.Series, pd.DataFrame]`**: Detects substation capacity violations and statistical anomalies.
* **`detect_schedule_mismatch(df: pd.DataFrame, hvac_threshold: float = 75.0, lighting_threshold: float = 30.0) -> pd.DataFrame`**: Detects after-hours electrical draw during unscheduled intervals.

---

### 5. `src.edge_cases`

* **`evaluate_data_quality(df: pd.DataFrame, edge_case_type: str = "NONE") -> Dict[str, Any]`**: Evaluates data freshness (`FRESH`, `STALE`, `MISSING`, `REDUCED CONFIDENCE`), calculates confidence score (0–100%), and sets execution locks (`actions_allowed`, `savings_claim_locked`).

---

## 🧪 Granular Unit Testing & Error Boundaries

The platform incorporates **30 automated unit tests** across 5 suites passing with 100% success:

```text
tests/
├── test_data.py          (6 tests)  -> Data ingestion, cleaning, feature lags, chronological splitting
├── test_data_quality.py  (5 tests)  -> 5 fault scenarios (missing, stale, occupancy, mismatch, surge)
├── test_disaggregation.py(9 tests)  -> Heuristics, NILM, Conservation of Energy, benchmark gains
├── test_mv.py            (5 tests)  -> ASHRAE 14 NMBE, CV(RMSE), zero-error, compliance bounds
└── test_savings.py       (5 tests)  -> IPMVP Option C savings, tariffs, 95% CI uncertainty
```

### Granular Test Suite Matrix

| Test Suite | Test Function Name | Objective & Coverage | Mathematical / Behavioral Assertion |
| :--- | :--- | :--- | :--- |
| `test_data.py` | `test_load_dataset` | Telemetry loading & column presence | Asserts all sub-load columns exist and dataset is non-empty. |
| | `test_clean_dataset_negative_clipping` | Non-physical negative power removal | Verifies $\min(\text{kW}) \ge 0.0$ across all sensors. |
| | `test_clean_dataset_sorting` | Chronological sorting verification | Asserts timestamps are monotonically strictly increasing. |
| | `test_feature_engineering_no_forward_leakage` | Forward leakage prevention | Confirms lags use strictly $t-k$ and rolling windows are backward-looking. |
| | `test_chronological_split_preserves_order` | Time-series partition integrity | Verifies $\max(T_{\text{train}}) < \min(T_{\text{val}}) < \min(T_{\text{test}})$. |
| | `test_partitioned_csv_files_exist` | Storage persistence audit | Asserts all required partitioned CSV telemetry files exist on disk. |
| `test_data_quality.py` | `test_case1_missing_meter_values` | Case 1: Missing telemetry injection | Asserts confidence $\le 50\%$, `actions_allowed = False`, `savings_claim_locked = True`. |
| | `test_case2_stale_meter_data` | Case 2: Frozen feed detection | Asserts status == `STALE`, confidence $\le 50\%$, `savings_claim_locked = True`. |
| | `test_case3_missing_occupancy_data` | Case 3: Offline occupancy sensors | Asserts status == `MISSING`, confidence drops below nominal 90%. |
| | `test_case4_equipment_schedule_mismatch` | Case 4: Nighttime HVAC leakage | Asserts schedule mismatch detector flags active HVAC $> 75\text{ kW}$ off-schedule. |
| | `test_case5_unexpected_extreme_meter_value` | Case 5: Electrical capacity surge | Flags surge $> 800\text{ kW}$ capacity with reason `Exceeds Physical Capacity`. |
| `test_disaggregation.py` | `test_load_dataset` | Primary meter structure test | Validates schema conformance of loaded data. |
| | `test_load_disaggregation` | Sub-load percentage rollup | Verifies cumulative kWh $> 0$ and category percentage shares sum to 100%. |
| | `test_peak_demand_analysis` | Peak contributor identification | Asserts primary contributor during 18:00–22:00 window is correctly identified. |
| | `test_evidence_chains` | Traceable root-cause evidence | Verifies complete 6-link causal chains from meter to recommended action. |
| | `test_mv_experiment_results` | Preliminary M&V experiment | Verifies baseline peak demand, post-intervention demand, and savings. |
| | `test_edge_cases_evaluation` | Multi-scenario status states | Verifies status transitions across clean, stale, missing, and corrupted feeds. |
| | `test_rule_based_disaggregation` | Legacy heuristic baseline | Verifies heuristic predictions produce non-negative outputs matching rows. |
| | `test_nilm_model_and_conservation_of_energy` | Physical Conservation of Energy | Verifies $\left\|\sum \hat{y}_i - P_{\text{total}}\right\|_{\infty} \le 0.01\text{ kW}$ (zero synthetic energy). |
| | `test_benchmark_metrics_improvement` | Empirical accuracy verification | Asserts NILM achieves strictly higher accuracy ($> 70\%$ MAE improvement) over heuristic. |
| `test_mv.py` | `test_perfect_prediction_zero_error` | Ideal zero-error baseline | Asserts $\text{MAE} = 0$, $\text{RMSE} = 0$, $\text{NMBE} = 0$, $\text{CV} = 0$, $R^2 = 1.0$. |
| | `test_nmbe_sign_and_formula` | NMBE sign and $(n-p)$ degrees penalty | Verifies $(+40 / (3 \times 125)) \times 100 = 10.67\%$ with positive underprediction sign. |
| | `test_cv_rmse_formula` | CV(RMSE) mathematical formula | Asserts $\frac{\sqrt{400/3}}{250} \times 100 = 4.62\%$ exactly matches ASHRAE formulation. |
| | `test_ashrae14_compliance_evaluation` | ASHRAE 14 pass/fail boundaries | Asserts compliant (PASS) vs NMBE fail ($>10\%$) vs CV(RMSE) fail ($>30\%$). |
| | `test_compute_all_metrics_dict` | Metric dictionary consistency | Verifies all 6 primary statistical keys are returned and correctly typed. |
| `test_savings.py` | `test_automated_savings_keys` | IPMVP Option C schema audit | Asserts all required financial, physical, and uncertainty keys are present. |
| | `test_peak_demand_reduction_formula` | Avoided peak demand formula | Verifies $\Delta P_{\text{peak}} = P_{\text{base, max}} - P_{\text{rep, max}} > 0$. |
| | `test_energy_reduction_percentage_formula` | Avoided energy percentage formula | Verifies reduction $\ge 10.0\%$ target and sets `target_achieved = True`. |
| | `test_financial_calculations` | Demand charge and TOU tariff | Asserts $\text{Demand Savings} = \Delta \text{kW} \times \$25.00$ and total savings reconciliation. |
| | `test_missing_period_raises_value_error` | Missing period boundary check | Asserts passing dataset missing baseline or reporting raises `ValueError`. |

### Exact Error Boundaries & Tolerances

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXACT SYSTEM ERROR BOUNDARIES                         │
├────────────────────────────────┬──────────────────────┬─────────────────────┤
│ Dimension / Metric             │ Mathematical Boundary│ System Action       │
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ Conservation of Energy         │ |Σ ŷ_i - P_total| ≤ 0.01 kW │ Enforced via physical│
│                                │                      │ normalization layer │
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ ASHRAE 14 NMBE (Sub-hourly)    │ |NMBE| ≤ 10.0%       │ Evaluated; triggers │
│ ASHRAE 14 NMBE (Monthly)       │ |NMBE| ≤ 5.0%        │ audit flag if failed│
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ ASHRAE 14 CV(RMSE) (Sub-hourly)│ CV(RMSE) ≤ 30.0%     │ Evaluated; triggers │
│ ASHRAE 14 CV(RMSE) (Monthly)   │ CV(RMSE) ≤ 15.0%     │ audit flag if failed│
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ Physical Substation Capacity   │ P_total ≤ 800.0 kW   │ Flags outlier surge │
│ Statistical Power Outlier      │ z-score ≤ 3.5 σ      │ Flags abnormal peak │
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ Telemetry Freshness Freeze     │ Latency ≤ 6.0 hours  │ If exceeded: STALE, │
│                                │                      │ locks savings claim │
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ Missing Data Tolerances        │ Null count == 0      │ If NaNs present:    │
│                                │                      │ locks savings claim │
├────────────────────────────────┼──────────────────────┼─────────────────────┤
│ Nighttime HVAC Deadband        │ kW ≤ 75.0 kW         │ Flags off-schedule  │
│ Nighttime Lighting Deadband    │ kW ≤ 30.0 kW         │ leakage if exceeded │
└────────────────────────────────┴──────────────────────┴─────────────────────┘
```

---

## 🔬 Empirical Benchmark: Rule-Based Baseline vs ML/NILM

Evaluated on an unseen chronological test partition (Days 26–30 of pre-intervention baseline):

| Equipment Category | Method | MAE (kW) | RMSE (kW) | R² Score | NMBE (%) | CV(RMSE) (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **HVAC System** | Rule-Based Baseline | 14.45 | 18.21 | 0.921 | +0.69% | 17.20% |
| **HVAC System** | **ML / NILM (Random Forest)** | **3.05** | **3.86** | **0.996** | **+0.08%** | **3.66%** |
| **Process Equipment** | Rule-Based Baseline | 17.59 | 23.28 | 0.952 | -14.25% | 20.79% |
| **Process Equipment** | **ML / NILM (Random Forest)** | **3.77** | **5.02** | **0.998** | **-0.01%** | **4.50%** |
| **Lighting Systems** | Rule-Based Baseline | 15.93 | 19.17 | -2.807 | +10.09% | 30.11% |
| **Lighting Systems** | **ML / NILM (Random Forest)** | **2.11** | **2.73** | **0.922** | **+0.01%** | **4.31%** |
| **Other / Auxiliary** | Rule-Based Baseline | 12.41 | 13.96 | -20.861 | +21.97% | 34.85% |
| **Other / Auxiliary** | **ML / NILM (Random Forest)** | **2.35** | **2.90** | **0.058** | **-0.21%** | **7.26%** |
| **Campus Average** | Rule-Based Baseline | 15.10 | 18.66 | -3.20 | +4.62% | 25.74% |
| **Campus Average** | **ML / NILM (Random Forest)** | **2.82** | **3.63** | **0.744** | **-0.03%** | **4.93%** |

> **Key Finding:** ML/NILM reduces mean absolute attribution error from **15.10 kW to 2.82 kW**, representing an **81.3% reduction in disaggregation error**.

---

## ⚡ Quick Start & Verification

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Automated Pytest Suite (30 Tests)
```bash
pytest -v --durations=10
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run app.py
```

---

## 🧪 Edge Case & Fault Simulator Controls

In the sidebar **Edge Case & Fault Simulator**, select from:
1. **NONE:** Clean real-time telemetry (95% confidence).
2. **MISSING_METER_VALUES (Case 1):** Missing meter intervals; avoids silent filling, triggers warnings, locks savings claims.
3. **STALE_DATA (Case 2):** Delayed or frozen telemetry (> 6 hours); locks savings verification.
4. **MISSING_OCCUPANCY (Case 3):** Offline occupancy sensors; drops confidence to fallback baseline.
5. **SCHEDULE_MISMATCH (Case 4):** Detects off-schedule equipment draw ($>75\text{ kW}$ HVAC).
6. **EXTREME_OUTLIER (Case 5):** Flags electrical surges exceeding physical capacity ($> 800\text{ kW}$).
7. **MISSING_TIMESTAMPS:** Corrupted time telemetry; disables aggregate trendlines.
