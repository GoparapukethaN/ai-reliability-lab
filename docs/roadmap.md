# Roadmap

This is the honest next-step list I would use if I kept building the platform.

## Reliability

- Add retrieval-only evals so ranking regressions are visible before answer generation.
- Add prompt-injection evals with source-conflict cases.
- Track per-case eval history and trend lines.
- Add thresholds for pass rate, refusal rate, and source coverage.
- Add failure drilldowns from the dashboard to the exact trace and retrieved chunks.

## Retrieval

- Add deterministic embeddings for a keyless vector baseline.
- Compare lexical, vector, and hybrid retrieval against the same eval set.
- Add a reranker interface and measure whether it improves citation coverage.
- Add chunking experiments for max tokens, overlap, and heading strategy.

## Providers

- Expand OpenAI support beyond the current optional Responses API adapter.
- Add streaming response support.
- Add Ollama health checks and model discovery.
- Add provider-specific cost and latency summaries.
- Add provider comparison reports over a fixed eval set.

## Operations

- Add a small monitoring export for Prometheus-style metrics.
- Add a dashboard report view for saved Markdown/JSON eval artifacts.
- Add a reset/seed command for local demo databases.
- Add deployment notes for a single-machine VM or container host.

## Documentation

- Add screenshots after the public repo is ready.
- Add a short architecture video script.
- Add a deeper write-up on eval design before adding LLM providers.
