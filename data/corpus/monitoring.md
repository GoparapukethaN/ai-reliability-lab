# Monitoring runbook

Model services should report latency, error rate, request volume, and dependency health.
For RAG systems, the service should also track retrieval coverage and citation coverage.

## Drift

Drift checks compare recent production features with the training or evaluation baseline.
The first alert should create an investigation ticket, not automatically retrain the
model.

## Latency

Track p50 and p95 latency separately. A single average hides tail latency, which is often
where user-facing AI systems feel unreliable.

