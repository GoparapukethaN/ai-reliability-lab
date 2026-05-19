PYTHON ?= python3

.PHONY: install test lint verify run ingest eval metrics

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

verify:
	./scripts/verify-local.sh

run:
	uvicorn ai_reliability_lab.app:app --reload

ingest:
	ai-lab ingest

eval:
	ai-lab eval --format markdown

metrics:
	ai-lab metrics
