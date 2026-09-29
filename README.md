# Actionable Energy-Use Disaggregation & M&V Platform (70% Milestone)

[![Actionable Energy Disaggregation CI](https://github.com/owner/cat-project/actions/workflows/ci.yml/badge.svg)](https://github.com/owner/cat-project/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)
![ASHRAE Guideline 14](https://img.shields.io/badge/ASHRAE%2014-Compliant%20(PASS)-brightgreen)
![Tests](https://img.shields.io/badge/Tests-30%20passed-brightgreen)

An end-to-end operational energy decision-support platform for industrial facilities and commercial campuses. Upgraded from the initial 35% prototype to **70% completion**, featuring benchmarked **Machine Learning Non-Intrusive Load Monitoring (NILM)** disaggregation, **ASHRAE Guideline 14** automated Measurement & Verification (NMBE & CV(RMSE)), whole-facility savings accounting, strict chronological validation, automated unit testing, and GitHub Actions CI.

---

## 🚀 What's New in the 70% Milestone (+35%)

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
4. **Verified Energy Savings Accounting:**
   - Baseline Peak: **621.44 kW** $\rightarrow$ Post-Intervention Peak: **255.55 kW** (**365.89 kW / 58.88% peak shaved**).
   - Total verified monthly financial savings: **$17,584.42 / month** ($9,147.25 demand charge + $8,437.17 energy cost).
5. **5-Scenario Data Quality & Failure Engine:**
   - Tested under Missing Meter Values (Case 1), Stale Data (Case 2), Missing Occupancy (Case 3), Schedule Mismatch (Case 4), and Extreme Surge Outliers (Case 5).
6. **Automated Testing & GitHub CI/CD:**
   - 30 unit tests across 5 pytest suites (`test_data.py`, `test_data_quality.py`, `test_disaggregation.py`, `test_mv.py`, `test_savings.py`).
   - Automated GitHub Actions workflow (`.github/workflows/ci.yml`).

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
├── evaluation_report.md             # Comprehensive 26-point technical evaluation report
└── README.md                        # Documentation
```

---

## 🔬 Benchmark: Rule-Based Baseline vs ML/NILM

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

---

## ⚡ Quick Start & Verification

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Run Automated Pytest Suite (30 Tests)
```bash
pytest -v
```

### 3. Launch Dashboard
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
5. **SCHEDULE_MISMATCH (Case 4):** Detects off-schedule equipment draw.
6. **EXTREME_OUTLIER (Case 5):** Flags electrical surges exceeding physical capacity (> 800 kW).
7. **MISSING_TIMESTAMPS:** Corrupted time telemetry; disables aggregate trendlines.
