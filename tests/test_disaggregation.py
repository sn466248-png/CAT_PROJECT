import unittest
import os
import pandas as pd
import numpy as np

from src.data_loader import load_dataset, get_summary_metrics
from src.disaggregation import (
    compute_load_disaggregation,
    analyze_peak_demand_period,
    get_evidence_chains,
    calculate_mv_experiment_results
)
from src.edge_cases import evaluate_data_quality
from preprocessing.clean_data import chronological_split
from models.disaggregation import (
    predict_rule_based_disaggregation,
    NILMDisaggregator,
    benchmark_disaggregation_methods
)

class TestEnergyDisaggregation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_df = load_dataset(edge_case_type="NONE")

    def test_load_dataset(self):
        self.assertFalse(self.sample_df.empty)
        self.assertIn("total_kw", self.sample_df.columns)
        self.assertIn("hvac_kw", self.sample_df.columns)
        self.assertIn("process_kw", self.sample_df.columns)
        self.assertIn("lighting_kw", self.sample_df.columns)
        self.assertIn("aux_kw", self.sample_df.columns)

    def test_load_disaggregation(self):
        disagg = compute_load_disaggregation(self.sample_df)
        self.assertIn("HVAC", disagg)
        self.assertIn("Process Equipment", disagg)
        self.assertIn("Lighting", disagg)
        self.assertIn("Auxiliary / Other", disagg)
        self.assertGreater(disagg["Total_kWh"], 0)

    def test_peak_demand_analysis(self):
        peak_res = analyze_peak_demand_period(self.sample_df)
        self.assertIn("top_contributor", peak_res)
        self.assertGreater(peak_res["avg_total_peak_kw"], 0)

    def test_evidence_chains(self):
        chains = get_evidence_chains(self.sample_df)
        self.assertGreaterEqual(len(chains), 3)
        for chain in chains:
            self.assertIn("meter_data", chain)
            self.assertIn("load_category", chain)
            self.assertIn("equipment_schedule", chain)
            self.assertIn("context", chain)
            self.assertIn("tariff_period", chain)
            self.assertIn("recommended_action", chain)

    def test_mv_experiment_results(self):
        mv_res = calculate_mv_experiment_results(self.sample_df)
        self.assertIn("baseline_mean_peak_kw", mv_res)
        self.assertIn("post_mean_peak_kw", mv_res)
        self.assertIn("measured_avg_reduction_pct", mv_res)
        self.assertGreater(mv_res["measured_avg_reduction_pct"], 0)
        self.assertGreater(mv_res["kw_demand_saved"], 0)

    def test_edge_cases_evaluation(self):
        # Clean Data
        q_none = evaluate_data_quality(self.sample_df, edge_case_type="NONE")
        self.assertEqual(q_none["status"], "FRESH")
        self.assertEqual(q_none["confidence_pct"], 95.0)

        # Stale Data
        stale_df = load_dataset(edge_case_type="STALE_DATA")
        q_stale = evaluate_data_quality(stale_df, edge_case_type="STALE_DATA")
        self.assertEqual(q_stale["status"], "STALE")
        self.assertFalse(q_stale["actions_allowed"])

        # Missing Occupancy Data
        missing_occ_df = load_dataset(edge_case_type="MISSING_OCCUPANCY")
        q_occ = evaluate_data_quality(missing_occ_df, edge_case_type="MISSING_OCCUPANCY")
        self.assertEqual(q_occ["status"], "MISSING")
        self.assertLess(q_occ["confidence_pct"], 90.0)

        # Missing Timestamps Data
        missing_ts_df = load_dataset(edge_case_type="MISSING_TIMESTAMPS")
        q_ts = evaluate_data_quality(missing_ts_df, edge_case_type="MISSING_TIMESTAMPS")
        self.assertEqual(q_ts["status"], "REDUCED CONFIDENCE")

    def test_rule_based_disaggregation(self):
        rb_preds = predict_rule_based_disaggregation(self.sample_df.head(100))
        self.assertEqual(len(rb_preds), 100)
        for col in ["hvac_kw", "process_kw", "lighting_kw", "aux_kw"]:
            self.assertIn(col, rb_preds.columns)
            self.assertTrue((rb_preds[col] >= 0).all())

    def test_nilm_model_and_conservation_of_energy(self):
        train_df, val_df, test_df = chronological_split(self.sample_df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        model = NILMDisaggregator(n_estimators=15, random_state=42)
        model.fit(train_df)
        self.assertTrue(model.is_fitted)

        test_sample = test_df.head(50).copy()
        preds = model.predict(test_sample)

        # Check Conservation of Energy: sum of predicted loads must equal total_kw
        predicted_sum = preds.sum(axis=1).values
        actual_total = test_sample["total_kw"].values
        np.testing.assert_allclose(predicted_sum, actual_total, rtol=1e-2)

    def test_benchmark_metrics_improvement(self):
        train_df, val_df, test_df = chronological_split(self.sample_df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        model = NILMDisaggregator(n_estimators=15, random_state=42)
        model.fit(train_df)
        
        bench_df, summary = benchmark_disaggregation_methods(test_df.head(100), model)
        self.assertIn("MAE (kW)", bench_df.columns)
        self.assertIn("RMSE (kW)", bench_df.columns)
        self.assertIn("R² Score", bench_df.columns)
        self.assertIn("NMBE (%)", bench_df.columns)
        self.assertIn("CV(RMSE) (%)", bench_df.columns)
        
        # NILM model should achieve lower MAE than the static rule-based heuristic
        self.assertGreater(summary["mae_improvement_pct"], 0.0)

if __name__ == "__main__":
    unittest.main()
