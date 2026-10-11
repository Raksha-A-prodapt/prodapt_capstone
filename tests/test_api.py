from __future__ import annotations

import unittest
from typing import Any

from starlette.testclient import TestClient

from api import app


class FakeOrchestrator:
    async def run(
        self,
        query: str,
        network_metrics: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "query": query,
            "top_k": top_k,
            "network_metrics": network_metrics,
        }

    def classify_scenario(
        self,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        return {"status": "classified", "metrics": metrics}


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.state.orchestrator = FakeOrchestrator()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.state.orchestrator = None

    def test_health_and_frontend_are_served(self) -> None:
        health = self.client.get("/api/health")
        frontend = self.client.get("/")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(
            health.json(),
            {
                "status": "ok",
                "orchestrator_initialized": True,
            },
        )
        self.assertEqual(frontend.status_code, 200)
        self.assertIn("Telecom Network Assistant", frontend.text)

    def test_analyze_endpoint_validates_and_forwards_request(self) -> None:
        response = self.client.post(
            "/api/analyze",
            json={
                "query": "Find winter latency incidents",
                "network_metrics": {"Latency (ms)": 145},
                "top_k": 7,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["top_k"], 7)
        self.assertEqual(
            response.json()["network_metrics"],
            {"Latency (ms)": 145},
        )

    def test_invalid_analyze_request_returns_422(self) -> None:
        response = self.client.post(
            "/api/analyze",
            json={"query": "x", "top_k": 51},
        )

        self.assertEqual(response.status_code, 422)

    def test_frontend_origin_is_allowed_to_call_api(self) -> None:
        response = self.client.options(
            "/api/analyze",
            headers={
                "Origin": "http://127.0.0.1:8790",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://127.0.0.1:8790",
        )

    def test_classification_endpoint_uses_active_classifier_surface(self) -> None:
        response = self.client.post(
            "/api/classify",
            json={"network_metrics": {"Latency (ms)": 145}},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "classified")


if __name__ == "__main__":
    unittest.main()
