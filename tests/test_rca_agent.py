from agents.rca_agent import RCAAgent


def _handoff(records):
    return {
        "synapt_context": {"answer": "advisory telecom context"},
        "retrieved_incidents": [
            {
                "incident_id": f"INC-{index}",
                "scores": {"hybrid": score},
                "incident": record,
            }
            for index, (score, record) in enumerate(records, start=1)
        ],
    }


def test_congestion_query_ranks_combined_congestion_hypothesis():
    records = [
        (0.95, {"incident_id": "C1", "latency_ms": 220, "packet_loss_rate": 8, "throughput_mbps": 25}),
        (0.90, {"incident_id": "C2", "latency_ms": 180, "packet_loss_rate": 6, "throughput_mbps": 30}),
        (0.85, {"incident_id": "C3", "latency_ms": 160, "packet_loss_rate": 5, "throughput_mbps": 35}),
        (0.80, {"incident_id": "R1", "signal_strength_dbm": -115, "call_drop_rate": 5, "handover_success_rate": 80}),
        (0.75, {"incident_id": "R2", "signal_strength_dbm": -110, "call_drop_rate": 4, "handover_success_rate": 82}),
        (0.70, {"incident_id": "A1", "critical_alarm_count": 3, "alarm_count": 10}),
    ]
    result = RCAAgent().process(
        "High latency, packet loss, and reduced throughput are observed.",
        _handoff(records),
    )

    assert result["status"] == "success"
    assert result["summary"]["top_hypothesis"] == "congestion / transport-capacity degradation"
    assert result["summary"]["evaluated_incident_count"] == 6
    assert set(result["hypotheses"][0]["supporting_incident_ids"]) >= {"INC-1", "INC-2"}
    assert result["hypotheses"][0]["score_label"] == "evidence-ranking score"
    assert any("Current network metrics were unavailable" in item for item in result["hypotheses"][0]["evidence"]["limitations"])


def test_radio_query_produces_different_evidence_supported_ranking():
    records = [
        (0.95, {"incident_id": "C1", "latency_ms": 220, "packet_loss_rate": 8, "throughput_mbps": 25}),
        (0.90, {"incident_id": "C2", "latency_ms": 180, "packet_loss_rate": 6, "throughput_mbps": 30}),
        (0.85, {"incident_id": "R1", "signal_strength_dbm": -120, "call_drop_rate": 7, "handover_success_rate": 75}),
        (0.80, {"incident_id": "R2", "signal_strength_dbm": -115, "call_drop_rate": 6, "handover_success_rate": 78}),
        (0.75, {"incident_id": "R3", "signal_strength_dbm": -112, "call_drop_rate": 5, "handover_success_rate": 80}),
        (0.70, {"incident_id": "A1", "critical_alarm_count": 3, "alarm_count": 10}),
    ]
    result = RCAAgent().process(
        "Weak signal, dropped calls, and poor handover success are observed.",
        _handoff(records),
    )

    assert result["status"] == "success"
    assert result["summary"]["top_hypothesis"] == "mobility / handover instability"
    assert "INC-3" in result["hypotheses"][0]["supporting_incident_ids"]


def test_identical_evidence_can_legitimately_produce_same_leading_hypothesis():
    handoff = _handoff([
        (0.9, {"incident_id": "I1", "latency_ms": 200, "packet_loss_rate": 7, "throughput_mbps": 20}),
        (0.8, {"incident_id": "I2", "latency_ms": 190, "packet_loss_rate": 6, "throughput_mbps": 25}),
    ])
    agent = RCAAgent()
    first = agent.process("High latency and reduced throughput.", handoff)
    second = agent.process("High latency and reduced throughput.", handoff)
    assert first["summary"]["top_hypothesis"] == second["summary"]["top_hypothesis"]


def test_query_without_supported_metric_returns_insufficient_evidence():
    result = RCAAgent().process(
        "Find similar incidents and explain what happened.",
        _handoff([(0.9, {"incident_id": "I1", "latency_ms": 200})]),
    )
    assert result["status"] == "insufficient_evidence"
    assert result["hypotheses"] == []
