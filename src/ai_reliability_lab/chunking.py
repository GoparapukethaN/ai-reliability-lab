from __future__ import annotations

import hashlib
import re

from ai_reliability_lab.models import Chunk

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def chunk_markdown(text: str, source: str, max_chars: int = 900) -> list[Chunk]:
    sections = _sections(text)
    chunks: list[Chunk] = []
    ordinal = 0

    for heading, section_text in sections:
        for piece in _split_to_limit(section_text, max_chars):
            if not piece:
                continue
            chunk_id = _stable_chunk_id(source, ordinal, piece)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    source=source,
                    heading=heading,
                    text=piece,
                    ordinal=ordinal,
                )
            )
            ordinal += 1

    return chunks


def _sections(text: str) -> list[tuple[str, str]]:
    heading = "Document"
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        match = _HEADING_RE.match(line)
        if match:
            if buffer:
                sections.append((heading, "\n".join(buffer).strip()))
                buffer = []
            heading = match.group(2).strip()
            continue
        if line.strip():
            buffer.append(line.strip())

    if buffer:
        sections.append((heading, "\n".join(buffer).strip()))

    return sections


def _split_to_limit(text: str, max_chars: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n") if paragraph.strip()]
    pieces: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_split_words(paragraph, max_chars))
            continue

        candidate = paragraph if not current else f"{current}\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            pieces.append(current)
            current = paragraph

    if current:
        pieces.append(current)

    return pieces


def _split_words(text: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = word[:max_chars]
    if current:
        pieces.append(current)
    return pieces


def _stable_chunk_id(source: str, ordinal: int, text: str) -> str:
    digest = hashlib.sha256(f"{source}:{ordinal}:{text}".encode()).hexdigest()
    return digest[:16]
