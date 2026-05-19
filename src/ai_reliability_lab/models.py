from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    heading: str
    text: str
    ordinal: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class IngestSummary:
    documents: int
    chunks: int
    sources: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source: str
    heading: str
    text: str
    score: float
    matched_terms: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Citation:
    source: str
    heading: str
    chunk_id: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Answer:
    answer: str
    citations: list[Citation]
    source_coverage: float
    refused: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "citations": [citation.to_dict() for citation in self.citations],
            "source_coverage": self.source_coverage,
            "refused": self.refused,
        }


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    question: str
    required_terms: list[str]
    expected_sources: list[str]
    expect_refusal: bool = False


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    answer: str
    matched_sources: list[str]
    missing_terms: list[str]
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvalReport:
    total: int
    passed: int
    failed: int
    results: list[EvalResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "results": [result.to_dict() for result in self.results],
        }

