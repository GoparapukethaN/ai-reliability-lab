# Evaluation

The eval suite is the regression gate for this project. I use it to check whether a
change improves the system or only makes the answer sound better.

## Current Cases

| Case | Type | Expected behavior |
| --- | --- | --- |
| `rollback-grounding` | Grounding | Answer from release/registry evidence and cite the model release runbook. |
| `no-evidence-refusal` | Refusal | Refuse a question that is outside the corpus. |
| `monitoring-latency` | Grounding | Cite monitoring evidence for latency and reliability signals. |
| `sensitive-request-refusal` | Safety/refusal | Refuse a request for an admin token unless evidence exists in the corpus. |

## What Gets Checked

- Required answer terms appear for grounding cases.
- Expected source files are cited.
- Unsupported questions are refused.
- Sensitive requests are refused when the corpus has no evidence.
- Provider, latency, source coverage, estimated cost, and pass/fail counts are recorded.
- Eval reports are persisted as Markdown and JSON artifacts.

## Running Evals

CLI:

```bash
ai-lab ingest
ai-lab eval --format markdown
```

API:

```bash
curl -X POST http://127.0.0.1:8000/eval/run
curl http://127.0.0.1:8000/reports
```

Dashboard:

1. Start the backend and frontend.
2. Ingest the corpus.
3. Click `Run Eval` in the Evaluation Gate panel.
4. Review pass/fail cases and matched sources.

## Metrics

- `total`, `passed`, `failed`: the core regression outcome.
- `missing_terms`: grounding terms that did not appear in the answer.
- `matched_sources`: citation sources attached to the answer.
- `provider`: the provider used for the eval run.
- `estimated_cost_usd`: provider cost estimate for the run.
- `recent_failures`: failed cases surfaced through `/metrics/summary`.

## Why This Exists

RAG systems can look impressive while quietly losing evidence, answering unsupported
questions, or changing behavior after a retriever tweak. The eval gate gives me a small
but concrete feedback loop before I add more providers or retrieval strategies.

## Next Eval Work

- Split evals into retrieval-only, answer-grounding, refusal, and injection sets.
- Add a larger corpus with ambiguous and overlapping runbook sections.
- Track per-case history over time.
- Add provider comparison thresholds.
- Add human-review notes for cases where exact required terms are too brittle.
