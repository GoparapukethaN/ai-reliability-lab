from pathlib import Path

from ai_reliability_lab.models import ProviderAnswer, RetrievedChunk
from ai_reliability_lab.storage import SQLiteStore


def test_store_records_query_trace_with_retrieval_and_metrics(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "lab.db")
    chunk = RetrievedChunk(
        chunk_id="release:0",
        source="model-release.md",
        heading="Rollback",
        text="Use the previous stable model.",
        score=0.91,
        matched_terms=["model"],
    )
    answer = ProviderAnswer(
        provider="deterministic",
        model="extractive-local",
        answer="Use the previous stable model. [C1]",
        citations=[],
        source_coverage=1.0,
        refused=False,
        latency_ms=4.0,
        estimated_cost_usd=0.0,
        warnings=[],
        confidence=1.0,
    )

    trace_id = store.record_query_trace(
        question="How do I roll back?",
        provider="deterministic",
        retrieved_chunks=[chunk],
        answer=answer,
    )

    trace = store.get_trace(trace_id)
    assert trace["trace_id"] == trace_id
    assert trace["question"] == "How do I roll back?"
    assert trace["retrieved_chunks"][0]["source"] == "model-release.md"
    assert store.metrics_summary()["provider_usage"]["deterministic"] == 1


def test_store_lists_recent_traces(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "lab.db")
    answer = ProviderAnswer(
        provider="deterministic",
        model="extractive-local",
        answer="No evidence.",
        citations=[],
        source_coverage=0.0,
        refused=True,
        latency_ms=2.0,
        estimated_cost_usd=0.0,
        warnings=["no_retrieved_evidence"],
        confidence=0.0,
    )
    trace_id = store.record_query_trace(
        question="What is the vacation policy?",
        provider="deterministic",
        retrieved_chunks=[],
        answer=answer,
    )

    traces = store.list_traces(limit=5)

    assert traces[0].trace_id == trace_id
    assert traces[0].refused is True
