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
    quote: str = ""

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
class ProviderInfo:
    id: str
    label: str
    enabled: bool
    requires_key: bool
    model: str
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderAnswer:
    provider: str
    answer: str
    citations: list[Citation]
    source_coverage: float
    refused: bool
    latency_ms: float
    estimated_cost_usd: float
    warnings: list[str]
    model: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.model,
            "answer": self.answer,
            "citations": [citation.to_dict() for citation in self.citations],
            "source_coverage": self.source_coverage,
            "refused": self.refused,
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "warnings": self.warnings,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class QueryTraceSummary:
    trace_id: str
    question: str
    provider: str
    latency_ms: float
    refused: bool
    source_coverage: float
    estimated_cost_usd: float
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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
    latency_ms: float = 0.0
    source_coverage: float = 0.0
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EvalReport:
    total: int
    passed: int
    failed: int
    results: list[EvalResult]
    provider: str = "deterministic"
    average_latency_ms: float = 0.0
    average_source_coverage: float = 0.0
    estimated_total_cost_usd: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "average_latency_ms": self.average_latency_ms,
            "average_source_coverage": self.average_source_coverage,
            "estimated_total_cost_usd": self.estimated_total_cost_usd,
            "results": [result.to_dict() for result in self.results],
        }
