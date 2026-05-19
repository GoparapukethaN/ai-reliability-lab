from __future__ import annotations

import math
import re
from collections import Counter

from ai_reliability_lab.models import RetrievedChunk
from ai_reliability_lab.storage import SQLiteStore

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "after",
    "an",
    "and",
    "are",
    "by",
    "do",
    "does",
    "for",
    "how",
    "i",
    "is",
    "it",
    "of",
    "or",
    "should",
    "the",
    "to",
    "what",
    "when",
    "with",
}


class Retriever:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def search(self, question: str, limit: int = 5) -> list[RetrievedChunk]:
        query_terms = _tokens(question)
        if not query_terms:
            return []

        scored: list[RetrievedChunk] = []
        for chunk in self.store.all_chunks():
            chunk_terms = _tokens(f"{chunk.heading} {chunk.text}")
            term_counts = Counter(chunk_terms)
            matched_terms = sorted(set(query_terms) & set(chunk_terms))
            if not matched_terms:
                continue

            score = sum(1 + math.log(term_counts[term]) for term in matched_terms)
            score += 0.2 * len(matched_terms)
            if "rollback" in matched_terms:
                score += 1.0
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    heading=chunk.heading,
                    text=chunk.text,
                    score=round(score, 4),
                    matched_terms=matched_terms,
                )
            )

        return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]


def _tokens(text: str) -> list[str]:
    text = text.lower().replace("roll back", "rollback")
    return [
        token
        for token in _TOKEN_RE.findall(text)
        if len(token) > 2 and token not in _STOPWORDS
    ]
