"""DeepEval contract checks for the orchestrated telecom response."""

from __future__ import annotations

import json
import io
from importlib import import_module
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig, CacheConfig, DisplayConfig
from deepeval.metrics import BaseMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

REPORT_PATH = Path(__file__).resolve().parent / "reports" / "orchestrator_deepeval_report.json"


REQUIRED_SECTION_IDS = {
    "prediction",
    "root_cause_analysis",
    "historical_data",
    "recommendations",
    "incident_prioritization",
    "network_impact",
}


class FrontendResponseContractMetric(BaseMetric):
    """Check the response contract and completeness of frontend sections."""

    def __init__(self) -> None:
        super().__init__()
        self.threshold = 1.0
        self.async_mode = False
        self.verbose_mode = False

    @property
    def __name__(self) -> str:
        return "Frontend Response Contract"

    def measure(self, test_case: LLMTestCase) -> float:
        failures: list[str] = []
        try:
            response = json.loads(test_case.actual_output or "{}")
        except json.JSONDecodeError:
            response = {}
            failures.append("response is not valid JSON")

        if response.get("schema_version") != 1:
            failures.append("unsupported or missing schema_version")
        if response.get("agent") != "TelecomAnalysisOrchestrator":
            failures.append("orchestrator identity is missing")
        if not isinstance(response.get("final_answer"), str) or not response.get(
            "final_answer", ""
        ).strip():
            failures.append("final_answer is missing")

        sections = response.get("sections")
        if not isinstance(sections, list):
            sections = []
            failures.append("sections must be a list")
        section_by_id = {
            section.get("id"): section
            for section in sections
            if isinstance(section, dict)
        }
        missing_sections = REQUIRED_SECTION_IDS - set(section_by_id)
        if missing_sections:
            failures.append(
                "required sections missing: "
                + ", ".join(sorted(missing_sections))
            )

        for section_id, section in section_by_id.items():
            if not section.get("title") or not section.get("status"):
                failures.append(f"{section_id} lacks title or status")
            if not isinstance(section.get("summary"), str):
                failures.append(f"{section_id} lacks a display summary")
            if not isinstance(section.get("data"), dict):
                failures.append(f"{section_id} lacks structured data")

        self.score = 1.0 if not failures else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            "; ".join(failures)
            if failures
            else "The frontend response has all required sections and fields."
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)


class EvidenceFlowMetric(BaseMetric):
    """Check that RCA and recommendations reference retrieved evidence."""

    def __init__(self) -> None:
        super().__init__()
        self.threshold = 1.0
        self.async_mode = False
        self.verbose_mode = False

    @property
    def __name__(self) -> str:
        return "Evidence and Agent Flow"

    def measure(self, test_case: LLMTestCase) -> float:
        failures: list[str] = []
        try:
            response = json.loads(test_case.actual_output or "{}")
        except json.JSONDecodeError:
            response = {}
            failures.append("response is not valid JSON")

        sections = {
            section.get("id"): section
            for section in response.get("sections", [])
            if isinstance(section, dict)
        }
        history = sections.get("historical_data", {}).get("data", {})
        incidents = history.get("incidents", [])
        incident_ids = {
            item.get("incident_id")
            for item in incidents
            if isinstance(item, dict) and item.get("incident_id")
        }

        rca_data = sections.get("root_cause_analysis", {}).get("data", {})
        for hypothesis in rca_data.get("hypotheses", []):
            matched_id = hypothesis.get("matched_incident_id")
            if matched_id and matched_id not in incident_ids:
                failures.append(
                    f"RCA hypothesis references unknown incident {matched_id}"
                )

        recommendation_data = sections.get("recommendations", {}).get("data", {})
        procedure_retrieval_called = bool(
            response.get("trace", {}).get(
                "synapt_procedure_retrieval_called", False
            )
        )
        requested = recommendation_data.get("requested")
        if requested is False and procedure_retrieval_called:
            failures.append("Synapt procedures were fetched when not requested")
        if requested is True and not procedure_retrieval_called:
            failures.append("requested procedures were not traced as retrieved")

        procedure_ids = {
            procedure.get("sop_id", procedure.get("procedure_id"))
            for procedure in recommendation_data.get("procedures", [])
            if isinstance(procedure, dict)
        }
        for item in recommendation_data.get("recommendations", []):
            if not isinstance(item, dict) or not item.get("action"):
                failures.append("recommendation is missing its action")
                continue
            procedure_id = item.get("procedure_id")
            if procedure_id and procedure_ids and procedure_id not in procedure_ids:
                failures.append(
                    f"recommendation references unknown procedure {procedure_id}"
                )

        classification = sections.get(
            "incident_prioritization", {}
        ).get("data", {})
        historical_classification = classification.get(
            "historical_examples", {}
        )
        priority_counts = historical_classification.get(
            "priority_counts", {}
        )
        if historical_classification.get("incident_count") != len(incidents):
            failures.append(
                "incident classifications do not match returned incident count"
            )
        if sum(priority_counts.values()) != len(incidents):
            failures.append(
                "incident priority totals do not match returned incident count"
            )

        impact = sections.get("network_impact", {}).get("data", {})
        for finding in impact.get("findings", []):
            if finding.get("confirmed_impact") is not False:
                failures.append(
                    "impact finding must not claim a confirmed service outcome"
                )

        self.score = 1.0 if not failures else 0.0
        self.success = self.score >= self.threshold
        self.reason = (
            "; ".join(failures)
            if failures
            else "RCA and recommendation outputs follow the retrieved evidence flow."
        )
        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)


def evaluate_response_with_deepeval(
    response: dict[str, Any],
    query: str,
) -> dict[str, Any]:
    """Run deterministic DeepEval metrics on one actual orchestrator response.

    This path is called only when the query agent reports that its planning
    LLM was invoked. The metrics validate grounded flow and output contracts;
    they do not make another LLM-as-judge call.
    """
    return evaluate_responses_with_deepeval(
        [("live_telecom_orchestrator_response", query, response)],
        write_report=False,
    )


def evaluate_responses_with_deepeval(
    cases: list[tuple[str, str, dict[str, Any]]],
    *,
    write_report: bool = False,
    judge_model: Any | None = None,
    judge_model_name: str | None = None,
) -> dict[str, Any]:
    """Evaluate named orchestrator responses with contract and optional judge metrics."""
    test_cases = []
    for name, query, response in cases:
        test_cases.append(
            LLMTestCase(
                name=name,
                input=query,
                actual_output=json.dumps(
                    response,
                    ensure_ascii=False,
                    default=str,
                ),
                retrieval_context=[
                    incident.get("document", "")
                    for section in response.get("sections", [])
                    if section.get("id") == "historical_data"
                    for incident in section.get("data", {}).get("incidents", [])
                    if isinstance(incident, dict) and incident.get("document")
                ],
            )
        )

    metrics: list[BaseMetric] = [
        FrontendResponseContractMetric(),
        EvidenceFlowMetric(),
    ]
    if judge_model is not None:
        metrics.append(
            GEval(
                name="Orchestrator Response Quality",
                evaluation_steps=[
                    "Check that the response addresses the user's telecom query and is clear and internally consistent with its structured sections.",
                    "Check whether factual claims are supported by the supplied incident evidence and distinguish hypotheses from confirmed causes.",
                    "Check whether prediction and recommendation availability is described accurately for the user's request.",
                    "Score overall response quality from 0 to 10 and explain the score using specific evidence from the response.",
                ],
                evaluation_params=[
                    SingleTurnParams.INPUT,
                    SingleTurnParams.ACTUAL_OUTPUT,
                    SingleTurnParams.RETRIEVAL_CONTEXT,
                ],
                model=judge_model,
                threshold=0.6,
                async_mode=False,
            )
        )

    test_run_module = import_module("deepeval.test_run.test_run")
    test_run_console = test_run_module.console
    previous_console_file = test_run_console.file
    test_run_console.file = io.StringIO()
    try:
        evaluation = evaluate(
            test_cases=test_cases,
            metrics=metrics,
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
    finally:
        test_run_console.file = previous_console_file

    metric_results = []
    for test_result in evaluation.test_results:
        for metric_data in test_result.metrics_data:
            metric_results.append(
                {
                    "test_case": test_result.name,
                    "name": metric_data.name,
                    "score": metric_data.score,
                    "success": bool(metric_data.success),
                    "reason": metric_data.reason,
                }
            )

    result = {
        "status": (
            "passed"
            if metric_results and all(item["success"] for item in metric_results)
            else "failed"
        ),
        "framework": "DeepEval",
        "evaluation_type": (
            "llm_judged_quality_and_deterministic_contract_and_evidence_metrics"
            if judge_model is not None
            else "deterministic_contract_and_evidence_metrics"
        ),
        "llm_as_judge_used": judge_model is not None,
        "judge_model": judge_model_name if judge_model is not None else None,
        "test_case_count": len(test_cases),
        "metric_count": len(metric_results),
        "passed_metrics": sum(
            1 for item in metric_results if item["success"]
        ),
        "failed_metrics": sum(
            1 for item in metric_results if not item["success"]
        ),
        "metrics": metric_results,
    }
    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        result["report_path"] = str(REPORT_PATH)
    return result
