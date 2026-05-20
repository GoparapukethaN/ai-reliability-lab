from ai_reliability_lab.config import Settings
from ai_reliability_lab.models import RetrievedChunk
from ai_reliability_lab.providers import ProviderError, ProviderRouter


def _release_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="release:0",
        source="model-release.md",
        heading="Rollback",
        text="Rollback uses the model registry alias and previous stable version.",
        score=0.8,
        matched_terms=["rollback", "registry"],
    )


def test_router_always_exposes_deterministic_provider() -> None:
    router = ProviderRouter.from_settings()

    assert "deterministic" in [provider.id for provider in router.available()]


def test_deterministic_provider_returns_citations_for_supported_question() -> None:
    router = ProviderRouter.from_settings()

    result = router.answer(
        "How should I roll back?",
        [_release_chunk()],
        provider_id="deterministic",
    )

    assert result.provider == "deterministic"
    assert result.citations
    assert result.refused is False
    assert result.estimated_cost_usd == 0


def test_optional_providers_are_reported_as_disabled_without_credentials() -> None:
    router = ProviderRouter.from_settings()
    providers = {provider.id: provider for provider in router.available()}

    assert providers["openai"].enabled is False
    assert providers["ollama"].enabled is False


def test_openai_provider_parses_response_and_estimates_cost(monkeypatch) -> None:
    requests: list[dict[str, object]] = []

    def stub_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        requests.append({"url": url, "payload": payload, "headers": headers})
        return {
            "output_text": "Use the registry alias to roll back to the previous model. [C1]",
            "usage": {"input_tokens": 1000, "output_tokens": 500},
        }

    monkeypatch.setattr("ai_reliability_lab.providers._post_json", stub_post_json)
    router = ProviderRouter.from_settings(Settings(openai_api_key="test-key"))

    result = router.answer("How should I roll back?", [_release_chunk()], provider_id="openai")

    assert result.provider == "openai"
    assert result.model == "gpt-4.1-mini"
    assert result.citations
    assert result.estimated_cost_usd == 0.00045
    assert result.warnings == []
    assert requests[0]["url"] == "https://api.openai.com/v1/responses"
    assert requests[0]["headers"] == {"Authorization": "Bearer test-key"}


def test_ollama_provider_parses_response_and_flags_missing_citation_markers(monkeypatch) -> None:
    requests: list[dict[str, object]] = []

    def stub_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        requests.append({"url": url, "payload": payload, "headers": headers})
        return {"response": "Use the registry alias to roll back to the previous model."}

    monkeypatch.setattr("ai_reliability_lab.providers._post_json", stub_post_json)
    router = ProviderRouter.from_settings(Settings(ollama_base_url="http://localhost:11434"))

    result = router.answer("How should I roll back?", [_release_chunk()], provider_id="ollama")

    assert result.provider == "ollama"
    assert result.model == "llama3.1"
    assert result.citations == []
    assert result.estimated_cost_usd == 0.0
    assert result.refused is True
    assert result.warnings == ["missing_citation_markers"]
    assert requests[0]["url"] == "http://localhost:11434/api/generate"


def test_openai_provider_only_credits_supported_citation_markers(monkeypatch) -> None:
    def stub_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        return {
            "output_text": "Use the registry alias to roll back. [C99]",
            "usage": {"input_tokens": 1000, "output_tokens": 500},
        }

    monkeypatch.setattr("ai_reliability_lab.providers._post_json", stub_post_json)
    router = ProviderRouter.from_settings(Settings(openai_api_key="test-key"))

    result = router.answer("How should I roll back?", [_release_chunk()], provider_id="openai")

    assert result.citations == []
    assert result.refused is True
    assert result.warnings == ["unsupported_citation_markers"]


def test_openai_provider_warns_when_some_citation_markers_are_unsupported(monkeypatch) -> None:
    def stub_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        return {
            "output_text": "Use the registry alias to roll back. [C1] [C99]",
            "usage": {"input_tokens": 1000, "output_tokens": 500},
        }

    monkeypatch.setattr("ai_reliability_lab.providers._post_json", stub_post_json)
    router = ProviderRouter.from_settings(Settings(openai_api_key="test-key"))

    result = router.answer("How should I roll back?", [_release_chunk()], provider_id="openai")

    assert [citation.chunk_id for citation in result.citations] == ["release:0"]
    assert result.refused is False
    assert result.warnings == ["unsupported_citation_markers"]


def test_provider_router_surfaces_provider_errors(monkeypatch) -> None:
    def stub_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        raise ProviderError("provider unavailable")

    monkeypatch.setattr("ai_reliability_lab.providers._post_json", stub_post_json)
    router = ProviderRouter.from_settings(Settings(openai_api_key="test-key"))

    try:
        router.answer("How should I roll back?", [_release_chunk()], provider_id="openai")
    except ProviderError as exc:
        assert str(exc) == "provider unavailable"
    else:
        raise AssertionError("expected provider error")
