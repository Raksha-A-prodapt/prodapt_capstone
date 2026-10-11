"""Run DeepEval retrieval, RCA, and final-answer metrics on local queries.

This benchmark uses the project's local Chroma/CSV retrieval and deterministic
query planner. It does not call Synapt; the current MCP service is unavailable.
Gemini Flash-Lite through AICredits is used only as the evaluation judge.

Run from the repository root:
    python -m evaluations.deepeval_agent_suite
"""

from __future__ import annotations

import asyncio
import argparse
import io
import json
import logging
import os
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig, CacheConfig, DisplayConfig
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BaseMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    GEval,
    HallucinationMetric,
)
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, SingleTurnParams

from agents.orchestrator import TelecomAnalysisOrchestrator
from agents.query_synapt_agent import QuerySynaptAgent
from evaluations.aicredits_judge import AICreditsGeminiJudge

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (
    PROJECT_ROOT
    / "evaluations"
    / "reports"
    / "deepeval_10_query_report.json"
)
logger = logging.getLogger(__name__)


async def _local_synapt_context(question: str, url: str) -> dict[str, str]:
    """Avoid external Synapt calls for this explicitly offline benchmark."""
    return {
        "answer": (
            "Offline benchmark: use the explicit telecom metric and threshold "
            "in the query. This response is not Synapt evidence."
        )
    }


QUERY_CASES = [
    {
        "name": "latency_above_130",
        "query": "Find historical incidents with latency above 130 ms.",
        "field": "latency_ms",
        "operator": ">",
        "value": 130.0,
        "cause_expectation": "latency symptom",
    },
    {
        "name": "packet_loss_above_12",
        "query": "Find historical incidents with packet loss above 12%.",
        "field": "packet_loss_rate",
        "operator": ">",
        "value": 12.0,
        "cause_expectation": "packet loss symptom",
    },
    {
        "name": "winter_high_latency",
        "query": "Find winter incidents with latency at least 130 ms.",
        "field": "latency_ms",
        "operator": ">=",
        "value": 130.0,
        "metadata": {"season": "winter"},
        "cause_expectation": "latency symptom",
    },
    {
        "name": "call_drop_above_3",
        "query": "Find historical cases where call drop rate is greater than 3%.",
        "field": "call_drop_rate",
        "operator": ">",
        "value": 3.0,
        "cause_expectation": "call drop symptom",
    },
    {
        "name": "handover_below_91",
        "query": "Find historical incidents with handover success below 91%.",
        "field": "handover_success_rate",
        "operator": "<",
        "value": 91.0,
        "cause_expectation": "handover symptom",
    },
    {
        "name": "availability_below_80",
        "query": "Find historical incidents with cell availability below 80%.",
        "field": "cell_availability",
        "operator": "<",
        "value": 80.0,
        "cause_expectation": "availability symptom",
    },
    {
        "name": "weak_signal_below_minus_114",
        "query": "Find historical incidents with signal strength below -114 dBm.",
        "field": "signal_strength_dbm",
        "operator": "<",
        "value": -114.0,
        "cause_expectation": "weak signal symptom",
    },
    {
        "name": "jitter_above_45",
        "query": "Find historical incidents with jitter above 45 ms.",
        "field": "jitter_ms",
        "operator": ">",
        "value": 45.0,
        "cause_expectation": "jitter symptom",
    },
    {
        "name": "alarm_count_at_least_14",
        "query": "Find historical incidents with alarm count at least 14.",
        "field": "alarm_count",
        "operator": ">=",
        "value": 14.0,
        "cause_expectation": "alarm symptom",
    },
    {
        "name": "fault_rate_above_60",
        "query": "Find historical incidents with fault occurrence rate above 60%.",
        "field": "fault_occurrence_rate",
        "operator": ">",
        "value": 60.0,
        "cause_expectation": "fault-rate symptom",
    },
]

def _is_match(actual: float, operator: str, target: float) -> bool:
    if operator == ">":
        return actual > target
    if operator == ">=":
        return actual >= target
    if operator == "<":
        return actual < target
    if operator == "<=":
        return actual <= target
    if operator == "=":
        return actual == target
    return False


def _record_description(
    record: dict[str, Any],
    fields: list[str] | None = None,
) -> str:
    selected_fields = fields or list(record)
    return "; ".join(
        f"{key}={value}"
        for key in selected_fields
        if (value := record.get(key)) is not None
    )


class RetrievalFilterMetric(BaseMetric):
    """Deterministically verify retrieved rows satisfy the requested filters."""

    def __init__(self) -> None:
        super().__init__()
        self.threshold = 1.0
        self.async_mode = False
        self.verbose_mode = False

    @property
    def __name__(self) -> str:
        return "Retrieval Filter Compliance"

    def measure(self, test_case: LLMTestCase) -> float:
        failures = []
        metadata = test_case.metadata or {}
        payload = json.loads(test_case.actual_output or "{}")
        expected = metadata["filter"]
        records = payload.get("records", [])

        if not records:
            failures.append("no incidents were retrieved")
        for record in records:
            value = record.get(expected["field"])
            if value is None or not _is_match(
                float(value),
                expected["operator"],
                float(expected["value"]),
            ):
                failures.append(
                    f"incident {record.get('incident_id')} violates "
                    f"{expected['field']} filter"
                )
            for field, target in expected.get("metadata", {}).items():
                if str(record.get(field, "")).casefold() != str(target).casefold():
                    failures.append(
                        f"incident {record.get('incident_id')} violates {field} filter"
                    )

        self.score = 1.0 if not failures else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            "; ".join(failures)
            if failures
            else "All returned rows satisfy the requested filters."
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)


class RCAEvidenceMetric(BaseMetric):
    """Check RCA hypotheses are ranked, linked to matches, and appropriately cautious."""

    def __init__(self) -> None:
        super().__init__()
        self.threshold = 1.0
        self.async_mode = False
        self.verbose_mode = False

    @property
    def __name__(self) -> str:
        return "RCA Evidence and Caution"

    def measure(self, test_case: LLMTestCase) -> float:
        failures = []
        data = json.loads(test_case.actual_output or "{}")
        metadata = test_case.metadata or {}
        hypotheses = data.get("hypotheses", [])
        retrieved_ids = set(metadata.get("retrieved_ids", []))

        if data.get("status") != "success" or not hypotheses:
            failures.append("RCA did not return a ranked hypothesis")
        for hypothesis in hypotheses:
            if not isinstance(hypothesis.get("score"), (float, int)):
                failures.append("hypothesis score is missing or invalid")
            matched_id = hypothesis.get("matched_incident_id")
            if not matched_id or matched_id not in retrieved_ids:
                failures.append("hypothesis is not linked to a retrieved incident")
            if not hypothesis.get("supporting_signals"):
                failures.append("hypothesis has no supporting signals")
        rca_summary = data.get("frontend_summary", "")
        if "not a confirmed cause" not in rca_summary.casefold():
            failures.append("RCA output does not state the cause is unconfirmed")

        self.score = 1.0 if not failures else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            "; ".join(failures)
            if failures
            else "Hypotheses are evidence-linked and the expected response is cautious."
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)


def _load_judge() -> DeepEvalBaseLLM:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("ai_credits_api_key") or os.getenv(
        "AI_CREDITS_API_KEY"
    )
    if not api_key:
        raise RuntimeError(
            "Configure ai_credits_api_key in the project .env before running "
            "LLM-judge metrics."
        )
    return AICreditsGeminiJudge(
        api_key=api_key,
        base_url=os.getenv(
            "DEEPEVAL_BASE_URL",
            "https://api.aicredits.in/v1",
        ),
        model=os.getenv(
            "DEEPEVAL_MODEL",
            "google/gemini-3.1-flash-lite",
        ),
    )


def _evaluate_group(
    name: str,
    test_cases: list[LLMTestCase],
    metrics: list[BaseMetric],
) -> list[dict[str, Any]]:
    test_run_module = import_module("deepeval.test_run.test_run")
    console = test_run_module.console
    rows = []
    for test_case in test_cases:
        for metric in metrics:
            previous_file = console.file
            console.file = io.StringIO()
            try:
                result = evaluate(
                    test_cases=[test_case],
                    metrics=[metric],
                    cache_config=CacheConfig(
                        write_cache=False,
                        use_cache=False,
                    ),
                    async_config=AsyncConfig(run_async=False),
                    display_config=DisplayConfig(
                        show_indicator=False,
                        print_results=False,
                        verbose_mode=False,
                        inspect_after_run=False,
                    ),
                )
                measured = [
                    evaluated_metric
                    for test_result in result.test_results
                    for evaluated_metric in test_result.metrics_data
                ]
                if not measured:
                    raise RuntimeError("DeepEval returned no metric result.")
                evaluated_metric = measured[0]
                rows.append(
                    {
                        "category": name,
                        "query_case": test_case.name,
                        "metric": metric.__name__,
                        "score": evaluated_metric.score,
                        "success": bool(evaluated_metric.success),
                        "reason": evaluated_metric.reason,
                        "status": "completed",
                    }
                )
            except Exception as exc:
                logger.exception(
                    "DeepEval metric failed: group=%s query=%s metric=%s",
                    name,
                    test_case.name,
                    metric.__name__,
                )
                rows.append(
                    {
                        "category": name,
                        "query_case": test_case.name,
                        "metric": metric.__name__,
                        "score": None,
                        "success": False,
                        "reason": None,
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            finally:
                console.file = previous_file
    return rows


async def _run_agent_cases(
    query_cases: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query_agent = QuerySynaptAgent(synapt_caller=_local_synapt_context)
    query_agent.llm_client = None
    orchestrator = TelecomAnalysisOrchestrator(query_agent=query_agent)

    cases = []
    for definition in query_cases or QUERY_CASES:
        response = await orchestrator.run(
            query=definition["query"],
            network_metrics=None,
            top_k=5,
        )
        sections = {
            section["id"]: section
            for section in response["sections"]
        }
        records = [
            item["incident"]
            for item in sections["historical_data"]["data"]["incidents"]
            if isinstance(item, dict) and isinstance(item.get("incident"), dict)
        ]
        retrieval_text = [
            item.get("document") or _record_description(item.get("incident", {}))
            for item in sections["historical_data"]["data"]["incidents"]
            if isinstance(item, dict)
        ]
        rca_data = sections["root_cause_analysis"]["data"]
        filter_description = (
            f"{definition['field']} {definition['operator']} "
            f"{definition['value']}"
            + (
                " and "
                + ", ".join(
                    f"{field}={value}"
                    for field, value in definition.get("metadata", {}).items()
                )
                if definition.get("metadata")
                else ""
            )
        )
        expected_output = (
            f"State how many historical incidents match {filter_description}. "
            f"Show a limited set of matching incident IDs and their "
            f"{definition['field']} values as examples, without claiming they "
            "are the only matching incidents."
        )
        expected_rca = (
            "Provide a ranked, cautious symptom hypothesis from the retrieved "
            "incident evidence. State that the leading cause is not confirmed; identify "
            f"the relevant symptom as {definition['cause_expectation']}."
        )
        rca_output = dict(rca_data)
        rca_output["frontend_summary"] = sections[
            "root_cause_analysis"
        ]["summary"]
        cases.append(
            {
                "definition": definition,
                "response": response,
                "records": records,
                "retrieval_text": retrieval_text,
                "relevant_retrieval_text": [
                    _record_description(
                        record,
                        [
                            "incident_id",
                            definition["field"],
                            *definition.get("metadata", {}).keys(),
                            "issue_reported",
                        ],
                    )
                    for record in records
                ],
                "expected_output": expected_output,
                "expected_rca": expected_rca,
                "rca_data": rca_output,
            }
        )

    retrieval_cases = []
    rca_cases = []
    final_cases = []
    for case in cases:
        definition = case["definition"]
        response = case["response"]
        records = case["records"]
        ids = [record.get("incident_id") for record in records]
        retrieval_cases.append(
            LLMTestCase(
                name=definition["name"],
                input=definition["query"],
                actual_output=json.dumps(
                    {"records": records},
                    ensure_ascii=False,
                    default=str,
                ),
                expected_output=case["expected_output"],
                retrieval_context=case["relevant_retrieval_text"],
                metadata={
                    "filter": {
                        "field": definition["field"],
                        "operator": definition["operator"],
                        "value": definition["value"],
                        "metadata": definition.get("metadata", {}),
                    },
                },
            )
        )
        rca_cases.append(
            LLMTestCase(
                name=definition["name"],
                input=definition["query"],
                actual_output=json.dumps(
                    case["rca_data"],
                    ensure_ascii=False,
                    default=str,
                ),
                expected_output=case["expected_rca"],
                retrieval_context=case["retrieval_text"],
                metadata={"retrieved_ids": ids},
            )
        )
        final_cases.append(
            LLMTestCase(
                name=definition["name"],
                input=definition["query"],
                actual_output=response["final_answer"],
                expected_output=case["expected_output"],
                retrieval_context=case["relevant_retrieval_text"],
                context=case["relevant_retrieval_text"],
            )
        )

    return cases, {
        "retrieval": retrieval_cases,
        "rca": rca_cases,
        "final_answer": final_cases,
    }


async def main(
    dry_run: bool = False,
    start_index: int = 1,
    limit: int = 10,
) -> int:
    if len(QUERY_CASES) < 10:
        raise RuntimeError("The DeepEval suite must contain at least 10 queries.")
    if start_index < 1:
        raise ValueError("--start-index must be at least 1.")
    if limit < 1:
        raise ValueError("--limit must be at least 1.")
    if start_index > len(QUERY_CASES):
        raise ValueError(
            f"--start-index must be between 1 and {len(QUERY_CASES)}."
        )

    selected_cases = QUERY_CASES[start_index - 1 : start_index - 1 + limit]
    if not selected_cases:
        raise ValueError("The requested query range contains no cases.")
    cases, test_cases = await _run_agent_cases(selected_cases)

    local_checks = []
    retrieval_filter_metric = RetrievalFilterMetric()
    rca_evidence_metric = RCAEvidenceMetric()
    for retrieval_case, rca_case in zip(
        test_cases["retrieval"],
        test_cases["rca"],
    ):
        local_checks.append(
            {
                "query_case": retrieval_case.name,
                "metric": retrieval_filter_metric.__name__,
                "score": retrieval_filter_metric.measure(retrieval_case),
                "success": bool(retrieval_filter_metric.success),
                "reason": retrieval_filter_metric.reason,
            }
        )
        local_checks.append(
            {
                "query_case": rca_case.name,
                "metric": rca_evidence_metric.__name__,
                "score": rca_evidence_metric.measure(rca_case),
                "success": bool(rca_evidence_metric.success),
                "reason": rca_evidence_metric.reason,
            }
        )
    failed_local_checks = [item for item in local_checks if not item["success"]]
    print(
        f"Prepared {len(cases)} real local retrieval/RCA cases; "
        f"local filter/RCA checks: "
        f"{len(local_checks) - len(failed_local_checks)}/{len(local_checks)} passed."
    )
    for failure in failed_local_checks:
        print(
            f"FAILED {failure['query_case']} | {failure['metric']}: "
            f"{failure['reason']}"
        )
    if dry_run:
        return 1 if failed_local_checks else 0

    report_path = REPORT_PATH
    if start_index != 1 or len(selected_cases) != len(QUERY_CASES):
        last_index = start_index + len(selected_cases) - 1
        report_path = (
            REPORT_PATH.parent
            / f"deepeval_queries_{start_index:02d}-{last_index:02d}_report.json"
        )

    judge = _load_judge()
    retrieval_metrics = [
        ContextualPrecisionMetric(model=judge, async_mode=False),
        ContextualRecallMetric(model=judge, async_mode=False),
        ContextualRelevancyMetric(model=judge, async_mode=False),
        RetrievalFilterMetric(),
    ]
    rca_metrics = [
        GEval(
            name="RCA Quality",
            criteria=(
                "Assess whether the RCA response ranks a plausible telecom "
                "symptom hypothesis, supports it with retrieved incident "
                "evidence, distinguishes evidence from inference, and avoids "
                "claiming a confirmed root cause."
            ),
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
                SingleTurnParams.RETRIEVAL_CONTEXT,
            ],
            model=judge,
            threshold=0.6,
            async_mode=False,
        ),
        FaithfulnessMetric(model=judge, async_mode=False),
        RCAEvidenceMetric(),
    ]
    final_metrics = [
        AnswerRelevancyMetric(model=judge, async_mode=False),
        FaithfulnessMetric(model=judge, async_mode=False),
        HallucinationMetric(model=judge, async_mode=False),
    ]

    metric_rows = []
    metric_rows.extend(
        _evaluate_group("retrieval", test_cases["retrieval"], retrieval_metrics)
    )
    metric_rows.extend(_evaluate_group("rca", test_cases["rca"], rca_metrics))
    metric_rows.extend(
        _evaluate_group(
            "final_answer",
            test_cases["final_answer"],
            final_metrics,
        )
    )

    scores_by_group: dict[str, dict[str, Any]] = {}
    for row in metric_rows:
        group = scores_by_group.setdefault(
            row["category"],
            {"metrics": {}, "passed": 0, "count": 0},
        )
        metric_summary = group["metrics"].setdefault(
            row["metric"],
            {"scores": [], "passed": 0, "count": 0},
        )
        if isinstance(row["score"], (int, float)):
            metric_summary["scores"].append(float(row["score"]))
        metric_summary["passed"] += int(row["success"])
        metric_summary["count"] += 1
        group["passed"] += int(row["success"])
        group["count"] += 1

    for group in scores_by_group.values():
        for metric in group["metrics"].values():
            scores = metric.pop("scores")
            metric["average_score"] = (
                sum(scores) / len(scores) if scores else None
            )
        group["pass_rate"] = (
            group["passed"] / group["count"] if group["count"] else 0.0
        )

    retrieval_group = scores_by_group.get("retrieval")
    if retrieval_group:
        quality_metrics = [
            metric.get("average_score")
            for name, metric in retrieval_group["metrics"].items()
            if name != "Retrieval Filter Compliance"
            and isinstance(metric.get("average_score"), (int, float))
        ]
        retrieval_group["quality_score"] = (
            sum(quality_metrics) / len(quality_metrics)
            if quality_metrics else None
        )
        retrieval_group["quality_definition"] = (
            "Mean of DeepEval Contextual Precision, Contextual Recall, and "
            "Contextual Relevancy; filter compliance is reported separately."
        )

    passed_count = sum(row["success"] for row in metric_rows)
    total_count = len(metric_rows)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "completed_with_errors"
            if any(row["status"] == "error" for row in metric_rows)
            else "completed"
        ),
        "dataset": "local historical telecom incidents",
        "query_count": len(cases),
        "query_range": {
            "start_index": start_index,
            "end_index": start_index + len(cases) - 1,
        },
        "report_path": str(report_path),
        "live_synapt_used": False,
        "synapt_note": (
            "QuerySynaptAgent was run against local CSV/Chroma retrieval with "
            "an offline advisory stub because the local Synapt MCP endpoint "
            "was not available."
        ),
        "query_planner_llm_used": False,
        "prediction_models_used": False,
        "prediction_note": (
            "No live/current feature payload was provided; predictions were "
            "marked not_applicable."
        ),
        "judge": {
            "provider": "AICredits OpenAI-compatible API",
            "model": judge.get_model_name(),
            "api_key_printed": False,
        },
        "llm_as_judge_used": True,
        "scores": {
            "passed": int(passed_count),
            "total": total_count,
            "pass_rate": passed_count / total_count if total_count else 0.0,
        },
        "groups": scores_by_group,
        "per_query_metrics": metric_rows,
        "queries": [
            {
                "name": case["definition"]["name"],
                "query": case["definition"]["query"],
                "retrieved_count": len(case["records"]),
                "retrieved_incident_ids": [
                    record.get("incident_id") for record in case["records"]
                ],
                "rca_status": case["rca_data"].get("status"),
                "final_answer": case["response"]["final_answer"],
            }
            for case in cases
        ],
        "flow_chart": [
            f"{len(cases)} user-query scenario(s), cases "
            f"{start_index}-{start_index + len(cases) - 1}",
            "Local QuerySynaptAgent: guardrail -> deterministic query parsing -> CSV/Chroma retrieval",
            "RCAAgent: rank hypotheses against retrieved incident records",
            "Frontend final answer: prediction section marked not_applicable; RCA and historical sections populated",
            "DeepEval Retrieval: Contextual Precision + Contextual Recall + Contextual Relevancy + filter-compliance check",
            "DeepEval RCA: GEval RCA Quality + Faithfulness (groundedness) + RCA evidence/caution check",
            "DeepEval Final Answer: Answer Relevancy + Faithfulness + Hallucination",
            "Persist aggregate and per-query metric scores",
        ],
        "metric_definitions": {
            "Contextual Precision": "Whether the retrieved contexts most relevant to the expected result rank highly.",
            "Contextual Recall": "Whether retrieved contexts contain the information needed to satisfy the expected result.",
            "Contextual Relevancy": "Whether retrieved context is relevant to the user query.",
            "Retrieval Filter Compliance": "Deterministically checks each returned incident satisfies requested numeric and metadata filters.",
            "RCA Quality (GEval)": "LLM-judged quality, evidence use, uncertainty, and relevance of the RCA hypothesis.",
            "Faithfulness (RCA)": "Whether RCA claims are supported by the retrieved incident context.",
            "RCA Evidence and Caution": "Deterministically checks ranked RCA output links to retrieved incidents and contains support.",
            "Answer Relevancy": "Whether the final answer addresses the user query.",
            "Faithfulness (Final Answer)": "Whether final-answer claims are supported by retrieved context.",
            "Hallucination": "Whether the final answer contains claims unsupported by the supplied context.",
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    print(f"DeepEval completed for {len(cases)} queries.")
    print(
        f"Passed metrics: {passed_count}/{total_count} "
        f"({report['scores']['pass_rate']:.1%})"
    )
    error_count = sum(row["status"] == "error" for row in metric_rows)
    if error_count:
        print(f"Metric evaluations with errors: {error_count}")
        print("Errors and completed scores were saved to the report.")
    for group_name, group in scores_by_group.items():
        print(f"\n{group_name}: {group['passed']}/{group['count']} passed")
        for metric_name, summary in group["metrics"].items():
            print(
                f"  {metric_name}: average={summary['average_score']} "
                f"passed={summary['passed']}/{summary['count']}"
            )
    print(f"\nDetailed report: {report_path}")
    return 1 if error_count else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate retrieval, RCA, and final answers on selected query cases."
        )
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="1-based index of the first query case to evaluate (default: 1).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of query cases to evaluate (default: 10).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Run the selected real local retrieval/RCA cases and deterministic "
            "checks without LLM judges."
        ),
    )
    args = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            main(
                dry_run=args.dry_run,
                start_index=args.start_index,
                limit=args.limit,
            )
        )
    )
