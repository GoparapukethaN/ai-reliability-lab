# AI Reliability Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ai-reliability-lab` into one end-to-end local-first AI reliability
platform with backend, dashboard, providers, traces, evals, reports, Docker Compose, and
verification.

**Architecture:** Keep the current FastAPI/SQLite core and add a provider router,
trace schema, report exports, and dashboard API endpoints. Fold the useful Next.js
dashboard from `applied-ai-eval-lab` into `frontend/` and wire it to the unified backend.

**Tech Stack:** Python 3.12, FastAPI, SQLite, pytest, ruff, Next.js, TypeScript, Docker
Compose, optional OpenAI/Ollama providers.

---

## File Structure

- Modify `src/ai_reliability_lab/models.py`: shared dataclasses for providers, traces,
  query responses, eval reports, and report summaries.
- Modify `src/ai_reliability_lab/config.py`: provider and report configuration from
  environment variables.
- Create `src/ai_reliability_lab/providers.py`: deterministic, OpenAI, Ollama, and router
  implementations behind one interface.
- Modify `src/ai_reliability_lab/storage.py`: trace tables, eval item tables, reports,
  document listing, and metrics summary.
- Modify `src/ai_reliability_lab/app.py`: API endpoints for documents, uploads, query,
  compare, eval compare, traces, reports, and metrics.
- Modify `src/ai_reliability_lab/cli.py`: provider-aware query, compare, traces, report.
- Modify `src/ai_reliability_lab/evaluation.py`: provider-aware evals and richer scoring.
- Modify `src/ai_reliability_lab/reporting.py`: Markdown/JSON report export.
- Create `frontend/`: Next.js dashboard copied and adapted from `applied-ai-eval-lab`.
- Create `docker-compose.yml`: backend/frontend local run.
- Modify `Dockerfile`, `Makefile`, `scripts/verify-local.sh`, `.env.example`,
  `.gitignore`.
- Modify docs: `README.md`, `docs/architecture.md`, `docs/evaluation.md`,
  `docs/providers.md`, `docs/observability.md`, `docs/demo.md`, `docs/verification.md`,
  `docs/roadmap.md`.

## Task 1: Provider Interface And Settings

**Files:**
- Modify: `src/ai_reliability_lab/models.py`
- Modify: `src/ai_reliability_lab/config.py`
- Create: `src/ai_reliability_lab/providers.py`
- Test: `tests/test_providers.py`

- [ ] **Step 1: Write failing provider tests**

```python
from ai_reliability_lab.models import RetrievedChunk
from ai_reliability_lab.providers import ProviderRouter


def test_router_always_exposes_deterministic_provider():
    router = ProviderRouter.from_settings()
    assert "deterministic" in [provider.id for provider in router.available()]


def test_deterministic_provider_returns_citations_for_supported_question():
    chunk = RetrievedChunk(
        chunk_id="release:0",
        source="model-release.md",
        heading="Rollback",
        text="Rollback uses the model registry alias and previous stable version.",
        score=0.8,
        matched_terms=["rollback", "registry"],
    )
    router = ProviderRouter.from_settings()
    result = router.answer("How should I roll back?", [chunk], provider_id="deterministic")
    assert result.provider == "deterministic"
    assert result.citations
    assert result.refused is False
    assert result.estimated_cost_usd == 0
```

- [ ] **Step 2: Verify red**

Run:

```bash
.venv/bin/python -m pytest tests/test_providers.py -q
```

Expected: import failure for `ai_reliability_lab.providers`.

- [ ] **Step 3: Implement provider models and router**

Add provider dataclasses to `models.py`, settings fields to `config.py`, and
`providers.py` with deterministic provider, disabled OpenAI/Ollama provider metadata, and
safe optional-provider stubs that only run when configured.

- [ ] **Step 4: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/test_providers.py -q
```

Expected: provider tests pass.

## Task 2: Trace Persistence And Metrics

**Files:**
- Modify: `src/ai_reliability_lab/storage.py`
- Test: `tests/test_traces_and_metrics.py`

- [ ] **Step 1: Write failing trace tests**

```python
from pathlib import Path

from ai_reliability_lab.models import ProviderAnswer, RetrievedChunk
from ai_reliability_lab.storage import SQLiteStore


def test_store_records_query_trace_with_retrieval_and_citations(tmp_path: Path):
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
        answer="Use the previous stable model. [C1]",
        citations=[],
        source_coverage=1.0,
        refused=False,
        latency_ms=4.0,
        estimated_cost_usd=0.0,
        warnings=[],
    )
    trace_id = store.record_query_trace(
        question="How do I roll back?",
        provider="deterministic",
        retrieved_chunks=[chunk],
        answer=answer,
    )
    trace = store.get_trace(trace_id)
    assert trace["trace_id"] == trace_id
    assert trace["retrieved_chunks"][0]["source"] == "model-release.md"
    assert store.metrics_summary()["provider_usage"]["deterministic"] == 1
```

- [ ] **Step 2: Verify red**

Run:

```bash
.venv/bin/python -m pytest tests/test_traces_and_metrics.py -q
```

Expected: `record_query_trace` missing.

- [ ] **Step 3: Implement trace schema and summary metrics**

Expand SQLite schema with query trace and retrieval trace tables. Keep old
`record_query` compatibility by delegating it into the new trace path.

- [ ] **Step 4: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/test_traces_and_metrics.py -q
```

Expected: trace tests pass.

## Task 3: Provider-Aware API

**Files:**
- Modify: `src/ai_reliability_lab/app.py`
- Test: `tests/test_api_platform.py`

- [ ] **Step 1: Write failing API tests**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from ai_reliability_lab.app import create_app
from ai_reliability_lab.config import Settings


def test_api_query_compare_traces_and_documents(tmp_path: Path):
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
    query = client.post(
        "/query",
        json={"question": "How should I roll back?", "provider": "deterministic"},
    ).json()
    assert query["trace_id"]
    assert query["provider"] == "deterministic"
    compare = client.post("/query/compare", json={"question": "How should I roll back?"}).json()
    assert compare["results"][0]["provider"] == "deterministic"
    trace = client.get(f"/traces/{query['trace_id']}").json()
    assert trace["question"] == "How should I roll back?"
```

- [ ] **Step 2: Verify red**

Run:

```bash
.venv/bin/python -m pytest tests/test_api_platform.py -q
```

Expected: request model and endpoints missing.

- [ ] **Step 3: Implement provider-aware endpoints**

Add provider fields to query requests, return trace ids, add `/documents`,
`/query/compare`, `/traces`, `/traces/{trace_id}`, and `/reports`.

- [ ] **Step 4: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/test_api_platform.py -q
```

Expected: API platform tests pass.

## Task 4: Eval Reports And Regression Gate

**Files:**
- Modify: `src/ai_reliability_lab/evaluation.py`
- Modify: `src/ai_reliability_lab/reporting.py`
- Modify: `scripts/verify-local.sh`
- Test: `tests/test_eval_platform.py`

- [ ] **Step 1: Write failing eval tests**

```python
from pathlib import Path

from ai_reliability_lab.answering import DeterministicAnswerComposer
from ai_reliability_lab.evaluation import default_eval_cases, run_evaluation
from ai_reliability_lab.ingestion import ingest_directory
from ai_reliability_lab.providers import ProviderRouter
from ai_reliability_lab.retrieval import Retriever
from ai_reliability_lab.storage import SQLiteStore


def test_deterministic_eval_report_passes_curated_local_set(tmp_path: Path):
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
    store = SQLiteStore(tmp_path / "lab.db")
    ingest_directory(corpus, store)
    report = run_evaluation(
        default_eval_cases(),
        Retriever(store),
        ProviderRouter.from_settings(),
        provider_id="deterministic",
    )
    assert report.provider == "deterministic"
    assert report.passed == report.total
```

- [ ] **Step 2: Verify red**

Run:

```bash
.venv/bin/python -m pytest tests/test_eval_platform.py -q
```

Expected: `run_evaluation` signature does not accept provider router.

- [ ] **Step 3: Implement provider-aware evals and report export**

Update eval scoring to use provider router, persist eval items, and export latest report
as Markdown/JSON under `artifacts/reports`.

- [ ] **Step 4: Verify green and gate**

Run:

```bash
.venv/bin/python -m pytest tests/test_eval_platform.py -q
make verify
```

Expected: eval test and full verification pass without API keys.

## Task 5: Dashboard Integration

**Files:**
- Create: `frontend/`
- Modify: `Makefile`
- Create: `docker-compose.yml`
- Test/check: frontend typecheck/build and browser QA.

- [ ] **Step 1: Copy dashboard source**

Copy the useful `applied-ai-eval-lab/frontend` files into `ai-reliability-lab/frontend`,
then update names, API paths, types, and copy to match AI Reliability Platform.

- [ ] **Step 2: Wire API contract**

The dashboard uses:

- `GET /documents`
- `POST /ingest`
- `POST /query`
- `POST /query/compare`
- `POST /eval/run`
- `GET /metrics/summary`
- `GET /traces`

- [ ] **Step 3: Add frontend verification**

Add `make frontend-install`, `make frontend-typecheck`, `make frontend-build`, and include
frontend checks in `make verify`.

- [ ] **Step 4: Verify dashboard build**

Run:

```bash
cd frontend
npm install
npm run typecheck
npm run build
```

Expected: typecheck and production build pass.

## Task 6: Documentation And Public Story

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/evaluation.md`
- Create: `docs/providers.md`
- Create: `docs/observability.md`
- Modify: `docs/demo.md`
- Modify: `docs/verification.md`
- Modify: `docs/roadmap.md`

- [ ] **Step 1: Rewrite README as platform documentation**

Lead with the end-to-end platform, not an MVP caveat. Include one-command run, feature
list, architecture, dashboard flow, API examples, provider modes, and verification.

- [ ] **Step 2: Add provider and observability docs**

Document deterministic/OpenAI/Ollama configuration and trace/eval metrics.

- [ ] **Step 3: Update verification output**

Run `make verify`, record the current passing output in `docs/verification.md`, and keep
claims tied to local evidence.

## Task 7: Final Local QA

**Files:**
- No new files unless QA finds a bug.

- [ ] **Step 1: Run full verification**

Run:

```bash
make verify
```

Expected: backend lint/tests, frontend typecheck/build, API smoke, CLI smoke, eval gate.

- [ ] **Step 2: Run Docker Compose smoke**

Run:

```bash
docker compose config --quiet
docker compose up --build
```

Expected: backend on `:8000`, frontend on `:3000`, dashboard can query backend.

- [ ] **Step 3: Browser QA**

Use the in-app browser to test dashboard query, evidence, eval, traces, and metrics.

- [ ] **Step 4: Commit and push**

Commit normal human-readable project messages and push once verification passes.
