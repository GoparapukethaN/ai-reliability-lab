# Enterprise RAG Reliability Platform

This repo is the full backend/platform implementation behind the enterprise-style RAG
story in my portfolio.

I use "enterprise RAG" to mean the workflow shape: document ingestion, retrieved
evidence, cited answers, refusal behavior, evaluation gates, traces, metrics, report
artifacts, and a dashboard. It does not mean the project has production users or customer
adoption.

## What This Repo Provides

- FastAPI backend for ingestion, query, provider comparison, evals, traces, reports, and
  metrics.
- SQLite-backed document and trace store.
- Deterministic no-key retrieval and answer baseline.
- Optional OpenAI and Ollama provider adapters.
- Next.js dashboard for the full workflow.
- CLI commands for ingest, query, compare, eval, providers, traces, and metrics.
- Local verification with tests, frontend build checks, and CLI smoke.
- Optional Docker Compose smoke when Docker is installed.

## Public Surfaces

- Portfolio map:
  <https://github.com/GoparapukethaN/kethan-portfolio/blob/main/docs/enterprise-rag-reliability-platform.md>
- Dashboard walkthrough:
  <https://github.com/GoparapukethaN/ai-reliability-lab/blob/main/docs/demo.md#dashboard-demo>
- Verification:
  <https://github.com/GoparapukethaN/ai-reliability-lab/blob/main/docs/verification.md>
- Live supporting demo:
  <https://goparapukethan.github.io/applied-ai-eval-lab/>

## Interview Boundary

The important claim is not external adoption. The important claim is that I can explain
how the platform is designed, how it is verified, what it measures, what it refuses, and
what I would improve before using the pattern in a real production environment.
