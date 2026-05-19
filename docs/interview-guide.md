# Interview Guide

This is how I would explain the project in a technical screen or hiring-manager call.

## Short Pitch

I built an AI reliability lab around MLOps runbooks. It ingests Markdown docs, retrieves
evidence, answers with citations, refuses unsupported questions, and runs regression
evals. I kept the first version local and deterministic so the behavior is testable
without an API key.

## Why I Built It

My background is MLOps, so I wanted a project that connects the AI/ML side with the
production side I already work in: repeatable setup, evals, observability, release
thinking, and failure modes.

## Technical Decisions

- I used SQLite so the whole system is easy to run and inspect locally.
- I started with lexical retrieval because it gives a deterministic baseline before
  adding embeddings.
- I made the answer composer deterministic so tests can verify citation and refusal
  behavior without model variance.
- I added a CLI because real engineering workflows usually need scriptable paths, not
  only web endpoints.
- I track eval history and query metrics because RAG changes need regression feedback.

## Tradeoffs I Would Discuss

- Lexical retrieval is explainable but weaker than hybrid retrieval for semantic matches.
- Deterministic answers are testable but not as flexible as a real LLM provider.
- The eval set is intentionally small; it proves the loop, not broad coverage.
- SQLite is right for a lab, but a production system would likely use managed storage and
  a dedicated retrieval service.

## Next Engineering Steps

1. Add embeddings behind the retrieval interface and compare against the lexical baseline.
2. Add an optional LLM provider and measure groundedness regressions.
3. Expand evals for prompt injection, unsupported questions, and retrieval misses.
4. Add a small dashboard for query logs and eval history.
5. Add deployment with persistent storage and environment-based config.

## Resume Bullet Drafts

- Built a local AI reliability lab for MLOps runbooks with FastAPI, SQLite, deterministic
  retrieval, cited answers, refusal behavior, evals, and metrics.
- Added regression-style RAG evaluation covering grounding, monitoring evidence, and
  unsupported sensitive requests.
- Designed the system to run without an API key so retrieval and eval behavior can be
  tested from a clean local setup.
