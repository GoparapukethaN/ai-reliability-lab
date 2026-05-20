from ai_reliability_lab.models import RetrievedChunk
from ai_reliability_lab.providers import ProviderRouter


def test_router_always_exposes_deterministic_provider() -> None:
    router = ProviderRouter.from_settings()

    assert "deterministic" in [provider.id for provider in router.available()]


def test_deterministic_provider_returns_citations_for_supported_question() -> None:
    chunk = RetrievedChunk(
        chunk_id="release:0",
        source="model-release.md",
        heading="Rollback",
        text="Rollback uses the model registry alias and previous stable version.",
        score=0.8,
        matched_terms=["rollback", "registry"],
    )
    router = ProviderRouter.from_settings()

    result = router.answer("How should I roll back?", [chunk], provider_id="deterministic")

    assert result.provider == "deterministic"
    assert result.citations
    assert result.refused is False
    assert result.estimated_cost_usd == 0


def test_optional_providers_are_reported_as_disabled_without_credentials() -> None:
    router = ProviderRouter.from_settings()
    providers = {provider.id: provider for provider in router.available()}

    assert providers["openai"].enabled is False
    assert providers["ollama"].enabled is False
