# RAG evaluation notes

Grounded answers should cite retrieved context. If the corpus does not contain evidence,
the system should refuse instead of inventing details.

## Retrieval quality

Retrieval quality can be checked by expected source, matched terms, and whether the
answer uses the right section of the runbook.

## Safety

Unsupported questions and prompt-injection attempts should be part of the evaluation set.
The system should prefer a clear refusal over an unsupported answer.

