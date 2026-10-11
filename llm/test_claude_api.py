from __future__ import annotations

import sys

from llm_client import LLMClient


def main() -> int:
    try:
        client = LLMClient()
        client.max_tokens = 48
        answer = client.generate(
            "Reply briefly to confirm the API test.",
            "Reply exactly: Claude API test successful.",
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Claude API test failed: {exc}")
        return 1

    print(f"Provider: {client.last_provider}")
    selected_model = {
        "Anthropic Claude": client.model,
        "AICredits Gemini": client.ai_credits_model,
        "OpenRouter": client.openrouter_model,
    }.get(client.last_provider)
    print(f"Model: {selected_model}")
    print(f"Response: {answer}")
    print("Claude API test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
