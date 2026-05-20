from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ai_reliability_lab.models import Chunk, ProviderAnswer, QueryTraceSummary, RetrievedChunk


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

                CREATE TABLE IF NOT EXISTS query_traces (
                    trace_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    source_coverage REAL NOT NULL,
                    refused INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    warnings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS retrieval_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    text TEXT NOT NULL,
                    score REAL NOT NULL,
                    matched_terms_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS answer_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    citation_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    quote TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS eval_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL DEFAULT '',
                    provider TEXT NOT NULL DEFAULT 'deterministic',
                    total INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    failed INTEGER NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            self._ensure_columns(
                connection,
                "eval_runs",
                {
                    "run_id": "TEXT NOT NULL DEFAULT ''",
                    "provider": "TEXT NOT NULL DEFAULT 'deterministic'",
                },
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

    def list_documents(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source, checksum, chunk_count, ingested_at
                FROM documents
                ORDER BY source
                """
            ).fetchall()
        return [
            {
                "source": row["source"],
                "title": row["source"],
                "checksum": row["checksum"],
                "chunk_count": row["chunk_count"],
                "ingested_at": row["ingested_at"],
            }
            for row in rows
        ]

    def record_query(
        self,
        question: str,
        retrieved_sources: list[str],
        latency_ms: float,
        source_coverage: float,
    ) -> None:
        answer = ProviderAnswer(
            provider="deterministic",
            model="legacy",
            answer="",
            citations=[],
            source_coverage=source_coverage,
            refused=False,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
            warnings=[],
            confidence=source_coverage,
        )
        retrieved_chunks = [
            RetrievedChunk(
                chunk_id=f"legacy:{index}",
                source=source,
                heading="",
                text="",
                score=0.0,
                matched_terms=[],
            )
            for index, source in enumerate(retrieved_sources)
        ]
        self.record_query_trace(
            question=question,
            provider="deterministic",
            retrieved_chunks=retrieved_chunks,
            answer=answer,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO query_logs
                    (question, retrieved_sources, latency_ms, source_coverage, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (question, json.dumps(retrieved_sources), latency_ms, source_coverage, _now()),
            )

    def record_query_trace(
        self,
        question: str,
        provider: str,
        retrieved_chunks: list[RetrievedChunk],
        answer: ProviderAnswer,
    ) -> str:
        trace_id = f"trace-{uuid4().hex[:12]}"
        now = _now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO query_traces
                    (
                        trace_id,
                        question,
                        provider,
                        model,
                        answer,
                        latency_ms,
                        estimated_cost_usd,
                        source_coverage,
                        refused,
                        confidence,
                        warnings_json,
                        created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    question,
                    provider,
                    answer.model,
                    answer.answer,
                    answer.latency_ms,
                    answer.estimated_cost_usd,
                    answer.source_coverage,
                    int(answer.refused),
                    answer.confidence,
                    json.dumps(answer.warnings),
                    now,
                ),
            )
            connection.executemany(
                """
                INSERT INTO retrieval_traces
                    (
                        trace_id,
                        chunk_id,
                        rank,
                        source,
                        heading,
                        text,
                        score,
                        matched_terms_json
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        trace_id,
                        chunk.chunk_id,
                        rank,
                        chunk.source,
                        chunk.heading,
                        chunk.text,
                        chunk.score,
                        json.dumps(chunk.matched_terms),
                    )
                    for rank, chunk in enumerate(retrieved_chunks, start=1)
                ],
            )
            connection.executemany(
                """
                INSERT INTO answer_citations
                    (trace_id, citation_id, chunk_id, source, heading, quote)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        trace_id,
                        f"C{index}",
                        citation.chunk_id,
                        citation.source,
                        citation.heading,
                        citation.quote,
                    )
                    for index, citation in enumerate(answer.citations, start=1)
                ],
            )
        return trace_id

    def get_trace(self, trace_id: str) -> dict[str, object]:
        with self._connect() as connection:
            trace = connection.execute(
                """
                SELECT trace_id, question, provider, model, answer, latency_ms,
                       estimated_cost_usd, source_coverage, refused, confidence,
                       warnings_json, created_at
                FROM query_traces
                WHERE trace_id = ?
                """,
                (trace_id,),
            ).fetchone()
            if trace is None:
                raise KeyError(trace_id)
            retrieved = connection.execute(
                """
                SELECT chunk_id, source, heading, text, score, matched_terms_json
                FROM retrieval_traces
                WHERE trace_id = ?
                ORDER BY rank
                """,
                (trace_id,),
            ).fetchall()
            citations = connection.execute(
                """
                SELECT citation_id, chunk_id, source, heading, quote
                FROM answer_citations
                WHERE trace_id = ?
                ORDER BY id
                """,
                (trace_id,),
            ).fetchall()
        return {
            "trace_id": trace["trace_id"],
            "question": trace["question"],
            "provider": trace["provider"],
            "model": trace["model"],
            "answer": trace["answer"],
            "latency_ms": trace["latency_ms"],
            "estimated_cost_usd": trace["estimated_cost_usd"],
            "source_coverage": trace["source_coverage"],
            "refused": bool(trace["refused"]),
            "confidence": trace["confidence"],
            "warnings": json.loads(trace["warnings_json"]),
            "created_at": trace["created_at"],
            "retrieved_chunks": [
                {
                    "chunk_id": row["chunk_id"],
                    "source": row["source"],
                    "heading": row["heading"],
                    "text": row["text"],
                    "score": row["score"],
                    "matched_terms": json.loads(row["matched_terms_json"]),
                }
                for row in retrieved
            ],
            "citations": [
                {
                    "id": row["citation_id"],
                    "chunk_id": row["chunk_id"],
                    "source": row["source"],
                    "heading": row["heading"],
                    "quote": row["quote"],
                }
                for row in citations
            ],
        }

    def list_traces(self, limit: int = 20) -> list[QueryTraceSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT trace_id, question, provider, latency_ms, refused,
                       source_coverage, estimated_cost_usd, created_at
                FROM query_traces
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            QueryTraceSummary(
                trace_id=row["trace_id"],
                question=row["question"],
                provider=row["provider"],
                latency_ms=row["latency_ms"],
                refused=bool(row["refused"]),
                source_coverage=row["source_coverage"],
                estimated_cost_usd=row["estimated_cost_usd"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def record_eval(
        self,
        total: int,
        passed: int,
        failed: int,
        report: dict[str, object],
        run_id: str = "",
        provider: str = "deterministic",
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO eval_runs
                    (run_id, provider, total, passed, failed, report_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, provider, total, passed, failed, json.dumps(report), _now()),
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
            trace_row = connection.execute(
                """
                SELECT COUNT(*) AS query_count,
                       COALESCE(AVG(latency_ms), 0) AS average_latency_ms,
                       COALESCE(SUM(refused), 0) AS refusal_count,
                       COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd
                FROM query_traces
                """
            ).fetchone()
            provider_rows = connection.execute(
                """
                SELECT provider, COUNT(*) AS count
                FROM query_traces
                GROUP BY provider
                ORDER BY provider
                """
            ).fetchall()
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
            "query_count": max(query_row["query_count"], trace_row["query_count"]),
            "eval_runs": eval_row["eval_runs"],
            "average_latency_ms": round(
                trace_row["average_latency_ms"] or query_row["average_latency_ms"],
                2,
            ),
            "refusal_count": trace_row["refusal_count"],
            "estimated_cost_usd": round(trace_row["estimated_cost_usd"], 6),
            "provider_usage": {row["provider"]: row["count"] for row in provider_rows},
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

    @staticmethod
    def _ensure_columns(
        connection: sqlite3.Connection,
        table: str,
        columns: dict[str, str],
    ) -> None:
        existing = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for column, definition in columns.items():
            if column not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _now() -> str:
    return datetime.now(UTC).isoformat()
