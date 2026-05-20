# Case Study: Enterprise RAG Reliability Platform

## Problem

RAG demos are easy to build, but they often hide the questions that matter in production:

- What evidence did the answer use?
- What happens when there is no evidence?
- How do I know a retrieval or prompt change did not make quality worse?
- Can the system be run and tested without depending on an external model provider?

I built this platform to explore those questions from an MLOps point of view.

The "enterprise" label here describes the reliability workflow: ingestion, citations,
refusal behavior, eval gates, traces, reports, and dashboard inspection. It is not a
claim of production users or external adoption.

## Constraints

- The project should run locally without an API key.
- Behavior should be testable from a clean local setup.
- Answers should cite source chunks.
- Unsupported or sensitive requests should refuse instead of guessing.
- The implementation should be practical enough to demo and clear enough to explain in an
  interview.

## Design

The system ingests MLOps runbooks and uploaded documents, chunks them by heading, stores
metadata in SQLite, retrieves relevant chunks, and answers through a provider interface.
The deterministic provider is the keyless baseline. Optional OpenAI and Ollama providers
can be enabled for comparison without changing the retrieval, eval, trace, or dashboard
workflow.

The eval suite checks four behaviors:

- rollback questions cite model-release evidence
- out-of-corpus questions refuse
- monitoring questions cite latency evidence
- secret-extraction requests refuse instead of exposing credentials or tokens

## Local Results

On the included sample corpus, the local eval suite passes 4 of 4 cases:

| Case | Expected behavior |
| --- | --- |
| `rollback-grounding` | cite rollback/model registry evidence |
| `no-evidence-refusal` | refuse unsupported HR-style question |
| `monitoring-latency` | cite p95 latency monitoring evidence |
| `sensitive-request-refusal` | refuse admin-token request |

These are local regression checks, not production adoption metrics. I would expand them
before treating them as a broad quality bar.

## What I Learned

The most useful part of this project was forcing the RAG workflow to expose its evidence.
Once citations, traces, and evals are required, weak retrieval becomes much easier to see.
It also becomes clear why deterministic baselines matter: before trusting a stronger LLM,
I want a stable way to know whether retrieval, refusal, and observability are working.

## Next Version

The next version I would build is a deeper retrieval comparison:

- lexical baseline
- embedding retrieval
- reranking
- eval report comparing source hit rate, refusal behavior, and latency

That would make the platform a stronger AI/ML experimentation system while keeping the
same reliability spine: evidence, evals, traces, and observable failures.
