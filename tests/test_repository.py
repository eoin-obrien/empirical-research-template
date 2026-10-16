"""Repository-level invariants: required files, known layout, generated values."""

import json
from pathlib import Path
from types import ModuleType

import pytest

REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    "_quarto.yml",
    "justfile",
    "pyproject.toml",
    "provenance.yml",
    "uv.lock",
    ".python-version",
    ".claude/settings.json",
    "data/README.md",
    "results/README.md",
    "results/variables.yml",
    "scripts/generate_variables.py",
    "paper/index.qmd",
    "paper/references.bib",
    "docs/protocol.qmd",
    "docs/decisions.qmd",
    "docs/provenance.qmd",
    "docs/workflow.qmd",
]

KNOWN_DIRECTORIES = {
    "data": {"external", "interim", "processed"},
    "results": {"raw", "derived", "tables", "figures"},
}


@pytest.mark.parametrize("path", REQUIRED_FILES)
def test_required_file_exists(root: Path, path: str) -> None:
    assert (root / path).is_file()


@pytest.mark.parametrize(("parent", "expected"), KNOWN_DIRECTORIES.items())
def test_only_known_directories(root: Path, parent: str, expected: set[str]) -> None:
    found = {p.name for p in (root / parent).iterdir() if p.is_dir()}
    assert found == expected


def test_variables_file_is_a_mapping(root: Path) -> None:
    values = json.loads((root / "results" / "variables.yml").read_text())
    assert isinstance(values, dict)


def test_variables_file_matches_generator(root: Path, generator: ModuleType) -> None:
    values = json.loads((root / "results" / "variables.yml").read_text())
    assert values == generator.collect(), "run `just values`"
