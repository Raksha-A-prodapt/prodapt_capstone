from __future__ import annotations

import unittest

from agents.impact_analysis import NetworkImpactAnalyzer


class NetworkImpactAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = NetworkImpactAnalyzer()

    def test_without_metrics_reports_impact_as_unavailable(self) -> None:
        result = self.analyzer.analyze(None)

        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["findings"], [])

    def test_flags_dataset_relative_indicators_without_claiming_impact(self) -> None:
        result = self.analyzer.analyze(
            {
                "latency_ms": 145.0,
                "packet_loss_rate": 13.0,
                "cell_availability": 95.0,
            }
        )

        self.assertEqual(result["status"], "available")
        self.assertEqual(
            [finding["metric"] for finding in result["findings"]],
            ["latency_ms", "packet_loss_rate"],
        )
        self.assertTrue(
            all(
                finding["confirmed_impact"] is False
                for finding in result["findings"]
            )
        )
        self.assertIn("dataset-relative", result["basis"])

    def test_includes_prediction_as_unconfirmed_model_evidence(self) -> None:
        result = self.analyzer.analyze(
            {"latency_ms": 100.0},
            {
                "prediction": {
                    "network_performance": {
                        "status": "success",
                        "predicted_throughput_mbps": 250.0,
                    }
                }
            },
        )

        prediction_findings = [
            item
            for item in result["findings"]
            if item["metric"] == "predicted_throughput_mbps"
        ]
        self.assertEqual(len(prediction_findings), 1)
        self.assertFalse(prediction_findings[0]["confirmed_impact"])


if __name__ == "__main__":
    unittest.main()
