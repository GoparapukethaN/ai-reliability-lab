from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    corpus_dir: Path = Path("data/corpus")
    database_path: Path = Path("data/runtime/lab.db")
    default_provider: str = "deterministic"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = ""
    ollama_model: str = "llama3.1"
    eval_report_dir: Path = Path("artifacts/reports")

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            corpus_dir=Path(os.getenv("LAB_CORPUS_DIR", cls.corpus_dir)),
            database_path=Path(os.getenv("LAB_DATABASE_PATH", cls.database_path)),
            default_provider=os.getenv("LAB_DEFAULT_PROVIDER", cls.default_provider),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", cls.openai_model),
            openai_base_url=os.getenv("OPENAI_BASE_URL", cls.openai_base_url),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", ""),
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
            eval_report_dir=Path(os.getenv("LAB_EVAL_REPORT_DIR", cls.eval_report_dir)),
        )
