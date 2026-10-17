"""paper/references.bib is a controlled artifact: it parses, keys are unique,
every citation resolves, and DOIs are well formed. Parsing uses the pandoc
bundled with Quarto, so no BibTeX library is needed."""

import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

# Quarto cross-reference prefixes, which share the @key syntax with citations.
CROSSREF_PREFIXES = (
    "fig-", "tbl-", "lst-", "eq-", "sec-", "thm-", "lem-", "cor-", "prp-",
    "cnj-", "def-", "exm-", "exr-", "sol-", "rem-", "tip-", "nte-", "wrn-",
    "imp-", "cau-",
)  # fmt: skip
DOI = re.compile(r"^10\.\d{4,9}/\S+$")


class PandocError(Exception):
    """Pandoc rejected its input."""


def pandoc(*args: str) -> Any:
    result = subprocess.run(
        ["quarto", "pandoc", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise PandocError(result.stderr.strip())
    return json.loads(result.stdout)


def bib_entries(bib: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = pandoc(str(bib), "-f", "bibtex", "-t", "csljson")
    return entries


def cited_keys(documents: list[Path]) -> set[str]:
    keys: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("t") == "Cite":
                keys.update(c["citationId"] for c in node["c"][0])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    if documents:
        walk(pandoc(*map(str, documents), "-f", "markdown", "-t", "json"))
    return {k for k in keys if not k.startswith(CROSSREF_PREFIXES)}


def duplicate_keys(entries: list[dict[str, Any]]) -> set[str]:
    counts = Counter(e["id"] for e in entries)
    return {key for key, n in counts.items() if n > 1}


def malformed_dois(entries: list[dict[str, Any]]) -> dict[str, str]:
    return {
        e["id"]: e["DOI"] for e in entries if "DOI" in e and not DOI.match(e["DOI"])
    }


# The repository's own bibliography and documents.


@pytest.fixture(scope="module")
def entries(root: Path) -> list[dict[str, Any]]:
    return bib_entries(root / "paper" / "references.bib")


def test_citekeys_are_unique(entries: list[dict[str, Any]]) -> None:
    assert duplicate_keys(entries) == set()


def test_every_citation_resolves(root: Path, entries: list[dict[str, Any]]) -> None:
    documents = sorted(
        p
        for p in [*root.glob("paper/**/*.qmd"), *root.glob("docs/**/*.qmd")]
        if not p.name.startswith("_")
    )
    missing = cited_keys(documents) - {e["id"] for e in entries}
    assert missing == set(), "cited keys missing from paper/references.bib"


def test_dois_are_well_formed(entries: list[dict[str, Any]]) -> None:
    assert malformed_dois(entries) == {}


# The checks themselves.


def test_malformed_bibtex_is_rejected(tmp_path: Path) -> None:
    bib = tmp_path / "bad.bib"
    bib.write_text("@article{bad,\n  title = {Unclosed\n")
    # Match the failure, not Pandoc's message, which varies between versions.
    with pytest.raises(PandocError):
        bib_entries(bib)


def test_duplicate_keys_are_found(tmp_path: Path) -> None:
    bib = tmp_path / "dup.bib"
    bib.write_text("@misc{a, title={x}}\n@misc{a, title={y}}\n@misc{b, title={z}}\n")
    assert duplicate_keys(bib_entries(bib)) == {"a"}


@pytest.mark.parametrize(
    ("doi", "ok"),
    [
        ("10.1000/xyz123", True),
        ("10.1145/3368089.3409741", True),
        ("https://doi.org/10.1000/xyz123", False),
        ("doi:10.1000/xyz123", False),
        ("10.1000", False),
    ],
)
def test_doi_pattern(doi: str, ok: bool) -> None:
    assert (malformed_dois([{"id": "k", "DOI": doi}]) == {}) == ok


def test_citations_exclude_code_and_crossrefs(tmp_path: Path) -> None:
    doc = tmp_path / "doc.qmd"
    doc.write_text(
        "See [@smith2020; @jones2019, p. 3] and @lee2021.\n\n"
        "Compare @fig-plot and @tbl-x. Mail a@b.com.\n\n"
        "`@incode`\n\n```\n@inblock\n```\n"
    )
    assert cited_keys([doc]) == {"smith2020", "jones2019", "lee2021"}
