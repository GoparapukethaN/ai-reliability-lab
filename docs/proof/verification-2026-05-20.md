# Verification Proof - 2026-05-20

This note captures the local verification run for the portfolio version of the project.

## Local Gate

Command:

```bash
PYTHON=.venv/bin/python make verify
```

Key output:

```text
All checks passed!
.............................                                            [100%]
29 passed in 0.74s
Compiled successfully in 1641ms
Generating static pages using 4 workers (3/3) in 214ms
local verification passed
```

The gate covers Ruff, pytest, frontend typecheck, frontend production build, CLI smoke
commands, and the local deterministic eval path against a temporary database and
temporary report directory.

The Python tests now include mocked OpenAI/Ollama provider adapters, provider error
handling, strict citation-marker parsing, unsupported citation-marker warnings,
Markdown upload, PDF upload, empty-PDF rejection coverage, and secret-extraction refusal
when retrieved evidence contains a secret-like value.

## Docker Compose Smoke

Command:

```bash
make docker-check
```

Key output:

```text
Image ai-reliability-lab-verify-18080-13080-56687-frontend Built
Image ai-reliability-lab-verify-18080-13080-56687-backend Built
Container ai-reliability-lab-verify-18080-13080-56687-backend-1 Healthy
docker compose verification passed
```

The Docker smoke builds both images, starts the stack on temporary local ports, ingests
the sample corpus through the containerized API, checks a cited rollback query, verifies
metrics persistence, checks the configured dashboard CORS origin, and confirms the
dashboard serves.

## Browser Smoke

Local services:

- Backend: `http://127.0.0.1:8000`
- Dashboard: `http://127.0.0.1:3000`

Checked with the tracked Playwright script:

```text
LAB_DASHBOARD_URL=http://127.0.0.1:13082 npm run qa:dashboard
desktop dashboard QA passed
mobile dashboard QA passed
```

- Page loaded with title `AI Reliability Platform`.
- `Ingest Corpus` showed 4 documents and 12 chunks.
- `Run Query` returned cited `model-release.md` evidence.
- `Run Eval` showed provider, 4/4 passed, 0 failed, average latency, average coverage,
  and estimated cost.
- Desktop and mobile viewports had no horizontal overflow.
- Browser console check returned 0 errors and 0 warnings.

## Eval Artifact

Representative deterministic eval artifact:

- [evaluation-deterministic-20260520T072345Z.md](evaluation-deterministic-20260520T072345Z.md)
- [evaluation-deterministic-20260520T072345Z.json](evaluation-deterministic-20260520T072345Z.json)
