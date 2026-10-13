# Claude Prompt: Application Design Document

Copy the prompt below into Claude after attaching the existing architecture diagram and the project files/documents.

```text
You are a senior software architect and technical-documentation writer.

Create a polished Application Design Document for the Telecom Network
Operations Assistant project. The existing architecture diagram is attached;
use it as the authoritative visual and place it in the architecture section.
Do not redraw, replace, or invent a different architecture diagram.

The document must describe the implemented system, not an imagined future
system. Where a capability is optional, legacy, synthetic, experimental, or
not production-ready, label it clearly.

Include these sections:

1. Title page, document purpose, scope, audience, and revision/date.
2. Executive summary explaining the telecom incident-analysis problem and the
   solution provided by the application.
3. Functional requirements: historical incident search, Synapt domain context,
   hybrid retrieval, RCA hypotheses, incident classification, network impact,
   historical KPI averages, live prediction, SOP retrieval, recommendations,
   feedback, and evaluation.
4. Non-functional requirements: latency, reliability, explainability,
   security, privacy, maintainability, local-service boundaries, and graceful
   fallback behavior.
5. Complete technical stack. Include Python, Starlette, Uvicorn, Pydantic,
   LangGraph, React, Vite, ChromaDB, sentence-transformers,
   BAAI/bge-small-en-v1.5, BM25, pandas, NumPy, scikit-learn, joblib, MCP,
   Synapt, AICredits Gemini, DeepEval, RAGAS, SQLite feedback storage, and
   the three local service ports: MCP 8000, API 8001, frontend 8790.
6. Architecture section containing the attached architecture diagram, followed
   by a written explanation of frontend, API, orchestrator, retrieval, Synapt,
   prediction, RCA, impact, recommendation, and evaluation boundaries.
7. End-to-end request sequence from the React query form to POST /api/analyze,
   query planning, Synapt context, retrieval, optional live prediction or
   historical baseline, RCA, classification, impact, SOP retrieval, response
   summary, and frontend rendering.
8. Agent responsibility matrix showing which agent calls which tool/module and
   what each agent returns.
9. Retrieval and embedding design: source CSV, schema normalization, local
   BGE embeddings, ChromaDB, BM25, hybrid ranking, filtering, top-k evidence,
   and limitations of synthetic historical data.
10. Prediction design: required live telemetry, throughput target, fault-risk
    target, feature groups, missing-feature behavior, and the rule that
    historical averages must never be presented as live predictions.
11. Synapt MCP design: local bridge, domain context retrieval, SOP retrieval,
    credential flow, timeout/fallback behavior, and port 8000 boundary.
12. API design with request/response examples for /api/health,
    /api/analyze, /api/predict, /api/classify, and /api/feedback.
13. UI design explaining the answer summary, tags, historical evaluation,
    baseline/prediction cards, RCA, impact, recommended actions, agent flow,
    and evaluation page.
14. Data design: dataset fields grouped by context, performance, operations,
    load, signal, environment, security, geography, and fault target.
15. Security design: .env secrets, AICredits and Synapt credential handling,
    localhost binding, TLS verification, CORS, input validation, and why
    credentials must not be committed.
16. Evaluation design: DeepEval and RAGAS objectives, LLM-as-judge provider,
    metrics, thresholds, saved reports, current results, limitations, and
    interpretation of moderate Context Precision.
17. Failure handling and fallback matrix covering unavailable LLM, unavailable
    Synapt, missing telemetry, missing historical evidence, SOP retrieval
    failure, prediction model failure, and judge timeouts.
18. Deployment/runbook section for starting the three local services and
    checking their health.
19. Risks, limitations, and future improvements.
20. Appendix with repository file map, environment-variable names (never show
    secret values), sample queries, and glossary.

Use clear headings, tables, numbered flows, and concise technical prose. Keep
the document suitable for a capstone final submission and a technical review.
Distinguish evidence from hypotheses. State that RCA hypotheses are not
confirmed causes, impact findings are not confirmed customer outcomes, and
historical baselines are not live telemetry or forecasts.

Use these project facts as constraints:

- Active LLM provider: AICredits; current evaluation model:
  google/gemini-3.1-flash-lite.
- Active local embedding: BAAI/bge-small-en-v1.5.
- Primary historical source: data/telecom_network_incidents_with_id.csv.
- Project schema/context describes 100,000 rows and 27 columns.
- Synapt MCP is local on port 8000, API on 8001, and React frontend on 8790.
- Current reports are in evaluations/reports/ and the evaluation page reads
  saved report data.
- Do not expose real .env values, API keys, tokens, client secrets, or private
  endpoints in the document.

Return the final document in a professional format with an executive summary,
table of contents, numbered sections, figure caption for the attached
architecture diagram, and a references/source-files section.
```
