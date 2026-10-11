"""Deferred DeepEval evaluation for feedback-flagged responses."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from .storage import FeedbackStore

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _judge():
    from evaluations.aicredits_judge import AICreditsGeminiJudge

    api_key = os.getenv("ai_credits_api_key") or os.getenv("AI_CREDITS_API_KEY")
    if not api_key:
        raise RuntimeError("AICredits judge key is not configured.")
    return AICreditsGeminiJudge(
        api_key=api_key,
        base_url=os.getenv("DEEPEVAL_BASE_URL", "https://api.aicredits.in/v1"),
        model=os.getenv("DEEPEVAL_MODEL", "google/gemini-3.1-flash-lite"),
    )


def evaluate_feedback_item(item: dict[str, Any], store: FeedbackStore | None = None) -> dict[str, Any]:
    """Evaluate one flagged feedback row and persist the result."""
    store = store or FeedbackStore()
    evaluator_name = "DeepEval: AnswerRelevancy + Faithfulness"
    context = item.get("context_json") or "{}"
    try:
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase

        judge = _judge()
        test_case = LLMTestCase(
            input=item["query"],
            actual_output=item["final_response"],
            retrieval_context=[context],
        )
        results: dict[str, Any] = {}
        for metric in (
            AnswerRelevancyMetric(model=judge, async_mode=False),
            FaithfulnessMetric(model=judge, async_mode=False),
        ):
            try:
                metric.measure(test_case)
                results[metric.__class__.__name__] = {
                    "score": getattr(metric, "score", None),
                    "success": getattr(metric, "success", None),
                    "reason": getattr(metric, "reason", None),
                }
            except Exception as exc:
                results[metric.__class__.__name__] = {"error": str(exc)}
        status = "success" if results and not all("error" in value for value in results.values()) else "error"
        store.save_evaluation(
            response_id=item["response_id"], feedback_id=item["id"],
            evaluator=evaluator_name, status=status, scores=results,
        )
        return {"feedback_id": item["id"], "status": status, "scores": results}
    except Exception as exc:
        store.save_evaluation(
            response_id=item["response_id"], feedback_id=item["id"],
            evaluator=evaluator_name, status="error", error=str(exc),
        )
        return {"feedback_id": item["id"], "status": "error", "error": str(exc)}


def evaluate_flagged(limit: int = 20, *, force: bool = False, store: FeedbackStore | None = None) -> list[dict[str, Any]]:
    """Evaluate pending negative feedback; existing evaluations are skipped."""
    store = store or FeedbackStore()
    items = store.flagged_feedback(limit, force=force)
    return [evaluate_feedback_item(item, store) for item in items]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate flagged feedback with DeepEval.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    print(evaluate_flagged(args.limit))
