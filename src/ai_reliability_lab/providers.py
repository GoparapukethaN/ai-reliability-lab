from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from time import perf_counter
from urllib.error import URLError
from urllib.request import Request, urlopen

from ai_reliability_lab.answering import DeterministicAnswerComposer
from ai_reliability_lab.config import Settings
from ai_reliability_lab.models import Citation, ProviderAnswer, ProviderInfo, RetrievedChunk


class ProviderError(RuntimeError):
    pass


class AnswerProvider(ABC):
    id: str

    @abstractmethod
    def info(self) -> ProviderInfo:
        raise NotImplementedError

    @abstractmethod
    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> ProviderAnswer:
        raise NotImplementedError


class DeterministicProvider(AnswerProvider):
    id = "deterministic"

    def __init__(self) -> None:
        self._composer = DeterministicAnswerComposer()

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            id=self.id,
            label="Deterministic local",
            enabled=True,
            requires_key=False,
            model="extractive-local",
            reason="Always available; no API key required.",
        )

    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> ProviderAnswer:
        started = perf_counter()
        answer = self._composer.compose(question, retrieved_chunks)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        return ProviderAnswer(
            provider=self.id,
            model="extractive-local",
            answer=answer.answer,
            citations=answer.citations,
            source_coverage=answer.source_coverage,
            refused=answer.refused,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
            warnings=[] if answer.citations or answer.refused else ["answer_without_citations"],
            confidence=0.0 if answer.refused else min(1.0, answer.source_coverage),
        )


class OpenAIProvider(AnswerProvider):
    id = "openai"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def info(self) -> ProviderInfo:
        enabled = bool(self.settings.openai_api_key)
        return ProviderInfo(
            id=self.id,
            label="OpenAI",
            enabled=enabled,
            requires_key=True,
            model=self.settings.openai_model,
            reason="OPENAI_API_KEY is configured." if enabled else "Set OPENAI_API_KEY to enable.",
        )

    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> ProviderAnswer:
        if not self.settings.openai_api_key:
            raise ProviderError("OpenAI provider is disabled because OPENAI_API_KEY is not set.")
        started = perf_counter()
        prompt = _grounded_prompt(question, retrieved_chunks)
        payload = {
            "model": self.settings.openai_model,
            "input": prompt,
        }
        response = _post_json(
            f"{self.settings.openai_base_url.rstrip('/')}/responses",
            payload,
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
        )
        answer_text = _extract_openai_text(response)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        citations = _citations_from_markers(answer_text, retrieved_chunks)
        warnings = _grounding_warnings(answer_text, retrieved_chunks, citations)
        source_coverage = _citation_source_coverage(citations)
        return ProviderAnswer(
            provider=self.id,
            model=self.settings.openai_model,
            answer=answer_text,
            citations=citations,
            source_coverage=source_coverage,
            refused=not citations,
            latency_ms=latency_ms,
            estimated_cost_usd=_estimate_openai_cost(response),
            warnings=warnings,
            confidence=0.0 if not citations else min(1.0, source_coverage),
        )


class OllamaProvider(AnswerProvider):
    id = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def info(self) -> ProviderInfo:
        enabled = bool(self.settings.ollama_base_url)
        reason = (
            "OLLAMA_BASE_URL is configured."
            if enabled
            else "Set OLLAMA_BASE_URL to enable."
        )
        return ProviderInfo(
            id=self.id,
            label="Ollama",
            enabled=enabled,
            requires_key=False,
            model=self.settings.ollama_model,
            reason=reason,
        )

    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> ProviderAnswer:
        if not self.settings.ollama_base_url:
            raise ProviderError("Ollama provider is disabled because OLLAMA_BASE_URL is not set.")
        started = perf_counter()
        payload = {
            "model": self.settings.ollama_model,
            "prompt": _grounded_prompt(question, retrieved_chunks),
            "stream": False,
        }
        response = _post_json(
            f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
            payload,
            headers={},
        )
        latency_ms = round((perf_counter() - started) * 1000, 2)
        answer_text = str(response.get("response", "")).strip()
        citations = _citations_from_markers(answer_text, retrieved_chunks)
        warnings = _grounding_warnings(answer_text, retrieved_chunks, citations)
        source_coverage = _citation_source_coverage(citations)
        return ProviderAnswer(
            provider=self.id,
            model=self.settings.ollama_model,
            answer=answer_text,
            citations=citations,
            source_coverage=source_coverage,
            refused=not citations,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
            warnings=warnings,
            confidence=0.0 if not citations else min(1.0, source_coverage),
        )


class ProviderRouter:
    def __init__(self, providers: list[AnswerProvider]) -> None:
        self._providers = {provider.id: provider for provider in providers}

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> ProviderRouter:
        resolved = settings or Settings.from_env()
        return cls(
            [
                DeterministicProvider(),
                OpenAIProvider(resolved),
                OllamaProvider(resolved),
            ]
        )

    def available(self) -> list[ProviderInfo]:
        return [provider.info() for provider in self._providers.values()]

    def enabled_provider_ids(self) -> list[str]:
        return [info.id for info in self.available() if info.enabled]

    def answer(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
        provider_id: str = "deterministic",
    ) -> ProviderAnswer:
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ProviderError(f"Unknown provider: {provider_id}")
        info = provider.info()
        if not info.enabled:
            raise ProviderError(f"{info.label} provider is disabled. {info.reason}")
        return provider.answer(question, retrieved_chunks)


def _grounded_prompt(question: str, retrieved_chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        f"[C{index}] {chunk.source} / {chunk.heading}\n{chunk.text}"
        for index, chunk in enumerate(retrieved_chunks, start=1)
    )
    return (
        "Answer the question using only the evidence below. "
        "If the evidence is insufficient, refuse briefly. Include citation markers.\n\n"
        f"Question: {question}\n\nEvidence:\n{context}"
    )


def _citations_from_markers(
    answer_text: str,
    retrieved_chunks: list[RetrievedChunk],
) -> list[Citation]:
    marker_indexes = _citation_marker_indexes(answer_text)
    citations: list[Citation] = []
    seen_chunk_ids: set[str] = set()
    for marker_index in marker_indexes:
        chunk_index = marker_index - 1
        if chunk_index < 0 or chunk_index >= len(retrieved_chunks):
            continue
        chunk = retrieved_chunks[chunk_index]
        if chunk.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk.chunk_id)
        citations.append(
            Citation(source=chunk.source, heading=chunk.heading, chunk_id=chunk.chunk_id)
        )
    return citations


def _citation_marker_indexes(answer_text: str) -> list[int]:
    indexes: list[int] = []
    for raw in re.findall(r"\[C(\d+)\]", answer_text):
        indexes.append(int(raw))
    return indexes


def _citation_source_coverage(citations: list[Citation]) -> float:
    if not citations:
        return 0.0
    return round(len({citation.source for citation in citations}) / len(citations), 3)


def _grounding_warnings(
    answer_text: str,
    retrieved_chunks: list[RetrievedChunk],
    citations: list[Citation],
) -> list[str]:
    warnings: list[str] = []
    if not retrieved_chunks:
        warnings.append("no_retrieved_evidence")
        return warnings
    marker_indexes = _citation_marker_indexes(answer_text)
    if not marker_indexes:
        warnings.append("missing_citation_markers")
    elif any(index < 1 or index > len(retrieved_chunks) for index in marker_indexes):
        warnings.append("unsupported_citation_markers")
    return warnings


def _post_json(url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **headers,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise ProviderError(f"Provider request failed: {exc}") from exc


def _extract_openai_text(response: dict[str, object]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    output = response.get("output")
    if isinstance(output, list):
        parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and isinstance(content.get("text"), str):
                    parts.append(content["text"])
        if parts:
            return "\n".join(parts).strip()
    return ""


def _estimate_openai_cost(response: dict[str, object]) -> float:
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return 0.0
    input_tokens = float(usage.get("input_tokens", 0) or 0)
    output_tokens = float(usage.get("output_tokens", 0) or 0)
    # Conservative display estimate for small-model portfolio runs.
    return round((input_tokens * 0.00000015) + (output_tokens * 0.0000006), 6)
