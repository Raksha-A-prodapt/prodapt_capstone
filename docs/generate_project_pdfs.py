"""Generate the project API, evaluation, and dataset PDFs without extra packages."""

from __future__ import annotations

import csv
import json
import math
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pdf_escape(value: str) -> str:
    value = value.encode("latin-1", "replace").decode("latin-1")
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(path: Path, title: str, sections: list[tuple[str, list[str]]]) -> None:
    lines: list[tuple[str, str]] = [("title", title)]
    for heading, body in sections:
        lines.append(("heading", heading))
        for paragraph in body:
            if not paragraph:
                lines.append(("space", ""))
                continue
            for line in textwrap.wrap(paragraph, width=105, break_long_words=False, break_on_hyphens=False):
                lines.append(("body", line))

    page_lines: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    for item in lines:
        current.append(item)
        if len(current) >= 48:
            page_lines.append(current)
            current = []
    if current:
        page_lines.append(current)

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_ids = [4 + i * 2 for i in range(len(page_lines))]
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for index, page in enumerate(page_lines):
        content: list[str] = ["BT"]
        y = 744
        for kind, line in page:
            if kind == "space":
                y -= 6
                continue
            if kind == "title":
                size = 17
                font = "/F1"
            elif kind == "heading":
                size = 11
                font = "/F1"
                y -= 5
            else:
                size = 9
                font = "/F1"
            if y < 48:
                break
            # Use an absolute text matrix for every line. Relative Td calls
            # would accumulate the x/y offsets and eventually move text off-page.
            content.append(f"{font} {size} Tf 1 0 0 1 54 {y} Tm ({pdf_escape(line)}) Tj")
            y -= 15 if kind != "title" else 24
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", "replace")
        page_object = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {5 + index * 2} 0 R >>".encode()
        objects.append(page_object)
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    path.write_bytes(output)


def dataset_sections() -> list[tuple[str, list[str]]]:
    schema = read_json(ROOT / "files_load_context_files" / "schema.json")
    csv_path = ROOT / "data" / "telecom_network_incidents_with_id.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    sections = [
        ("Dataset identity", [
            "Primary source: data/telecom_network_incidents_with_id.csv.",
            f"Observed rows: {len(rows):,}; observed columns: {len(columns)}.",
            "The dataset represents telecom network incidents/observations across performance, operations, load, signal, environment, security, geography, and fault-risk fields.",
        ]),
        ("Schema and field groups", [
            "The canonical schema is files_load_context_files/schema.json and the normalized schema is files_load_context_files/schema.jsonl.",
            "Context and geography: Incident_ID, Season, Weather, Issue Reported, City, State, Zip.",
            "Performance: Cell Availability, Throughput, Latency, Packet Loss Rate, Call Drop Rate, Handover Success Rate, Jitter, Connection Setup Success Rate.",
            "Operations: MTTR, Alarm Count, Critical Alarm Count, Parameter Changes, Successful Configuration Changes.",
            "Load and environment: Data Usage, User Count, Signal Strength, Temperature, Humidity.",
            "Security and target: Security Incidents, Authentication Failures, Fault Occurrence Rate.",
        ]),
        ("Data quality and usage", [
            "The Synapt knowledge context describes the source dataset as 100,000 rows with 27 columns and no missing values; verify against the current CSV before production use.",
            "Historical retrieval uses metadata/numeric filters plus semantic and lexical ranking; historical averages are descriptive and are not live telemetry.",
            "The dataset contains synthetic/project data and should not be presented as a live operator network feed.",
        ]),
        ("Embedding and retrieval", [
            "Local embedding model: BAAI/bge-small-en-v1.5 through sentence-transformers.",
            "Vector store: ChromaDB; lexical retrieval: rank-bm25; orchestration combines semantic and lexical evidence.",
            "The project also contains older commented OpenRouter embedding code; the active embedding path is local BGE.",
        ]),
        ("Prediction features", [
            "Throughput prediction uses performance, operational, load, signal, environmental, security, and categorical context features.",
            "Fault-risk prediction uses throughput, performance, operational, load, signal, environmental, and security features.",
            "Models run only when the required live feature set is supplied; missing telemetry must not be silently imputed as current truth.",
        ]),
    ]
    return sections


def api_sections() -> list[tuple[str, list[str]]]:
    return [
        ("Service topology", [
            "Synapt MCP bridge: http://127.0.0.1:8000/mcp.",
            "Starlette backend API: http://127.0.0.1:8001.",
            "React/Vite frontend: http://127.0.0.1:8790.",
        ]),
        ("GET /api/health", [
            "Purpose: check backend liveness and whether the orchestrator has initialized.",
            "Response: { status: 'ok', orchestrator_initialized: boolean }.",
        ]),
        ("POST /api/analyze", [
            "Purpose: run guardrail, query planning, Synapt context, incident retrieval, prediction or historical baseline, RCA, classification, impact, recommendations, summary, and response assembly.",
            "Request fields: query string required; network_metrics object optional; prediction_mode is network_performance or fault_tolerance; top_k is an integer from 1 to 50.",
            "Prediction behavior: live models run only with required telemetry; without telemetry, evaluation-style queries can produce a historical baseline.",
            "Response: structured JSON containing final_answer, user_answer, sections, trace, execution metadata, and optional evaluation output.",
        ]),
        ("POST /api/predict", [
            "Purpose: run the prediction agent directly without the complete assistant workflow.",
            "Request: network_metrics object required and prediction_mode optional.",
            "Response: prediction status, predicted throughput/fault risk, model trace, missing-feature information, and model limitations.",
        ]),
        ("POST /api/classify", [
            "Purpose: classify and prioritize a supplied current metric scenario.",
            "Request: network_metrics object required.",
            "Response: configured dataset-relative risk labels and classification details; these are not telecom SLAs.",
        ]),
        ("POST /api/feedback", [
            "Purpose: save user feedback for a response.",
            "Request: response_id, query, final_response, rating (helpful or not_helpful), and optional comment/context.",
            "Response: accepted status, feedback_id, response_id, and whether it was marked for evaluation.",
        ]),
        ("Example /api/analyze request", [
            '{ "query": "Calculate historical averages for high latency and packet loss, assess network impact, and suggest troubleshooting actions from Synapt SOPs.", "prediction_mode": "network_performance", "top_k": 15 }',
        ]),
        ("Error behavior", [
            "Invalid JSON or validation errors return HTTP 400/422 with a detail field.",
            "Prediction model execution errors return HTTP 500 with a safe error message and diagnostic field.",
            "The API is configured for local frontend origins on port 8790 and should remain bound to localhost during development.",
        ]),
    ]


def evaluation_sections() -> list[tuple[str, list[str]]]:
    ragas = read_json(ROOT / "evaluations" / "reports" / "ragas_synapt_report.json")
    synapt = read_json(ROOT / "evaluations" / "reports" / "synapt_agent_deepeval_report.json")
    orch = read_json(ROOT / "evaluations" / "reports" / "orchestrator_deepeval_report.json")
    prediction = read_json(ROOT / "evaluations" / "reports" / "prediction_agent_deepeval_report.json")
    metric_lines = []
    for name, item in ragas.get("metrics", {}).items():
        metric_lines.append(f"RAGAS {name}: average {item.get('average_score')}, count {item.get('count')}, good={item.get('good')}.")
    prediction_metrics = prediction.get("metrics", {})
    prediction_metric_names = list(prediction_metrics.keys()) if isinstance(prediction_metrics, dict) else [str(item) for item in prediction_metrics]
    return [
        ("Evaluation scope", [
            "The project evaluates Synapt retrieval, the complete orchestrator, prediction behavior, and RAG quality.",
            "Judges use the AICredits OpenAI-compatible API with google/gemini-3.1-flash-lite where configured.",
            "Scores are project evaluation results, not production service-level guarantees.",
        ]),
        ("RAGAS Synapt evaluation", [
            f"Queries: {ragas.get('query_count')}; good threshold: {ragas.get('good_threshold')}; overall score: {ragas.get('overall_score')}; frontend qualification: {ragas.get('qualifies_for_frontend')}.",
            *metric_lines,
            "Context window was bounded to three contexts and 3,500 characters per context to control judge latency.",
        ]),
        ("DeepEval Synapt evaluation", [
            f"Status: {synapt.get('status')}; queries: {synapt.get('query_count')}; usable queries: {synapt.get('usable_query_count')}; average score: {synapt.get('average_score')}.",
            "Metrics cover answer relevancy, faithfulness, contextual relevance/precision, and procedure/retrieval behavior depending on the case.",
        ]),
        ("Orchestrator and prediction evaluation", [
            f"Orchestrator test cases: {orch.get('test_case_count')}; metrics: {orch.get('metric_count')}; passed metrics: {orch.get('passed_metrics')}; failed metrics: {orch.get('failed_metrics')}.",
            f"Prediction evaluation cases: {prediction.get('total')}; passed: {prediction.get('passed')}; metrics: {prediction_metric_names}.",
            "The evaluation page reads saved reports from evaluations/reports and frontend/src/data.",
        ]),
        ("Interpretation and limitations", [
            "Faithfulness measures support from retrieved context; contextual precision measures how focused the retrieved context is.",
            "The moderate Context Precision score indicates retrieval noise or broad SOP/shared context and is an improvement area, not proof that every answer is incorrect.",
            "AICredits/judge timeouts can make a metric unavailable; the reports record missing metrics and qualification logic.",
        ]),
    ]


def main() -> None:
    make_pdf(OUT / "api_documentation.pdf", "Telecom Network Operations Assistant - API Documentation", api_sections())
    make_pdf(OUT / "evaluation_report.pdf", "Telecom Network Operations Assistant - Evaluation Report", evaluation_sections())
    make_pdf(OUT / "dataset_details.pdf", "Telecom Network Operations Assistant - Dataset Details", dataset_sections())
    print("Generated:")
    for name in ("api_documentation.pdf", "evaluation_report.pdf", "dataset_details.pdf"):
        print(OUT / name)


if __name__ == "__main__":
    main()
