from __future__ import annotations

import re

from ai_reliability_lab.models import Answer, Citation, RetrievedChunk

_SENSITIVE_TERMS = {"admin", "credential", "credentials", "key", "password", "secret", "token"}
_SENSITIVE_ACTION_TERMS = {
    "display",
    "dump",
    "extract",
    "give",
    "ignore",
    "list",
    "print",
    "reveal",
    "return",
    "share",
    "show",
}


class DeterministicAnswerComposer:
    def compose(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> Answer:
        useful_chunks = [chunk for chunk in retrieved_chunks if chunk.score > 0]
        if _asks_for_sensitive_information(question):
            return Answer(
                answer=(
                    "I cannot retrieve or expose sensitive credentials, tokens, keys, "
                    "or secrets. I can help summarize rotation or incident-response "
                    "guidance when the corpus contains that policy."
                ),
                citations=[],
                source_coverage=0.0,
                refused=True,
            )
        if not useful_chunks:
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


def _asks_for_sensitive_information(question: str) -> bool:
    question_terms = set(re.findall(r"[a-z0-9_]+", question.lower()))
    requested_sensitive_terms = question_terms & _SENSITIVE_TERMS
    if not requested_sensitive_terms:
        return False

    asks_to_extract = bool(question_terms & _SENSITIVE_ACTION_TERMS)
    asks_for_named_secret = "admin" in question_terms and bool(
        requested_sensitive_terms - {"admin"}
    )
    return asks_to_extract or asks_for_named_secret
