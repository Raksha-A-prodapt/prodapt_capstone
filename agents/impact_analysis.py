"""Evidence-based network impact assessment from supplied telemetry."""

from __future__ import annotations

from typing import Any

from config.metric_thresholds import CLASSIFICATION_RISK_THRESHOLDS


IMPACT_DETAILS = {
    "latency_ms": (
        "Responsiveness-sensitive services may experience delay."
    ),
    "packet_loss_rate": (
        "Traffic reliability may be degraded, affecting voice or data quality."
    ),
    "call_drop_rate": (
        "Call continuity may be affected."
    ),
    "handover_success_rate": (
        "Mobility between cells may be impaired."
    ),
    "cell_availability": (
        "Service availability for the affected cell may be reduced."
    ),
    "throughput_mbps": (
        "Available user data capacity may be reduced."
    ),
    "signal_strength_dbm": (
        "Coverage or radio-link quality may be weak."
    ),
    "jitter_ms": (
        "Real-time service quality may be inconsistent."
    ),
    "alarm_count": (
        "The number of active network alarms is elevated."
    ),
}


class NetworkImpactAnalyzer:
    """Describe potential service effects without asserting root cause."""

    def analyze(
        self,
        network_metrics: dict[str, Any] | None,
        prediction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not network_metrics:
            return {
                "status": "not_applicable",
                "basis": "No current network metrics were supplied.",
                "findings": [],
                "limitations": [
                    "Potential current service impact cannot be assessed without telemetry."
                ],
            }

        findings = []
        for field, operator, label, threshold in CLASSIFICATION_RISK_THRESHOLDS:
            raw_value = network_metrics.get(field)
            if raw_value is None:
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            if not (value > threshold if operator == ">" else value < threshold):
                continue
            findings.append(
                {
                    "metric": field,
                    "observed_value": value,
                    "dataset_relative_rule": {
                        "operator": operator,
                        "threshold": threshold,
                        "label": label,
                    },
                    "potential_impact": IMPACT_DETAILS.get(
                        field,
                        "This metric is outside the configured dataset-relative range.",
                    ),
                    "confirmed_impact": False,
                }
            )

        prediction_values = (prediction or {}).get("prediction", {})
        throughput = prediction_values.get("network_performance", {})
        if throughput.get("status") == "success":
            findings.append(
                {
                    "metric": "predicted_throughput_mbps",
                    "observed_value": throughput.get(
                        "predicted_throughput_mbps"
                    ),
                    "potential_impact": (
                        "Model-estimated throughput indicates expected data capacity; "
                        "compare with an actual throughput measurement before treating "
                        "this as an observed service impact."
                    ),
                    "confirmed_impact": False,
                    "source": "network performance prediction model",
                }
            )

        return {
            "status": "available",
            "basis": (
                "Supplied telemetry and model outputs. Thresholds are "
                "dataset-relative triage indicators, not telecom standards."
            ),
            "findings": findings,
            "limitations": [
                "Potential impacts are not confirmed customer or service outcomes.",
                "The assessment does not establish causation; consult RCA hypotheses separately.",
            ],
        }
