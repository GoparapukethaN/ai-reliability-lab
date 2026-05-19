from ai_reliability_lab.chunking import chunk_markdown


def test_chunk_markdown_keeps_heading_metadata_and_stable_ids() -> None:
    text = """# Model release runbook

Models are promoted only after offline evaluation passes.

## Rollback

Rollback uses the model registry pointer and keeps the previous stable version available.
"""

    first_pass = chunk_markdown(text, source="runbooks/model-release.md", max_chars=120)
    second_pass = chunk_markdown(text, source="runbooks/model-release.md", max_chars=120)

    assert [chunk.chunk_id for chunk in first_pass] == [
        chunk.chunk_id for chunk in second_pass
    ]
    assert first_pass[0].source == "runbooks/model-release.md"
    assert first_pass[0].heading == "Model release runbook"
    assert any(chunk.heading == "Rollback" for chunk in first_pass)
    assert all(len(chunk.text) <= 120 for chunk in first_pass)

