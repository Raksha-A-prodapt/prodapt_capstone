"""Small, real-agent DeepEval benchmark for the Synapt MCP QueryAgent.

This evaluates the agent in ``synapt_mcp_bundle/query_agent/agent.py`` against
live Synapt data.  It intentionally runs only a few representative cases so
that LLM-judge cost and MCP latency stay bounded.

Run from the repository root:
    venv\\Scripts\\python.exe -m evaluations.synapt_agent_deepeval --limit 3

The Synapt agent reads credentials from ``synapt_mcp_bundle/.env``.  The judge
uses the project-root ``.env`` for the AICredits key, unless
``DEEPEVAL_JUDGE_ENV`` is set to another file.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

from deepeval import evaluate
from deepeval.evaluate.configs import AsyncConfig, CacheConfig, DisplayConfig
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, SingleTurnParams
from dotenv import load_dotenv

from evaluations.aicredits_judge import AICreditsGeminiJudge
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "evaluations" / "reports" / "synapt_agent_deepeval_report.json"

# These are deliberately broad and representative rather than trivia questions.
# Expected answers are used by DeepEval as a relevance/completeness reference,
# not as exact string-match targets.
CASES = [
    {
        "name": "core_capabilities",
        "query": "What are the main capabilities and tools available through Synapt?",
        "expected": "Explain the agent's available knowledge/query capabilities and name the relevant tools or functions when supported by the retrieved context.",
        "needs_procedures": False,
    },
    {
        "name": "recommendations_and_sop",
        "query": "Suggest recommendations and troubleshooting procedures for a network issue with high latency and packet loss.",
        "expected": "Suggest relevant troubleshooting recommendations grounded in Synapt SOP/procedure evidence, and clearly distinguish retrieved procedures from assumptions.",
        "needs_procedures": True,
    },
    {
        "name": "evidence_grounded_question",
        "query": "What does the available Synapt knowledge say about monitoring, incidents, or operational guidance?",
        "expected": "Give a concise answer grounded in the retrieved Synapt knowledge, cite or describe supporting evidence, and state uncertainty when the context is insufficient.",
        "needs_procedures": False,
    },
]


def _load_judge() -> DeepEvalBaseLLM:
    load_dotenv(ROOT / ".env", override=False)
    env_file = os.getenv("DEEPEVAL_JUDGE_ENV")
    if env_file:
        load_dotenv(Path(env_file), override=False)
    api_key = os.getenv("ai_credits_api_key") or os.getenv("AI_CREDITS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No AICredits key found for the judge. Set ai_credits_api_key in "
            "the project-root .env or configure DEEPEVAL_JUDGE_ENV."
        )
    return AICreditsGeminiJudge(
        api_key=api_key,
        base_url=os.getenv("DEEPEVAL_BASE_URL", "https://api.aicredits.in/v1"),
        model=os.getenv("DEEPEVAL_MODEL", "google/gemini-3.1-flash-lite"),
    )


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _contexts(value: Any) -> list[str]:
    """Convert the agent's raw chunk response into DeepEval context strings."""
    if isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        items = value.get("chunks") or value.get("results") or value.get("data") or [value]
    else:
        items = [value]
    output: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("content") or item.get("document") or item
        else:
            text = item
        rendered = _text(text).strip()
        if rendered:
            output.append(rendered)
    return output


async def _collect(limit: int, top_k: int) -> list[dict[str, Any]]:
    # Evaluate through the running local bridge. The bridge itself loads
    # synapt_mcp_bundle/.env and calls the registered Synapt QueryAgent.
    selected = CASES[:limit]
    records: list[dict[str, Any]] = []
    mcp_url = os.getenv("SYNAPT_EVAL_MCP_URL", "http://127.0.0.1:8000/mcp")
    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            for case in selected:
                try:
                    answer_result = await session.call_tool(
                        "ask_synapt",
                        {"question": case["query"], "top_k": top_k, "graph_hops": 2},
                    )
                    chunks_result = await session.call_tool(
                        "get_synapt_chunks",
                        {"query": case["query"], "top_k": top_k},
                    )
                    procedure_payload = None
                    if case.get("needs_procedures"):
                        procedure_result = await session.call_tool(
                            "get_synapt_procedures",
                            {"query": case["query"]},
                        )
                        procedure_payload = _tool_payload(procedure_result)
                    answer_payload = _tool_payload(answer_result)
                    chunks_payload = _tool_payload(chunks_result)
                    answer_text = (
                        answer_payload.get("answer")
                        if isinstance(answer_payload, dict)
                        else answer_payload
                    )
                    records.append(
                        {
                            "name": case["name"],
                            "query": case["query"],
                            "expected": case["expected"],
                            "answer": _text(answer_text),
                            "raw_metadata": {
                                key: answer_payload[key]
                                for key in ("confidence_score", "ks_confidence", "ps_confidence", "graph_confidence", "trust_signal", "warnings", "resolved_mode", "intent")
                                if isinstance(answer_payload, dict) and key in answer_payload
                            },
                            "contexts": _contexts(chunks_payload)
                            + (_contexts(procedure_payload) if procedure_payload is not None else []),
                            "procedures_retrieved": procedure_payload is not None,
                            "error": None,
                        }
                    )
                except Exception as exc:
                    records.append(
                        {
                            "name": case["name"],
                            "query": case["query"],
                            "expected": case["expected"],
                            "answer": "",
                            "raw_metadata": {},
                            "contexts": [],
                            "procedures_retrieved": False,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
    return records


def _tool_payload(result: Any) -> Any:
    if getattr(result, "isError", False):
        raise RuntimeError("MCP tool returned an error")
    text_parts = [item.text for item in result.content if getattr(item, "text", None)]
    text = "\n".join(text_parts).strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _metric_rows(cases: list[LLMTestCase], metrics: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    test_run_console = import_module("deepeval.test_run.test_run").console
    for test_case in cases:
        previous_file = test_run_console.file
        test_run_console.file = io.StringIO()
        try:
            result = evaluate(
                test_cases=[test_case],
                metrics=metrics,
                cache_config=CacheConfig(write_cache=False, use_cache=False),
                async_config=AsyncConfig(run_async=False),
                display_config=DisplayConfig(
                    show_indicator=False,
                    print_results=False,
                    verbose_mode=False,
                    inspect_after_run=False,
                ),
            )
        finally:
            test_run_console.file = previous_file
        for test_result in result.test_results:
            for metric in test_result.metrics_data:
                rows.append(
                    {
                        "case": test_result.name,
                        "metric": metric.name,
                        "score": metric.score,
                        "success": bool(metric.success),
                        "reason": metric.reason,
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3, choices=(2, 3))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    records = asyncio.run(_collect(args.limit, args.top_k))
    usable = [record for record in records if not record["error"] and record["answer"].strip()]
    if not usable:
        raise RuntimeError("The Synapt agent returned no usable answers. See connection errors in the report.")

    judge = _load_judge()
    test_cases = [
        LLMTestCase(
            name=record["name"],
            input=record["query"],
            actual_output=record["answer"],
            expected_output=record["expected"],
            retrieval_context=record["contexts"],
        )
        for record in usable
    ]
    metrics = [
        AnswerRelevancyMetric(model=judge, threshold=0.6, async_mode=False),
        FaithfulnessMetric(model=judge, threshold=0.6, async_mode=False),
        ContextualRelevancyMetric(model=judge, threshold=0.6, async_mode=False),
        GEval(
            name="Synapt Answer Quality",
            criteria=(
                "Assess the answer using balanced standards: it should address the question, "
                "be understandable and sufficiently complete, remain grounded in the supplied "
                "Synapt context, avoid invented details, and acknowledge uncertainty when the "
                "context does not support a firm claim. Do not reward verbosity or penalize a "
                "concise answer that covers the important points."
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
    ]
    rows = _metric_rows(test_cases, metrics)
    numeric = [float(row["score"]) for row in rows if isinstance(row["score"], (int, float))]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if not any(record["error"] for record in records) else "completed_with_agent_errors",
        "framework": "DeepEval",
        "agent": "synapt_mcp_bundle.query_agent.agent.QueryAgent",
        "judge_model": judge.get_model_name(),
        "judge_policy": "Balanced threshold 0.60; scores are reported raw and not converted to artificial perfect values.",
        "query_count": len(records),
        "usable_query_count": len(usable),
        "average_score": sum(numeric) / len(numeric) if numeric else None,
        "records": records,
        "metrics": rows,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    passed = sum(1 for row in rows if row["success"])
    print(f"Synapt DeepEval completed: {passed}/{len(rows)} metric checks passed")
    print(f"Average score: {report['average_score']:.3f}" if report["average_score"] is not None else "Average score: unavailable")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
