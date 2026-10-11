"""Rule-based classification for predicted network-performance KPIs.

The thresholds in this module are illustrative starting points for a 5G-style
prototype. They are not validated network-service requirements, 3GPP limits,
or operator SLAs. Keep them configurable and validate them before deployment.
"""

from __future__ import annotations

import math
from typing import Any


KPI_THRESHOLDS: dict[str, dict[str, float | str]] = {
    # Boundaries are ordered from best to worst for each KPI.
    "Throughput (Mbps)": {
        "direction": "higher",
        "good": 500.0,
        "moderate": 300.0,
        "poor": 150.0,
        "critical": 0.0,
    },
    "Latency (ms)": {
        "direction": "lower",
        "good": 50.0,
        "moderate": 100.0,
        "poor": 150.0,
        "critical": 300.0,
    },
    "Packet Loss Rate (%)": {
        "direction": "lower",
        "good": 1.0,
        "moderate": 3.0,
        "poor": 7.0,
        "critical": 15.0,
    },
    "Call Drop Rate (%)": {
        "direction": "lower",
        "good": 0.5,
        "moderate": 1.5,
        "poor": 3.0,
        "critical": 8.0,
    },
    "Handover Success Rate (%)": {
        "direction": "higher",
        "good": 98.0,
        "moderate": 95.0,
        "poor": 90.0,
        "critical": 0.0,
    },
    "Jitter (ms)": {
        "direction": "lower",
        "good": 10.0,
        "moderate": 20.0,
        "poor": 35.0,
        "critical": 100.0,
    },
    "Connection Setup Success Rate (%)": {
        "direction": "higher",
        "good": 99.0,
        "moderate": 97.0,
        "poor": 94.0,
        "critical": 0.0,
    },
}

KPI_WEIGHTS: dict[str, float] = {
    "Throughput (Mbps)": 1.5,
    "Latency (ms)": 1.5,
    "Packet Loss Rate (%)": 1.5,
    "Call Drop Rate (%)": 1.25,
    "Handover Success Rate (%)": 1.0,
    "Jitter (ms)": 0.75,
    "Connection Setup Success Rate (%)": 1.0,
}

CRITICAL_INDICATORS = {
    "Throughput (Mbps)",
    "Latency (ms)",
    "Packet Loss Rate (%)",
    "Call Drop Rate (%)",
}


def validate_configuration() -> None:
    """Raise a clear error if thresholds or weights are malformed."""
    if set(KPI_THRESHOLDS) != set(KPI_WEIGHTS):
        raise ValueError("KPI thresholds and weights must cover the same KPIs.")
    if sum(KPI_WEIGHTS.values()) <= 0 or any(
        not math.isfinite(weight) or weight < 0 for weight in KPI_WEIGHTS.values()
    ):
        raise ValueError("KPI weights must be finite and have a positive total.")
    for kpi, config in KPI_THRESHOLDS.items():
        values = [float(config[name]) for name in ("good", "moderate", "poor", "critical")]
        if config["direction"] == "lower":
            if not values[0] <= values[1] <= values[2] <= values[3]:
                raise ValueError(f"Invalid lower-is-better thresholds for {kpi}.")
        elif config["direction"] == "higher":
            if not values[0] >= values[1] >= values[2] >= values[3]:
                raise ValueError(f"Invalid higher-is-better thresholds for {kpi}.")
        else:
            raise ValueError(f"Unknown threshold direction for {kpi}.")


def classify_kpi(kpi: str, value: Any) -> dict[str, Any]:
    """Classify one KPI. Boundary values belong to the better band."""
    if kpi not in KPI_THRESHOLDS:
        raise KeyError(f"Unsupported KPI: {kpi}")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{kpi} prediction is not numeric.") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{kpi} prediction must be finite.")

    config = KPI_THRESHOLDS[kpi]
    direction = config["direction"]
    good = float(config["good"])
    moderate = float(config["moderate"])
    poor = float(config["poor"])
    if direction == "higher":
        category = (
            "Good" if numeric >= good else
            "Moderate" if numeric >= moderate else
            "Poor" if numeric >= poor else "Critical"
        )
        best, worst = good, poor
    else:
        category = (
            "Good" if numeric <= good else
            "Moderate" if numeric <= moderate else
            "Poor" if numeric <= poor else "Critical"
        )
        best, worst = good, poor

    return {
        "kpi": kpi,
        "value": numeric,
        "classification": category,
        "direction": direction,
        "thresholds": {
            "good": good,
            "moderate": moderate,
            "poor": poor,
            "critical": float(config["critical"]),
        },
        "score": _normalize(numeric, best, worst, direction),
    }


def _normalize(value: float, best: float, worst: float, direction: str) -> float:
    if direction == "higher":
        raw = (value - worst) / (best - worst)
    else:
        raw = (worst - value) / (worst - best)
    return round(max(0.0, min(1.0, raw)) * 100.0, 2)


def classify_network_performance(predictions: dict[str, Any]) -> dict[str, Any]:
    """Classify available seven-KPI predictions and calculate status/score.

    If one or more required KPI predictions are missing or invalid, the result
    is explicitly incomplete and no misleading overall score is returned.
    """
    validate_configuration()
    kpi_classifications: dict[str, dict[str, Any]] = {}
    invalid: dict[str, str] = {}
    for kpi in KPI_THRESHOLDS:
        if kpi not in predictions:
            invalid[kpi] = "Prediction is unavailable."
            continue
        try:
            kpi_classifications[kpi] = classify_kpi(kpi, predictions[kpi])
        except (TypeError, ValueError) as exc:
            invalid[kpi] = str(exc)

    if invalid:
        return {
            "status": "incomplete",
            "kpi_classifications": kpi_classifications,
            "overall_risk": None,
            "performance_score": None,
            "reasons": ["Classification is incomplete because required KPI predictions are unavailable or invalid."],
            "responsible_kpis": list(invalid),
            "invalid_predictions": invalid,
            "threshold_basis": "Illustrative thresholds; not validated against service requirements or SLAs.",
        }

    critical = [k for k, item in kpi_classifications.items() if item["classification"] == "Critical"]
    poor = [k for k, item in kpi_classifications.items() if item["classification"] == "Poor"]
    moderate = [k for k, item in kpi_classifications.items() if item["classification"] == "Moderate"]
    critical_indicators = [k for k in critical if k in CRITICAL_INDICATORS]

    if critical or len(poor) >= 2:
        overall = "Critical" if critical or len(poor) >= 3 else "High"
    elif poor or len(moderate) >= 2:
        overall = "High" if any(k in CRITICAL_INDICATORS for k in poor) else "Medium"
    elif moderate:
        overall = "Medium"
    else:
        overall = "Low"

    responsible = critical + poor + moderate
    if overall == "Low":
        reasons = ["All seven predicted KPIs are within the illustrative Good bands."]
    else:
        reasons = [f"{k}: {kpi_classifications[k]['classification']}" for k in responsible]
    if critical_indicators:
        reasons.insert(0, "A critical service indicator triggered the critical override.")

    total_weight = sum(KPI_WEIGHTS.values())
    score = sum(
        kpi_classifications[k]["score"] * KPI_WEIGHTS[k]
        for k in KPI_THRESHOLDS
    ) / total_weight
    return {
        "status": "success",
        "kpi_classifications": kpi_classifications,
        "overall_risk": overall,
        "performance_score": round(max(0.0, min(100.0, score)), 2),
        "reasons": reasons,
        "responsible_kpis": responsible,
        "threshold_basis": "Illustrative thresholds; not validated against service requirements or SLAs.",
        "score_basis": "Weighted 0-100 normalization between each KPI's Good and Poor boundaries.",
    }


validate_configuration()
