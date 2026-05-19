from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    corpus_dir: Path = Path("data/corpus")
    database_path: Path = Path("data/runtime/lab.db")

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            corpus_dir=Path(os.getenv("LAB_CORPUS_DIR", cls.corpus_dir)),
            database_path=Path(os.getenv("LAB_DATABASE_PATH", cls.database_path)),
        )
