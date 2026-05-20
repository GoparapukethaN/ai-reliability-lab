# Observability

The observability layer is intentionally built into the first version instead of added at
the end. A RAG system is hard to trust if I cannot inspect what it retrieved, what it
cited, and why it refused.

## Query Traces

Each query records:

- trace id
- question
- provider and model
- answer text
- latency
- estimated cost
- source coverage
- refusal state
- confidence
- warnings
- retrieved chunks with rank and score
- citations with source, heading, chunk id, and quote

API:

```bash
curl http://127.0.0.1:8000/traces
curl http://127.0.0.1:8000/traces/{trace_id}
```

CLI:

```bash
ai-lab traces
```

## Eval Reports

Eval runs are stored in SQLite and written as report artifacts:

- Markdown for human review
- JSON for tooling

API:

```bash
curl -X POST http://127.0.0.1:8000/eval/run
curl http://127.0.0.1:8000/reports
```

Default report directory:

```bash
artifacts/reports
```

## Metrics Summary

The metrics endpoint summarizes the current local workspace:

- query count
- eval run count
- average latency
- refusal count
- estimated cost
- provider usage
- recent eval failures

```bash
curl http://127.0.0.1:8000/metrics/summary
```

## Dashboard View

The dashboard uses these same APIs. It shows:

- corpus size
- provider availability
- query/eval counts
- average latency
- refusals
- answer diagnostics
- retrieved evidence
- eval results
- recent traces

## What I Watch First

For this project, the most useful signals are:

- Did the answer cite the expected source?
- Did unsupported or sensitive questions refuse?
- Did retrieval coverage drop after a change?
- Did eval failures appear after changing chunking, retrieval, or provider settings?
- Did an existing local database migrate cleanly after schema changes?
