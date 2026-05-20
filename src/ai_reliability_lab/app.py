from __future__ import annotations

from time import perf_counter
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ai_reliability_lab.config import Settings
from ai_reliability_lab.evaluation import default_eval_cases, run_evaluation
from ai_reliability_lab.ingestion import ingest_directory, ingest_text
from ai_reliability_lab.providers import ProviderError, ProviderRouter
from ai_reliability_lab.reporting import list_report_artifacts, save_eval_report
from ai_reliability_lab.retrieval import Retriever
from ai_reliability_lab.storage import SQLiteStore


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    limit: int = Field(default=5, ge=1, le=10)
    provider: str | None = None


class CompareRequest(BaseModel):
    question: str = Field(min_length=3)
    limit: int = Field(default=5, ge=1, le=10)
    providers: list[str] | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    store = SQLiteStore(resolved_settings.database_path)
    retriever = Retriever(store)
    provider_router = ProviderRouter.from_settings(resolved_settings)
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

    @app.get("/providers")
    def providers() -> list[dict[str, object]]:
        return [provider.to_dict() for provider in provider_router.available()]

    @app.get("/documents")
    def documents() -> list[dict[str, object]]:
        return store.list_documents()

    @app.post("/ingest")
    def ingest() -> dict[str, object]:
        return ingest_directory(resolved_settings.corpus_dir, store).to_dict()

    @app.post("/documents/upload")
    async def upload_document(file: Annotated[UploadFile, File(...)]) -> dict[str, object]:
        content = await file.read()
        text = _decode_upload(file.filename or "uploaded.md", content)
        return ingest_text(file.filename or "uploaded.md", text, store).to_dict()

    @app.post("/query")
    def query(request: QueryRequest) -> dict[str, object]:
        provider_id = request.provider or resolved_settings.default_provider
        payload = _answer_payload(
            question=request.question,
            limit=request.limit,
            provider_id=provider_id,
            retriever=retriever,
            provider_router=provider_router,
            store=store,
        )
        return payload

    @app.post("/query/compare")
    def query_compare(request: CompareRequest) -> dict[str, object]:
        provider_ids = request.providers or provider_router.enabled_provider_ids()
        results = []
        for provider_id in provider_ids:
            results.append(
                _answer_payload(
                    question=request.question,
                    limit=request.limit,
                    provider_id=provider_id,
                    retriever=retriever,
                    provider_router=provider_router,
                    store=store,
                )
            )
        return {"question": request.question, "results": results}

    @app.get("/traces")
    def traces(limit: int = 20) -> list[dict[str, object]]:
        return [trace.to_dict() for trace in store.list_traces(limit=limit)]

    @app.get("/traces/{trace_id}")
    def trace_detail(trace_id: str) -> dict[str, object]:
        try:
            return store.get_trace(trace_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Trace not found") from exc

    @app.get("/reports")
    def reports() -> list[dict[str, object]]:
        return [
            report.to_dict()
            for report in list_report_artifacts(resolved_settings.eval_report_dir)
        ]

    @app.post("/eval/compare")
    def eval_compare(request: CompareRequest | None = None) -> dict[str, object]:
        provider_ids = (
            request.providers
            if request and request.providers
            else provider_router.enabled_provider_ids()
        )
        reports = []
        for provider_id in provider_ids:
            report = run_evaluation(
                default_eval_cases(),
                retriever,
                provider_router,
                provider_id=provider_id,
            )
            reports.append(report.to_dict())
        return {"reports": reports}

    @app.post("/eval/run")
    def eval_run() -> dict[str, object]:
        report = run_evaluation(
            default_eval_cases(),
            retriever,
            provider_router,
            provider_id=resolved_settings.default_provider,
        )
        payload = report.to_dict()
        store.record_eval(
            total=report.total,
            passed=report.passed,
            failed=report.failed,
            report=payload,
            provider=report.provider,
        )
        save_eval_report(report, resolved_settings.eval_report_dir)
        return payload

    @app.get("/metrics/summary")
    def metrics_summary() -> dict[str, object]:
        return store.metrics_summary()

    return app


def _answer_payload(
    question: str,
    limit: int,
    provider_id: str,
    retriever: Retriever,
    provider_router: ProviderRouter,
    store: SQLiteStore,
) -> dict[str, object]:
    started = perf_counter()
    retrieved = retriever.search(question, limit=limit)
    try:
        answer = provider_router.answer(question, retrieved, provider_id=provider_id)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    total_latency_ms = round((perf_counter() - started) * 1000, 2)
    answer_latency_ms = total_latency_ms if answer.latency_ms == 0 else answer.latency_ms
    trace_id = store.record_query_trace(
        question=question,
        provider=provider_id,
        retrieved_chunks=retrieved,
        answer=answer,
    )
    return {
        "trace_id": trace_id,
        "provider": answer.provider,
        "model": answer.model,
        "answer": answer.answer,
        "citations": [citation.to_dict() for citation in answer.citations],
        "retrieved_chunks": [chunk.to_dict() for chunk in retrieved],
        "latency_ms": total_latency_ms,
        "estimated_cost_usd": answer.estimated_cost_usd,
        "warnings": answer.warnings,
        "diagnostics": {
            "source_coverage": answer.source_coverage,
            "refused": answer.refused,
            "retrieved_count": len(retrieved),
            "provider_latency_ms": answer_latency_ms,
            "confidence": answer.confidence,
        },
    }


app = create_app()


def _decode_upload(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise HTTPException(status_code=400, detail="PDF support is unavailable.") from exc
        from io import BytesIO

        reader = PdfReader(BytesIO(content))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")
        return text
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Upload must be UTF-8 text or PDF.") from exc
