# Roadmap

This is the honest next-step list I would use if I kept developing the lab.

## Near Term

- Add an optional hosted or local-model provider behind the existing answer composer
  interface.
- Add embedding-based retrieval and compare it against the current lexical baseline.
- Save eval reports as Markdown artifacts so changes are easier to review in pull
  requests.
- Add a lightweight dashboard for query logs, retrieved chunks, and eval history.

## MLOps Extensions

- Add model/provider configuration with environment-based secrets.
- Add Docker Compose with persistent SQLite storage.
- Add release-style regression gates for eval pass rate.
- Add latency and cost tracking once a real LLM provider is enabled.

## AI/ML Learning Extensions

- Add reranking and measure whether it improves evidence selection.
- Add chunking experiments with different max lengths and overlap.
- Add prompt-injection and unsupported-question eval cases.
- Add model cards for any local or hosted model used later.
