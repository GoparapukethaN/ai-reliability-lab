.PHONY: install test lint run ingest eval metrics

install:
	python -m pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

run:
	uvicorn ai_reliability_lab.app:app --reload

ingest:
	ai-lab ingest

eval:
	ai-lab eval --format markdown

metrics:
	ai-lab metrics
