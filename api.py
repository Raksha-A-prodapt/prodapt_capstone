"""Starlette API wrapper for the telecom analysis orchestrator."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from agents.orchestrator import TelecomAnalysisOrchestrator
from agents.prediction_agent import NetworkPredictionAgent
from feedback.storage import FeedbackStore

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_PATH = PROJECT_ROOT / "frontend" / "index.html"
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    network_metrics: dict[str, Any] | None = None
    prediction_mode: Literal["network_performance", "fault_tolerance"] = "network_performance"
    # Kept for API compatibility; the orchestrator uses the fixed retrieval
    # budget so the UI and RCA always receive the same evidence count.
    top_k: int = Field(default=15, ge=1, le=50)


class ClassifyRequest(BaseModel):
    network_metrics: dict[str, Any]


class PredictRequest(BaseModel):
    network_metrics: dict[str, Any]
    prediction_mode: Literal["network_performance", "fault_tolerance"] = "network_performance"


class FeedbackRequest(BaseModel):
    response_id: str = Field(min_length=1, max_length=200)
    query: str = Field(min_length=1, max_length=4000)
    final_response: str = Field(min_length=1, max_length=20000)
    rating: str = Field(pattern="^(helpful|not_helpful)$")
    comment: str | None = Field(default=None, max_length=4000)
    context: dict[str, Any] | None = None


def get_orchestrator(request: Request) -> TelecomAnalysisOrchestrator:
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None:
        orchestrator = TelecomAnalysisOrchestrator()
        request.app.state.orchestrator = orchestrator
    return orchestrator


async def _request_body(
    request: Request,
    model: type[BaseModel],
) -> BaseModel | JSONResponse:
    try:
        payload = await request.json()
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        return JSONResponse(
            {"detail": f"Request body must be valid JSON: {exc}"},
            status_code=400,
        )
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        return JSONResponse(
            {"detail": exc.errors(include_context=False)},
            status_code=422,
        )


async def index(request: Request) -> Response:
    if not FRONTEND_PATH.is_file():
        raise HTTPException(
            status_code=404,
            detail="The frontend page is not installed.",
        )
    return FileResponse(
        FRONTEND_PATH,
        headers={"X-Served-Path": request.url.path},
    )


async def health(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "orchestrator_initialized": getattr(
                request.app.state,
                "orchestrator",
                None,
            )
            is not None,
        }
    )


async def analyze(request: Request) -> Response:
    body = await _request_body(request, AnalyzeRequest)
    if isinstance(body, JSONResponse):
        return body
    request_data = body.model_dump()
    query = request_data["query"].strip()
    if not query:
        return JSONResponse(
            {"detail": "Query cannot contain only whitespace."},
            status_code=422,
        )
    orchestrator = get_orchestrator(request)
    result = await orchestrator.run(
        query=query,
        network_metrics=request_data["network_metrics"],
        prediction_mode=request_data["prediction_mode"],
        top_k=request_data["top_k"],
    )
    return JSONResponse(result)


async def classify(request: Request) -> Response:
    body = await _request_body(request, ClassifyRequest)
    if isinstance(body, JSONResponse):
        return body
    orchestrator = get_orchestrator(request)
    try:
        result = await run_in_threadpool(
            orchestrator.classify_scenario,
            body.network_metrics,
        )
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    return JSONResponse(result)


async def predict(request: Request) -> Response:
    """Run the ML prediction agent without invoking the assistant workflow."""
    body = await _request_body(request, PredictRequest)
    if isinstance(body, JSONResponse):
        return body

    metrics = dict(body.network_metrics)
    # Older frontend bundles contain a mojibake spelling for the degree symbol.
    if "Temperature (Â°C)" in metrics and "Temperature (°C)" not in metrics:
        metrics["Temperature (°C)"] = metrics.pop("Temperature (Â°C)")

    orchestrator = get_orchestrator(request)
    try:
        if orchestrator.prediction_agent is None:
            orchestrator.prediction_agent = NetworkPredictionAgent()
        result = await run_in_threadpool(
            lambda: orchestrator.prediction_agent.process(
                metrics,
                prediction_mode=body.prediction_mode,
            )
        )
    except (ValueError, KeyError, TypeError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    except Exception as exc:
        request.app.state.last_prediction_error = str(exc)
        return JSONResponse(
            {"detail": "Prediction model execution failed.", "error": str(exc)},
            status_code=500,
        )
    return JSONResponse(result)


async def feedback(request: Request) -> Response:
    body = await _request_body(request, FeedbackRequest)
    if isinstance(body, JSONResponse):
        return body
    try:
        feedback_id = FeedbackStore().save_feedback(
            response_id=body.response_id,
            query=body.query,
            final_response=body.final_response,
            rating=body.rating,
            comment=body.comment,
            context=body.context,
        )
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)
    return JSONResponse({
        "status": "accepted",
        "feedback_id": feedback_id,
        "response_id": body.response_id,
        "marked_for_evaluation": body.rating == "not_helpful",
    })


routes = [
    Route("/", index, methods=["GET"]),
    Route("/api/health", health, methods=["GET"]),
    Route("/api/analyze", analyze, methods=["POST"]),
    Route("/api/classify", classify, methods=["POST"]),
    Route("/api/predict", predict, methods=["POST"]),
    Route("/api/feedback", feedback, methods=["POST"]),
]

@asynccontextmanager
async def lifespan(application: Starlette):
    """Warm the orchestrator and embedding/retrieval resources at startup."""
    if getattr(application.state, "orchestrator", None) is None:
        try:
            logger.info(
                "Initializing telecom orchestrator and loading retrieval model..."
            )
            application.state.orchestrator = TelecomAnalysisOrchestrator()
            logger.info(
                "Telecom orchestrator ready; retrieval model and indexes are warm."
            )
        except Exception:
            logger.exception(
                "Startup model initialization failed; the first request may retry initialization."
            )
    yield


app = Starlette(debug=False, routes=routes, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8790",
        "http://localhost:8790",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
