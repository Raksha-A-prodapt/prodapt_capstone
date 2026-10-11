"""Aggregate metadata-filtered historical network metrics on request."""

from __future__ import annotations

import re
from math import isfinite
from typing import Any

from classification import classify_network_performance


KPI_FIELDS = {
    "throughput_mbps": "Throughput (Mbps)",
    "latency_ms": "Latency (ms)",
    "packet_loss_rate": "Packet Loss Rate (%)",
    "call_drop_rate": "Call Drop Rate (%)",
    "handover_success_rate": "Handover Success Rate (%)",
    "jitter_ms": "Jitter (ms)",
    "connection_setup_success_rate": "Connection Setup Success Rate (%)",
}


class HistoricalEvaluationAgent:
    """Calculate descriptive results for the filtered incident population.

    This is deliberately separate from the current-telemetry Prediction Agent.
    It is used only when a user asks for an evaluation/average without
    supplying current telemetry.
    """

    REQUEST_TERMS = re.compile(
        r"\b(average|avg|mean|evaluate|evaluation|assess|assessment|trend|"
        r"performance|fault\s+risk|fault\s+rate|impact)\b",
        re.IGNORECASE,
    )

    @classmethod
    def requested_for(cls, query: str) -> bool:
        return bool(cls.REQUEST_TERMS.search(query or ""))

    @staticmethod
    def _numeric_average(records: list[dict[str, Any]], field: str) -> float | None:
        values: list[float] = []
        for record in records:
            try:
                value = float(record.get(field))
            except (TypeError, ValueError):
                continue
            if isfinite(value):
                values.append(value)
        return round(sum(values) / len(values), 4) if values else None

    def evaluate(
        self,
        query: str,
        records: list[dict[str, Any]],
        query_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.requested_for(query):
            return {
                "status": "not_requested",
                "analysis_basis": "not_requested",
                "record_count": 0,
                "aggregate_metrics": {},
                "classification": None,
            }
        if not records:
            return {
                "status": "no_evidence",
                "analysis_basis": "metadata_filtered_historical_records",
                "record_count": 0,
                "aggregate_metrics": {},
                "classification": None,
                "query_plan": query_plan or {},
            }

        averages = {
            field: average
            for field in (*KPI_FIELDS.keys(), "fault_occurrence_rate")
            if (average := self._numeric_average(records, field)) is not None
        }
        performance_inputs = {
            KPI_FIELDS[field]: averages[field]
            for field in KPI_FIELDS
            if field in averages
        }
        classification = (
            classify_network_performance(performance_inputs)
            if performance_inputs
            else None
        )
        return {
            "status": "available",
            "analysis_basis": "metadata_filtered_historical_records",
            "record_count": len(records),
            "aggregate_metrics": averages,
            "classification": classification,
            "query_plan": query_plan or {},
            "limitations": [
                "These are descriptive historical averages, not current-network predictions.",
                "Averages can hide severe incident outliers; review retrieved evidence and distributions.",
            ],
        }
