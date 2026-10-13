# Project Navigation

This file is a quick map of the telecom analysis project: what starts the system,
which agents call which components, and where the UI/evaluation code lives.

## Safe-to-delete generated items

These are rebuildable caches or build output and can be deleted when no process
is using them:

- `__pycache__/` folders and `*.pyc` files — Python bytecode caches.
- `.pytest_cache/` — pytest cache.
- `frontend/pytest-cache-files-*/` — temporary pytest files created under the frontend folder.
- `frontend/dist/` — Vite production output; recreate with `npm.cmd run build`.
- `frontend/node_modules/` — npm dependencies; recreate with `npm install`.
- `.deepeval/` and `frontend/.deepeval/` — DeepEval run cache/state; evaluation reports are separate and should be kept.

Do not delete these without confirming first: `.env`, `data/`, `feedback/feedback.sqlite3`,
`rag/chroma_db/`, evaluation reports, model files, `agents/query_synapt_agent.py.backup`,
`frontend/legacy_index.html`, or any file under `files_load_context_files/`.

## How the application starts

```text
frontend/src/pages/AIAssistant.jsx
        -> frontend/src/services/api.js
        -> api.py (/api/analyze)
        -> agents/orchestrator.py
        -> agents/query_synapt_agent.py
        -> retrieval + optional Synapt context
        -> prediction / RCA / classification / impact / SOP agents
        -> structured response -> frontend/src/components/AnalysisResults.jsx
```

Services:

- `synapt_mcp_bundle/synapt_mcp_server.py` — local Synapt MCP bridge, normally port 8000.
- `api.py` — Starlette API, normally port 8001.
- `frontend/src/` — React/Vite user interface.
- `llm/llm_client.py` — active LLM provider client; root `.env` selects AICredits.

## Root files

- `api.py` — HTTP endpoints, request validation, orchestrator lifecycle, and feedback routes.
- `main.py` — command-line entry point for running an analysis without the web API.
- `classification.py` — shared network-performance classification helpers.
- `requirements.txt` — main Python dependencies.
- `requirements-ragas.txt` — optional RAGAS evaluation dependencies.
- `.env` — local secrets and runtime configuration; never commit or share it.
- `README.md` — setup and run instructions.
- `APPLICATION_FLOW.md` — longer architecture and request-flow explanation.
- `ARCHITECTURE_AND_PPT_GUIDE.md` — presentation and architecture notes.
- `cmd1.txt`, `command_notes.txt`, `dataset_path.txt` — local run/path notes.
- `sample_user_queries.txt`, `prompt.txt`, `question.txt`, `qery1fix.txt` — query and prompt examples.

## Agents

- `agents/orchestrator.py` — LangGraph coordinator; calls every analysis stage and assembles the API response.
- `agents/query_synapt_agent.py` — guardrail, Synapt domain context, query planning, and incident retrieval.
- `agents/query_agent.py` — older/local query-retrieval implementation retained for compatibility.
- `agents/prediction_agent.py` — runs throughput and fault-risk models when live telemetry is supplied.
- `agents/historical_evaluation.py` — calculates metadata-filtered historical averages when requested.
- `agents/rca_agent.py` — ranks evidence-linked root-cause hypotheses.
- `agents/incident_classifier.py` — classifies historical incidents and current telemetry scenarios.
- `agents/impact_analysis.py` — describes potential service effects from telemetry or historical baselines.
- `agents/recommendation_agent.py` — detects action intent and retrieves Synapt SOP procedures.
- `agents/11query.py` — legacy/query experiment module; not part of the primary API flow.
- `agents/query_synapt_agent.py.backup` — backup copy; keep until the active implementation is confirmed stable.

## Configuration and models

- `config/config.py` — general project configuration.
- `config/llm_config.py` — LLM configuration helpers.
- `config/chroma_config.py` — Chroma/vector-store configuration.
- `config/metric_schema.py` — metric aliases and canonical field names.
- `config/metric_thresholds.py` — dataset-relative classification thresholds.
- `config/prediction_config.py` — prediction feature/model configuration.
- `llm/llm_client.py` — AICredits/OpenRouter-compatible chat client, with AICredits active by default.
- `llm/llm_test.py` — LLM connectivity smoke test.
- `llm/local_llm_test.py` — local LLM experiment.
- `llm/test_claude_api.py` — legacy Claude connectivity experiment.
- `ml_model/net_performance.py` — network-performance prediction model.
- `ml_model/net_throughput_prediction.py` — throughput prediction implementation.
- `ml_model/fault_risk.py` — fault-risk prediction implementation.
- `ml_model/fault_tol_v1.py` — fault-tolerance model variant.
- `ml_model/fault_tolerance_model.py` — fault-tolerance model wrapper.
- `ml_model/ml_eval.py` — model evaluation utilities.
- `ml_model/p1.py` — model experiment/utility; verify references before deleting.
- `ml_model/model_notes.txt` — model notes.

## Retrieval and data

- `data/telecom_network_incidents_with_id.csv` — historical incident source used for retrieval and averages.
- `data/5g_netops.csv` — additional network dataset.
- `data/user_feedback.json` — feedback data file.
- `files_load_context_files/domain_knowledge.json` — telecom domain context.
- `files_load_context_files/incident_knowledge.json` — incident knowledge context.
- `files_load_context_files/sop_knowledge.json` — SOP/procedure knowledge context.
- `files_load_context_files/schema.json` and `schema.jsonl` — data schemas.
- `files_load_context_files/doc.txt` — loaded context/document notes.
- `rag/embedding_model.py` — embedding model setup.
- `rag/index.py` — vector index/search helpers.
- `rag/chromadb_setup.py` — Chroma index creation/setup.
- `rag/batch_test.py` — retrieval batch test.
- `rag/test_embed.py` — embedding smoke test.
- `rag/telecom_rag_indexing_summary.txt` — indexing notes.
- `retieval_sematics/create_json.py` — retrieval-document preparation utility.

## Synapt MCP bundle

- `synapt_mcp_bundle/synapt_mcp_server.py` — local MCP server exposing Synapt tools.
- `synapt_mcp_bundle/query_agent/agent.py` — Synapt query-agent implementation.
- `synapt_mcp_bundle/query_agent/mcp_client.py` — MCP client connection/tool calls.
- `synapt_mcp_bundle/query_agent/config.py` — Synapt bundle configuration.
- `synapt_mcp_bundle/query_agent/s2s.py` — Synapt service-to-service experiment/helper.
- `synapt_mcp_bundle/README.md` — Synapt bundle setup notes.
- `synapt_mcp_bundle/requirements.txt` — Synapt bundle dependencies.
- `synapt_layer/synapt_mcp_client.py` — alternate Synapt MCP client layer.

## Evaluations

- `evaluations/synapt_agent_deepeval.py` — DeepEval tests for Synapt retrieval/domain context.
- `evaluations/orchestrator_deepeval.py` — DeepEval metrics for the complete orchestrator response.
- `evaluations/run_orchestrator_deepeval.py` — orchestrator evaluation runner.
- `evaluations/deepeval_agent_suite.py` — multi-agent evaluation suite.
- `evaluations/query_agent_deepeval.py` — query-agent evaluation.
- `evaluations/prediction_agent_deepeval.py` — prediction-agent evaluation.
- `evaluations/ragas_synapt_evaluation.py` — RAGAS evaluation using the Synapt report context.
- `evaluations/aicredits_judge.py` — AICredits LLM-as-judge helper.
- `evaluations/reports/` — saved DeepEval/RAGAS reports used for review and the evaluation page.
- `frontend/src/pages/Evaluations.jsx` — evaluation dashboard and displayed evaluation metrics.

## Frontend

- `frontend/src/App.jsx` — frontend application shell and routing.
- `frontend/src/main.jsx` — React entry point.
- `frontend/src/pages/AIAssistant.jsx` — query form, telemetry inputs, and API response screen.
- `frontend/src/pages/HomeDashboard.jsx` — project overview/dashboard.
- `frontend/src/pages/PredictionDashboard.jsx` — live prediction input and results page.
- `frontend/src/pages/ScenarioComparison.jsx` — scenario comparison view.
- `frontend/src/pages/Evaluations.jsx` — evaluation metrics page.
- `frontend/src/components/AnalysisResults.jsx` — user-friendly answer, tags, sections, metrics, RCA, impact, and recommendation display.
- `frontend/src/components/AgentFlow.jsx` — visual execution flow and agent trace.
- `frontend/src/components/StatusBadge.jsx` — reusable status/tag badge.
- `frontend/src/components/ModelAgreementCard.jsx` — prediction model agreement display.
- `frontend/src/components/AppErrorBoundary.jsx` — frontend error boundary.
- `frontend/src/services/api.js` — browser-to-API request functions.
- `frontend/src/styles/global.css` — component/layout styling.
- `frontend/src/styles/theme.css` — color and theme variables.
- `frontend/src/utils/modelAgreement.js` — model agreement calculations.
- `frontend/src/utils/predictionValidation.js` — telemetry/prediction input validation.
- `frontend/package.json` and `package-lock.json` — frontend scripts and locked npm dependencies.
- `frontend/index.html` — Vite/static frontend entry page.
- `frontend/streamlit_app.py` — legacy Streamlit frontend path; not used by the React API flow.

## Tests

- `tests/test_api.py` — API endpoint tests.
- `tests/test_orchestrator.py` — orchestration and response-contract tests.
- `tests/test_query_synapt_retrieval.py` — Synapt/query retrieval tests.
- `tests/test_prediction_agent.py` — prediction tests.
- `tests/test_impact_analysis.py` — network-impact tests.
- `tests/test_classification.py` — classification tests.
- `tests/test_rca_agent.py` — RCA tests.
- `tests/test_llm_client.py` — LLM-client tests.
- `tests/test_aicredits_judge.py` — AICredits judge tests.

## Recommended run order

1. Start `synapt_mcp_bundle/synapt_mcp_server.py` on port 8000.
2. Start `api.py`/Uvicorn on port 8001.
3. Start the frontend with `npm run dev`, or serve the built/static frontend.
4. Open the AI Assistant and submit a query; add telemetry fields for live predictions.
5. Use `evaluations/` scripts only when evaluating, not for normal user queries.
