"""Small offline DeepEval contract suite for the prediction agent.

This evaluates the agent contract and classification output around the real
checked-in Joblib artifacts. It does not claim to validate model accuracy;
that requires labelled holdout data and is reported separately in the model
evaluation files.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig, CacheConfig, DisplayConfig
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from agents.prediction_agent import NetworkPredictionAgent

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "evaluations" / "reports" / "prediction_agent_deepeval_report.json"

SAMPLES = [
    ("healthy_telemetry", 98.0, 1.0, 0.2, 99.0),
    ("moderate_telemetry", 90.0, 6.0, 1.5, 95.0),
    ("degraded_telemetry", 82.0, 14.0, 4.0, 90.0),
]


def features(availability: float, packet_loss: float, call_drop: float, handover: float) -> dict[str, Any]:
    return {
        "Cell Availability (%)": availability, "MTTR (hours)": 5.0,
        "Throughput (Mbps)": 580.0, "Latency (ms)": 75.0,
        "Packet Loss Rate (%)": packet_loss, "Call Drop Rate (%)": call_drop,
        "Handover Success Rate (%)": handover, "Alarm Count": 10.0,
        "Critical Alarm Count": 2.0, "Parameter Changes": 4.0,
        "Successful Configuration Changes (%)": 97.0, "Data Usage (GB)": 25.0,
        "User Count": 1500.0, "Signal Strength (dBm)": -85.0, "Jitter (ms)": 10.0,
        "Connection Setup Success Rate (%)": 98.0, "Security Incidents": 1.0,
        "Authentication Failures": 3.0, "Temperature (�C)": 25.0,
        "Humidity (%)": 60.0, "Fault Occurrence Rate (%)": 12.0,
        "Season": "Summer", "Weather": "Clear", "City": "Chennai", "State": "Tamil Nadu",
    }


class PredictionContractMetric(BaseMetric):
    def __init__(self) -> None:
        super().__init__()
        self.threshold = 1.0
        self.async_mode = False
        self.verbose_mode = False

    @property
    def __name__(self) -> str:
        return "Prediction Agent Contract"

    def measure(self, test_case: LLMTestCase) -> float:
        payload = json.loads(test_case.actual_output or "{}")
        failures = []
        trace = payload.get("trace", {})
        if trace.get("single_shared_input") is not True:
            failures.append("shared-input trace missing")
        if "network_performance_model" not in trace.get("models_called", []):
            failures.append("performance model was not called")
        if "fault_occurrence_prediction_model" not in trace.get("models_called", []):
            failures.append("fault model was not called")
        performance = payload.get("prediction", {}).get("network_performance", {})
        fault = payload.get("prediction", {}).get("fault_risk", {})
        if performance.get("status") != "success":
            failures.append("performance prediction unavailable")
        if fault.get("status") != "success" or not 0 <= float(fault.get("predicted_fault_occurrence_rate_percent", -1)) <= 100:
            failures.append("fault prediction invalid")
        self.score = 1.0 if not failures else 0.0
        self.success = self.score >= self.threshold
        self.reason = "; ".join(failures) if failures else "Both model outputs are finite and satisfy the shared-input response contract."
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)


def main() -> int:
    agent = NetworkPredictionAgent()
    cases = []
    for name, availability, loss, drop, handover in SAMPLES:
        result = agent.process(features(availability, loss, drop, handover), query=name)
        cases.append(LLMTestCase(name=name, input=name, actual_output=json.dumps(result, default=str), expected_output="Both models run and return valid numeric outputs."))

    evaluation = evaluate(
        test_cases=cases,
        metrics=[PredictionContractMetric()],
        cache_config=CacheConfig(write_cache=False, use_cache=False),
        async_config=AsyncConfig(run_async=False),
        display_config=DisplayConfig(show_indicator=False, print_results=False, verbose_mode=False, inspect_after_run=False),
    )
    rows = []
    for test_result in evaluation.test_results:
        for metric in test_result.metrics_data:
            rows.append({"query": test_result.name, "metric": metric.name, "score": metric.score, "success": metric.success, "reason": metric.reason})
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "framework": "DeepEval",
        "evaluation_type": "offline prediction-agent contract",
        "accuracy_note": "This suite validates integration/output contracts, not model accuracy.",
        "queries": [name for name, *_ in SAMPLES],
        "metrics": rows,
        "passed": sum(bool(row["success"]) for row in rows),
        "total": len(rows),
        "model_trace": agent.process(features(*SAMPLES[0][1:]), query=SAMPLES[0][0]).get("trace", {}),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"DeepEval prediction contract: {report['passed']}/{report['total']} passed")
    print(f"Report: {REPORT_PATH}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
