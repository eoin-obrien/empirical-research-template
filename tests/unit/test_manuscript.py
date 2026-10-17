from pathlib import Path
from types import ModuleType

import pytest


def test_unresolved_meta_is_found_in_text(manuscript: ModuleType) -> None:
    html = "<p>We recruited ?meta:sample.n people.</p>"
    assert manuscript.unresolved_meta(html) == ["?meta:sample.n"]


def test_meta_in_code_is_ignored(manuscript: ModuleType) -> None:
    html = "<p>Renders as <code>?meta:key</code>.</p><pre>?meta:block</pre>"
    assert manuscript.unresolved_meta(html) == []


def test_citation_needed_is_found_with_line(manuscript: ModuleType) -> None:
    text = "First.\n\nPrior work [CITATION NEEDED: survey] exists.\n"
    assert manuscript.citations_needed(text) == [3]


@pytest.mark.parametrize(
    "text",
    [
        "Mark it as `[CITATION NEEDED: <what>]`.",
        "```\n[CITATION NEEDED: x]\n```",
        "<!-- [CITATION NEEDED: x] -->",
        "<!--\n[CITATION NEEDED: x]\n-->",
    ],
)
def test_citation_needed_in_code_or_comments_is_ignored(
    manuscript: ModuleType, text: str
) -> None:
    assert manuscript.citations_needed(text) == []


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("The effect was reliable, p < .001.", "p-value"),
        ("A difference, t(38) = 2.10, was found.", "test statistic"),
        ("The interval was CI [0.2, 0.9].", "interval"),
        ("Accuracy correlated with time, r = 0.42.", "estimate"),
    ],
)
def test_typed_statistics_warn(manuscript: ModuleType, text: str, kind: str) -> None:
    assert [k for _, k, _ in manuscript.typed_statistics(text)] == [kind]


@pytest.mark.parametrize(
    "text",
    [
        "The effect was reliable, p {{< meta result.p >}}.",
        "We use `p < .05` as the threshold in code.",
        "Participants (n = 40) took part.",
    ],
)
def test_generated_or_code_statistics_do_not_warn(
    manuscript: ModuleType, text: str
) -> None:
    assert manuscript.typed_statistics(text) == []


def test_check_reports_errors_and_warnings(
    manuscript: ModuleType, tmp_path: Path
) -> None:
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "index.qmd").write_text("Gap [CITATION NEEDED: x], r = 0.4.\n")
    (paper / "index.html").write_text("<p>?meta:missing</p>")
    (paper / "_draft.qmd").write_text("[CITATION NEEDED: ignored]\n")
    errors, warnings = manuscript.check(tmp_path)
    assert errors == [
        "paper/index.qmd:1: [CITATION NEEDED]",
        "paper/index.html: unresolved ?meta:missing",
    ]
    assert len(warnings) == 1


def test_check_requires_rendered_output(manuscript: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notes.qmd").write_text("Text.\n")
    errors, _ = manuscript.check(tmp_path)
    assert errors == ["docs/notes.qmd: not rendered; run `just render` first"]
