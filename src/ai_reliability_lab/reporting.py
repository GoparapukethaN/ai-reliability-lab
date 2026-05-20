from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from ai_reliability_lab.models import EvalReport


@dataclass(frozen=True)
class ReportArtifact:
    kind: str
    path: str
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def format_eval_report_markdown(report: EvalReport) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"- Provider: {report.provider}",
        f"- Total: {report.total}",
        f"- Passed: {report.passed}",
        f"- Failed: {report.failed}",
        f"- Average latency: {report.average_latency_ms:.2f} ms",
        f"- Average source coverage: {report.average_source_coverage:.2f}",
        f"- Estimated cost: ${report.estimated_total_cost_usd:.6f}",
        "",
        "| Case | Status | Latency (ms) | Coverage | Cost | Reason | Sources | Missing terms |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for result in report.results:
        status = "Passed" if result.passed else "Failed"
        sources = ", ".join(result.matched_sources) if result.matched_sources else "None"
        missing = ", ".join(result.missing_terms) if result.missing_terms else "None"
        lines.append(
            f"| {result.case_id} | {status} | {result.latency_ms:.2f} | "
            f"{result.source_coverage:.2f} | ${result.estimated_cost_usd:.6f} | "
            f"{result.reason} | {sources} | {missing} |"
        )
    return "\n".join(lines) + "\n"


def save_eval_report(report: EvalReport, report_dir: Path) -> ReportArtifact:
    report_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stem = f"evaluation-{report.provider}-{created_at}"
    markdown_path = report_dir / f"{stem}.md"
    json_path = report_dir / f"{stem}.json"
    markdown_path.write_text(format_eval_report_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return ReportArtifact(
        kind="evaluation",
        path=str(markdown_path),
        created_at=created_at,
    )


def list_report_artifacts(report_dir: Path) -> list[ReportArtifact]:
    if not report_dir.exists():
        return []
    artifacts: list[ReportArtifact] = []
    for path in sorted(report_dir.glob("*.md"), reverse=True):
        kind = path.name.split("-", 1)[0]
        artifacts.append(
            ReportArtifact(
                kind=kind,
                path=str(path),
                created_at=datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            )
        )
    return artifacts
