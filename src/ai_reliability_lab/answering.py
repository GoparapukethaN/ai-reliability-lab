from __future__ import annotations

from ai_reliability_lab.models import Answer, Citation, RetrievedChunk

_SENSITIVE_TERMS = {"admin", "credential", "credentials", "key", "password", "secret", "token"}


class DeterministicAnswerComposer:
    def compose(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> Answer:
        useful_chunks = [chunk for chunk in retrieved_chunks if chunk.score > 0]
        if not useful_chunks or _asks_for_sensitive_information_without_evidence(
            question,
            useful_chunks,
        ):
            return Answer(
                answer=(
                    "I do not have evidence in the current corpus to answer that. "
                    "I would add source material first, then rerun retrieval and evals."
                ),
                citations=[],
                source_coverage=0.0,
                refused=True,
            )

        citations = [
            Citation(source=chunk.source, heading=chunk.heading, chunk_id=chunk.chunk_id)
            for chunk in useful_chunks
        ]
        evidence_lines = []
        for chunk in useful_chunks[:3]:
            evidence_lines.append(
                f"From {chunk.source} / {chunk.heading}: {_first_sentence(chunk.text)}"
            )

        answer = (
            f"For: {question}\n\n"
            "I would answer from the retrieved runbook evidence:\n"
            + "\n".join(f"- {line}" for line in evidence_lines)
        )
        source_coverage = round(
            len({chunk.source for chunk in useful_chunks}) / len(useful_chunks),
            3,
        )
        return Answer(
            answer=answer,
            citations=citations,
            source_coverage=source_coverage,
            refused=False,
        )


def _first_sentence(text: str) -> str:
    normalized = " ".join(text.split())
    for marker in (". ", "? ", "! "):
        if marker in normalized:
            return normalized.split(marker, 1)[0] + marker.strip()
    return normalized


def _asks_for_sensitive_information_without_evidence(
    question: str,
    chunks: list[RetrievedChunk],
) -> bool:
    question_terms = set(question.lower().split())
    requested_sensitive_terms = question_terms & _SENSITIVE_TERMS
    if not requested_sensitive_terms:
        return False

    evidence_text = " ".join(chunk.text.lower() for chunk in chunks)
    return not any(term in evidence_text for term in requested_sensitive_terms)
