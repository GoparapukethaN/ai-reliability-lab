# Architecture

This project is intentionally small, but it keeps the same boundaries I would want in a
larger AI system.

## Data Flow

1. Markdown files in `data/corpus` are treated as the source of truth.
2. The ingestion step reads each file, computes a checksum, and chunks content by
   Markdown headings.
3. Chunks are stored in SQLite with source, heading, ordinal, and text metadata.
4. Retrieval scores chunks against the question using deterministic token matching.
5. The answer composer builds a cited answer from the retrieved chunks or refuses when
   there is no evidence.
6. Query and eval metadata are written back to SQLite for observability.

## Boundaries

- `ingestion` owns file discovery and document replacement.
- `chunking` owns Markdown parsing and stable chunk IDs.
- `retrieval` owns ranking and matched-term diagnostics.
- `answering` owns answer construction and refusal behavior.
- `evaluation` owns regression cases and pass/fail logic.
- `storage` owns SQLite schema and metrics persistence.
- `app` wires the system into FastAPI routes.

## Tradeoffs

I used SQLite because it makes the system easy to run and inspect locally. A larger
version would move retrieval to a vector database or hybrid search service, but SQLite is
enough for proving ingestion, persistence, and observability behavior.

The first retriever is lexical instead of embedding-based. That keeps tests deterministic
and makes failures easier to understand. The next step would be adding embeddings behind
the same retrieval interface, then comparing lexical, vector, and hybrid retrieval in the
eval runner.

The answer composer is deterministic on purpose. It is not trying to be a great language
model. It is a testable boundary that proves the system can carry citations, refusals,
and diagnostics before adding an LLM provider.

## Failure Modes I Care About

- A question retrieves the wrong runbook section.
- An answer drops the citation even when evidence exists.
- The system answers when no evidence exists.
- Evals pass even though the answer is missing required evidence.
- A retrieval change improves one case but regresses another.

