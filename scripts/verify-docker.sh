#!/usr/bin/env bash
set -euo pipefail

backend_port="${LAB_VERIFY_BACKEND_PORT:-18080}"
frontend_port="${LAB_VERIFY_FRONTEND_PORT:-13080}"
project="ai-reliability-lab-verify-${backend_port}-${frontend_port}-$$"

if command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
else
  python_cmd="python"
fi

export LAB_BACKEND_PORT="$backend_port"
export LAB_FRONTEND_PORT="$frontend_port"
export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:${backend_port}"
export LAB_ALLOWED_ORIGINS="http://127.0.0.1:${frontend_port},http://localhost:${frontend_port},http://localhost:3000,http://127.0.0.1:3000"

cleanup() {
  docker compose -p "$project" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose -p "$project" config --quiet
docker compose -p "$project" up --build -d

"$python_cmd" - <<PY
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

backend = "http://127.0.0.1:${backend_port}"
frontend = "http://127.0.0.1:${frontend_port}"
frontend_origin = frontend


def request(method: str, url: str, payload: dict[str, object] | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        body = response.read()
        return response.status, response.headers, body


def request_json(method: str, url: str, payload: dict[str, object] | None = None):
    status, _, body = request(method, url, payload)
    return status, json.loads(body.decode())


def wait_for_json(url: str, predicate, label: str):
    last_error = None
    for _ in range(120):
        try:
            status, payload = request_json("GET", url)
            if status == 200 and predicate(payload):
                return payload
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"{label} did not become ready: {last_error}")


def wait_for_text(url: str, expected: str, label: str):
    last_error = None
    for _ in range(120):
        try:
            status, _, body = request("GET", url)
            text = body.decode(errors="replace")
            if status == 200 and expected in text:
                return text
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(1)
    raise AssertionError(f"{label} did not become ready: {last_error}")


health = wait_for_json(f"{backend}/health", lambda payload: payload["status"] == "ok", "backend")
assert health["chunks"] == 0

ingest_status, ingest = request_json("POST", f"{backend}/ingest", {})
assert ingest_status == 200
assert ingest["documents"] == 4, ingest
assert ingest["chunks"] == 12, ingest

query_status, query = request_json(
    "POST",
    f"{backend}/query",
    {"question": "How should I roll back a model release?", "limit": 5},
)
assert query_status == 200
assert query["trace_id"], query
assert query["provider"] == "deterministic", query
assert query["citations"], query
assert any(chunk["source"] == "model-release.md" for chunk in query["retrieved_chunks"]), query

metrics_status, metrics = request_json("GET", f"{backend}/metrics/summary")
assert metrics_status == 200
assert metrics["query_count"] >= 1, metrics

preflight = urllib.request.Request(
    f"{backend}/health",
    method="OPTIONS",
    headers={
        "Origin": frontend_origin,
        "Access-Control-Request-Method": "GET",
    },
)
with urllib.request.urlopen(preflight, timeout=5) as response:
    assert response.status == 200
    assert response.headers["access-control-allow-origin"] == frontend_origin

dashboard = wait_for_text(frontend, "AI Reliability", "frontend")
assert "Run Query" in dashboard
print("docker compose verification passed")
PY
