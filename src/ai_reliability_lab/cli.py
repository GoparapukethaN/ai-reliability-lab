from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ai_reliability_lab.answering import DeterministicAnswerComposer
from ai_reliability_lab.config import Settings
from ai_reliability_lab.evaluation import default_eval_cases, run_evaluation
from ai_reliability_lab.ingestion import ingest_directory
from ai_reliability_lab.reporting import format_eval_report_markdown
from ai_reliability_lab.retrieval import Retriever
from ai_reliability_lab.storage import SQLiteStore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    settings = Settings(
        corpus_dir=args.corpus_dir,
        database_path=args.database_path,
    )
    store = SQLiteStore(settings.database_path)

    if args.command == "ingest":
        _print_json(ingest_directory(settings.corpus_dir, store).to_dict())
        return 0

    if args.command == "query":
        retriever = Retriever(store)
        composer = DeterministicAnswerComposer()
        retrieved = retriever.search(args.question, limit=args.limit)
        answer = composer.compose(args.question, retrieved)
        _print_json(
            {
                "answer": answer.answer,
                "citations": [citation.to_dict() for citation in answer.citations],
                "retrieved_chunks": [chunk.to_dict() for chunk in retrieved],
                "diagnostics": {
                    "source_coverage": answer.source_coverage,
                    "refused": answer.refused,
                    "retrieved_count": len(retrieved),
                },
            }
        )
        return 0

    if args.command == "eval":
        report = run_evaluation(
            default_eval_cases(),
            Retriever(store),
            DeterministicAnswerComposer(),
        )
        payload = report.to_dict()
        store.record_eval(
            total=report.total,
            passed=report.passed,
            failed=report.failed,
            report=payload,
        )
        if args.format == "markdown":
            print(format_eval_report_markdown(report), end="")
        else:
            _print_json(payload)
        return 0

    if args.command == "metrics":
        _print_json(store.metrics_summary())
        return 0

    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    defaults = Settings.from_env()
    parser = argparse.ArgumentParser(
        prog="ai-lab",
        description="Run the AI Reliability Lab from the terminal.",
    )
    parser.add_argument("--corpus-dir", type=Path, default=defaults.corpus_dir)
    parser.add_argument("--database-path", type=Path, default=defaults.database_path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ingest", help="Ingest the configured Markdown corpus.")

    query_parser = subparsers.add_parser("query", help="Ask a question against the corpus.")
    query_parser.add_argument("question")
    query_parser.add_argument("--limit", type=int, default=5)

    eval_parser = subparsers.add_parser("eval", help="Run the default evaluation suite.")
    eval_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    subparsers.add_parser("metrics", help="Print query/eval summary metrics.")
    return parser


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
