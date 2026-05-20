from __future__ import annotations

import hashlib
from pathlib import Path

from ai_reliability_lab.chunking import chunk_markdown
from ai_reliability_lab.models import IngestSummary
from ai_reliability_lab.storage import SQLiteStore


def ingest_directory(corpus_dir: Path, store: SQLiteStore) -> IngestSummary:
    markdown_files = sorted(path for path in corpus_dir.rglob("*.md") if path.is_file())
    total_chunks = 0
    sources: list[str] = []

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        source = path.relative_to(corpus_dir).as_posix()
        chunks = chunk_markdown(text, source=source)
        store.replace_document(source, checksum=_checksum(text), chunks=chunks)
        total_chunks += len(chunks)
        sources.append(source)

    return IngestSummary(documents=len(markdown_files), chunks=total_chunks, sources=sources)


def ingest_text(source: str, text: str, store: SQLiteStore) -> IngestSummary:
    safe_source = Path(source).name or "uploaded.md"
    chunks = chunk_markdown(text, source=safe_source)
    store.replace_document(safe_source, checksum=_checksum(text), chunks=chunks)
    return IngestSummary(documents=1, chunks=len(chunks), sources=[safe_source])


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
