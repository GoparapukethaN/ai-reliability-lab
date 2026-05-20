from pathlib import Path

from fastapi.testclient import TestClient

from ai_reliability_lab.app import create_app
from ai_reliability_lab.config import Settings


def test_api_query_compare_traces_providers_and_documents(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "model-release.md").write_text(
        "# Release\n\nRollback uses the model registry alias and previous stable version.",
        encoding="utf-8",
    )
    client = TestClient(create_app(Settings(corpus_dir=corpus, database_path=tmp_path / "lab.db")))

    assert client.post("/ingest").status_code == 200
    documents = client.get("/documents").json()
    assert documents[0]["source"] == "model-release.md"

    providers = client.get("/providers").json()
    assert providers[0]["id"] == "deterministic"

    query = client.post(
        "/query",
        json={"question": "How should I roll back?", "provider": "deterministic"},
    ).json()
    assert query["trace_id"]
    assert query["provider"] == "deterministic"
    assert query["citations"]

    compare = client.post("/query/compare", json={"question": "How should I roll back?"}).json()
    assert compare["results"][0]["provider"] == "deterministic"
    assert compare["results"][0]["trace_id"]

    trace = client.get(f"/traces/{query['trace_id']}").json()
    assert trace["question"] == "How should I roll back?"
    assert trace["retrieved_chunks"][0]["source"] == "model-release.md"

    traces = client.get("/traces").json()
    assert traces[0]["trace_id"]


def test_api_uploads_text_document_into_corpus(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    client = TestClient(create_app(Settings(corpus_dir=corpus, database_path=tmp_path / "lab.db")))

    response = client.post(
        "/documents/upload",
        files={"file": ("uploaded.md", b"# Uploaded\n\nRollback policy uses registry aliases.")},
    )

    assert response.status_code == 200
    assert response.json()["documents"] == 1
    documents = client.get("/documents").json()
    assert documents[0]["source"] == "uploaded.md"


def test_api_allows_local_dashboard_cors(tmp_path: Path) -> None:
    client = TestClient(
        create_app(Settings(corpus_dir=tmp_path / "corpus", database_path=tmp_path / "lab.db"))
    )

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_eval_run_writes_report_artifacts(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "model-release.md").write_text(
        "# Release\n\nRollback uses the model registry and previous stable version.",
        encoding="utf-8",
    )
    (corpus / "monitoring.md").write_text(
        "# Monitoring\n\nWatch p95 latency and retrieval coverage after deployment.",
        encoding="utf-8",
    )
    settings = Settings(
        corpus_dir=corpus,
        database_path=tmp_path / "lab.db",
        eval_report_dir=tmp_path / "reports",
    )
    client = TestClient(create_app(settings))
    client.post("/ingest")

    response = client.post("/eval/run")

    assert response.status_code == 200
    reports = client.get("/reports").json()
    assert reports
    assert reports[0]["kind"] == "evaluation"
    assert Path(reports[0]["path"]).exists()
