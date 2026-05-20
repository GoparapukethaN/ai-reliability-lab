# Architecture Video Script

This is the short walkthrough I would use for a 3-5 minute project video.

## Opening

I built this project to answer one question: what does it take to move a RAG workflow
from a demo into something I can measure and debug?

The default path is local and keyless. That lets me test retrieval, citations, refusal
behavior, traces, and evals without depending on an external model provider.

## System Flow

The system starts with Markdown, text, or PDF documents. Ingestion normalizes each file,
chunks it, and stores chunk metadata in SQLite: source, heading, ordinal, checksum, token
estimate, and text.

When I ask a question, the retriever scores chunks with deterministic lexical matching.
The provider layer then receives the question and retrieved evidence. The deterministic
provider composes an extractive answer from the evidence, while optional OpenAI and
Ollama providers can be enabled for comparison.

Every answer returns citations, retrieved chunks, latency, source coverage, provider
metadata, refusal status, and a trace id.

## Reliability Layer

The important part of the project is not only answering a question. The important part is
making the answer inspectable.

The eval suite checks grounding, expected citations, refusal behavior, sensitive-request
handling, latency, and source coverage. Eval runs are saved as Markdown and JSON reports,
and the metrics summary keeps query counts, eval counts, average latency, refusals,
provider usage, and recent failures visible.

## Dashboard Flow

The dashboard gives me the core loop:

1. Ingest the sample corpus or upload a document.
2. Ask a question and inspect the answer, citations, retrieved evidence, trace id, and
   diagnostics.
3. Compare enabled providers on the same prompt and evidence.
4. Run the eval gate and inspect pass/fail cases.
5. Check metrics and recent traces.

For the demo query, I usually ask: `How should I roll back a model release?`

## Tradeoffs

I started with lexical retrieval because it is deterministic, easy to test, and does not
need an API key. That makes it a good baseline, but it also means there is room to add
embedding and hybrid retrieval later.

The deterministic provider is intentionally simple. It is not meant to sound impressive;
it is meant to make the retrieval and citation path testable. Once that path is
measurable, adding stronger providers becomes less risky.

The project also avoids claiming production traffic or adoption. The proof is local:
tests, Docker smoke checks, browser QA, report artifacts, and repeatable demo commands.

## Close

The main thing I wanted to practice is reliability before model polish. A RAG answer is
only useful if I can see what evidence it used, why it refused, how it performed, and
whether a later change made it worse.

