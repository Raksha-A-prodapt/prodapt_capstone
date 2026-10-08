# import json
# import requests

# from config.llm_config import (
#     OPENROUTER_MODEL,
#     OPENROUTER_API_KEYS,
#     LLM_TEMPERATURE,
#     LLM_MAX_TOKENS,
#     LLM_TIMEOUT,
# )


# OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# class LLMClient:
#     """
#     Centralized LLM client.

#     All agents should call this class instead of calling
#     OpenRouter directly.

#     If one API key fails, the next API key is tried.
#     The same model is used for every API key.
#     """

#     def __init__(self):

#         if not OPENROUTER_API_KEYS:
#             raise ValueError(
#                 "No OpenRouter API keys are configured in .env"
#             )

#         self.api_keys = OPENROUTER_API_KEYS
#         self.model = OPENROUTER_MODEL
#         self.temperature = LLM_TEMPERATURE
#         self.max_tokens = LLM_MAX_TOKENS
#         self.timeout = LLM_TIMEOUT

#     # =====================================================
#     # BASIC LLM CALL
#     # =====================================================

#     def generate(
#         self,
#         system_prompt,
#         user_prompt
#     ):
#         """
#         Send a prompt to OpenRouter.

#         If the current API key fails, automatically tries
#         the next configured API key.

#         Returns:
#             str: LLM response

#         Returns None if all API keys fail.
#         """

#         for index, api_key in enumerate(
#             self.api_keys,
#             start=1
#         ):

#             print(
#                 f"\n[LLM] Attempt {index}/{len(self.api_keys)}"
#             )

#             print(
#                 f"[LLM] Model: {self.model}"
#             )

#             headers = {
#                 "Authorization": f"Bearer {api_key}",
#                 "Content-Type": "application/json",
#                 "HTTP-Referer": "http://localhost:8000",
#                 "X-Title": "Telecom Network RAG",
#             }

#             payload = {
#                 "model": self.model,

#                 "messages": [
#                     {
#                         "role": "system",
#                         "content": system_prompt,
#                     },
#                     {
#                         "role": "user",
#                         "content": user_prompt,
#                     },
#                 ],

#                 "temperature": self.temperature,
#                 "max_tokens": self.max_tokens,
#             }

#             try:

#                 response = requests.post(
#                     OPENROUTER_URL,
#                     headers=headers,
#                     json=payload,
#                     timeout=self.timeout,
#                 )

#                 response.raise_for_status()

#                 data = response.json()

#                 answer = data["choices"][0]["message"]["content"]

#                 if not answer:
#                     raise ValueError(
#                         "LLM returned an empty response."
#                     )

#                 print(
#                     f"[LLM] SUCCESS - Key {index}"
#                 )

#                 return answer

#             except requests.exceptions.RequestException as e:

#                 print(
#                     f"[LLM] FAILED - Key {index}"
#                 )

#                 print(
#                     f"[LLM] Error - {e}"
#                 )

#                 if index < len(self.api_keys):
#                     print(
#                         "[LLM] Trying next API key..."
#                     )

#             except (
#                 KeyError,
#                 IndexError,
#                 TypeError,
#                 ValueError,
#             ) as e:

#                 print(
#                     f"[LLM] INVALID RESPONSE - Key {index}"
#                 )

#                 print(
#                     f"[LLM] Error - {e}"
#                 )

#                 if index < len(self.api_keys):
#                     print(
#                         "[LLM] Trying next API key..."
#                     )

#         print(
#             "\n[LLM] ALL OPENROUTER API KEYS FAILED."
#         )

#         return None

#     # =====================================================
#     # NETWORK INCIDENT ANALYSIS
#     # =====================================================

#     def analyze_incidents(
#         self,
#         query,
#         retrieved_results,
#         sop_evidence=None,
#     ):
#         """
#         Analyze retrieved historical telecom incidents.

#         The LLM is instructed to use only the retrieved
#         historical evidence.
#         """

#         system_prompt = """
# You are a telecom network troubleshooting assistant.

# You must answer ONLY using the evidence provided
# in the retrieved historical incidents.

# Do not invent network conditions,
# root causes, incidents, risk values,
# or corrective actions.

# If the retrieved evidence is insufficient,
# explicitly say that there is insufficient evidence.

# Your task is to:

# 1. Understand the user's query.
# 2. Summarize the most relevant historical incidents.
# 3. Identify patterns across the incidents.
# 4. Identify the most likely root cause ONLY if
#    supported by the evidence.
# 5. Explain the network impact.
# 6. Suggest corrective actions ONLY when supported
#    by the retrieved incident evidence and the provided
#    synthetic SOP guidance. Do not present synthetic SOPs
#    as vendor-specific operational procedures.

# Clearly distinguish between:

# - Evidence
# - Inference
# - Recommendation
# """

#         evidence_parts = []

#         for i, result in enumerate(
#             retrieved_results,
#             start=1
#         ):
#             scores = result.get("scores", {})
#             record = (
#                 result.get("document")
#                 or result.get("record")
#                 or result.get("incident")
#             )

#             evidence_parts.append(
#                 f"""
# Historical Incident {i}

# Incident ID:
# {result.get("incident_id")}

# Hybrid Score:
# {result.get("hybrid_score", scores.get("hybrid"))}

# BM25 Score:
# {result.get("bm25_score", scores.get("bm25"))}

# Semantic Score:
# {result.get("semantic_score", scores.get("semantic"))}

# Record:
# {record}
# """
#             )

#         evidence = "\n".join(evidence_parts)
#         sop_context = json.dumps(
#             sop_evidence or [],
#             ensure_ascii=False,
#             indent=2,
#         )

#         user_prompt = f"""
# User Query:

# {query}


# Retrieved Historical Evidence:

# {evidence}

# Retrieved Synthetic SOP Guidance:

# {sop_context}


# Provide the response in this structure:

# 1. Query Understanding
# 2. Relevant Historical Cases
# 3. Observed Network Pattern
# 4. Likely Root Cause
# 5. Network Impact
# 6. Recommended Corrective Actions
# 7. Evidence Limitations
# """

#         return self.generate(
#             system_prompt,
#             user_prompt
#         )


##################
        #################################
#######################

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMClient:

    def __init__(self):

        self.api_key = os.getenv("OPENROUTER_API_KEY1")
        self.model = os.getenv("OPENROUTER_MODEL")

        self.temperature = float(
            os.getenv("LLM_TEMPERATURE", "0.2")
        )
        self.max_tokens = int(
            os.getenv("LLM_MAX_TOKENS", "1000")
        )
        self.timeout = int(
            os.getenv("LLM_TIMEOUT", "30")
        )

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY1 is missing in .env"
            )

        if not self.model:
            raise ValueError(
                "OPENROUTER_MODEL is missing in .env"
            )

    def generate(self, system_prompt, user_prompt):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Telecom Network RAG",
        }

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
        print(f"Model: {self.model}")

        try:

            response = requests.post(
                OPENROUTER_URL,
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