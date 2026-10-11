from __future__ import annotations

import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from pydantic import BaseModel

from evaluations.aicredits_judge import AICreditsGeminiJudge


class ScoreReason(BaseModel):
    score: float
    reason: str


def _completion(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class AICreditsGeminiJudgeTests(unittest.TestCase):
    def test_generate_requests_json_and_validates_schema_without_network(self) -> None:
        client = Mock()
        client.chat.completions.create.return_value = _completion(
            json.dumps({"score": 0.8, "reason": "Grounded."})
        )
        judge = AICreditsGeminiJudge(
            api_key="test-key",
            client=client,
            async_client=Mock(),
        )

        result = judge.generate("Score the response.", schema=ScoreReason)

        self.assertEqual(result, ScoreReason(score=0.8, reason="Grounded."))
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(
            request["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(request["model"], "google/gemini-3.1-flash-lite")
        self.assertIn(
            "JSON schema",
            request["messages"][0]["content"],
        )

    def test_generate_reports_invalid_or_empty_json(self) -> None:
        for content, message in (
            ("not json", "invalid JSON"),
            (None, "empty content"),
        ):
            with self.subTest(content=content):
                client = Mock()
                client.chat.completions.create.return_value = _completion(content)
                judge = AICreditsGeminiJudge(
                    api_key="test-key",
                    client=client,
                    async_client=Mock(),
                )

                with self.assertRaisesRegex(RuntimeError, message):
                    judge.generate("Score the response.", schema=ScoreReason)

    def test_async_generate_uses_mock_client(self) -> None:
        client = Mock()
        client.chat.completions.create = AsyncMock(
            return_value=_completion('{"score": 1, "reason": "Clear."}')
        )
        judge = AICreditsGeminiJudge(
            api_key="test-key",
            client=Mock(),
            async_client=client,
        )

        result = asyncio.run(judge.a_generate("Score the response."))

        self.assertEqual(
            json.loads(result),
            {"score": 1, "reason": "Clear."},
        )
        self.assertEqual(
            client.chat.completions.create.call_args.kwargs["response_format"],
            {"type": "json_object"},
        )


if __name__ == "__main__":
    unittest.main()
