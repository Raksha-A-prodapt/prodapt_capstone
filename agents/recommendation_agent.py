"""Query-gated retrieval of telecom procedures from the Synapt layer."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from synapt_layer.synapt_mcp_client import (
    DEFAULT_URL,
    get_synapt_procedures,
)

logger = logging.getLogger(__name__)
SYNAPT_TIMEOUT_SECONDS = float(os.getenv("SYNAPT_TIMEOUT_SECONDS", "15"))
ProcedureRetriever = Callable[[str, str], Awaitable[Any]]


class RecommendationAgent:
    """Retrieve applicable procedures only when the user asks for actions."""

    RECOMMENDATION_TERMS = (
        "recommend",
        "recommendation",
        "suggest",
        "suggestion",
        "what should i do",
        "what can i do",
        "how do i fix",
        "how to fix",
        "how can i fix",
        "how to address",
        "fix this",
        "resolve",
        "remediate",
        "corrective action",
        "actions",
        "next steps",
        "steps to",
        "action plan",
        "sop",
        "procedure",
        "troubleshoot",
    )

    def __init__(
        self,
        synapt_url: str = DEFAULT_URL,
        procedure_retriever: ProcedureRetriever | None = None,
    ) -> None:
        self.synapt_url = synapt_url
        self.procedure_retriever = procedure_retriever or get_synapt_procedures

    @classmethod
    def requested_for(cls, query: str) -> bool:
        lowered = query.casefold()
        return any(term in lowered for term in cls.RECOMMENDATION_TERMS)

    @staticmethod
    def _procedure_records(value: Any) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        collection_keys = {"procedures", "sops", "results", "items"}

        def visit(item: Any, is_record: bool = False) -> None:
            if isinstance(item, list):
                for child in item:
                    visit(child, is_record=True)
                return
            if not isinstance(item, dict):
                return

            if is_record or any(
                key in item
                for key in (
                    "sop_id",
                    "procedure_id",
                    "recommended_actions",
                    "procedure_steps",
                )
            ):
                records.append(item)
                return

            for key, child in item.items():
                visit(child, key.casefold() in collection_keys)

        visit(value)
        return records

    @staticmethod
    def _recommendations(procedures: list[dict[str, Any]]) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        for procedure in procedures:
            actions = next(
                (
                    procedure[key]
                    for key in (
                        "recommended_actions",
                        "actions",
                        "procedure_steps",
                        "steps",
                    )
                    if key in procedure
                ),
                [],
            )
            if isinstance(actions, str):
                actions = [actions]
            elif isinstance(actions, dict):
                actions = [actions]
            if not isinstance(actions, list):
                continue
            for action in actions:
                if isinstance(action, dict):
                    action = (
                        action.get("action")
                        or action.get("step")
                        or action.get("description")
                        or action.get("instruction")
                    )
                if not isinstance(action, str) or not action.strip():
                    continue
                recommendations.append(
                    {
                        "action": action.strip(),
                        "procedure_id": procedure.get(
                            "sop_id", procedure.get("procedure_id")
                        ),
                        "procedure_name": procedure.get(
                            "name", procedure.get("title")
                        ),
                        "scenario": procedure.get("scenario"),
                        "source": "Synapt procedure retrieval",
                    }
                )
        return recommendations

    async def process(
        self,
        query: str,
        root_cause_analysis: dict[str, Any] | None = None,
        network_metrics: dict[str, Any] | None = None,
        prediction: dict[str, Any] | None = None,
        retrieval_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.requested_for(query):
            return {
                "status": "not_requested",
                "requested": False,
                "procedure_retrieval_called": False,
                "procedures": [],
                "recommendations": [],
                "retrieval_context": retrieval_context or {},
            }

        rca_summary = (root_cause_analysis or {}).get("summary", {})
        top_hypothesis = (
            rca_summary.get("top_hypothesis")
            if isinstance(rca_summary, dict)
            else None
        )
        retrieval_query = (
            "Find operational procedures relevant to this user request. "
            f"Request: {query}\n"
            f"Retrieval plan and domain context: {retrieval_context or {}}\n"
            f"Supported RCA hypothesis, if any: {top_hypothesis or 'not established'}\n"
            f"Available network metrics: {network_metrics or {}}\n"
            f"Prediction evidence: {prediction or {}}\n"
            "Return only procedures relevant to the stated condition. "
            "Do not infer a root cause that is not supported by evidence."
        )

        try:
            raw_result = await asyncio.wait_for(
                self.procedure_retriever(
                    retrieval_query,
                    self.synapt_url,
                ),
                timeout=SYNAPT_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("Synapt procedure retrieval failed: %s", exc)
            return {
                "status": "unavailable",
                "requested": True,
                "procedure_retrieval_called": True,
                "error": str(exc),
                "procedures": [],
                "recommendations": [],
                "retrieval_context": retrieval_context or {},
            }

        procedures = self._procedure_records(raw_result)
        return {
            "status": "success" if procedures else "no_procedures",
            "requested": True,
            "procedure_retrieval_called": True,
            "procedures": procedures,
            "recommendations": self._recommendations(procedures),
            "raw_result": raw_result,
            "retrieval_context": retrieval_context or {},
        }
