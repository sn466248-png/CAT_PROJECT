# Comprehensive Technical Evaluation Report: 70% Milestone
## Actionable Energy-Use Disaggregation & M&V Platform

> **Notice on Data Nature:** All experimental and empirical telemetry evaluated herein is derived from a calibrated, physics-informed synthetic industrial dataset (`data/industrial_energy_data.csv`). The operational dynamics, noise distributions, schedule overlaps, and tariff penalties realistically simulate a medium industrial manufacturing campus. All evaluation metrics, statistical errors, and financial values presented are calculated directly from this dataset.

---

### 1. Original Problem
Industrial manufacturing facilities and commercial campuses face exorbitant electricity costs due to peak demand charges ($25/kW) and peak-period time-of-use tariffs ($0.35/kWh between 18:00 and 22:00). Traditional Energy Management Systems (EMS) only provide aggregate meter telemetry (total facility kWh). They fail to answer:
1. *What equipment is driving the peak demand spike?*
2. *Why is energy being consumed during expensive tariff windows?*
3. *What specific operational interventions can be executed?*
4. *How much demand reduction was achieved, and how reliable is the measurement?*

---

### 2. Existing 35% Implementation
The initial 35% prototype delivered the operational foundation:
- 15-minute interval time-series telemetry (3,552 records across 37 days).
- Equipment schedule matrices and contextual zone occupancy data.
- Initial deterministic / rule-based energy disaggregation heuristics.
- Persona-based dashboards (Executive, Energy Manager, Facilities, Field Tech).
- Data freshness indicators (`FRESH`, `STALE`, `MISSING`, `REDUCED CONFIDENCE`).
- Low-bandwidth text/table mode and offline mobile field inspection queue.
- Initial 30-day baseline vs. 7-day intervention experiment.

---

### 3. New 35% Implementation (+35% -> 70% Total Progress)
The current milestone implements:
1. **Supervised ML/NILM Disaggregation Engine:** Random Forest decomposition attributing `total_kw` to HVAC, Process, Lighting, and Auxiliary loads.
2. **Conservation of Energy Constraint:** Strict physical post-processing ($\sum \hat{y}_i \equiv \text{total\_kw}$).
3. **Chronological Time-Series Partitioning:** Strict Train/Val/Test split preventing future information leakage.
4. **Comprehensive Benchmarking:** Direct empirical comparison between Rule-Based Baseline and ML/NILM across MAE, RMSE, R², NMBE, and CV(RMSE).
5. **ASHRAE Guideline 14 M&V Validation:** Mathematical formulation and automated compliance evaluation for NMBE and CV(RMSE).
6. **Automated Measurement & Verification (M&V) Savings Module:** IPMVP Option C whole-facility verification separating measured telemetry, model baseline, avoided demand, and statistical uncertainty.
7. **5-Case Data Quality & Fault Engine:** Testing missing meter intervals, stale feeds, missing occupancy, schedule mismatches, and physical outliers.
8. **Automated Testing Suite:** 30 unit tests across 5 pytest suites passing with 100% success.
9. **GitHub Actions CI/CD Pipeline:** Fully configured workflow testing across Python 3.11, 3.12, and 3.13.

---

### 4. Rule-Based Baseline Disaggregation
The baseline approach applies fixed schedule masks and static engineering load ratio allocations:
- Normal work hours (07:30–18:00): Process ~50%, HVAC ~30%, Lighting ~12%, Aux ~8%.
- Peak window (18:00–22:00): HVAC ~35%, Process ~45%, Lighting ~12%, Aux ~8%.
- Unscheduled / Night (22:00–06:00): Auxiliary baseload ~40%, Lighting leakage ~30%, HVAC setback ~30%.

While computationally trivial, it cannot adapt to dynamic weather shifts, variable manufacturing throughput, or unexpected operational overrides.

---

### 5. ML / NILM Methodology
The Supervised Non-Intrusive Load Monitoring (NILM) decomposition uses a multi-target `RandomForestRegressor` with:
- `n_estimators = 60`, `max_depth = 14`, `min_samples_leaf = 2`, `random_state = 42`.
- Physical constraint normalization:
  $$\hat{y}_{i, \text{normalized}} = \hat{y}_i \times \frac{P_{\text{total\_meter}}}{\sum_{j} \hat{y}_j}$$
Ensures zero fictitious energy is generated or omitted.

---

### 6. Dataset Specification
- **Duration:** 37 calendar days (2026-08-01 through 2026-09-06).
- **Resolution:** 15-minute intervals (96 intervals/day; 3,552 records total).
- **Baseline Period:** Days 1–30 (2,880 records; standard uncoordinated operations).
- **Reporting Period:** Days 31–37 (672 records; operational interventions active).
- **Sub-loads:** HVAC Chiller Plant, Process Line 1 & 2, Lighting Bays, Auxiliary/Data Center.
- **Context:** Ambient temperature (°C), zone occupancy (%), equipment schedule expectations, tariff structures ($0.35 peak, $0.18 normal, $0.08 off-peak).

---

### 7. Feature Engineering
Engineered exclusively with backward-looking features to avoid lookahead bias:
- **Cyclical Time:** $\sin(2\pi h / 24)$, $\cos(2\pi h / 24)$, $\sin(2\pi \text{dow} / 7)$, $\cos(2\pi \text{dow} / 7)$.
- **Lag Telemetry:** `total_kw_lag1` (15 min prior), `total_kw_lag4` (1 hour prior).
- **Rolling Statistics:** `total_kw_rolling_mean_4`, `total_kw_rolling_std_4`.
- **Weather & Thermal:** Cooling Degree Hours ($\max(0, T_{\text{ambient}} - 18.3^\circ\text{C})$).
- **Context Interactions:** $T_{\text{ambient}} \times \text{Occupancy Norm}$.
- **Tariff Indicator:** Binary peak window flag.

---

### 8. Model Training
- **Training Partition:** Days 1–21 (2,016 intervals; 70% of baseline).
- **Validation Partition:** Days 22–25 (384 intervals; 13% of baseline).
- **Testing Partition:** Days 26–30 (433 intervals; 15% of baseline).
- Strict chronological division guarantees zero data leakage.

---

### 9. Test Methodology
Performance is evaluated strictly on the unseen Days 26–30 test partition. Predicted component kW values are compared against ground-truth sub-metered telemetry.

---

### 10–14. Empirical Benchmark Comparison Metrics

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

> **Key Finding:** The ML/NILM approach reduces mean absolute attribution error from **15.10 kW to 2.82 kW**, representing an **81.3% reduction in disaggregation error**.

---

### 15–18. M&V Energy Savings Verification (IPMVP Option C)

- **Baseline Period Demand:** Mean Peak = `412.05 kW`, Max Peak = `621.44 kW`
- **Target Peak Demand Reduction:** `10.0%`
- **Measured Reporting Demand:** Mean Peak = `211.17 kW`, Max Peak = `255.55 kW`
- **Measured Peak Max Shaved:** `365.89 kW` (**58.88% reduction**)
- **Measured Peak Average Reduction:** `200.89 kW` (**48.75% reduction**)
- **Target Achieved:** `True (100% verified)`
- **Daily Peak kWh Saved:** `803.54 kWh/day`
- **Monthly Demand Charge Savings:** `$9,147.25 / month` ($25/kW peak shaved)
- **Monthly Energy Cost Savings:** `$8,437.17 / month` ($0.35/kWh peak energy avoided)
- **Total Monthly Verified Savings:** **`$17,584.42 / month`**

---

### 19. ASHRAE Guideline 14 Error & Uncertainty Analysis
- **NMBE Formula:**
  $$\text{NMBE} = \frac{\sum_{i=1}^n (y_i - \hat{y}_i)}{(n - p) \cdot \bar{y}} \times 100\% = -0.0\% \quad (\text{Threshold: } |\text{NMBE}| \le 10.0\%) \implies \textbf{PASS}$$
- **CV(RMSE) Formula:**
  $$\text{CV(RMSE)} = \frac{\sqrt{\frac{1}{n-p}\sum_{i=1}^n (y_i - \hat{y}_i)^2}}{\bar{y}} \times 100\% = 29.70\% \quad (\text{Threshold: } \text{CV(RMSE)} \le 30.0\%) \implies \textbf{PASS}$$
- **Fractional Savings Uncertainty at 95% Confidence ($U_{95}$):**
  $$U_{95} = 1.96 \cdot \frac{\text{CV(RMSE)}}{F_{\text{savings}}} \cdot \sqrt{\frac{1 + 2/n}{m}} = \pm 13.39\%$$
  Distinguishes firmly between deterministic claim and statistically bounded savings.

---

### 20. Failure Case Analysis & Validation

| Failure Scenario | Input Condition | System Detection & Response | Verification Status |
| :--- | :--- | :--- | :--- |
| **Case 1: Missing Meter Values** | Null/NaN entries in `total_kw` telemetry | Flags missing readings, refuses silent imputation, downgrades confidence to 35%, locks savings claims | Verified in `test_case1_missing_meter_values` |
| **Case 2: Stale Meter Feed** | Telemetry timestamp frozen > 6 hours | Displays `STALE` badge, locks savings claim verification until feed restoration | Verified in `test_case2_stale_meter_data` |
| **Case 3: Missing Occupancy Data** | Occupancy sensor offline (`NaN`) | Displays `MISSING` status, switches HVAC attribution to temperature-only fallback mode | Verified in `test_case3_missing_occupancy_data` |
| **Case 4: Schedule Mismatch** | Equipment running high load outside schedule | Triggers after-hours leakage alert, highlights override switch status in Facilities view | Verified in `test_case4_equipment_schedule_mismatch` |
| **Case 5: Extreme Meter Value** | Demand spike > 800 kW or > 3.5σ | Detects physical substation capacity exceedance, flags anomaly for engineering audit | Verified in `test_case5_unexpected_extreme_meter_value` |

---

### 21. CI / CD and Testing Automation
- **Pytest Suite:** 30 unit tests distributed across 5 modules (`test_data.py`, `test_data_quality.py`, `test_disaggregation.py`, `test_mv.py`, `test_savings.py`).
- **Execution Time:** ~3.1 seconds locally.
- **GitHub Actions Pipeline:** Configured in `.github/workflows/ci.yml` running matrix builds on Python 3.11, 3.12, and 3.13.

---

### 22. Environmental Implications
Reducing 365.89 kW of industrial peak demand between 18:00 and 22:00 displaces high-heat-rate gas turbine peaker plants. Avoids approximately **10,847.8 kg CO2e monthly** (~10.8 metric tons CO2e/month).

---

### 23. Ethical & Privacy Implications
Occupancy telemetry is aggregated at the building/bay level rather than monitoring individual badge scans, preserving employee privacy. View-level RBAC scopes operational controls and financial audits to authorized personas.

---

### 24. Maintenance Implications
The system includes an automated maintenance protocol:
- Annual CT sub-meter calibration.
- Quarterly NILM disaggregation model retraining and validation.
- Bi-annual tariff structure synchronizations.

---

### 25. Current Limitations
1. **Synthetic Telemetry Origin:** While statistically and physically realistic, real facilities encounter non-stationary noise and seasonal equipment degradation.
2. **Supervised Requirement:** The current Random Forest model requires historical sub-metered training data. Truly unsupervised NILM remains an area for further development.

---

### 26. Future Improvements (Roadmap to 100%)
1. Integration of Sequence-to-Point (Seq2Point) deep learning / 1D-CNN architectures for sub-minute telemetry.
2. Automated Modbus / BACnet BMS protocol connectors for bi-directional setpoint automation.
3. Multi-year weather degree-day normalization supporting IPMVP Option C over rolling 3-year horizons.
