# Claude Prompt: Generate the Three Project PDFs

Use the following prompt with Claude after attaching the repository files,
`README.md`, `APPLICATION_FLOW.md`, `PROJECT_NAVIGATION.md`,
`docs/TECHNICAL_STACK.md`, the architecture diagram, the API source, the
evaluation JSON reports, the schema files, and the dataset summary.

```text
You are a senior technical writer and software architect. Create three
separate, polished PDF documents for the Telecom Network Operations Assistant
capstone project. Use the attached repository files as the source of truth.
Do not invent frameworks, endpoints, metrics, evaluation results, dataset
statistics, credentials, or architecture components.

Important implementation distinction:
- React/Vite is the user-facing frontend.
- The project also has a Python backend API in api.py served locally by Uvicorn;
  identify the actual backend framework from api.py rather than guessing.
- The local Synapt MCP bridge runs separately on port 8000.
- The API runs on port 8001.
- The React frontend runs on port 8790.
- The active LLM provider is AICredits; do not describe OpenRouter or Claude as
  the active provider unless the source files explicitly show that configuration.
- The active local embedding model is BAAI/bge-small-en-v1.5.
- Never print real API keys, client secrets, tokens, .env values, or private
  endpoints.

Create these three independent PDFs:

PDF 1: API Documentation
Include:
1. Application purpose and service topology.
2. Ports and startup dependencies.
3. GET /api/health.
4. POST /api/analyze, including every request field, validation rule, optional
   telemetry behavior, historical-baseline behavior, and response sections.
5. POST /api/predict.
6. POST /api/classify.
7. POST /api/feedback.
8. JSON request and response examples derived from the actual Pydantic models
   and api.py implementation.
9. HTTP status/error behavior, CORS/local-host behavior, and security notes.
10. A complete end-to-end request sequence from React to API, orchestrator,
    retrieval, Synapt, prediction/RCA/impact/recommendations, and UI.

PDF 2: Evaluation Report
Include:
1. Evaluation objectives and test scope.
2. DeepEval test suites and metrics.
3. RAGAS metrics and definitions.
4. LLM-as-judge provider/model and timeout/retry policy.
5. Exact aggregate and per-query results from the attached JSON reports.
6. Evaluation thresholds and frontend qualification logic.
7. Interpretation of good, moderate, low, unavailable, and timeout results.
8. Limitations: synthetic data, bounded context windows, judge variability,
    retrieval noise, and absence of live telemetry in historical tests.
9. Separate findings for Synapt retrieval, complete orchestration, prediction,
    RCA, faithfulness, relevance, contextual precision, and contextual recall.
10. Recommendations for improving weak metrics without fabricating better
    scores.

PDF 3: Dataset Details
Include:
1. Dataset purpose, source path, row count, column count, and data type.
2. A complete field dictionary grouped into context/geography, performance,
    operations, load, signal/environment, security, and prediction target.
3. Units, ranges, categorical values, missing-value information, and schema
    source from the attached schema files.
4. How the dataset is used by metadata filtering, ChromaDB/vector retrieval,
    BM25 lexical retrieval, RCA, historical averages, classification, and ML.
5. Embedding details: sentence-transformers and BAAI/bge-small-en-v1.5.
6. Data-quality, synthetic-data, privacy, bias, and production limitations.
7. Which fields are required for throughput prediction and fault-risk prediction.
8. Explain why historical averages are baselines and not live predictions.

Formatting requirements for all three PDFs:
- Add a title page, table of contents, numbered headings, page numbers, and a
  generated date.
- Use readable tables, monospace formatting for endpoints/JSON, consistent
  captions, and professional capstone-report styling.
- Include the existing architecture diagram only in the API/Application flow
  document if it is attached; do not redraw or replace it.
- Add a source-files/references section.
- Clearly label facts, implementation behavior, assumptions, and limitations.
- Do not include secrets or copy the contents of .env.
- Return three separate PDF files with these names:
  api_documentation.pdf, evaluation_report.pdf, dataset_details.pdf.
```
