from __future__ import annotations

import unittest
from typing import Any

from agents.orchestrator import TelecomAnalysisOrchestrator
from agents.recommendation_agent import RecommendationAgent


class FakeQueryAgent:
    def __init__(
        self,
        llm_call_invoked: bool = False,
        blocked: bool = False,
    ) -> None:
        self.llm_call_invoked = llm_call_invoked
        self.blocked = blocked

    async def run(self, query: str, top_k: int = 5) -> dict[str, Any]:
        if self.blocked:
            return {
                "agent": "QuerySynaptAgent",
                "query": query,
                "status": "blocked",
                "answer": "Query blocked by input guardrail.",
                "rca_handoff": None,
                "guardrail": {
                    "allowed": False,
                    "reason": "Query blocked by input guardrail.",
                },
            }
        incident = {
            "incident_id": "INC000001",
            "scores": {"hybrid": 0.82, "bm25": 0.7, "semantic": 0.9},
            "incident": {
                "incident_id": "INC000001",
                "issue_reported": "yes",
                "latency_ms": 145.0,
                "packet_loss_rate": 5.0,
                "call_drop_rate": 1.2,
                "cell_availability": 95.0,
                "fault_occurrence_rate": 10.0,
            },
            "document": "historical incident",
        }
        return {
            "agent": "QuerySynaptAgent",
            "query": query,
            "status": "completed",
            "answer_status": "ready_for_rca",
            "llm_call_invoked": self.llm_call_invoked,
            "query_plan": {
                "numeric_conditions": [
                    {
                        "field": "latency_ms",
                        "operator": ">",
                        "value": 130.0,
                    }
                ]
            },
            "rca_handoff": {
                "retrieved_incidents": [incident],
                "synapt_context": {"status": "received", "answer": "context"},
            },
            "retrieved_incidents": [incident],
            "candidate_count": 142,
            "retrieval": {"candidate_count": 142},
            "synapt_context": {"status": "received"},
        }


class FakePredictionAgent:
    def __init__(self) -> None:
        self.received_metrics: dict[str, Any] | None = None

    def process(
        self,
        network_features: dict[str, Any],
        query: str | None = None,
    ) -> dict[str, Any]:
        self.received_metrics = network_features
        return {
            "agent": "NetworkPredictionAgent",
            "status": "success",
            "prediction": {
                "network_performance": {
                    "status": "success",
                    "predicted_throughput_mbps": 320.0,
                },
                "fault_risk": {
                    "status": "success",
                    "predicted_fault_occurrence_rate_percent": 12.0,
                    "fault_risk": "LOW",
                },
            },
            "trace": {
                "models_called": [
                    "throughput_prediction_model",
                    "fault_occurrence_prediction_model",
                ],
                "models_skipped": [],
            },
        }


class OrchestratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_simple_filtered_lookup_is_concise_and_labels_examples(self) -> None:
        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
        )

        result = await orchestrator.run(
            "Find historical incidents with latency above 130 ms."
        )

        self.assertIn("Historical Incident Matches", result["final_answer"])
        self.assertIn("INC000001", result["final_answer"])
        self.assertIn("Answer", result["final_answer"])
        self.assertNotIn("##", result["final_answer"])
        self.assertEqual(result["overall_summary_status"], "fallback")
        self.assertEqual(result["overall_summary_source"], "deterministic_fallback")
        self.assertEqual(
            result["sections"][2]["data"]["matching_count"],
            142,
        )
        self.assertEqual(
            result["sections"][2]["data"]["returned_count"],
            1,
        )

    async def test_procedure_lookup_is_skipped_when_not_requested(self) -> None:
        calls: list[str] = []

        async def retrieve(query: str, url: str) -> Any:
            calls.append(query)
            return {"procedures": []}

        recommendation_agent = RecommendationAgent(
            procedure_retriever=retrieve,
        )
        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
            recommendation_agent=recommendation_agent,
        )

        result = await orchestrator.run("Compare this with historical latency.")

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            [section["id"] for section in result["sections"]],
            [
                "prediction",
                "root_cause_analysis",
                "historical_data",
                "recommendations",
                "incident_prioritization",
                "network_impact",
            ],
        )
        self.assertEqual(calls, [])
        self.assertFalse(
            result["trace"]["synapt_procedure_retrieval_called"]
        )
        self.assertFalse(result["trace"]["llm_call_invoked"])
        self.assertEqual(result["overall_summary_status"], "fallback")
        self.assertEqual(
            result["overall_summary_source"],
            "deterministic_fallback",
        )
        self.assertIn("LLM summary unavailable", result["overall_summary"])
        self.assertIn(
            "1 historical incident(s) were retrieved for comparison.",
            result["overall_summary"],
        )
        self.assertFalse(result["trace"]["summary_llm_call_invoked"])
        self.assertNotIn("evaluation", result)
        self.assertIn("Historical Incident Matches", result["final_answer"])
        self.assertIn(
            "- INC000001: latency 145 ms",
            result["final_answer"],
        )
        self.assertIn(
            "Answer (deterministic fallback; LLM unavailable)",
            result["final_answer"],
        )

    async def test_recommendation_request_retrieves_synapt_procedures(self) -> None:
        calls: list[str] = []

        async def retrieve(query: str, url: str) -> Any:
            calls.append(query)
            return {
                "procedures": [
                    {
                        "sop_id": "SOP-1",
                        "name": "Latency investigation",
                        "recommended_actions": ["Review segment alarms."],
                    }
                ]
            }

        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
            recommendation_agent=RecommendationAgent(
                procedure_retriever=retrieve,
            ),
        )

        result = await orchestrator.run(
            "Recommend next steps for high latency."
        )

        self.assertEqual(len(calls), 1)
        self.assertTrue(
            result["trace"]["synapt_procedure_retrieval_called"]
        )
        recommendation_section = result["sections"][3]
        self.assertEqual(recommendation_section["status"], "success")
        self.assertEqual(
            recommendation_section["data"]["recommendations"][0]["action"],
            "Review segment alarms.",
        )

    async def test_metrics_prediction_and_sectioned_output(self) -> None:
        prediction_agent = FakePredictionAgent()
        metrics = {"Latency (ms)": 80.0}
        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
            prediction_agent=prediction_agent,
        )

        result = await orchestrator.run(
            "Analyze this network condition.",
            network_metrics=metrics,
        )

        self.assertIs(prediction_agent.received_metrics, metrics)
        prediction_section = result["sections"][0]
        self.assertEqual(
            prediction_section["data"]["prediction"]["network_performance"][
                "predicted_throughput_mbps"
            ],
            320.0,
        )
        self.assertIn("Predicted throughput: 320.0 Mbps", result["final_answer"])
        self.assertEqual(result["sections"][2]["data"]["returned_count"], 1)
        classification = result["sections"][4]["data"]
        self.assertEqual(
            classification["historical_examples"]["incident_count"],
            1,
        )
        self.assertIsNotNone(classification["current_scenario"])
        impact = result["sections"][5]["data"]
        self.assertEqual(impact["status"], "available")
        self.assertTrue(
            any(
                finding["metric"] == "predicted_throughput_mbps"
                for finding in impact["findings"]
            )
        )

    async def test_deepeval_runs_only_after_an_llm_call(self) -> None:
        evaluated_responses: list[dict[str, Any]] = []

        def evaluator(response: dict[str, Any], query: str) -> dict[str, Any]:
            evaluated_responses.append(response)
            return {
                "status": "passed",
                "framework": "DeepEval",
                "metrics": [],
            }

        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(llm_call_invoked=True),
            response_evaluator=evaluator,
        )

        result = await orchestrator.run("Summarize network latency.")

        self.assertEqual(len(evaluated_responses), 1)
        self.assertTrue(result["trace"]["llm_call_invoked"])
        self.assertEqual(result["evaluation"]["framework"], "DeepEval")

    async def test_llm_summary_is_appended_and_evaluated(self) -> None:
        evaluated_responses: list[dict[str, Any]] = []
        prompts: list[str] = []

        def summarize(system_prompt: str, user_prompt: str) -> str:
            prompts.append(user_prompt)
            return "The retrieved evidence suggests latency issues; review segment alarms."

        def evaluator(response: dict[str, Any], query: str) -> dict[str, Any]:
            evaluated_responses.append(response)
            return {"status": "passed", "framework": "DeepEval"}

        async def retrieve(query: str, url: str) -> Any:
            return {
                "procedures": [
                    {
                        "sop_id": "SOP-1",
                        "name": "Latency investigation",
                        "recommended_actions": ["Review segment alarms."],
                    }
                ]
            }

        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
            recommendation_agent=RecommendationAgent(
                procedure_retriever=retrieve,
            ),
            response_summarizer=summarize,
            response_evaluator=evaluator,
        )

        result = await orchestrator.run(
            "Recommend next steps for high latency."
        )

        self.assertTrue(result["final_answer"].startswith("Answer\n"))
        self.assertIn("Recommendations", result["final_answer"])
        self.assertNotIn("##", result["final_answer"])
        self.assertEqual(
            result["overall_summary"],
            "The retrieved evidence suggests latency issues; review segment alarms.",
        )
        self.assertIn(result["overall_summary"], result["final_answer"])
        self.assertIn("Review segment alarms.", prompts[0])
        self.assertTrue(result["trace"]["summary_llm_call_invoked"])
        self.assertEqual(
            result["trace"]["llm_call_sources"],
            ["TelecomAnalysisOrchestrator.response_summary"],
        )
        self.assertEqual(len(evaluated_responses), 1)
        self.assertEqual(
            evaluated_responses[0]["overall_summary"],
            result["overall_summary"],
        )
        self.assertEqual(result["evaluation"]["framework"], "DeepEval")

    async def test_summary_fallback_keeps_last_synapt_sop_action(self) -> None:
        async def retrieve(query: str, url: str) -> Any:
            return {
                "procedures": [
                    {
                        "sop_id": "SOP-1",
                        "name": "Latency investigation",
                        "recommended_actions": [
                            "Review segment alarms.",
                            "Verify latency after the corrective action.",
                        ],
                    }
                ]
            }

        def failed_summary(system_prompt: str, user_prompt: str) -> None:
            return None

        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(),
            recommendation_agent=RecommendationAgent(
                procedure_retriever=retrieve,
            ),
            response_summarizer=failed_summary,
        )

        result = await orchestrator.run(
            "Recommend next steps for high latency."
        )

        summary = result["overall_summary"]
        self.assertEqual(result["overall_summary_status"], "fallback")
        self.assertEqual(
            result["overall_summary_source"],
            "deterministic_fallback",
        )
        self.assertTrue(result["trace"]["summary_llm_call_invoked"])
        self.assertIn("LLM summary unavailable", summary)
        self.assertIn("Review segment alarms.", summary)
        self.assertTrue(
            summary.rstrip().endswith(
                "Final action returned by Synapt (SOP: Latency investigation): "
                "Verify latency after the corrective action."
            )
        )
        self.assertIn(summary, result["final_answer"])

    async def test_guardrail_block_stops_downstream_graph_nodes(self) -> None:
        calls: list[str] = []

        async def retrieve(query: str, url: str) -> Any:
            calls.append(query)
            return {}

        orchestrator = TelecomAnalysisOrchestrator(
            query_agent=FakeQueryAgent(blocked=True),
            recommendation_agent=RecommendationAgent(
                procedure_retriever=retrieve,
            ),
        )

        result = await orchestrator.run("unsafe request")

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["sections"][0]["id"], "query_status")
        self.assertEqual(calls, [])
        self.assertFalse(
            result["trace"]["synapt_procedure_retrieval_called"]
        )


if __name__ == "__main__":
    unittest.main()
