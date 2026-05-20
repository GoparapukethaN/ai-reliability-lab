#!/usr/bin/env bash
set -euo pipefail

db_path="${TMPDIR:-/tmp}/ai-reliability-lab-verify.db"
rm -f "$db_path"

if [[ -x ".venv/bin/python" ]]; then
  python_cmd=".venv/bin/python"
else
  python_cmd="${PYTHON:-python3}"
fi

"$python_cmd" -m ruff check .
"$python_cmd" -m pytest

if [[ -f "frontend/package.json" ]]; then
  (cd frontend && npm run typecheck)
  (cd frontend && npm run build)
fi

"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" ingest \
  >/tmp/ai-reliability-lab-ingest.json
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" query \
  "How should I roll back a model release?" \
  >/tmp/ai-reliability-lab-query.json
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" compare \
  "How should I roll back a model release?" \
  >/tmp/ai-reliability-lab-compare.json
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" providers \
  >/tmp/ai-reliability-lab-providers.json
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" traces \
  >/tmp/ai-reliability-lab-traces.json
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" eval --format markdown \
  >/tmp/ai-reliability-lab-eval.md
"$python_cmd" -m ai_reliability_lab.cli --database-path "$db_path" metrics \
  >/tmp/ai-reliability-lab-metrics.json

"$python_cmd" - <<'PY'
from pathlib import Path

query = Path("/tmp/ai-reliability-lab-query.json").read_text()
compare = Path("/tmp/ai-reliability-lab-compare.json").read_text()
providers = Path("/tmp/ai-reliability-lab-providers.json").read_text()
traces = Path("/tmp/ai-reliability-lab-traces.json").read_text()
eval_report = Path("/tmp/ai-reliability-lab-eval.md").read_text()
metrics = Path("/tmp/ai-reliability-lab-metrics.json").read_text()

assert "model-release.md" in query
assert '"provider": "deterministic"' in compare
assert '"id": "deterministic"' in providers
assert '"trace_id":' in traces
assert "Passed: 4" in eval_report
assert '"query_count": 2' in metrics
assert '"eval_runs": 1' in metrics
PY

echo "local verification passed"
