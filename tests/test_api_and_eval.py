from pathlib import Path

from fastapi.testclient import TestClient

from ai_reliability_lab.app import create_app
from ai_reliability_lab.config import Settings


def _write_corpus(corpus_dir: Path) -> None:
    corpus_dir.mkdir()
    (corpus_dir / "release.md").write_text(
        """# Release checklist

Model releases require offline evaluation, smoke tests, and a rollback plan.

## Evidence

The model registry keeps the previous stable version so rollback does not require retraining.
""",
        encoding="utf-8",
    )
    (corpus_dir / "evals.md").write_text(
        """# Evaluation notes

Grounded answers should cite retrieved context and refuse when the corpus has no evidence.
""",
        encoding="utf-8",
    )


def test_api_ingests_queries_runs_evals_and_reports_metrics(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus(corpus_dir)
    settings = Settings(corpus_dir=corpus_dir, database_path=tmp_path / "lab.db")
    client = TestClient(create_app(settings))

    health_before = client.get("/health")
    assert health_before.status_code == 200
    assert health_before.json()["chunks"] == 0

    ingest_response = client.post("/ingest")
    assert ingest_response.status_code == 200
    assert ingest_response.json()["documents"] == 2
    assert ingest_response.json()["chunks"] > 0

    query_response = client.post(
        "/query",
        json={"question": "How should I roll back a model release?", "limit": 3},
    )
    assert query_response.status_code == 200
    query_payload = query_response.json()
    assert query_payload["citations"]
    assert "registry" in query_payload["answer"].lower()
    assert query_payload["diagnostics"]["source_coverage"] > 0

    eval_response = client.post("/eval/run")
    assert eval_response.status_code == 200
    eval_payload = eval_response.json()
    assert eval_payload["total"] >= 2
    assert eval_payload["passed"] >= 1
    assert eval_payload["provider"] == "deterministic"
    assert eval_payload["average_latency_ms"] >= 0
    assert eval_payload["average_source_coverage"] >= 0
    assert eval_payload["estimated_total_cost_usd"] >= 0
    assert {
        "latency_ms",
        "source_coverage",
        "estimated_cost_usd",
    } <= set(eval_payload["results"][0])

    metrics_response = client.get("/metrics/summary")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["query_count"] >= 1
    assert metrics["eval_runs"] >= 1
    assert metrics["average_latency_ms"] >= 0
