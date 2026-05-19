from pathlib import Path

from ai_reliability_lab.ingestion import ingest_directory
from ai_reliability_lab.retrieval import Retriever
from ai_reliability_lab.storage import SQLiteStore


def _write_corpus(corpus_dir: Path) -> None:
    corpus_dir.mkdir()
    (corpus_dir / "model-release.md").write_text(
        """# Model release runbook

Every model candidate must pass offline evaluation before promotion.

## Rollback

When live metrics regress, roll back by moving the registry alias to the previous stable model.
""",
        encoding="utf-8",
    )
    (corpus_dir / "monitoring.md").write_text(
        """# Monitoring runbook

Track p95 latency, error rate, retrieval coverage, and drift alerts after each deployment.
""",
        encoding="utf-8",
    )


def test_ingestion_is_idempotent_and_records_chunks(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus(corpus_dir)
    store = SQLiteStore(tmp_path / "lab.db")

    first = ingest_directory(corpus_dir, store)
    second = ingest_directory(corpus_dir, store)

    assert first.documents == 2
    assert first.chunks > 0
    assert second.documents == 2
    assert second.chunks == first.chunks
    assert store.count_documents() == 2
    assert store.count_chunks() == first.chunks


def test_retriever_ranks_relevant_runbook_chunks(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus(corpus_dir)
    store = SQLiteStore(tmp_path / "lab.db")
    ingest_directory(corpus_dir, store)

    results = Retriever(store).search("How do I roll back a bad model release?", limit=2)

    assert results
    assert results[0].source == "model-release.md"
    assert results[0].score > 0
    assert {"rollback", "model"} <= set(results[0].matched_terms)

