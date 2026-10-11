from __future__ import annotations

import math

import pytest

from classification import classify_kpi, classify_network_performance


def test_higher_and_lower_boundaries_are_inclusive_for_better_band() -> None:
    assert classify_kpi("Throughput (Mbps)", 500)["classification"] == "Good"
    assert classify_kpi("Latency (ms)", 50)["classification"] == "Good"
    assert classify_kpi("Latency (ms)", 100)["classification"] == "Moderate"
    assert classify_kpi("Handover Success Rate (%)", 95)["classification"] == "Moderate"


def test_all_kpi_directions_and_critical_values() -> None:
    assert classify_kpi("Packet Loss Rate (%)", 8)["classification"] == "Critical"
    assert classify_kpi("Call Drop Rate (%)", 3)["classification"] == "Poor"
    assert classify_kpi("Handover Success Rate (%)", 89)["classification"] == "Critical"
    assert classify_kpi("Connection Setup Success Rate (%)", 99)["classification"] == "Good"


def test_overall_critical_override_and_score() -> None:
    values = {
        "Throughput (Mbps)": 600,
        "Latency (ms)": 40,
        "Packet Loss Rate (%)": 0.5,
        "Call Drop Rate (%)": 0.2,
        "Handover Success Rate (%)": 99,
        "Jitter (ms)": 5,
        "Connection Setup Success Rate (%)": 99.5,
    }
    result = classify_network_performance(values)
    assert result["overall_risk"] == "Low"
    assert 0 <= result["performance_score"] <= 100

    values["Packet Loss Rate (%)"] = 16
    result = classify_network_performance(values)
    assert result["overall_risk"] == "Critical"
    assert "Packet Loss Rate (%)" in result["responsible_kpis"]


def test_incomplete_or_invalid_predictions_do_not_get_good_classification() -> None:
    result = classify_network_performance({"Throughput (Mbps)": math.nan})
    assert result["status"] == "incomplete"
    assert result["performance_score"] is None
    with pytest.raises(ValueError):
        classify_kpi("Latency (ms)", float("inf"))
