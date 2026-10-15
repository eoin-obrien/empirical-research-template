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

check: lint test

render:
    quarto render

all: check render
