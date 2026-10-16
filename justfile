default:
    @just --list

setup:
    uv sync

format:
    uv run ruff format .

lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run mypy

test:
    uv run pytest

prose:
    vale --glob='*.{md,qmd}' paper docs

check: lint test

freeze-protocol:
    uv run python scripts/freeze_protocol.py

values:
    uv run python scripts/generate_variables.py

render: values
    quarto render

all: check render
