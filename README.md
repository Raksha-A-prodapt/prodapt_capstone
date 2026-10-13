# Telecom Network Operations Assistant

## About the application

This project is a telecom network analysis assistant for investigating network incidents and operational performance. It combines historical incident retrieval, Synapt telecom-domain knowledge, optional live network prediction models, RCA hypotheses, impact analysis, incident classification, and Synapt SOP retrieval.

The application supports two analysis modes:

- **Live analysis:** current telemetry is supplied and the throughput/fault-risk prediction models can run.
- **Historical analysis:** no telemetry is supplied; filtered historical averages are shown as a clearly labelled baseline, not as a live prediction.

The result is shown as an answer summary, evidence, RCA, network impact, historical evaluation, prediction or baseline status, and recommended actions.

## Project setup

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- Synapt MCP credentials
- An AICredits API key for query planning and response summarization

### Install dependencies

From the project root:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install the Synapt MCP bundle dependencies:

```powershell
cd synapt_mcp_bundle
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ..
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

### Configure credentials

Create or update the root `.env` file. Do not commit or share this file.

Important root settings:

```env
LLM_PROVIDER=aicredits
ai_credits_api_key=<your-aicredits-key>
SYNAPT_MCP_URL=http://127.0.0.1:8000/mcp
```

The root environment may also contain `LLM_TIMEOUT`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`, and `DEEPEVAL_LIVE_ENABLED`.

Configure `synapt_mcp_bundle/.env` with the registered Synapt identity. Use either client credentials or a temporary session token:

```env
SYNAPT_PROVIDER_ID=<provider-id>
SYNAPT_AGENT_CLIENT_ID=<client-id>
SYNAPT_AGENT_CLIENT_SECRET=<client-secret>
# Or use: SYNAPT_AGENT_TOKEN=<temporary-session-token>
SYNAPT_VERIFY_SSL=true
```

Never place real keys in source files, README files, screenshots, or commit history. OpenRouter and Claude variables are legacy compatibility settings; the active project provider is AICredits.

## Run the application: three servers

Start each command in a separate terminal and keep all three terminals open.

### 1. Synapt MCP server — port 8000

```powershell
cd synapt_mcp_bundle
.\.venv\Scripts\python.exe synapt_mcp_server.py
```

Endpoint: `http://127.0.0.1:8000/mcp`

### 2. Backend API — port 8001

From the project root:

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --port 8001
```

Useful endpoints:

- `GET http://127.0.0.1:8001/api/health` — backend health check.
- `POST http://127.0.0.1:8001/api/analyze` — run the complete analysis flow.
- `POST http://127.0.0.1:8001/api/classify` — classify supplied metrics.

### 3. React frontend — port 8790

```powershell
cd frontend
npm run dev
```

Open <http://127.0.0.1:8790> in the browser. The frontend calls the backend on port 8001, and the backend calls the local Synapt MCP server on port 8000.

## Sample usage

### Example query

Use this short query in the AI Assistant:

> Calculate historical averages for high latency and packet loss, assess network impact, and suggest troubleshooting actions from Synapt SOPs.

This requests historical evaluation and SOP retrieval. It does not require live telemetry.

### Representative result and recommendations

The application returns evidence-grounded results such as:

- filtered historical averages for latency, packet loss, throughput, call-drop rate, handover success, and fault occurrence when available;
- potential impact based on the historical baseline, clearly labelled as not current-network observation;
- an RCA hypothesis based on retrieved incidents, not a confirmed physical cause;
- Synapt SOP actions such as comparing the condition with historical baselines, checking throughput/user load/data usage, reviewing active and critical alarms, and escalating persistent degradation for engineering investigation.

For live prediction, enter current telemetry in the UI and use:

> Analyze the current cell performance and predict throughput and fault risk.

The prediction models run only when their required live metric fields are provided. Without telemetry, the UI shows a historical baseline or explains why live prediction was not applicable.

## Sample test queries

1. **Winter performance and resolution**

   > What are the reasons for network congestion in Winter, what is the network performance and impact, and how can it be resolved?

2. **Historical baseline and impact**

   > Calculate historical averages for high latency and packet loss, then assess network impact.

3. **SOP retrieval and recommendations**

   > Suggest troubleshooting actions for high latency and packet loss using the relevant Synapt SOPs.

4. **Historical comparison and RCA**

   > Compare the five most relevant historical incidents for packet loss and explain the likely causes.

5. **Winter congestion with SOP actions**

   > Assess Winter network performance, identify likely congestion factors, and suggest recommended actions.

6. **Live prediction and recommendations**

   > Analyze the current cell performance, predict throughput and fault risk, and recommend next actions.

   For query 6, also enter current telemetry such as latency, packet loss, throughput, call-drop rate, handover success, and MTTR in the live metrics fields.

## Main processing flow

```text
React frontend
  -> POST /api/analyze
  -> TelecomAnalysisOrchestrator
  -> query planning + Synapt domain context
  -> historical incident retrieval
  -> optional live prediction or historical baseline
  -> RCA and incident classification
  -> network impact assessment
  -> Synapt SOP retrieval when recommendations are requested
  -> structured answer and frontend cards
```

The main implementation files are mapped in [PROJECT_NAVIGATION.md](./PROJECT_NAVIGATION.md). The detailed flow and trust boundaries are documented in [APPLICATION_FLOW.md](./APPLICATION_FLOW.md).

The technical stack is listed in [docs/TECHNICAL_STACK.md](./docs/TECHNICAL_STACK.md). The ready-to-use Claude prompt for the full application-design document is in [docs/CLAUDE_APPLICATION_DESIGN_PROMPT.md](./docs/CLAUDE_APPLICATION_DESIGN_PROMPT.md).

## Evaluation

Evaluation scripts are under `evaluations/`:

- `evaluations/synapt_agent_deepeval.py` — Synapt retrieval/domain evaluation.
- `evaluations/orchestrator_deepeval.py` — complete response evaluation.
- `evaluations/ragas_synapt_evaluation.py` — RAGAS evaluation.
- `evaluations/reports/` — saved evaluation reports displayed by the evaluation page.

Generated documentation PDFs:

- [API Documentation](./docs/api_documentation.pdf)
- [Evaluation Report](./docs/evaluation_report.pdf)
- [Dataset Details](./docs/dataset_details.pdf)

The optional RAGAS dependencies are listed in `requirements-ragas.txt`.

## Security and operational notes

- Keep all AICredits and Synapt credentials private.
- Keep the MCP and API services bound to localhost for local development.
- Do not treat historical averages as live telemetry or model forecasts.
- RCA results are evidence-based hypotheses, not confirmed root causes.
- Impact findings are potential service effects, not confirmed customer impact or SLA determinations.
