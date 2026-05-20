# What I Learned Building Evals Before Adding an LLM

When I started this project, the tempting path was obvious: plug in a hosted model, add a
nice chat endpoint, and make the demo feel smart.

I decided to do the opposite first.

The first version of this lab uses deterministic retrieval and a deterministic answer
composer. That sounds less impressive, but it forced the system to answer a more useful
question: can I tell whether the workflow is grounded before I add model variance?

## The Problem With Starting at the Model

If the first version depends on a strong model, it becomes harder to see what is actually
working.

A fluent answer can hide weak retrieval. A confident answer can hide missing evidence. A
good-looking demo can still fail basic reliability checks:

- Did the answer cite the right source?
- Did retrieval find the section I expected?
- Did the system refuse when the corpus had no evidence?
- Did a change improve one question while breaking another?
- Can I reproduce the result tomorrow?

Those are engineering questions, not model questions.

## Why I Started With a Baseline

The baseline in this repo is intentionally simple:

- Markdown docs are chunked by heading.
- Chunks are stored in SQLite with source metadata.
- Retrieval uses deterministic token matching.
- Answers are composed from retrieved evidence.
- Evals check grounding, refusal, monitoring evidence, and sensitive unsupported
  requests.

This makes the system easier to inspect. When an eval fails, I can look at the retrieved
chunks, matched terms, citations, and answer text without guessing whether the model
changed its behavior.

## What the Evals Catch

The current eval set is small, but it already catches the mistakes I care about early:

- answering a rollback question without model-registry evidence
- answering an out-of-corpus question instead of refusing
- missing the p95 latency evidence in the monitoring runbook
- responding to a secret-extraction request instead of refusing

That is not a complete quality system. It is a starting gate.

## What I Would Add Next

The next useful step is not just "use a better model." It is comparison:

1. lexical retrieval baseline
2. embedding retrieval
3. hybrid retrieval
4. reranking
5. hosted or local answer generation

Then I would compare source hit rate, refusal behavior, latency, and citation coverage
across each setup.

## Main Takeaway

For production AI systems, the model is only part of the reliability story. Before I care
about how polished an answer sounds, I want to know what evidence it used, what it did
when evidence was missing, and whether I can detect regressions when I change the system.

That is why this project starts with evals before a stronger LLM provider.
