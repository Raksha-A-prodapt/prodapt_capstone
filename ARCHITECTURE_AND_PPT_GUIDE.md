# Telecom Network Operations Assistant

## Purpose

This document is a current architecture brief for generating project diagrams
and a presentation. It describes the implemented prototype as it exists now.
Do not show predictions, RCA hypotheses, or recommendations as confirmed network
facts.

## Project summary

The system is a telecom network decision-support application. A user can ask a
natural-language network question, provide optional current telemetry, or enter
telemetry directly in the ML dashboard. The application retrieves similar
historical incidents, runs two independent ML models when valid telemetry is
available, classifies network performance, performs evidence-linked RCA, and
returns troubleshooting guidance when requested.

The system is a prototype. It is not connected to live telecom network
telemetry, and live Synapt procedure retrieval has not been validated. Local
synthetic SOP data is available for demonstration.

## Main services

| Component | Location | Responsibility |
|---|---|---|
| React frontend | `frontend/src` | Login, AI assistant, ML dashboard, scenario comparison, evaluation views |
| Starlette API | `api.py` | HTTP validation and orchestration entry points |
| Orchestrator | `agents/orchestrator.py` | Coordinates the multi-agent LangGraph workflow |
| Query/RAG agent | `agents/query_synapt_agent.py` | Guardrails, query parsing, filtering, hybrid retrieval |
| Prediction agent | `agents/prediction_agent.py` | Runs both ML models from one shared telemetry object |
| RCA agent | `agents/rca_agent.py` | Produces ranked evidence-linked hypotheses |
| Impact analyzer | `agents/impact_analysis.py` | Estimates possible network/service impact |
| Classification agent | `agents/incident_classifier.py` | Incident priority and current-scenario classification |
| Recommendation agent | `agents/recommendation_agent.py` | Retrieves troubleshooting/SOP recommendations when requested |
| Input guardrail | `guardrail/input_gaurdrail.py` | Validates and blocks unsafe or unusable natural-language queries |
| Evaluation modules | `evaluations` | DeepEval, contract checks, feedback evaluation, model evaluation |

## Implemented end-to-end flow

```text
User
  |
  +------------------------------+
  |                              |
  v                              v
AI Assistant page          ML Prediction page
natural-language query     direct telemetry form
  |                              |
  |                              +--> client input validation
  |                              +--> POST /api/predict
  |                              +--> Prediction Agent
  |                              |       |--> Network performance model
  |                              |       |--> Fault risk model
  |                              |       |--> KPI classification
  |                              |       '--> score and model agreement
  |                              '--> KPI result cards
  |
  +--> POST /api/analyze
          |
          v
      Starlette API
          |
          v
      TelecomAnalysisOrchestrator / LangGraph
          |
          +--> InputGuardrail
          |       |--> blocked/invalid: return safe status
          |       '--> allowed: continue
          |
          +--> Query Agent
          |       +--> deterministic query parsing or LLM planning
          |       +--> metadata and numeric filters
          |       +--> Chroma semantic search
          |       +--> BM25 keyword search
          |       '--> ranked historical incidents
          |
          +--> Prediction Agent (only with complete telemetry)
          |       +--> network_performance_model.joblib
          |       |       '--> seven KPI predictions
          |       |       '--> Good/Moderate/Poor/Critical KPI classes
          |       |       '--> Low/Medium/High/Critical network status
          |       +--> fault_tolerance_model.joblib
          |       |       '--> fault occurrence rate and risk tier
          |       '--> model agreement indicator
          |
          +--> Incident Classification / Prioritization
          +--> RCA Agent
          +--> Impact Analysis
          +--> Recommendation Agent
          |       '--> Synapt procedures when action/troubleshooting is requested
          |
          '--> Structured response assembly
                  +--> final answer
                  +--> historical evidence
                  +--> prediction section
                  +--> RCA section
                  +--> impact section
                  +--> recommendation section
                  '--> trace and evaluation metadata
```

## Retrieval flow

The historical incident dataset is:

```text
data/telecom_network_incidents_with_id.csv
```

The query agent uses metadata and numeric filters, then combines:

- Chroma semantic similarity: approximately 60%
- BM25 lexical similarity: approximately 40%

The result is a ranked list of similar incidents used by RCA and incident
classification. Historical incidents are not the same source as SOP procedures.

## ML flow

Both models receive the same current telemetry input through the Prediction
Agent. They remain independent models.

### Network performance model

Artifact:

```text
ml_model/models/network_performance_model.joblib
```

It produces these seven KPI predictions:

1. Throughput (Mbps)
2. Latency (ms)
3. Packet Loss Rate (%)
4. Call Drop Rate (%)
5. Handover Success Rate (%)
6. Jitter (ms)
7. Connection Setup Success Rate (%)

The predictions are passed to `classification.py`, which applies configurable,
illustrative KPI-specific thresholds and returns:

- Good, Moderate, Poor, or Critical KPI classifications
- Low, Medium, High, or Critical overall network status
- Responsible KPI names and reasons
- Optional rule-based performance score from 0 to 100

The thresholds are prototype values. They are not 3GPP requirements or
operator SLAs.

### Fault risk model

Artifact:

```text
ml_model/models/fault_tolerance_model.joblib
```

It predicts Fault Occurrence Rate (%) and maps it to a separate risk tier:

```text
LOW -> MEDIUM -> HIGH -> CRITICAL
```

Fault risk must not be confused with the overall network performance status.

### Model Agreement card

The frontend combines the two model outputs using transparent rules. It does
not claim statistical model agreement. It explains whether the outputs indicate:

- Healthy agreement
- Moderate degradation
- Performance warning
- Fault warning
- High-risk agreement
- Critical agreement
- Mixed result
- Incomplete or unavailable result

## Scenario Comparison page

The Scenario Comparison page sends Scenario A and Scenario B through the same
Prediction Agent. It displays both results side by side and calculates the
change in the rule-based performance score.

```text
Scenario A: current network telemetry
Scenario B: what-if network telemetry
          |
          +--> same validation rules
          +--> same two ML models
          +--> same KPI classification
          '--> score and status comparison
```

This is a what-if decision-support feature. It does not represent a time trend
because the dataset does not contain time-series timestamps.

## Guardrails and reliability

Natural-language queries use `InputGuardrail` before retrieval and downstream
agents. The ML forms and prediction agent validate:

- Required feature presence
- Numeric and finite values
- Percentage values from 0 to 100
- Non-negative count, user, data-usage, and duration fields
- Model feature compatibility
- Missing or unavailable model artifacts
- Missing KPI predictions
- Non-finite model outputs

Invalid values are rejected or marked incomplete. They are not silently changed
to zero or classified as Good.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API liveness |
| POST | `/api/analyze` | Full query, retrieval, agent, RCA, impact, and recommendation flow |
| POST | `/api/classify` | Direct incident/current-scenario classification |
| POST | `/api/predict` | Direct execution of both ML models |
| POST | `/api/feedback` | Store helpful/not-helpful feedback for later evaluation |

## Frontend pages

- **Home Dashboard:** project overview and entry points
- **AI Assistant:** natural-language query, retrieved incidents, predictions,
  RCA, impact, recommendations, and model agreement
- **Network Performance & Fault Prediction:** direct telemetry form, both model
  results, KPI cards, classification, score, and model agreement
- **Scenario Comparison:** two telemetry scenarios and score/status comparison
- **Evaluations:** model and agent evaluation summaries

## Evaluation and limitations

Current evaluation includes focused tests, prediction-agent contract checks,
retrieval/RCA/final-answer evaluation, and feedback-based deferred evaluation.
The project does not yet prove live Synapt procedure quality, production model
accuracy, real-time telemetry behavior, or automatic model retraining.

Important trust labels for diagrams and slides:

- ML outputs are predictions, not observations.
- RCA output is a ranked hypothesis, not a confirmed cause.
- Impact output describes potential effects, not confirmed customer impact.
- Recommendations require validation against approved operational procedures.
- Local SOP examples are synthetic/demo data until a live procedure source is
  connected and validated.

## Recommended architecture diagrams

Generate either one complete diagram or two cleaner diagrams.

### Option A: one complete diagram

Show three horizontal layers:

1. **Presentation:** React pages and user inputs
2. **Application:** API, orchestrator, agents, guardrails, classification,
   prediction, RCA, impact, recommendation
3. **Data and services:** incident CSV, Chroma, model artifacts, Synapt MCP,
   evaluation and feedback storage

Use arrows for normal data flow and dashed arrows for optional branches such as
telemetry, Synapt procedures, feedback, and DeepEval.

### Option B: two diagrams

**Diagram 1 — Operational request flow:**

```text
User -> Frontend -> API -> Guardrail -> Query Agent -> Retrieval ->
Prediction/RCA/Impact/Recommendation -> Response cards
```

**Diagram 2 — ML and evaluation flow:**

```text
Shared telemetry -> Prediction Agent -> Performance model -> seven KPIs ->
classification/score

Shared telemetry -> Prediction Agent -> Fault model -> fault risk

Both outputs -> Model Agreement -> UI

Responses/feedback -> evaluation reports -> improvement backlog
```

Use different colors for user interface, agents, ML/rules, data stores, and
external services. Label optional paths clearly.

## Presentation outline

Suggested 10-minute presentation:

1. **Problem and motivation** — telecom incidents require fast evidence-based
   triage and troubleshooting.
2. **Objective** — combine RAG, multi-agent analysis, classification, RCA,
   recommendations, and network prediction.
3. **Architecture** — show the operational request-flow diagram.
4. **Data and retrieval** — incident CSV, Chroma semantic search, BM25 search,
   filters, and ranking.
5. **Multi-agent workflow** — Query, Prediction, Classification, RCA, Impact,
   and Recommendation agents.
6. **ML prediction flow** — two independent models using shared telemetry.
7. **KPI classification and model agreement** — seven KPI cards, status, score,
   fault risk, and agreement card.
8. **Live demo** — ask a network question, run a telemetry prediction, then
   compare a current and improved scenario.
9. **Evaluation and guardrails** — tests, DeepEval, validation, uncertainty,
   and feedback capture.
10. **Limitations and next steps** — live Synapt validation, real telemetry,
    production monitoring, and continuous improvement.

## Suggested demo sequence

1. Open AI Assistant.
2. Ask for incidents around a city/season with degraded performance.
3. Show filtered historical incidents and ranked evidence.
4. Provide complete telemetry and show both model outputs.
5. Point out KPI classifications, fault risk, and Model Agreement.
6. Open Scenario Comparison.
7. Run a current scenario and an improved what-if scenario.
8. Show the score/status difference.

## Local run commands

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8001
python -m http.server 8790 --bind 127.0.0.1 --directory frontend
```

Open:

```text
http://127.0.0.1:8790
```

The API is normally available at `http://127.0.0.1:8001`.
