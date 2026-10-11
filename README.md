# Telecom Network Operations Assistant

See [APPLICATION_FLOW.md](./APPLICATION_FLOW.md) for the full request flow,
agent responsibilities, service ports, and data/trust boundaries.

## LLM provider

The active `LLMClient` uses Anthropic's Claude Messages API. It reads
`claude_api_key` from the project `.env` file and defaults to
`claude-haiku-5-5`; optionally set `CLAUDE_MODEL` to select another model
available to your Anthropic account. Keep API keys private and out of source
control.

## Run Synapt, the API, and the web interface

Install the project dependencies in the active virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Keep the Synapt MCP server on port `8000`. In a separate terminal, start the
project API on port `8001`:

```powershell
.\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8001
```

In another terminal, serve the frontend on port `8790`:

```powershell
.\venv\Scripts\python.exe -m http.server 8790 --bind 127.0.0.1 --directory frontend
```

Open <http://127.0.0.1:8790/> for the browser interface. The API is available
at <http://127.0.0.1:8001/> and its interactive endpoints are:

- `GET /api/health` — API liveness.
- `POST /api/analyze` — run the existing retrieval/orchestration flow.
- `POST /api/classify` — classify and prioritize a current metric scenario.

The frontend is configured to call the API at `http://127.0.0.1:8001`.
The API allows browser requests from the local frontend origin on port `8790`.
Synapt's MCP URL remains `http://127.0.0.1:8000/mcp` by default; set
`SYNAPT_MCP_URL` if its endpoint differs.

Example analysis request:

```json
{
  "query": "Find winter incidents around Schneiderville where performance degraded badly",
  "top_k": 5
}
```

Current metrics can optionally be added as a JSON object using the dataset's
feature names, for example `"Latency (ms)"` or `"Packet Loss Rate (%)"`.
Prediction models run only when their required input features are supplied.

## Classification and network impact

The existing RCA agent remains unchanged: it ranks evidence-linked hypotheses
and does not establish a confirmed cause. A separate deterministic impact
assessment now follows RCA in the orchestration graph. It reports observed
metrics that cross the project's dataset-relative triage cutoffs and explains
possible service effects as potential, not confirmed, outcomes. Predicted
throughput is identified as model evidence, not an observation. These cutoffs
are not telecom SLAs or universal standards.

Incident prioritization uses the existing classifier on retrieved examples;
when current metrics are supplied, it also classifies the current scenario.
This is additive: retrieval ranking, RCA logic, CLI invocation, and existing
recommendation gating are not changed. The frontend/API exposes the same
structured sections returned by the orchestrator.

## Run focused tests

```powershell
.\venv\Scripts\python.exe -m pytest tests\test_api.py tests\test_impact_analysis.py tests\test_orchestrator.py -q
```
