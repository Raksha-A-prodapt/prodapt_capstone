"""Run DeepEval contract checks and an LLM judge on orchestrator response fixtures.

Run from the repository root:
    python -m evaluations.run_orchestrator_deepeval

These controlled response fixtures assess response quality with Gemini via
AICredits as the LLM judge, validate agent-output contracts, and do not
require live Synapt.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from deepeval.models import DeepEvalBaseLLM

from evaluations.aicredits_judge import AICreditsGeminiJudge
from evaluations.orchestrator_deepeval import (
    REPORT_PATH,
    evaluate_responses_with_deepeval,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JUDGE_MODEL = "google/gemini-3.1-flash-lite"

FLOW_CHART = [
    "User query",
    "QuerySynaptAgent: guardrail, parsing, historical retrieval",
    "NetworkPredictionAgent: optional when current metrics are supplied",
    "RCAAgent: compare retrieved evidence with available metrics/predictions",
    "RecommendationAgent: retrieve SOP only when recommendations are requested",
    "Frontend response: final_answer plus prediction, RCA, history, recommendation sections",
    "LLM-as-judge: evaluate the assembled response for query relevance, clarity, evidence, and appropriate uncertainty",
]

EVALUATION_FLOW_CHART = [
    "Three controlled orchestrator response fixtures",
    "LLM judge: GEval assesses answer quality, evidence use, and appropriate uncertainty",
    "Frontend Response Contract metric: schema version, agent identity, final answer, four sections and required fields",
    "Evidence and Agent Flow metric: RCA incident references, SOP lookup gating, and recommendation-to-procedure links",
    "Record per-case metric score, pass/fail status, and reason",
    "Save all results and both flow charts to evaluations/reports/orchestrator_deepeval_report.json",
]

METRIC_DESCRIPTIONS = {
    "Orchestrator Response Quality": (
        "LLM-judged relevance, clarity, consistency, evidence grounding, and "
        "appropriate uncertainty about predictions and recommendations."
    ),
    "Frontend Response Contract": (
        "Checks schema_version, orchestrator identity, final_answer, "
        "and prediction/RCA/history/recommendation section fields."
    ),
    "Evidence and Agent Flow": (
        "Checks RCA incident references against retrieved incidents, "
        "ensures SOP retrieval follows query intent, and checks that "
        "recommendations reference retrieved procedures."
    ),
}


def _load_judge() -> DeepEvalBaseLLM:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("ai_credits_api_key") or os.getenv(
        "AI_CREDITS_API_KEY"
    )
    if not api_key:
        raise RuntimeError(
            "Configure ai_credits_api_key in the project .env before running "
            "the LLM judge."
        )
    return AICreditsGeminiJudge(
        api_key=api_key,
        base_url=os.getenv(
            "DEEPEVAL_BASE_URL",
            "https://api.aicredits.in/v1",
        ),
        model=os.getenv("DEEPEVAL_MODEL", DEFAULT_JUDGE_MODEL),
    )


def _response(
    query: str,
    *,
    recommendations_requested: bool,
    include_prediction: bool,
) -> dict:
    incident = {
        "incident_id": "INC-EVAL-001",
        "scores": {"hybrid": 0.84, "bm25": 0.75, "semantic": 0.9},
        "incident": {
            "incident_id": "INC-EVAL-001",
            "latency_ms": 82.0,
            "packet_loss_rate": 5.0,
            "call_drop_rate": 1.2,
        },
        "document": "Evaluation fixture: historical high-latency incident.",
    }
    procedure = {
        "sop_id": "SOP-EVAL-001",
        "name": "Latency investigation",
        "recommended_actions": ["Review alarms on the affected network segment."],
    }
    recommendations = [
        {
            "action": action,
            "procedure_id": procedure["sop_id"],
            "procedure_name": procedure["name"],
            "source": "Synapt procedure retrieval",
        }
        for action in procedure["recommended_actions"]
    ] if recommendations_requested else []
    procedures = [procedure] if recommendations_requested else []
    if include_prediction:
        prediction_data = {
            "status": "success",
            "prediction": {
                "network_performance": {
                    "status": "success",
                    "predicted_throughput_mbps": 315.4,
                },
                "fault_risk": {
                    "status": "success",
                    "predicted_fault_occurrence_rate_percent": 14.2,
                    "fault_risk": "LOW",
                },
            },
        }
        prediction_summary = (
            "Predicted throughput: 315.4 Mbps; "
            "predicted fault occurrence rate: 14.2% (LOW risk)."
        )
    else:
        prediction_data = {
            "status": "not_applicable",
            "reason": "Current network metrics were not provided.",
            "prediction": {
                "network_performance": {"status": "not_run"},
                "fault_risk": {"status": "not_run"},
            },
        }
        prediction_summary = (
            "Predictions were not run because current network metrics "
            "were not provided."
        )

    rca_data = {
        "status": "success",
        "summary": {
            "top_hypothesis": "latency / congestion issue",
            "top_score": 0.81,
        },
        "hypotheses": [
            {
                "hypothesis": "latency / congestion issue",
                "score": 0.81,
                "matched_incident_id": incident["incident_id"],
            }
        ],
    }
    recommendation_data = {
        "status": "success" if recommendations_requested else "not_requested",
        "requested": recommendations_requested,
        "procedure_retrieval_called": recommendations_requested,
        "procedures": procedures,
        "recommendations": recommendations,
    }
    classification_data = {
        "status": "available",
        "basis": "Dataset-relative triage thresholds.",
        "historical_examples": {
            "incident_count": 1,
            "priority_counts": {"P1": 0, "P2": 0, "P3": 0, "P4": 1},
            "highest_priority": "P4",
            "incidents": [
                {
                    "incident_id": incident["incident_id"],
                    "priority": "P4",
                    "labels": [],
                }
            ],
        },
        "current_scenario": None,
    }
    impact_data = {
        "status": "available" if include_prediction else "not_applicable",
        "basis": "Controlled evaluation fixture.",
        "findings": (
            [
                {
                    "metric": "predicted_throughput_mbps",
                    "observed_value": 315.4,
                    "potential_impact": "Model-estimated throughput.",
                    "confirmed_impact": False,
                }
            ]
            if include_prediction
            else []
        ),
        "limitations": [],
    }
    sections = [
        {
            "id": "prediction",
            "title": "Network Predictions",
            "status": prediction_data["status"],
            "summary": prediction_summary,
            "data": prediction_data,
        },
        {
            "id": "root_cause_analysis",
            "title": "Root-Cause Analysis",
            "status": "success",
            "summary": "Leading hypothesis is latency/congestion, not a confirmed cause.",
            "data": rca_data,
        },
        {
            "id": "historical_data",
            "title": "Historical Incident Matches",
            "status": "success",
            "summary": "One historical incident retrieved.",
            "data": {"returned_count": 1, "incidents": [incident]},
        },
        {
            "id": "recommendations",
            "title": "Recommendations",
            "status": recommendation_data["status"],
            "summary": (
                "Review alarms on the affected network segment."
                if recommendations_requested
                else "Not requested; procedure lookup was skipped."
            ),
            "data": recommendation_data,
        },
        {
            "id": "incident_prioritization",
            "title": "Incident Classification and Prioritization",
            "status": "available",
            "summary": "One returned example is classified as P4.",
            "data": classification_data,
        },
        {
            "id": "network_impact",
            "title": "Network Impact Assessment",
            "status": impact_data["status"],
            "summary": "Potential impact only." if include_prediction else "No current metrics were supplied.",
            "data": impact_data,
        },
    ]
    return {
        "schema_version": 1,
        "agent": "TelecomAnalysisOrchestrator",
        "status": "success",
        "query": query,
        "final_answer": "\n\n".join(
            f"## {section['title']}\n{section['summary']}"
            for section in sections
        ),
        "sections": sections,
        "trace": {
            "synapt_procedure_retrieval_called": recommendations_requested,
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cases = [
        (
            "metrics_missing_sop_skipped",
            "Summarize historical latency incidents.",
            _response(
                "Summarize historical latency incidents.",
                recommendations_requested=False,
                include_prediction=False,
            ),
        ),
        (
            "prediction_and_recommendation_requested",
            "Predict the network status and recommend next steps for latency.",
            _response(
                "Predict the network status and recommend next steps for latency.",
                recommendations_requested=True,
                include_prediction=True,
            ),
        ),
        (
            "recommendation_requested_without_predictions",
            "Suggest troubleshooting steps for high latency.",
            _response(
                "Suggest troubleshooting steps for high latency.",
                recommendations_requested=True,
                include_prediction=False,
            ),
        ),
    ]
    judge = _load_judge()
    judge_model_name = os.getenv(
        "DEEPEVAL_MODEL",
        DEFAULT_JUDGE_MODEL,
    )
    result = evaluate_responses_with_deepeval(
        cases,
        write_report=False,
        judge_model=judge,
        judge_model_name=judge_model_name,
    )
    result["flow_chart"] = FLOW_CHART
    result["evaluation_flow_chart"] = EVALUATION_FLOW_CHART
    result["metric_descriptions"] = METRIC_DESCRIPTIONS
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("DeepEval orchestration evaluation")
    print(f"Status: {result['status']}")
    print(
        f"Passed metrics: {result['passed_metrics']}/"
        f"{result['metric_count']} across {result['test_case_count']} cases"
    )
    for metric in result["metrics"]:
        print(
            f"{metric['test_case']} | {metric['name']}: "
            f"score={metric['score']} passed={metric['success']} "
            f"reason={metric['reason']}"
        )
    print(f"Report saved to: {REPORT_PATH}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
