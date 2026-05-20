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
.........................                                                [100%]
25 passed in 0.42s
Compiled successfully in 1152ms
Generating static pages using 4 workers (3/3) in 175ms
local verification passed
```

The gate covers Ruff, pytest, frontend typecheck, frontend production build, CLI smoke
commands, and the local deterministic eval path.

The Python tests now include mocked OpenAI/Ollama provider adapters, provider error
handling, Markdown upload, PDF upload, and empty-PDF rejection coverage.

## Compose Check

Command:

```bash
docker compose config --quiet
```

Result: exited successfully with no output.

## Browser Smoke

Local services:

- Backend: `http://127.0.0.1:8000`
- Dashboard: `http://127.0.0.1:3000`

Checked with Playwright:

- Page loaded with title `AI Reliability Platform`.
- `Ingest Corpus` showed 4 documents and 12 chunks.
- `Run Eval` showed provider, 4/4 passed, 0 failed, average latency, average coverage,
  and estimated cost.
- Browser console check returned 0 errors and 0 warnings.

## Eval Artifact

Representative deterministic eval artifact:

- [evaluation-deterministic-20260520T072345Z.md](evaluation-deterministic-20260520T072345Z.md)
- [evaluation-deterministic-20260520T072345Z.json](evaluation-deterministic-20260520T072345Z.json)
