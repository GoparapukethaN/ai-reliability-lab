# Verification

Last local verification: 2026-05-20

## Automated Local Gate

Command:

```bash
make verify
```

Result:

- Ruff check: clean
- Pytest: 29 passed
- Frontend typecheck: passed
- Frontend production build: passed
- CLI smoke test: ingest, query, compare, providers, traces, eval, and metrics completed
  against a temporary database and temporary eval report directory
- Provider adapter tests cover mocked OpenAI/Ollama responses, provider errors, missing
  citation markers, and unsupported citation markers.
- Upload tests cover Markdown, PDF text extraction, and empty-PDF rejection.
- Safety tests cover secret-extraction refusal even when retrieved evidence contains a
  matching secret-like value.

Tracked proof:

- [verification-2026-05-20.md](proof/verification-2026-05-20.md)
- [evaluation-deterministic-20260520T072345Z.md](proof/evaluation-deterministic-20260520T072345Z.md)

## Docker Compose Check

Command:

```bash
make docker-check
```

Result:

- Docker Compose config: passed
- Backend image build: passed
- Frontend image build: passed
- Stack startup with temporary local ports: passed
- Corpus ingest through containerized API: 4 documents, 12 chunks
- Query smoke test: deterministic answer with citations and `model-release.md` evidence
- Metrics smoke test: query count recorded
- Dashboard CORS preflight from the configured frontend port: passed
- Dashboard readiness check: passed

## Browser QA

Local services:

- Backend: `http://127.0.0.1:8000`
- Dashboard: `http://127.0.0.1:3000`

Verified in the dashboard:

- Corpus ingests to 4 documents and 12 chunks.
- Query for rollback returns a grounded answer, citations, retrieved evidence, trace id,
  provider, coverage, latency, and estimated cost.
- Provider comparison returns the deterministic provider result.
- Eval gate runs successfully and passes 4/4 cases with provider, average latency,
  average coverage, and estimated cost visible.
- Metrics update after query, compare, and eval runs.
- Recent traces are visible.
- Long provider/trace values fit cleanly in dashboard metric cards.

The dashboard browser QA can be rerun against a live backend/dashboard:

```bash
cd frontend
npx playwright install chromium
LAB_DASHBOARD_URL=http://127.0.0.1:3000 npm run qa:dashboard
```

The script checks desktop and mobile viewports, console warnings/errors, horizontal
overflow, corpus ingest, grounded query, cited evidence, and the 4/4 eval gate.

## Migration Check

I also tested the SQLite upgrade path for an existing `eval_runs` table created before
provider/run id fields existed. The store now migrates that shape and records eval runs
without requiring a manual database reset.

## Notes

This project can run without hosted CI minutes because the local gate covers the core
backend, frontend, and CLI workflow. Docker Compose and dashboard browser QA stay as
separate checks for machines where those tools are installed. GitHub Actions can still be
used later when minutes are available again.
