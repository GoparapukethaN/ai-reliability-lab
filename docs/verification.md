# Verification

Last local verification: 2026-05-20

Command:

```bash
make verify
```

Result:

- Ruff check: clean
- Pytest: 8 passed
- CLI smoke: ingest, query, eval, and metrics completed against a temporary database

This is a local verification artifact, not a hosted CI badge. The project intentionally
runs without provider API keys so the core workflow can be checked on a clean machine.
