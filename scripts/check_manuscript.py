"""Check rendered documents and their sources for unfinished text.

Fails on:
- an unresolved `?meta:key` placeholder in rendered HTML, which Quarto emits
  for a missing or misspelled key in results/variables.yml;
- a `[CITATION NEEDED` marker in a source document.

Warns, without failing, on manuscript text that looks like a statistical
result typed by hand rather than cited through the `meta` shortcode.

Code spans, code blocks and HTML comments are ignored. Run after
`quarto render`; see docs/workflow.qmd.
"""

import re
import sys
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("paper/**/*.qmd", "docs/**/*.qmd")
MANUSCRIPT = ("paper/**/*.qmd",)

META = re.compile(r"\?meta:[\w.-]+")
CITATION_NEEDED = re.compile(r"\[CITATION NEEDED", re.IGNORECASE)
# Heuristics for hand-typed results. They warn; they never fail.
STATISTICS = {
    "p-value": re.compile(r"\bp\s*[<>=≤≥]\s*0?\.\d+"),
    "test statistic": re.compile(
        r"(\b[tFzW]|χ2|χ²)\s*\(\s*\d+(\.\d+)?(\s*,\s*\d+(\.\d+)?)?\s*\)\s*=\s*-?\d"
    ),
    "interval": re.compile(r"\bCI\s*[=:]?\s*[\[(]\s*-?\d"),
    "estimate": re.compile(
        r"(?<![\w.])(r|d|g|β|b|SE|SD|M|OR|RR|HR|R²|R\^2|η²)\s*=\s*-?\d"
    ),
}

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"(`+).+?\1")
SHORTCODE = re.compile(r"\{\{<.*?>\}\}")
COMMENT = re.compile(r"<!--.*?-->")
SKIPPED_TAGS = {"code", "pre", "script", "style"}


def source_files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    """Return documents Quarto renders: files starting with `_` are skipped."""
    return sorted(
        {
            path
            for pattern in patterns
            for path in root.glob(pattern)
            if not path.name.startswith("_")
        }
    )


def prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, text) with code, shortcodes and comments removed."""
    in_fence = False
    in_comment = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if in_comment:
            if "-->" not in line:
                continue
            line = line.split("-->", 1)[1]
            in_comment = False
        line = COMMENT.sub("", line)
        if "<!--" in line:
            line, in_comment = line.split("<!--", 1)[0], True
        yield number, SHORTCODE.sub("", INLINE_CODE.sub("", line))


class _TextExtractor(HTMLParser):
    """Collect rendered text outside code, pre, script and style elements."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIPPED_TAGS:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED_TAGS and self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.depth:
            self.chunks.append(data)


def unresolved_meta(html: str) -> list[str]:
    parser = _TextExtractor()
    parser.feed(html)
    return META.findall(" ".join(parser.chunks))


def citations_needed(text: str) -> list[int]:
    return [n for n, line in prose_lines(text) if CITATION_NEEDED.search(line)]


def typed_statistics(text: str) -> list[tuple[int, str, str]]:
    return [
        (n, kind, match.group(0))
        for n, line in prose_lines(text)
        for kind, pattern in STATISTICS.items()
        for match in pattern.finditer(line)
    ]


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for the repository at root."""
    errors: list[str] = []
    warnings: list[str] = []
    for source in source_files(root, SOURCES):
        name = source.relative_to(root)
        text = source.read_text()
        errors += [f"{name}:{n}: [CITATION NEEDED]" for n in citations_needed(text)]
        html = source.with_suffix(".html")
        if not html.is_file():
            errors.append(f"{name}: not rendered; run `just render` first")
            continue
        errors += [
            f"{html.relative_to(root)}: unresolved {key}"
            for key in unresolved_meta(html.read_text())
        ]
    for source in source_files(root, MANUSCRIPT):
        name = source.relative_to(root)
        warnings += [
            f"{name}:{n}: possible hand-typed {kind} {found!r}; cite a generated value"
            for n, kind, found in typed_statistics(source.read_text())
        ]
    return errors, warnings


def main() -> int:
    errors, warnings = check(ROOT)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Manuscript check passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
