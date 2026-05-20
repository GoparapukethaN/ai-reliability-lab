from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from ai_reliability_lab.config import Settings
from ai_reliability_lab.evaluation import default_eval_cases, run_evaluation
from ai_reliability_lab.ingestion import ingest_directory
from ai_reliability_lab.providers import ProviderRouter
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
    provider_router = ProviderRouter.from_settings(settings)

    if args.command == "ingest":
        _print_json(ingest_directory(settings.corpus_dir, store).to_dict())
        return 0

    if args.command == "query":
        retriever = Retriever(store)
        _print_json(
            _run_provider_query(
                question=args.question,
                limit=args.limit,
                provider_id=args.provider,
                retriever=retriever,
                provider_router=provider_router,
                store=store,
            )
        )
        return 0

    if args.command == "compare":
        retriever = Retriever(store)
        providers = args.providers or provider_router.enabled_provider_ids()
        results = [
            _run_provider_query(
                question=args.question,
                limit=args.limit,
                provider_id=provider_id,
                retriever=retriever,
                provider_router=provider_router,
                store=store,
            )
            for provider_id in providers
        ]
        _print_json({"question": args.question, "results": results})
        return 0

    if args.command == "providers":
        _print_json({"providers": [provider.to_dict() for provider in provider_router.available()]})
        return 0

    if args.command == "traces":
        _print_json(
            {
                "traces": [
                    trace.to_dict() for trace in store.list_traces(limit=args.limit)
                ]
            }
        )
        return 0

    if args.command == "eval":
        report = run_evaluation(
            default_eval_cases(),
            Retriever(store),
            provider_router,
            provider_id=args.provider,
        )
        payload = report.to_dict()
        store.record_eval(
            total=report.total,
            passed=report.passed,
            failed=report.failed,
            report=payload,
            provider=report.provider,
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
    query_parser.add_argument("--provider", default=defaults.default_provider)

    compare_parser = subparsers.add_parser("compare", help="Compare enabled answer providers.")
    compare_parser.add_argument("question")
    compare_parser.add_argument("--limit", type=int, default=5)
    compare_parser.add_argument("--providers", nargs="+")

    eval_parser = subparsers.add_parser("eval", help="Run the default evaluation suite.")
    eval_parser.add_argument("--format", choices=["json", "markdown"], default="json")
    eval_parser.add_argument("--provider", default=defaults.default_provider)
    trace_parser = subparsers.add_parser("traces", help="List recent query traces.")
    trace_parser.add_argument("--limit", type=int, default=20)
    subparsers.add_parser("providers", help="List configured answer providers.")
    subparsers.add_parser("metrics", help="Print query/eval summary metrics.")
    return parser


def _run_provider_query(
    question: str,
    limit: int,
    provider_id: str,
    retriever: Retriever,
    provider_router: ProviderRouter,
    store: SQLiteStore,
) -> dict[str, Any]:
    started = perf_counter()
    retrieved = retriever.search(question, limit=limit)
    answer = provider_router.answer(question, retrieved, provider_id=provider_id)
    latency_ms = round((perf_counter() - started) * 1000, 2)
    trace_id = store.record_query_trace(
        question=question,
        provider=provider_id,
        retrieved_chunks=retrieved,
        answer=answer,
    )
    return {
        "trace_id": trace_id,
        "provider": answer.provider,
        "model": answer.model,
        "answer": answer.answer,
        "citations": [citation.to_dict() for citation in answer.citations],
        "retrieved_chunks": [chunk.to_dict() for chunk in retrieved],
        "latency_ms": latency_ms,
        "estimated_cost_usd": answer.estimated_cost_usd,
        "warnings": answer.warnings,
        "diagnostics": {
            "source_coverage": answer.source_coverage,
            "refused": answer.refused,
            "retrieved_count": len(retrieved),
            "provider_latency_ms": answer.latency_ms,
            "confidence": answer.confidence,
        },
    }


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
