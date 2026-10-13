# """Evidence-ranked, deterministic root-cause hypothesis analysis."""

# from __future__ import annotations

# import math
# import re
# import csv
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# from config.config import CSV_PATH


# class RCAAgent:
#     """Rank investigative hypotheses from Query Agent evidence.

#     Scores are evidence-ranking scores, not calibrated probabilities.
#     Historical alignment is evidence for investigation, not proof of cause.
#     """

#     SIGNAL_FIELDS = {
#         "latency": ("latency_ms",),
#         "packet_loss": ("packet_loss_rate",),
#         "throughput": ("throughput_mbps",),
#         "load": ("user_count", "data_usage_gb"),
#         "signal": ("signal_strength_dbm",),
#         "jitter": ("jitter_ms",),
#         "call_drop": ("call_drop_rate",),
#         "handover": ("handover_success_rate",),
#         "availability": ("cell_availability",),
#         "alarms": ("alarm_count", "critical_alarm_count"),
#         "fault": ("fault_occurrence_rate",),
#         "configuration": ("parameter_changes", "successful_configuration_changes"),
#         "connection": ("connection_setup_success_rate",),
#         "environment": ("temperature_c", "humidity_percent"),
#         "security": ("security_incidents", "authentication_failures"),
#     }
#     METRIC_DIRECTIONS = {
#         "latency_ms": "higher", "packet_loss_rate": "higher",
#         "throughput_mbps": "lower", "signal_strength_dbm": "lower",
#         "user_count": "higher", "data_usage_gb": "higher",
#         "jitter_ms": "higher",
#         "call_drop_rate": "higher", "handover_success_rate": "lower",
#         "cell_availability": "lower", "alarm_count": "higher",
#         "critical_alarm_count": "higher", "fault_occurrence_rate": "higher",
#         "security_incidents": "higher", "authentication_failures": "higher",
#         "parameter_changes": "higher", "successful_configuration_changes": "lower",
#         "connection_setup_success_rate": "lower", "temperature_c": "higher",
#         "humidity_percent": "higher",
#     }
#     # The registry is intentionally broader than what one dataset can prove.
#     # A profile is emitted only when its query signals have usable evidence.
#     HYPOTHESIS_PROFILES = (
#         {"label": "capacity and network congestion", "signals": {"latency", "throughput", "load"}, "metrics": ("latency_ms", "throughput_mbps", "user_count", "data_usage_gb")},
#         {"label": "packet loss and transmission instability", "signals": {"packet_loss", "jitter"}, "metrics": ("packet_loss_rate", "jitter_ms")},
#         {"label": "radio signal quality degradation", "signals": {"packet_loss", "signal", "jitter"}, "metrics": ("packet_loss_rate", "signal_strength_dbm", "jitter_ms")},
#         {"label": "poor radio coverage", "signals": {"signal", "availability"}, "metrics": ("signal_strength_dbm", "cell_availability")},
#         {"label": "mobility and handover instability", "signals": {"handover", "call_drop", "signal"}, "metrics": ("handover_success_rate", "call_drop_rate", "signal_strength_dbm")},
#         {"label": "equipment or hardware degradation", "signals": {"fault", "alarms", "environment"}, "metrics": ("fault_occurrence_rate", "alarm_count", "critical_alarm_count", "temperature_c")},
#         {"label": "configuration or parameter-change issues", "signals": {"configuration"}, "metrics": ("parameter_changes", "successful_configuration_changes")},
#         {"label": "alarm-intensive operational faults", "signals": {"alarms", "fault"}, "metrics": ("alarm_count", "critical_alarm_count", "fault_occurrence_rate")},
#         {"label": "transport or backhaul degradation", "signals": {"latency", "packet_loss", "throughput", "jitter"}, "metrics": ("latency_ms", "packet_loss_rate", "throughput_mbps", "jitter_ms")},
#         {"label": "connection establishment failures", "signals": {"connection", "availability"}, "metrics": ("connection_setup_success_rate", "cell_availability")},
#         {"label": "security or authentication disruption", "signals": {"security"}, "metrics": ("security_incidents", "authentication_failures")},
#         {"label": "environmental stress", "signals": {"environment", "fault"}, "metrics": ("temperature_c", "humidity_percent", "fault_occurrence_rate")},
#         {"label": "availability and service outages", "signals": {"availability", "connection"}, "metrics": ("cell_availability", "connection_setup_success_rate")},
#         {"label": "quality-of-service instability", "signals": {"latency", "packet_loss", "throughput", "jitter", "call_drop"}, "metrics": ("latency_ms", "packet_loss_rate", "throughput_mbps", "jitter_ms", "call_drop_rate")},
#     )
#     UNKNOWN_LABEL = "unknown, mixed-cause or insufficient-evidence"

#     def __init__(self, max_hypotheses: int = 5, max_evidence_incidents: int = 100) -> None:
#         self.max_hypotheses = max(1, max_hypotheses)
#         self.max_evidence_incidents = max(1, max_evidence_incidents)
#         self.reference_distributions = self._load_reference_distributions()
#         # Compatibility attribute for existing callers.
#         self.metric_profiles = tuple(
#             {"metric": metric, "label": label, "direction": direction}
#             for metric, label, direction in (
#                 ("packet_loss_rate", "packet loss / radio-quality degradation", "higher_is_worse"),
#                 ("latency_ms", "latency / congestion issue", "higher_is_worse"),
#                 ("call_drop_rate", "call-drop or handover instability", "higher_is_worse"),
#                 ("handover_success_rate", "handover / mobility failure", "lower_is_worse"),
#                 ("cell_availability", "cell availability / coverage problem", "lower_is_worse"),
#                 ("signal_strength_dbm", "weak-signal / coverage degradation", "lower_is_worse"),
#                 ("fault_occurrence_rate", "fault-occurrence or environmental degradation", "higher_is_worse"),
#                 ("security_incidents", "security-event-driven disruption", "higher_is_worse"),
#                 ("authentication_failures", "authentication or identity failure", "higher_is_worse"),
#             )
#         )

#     @staticmethod
#     def _load_reference_distributions() -> Dict[str, List[float]]:
#         distributions: Dict[str, List[float]] = {}
#         try:
#             with Path(CSV_PATH).open("r", encoding="utf-8-sig", newline="") as handle:
#                 for row in csv.DictReader(handle):
#                     for raw_name, raw_value in row.items():
#                         if raw_value is None:
#                             continue
#                         name = {
#                             "Latency (ms)": "latency_ms", "Packet Loss Rate (%)": "packet_loss_rate",
#                             "Throughput (Mbps)": "throughput_mbps", "Signal Strength (dBm)": "signal_strength_dbm",
#                             "Call Drop Rate (%)": "call_drop_rate", "Handover Success Rate (%)": "handover_success_rate",
#                             "Cell Availability (%)": "cell_availability", "Alarm Count": "alarm_count",
#                             "Critical Alarm Count": "critical_alarm_count", "Fault Occurrence Rate (%)": "fault_occurrence_rate",
#                             "Jitter (ms)": "jitter_ms", "User Count": "user_count", "Data Usage (GB)": "data_usage_gb",
#                             "Parameter Changes": "parameter_changes", "Successful Configuration Changes (%)": "successful_configuration_changes",
#                             "Connection Setup Success Rate (%)": "connection_setup_success_rate", "Security Incidents": "security_incidents",
#                             "Authentication Failures": "authentication_failures", "Temperature (Â°C)": "temperature_c", "Temperature (Ã‚Â°C)": "temperature_c", "Humidity (%)": "humidity_percent",
#                         }.get(raw_name)
#                         if not name:
#                             continue
#                         try:
#                             value = float(raw_value)
#                         except (TypeError, ValueError):
#                             continue
#                         if math.isfinite(value):
#                             distributions.setdefault(name, []).append(value)
#         except (OSError, TypeError):
#             return {}
#         return distributions

#     @staticmethod
#     def _as_float(value: Any) -> Optional[float]:
#         if value is None or value == "":
#             return None
#         try:
#             number = float(value)
#         except (TypeError, ValueError):
#             return None
#         return number if math.isfinite(number) else None

#     @staticmethod
#     def _safe_get_mapping(value: Any) -> Dict[str, Any]:
#         return value if isinstance(value, dict) else {}

#     @staticmethod
#     def _safe_list(value: Any) -> List[Any]:
#         return value if isinstance(value, list) else []

#     @classmethod
#     def _query_signals(cls, query: str) -> set[str]:
#         lowered = (query or "").casefold()
#         patterns = {
#             "latency": r"\b(latency|delay|slow response|response time)\b",
#             "packet_loss": r"\b(packet loss|packet drop|lost packets?)\b",
#             "throughput": r"\b(throughput|bandwidth|low data rate|reduced (?:data|throughput))\b",
#             "load": r"\b(load|capacity|congestion|users?|data usage|traffic)\b",
#             "signal": r"\b(signal|coverage|weak[- ]signal|poor radio|radio quality)\b",
#             "jitter": r"\b(jitter|transmission instability)\b",
#             "call_drop": r"\b(call drop|dropped calls?|voice drop|rising call drops?)\b",
#             "handover": r"\b(handover|handoff|mobility)\b",
#             "availability": r"\b(availability|outage|unavailable|cell down)\b",
#             "alarms": r"\b(alarm|alarms|critical alarm|alert)\b",
#             "fault": r"\b(fault|failure|equipment issue|hardware|hardware degradation)\b",
#             "configuration": r"\b(configuration|config(?:uration)? changes?|parameter changes?|settings change)\b",
#             "connection": r"\b(connection setup|establishment|attach failure|connection failure)\b",
#             "environment": r"\b(environment|temperature|heat|humidity|weather|environmental)\b",
#             "security": r"\b(security|authentication|login failure|auth failure|repeated authentication)\b",
#         }
#         return {signal for signal, pattern in patterns.items() if re.search(pattern, lowered)}

#     @classmethod
#     def _normalize_current_metrics(cls, current_metrics: Optional[Dict[str, Any]], network_prediction: Optional[Dict[str, Any]]) -> Dict[str, Any]:
#         current = dict(current_metrics) if isinstance(current_metrics, dict) else {}
#         if isinstance(network_prediction, dict):
#             prediction = cls._safe_get_mapping(network_prediction.get("prediction"))
#             performance = cls._safe_get_mapping(prediction.get("network_performance"))
#             fault = cls._safe_get_mapping(prediction.get("fault_risk"))
#             if "predicted_throughput_mbps" in performance:
#                 current["throughput_mbps"] = performance["predicted_throughput_mbps"]
#             if "predicted_fault_occurrence_rate_percent" in fault:
#                 current["fault_occurrence_rate"] = fault["predicted_fault_occurrence_rate_percent"]
#         return current

#     @staticmethod
#     def _incident_record(item: Any) -> Dict[str, Any]:
#         if not isinstance(item, dict):
#             return {}
#         record = item.get("incident")
#         return record if isinstance(record, dict) else {}

#     @classmethod
#     def _metric_severity(cls, metric: str, value: float, values: List[float], reference_values: Optional[List[float]] = None) -> float:
#         """Return dataset-relative extremeness, not probability."""
#         comparison = reference_values or values
#         if len(comparison) < 2 or max(comparison) == min(comparison):
#             return 0.5
#         rank = sum(candidate <= value for candidate in comparison) / len(comparison)
#         if cls.METRIC_DIRECTIONS.get(metric) == "lower":
#             rank = 1.0 - rank + (1.0 / len(comparison))
#         return max(0.0, min(1.0, rank))

#     @staticmethod
#     def _retrieval_score(item: Dict[str, Any]) -> float:
#         scores = item.get("scores") if isinstance(item.get("scores"), dict) else item
#         value = scores.get("hybrid", scores.get("hybrid_score", 0.5))
#         try:
#             return max(0.0, min(1.0, float(value)))
#         except (TypeError, ValueError):
#             return 0.5

#     @classmethod
#     def _current_alignment(cls, metric: str, historical_values: List[float], current: Dict[str, Any]) -> Optional[float]:
#         current_value = cls._as_float(current.get(metric))
#         if current_value is None or not historical_values:
#             return None
#         historical_mean = sum(historical_values) / len(historical_values)
#         if historical_mean == 0:
#             return 0.5
#         ratio = current_value / historical_mean
#         if cls.METRIC_DIRECTIONS.get(metric) == "lower":
#             ratio = 1.0 / ratio if ratio else 1.0
#         return max(0.0, min(1.0, ratio))

#     def _build_candidate(self, profile: Dict[str, Any], query_signals: set[str], incidents: List[Dict[str, Any]], current: Dict[str, Any]) -> Optional[Dict[str, Any]]:
#         matched_signals = query_signals & profile["signals"]
#         if not matched_signals:
#             return None
#         metric_values: Dict[str, List[float]] = {metric: [] for metric in profile["metrics"]}
#         for item in incidents:
#             record = self._incident_record(item)
#             for metric in profile["metrics"]:
#                 value = self._as_float(record.get(metric))
#                 if value is not None:
#                     metric_values[metric].append(value)
#         relevant_metrics = list(dict.fromkeys(
#             metric for signal in matched_signals for metric in self.SIGNAL_FIELDS[signal]
#             if metric in profile["metrics"] and metric_values.get(metric)
#         ))
#         if not relevant_metrics:
#             return None
#         expected_metrics = list(dict.fromkeys(
#             metric for signal in matched_signals for metric in self.SIGNAL_FIELDS[signal]
#             if metric in profile["metrics"]
#         ))
#         missing_metrics = [metric for metric in expected_metrics if not metric_values.get(metric)]

#         supporting_incidents: List[Dict[str, Any]] = []
#         contradictory_incidents: List[Dict[str, Any]] = []
#         retrieval_scores: List[float] = []
#         evidence_strengths: List[float] = []
#         current_alignments: List[float] = []
#         for item in incidents:
#             record = self._incident_record(item)
#             observations: Dict[str, Any] = {}
#             severities: List[float] = []
#             for metric in relevant_metrics:
#                 value = self._as_float(record.get(metric))
#                 if value is None:
#                     continue
#                 observations[metric] = value
#                 severities.append(self._metric_severity(metric, value, metric_values[metric], self.reference_distributions.get(metric)))
#                 alignment = self._current_alignment(metric, metric_values[metric], current)
#                 if alignment is not None:
#                     current_alignments.append(alignment)
#             if not observations:
#                 continue
#             retrieval_score = self._retrieval_score(item)
#             evidence_strength = sum(severities) / len(severities)
#             retrieval_scores.append(retrieval_score)
#             evidence_strengths.append(evidence_strength)
#             if evidence_strength >= 0.5:
#                 supporting_incidents.append({
#                     "incident_id": item.get("incident_id") or record.get("incident_id"),
#                     "metrics": observations,
#                     "severity": round(evidence_strength, 4),
#                     "retrieval_score": round(retrieval_score, 4),
#                 })
#             elif evidence_strength < 0.35:
#                 contradictory_incidents.append({
#                     "incident_id": item.get("incident_id") or record.get("incident_id"),
#                     "metrics": observations,
#                     "reason": "Observed values were not unusually severe relative to the dataset reference distribution.",
#                 })
#         if not evidence_strengths:
#             return None

#         query_fit = len(matched_signals) / max(1, len(query_signals))
#         evidence_strength = sum(evidence_strengths) / len(evidence_strengths)
#         retrieval_relevance = sum(retrieval_scores) / len(retrieval_scores)
#         current_alignment = sum(current_alignments) / len(current_alignments) if current_alignments else None
#         score = 0.4 * query_fit + 0.35 * evidence_strength + 0.25 * retrieval_relevance
#         if current_alignment is not None:
#             score = 0.8 * score + 0.2 * current_alignment
#         uncertainty = "low" if len(supporting_incidents) >= 4 and not missing_metrics and not contradictory_incidents else "moderate" if len(supporting_incidents) >= 2 else "high"
#         limitations = [
#             "Score is an evidence-ranking score, not a calibrated probability.",
#             "Historical metric alignment does not confirm the physical root cause.",
#         ]
#         if not current:
#             limitations.append("Current network metrics were unavailable; no current-to-history alignment was performed.")
#         return {
#             "hypothesis": profile["label"],
#             "score": round(max(0.0, min(1.0, score)), 4),
#             "score_label": "evidence-ranking score",
#             "matched_incident_id": supporting_incidents[0].get("incident_id") if supporting_incidents else None,
#             "supporting_incident_ids": [item.get("incident_id") for item in supporting_incidents if item.get("incident_id")],
#             "supporting_signals": [f"{metric} observed in {len(values)} retrieved incident(s)" for metric, values in metric_values.items() if metric in relevant_metrics and values],
#             "metric_values": {
#                 metric: {"count": len(values), "min": min(values), "max": max(values), "mean": round(sum(values) / len(values), 4)}
#                 for metric, values in metric_values.items() if metric in relevant_metrics and values
#             },
#             "contradictory_evidence": contradictory_incidents,
#             "missing_metrics": missing_metrics,
#             "additional_checks_needed": [
#                 f"Collect current {metric} telemetry" for metric in missing_metrics
#             ] + (["Validate the leading pattern against live alarms, configuration history, and service counters"] if not current else []),
#             "evidence": {
#                 "query_signals": sorted(matched_signals),
#                 "supporting_incidents": supporting_incidents,
#                 "current_metrics_used": bool(current),
#                 "limitations": limitations,
#             },
#             "uncertainty": uncertainty,
#         }

#     def _unknown_hypothesis(self, reason: str, query_signals: set[str], evidence_count: int) -> Dict[str, Any]:
#         return {
#             "rank": 1,
#             "hypothesis": self.UNKNOWN_LABEL,
#             "score": 0.0,
#             "score_label": "evidence-ranking score",
#             "supporting_incident_ids": [],
#             "supporting_signals": [],
#             "metric_values": {},
#             "contradictory_evidence": [],
#             "missing_metrics": [],
#             "uncertainty": "high",
#             "evidence": {
#                 "query_signals": sorted(query_signals),
#                 "supporting_incidents": [],
#                 "limitations": [reason],
#                 "evaluated_incident_count": evidence_count,
#             },
#             "additional_checks_needed": [
#                 "Provide current telemetry or a more specific symptom",
#                 "Retrieve incidents containing the relevant metric fields",
#             ],
#         }

#     def process(self, query: str, rca_handoff: Optional[Dict[str, Any]], current_metrics: Optional[Dict[str, Any]] = None, network_prediction: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
#         if not isinstance(rca_handoff, dict):
#             return {"agent": "RCAAgent", "query": query, "status": "error", "reason": "rca_handoff must be a dictionary.", "hypotheses": [], "trace": {"synapt_context_used": False}}
#         retrieved = self._safe_list(rca_handoff.get("retrieved_incidents"))
#         synapt_context = self._safe_get_mapping(rca_handoff.get("synapt_context"))
#         base_trace = {"synapt_context_used": bool(synapt_context.get("answer")), "synapt_call_count": 0, "retrieved_incident_count": len(retrieved)}
#         if not retrieved:
#             return {"agent": "RCAAgent", "query": query, "status": "no_evidence", "reason": "No retrieved incidents were provided in the handoff.", "hypotheses": [], "trace": base_trace}

#         evidence_set = [item for item in retrieved if self._incident_record(item)][: self.max_evidence_incidents]
#         query_signals = self._query_signals(query)
#         base_trace.update({"evidence_set_size": len(evidence_set), "query_signals": sorted(query_signals)})
#         empty_summary = {"retrieved_incident_count": len(retrieved), "evaluated_incident_count": len(evidence_set), "top_hypothesis": None, "top_score": None}
#         if not query_signals:
#             reason = "Insufficient evidence: the query did not identify a supported network symptom or metric."
#             return {"agent": "RCAAgent", "query": query, "status": "insufficient_evidence", "reason": reason, "hypotheses": [self._unknown_hypothesis(reason, query_signals, len(evidence_set))], "summary": empty_summary, "trace": base_trace}

#         current = self._normalize_current_metrics(current_metrics, network_prediction)
#         candidates = [candidate for profile in self.HYPOTHESIS_PROFILES if (candidate := self._build_candidate(profile, query_signals, evidence_set, current)) is not None]
#         candidates.sort(key=lambda item: (-item["score"], -len(item["supporting_incident_ids"]), item["hypothesis"]))
#         hypotheses = candidates[: self.max_hypotheses]
#         if not hypotheses:
#             reason = "Insufficient evidence: retrieved incidents did not contain usable values for the query symptoms."
#             return {"agent": "RCAAgent", "query": query, "status": "insufficient_evidence", "reason": reason, "hypotheses": [self._unknown_hypothesis(reason, query_signals, len(evidence_set))], "summary": empty_summary, "trace": base_trace}
#         for rank, hypothesis in enumerate(hypotheses, start=1):
#             hypothesis["rank"] = rank
#         top = hypotheses[0]
#         return {
#             "agent": "RCAAgent", "query": query, "status": "success",
#             "synapt_context": {"used": bool(synapt_context.get("answer")), "note": "Prior Synapt answer is advisory-only and was not re-called.", "answer": synapt_context.get("answer")},
#             "summary": {"retrieved_incident_count": len(retrieved), "evaluated_incident_count": len(evidence_set), "candidate_hypothesis_count": len(candidates), "top_hypothesis": top["hypothesis"], "top_score": top["score"], "score_label": "evidence-ranking score", "uncertainty": top["uncertainty"]},
#             "hypotheses": hypotheses,
#             "trace": {**base_trace, "current_metrics_used": bool(current), "network_prediction_used": bool(network_prediction)},
#         }

"""Evidence-ranked, deterministic root-cause hypothesis analysis.

Compatibility:
- Preserves RCAAgent.process(query, rca_handoff, current_metrics, network_prediction).
- Preserves the existing handoff keys and main output fields.
- Does not call Synapt, retrieval, or an LLM again.
- Scores rank hypotheses; scores are not calibrated probabilities.
"""

from __future__ import annotations

import bisect
import csv
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.config import CSV_PATH
from config.metric_schema import canonical_field


class RCAAgent:
    """Rank investigative hypotheses using historical incident evidence."""

    SIGNAL_FIELDS = {
        "latency": ("latency_ms",),
        "packet_loss": ("packet_loss_rate",),
        "throughput": ("throughput_mbps",),
        "load": ("user_count", "data_usage_gb"),
        "signal": ("signal_strength_dbm",),
        "jitter": ("jitter_ms",),
        "call_drop": ("call_drop_rate",),
        "handover": ("handover_success_rate",),
        "availability": ("cell_availability",),
        "alarms": ("alarm_count", "critical_alarm_count"),
        "fault": ("fault_occurrence_rate",),
        "configuration": (
            "parameter_changes",
            "successful_configuration_changes",
        ),
        "connection": ("connection_setup_success_rate",),
        "environment": ("temperature_c", "humidity_percent"),
        "security": ("security_incidents", "authentication_failures"),
    }

    # "higher" means a higher value is generally more concerning.
    # "lower" means a lower value is generally more concerning.
    METRIC_DIRECTIONS = {
        "latency_ms": "higher",
        "packet_loss_rate": "higher",
        "throughput_mbps": "lower",
        "signal_strength_dbm": "lower",
        "user_count": "higher",
        "data_usage_gb": "higher",
        "jitter_ms": "higher",
        "call_drop_rate": "higher",
        "handover_success_rate": "lower",
        "cell_availability": "lower",
        "alarm_count": "higher",
        "critical_alarm_count": "higher",
        "fault_occurrence_rate": "higher",
        "security_incidents": "higher",
        "authentication_failures": "higher",
        "parameter_changes": "higher",
        "successful_configuration_changes": "lower",
        "connection_setup_success_rate": "lower",
        "temperature_c": "higher",
        "humidity_percent": "higher",
    }

    # A query can activate several profiles.
    # Profiles describe investigative hypotheses, not confirmed causes.
    HYPOTHESIS_PROFILES = (
        {
            "label": "capacity and network congestion",
            "signals": {"latency", "throughput", "load"},
            "metrics": (
                "latency_ms", "throughput_mbps",
                "user_count", "data_usage_gb",
            ),
        },
        {
            "label": "packet loss and transmission instability",
            "signals": {"packet_loss", "jitter"},
            "metrics": ("packet_loss_rate", "jitter_ms"),
        },
        {
            "label": "radio signal quality degradation",
            "signals": {"packet_loss", "signal", "jitter"},
            "metrics": (
                "packet_loss_rate", "signal_strength_dbm", "jitter_ms",
            ),
        },
        {
            "label": "poor radio coverage",
            "signals": {"signal", "availability"},
            "metrics": ("signal_strength_dbm", "cell_availability"),
        },
        {
            "label": "mobility and handover instability",
            "signals": {"handover", "call_drop", "signal"},
            "metrics": (
                "handover_success_rate", "call_drop_rate",
                "signal_strength_dbm",
            ),
        },
        {
            "label": "equipment or hardware degradation",
            "signals": {"fault", "alarms", "environment"},
            "metrics": (
                "fault_occurrence_rate", "alarm_count",
                "critical_alarm_count", "temperature_c",
            ),
        },
        {
            "label": "configuration or parameter-change issues",
            "signals": {"configuration"},
            "metrics": (
                "parameter_changes",
                "successful_configuration_changes",
            ),
        },
        {
            "label": "alarm-intensive operational faults",
            "signals": {"alarms", "fault"},
            "metrics": (
                "alarm_count", "critical_alarm_count",
                "fault_occurrence_rate",
            ),
        },
        {
            "label": "transport or backhaul degradation",
            "signals": {"latency", "packet_loss", "throughput", "jitter"},
            "metrics": (
                "latency_ms", "packet_loss_rate",
                "throughput_mbps", "jitter_ms",
            ),
        },
        {
            "label": "connection establishment failures",
            "signals": {"connection", "availability"},
            "metrics": (
                "connection_setup_success_rate", "cell_availability",
            ),
        },
        {
            "label": "security or authentication disruption",
            "signals": {"security"},
            "metrics": ("security_incidents", "authentication_failures"),
        },
        {
            "label": "environmental stress",
            "signals": {"environment", "fault"},
            "metrics": (
                "temperature_c", "humidity_percent",
                "fault_occurrence_rate",
            ),
        },
        {
            "label": "availability and service outages",
            "signals": {"availability", "connection"},
            "metrics": (
                "cell_availability", "connection_setup_success_rate",
            ),
        },
        {
            "label": "quality-of-service instability",
            "signals": {
                "latency", "packet_loss", "throughput",
                "jitter", "call_drop",
            },
            "metrics": (
                "latency_ms", "packet_loss_rate", "throughput_mbps",
                "jitter_ms", "call_drop_rate",
            ),
        },
    )

    UNKNOWN_LABEL = "unknown, mixed-cause or insufficient-evidence"

    # CSV header -> normalized metadata field.
    CSV_FIELD_MAP = {
        "latency (ms)": "latency_ms",
        "packet loss rate (%)": "packet_loss_rate",
        "throughput (mbps)": "throughput_mbps",
        "signal strength (dbm)": "signal_strength_dbm",
        "call drop rate (%)": "call_drop_rate",
        "handover success rate (%)": "handover_success_rate",
        "cell availability (%)": "cell_availability",
        "alarm count": "alarm_count",
        "critical alarm count": "critical_alarm_count",
        "fault occurrence rate (%)": "fault_occurrence_rate",
        "jitter (ms)": "jitter_ms",
        "user count": "user_count",
        "data usage (gb)": "data_usage_gb",
        "parameter changes": "parameter_changes",
        "successful configuration changes (%)":
            "successful_configuration_changes",
        "connection setup success rate (%)":
            "connection_setup_success_rate",
        "security incidents": "security_incidents",
        "authentication failures": "authentication_failures",
        "temperature (°c)": "temperature_c",
        "temperature (â°c)": "temperature_c",
        "temperature (ã‚°c)": "temperature_c",
        "humidity (%)": "humidity_percent",
    }

    # Handles common natural-language variants.
    SIGNAL_PATTERNS = {
        "latency": (
            r"\b(latency|delays?|slow response|response time|"
            r"high response time|slow network)\b",
        ),
        "packet_loss": (
            r"\b(packet[\s-]*loss|packet[\s-]*drops?|"
            r"lost packets?|loss of packets?)\b",
        ),
        "throughput": (
            r"\b(throughput|bandwidth|data rate|"
            r"reduced throughput|low throughput)\b",
        ),
        "load": (
            r"\b(load|capacity|congestion|users?|user count|"
            r"data usage|traffic|overload|high demand)\b",
        ),
        "signal": (
            r"\b(signal|coverage|weak[\s-]*signal|poor radio|"
            r"radio quality|low signal strength)\b",
        ),
        "jitter": (
            r"\b(jitter|transmission instability)\b",
        ),
        "call_drop": (
            r"\b(call[\s-]*drops?|dropped calls?|voice drops?|"
            r"call drop rate)\b",
        ),
        "handover": (
            r"\b(handovers?|handoffs?|mobility|handover success)\b",
        ),
        "availability": (
            r"\b(availability|outages?|unavailable|cell down|"
            r"service interruption|service outage)\b",
        ),
        "alarms": (
            r"\b(alarms?|critical alarms?|alarm counts?|alerts?)\b",
        ),
        "fault": (
            r"\b(faults?|failures?|equipment issues?|hardware|"
            r"fault occurrence|component failure)\b",
        ),
        "configuration": (
            r"\b(configurations?|configs?|parameter changes?|"
            r"settings changes?|configuration changes?)\b",
        ),
        "connection": (
            r"\b(connection setup|connection establishment|"
            r"attach failures?|connection failures?|"
            r"setup success rate)\b",
        ),
        "environment": (
            r"\b(environment|temperature|heat|humidity|weather|"
            r"environmental conditions?)\b",
        ),
        "security": (
            r"\b(security|authentication|login failures?|"
            r"auth failures?|security incidents?)\b",
        ),
    }

    def __init__(
        self,
        max_hypotheses: int = 5,
        max_evidence_incidents: int = 100,
    ) -> None:
        self.max_hypotheses = max(1, max_hypotheses)
        self.max_evidence_incidents = max(1, max_evidence_incidents)

        # Sorted dataset-wide distributions make percentile lookups efficient.
        self.reference_distributions = self._load_reference_distributions()

        # Compatibility attribute for callers using the older field.
        self.metric_profiles = tuple(
            {
                "metric": metric,
                "label": label,
                "direction": direction,
            }
            for metric, label, direction in (
                ("packet_loss_rate", "packet loss / radio-quality degradation", "higher_is_worse"),
                ("latency_ms", "latency / congestion issue", "higher_is_worse"),
                ("call_drop_rate", "call-drop or handover instability", "higher_is_worse"),
                ("handover_success_rate", "handover / mobility failure", "lower_is_worse"),
                ("cell_availability", "cell availability / coverage problem", "lower_is_worse"),
                ("signal_strength_dbm", "weak-signal / coverage degradation", "lower_is_worse"),
                ("fault_occurrence_rate", "fault-occurrence or environmental degradation", "higher_is_worse"),
                ("security_incidents", "security-event-driven disruption", "higher_is_worse"),
                ("authentication_failures", "authentication or identity failure", "higher_is_worse"),
            )
        )

    @classmethod
    def _load_reference_distributions(cls) -> Dict[str, List[float]]:
        """Load dataset-wide metric distributions for severity estimation."""
        distributions: Dict[str, List[float]] = {}

        try:
            with Path(CSV_PATH).open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                for row in csv.DictReader(handle):
                    for raw_name, raw_value in row.items():
                        if raw_name is None or raw_value is None:
                            continue

                        normalized_header = raw_name.strip().casefold()
                        metric = canonical_field(raw_name)
                        if metric not in cls.METRIC_DIRECTIONS and metric not in {
                            "cell_availability", "mttr_hours", "throughput_mbps",
                            "latency_ms", "packet_loss_rate", "call_drop_rate",
                            "handover_success_rate", "alarm_count",
                            "critical_alarm_count", "parameter_changes",
                            "successful_configuration_changes", "data_usage_gb",
                            "user_count", "signal_strength_dbm", "jitter_ms",
                            "connection_setup_success_rate", "security_incidents",
                            "authentication_failures", "temperature_c",
                            "humidity_percent", "fault_occurrence_rate",
                        }:
                            metric = cls.CSV_FIELD_MAP.get(normalized_header)

                        # Tolerate common mojibake variants in CSV headers.
                        if metric is None and "temperature" in normalized_header:
                            if "c" in normalized_header:
                                metric = "temperature_c"

                        if metric is None:
                            continue

                        value = cls._as_float(raw_value)
                        if value is not None:
                            distributions.setdefault(metric, []).append(value)

        except (OSError, TypeError, ValueError):
            # The agent can still run using the retrieved incidents.
            return {}

        for values in distributions.values():
            values.sort()

        return distributions

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None

        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return None

        return number if math.isfinite(number) else None

    @staticmethod
    def _safe_get_mapping(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _safe_list(value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    @classmethod
    def _query_signals(cls, query: str) -> set[str]:
        lowered = str(query or "").casefold()
        return {
            signal
            for signal, patterns in cls.SIGNAL_PATTERNS.items()
            if any(re.search(pattern, lowered) for pattern in patterns)
        }

    @classmethod
    def _normalize_current_metrics(
        cls,
        current_metrics: Optional[Dict[str, Any]],
        network_prediction: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        current = dict(current_metrics) if isinstance(current_metrics, dict) else {}

        # Preserve the existing prediction payload contract.
        if isinstance(network_prediction, dict):
            prediction = cls._safe_get_mapping(
                network_prediction.get("prediction")
            )
            performance = cls._safe_get_mapping(
                prediction.get("network_performance")
            )
            fault = cls._safe_get_mapping(prediction.get("fault_risk"))

            if "predicted_throughput_mbps" in performance:
                current["throughput_mbps"] = performance[
                    "predicted_throughput_mbps"
                ]

            if "predicted_fault_occurrence_rate_percent" in fault:
                current["fault_occurrence_rate"] = fault[
                    "predicted_fault_occurrence_rate_percent"
                ]

        return current

    @classmethod
    def _incident_record(cls, item: Any) -> Dict[str, Any]:
        if not isinstance(item, dict):
            return {}

        # Standard Query Agent result.
        record = item.get("incident")
        if isinstance(record, dict):
            return record

        # Also accept a direct record without changing the usual contract.
        if any(key in item for key in cls.SIGNAL_FIELDS.values()):
            return item

        # Some retrieval implementations put fields directly in the result.
        if any(
            isinstance(value, (int, float))
            for key, value in item.items()
            if key.endswith(("_ms", "_rate", "_mbps", "_dbm"))
        ):
            return item

        return {}
#metric_severity() function, the current metric is compared with values loaded from your CSV dataset, 
# provided those values are passed as reference_values.
    @classmethod
    def _metric_severity(
        cls,
        metric: str,
        value: float,
        values: List[float],
        reference_values: Optional[List[float]] = None,
    ) -> float:
        """Estimate abnormality using empirical percentiles, not probability.

        Dataset-wide distributions are preferred. Retrieved evidence is used
        only when a sufficiently large reference distribution is unavailable.
        """
        comparison = (
            reference_values
            if reference_values is not None and len(reference_values) >= 20
            else sorted(values)
        )

        if len(comparison) < 2:
            return 0.5  # Unknown severity, not proof of normality.

        # reference_values are sorted when loaded; fallback values are sorted.
        percentile = bisect.bisect_right(comparison, value) / len(comparison)

        if cls.METRIC_DIRECTIONS.get(metric) == "lower":
            severity = 1.0 - percentile
        else:
            severity = percentile

        return max(0.0, min(1.0, severity))
#hecks how strongly a retrieved incident matches the user's query, based on its hybrid retrieval score.
    @staticmethod
    def _retrieval_score(item: Dict[str, Any]) -> float:
        scores = item.get("scores")
        if not isinstance(scores, dict):
            scores = item

        value = scores.get("hybrid", scores.get("hybrid_score"))

        try:
            score = float(value)
        except (TypeError, ValueError, OverflowError):
            return 0.5

        if not math.isfinite(score):
            return 0.5

        return max(0.0, min(1.0, score))
#How abnormal is the current metric?
    def _current_alignment(
        self,
        metric: str,
        historical_values: List[float],
        current: Dict[str, Any],
    ) -> Optional[float]:
        """Measure whether supplied values are abnormal vs. dataset history."""
        current_value = self._as_float(current.get(metric))
        if current_value is None:
            return None

        reference = self.reference_distributions.get(metric)
        return self._metric_severity(
            metric,
            current_value,
            historical_values,
            reference,
        )

    def _build_candidate(
        self,
        profile: Dict[str, Any],
        query_signals: set[str],
        incidents: List[Dict[str, Any]],
        current: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        matched_signals = query_signals & profile["signals"]
        if not matched_signals:
            return None

        metric_values: Dict[str, List[float]] = {
            metric: [] for metric in profile["metrics"]
        }

        for item in incidents:
            record = self._incident_record(item)
            for metric in profile["metrics"]:
                value = self._as_float(record.get(metric))
                if value is not None:
                    metric_values[metric].append(value)

        relevant_metrics = list(dict.fromkeys(
            metric
            for signal in matched_signals
            for metric in self.SIGNAL_FIELDS[signal]
            if metric in profile["metrics"] and metric_values.get(metric)
        ))

        if not relevant_metrics:
            return None

        expected_metrics = list(dict.fromkeys(
            metric
            for signal in matched_signals
            for metric in self.SIGNAL_FIELDS[signal]
            if metric in profile["metrics"]
        ))
        missing_metrics = [
            metric for metric in expected_metrics
            if not metric_values.get(metric)
        ]

        supporting_incidents: List[Dict[str, Any]] = []
        weak_evidence: List[Dict[str, Any]] = []
        incident_strengths: List[float] = []
        retrieval_scores: List[float] = []
        current_alignments: List[float] = []

        for item in incidents:
            record = self._incident_record(item)
            observations: Dict[str, float] = {}
            severities: List[float] = []

            for metric in relevant_metrics:
                value = self._as_float(record.get(metric))
                if value is None:
                    continue

                observations[metric] = value
                severities.append(
                    self._metric_severity(
                        metric,
                        value,
                        metric_values[metric],
                        self.reference_distributions.get(metric),
                    )
                )

            if not observations or not severities:
                continue

            incident_severity = sum(severities) / len(severities)
            retrieval_score = self._retrieval_score(item)

            incident_strengths.append(incident_severity)
            retrieval_scores.append(retrieval_score)

            incident_id = (
                item.get("incident_id")
                or record.get("incident_id")
                or record.get("Incident_ID")
            )

            evidence_item = {
                "incident_id": incident_id,
                "metrics": observations,
                "severity": round(incident_severity, 4),
                "retrieval_score": round(retrieval_score, 4),
            }

            # These thresholds indicate evidence strength only.
            # They do not mean that the incident confirms the hypothesis.
            if incident_severity >= 0.65:
                supporting_incidents.append(evidence_item)
            elif incident_severity <= 0.30:
                weak_evidence.append({
                    **evidence_item,
                    "reason": (
                        "The observed metrics did not show strong abnormality "
                        "under the available reference distribution."
                    ),
                })

        if not incident_strengths:
            return None

        # Evaluate supplied telemetry independently of historical evidence.
        for metric in relevant_metrics:
            alignment = self._current_alignment(
                metric, metric_values[metric], current
            )
            if alignment is not None:
                current_alignments.append(alignment)

        query_fit = len(matched_signals) / max(1, len(query_signals))
        evidence_strength = sum(incident_strengths) / len(incident_strengths)
        retrieval_relevance = (
            sum(retrieval_scores) / len(retrieval_scores)
            if retrieval_scores else 0.5
        )
        current_alignment = (
            sum(current_alignments) / len(current_alignments)
            if current_alignments else None
        )

        # Weights sum to 1.0 in either scoring path.
        if current_alignment is None:
            score = (
                0.35 * query_fit
                + 0.45 * evidence_strength
                + 0.20 * retrieval_relevance
            )
        else:
            score = (
                0.30 * query_fit
                + 0.40 * evidence_strength
                + 0.20 * retrieval_relevance
                + 0.10 * current_alignment
            )

        # Do not label a hypothesis low-uncertainty merely because several
        # retrieved records exist. Metric coverage and weak evidence matter.
        if (
            len(supporting_incidents) >= 4
            and not missing_metrics
            and not weak_evidence
            and len(relevant_metrics) >= 2
        ):
            uncertainty = "low"
        elif len(supporting_incidents) >= 2 and not missing_metrics:
            uncertainty = "moderate"
        else:
            uncertainty = "high"

        limitations = [
            "The score ranks investigative hypotheses; it is not a probability.",
            "Historical similarity and abnormal metrics do not prove causation.",
            "Percentile severity indicates unusual values, not necessarily a fault.",
        ]

        if not self.reference_distributions:
            limitations.append(
                "Dataset-wide reference distributions were unavailable; "
                "severity may rely on retrieved incidents."
            )
        if not current:
            limitations.append(
                "Current telemetry was not supplied; current network conditions "
                "cannot be confirmed."
            )
        if missing_metrics:
            limitations.append(
                "Some expected metrics were missing from the retrieved evidence."
            )

        metric_summary = {
            metric: {
                "count": len(values),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "mean": round(sum(values) / len(values), 4),
            }
            for metric, values in metric_values.items()
            if metric in relevant_metrics and values
        }

        return {
            "hypothesis": profile["label"],
            "score": round(max(0.0, min(1.0, score)), 4),
            "score_label": "evidence-ranking score",
            "matched_incident_id": (
                supporting_incidents[0].get("incident_id")
                if supporting_incidents else None
            ),
            "supporting_incident_ids": [
                item.get("incident_id")
                for item in supporting_incidents
                if item.get("incident_id")
            ],
            "supporting_signals": [
                f"{metric} observed in {len(metric_values[metric])} "
                "retrieved incident(s)"
                for metric in relevant_metrics
                if metric_values.get(metric)
            ],
            "metric_values": metric_summary,
            "contradictory_evidence": weak_evidence,
            "missing_metrics": missing_metrics,
            "additional_checks_needed": [
                f"Collect current {metric} telemetry"
                for metric in missing_metrics
            ] + (
                [
                    "Validate the leading pattern against live alarms, "
                    "configuration history, and service counters"
                ]
                if not current else []
            ),
            "evidence": {
                "query_signals": sorted(matched_signals),
                "supporting_incidents": supporting_incidents,
                "current_metrics_used": bool(current),
                "limitations": limitations,
            },
            "uncertainty": uncertainty,
        }

    def _unknown_hypothesis(
        self,
        reason: str,
        query_signals: set[str],
        evidence_count: int,
    ) -> Dict[str, Any]:
        return {
            "rank": 1,
            "hypothesis": self.UNKNOWN_LABEL,
            "score": 0.0,
            "score_label": "evidence-ranking score",
            "supporting_incident_ids": [],
            "supporting_signals": [],
            "metric_values": {},
            "contradictory_evidence": [],
            "missing_metrics": [],
            "uncertainty": "high",
            "evidence": {
                "query_signals": sorted(query_signals),
                "supporting_incidents": [],
                "limitations": [reason],
                "evaluated_incident_count": evidence_count,
            },
            "additional_checks_needed": [
                "Provide current telemetry or a more specific symptom",
                "Retrieve incidents containing the relevant metric fields",
            ],
        }

    def process(
        self,
        query: str,
        rca_handoff: Optional[Dict[str, Any]],
        current_metrics: Optional[Dict[str, Any]] = None,
        network_prediction: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process existing handoff data without modifying the agent chain."""
        if not isinstance(rca_handoff, dict):
            return {
                "agent": "RCAAgent",
                "query": query,
                "status": "error",
                "reason": "rca_handoff must be a dictionary.",
                "hypotheses": [],
                "trace": {"synapt_context_used": False},
            }

        retrieved = self._safe_list(
            rca_handoff.get("retrieved_incidents")
        )
        synapt_context = self._safe_get_mapping(
            rca_handoff.get("synapt_context")
        )

        base_trace = {
            "synapt_context_used": bool(synapt_context.get("answer")),
            "synapt_call_count": 0,
            "retrieved_incident_count": len(retrieved),
        }

        if not retrieved:
            return {
                "agent": "RCAAgent",
                "query": query,
                "status": "no_evidence",
                "reason": (
                    "No retrieved incidents were provided in the handoff."
                ),
                "hypotheses": [],
                "trace": base_trace,
            }

        evidence_set = [
            item for item in retrieved
            if self._incident_record(item)
        ][:self.max_evidence_incidents]

        query_signals = self._query_signals(query)
        base_trace.update({
            "evidence_set_size": len(evidence_set),
            "query_signals": sorted(query_signals),
        })

        empty_summary = {
            "retrieved_incident_count": len(retrieved),
            "evaluated_incident_count": len(evidence_set),
            "candidate_hypothesis_count": 0,
            "top_hypothesis": None,
            "top_score": None,
        }

        if not query_signals:
            reason = (
                "Insufficient evidence: the query did not identify a "
                "supported network symptom or metric."
            )
            return {
                "agent": "RCAAgent",
                "query": query,
                "status": "insufficient_evidence",
                "reason": reason,
                "hypotheses": [
                    self._unknown_hypothesis(
                        reason, query_signals, len(evidence_set)
                    )
                ],
                "summary": empty_summary,
                "trace": base_trace,
            }

        current = self._normalize_current_metrics(
            current_metrics, network_prediction
        )

        candidates = []
        for profile in self.HYPOTHESIS_PROFILES:
            candidate = self._build_candidate(
                profile, query_signals, evidence_set, current
            )
            if candidate is not None:
                candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                -item["score"],
                -len(item["supporting_incident_ids"]),
                item["hypothesis"],
            )
        )

        hypotheses = candidates[:self.max_hypotheses]

        if not hypotheses:
            reason = (
                "Insufficient evidence: retrieved incidents did not contain "
                "usable values for the query symptoms."
            )
            return {
                "agent": "RCAAgent",
                "query": query,
                "status": "insufficient_evidence",
                "reason": reason,
                "hypotheses": [
                    self._unknown_hypothesis(
                        reason, query_signals, len(evidence_set)
                    )
                ],
                "summary": empty_summary,
                "trace": base_trace,
            }

        # If every candidate has weak abnormality evidence, do not present
        # the highest arbitrary score as a useful diagnosis.
        if all(
            item["uncertainty"] == "high"
            and not item["supporting_incident_ids"]
            for item in hypotheses
        ):
            reason = (
                "Insufficient evidence: no hypothesis has strong supporting "
                "metric evidence in the retrieved incidents."
            )
            return {
                "agent": "RCAAgent",
                "query": query,
                "status": "insufficient_evidence",
                "reason": reason,
                "hypotheses": [
                    self._unknown_hypothesis(
                        reason, query_signals, len(evidence_set)
                    )
                ],
                "summary": {
                    **empty_summary,
                    "candidate_hypothesis_count": len(candidates),
                },
                "trace": base_trace,
            }

        for rank, hypothesis in enumerate(hypotheses, start=1):
            hypothesis["rank"] = rank

        top = hypotheses[0]

        return {
            "agent": "RCAAgent",
            "query": query,
            "status": "success",
            "synapt_context": {
                "used": bool(synapt_context.get("answer")),
                "note": (
                    "Prior Synapt answer is advisory-only and was not "
                    "re-called."
                ),
                "answer": synapt_context.get("answer"),
            },
            "summary": {
                "retrieved_incident_count": len(retrieved),
                "evaluated_incident_count": len(evidence_set),
                "candidate_hypothesis_count": len(candidates),
                "top_hypothesis": top["hypothesis"],
                "top_score": top["score"],
                "score_label": "evidence-ranking score",
                "uncertainty": top["uncertainty"],
            },
            "hypotheses": hypotheses,
            "trace": {
                **base_trace,
                "current_metrics_used": bool(current),
                "network_prediction_used": bool(network_prediction),
            },
        }
