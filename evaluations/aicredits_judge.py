"""DeepEval adapter for the AICredits OpenAI-compatible Gemini endpoint."""

from __future__ import annotations

import json
from typing import Any

from deepeval.models import DeepEvalBaseLLM
from openai import AsyncOpenAI, OpenAI


class AICreditsGeminiJudge(DeepEvalBaseLLM):
    """Call Gemini through AICredits and require JSON judge responses."""

    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-3.1-flash-lite",
        base_url: str = "https://api.aicredits.in/v1",
        client: OpenAI | None = None,
        async_client: AsyncOpenAI | None = None,
    ) -> None:
        self._client = client or OpenAI(api_key=api_key, base_url=base_url)
        self._async_client = async_client or AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        super().__init__(model=model)

    def load_model(self) -> OpenAI:
        return self._client

    @staticmethod
    def _prompt_with_schema(prompt: str, schema: Any | None) -> str:
        if schema is None:
            return prompt
        return (
            f"{prompt}\n\nReturn a JSON object matching this JSON schema:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )

    @staticmethod
    def _decode_response(content: str | None, schema: Any | None) -> Any:
        if not content or not content.strip():
            raise RuntimeError("AICredits Gemini judge returned empty content.")
        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "AICredits Gemini judge returned invalid JSON."
            ) from exc
        if schema is not None:
            return schema.model_validate(result)
        return json.dumps(result, ensure_ascii=False)

    def generate(self, prompt: str, schema: Any | None = None) -> Any:
        response = self.model.chat.completions.create(
            model=self.name,
            messages=[
                {
                    "role": "user",
                    "content": self._prompt_with_schema(prompt, schema),
                }
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return self._decode_response(content, schema)

    async def a_generate(self, prompt: str, schema: Any | None = None) -> Any:
        response = await self._async_client.chat.completions.create(
            model=self.name,
            messages=[
                {
                    "role": "user",
                    "content": self._prompt_with_schema(prompt, schema),
                }
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return self._decode_response(content, schema)

    def get_model_name(self) -> str:
        return self.name

    def supports_log_probs(self) -> bool:
        return False

    def supports_json_mode(self) -> bool:
        return True
