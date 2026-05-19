# Demo Walkthrough

This is the shortest path I use to verify the lab from a fresh local database. It
shows the full loop: ingest a small MLOps corpus, ask a grounded question, run the eval
suite, and inspect the observability summary.

## Commands

```bash
rm -f /tmp/ai-reliability-demo.db
ai-lab --database-path /tmp/ai-reliability-demo.db ingest
ai-lab --database-path /tmp/ai-reliability-demo.db query \
  "How should I roll back a model release?"
ai-lab --database-path /tmp/ai-reliability-demo.db eval --format markdown
ai-lab --database-path /tmp/ai-reliability-demo.db metrics
```

## Ingestion

```json
{
  "chunks": 12,
  "documents": 4,
  "sources": [
    "incident-response.md",
    "model-release.md",
    "monitoring.md",
    "rag-evaluation.md"
  ]
}
```

## Grounded Query

The answer includes citations and diagnostics. I trimmed the retrieved chunk text here so
the signal is easier to scan.

```json
{
  "answer": "For: How should I roll back a model release?\n\nI would answer from the retrieved runbook evidence:\n- From model-release.md / Rollback: When live metrics regress, roll back by moving the registry alias to the previous stable model.\n- From model-release.md / Model release runbook: Model releases should start with an offline evaluation report.\n- From incident-response.md / Triage: During triage, check recent deployments, data pipeline health, model registry changes, and upstream dependency errors.",
  "citations": [
    {
      "chunk_id": "e63a863ed633cd76",
      "heading": "Rollback",
      "source": "model-release.md"
    },
    {
      "chunk_id": "dacecbe2e6c027c4",
      "heading": "Model release runbook",
      "source": "model-release.md"
    },
    {
      "chunk_id": "fc8187a55d41ba82",
      "heading": "Triage",
      "source": "incident-response.md"
    }
  ],
  "diagnostics": {
    "refused": false,
    "retrieved_count": 5,
    "source_coverage": 0.6
  },
  "latency_ms": 0.33
}
```

## Eval Report

```markdown
# Evaluation Report

- Total: 4
- Passed: 4
- Failed: 0

| Case | Status | Reason | Sources | Missing terms |
| --- | --- | --- | --- | --- |
| rollback-grounding | Passed | grounded answer matched expected terms and sources | model-release.md, model-release.md, incident-response.md, model-release.md, monitoring.md | None |
| no-evidence-refusal | Passed | refused without corpus evidence | None | None |
| monitoring-latency | Passed | grounded answer matched expected terms and sources | monitoring.md, model-release.md, monitoring.md | None |
| sensitive-request-refusal | Passed | refused without corpus evidence | None | None |
```

## Metrics

```json
{
  "average_latency_ms": 0.33,
  "eval_runs": 1,
  "query_count": 1,
  "recent_failures": []
}
```

The part I care about is not the small latency number itself. It is that the system has a
place to record operational signals from the start: queries, eval runs, latency, source
coverage, and recent eval failures.
