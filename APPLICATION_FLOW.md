# Application Flow

This document describes the current application path from a user request to the
structured response. The web UI and command-line interface both use the same
`TelecomAnalysisOrchestrator`.

## Services and ports

| Component | Local address | Responsibility |
|---|---|---|
| Synapt MCP server | `http://127.0.0.1:8000/mcp` | Telecom domain context and on-demand procedure retrieval |
| Starlette API | `http://127.0.0.1:8001` | Validates requests and calls the orchestrator |
| Static web UI | `http://127.0.0.1:8790` | Collects the question and optional current network metrics |

The Synapt URL can be overridden with `SYNAPT_MCP_URL`. The browser UI sends
analysis requests to the API on port `8001`; the API permits the local UI origin
on port `8790`.

## End-to-end flow

```text
Browser UI or CLI
        |
        v
Starlette API (UI only) or direct CLI
        |
        v
TelecomAnalysisOrchestrator / LangGraph
        |
        +--> Input guardrail
        |       blocked/invalid query --> return status response
        |
        +--> Query understanding and historical incident retrieval
        |       |--> Synapt ask_synapt: advisory telecom-domain context
        |       |--> LLM query planner, or deterministic parser fallback
        |       |--> metadata/numeric filters
        |       |--> Chroma semantic search + BM25 lexical search
        |       '--> ranked incident evidence and RCA handoff
        |
        +--> Optional predictions (requires supplied model features)
        +--> Evidence-linked RCA hypotheses
        +--> Historical/current-scenario classification
        +--> Potential network impact assessment
        +--> SOP retrieval only when actions/troubleshooting are requested
        +--> Concise summaries and structured response assembly
        '--> Deterministic response contract/evidence checks when an LLM ran
```

## Request entry points

### Web UI

The page at `frontend/index.html` sends `POST /api/analyze` with:

```json
{
  "query": "Find winter incidents around Schneiderville with high latency",
  "top_k": 5,
  "network_metrics": null
}
```

`network_metrics` is optional and must be a JSON object when provided. The UI
renders `final_answer` and each structured response section.

### API

- `GET /api/health` reports API liveness and whether the orchestrator has been
  initialized.
- `POST /api/analyze` runs the complete analysis flow. Query length and `top_k`
  are validated; `top_k` must be from 1 to 50.
- `POST /api/classify` runs the existing classifier directly on a supplied
  `network_metrics` object.

### Command line

`main.py` invokes the same orchestrator without the HTTP API:

```powershell
 .\venv\Scripts\python.exe main.py --query "Find winter incidents around Schneiderville" --top-k 5
```

Add `--network-metrics <path-to-json>` to provide current metric values.

## Analysis stages

1. **Guardrail:** the query is checked before downstream analysis. Blocked or
   otherwise unusable requests stop before RCA and return a query-status
   response.
2. **Query understanding and retrieval:** the query agent asks Synapt for
   advisory telecom-domain context. Synapt is not treated as the source of
   historical matching incidents. A configured LLM converts the query and
   context into a validated retrieval plan; if that LLM is unavailable or
   fails, a deterministic query parser is used.
3. **Historical incident search:** metadata and explicit numeric constraints
   narrow candidates from the incident CSV. The query agent then combines
   Chroma semantic similarity (weight `0.6`) with BM25 lexical relevance
   (weight `0.4`), ranks the matches, and attaches the incident records. The
   CSV is `data/telecom_network_incidents_with_id.csv`; the persistent Chroma
   collection is under `rag/chroma_db`.
4. **Prediction:** if current metrics are absent, prediction models are
   skipped. If metrics are supplied, the throughput and fault models run only
   when their required feature sets are present; incomplete inputs can result
   in skipped or partial predictions. Predictions are estimates, not observed
   measurements.
5. **Root-cause analysis:** the RCA agent ranks hypotheses using retrieved
   incident evidence and any available current metrics/predictions. It does not
   re-query Synapt and does not establish a confirmed cause.
6. **Classification and impact:** classification provides dataset-relative
   triage guidance for retrieved examples and, when supplied, current metrics.
   The separate impact analyzer describes potential effects from telemetry
   and prediction outputs. Its thresholds are not SLAs, and its findings do
   not assert confirmed customer impact or causation.
7. **Troubleshooting recommendations:** the recommendation agent checks the
   user query for action/troubleshooting intent. If requested, it calls
   Synapt's `get_synapt_procedures` tool with the request, RCA hypothesis,
   metrics, and prediction context. Returned procedure actions are labelled
   with their procedure identity when available. Retrieval can report
   `success`, `no_procedures`, or `unavailable`; procedure retrieval is not
   called for ordinary incident lookups.
8. **Response assembly:** the API returns a `final_answer`, status, trace, and
   sections for predictions, RCA, historical matches, recommendations,
   classification/prioritization, and network impact. Simple incident lookups
   use a concise history summary and skip the extra summary LLM call. Other
   queries use an LLM summary when configured, with a deterministic fallback
   if it is unavailable or fails.
9. **Evaluation trace:** when query planning or response summarization invoked
   an LLM, the orchestrator runs DeepEval's deterministic response-contract
   and evidence-flow checks. The normal application path does not use an
   LLM-as-judge metric.

## Data and trust boundaries

- The incident CSV and Chroma collection provide historical incident evidence;
  they are not the troubleshooting procedure store.
- Synapt's `ask_synapt` response is advisory domain context. Retrieved local
  incident records remain the evidence used for historical matches and RCA.
- SOP/procedure recommendations come from Synapt's separate
  `get_synapt_procedures` call. The exact live procedure corpus and retrieval
  quality must be verified independently.
- `files_load_context_files/sop_knowledge.json` contains synthetic example
  SOPs. They can support a prototype/demo but should not be presented as
  approved operational instructions.
- RCA results are hypotheses; predictions are model estimates; impact
  findings are potential effects. None should be described as confirmed
  operational facts without independent validation.
- Live Synapt procedure retrieval has not been established by the local mock
  tests. Ensure Synapt is running and its procedure source is populated before
  relying on recommendations.

## Start locally

Start each component in its own terminal:

```powershell
# Terminal 1: Synapt MCP server (start using its own project instructions)

# Terminal 2: API
.\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8001

# Terminal 3: static UI
.\venv\Scripts\python.exe -m http.server 8790 --bind 127.0.0.1 --directory frontend
```

Then open <http://127.0.0.1:8790/>. Project setup and focused test commands are
also documented in [README.md](./README.md).
