# Evaluation

The eval suite is small by design. It is meant to prove the feedback loop, not to pretend
the system is solved.

## Current Eval Types

- **Grounding case:** asks how to roll back a model release and expects the answer to use
  release or registry evidence.
- **Refusal case:** asks for information outside the corpus and expects the system to say
  it does not have enough evidence.
- **Monitoring case:** asks which latency metric to watch and expects the answer to cite
  monitoring evidence.
- **Sensitive request case:** asks for an admin token and expects refusal unless the
  corpus explicitly contains that evidence.

## Metrics

- `passed`: the case met its expected behavior.
- `missing_terms`: required evidence terms that did not appear in the answer.
- `matched_sources`: citations attached to the answer.
- `recent_failures`: failed eval cases surfaced through the metrics endpoint.
- Markdown report output from `ai-lab eval --format markdown`.

## Why These Metrics Exist

For RAG systems, I care less about whether an answer sounds fluent and more about whether
it is traceable to evidence. That is why the first metrics are source coverage, required
terms, citation presence, and refusal behavior.

## What I Would Add Next

- A larger eval set split by retrieval, grounding, refusal, and safety behavior.
- Regression thresholds in an automated test gate.
- Prompt-injection cases.
- Side-by-side comparison of lexical, vector, and hybrid retrieval.
- Human review notes for ambiguous cases where exact string checks are too brittle.
