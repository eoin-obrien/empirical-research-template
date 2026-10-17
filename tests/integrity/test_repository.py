"""Repository-level invariants: required files, known layout, provenance."""

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml

REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "LICENSING.md",
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
    "protocol/manifest.toml",
    "scripts/protocol_lock.py",
    "scripts/check_manuscript.py",
    "scripts/check_notebooks.py",
    "paper/index.qmd",
    "paper/references.bib",
    "docs/protocol.qmd",
    "docs/decisions.qmd",
    "docs/provenance.qmd",
    "docs/workflow.qmd",
    "docs/amendments/README.md",
    "docs/amendments/_template.qmd",
]

KNOWN_DIRECTORIES = {
    "data": {"external", "interim", "processed"},
    "results": {"raw", "derived", "tables", "figures", "exploratory"},
}

PLACEHOLDERS = {".gitkeep"}


@pytest.fixture(scope="module")
def provenance(root: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load((root / "provenance.yml").read_text())
    return loaded


@pytest.mark.parametrize("path", REQUIRED_FILES)
def test_required_file_exists(root: Path, path: str) -> None:
    assert (root / path).is_file()


@pytest.mark.parametrize(("parent", "expected"), KNOWN_DIRECTORIES.items())
def test_only_known_directories(root: Path, parent: str, expected: set[str]) -> None:
    found = {p.name for p in (root / parent).iterdir() if p.is_dir()}
    assert found == expected


def test_variables_file_is_a_mapping(root: Path) -> None:
    values = yaml.safe_load((root / "results" / "variables.yml").read_text())
    assert isinstance(values, dict)


def test_provenance_has_required_sections(provenance: dict[str, Any]) -> None:
    assert {"project", "template", "sources", "outputs"} <= provenance.keys()
    assert isinstance(provenance["sources"], list)
    assert isinstance(provenance["outputs"], list)


def test_every_external_file_is_recorded(
    root: Path, provenance: dict[str, Any]
) -> None:
    external = root / "data" / "external"
    on_disk = {
        p.relative_to(root).as_posix()
        for p in external.rglob("*")
        if p.is_file() and p.name not in PLACEHOLDERS
    }
    recorded = {s["path"] for s in provenance["sources"]}
    assert on_disk - recorded == set(), "record these files in provenance.yml"


def test_recorded_sources_match_their_checksums(
    root: Path, provenance: dict[str, Any]
) -> None:
    mismatched = {
        source["path"]
        for source in provenance["sources"]
        if not (root / source["path"]).is_file()
        or hashlib.sha256((root / source["path"]).read_bytes()).hexdigest()
        != source["sha256"]
    }
    assert mismatched == set(), "data/external files are missing or changed"


def test_recorded_outputs_name_existing_code(
    root: Path, provenance: dict[str, Any]
) -> None:
    missing = {
        output["path"]
        for output in provenance["outputs"]
        if not (root / output["produced_by"]).is_file()
    }
    assert missing == set(), "produced_by must name a file in the repository"
