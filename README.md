# AI Reliability Platform

I built this project to understand how I would move a RAG or agent workflow from a
notebook-style demo into a measurable system. The platform ingests MLOps runbooks,
retrieves evidence, answers with citations, compares answer providers, runs regression
evals, and exposes traces and metrics through both an API and a dashboard.

The default path is completely local and keyless. Optional OpenAI and Ollama providers
can be enabled when I want to compare a hosted or local model against the deterministic
baseline.

## What It Does

- Ingests Markdown, text, and PDF documents into a SQLite-backed corpus.
- Chunks documents with source, heading, ordinal, checksum, and token metadata.
- Retrieves relevant evidence with deterministic lexical scoring.
- Answers questions through a provider interface with citations and refusal behavior.
- Compares enabled providers on the same prompt and evidence set.
- Stores query traces, retrieved chunks, citations, latency, refusals, and cost estimates.
- Runs a grounding and refusal eval suite and saves Markdown/JSON report artifacts.
- Provides a FastAPI backend, a Next.js dashboard, Docker Compose, CLI workflows, tests,
  linting, and local verification.

## Dashboard

The dashboard is designed as an operational console, not a landing page. It gives me the
core workflow in one place:

- Ingest the sample corpus or upload a PDF/TXT/Markdown document.
- Ask a question and inspect the answer, citations, retrieved chunks, trace id, coverage,
  provider, latency, and estimated cost.
- Compare enabled providers.
- Run the eval gate and review pass/fail cases.
- Watch query counts, eval runs, average latency, refusals, and recent traces.

![Dashboard showing a grounded rollback query with metrics and retrieved evidence](docs/assets/dashboard-query.jpg)

```bash
docker compose up --build
```

Then open `http://localhost:3000`.

## Local Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
make verify
```

Run the API and dashboard without Docker:

```bash
uvicorn ai_reliability_lab.app:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

## CLI Workflow

```bash
ai-lab ingest
ai-lab query "How should I roll back a model release?"
ai-lab compare "How should I roll back a model release?"
ai-lab eval --format markdown
ai-lab providers
ai-lab traces
ai-lab metrics
```

Point the same workflow at a different corpus or database:

```bash
LAB_CORPUS_DIR=data/corpus LAB_DATABASE_PATH=data/runtime/lab.db ai-lab ingest
```

## API

- `GET /health` reports service, database, document, and chunk status.
- `GET /providers` lists deterministic, OpenAI, and Ollama provider availability.
- `GET /documents` lists indexed documents and chunk counts.
- `POST /documents/upload` indexes a Markdown, text, or PDF upload.
- `POST /ingest` ingests the configured corpus.
- `POST /query` returns answer, citations, retrieved chunks, trace id, latency, cost, and
  diagnostics.
- `POST /query/compare` runs the same question across enabled providers.
- `POST /eval/run` runs the evaluation set and stores report artifacts.
- `POST /eval/compare` compares eval results across providers.
- `GET /traces` and `GET /traces/{trace_id}` expose query trace history.
- `GET /reports` lists saved eval reports.
- `GET /metrics/summary` returns query/eval counts, average latency, refusals, provider
  usage, cost estimate, and recent failures.

## Architecture

```mermaid
flowchart LR
    A["Docs: Markdown, TXT, PDF"] --> B["Ingestion"]
    B --> C["Chunking + metadata"]
    C --> D["SQLite store"]
    D --> E["Retriever"]
    E --> F["Provider router"]
    F --> G["Deterministic local"]
    F --> H["OpenAI optional"]
    F --> I["Ollama optional"]
    G --> J["Cited answer"]
    H --> J
    I --> J
    J --> K["Query traces + citations"]
    E --> L["Eval runner"]
    F --> L
    L --> M["Markdown/JSON reports"]
    K --> N["Dashboard + metrics"]
    M --> N
```

## Verification

Hosted CI is useful, but I do not need it to prove the core workflow. The local gate runs
backend linting, tests, frontend typecheck/build, and CLI smoke tests against a temporary
database:

```bash
make verify
```

Latest local verification details are in [docs/verification.md](docs/verification.md).

## Interview Notes

The main engineering point is that every answer carries evidence and every eval is
repeatable. I started with a deterministic provider so I can test retrieval, citations,
refusals, and observability without depending on an external model. The provider boundary
lets me add real LLMs later without rewriting ingestion, retrieval, tracing, or evals.

The system is intentionally honest about what it measures: it records local latency,
provider availability, source coverage, refusal behavior, retrieved evidence, and eval
pass/fail results. It does not claim production users or adoption.

## More Detail

- [Architecture](docs/architecture.md)
- [Providers](docs/providers.md)
- [Observability](docs/observability.md)
- [Evaluation](docs/evaluation.md)
- [Demo Walkthrough](docs/demo.md)
- [Case Study](docs/case-study.md)
- [Interview Guide](docs/interview-guide.md)
- [Roadmap](docs/roadmap.md)
- [Verification](docs/verification.md)
