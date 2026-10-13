

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AICREDITS_URL = "https://api.aicredits.in/v1/chat/completions"
DEFAULT_AICREDITS_MODEL = "google/gemini-3.1-flash-lite"


class LLMClient:

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "aicredits").strip().lower()
        self.last_provider = None
        self.ai_credits_model = os.getenv(
            "AICREDITS_MODEL",
            os.getenv("DEEPEVAL_MODEL", DEFAULT_AICREDITS_MODEL),
        )
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "")
        self.model = (
            self.ai_credits_model
            if self.provider in {"aicredits", "ai_credits", "aicredit"}
            else self.openrouter_model
        )

        self.temperature = float(
            os.getenv("LLM_TEMPERATURE", "0.1")
        )
        self.max_tokens = int(
            os.getenv("LLM_MAX_TOKENS", "1000")
        )
        self.timeout = int(
            os.getenv("LLM_TIMEOUT", "40")
        )

        if self.provider in {"aicredits", "ai_credits", "aicredit"}:
            self.api_key = os.getenv("ai_credits_api_key") or os.getenv(
                "AI_CREDITS_API_KEY"
            )
            self.base_url = os.getenv("AICREDITS_BASE_URL", AICREDITS_URL)
            self.provider_name = "AICredits Gemini"
            if not self.api_key:
                raise ValueError("ai_credits_api_key is missing in .env")
        elif self.provider == "openrouter":
            self.api_key = os.getenv("OPENROUTER_API_KEY1")
            self.base_url = OPENROUTER_URL
            self.provider_name = "OpenRouter"
            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY1 is missing in .env")
            if not self.model:
                raise ValueError("OPENROUTER_MODEL is missing in .env")
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER={self.provider!r}; use aicredits or openrouter"
            )

    def generate(self, system_prompt, user_prompt):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == "openrouter":
            headers.update(
                {
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Telecom Network RAG",
                }
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        print("\n[LLM]")
        print(f"Provider: {self.provider_name}")
        print(f"Model: {self.model}")

        try:

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            data = response.json()

            answer = data["choices"][0]["message"]["content"]

            if not answer:
                raise ValueError("LLM returned an empty response.")

            print("[LLM] SUCCESS")

            self.last_provider = self.provider_name

            return answer

        except requests.exceptions.RequestException as e:

            print("[LLM] FAILED")
            print(f"[LLM] Error: {e}")

            try:
                print("[LLM] Response:", response.text)
            except Exception:
                pass

            return None

        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
        ) as e:

            print("[LLM] INVALID RESPONSE")
            print(f"[LLM] Error: {e}")

            return None

    def analyze_incidents(
        self,
        query,
        retrieved_results,
        sop_evidence=None,
    ):

        system_prompt = """
You are a telecom network troubleshooting assistant.

Answer ONLY using the evidence provided.

Do not invent network conditions, root causes,
incidents, risk values, or corrective actions.

If evidence is insufficient, explicitly say so.

Clearly distinguish between:
- Evidence
- Inference
- Recommendation
"""

        evidence_parts = []

        for i, result in enumerate(
            retrieved_results,
            start=1
        ):

            scores = result.get("scores", {})

            record = (
                result.get("document")
                or result.get("record")
                or result.get("incident")
            )
            classification = result.get("classification")

            evidence_parts.append(
                f"""
Historical Incident {i}

Incident ID:
{result.get("incident_id")}

Hybrid Score:
{result.get("hybrid_score", scores.get("hybrid"))}

BM25 Score:
{result.get("bm25_score", scores.get("bm25"))}

Semantic Score:
{result.get("semantic_score", scores.get("semantic"))}

Record:
{record}

Classification:
{classification}
"""
            )

        evidence = "\n".join(evidence_parts)

        sop_context = json.dumps(
            sop_evidence or [],
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = f"""
User Query:

{query}

Retrieved Historical Evidence:

{evidence}

Retrieved Synthetic SOP Guidance:

{sop_context}

Provide the response in this structure:

1. Query Understanding
2. Relevant Historical Cases
3. Observed Network Pattern
4. Likely Root Cause
5. Network Impact
6. Recommended Corrective Actions
7. Evidence Limitations
"""

        answer = self.generate(
            system_prompt,
            user_prompt
        )

        if answer is not None:
            return answer

        print("[LLM] Using deterministic fallback.")

        return self._fallback(
            query,
            retrieved_results
        )

    def _fallback(
        self,
        query,
        retrieved_results
    ):

        if not retrieved_results:

            return f"""
1. Query Understanding

{query}

2. Relevant Historical Cases

No historical incidents were found.

3. Observed Network Pattern

Insufficient evidence.

4. Likely Root Cause

Cannot determine from available evidence.

5. Network Impact

Cannot determine from available evidence.

6. Recommended Corrective Actions

No evidence-supported action available.

7. Evidence Limitations

LLM unavailable and no historical evidence
was retrieved.

Fallback Used: Yes
"""

        cases = []

        for i, result in enumerate(
            retrieved_results[:5],
            start=1
        ):

            incident_id = result.get(
                "incident_id",
                "Unknown"
            )

            record = (
                result.get("document")
                or result.get("record")
                or result.get("incident")
            )

            cases.append(
                f"{i}. {incident_id}: {record}"
            )

        return f"""
1. Query Understanding

{query}

2. Relevant Historical Cases

{chr(10).join(cases)}

3. Observed Network Pattern

The retrieved incidents are the closest
historical matches returned by the retrieval system.

4. Likely Root Cause

Cannot determine reliably from the available
evidence without LLM analysis.

5. Network Impact

Refer to the recorded network metrics and
issue descriptions in the historical cases.

6. Recommended Corrective Actions

No new corrective action is generated by the
fallback system.

7. Evidence Limitations

LLM analysis was unavailable. This response
uses only retrieved historical evidence.

Fallback Used: Yes
"""
