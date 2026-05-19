# Case Study: AI Reliability Lab

## Problem

RAG demos are easy to build, but they often hide the questions that matter in production:

- What evidence did the answer use?
- What happens when there is no evidence?
- How do I know a retrieval or prompt change did not make quality worse?
- Can the system be run and tested without depending on an external model provider?

I built this lab to explore those questions from an MLOps point of view.

## Constraints

- The project should run locally without an API key.
- Behavior should be testable from a clean local setup.
- Answers should cite source chunks.
- Unsupported or sensitive requests should refuse instead of guessing.
- The implementation should be small enough to explain in an interview.

## Design

The system ingests Markdown MLOps runbooks, chunks them by heading, stores metadata in
SQLite, retrieves relevant chunks, and composes an answer from the retrieved evidence.
The first version uses deterministic lexical retrieval and deterministic answer
composition so failures are easy to inspect.

The eval suite checks four behaviors:

- rollback questions cite model-release evidence
- out-of-corpus questions refuse
- monitoring questions cite latency evidence
- sensitive requests refuse without explicit evidence

## Local Results

On the included sample corpus, the local eval suite currently passes 4 of 4 cases:

| Case | Expected behavior |
| --- | --- |
| `rollback-grounding` | cite rollback/model registry evidence |
| `no-evidence-refusal` | refuse unsupported HR-style question |
| `monitoring-latency` | cite p95 latency monitoring evidence |
| `sensitive-request-refusal` | refuse admin-token request |

These are local regression checks, not production metrics. I would expand them before
treating this as a real quality bar.

## What I Learned

The most useful part of this project was forcing the RAG workflow to expose its evidence.
Once citations and evals are required, weak retrieval becomes much easier to see. It also
becomes clear why deterministic baselines matter: before adding a stronger LLM, I want a
stable way to know whether retrieval, refusal, and observability are working.

## Next Version

The next version I would build is a hybrid retrieval comparison:

- lexical baseline
- embedding retrieval
- reranking
- eval report comparing source hit rate, refusal behavior, and latency

That would turn the lab from a working reliability skeleton into a more serious AI/ML
experimentation project.
