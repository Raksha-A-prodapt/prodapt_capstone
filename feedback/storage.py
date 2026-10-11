"""Small SQLite store for response feedback and deferred evaluations."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "feedback" / "feedback.sqlite3"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


class FeedbackStore:
    """Persist feedback and evaluation records without storing secrets."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured = db_path or os.getenv("FEEDBACK_DB_PATH")
        self.db_path = Path(configured) if configured else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    final_response TEXT NOT NULL,
                    rating TEXT NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
                    comment TEXT,
                    context_json TEXT NOT NULL DEFAULT '{}',
                    needs_evaluation INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_feedback_evaluation
                    ON feedback(needs_evaluation, id);
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id TEXT NOT NULL,
                    feedback_id INTEGER,
                    evaluator TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scores_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT,
                    evaluated_at TEXT NOT NULL,
                    FOREIGN KEY(feedback_id) REFERENCES feedback(id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_evaluations_once
                    ON evaluations(feedback_id, evaluator);
                """
            )

    def save_feedback(
        self,
        *,
        response_id: str,
        query: str,
        final_response: str,
        rating: str,
        comment: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> int:
        if rating not in {"helpful", "not_helpful"}:
            raise ValueError("rating must be helpful or not_helpful")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO feedback
                    (response_id, query, final_response, rating, comment,
                     context_json, needs_evaluation, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response_id,
                    query[:4000],
                    final_response[:20000],
                    rating,
                    (comment or "")[:4000] or None,
                    _json(context),
                    1 if rating == "not_helpful" else 0,
                    _timestamp(),
                ),
            )
            return int(cursor.lastrowid)

    def flagged_feedback(self, limit: int = 20, *, force: bool = False) -> list[dict[str, Any]]:
        with self._connect() as connection:
            condition = "rating = 'not_helpful'" if force else "needs_evaluation = 1"
            rows = connection.execute(
                f"SELECT * FROM feedback WHERE {condition} ORDER BY id LIMIT ?",
                (max(1, min(limit, 100)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_evaluation(
        self,
        *,
        response_id: str,
        feedback_id: int,
        evaluator: str,
        status: str,
        scores: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO evaluations
                    (response_id, feedback_id, evaluator, status,
                     scores_json, error, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (response_id, feedback_id, evaluator, status, _json(scores), error, _timestamp()),
            )
            connection.execute(
                "UPDATE feedback SET needs_evaluation = 0 WHERE id = ?",
                (feedback_id,),
            )

    def summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            ratings = connection.execute(
                "SELECT rating, COUNT(*) AS count FROM feedback GROUP BY rating"
            ).fetchall()
            evaluations = connection.execute(
                "SELECT status, COUNT(*) AS count FROM evaluations GROUP BY status"
            ).fetchall()
            pending = connection.execute(
                "SELECT COUNT(*) AS count FROM feedback WHERE needs_evaluation = 1"
            ).fetchone()["count"]
        return {
            "ratings": {row["rating"]: row["count"] for row in ratings},
            "evaluations": {row["status"]: row["count"] for row in evaluations},
            "pending_evaluations": pending,
        }
