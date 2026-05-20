# Providers

The provider layer lets me compare answer generation without changing ingestion,
retrieval, evals, or tracing.

## Deterministic Local Provider

The deterministic provider is always enabled and requires no API key. It builds an
extractive answer from retrieved chunks and refuses when there is no supporting evidence.

I use it as the control group because it is:

- repeatable in tests
- free to run locally
- easy to debug
- good enough to verify citations, coverage, refusals, traces, and eval plumbing

## OpenAI Provider

The OpenAI provider is optional. It is enabled when `OPENAI_API_KEY` is set.

```bash
OPENAI_API_KEY=... OPENAI_MODEL=gpt-4.1-mini uvicorn ai_reliability_lab.app:app --reload
```

Relevant settings:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`

The provider receives the question and retrieved evidence. It must still return through
the same answer contract: answer text, citations, refusal state, confidence, warnings,
latency, and estimated cost.

Provider answers only receive citation credit for explicit evidence markers such as
`[C1]` or `[C2]` that map to retrieved chunks in the prompt. Missing markers produce a
`missing_citation_markers` warning. Markers that do not map to retrieved evidence produce
an `unsupported_citation_markers` warning and are not counted as citations.

## Ollama Provider

The Ollama provider is optional. It is enabled when `OLLAMA_BASE_URL` is set.

```bash
OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=llama3.1 \
  uvicorn ai_reliability_lab.app:app --reload
```

Relevant settings:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

## Comparison Flow

CLI:

```bash
ai-lab compare "How should I roll back a model release?"
ai-lab providers
```

API:

```bash
curl http://127.0.0.1:8000/providers
curl -X POST http://127.0.0.1:8000/query/compare \
  -H "Content-Type: application/json" \
  -d '{"question":"How should I roll back a model release?"}'
```

Dashboard:

- Select a provider in the Ask and Trace panel.
- Click `Compare` to run the question across enabled providers.

## Why This Boundary Matters

Provider quality is only one part of reliability. I want the surrounding system to keep
working even when providers change: same retrieval path, same eval cases, same traces,
same citation expectations, and same dashboard metrics. The citation parser is deliberately
strict so an optional provider cannot get grounding credit from evidence it did not mark.
