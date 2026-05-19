from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ai_reliability_lab.answering import DeterministicAnswerComposer
from ai_reliability_lab.config import Settings
from ai_reliability_lab.evaluation import default_eval_cases, run_evaluation
from ai_reliability_lab.ingestion import ingest_directory
from ai_reliability_lab.retrieval import Retriever
from ai_reliability_lab.storage import SQLiteStore


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    limit: int = Field(default=5, ge=1, le=10)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    store = SQLiteStore(resolved_settings.database_path)
    retriever = Retriever(store)
    composer = DeterministicAnswerComposer()
    app = FastAPI(title="AI Reliability Lab", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "database_path": str(resolved_settings.database_path),
            "corpus_dir": str(resolved_settings.corpus_dir),
            "documents": store.count_documents(),
            "chunks": store.count_chunks(),
        }

    @app.post("/ingest")
    def ingest() -> dict[str, object]:
        return ingest_directory(resolved_settings.corpus_dir, store).to_dict()

    @app.post("/query")
    def query(request: QueryRequest) -> dict[str, object]:
        started = perf_counter()
        retrieved = retriever.search(request.question, limit=request.limit)
        answer = composer.compose(request.question, retrieved)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        store.record_query(
            question=request.question,
            retrieved_sources=[chunk.source for chunk in retrieved],
            latency_ms=latency_ms,
            source_coverage=answer.source_coverage,
        )
        return {
            "answer": answer.answer,
            "citations": [citation.to_dict() for citation in answer.citations],
            "retrieved_chunks": [chunk.to_dict() for chunk in retrieved],
            "latency_ms": latency_ms,
            "diagnostics": {
                "source_coverage": answer.source_coverage,
                "refused": answer.refused,
                "retrieved_count": len(retrieved),
            },
        }

    @app.post("/eval/run")
    def eval_run() -> dict[str, object]:
        report = run_evaluation(default_eval_cases(), retriever, composer)
        payload = report.to_dict()
        store.record_eval(
            total=report.total,
            passed=report.passed,
            failed=report.failed,
            report=payload,
        )
        return payload

    @app.get("/metrics/summary")
    def metrics_summary() -> dict[str, object]:
        return store.metrics_summary()

    return app


app = create_app()
