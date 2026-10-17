# Every uv command uses uv.lock as committed. Run `uv lock` to change it.
export UV_LOCKED := "1"

default:
    @just --list

# Install the locked environment.
setup:
    uv sync

format:
    uv run ruff format .

lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy

# Unit tests only; tests/integrity runs under `verify`.
test:
    uv run pytest

# Fast Python checks. Needs no Quarto.
check: lint test

# Run the canonical analysis. Replace this body with the project's pipeline.
analyse:
    @echo "No analysis defined. Add the project's pipeline to the analyse recipe." >&2
    @exit 1

# Repository integrity, render and manuscript checks. Does not run the analysis.
verify:
    uv run python scripts/protocol_lock.py verify
    uv run pytest tests/integrity
    just render
    uv run python scripts/check_manuscript.py

render:
    quarto render --to html

pdf:
    quarto render paper/index.qmd --to pdf

prose:
    vale --glob='*.{md,qmd}' paper docs

freeze-protocol:
    uv run python scripts/protocol_lock.py freeze

all: check verify
