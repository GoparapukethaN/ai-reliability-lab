from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from ai_reliability_lab.models import Chunk


class SQLiteStore:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.init_schema()

    def init_schema(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    source TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    heading TEXT NOT NULL,
                    text TEXT NOT NULL,
                    token_count INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    retrieved_sources TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    source_coverage REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS eval_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def replace_document(self, source: str, checksum: str, chunks: Iterable[Chunk]) -> None:
        chunk_list = list(chunks)
        now = _now()
        with self._connect() as connection:
            connection.execute("DELETE FROM chunks WHERE source = ?", (source,))
            connection.execute(
                """
                INSERT INTO documents (source, checksum, chunk_count, ingested_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    checksum = excluded.checksum,
                    chunk_count = excluded.chunk_count,
                    ingested_at = excluded.ingested_at
                """,
                (source, checksum, len(chunk_list), now),
            )
            connection.executemany(
                """
                INSERT INTO chunks (chunk_id, source, ordinal, heading, text, token_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        source,
                        chunk.ordinal,
                        chunk.heading,
                        chunk.text,
                        len(chunk.text.split()),
                    )
                    for chunk in chunk_list
                ],
            )

    def count_documents(self) -> int:
        return self._count("documents")

    def count_chunks(self) -> int:
        return self._count("chunks")

    def all_chunks(self) -> list[Chunk]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT chunk_id, source, heading, text, ordinal
                FROM chunks
                ORDER BY source, ordinal
                """
            ).fetchall()
        return [
            Chunk(
                chunk_id=row["chunk_id"],
                source=row["source"],
                heading=row["heading"],
                text=row["text"],
                ordinal=row["ordinal"],
            )
            for row in rows
        ]

    def record_query(
        self,
        question: str,
        retrieved_sources: list[str],
        latency_ms: float,
        source_coverage: float,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO query_logs
                    (question, retrieved_sources, latency_ms, source_coverage, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (question, json.dumps(retrieved_sources), latency_ms, source_coverage, _now()),
            )

    def record_eval(self, total: int, passed: int, failed: int, report: dict[str, object]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO eval_runs (total, passed, failed, report_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (total, passed, failed, json.dumps(report), _now()),
            )

    def metrics_summary(self) -> dict[str, object]:
        with self._connect() as connection:
            query_row = connection.execute(
                """
                SELECT COUNT(*) AS query_count,
                       COALESCE(AVG(latency_ms), 0) AS average_latency_ms
                FROM query_logs
                """
            ).fetchone()
            eval_row = connection.execute(
                "SELECT COUNT(*) AS eval_runs FROM eval_runs"
            ).fetchone()
            recent_failures = connection.execute(
                """
                SELECT report_json
                FROM eval_runs
                ORDER BY id DESC
                LIMIT 3
                """
            ).fetchall()

        failures: list[dict[str, object]] = []
        for row in recent_failures:
            report = json.loads(row["report_json"])
            failures.extend(
                result for result in report.get("results", []) if not result.get("passed")
            )

        return {
            "query_count": query_row["query_count"],
            "eval_runs": eval_row["eval_runs"],
            "average_latency_ms": round(query_row["average_latency_ms"], 2),
            "recent_failures": failures[:5],
        }

    def _count(self, table: str) -> int:
        with self._connect() as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
        return int(row["count"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def _now() -> str:
    return datetime.now(UTC).isoformat()

