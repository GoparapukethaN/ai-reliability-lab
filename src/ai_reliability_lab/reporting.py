from __future__ import annotations

from ai_reliability_lab.models import EvalReport


def format_eval_report_markdown(report: EvalReport) -> str:
    lines = [
        "# Evaluation Report",
        "",
        f"- Total: {report.total}",
        f"- Passed: {report.passed}",
        f"- Failed: {report.failed}",
        "",
        "| Case | Status | Reason | Sources | Missing terms |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in report.results:
        status = "Passed" if result.passed else "Failed"
        sources = ", ".join(result.matched_sources) if result.matched_sources else "None"
        missing = ", ".join(result.missing_terms) if result.missing_terms else "None"
        lines.append(
            f"| {result.case_id} | {status} | {result.reason} | {sources} | {missing} |"
        )
    return "\n".join(lines) + "\n"

