"""Rule-based incident classification and live scenario scoring."""

from __future__ import annotations

import logging
import re
from math import isfinite
from pathlib import Path
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)
FAULT_MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml_model"
    / "models"
    / "fault_tolerance_model.joblib"
)


class IncidentClassificationAgent:
    """Classify historical cases or caller-supplied live metrics."""

    # Empirical P90 cutoffs for high-is-bad metrics and P10 for low-is-bad.
    # These are dataset-relative triage flags, not telecom standards.
    THRESHOLDS = (
        ("latency_ms", ">", "high_latency", 129.9218),
        ("packet_loss_rate", ">", "high_packet_loss", 11.88),
        ("call_drop_rate", ">", "high_call_drop_rate", 3.1338),
        ("handover_success_rate", "<", "low_handover_success", 91.01),
        ("cell_availability", "<", "low_cell_availability", 79.4339),
        ("throughput_mbps", "<", "low_throughput", 304.2482),
        ("signal_strength_dbm", "<", "weak_signal", -114.04),
        ("jitter_ms", ">", "high_jitter", 44.98),
        ("alarm_count", ">=", "high_alarm_count", 14.0),
    )

    PRIORITY_LEVELS = (
        ("P1", "critical", 4),
        ("P2", "high", 2),
        ("P3", "medium", 1),
        ("P4", "low", 0),
    )

    FAULT_RISK_BANDS = (
        ("low", 39.455),
        ("elevated", 48.152),
        ("high", 55.513),
        ("critical", float("inf")),
    )

    SCENARIO_FIELDS = {
        "cell_availability": "cell_availability",
        "cell_availability_percent": "cell_availability",
        "mttr_hours": "mttr_hours",
        "throughput_mbps": "throughput_mbps",
        "latency": "latency_ms",
        "latency_ms": "latency_ms",
        "packet_loss": "packet_loss_rate",
        "packet_loss_rate": "packet_loss_rate",
        "call_drop_rate": "call_drop_rate",
        "call_drops": "call_drop_rate",
        "handover_success_rate": "handover_success_rate",
        "alarm_count": "alarm_count",
        "critical_alarm_count": "critical_alarm_count",
        "parameter_changes": "parameter_changes",
        "successful_configuration_changes": "successful_configuration_changes",
        "data_usage_gb": "data_usage_gb",
        "user_count": "user_count",
        "signal_strength": "signal_strength_dbm",
        "signal_strength_dbm": "signal_strength_dbm",
        "jitter": "jitter_ms",
        "jitter_ms": "jitter_ms",
        "connection_setup_success_rate": "connection_setup_success_rate",
        "security_incidents": "security_incidents",
        "authentication_failures": "authentication_failures",
        "temperature": "temperature_c",
        "temperature_c": "temperature_c",
        "humidity": "humidity_percent",
        "humidity_percent": "humidity_percent",
        "season": "season",
        "weather": "weather",
    }

    def __init__(
        self,
        fault_model_path: str | Path = FAULT_MODEL_PATH,
    ) -> None:
        self.fault_model_path = Path(fault_model_path)
        self.fault_model = None
        if not self.fault_model_path.is_file():
            logger.warning(
                "Fault prediction model not found at %s; "
                "rule-based classification remains available.",
                self.fault_model_path,
            )
            return

        import joblib

        self.fault_model = joblib.load(self.fault_model_path)
        self.fault_model_features = list(
            self.fault_model.feature_names_in_
        )

    @staticmethod
    def _normalize_feature_name(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

    def _predict_fault_occurrence_rate(
        self,
        incident: dict[str, Any],
    ) -> float | None:
        if self.fault_model is None:
            return None

        values = {
            self._normalize_feature_name(str(field)): value
            for field, value in incident.items()
        }
        model_input = {
            feature: values.get(self._normalize_feature_name(feature))
            for feature in self.fault_model_features
        }
        prediction = float(
            self.fault_model.predict(pd.DataFrame([model_input]))[0]
        )
        if not isfinite(prediction):
            raise ValueError(
                "Fault prediction model returned a non-finite value."
            )
        return min(max(prediction, 0.0), 100.0)

    @classmethod
    def _fault_risk_band(cls, prediction: float) -> str:
        for band, upper_bound in cls.FAULT_RISK_BANDS:
            if prediction < upper_bound:
                return band
        return "critical"

    @staticmethod
    def _matches(value: float, operator: str, threshold: float) -> bool:
        if operator == ">":
            return value > threshold
        if operator == ">=":
            return value >= threshold
        return value < threshold

    def classify_incident(
        self,
        incident: dict[str, Any],
    ) -> dict[str, Any]:
        """Classify one historical record or normalized scenario."""
        labels = []
        matched_thresholds = {}
        for field, operator, label, threshold in self.THRESHOLDS:
            raw_value = incident.get(field)
            if raw_value is None:
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            if not isfinite(value) or not self._matches(
                value,
                operator,
                threshold,
            ):
                continue
            labels.append(label)
            matched_thresholds[field] = {
                "operator": operator,
                "threshold": threshold,
                "observed": value,
            }

        priority_code, priority, minimum_count = self.PRIORITY_LEVELS[-1]
        for code, level, count in self.PRIORITY_LEVELS:
            if len(labels) >= count:
                priority_code, priority, minimum_count = code, level, count
                break

        if labels:
            priority_reason = (
                f"{len(labels)} metric threshold(s) exceeded; "
                f"{priority_code} priority requires at least {minimum_count}."
            )
        else:
            priority_reason = (
                "No configured dataset-tail threshold was exceeded."
            )

        classification = {
            "incident_id": incident.get("incident_id"),
            "labels": labels,
            "priority": priority_code,
            "priority_level": priority,
            "priority_reason": priority_reason,
            "classification_basis": "dataset_percentile_triage",
            "thresholds_exceeded": matched_thresholds,
        }
        prediction = self._predict_fault_occurrence_rate(incident)
        if prediction is None:
            classification["fault_prediction"] = {
                "status": "unavailable",
                "reason": "Saved fault prediction model is not available.",
            }
        else:
            classification["fault_prediction"] = {
                "status": "experimental",
                "target": "fault_occurrence_rate",
                "predicted_fault_occurrence_rate_percent": prediction,
                "risk_band": self._fault_risk_band(prediction),
                "model": self.fault_model_path.name,
                "priority_influenced": False,
                "caveat": (
                    "Model report flags possible target leakage; prediction "
                    "is not a calibrated failure probability."
                ),
            }
        return classification

    def classify_scenario(
        self,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Classify live metric input without historical retrieval."""
        if not isinstance(metrics, dict) or not metrics:
            raise ValueError(
                "Live scenario metrics must be a non-empty dictionary."
            )

        normalized_metrics: dict[str, Any] = {}
        numeric_metric_count = 0
        for raw_field, raw_value in metrics.items():
            key = self._normalize_feature_name(str(raw_field))
            field = self.SCENARIO_FIELDS.get(key)
            if field is None:
                raise ValueError(
                    f"Unsupported live scenario field: {raw_field!r}."
                )
            if field in normalized_metrics:
                raise ValueError(
                    f"Live scenario field {field!r} was provided more than once."
                )
            if field in {"season", "weather"}:
                if not isinstance(raw_value, str) or not raw_value.strip():
                    raise ValueError(
                        f"{field} must be a non-empty string."
                    )
                normalized_metrics[field] = raw_value.strip()
                continue

            if isinstance(raw_value, bool):
                raise ValueError(f"{field} must be a finite number.")
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{field} must be a finite number."
                ) from exc
            if not isfinite(value):
                raise ValueError(f"{field} must be a finite number.")
            normalized_metrics[field] = value
            numeric_metric_count += 1

        if numeric_metric_count == 0:
            raise ValueError(
                "Provide at least one numeric network metric."
            )

        classification = self.classify_incident(normalized_metrics)
        classification["classification_basis"] = (
            "live_scenario_dataset_percentile_triage"
        )
        classification["scenario_input"] = normalized_metrics
        classification["historical_retrieval_performed"] = False
        prediction = classification["fault_prediction"]

        if self.fault_model is not None:
            missing_features = [
                feature
                for feature in self.fault_model_features
                if self.SCENARIO_FIELDS.get(
                    self._normalize_feature_name(feature),
                    self._normalize_feature_name(feature),
                )
                not in normalized_metrics
            ]
            prediction["status"] = (
                "experimental_partial_input"
                if missing_features
                else "experimental"
            )
            prediction["input_completeness"] = (
                "partial" if missing_features else "complete"
            )
            prediction["missing_model_features"] = missing_features
            if missing_features:
                prediction["caveat"] += (
                    " Missing inputs were imputed by the saved model."
                )
        return classification

    def classify_results(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Attach classifications and summarize retrieved-case priorities."""
        priority_counts = {
            code: 0
            for code, _, _ in self.PRIORITY_LEVELS
        }
        priority_order = {
            code: index
            for index, (code, _, _) in enumerate(self.PRIORITY_LEVELS)
        }
        classifications = []
        for result in results:
            classification = self.classify_incident(result["incident"])
            result["classification"] = classification
            classifications.append(classification)
            priority_counts[classification["priority"]] += 1

        highest_priority = None
        if classifications:
            highest_priority = min(
                (item["priority"] for item in classifications),
                key=priority_order.__getitem__,
            )
        return {
            "incident_count": len(classifications),
            "priority_counts": priority_counts,
            "highest_priority": highest_priority,
            "incidents": classifications,
        }
