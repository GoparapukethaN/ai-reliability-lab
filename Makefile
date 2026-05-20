PYTHON ?= python3

.PHONY: install test lint frontend-install frontend-typecheck frontend-build dashboard-check verify docker-check run ingest eval metrics

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

frontend-install:
	cd frontend && npm install

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-build:
	cd frontend && npm run build

dashboard-check:
	cd frontend && npm run qa:dashboard

verify:
	./scripts/verify-local.sh

docker-check:
	./scripts/verify-docker.sh

run:
	uvicorn ai_reliability_lab.app:app --reload

ingest:
	ai-lab ingest

eval:
	ai-lab eval --format markdown

metrics:
	ai-lab metrics
