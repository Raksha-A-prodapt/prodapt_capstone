# Technical Stack

## Application and runtime

- **Language:** Python 3.10+ for the backend, agents, retrieval, prediction, and evaluation tooling.
- **Frontend:** React 18.3 with Vite 5.4, JavaScript/JSX, and CSS.
- **Backend:** Starlette ASGI application served with Uvicorn.
- **Validation:** Pydantic 2.x request models.
- **Orchestration:** LangGraph state graph in `agents/orchestrator.py`.
- **Services:** local Synapt MCP bridge on port 8000, backend API on port 8001, React frontend on port 8790.

## LLM and credentials

- **Active LLM provider:** AICredits OpenAI-compatible chat API.
- **Active model:** configured through `DEEPEVAL_MODEL`/AICredits model settings; current evaluation uses `google/gemini-3.1-flash-lite`.
- **LLM client:** `llm/llm_client.py` with provider selection, timeout, temperature, token limit, and retry settings.
- **LLM uses:** query planning, response summarization, and LLM-as-judge evaluation.
- **Credentials:** root `.env` contains the AICredits key; `synapt_mcp_bundle/.env` contains Synapt provider and agent credentials.
- **Legacy compatibility:** OpenRouter and Claude settings remain in the environment/code but are not the active provider.

## Telecom agents

- **Query/Synapt agent:** guardrail, Synapt telecom context, query plan, metadata filtering, semantic/lexical retrieval, and RCA handoff.
- **Historical evaluation agent:** descriptive averages over metadata-filtered records when a query requests averages, performance, trends, assessment, or impact.
- **Prediction agent:** throughput and fault-occurrence prediction when required current telemetry is supplied.
- **RCA agent:** ranks evidence-linked hypotheses and preserves uncertainty.
- **Incident classifier:** dataset-relative priority/risk classification.
- **Impact analyzer:** potential network/service effects from telemetry or historical averages.
- **Recommendation agent:** calls Synapt procedure retrieval when the query requests recommendations, troubleshooting, SOPs, or resolution steps.

## Retrieval and embeddings

- **Embedding library:** `sentence-transformers`.
- **Active embedding model:** `BAAI/bge-small-en-v1.5`, loaded locally.
- **Vector database:** ChromaDB with a persistent local collection.
- **Lexical retrieval:** `rank-bm25`.
- **Hybrid ranking:** semantic similarity and BM25 lexical relevance are combined for incident retrieval.
- **Canonical metrics:** `config/metric_schema.py` maps human-readable CSV headers and aliases to stable snake_case fields.
- **Source of truth:** `data/telecom_network_incidents_with_id.csv` for historical observations.

## Machine learning

- **ML libraries:** scikit-learn, NumPy, pandas, and joblib.
- **Performance target:** `Throughput (Mbps)`.
- **Fault target:** `Fault Occurrence Rate (%)`.
- **Model inputs:** performance, operational, load, signal, environmental, security, geography, season, and weather features as configured in `config/prediction_config.py`.
- **Prediction rule:** models are not run without the required live feature set; historical averages are labelled as baselines rather than predictions.

## Synapt integration

- **Protocol/client:** MCP with the Python `mcp` package and `httpx`/HTTP requests.
- **Local endpoint:** `http://127.0.0.1:8000/mcp`.
- **Synapt capabilities:** domain-context retrieval and on-demand SOP/procedure retrieval.
- **Authentication:** registered client ID/client secret exchange or temporary session token.

## Evaluation and observability

- **DeepEval:** answer relevancy, faithfulness, contextual retrieval metrics, RCA quality, and agent-specific checks.
- **RAGAS:** faithfulness, context precision, and context relevance for the Synapt/RAG path.
- **Judge:** AICredits OpenAI-compatible endpoint with Gemini evaluation model.
- **Reports:** JSON reports in `evaluations/reports/`, displayed by `frontend/src/pages/Evaluations.jsx`.
- **Feedback:** Starlette feedback endpoint with SQLite persistence in `feedback/feedback.sqlite3`.

## Data and documentation

- **Primary dataset:** 100,000 telecom network observations and 27 columns according to the project schema/context.
- **Context files:** domain, incident, SOP, and schema files in `files_load_context_files/`.
- **Documentation:** `README.md`, `APPLICATION_FLOW.md`, `ARCHITECTURE_AND_PPT_GUIDE.md`, and `PROJECT_NAVIGATION.md`.

## Main dependencies

`pandas`, `numpy`, `scikit-learn`, `joblib`, `pydantic`, `sentence-transformers`, `chromadb`, `rank-bm25`, `requests`, `python-dotenv`, `httpx`, `mcp`, `deepeval`, `ragas`, `langchain-openai`, `react`, `react-dom`, and `vite`.
