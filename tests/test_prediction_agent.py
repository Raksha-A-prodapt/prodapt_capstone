from __future__ import annotations

import numpy as np

from agents.prediction_agent import NetworkPredictionAgent
from config.prediction_config import FAULT_FEATURES, THROUGHPUT_FEATURES


class FakeModel:
    def __init__(self, value, features):
        self.value = value
        self.feature_names_in_ = np.asarray(features)

    def predict(self, frame):
        return np.asarray([self.value])


def _features(agent: NetworkPredictionAgent) -> dict[str, object]:
    fields = set(agent._model_features(agent.throughput_model, [])) | set(agent._model_features(agent.fault_model, []))
    result = {field: 1.0 for field in fields}
    result.update({"Season": "Winter", "Weather": "Clear", "City": "Chennai", "State": "TN"})
    result["Temperature (�C)"] = 25.0
    return result


def test_agent_runs_two_models_from_one_input_and_chains_throughput() -> None:
    agent = NetworkPredictionAgent.__new__(NetworkPredictionAgent)
    agent.throughput_model = FakeModel([600, 40, 0.5, 0.2, 99, 5, 99.5], THROUGHPUT_FEATURES)
    agent.fault_model = FakeModel(12.5, FAULT_FEATURES)
    agent.model_errors = {}
    features = _features(agent)
    features.pop("Throughput (Mbps)", None)
    result = agent.process(features, query="predict")
    assert result["status"] == "success"
    assert result["trace"]["single_shared_input"] is True
    assert result["trace"]["fault_chain_used"] == "predicted_performance_kpis"
    assert result["trace"]["models_called"] == ["network_performance_model", "fault_occurrence_prediction_model"]
    assert result["prediction"]["network_performance"]["classification"]["overall_risk"] == "Low"
    assert result["prediction"]["fault_risk"]["predicted_fault_occurrence_rate_percent"] == 12.5


def test_one_output_artifact_is_explicitly_incomplete_for_seven_kpi_classification() -> None:
    agent = NetworkPredictionAgent.__new__(NetworkPredictionAgent)
    agent.throughput_model = FakeModel(600, THROUGHPUT_FEATURES)
    agent.fault_model = FakeModel(12.5, FAULT_FEATURES)
    agent.model_errors = {}
    result = agent.process(_features(agent))
    classification = result["prediction"]["network_performance"]["classification"]
    assert classification["status"] == "incomplete"
    assert classification["performance_score"] is None
