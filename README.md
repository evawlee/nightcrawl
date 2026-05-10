# nightcrawl

Overnight batch scheduler for multi-tenant workloads (digests, ETL exports, recurring reports).

## Layout

```
nightcrawl/    package source
tests/         baseline regression tests
conftest.py    pytest fixtures (per-test store reset)
pyproject.toml package metadata
```

## Run tests

```
pip install -e ".[dev]"
python -m pytest tests/
```
