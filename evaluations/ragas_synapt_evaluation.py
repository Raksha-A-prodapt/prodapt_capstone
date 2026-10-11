"""Run RAGAS metrics over the real Synapt-agent benchmark output.

The input is the three-case live report produced by synapt_agent_deepeval.py.
This avoids repeating MCP calls while still using the actual Synapt answers and
retrieved context. The judge is the configured AICredits OpenAI-compatible
Gemini endpoint.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    ContextRelevance,
    Faithfulness,
    LLMContextPrecisionWithoutReference,
)
from ragas.run_config import RunConfig
from ragas.dataset_schema import SingleTurnSample

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "evaluations" / "reports" / "synapt_agent_deepeval_report.json"
REPORT_PATH = ROOT / "evaluations" / "reports" / "ragas_synapt_report.json"
GOOD_THRESHOLD = 0.60
MINIMUM_VALID_METRICS = 2
RAGAS_CONTEXT_LIMIT = 3
RAGAS_CONTEXT_CHARS = 3500


def _load_model() -> ChatOpenAI:
    load_dotenv(ROOT / ".env", override=False)
    api_key = os.getenv("ai_credits_api_key") or os.getenv("AI_CREDITS_API_KEY")
    if not api_key:
        raise RuntimeError("AICredits key is missing from the project .env")
    return ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPEVAL_BASE_URL", "https://api.aicredits.in/v1"),
        model=os.getenv("DEEPEVAL_MODEL", "google/gemini-3.1-flash-lite"),
        temperature=0,
        max_tokens=2000,
        timeout=120,
    )


def _load_samples() -> list[dict[str, Any]]:
    source = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    samples = []
    for record in source.get("records", []):
        if record.get("error") or not record.get("answer") or not record.get("contexts"):
            continue
        compact = dict(record)
        compact["contexts"] = [
            str(context)[:RAGAS_CONTEXT_CHARS]
            for context in record["contexts"][:RAGAS_CONTEXT_LIMIT]
        ]
        samples.append(compact)
    if not samples:
        raise RuntimeError(f"No usable Synapt records found in {INPUT_PATH}")
    return samples


def main() -> int:
    records = _load_samples()
    dataset = EvaluationDataset(
        samples=[
            SingleTurnSample(
                user_input=record["query"],
                response=record["answer"],
                retrieved_contexts=record["contexts"],
            )
            for record in records
        ]
    )
    llm = LangchainLLMWrapper(_load_model())
    metrics = [
        Faithfulness(llm=llm, name="Faithfulness"),
        LLMContextPrecisionWithoutReference(
            llm=llm,
            name="Context Precision",
        ),
        ContextRelevance(llm=llm, name="Context Relevance"),
    ]
    result = evaluate(
        dataset,
        metrics=metrics,
        run_config=RunConfig(max_retries=2, max_wait=30, timeout=120),
        raise_exceptions=False,
        show_progress=False,
    )
    frame = result.to_pandas()
    metric_names = [metric.name for metric in metrics]
    metric_rows: dict[str, dict[str, Any]] = {}
    for name in metric_names:
        values = [float(value) for value in frame[name].tolist() if value == value]
        average = sum(values) / len(values) if values else None
        metric_rows[name] = {
            "average_score": average,
            "count": len(values),
            "good": average is not None and average >= GOOD_THRESHOLD,
        }
    averages = [
        row["average_score"]
        for row in metric_rows.values()
        if isinstance(row["average_score"], (int, float))
    ]
    overall = sum(averages) / len(averages) if averages else None
    all_metrics_scored = len(averages) == len(metric_names)
    valid_metrics_good = (
        len(averages) >= MINIMUM_VALID_METRICS
        and overall is not None
        and overall >= GOOD_THRESHOLD
    )
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "framework": "RAGAS",
        "agent": "synapt_mcp_bundle.query_agent.agent.QueryAgent",
        "judge_provider": "AICredits OpenAI-compatible API",
        "judge_model": os.getenv("DEEPEVAL_MODEL", "google/gemini-3.1-flash-lite"),
        "source_report": str(INPUT_PATH),
        "query_count": len(records),
        "good_threshold": GOOD_THRESHOLD,
        "overall_score": overall,
        "all_metrics_scored": all_metrics_scored,
        "minimum_valid_metrics": MINIMUM_VALID_METRICS,
        "context_window": {
            "max_contexts_per_query": RAGAS_CONTEXT_LIMIT,
            "max_characters_per_context": RAGAS_CONTEXT_CHARS,
        },
        "qualifies_for_frontend": valid_metrics_good,
        "metrics": metric_rows,
        "per_query": frame.to_dict(orient="records"),
        "metric_definitions": {
            "Faithfulness": "Whether answer claims are supported by retrieved Synapt context.",
            "Context Precision": "Whether retrieved context is relevant to the query without requiring a reference answer.",
            "Context Relevance": "How relevant the retrieved context is to the user query.",
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"RAGAS completed: overall={overall:.3f}" if overall is not None else "RAGAS completed: no score")
    print(f"Qualifies for frontend: {report['qualifies_for_frontend']}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
