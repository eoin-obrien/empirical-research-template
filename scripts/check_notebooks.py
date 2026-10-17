"""Check that committed Jupyter notebooks carry no execution state.

A code cell fails if its `execution_count` is not null or its `outputs` are
not empty. Clear outputs before committing. Only files tracked by Git are
checked; cells are numbered from 1, as Jupyter shows them.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def committed_notebooks(root: Path) -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.ipynb"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    paths = (root / name for name in sorted(listed.split("\0")) if name)
    return [path for path in paths if path.is_file()]  # skip deleted, not committed


def notebook_errors(path: Path, name: str) -> list[str]:
    """Return one error per problem in the notebook at path, labelled name."""
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{name}: not valid notebook JSON: {error}"]
    cells = notebook.get("cells") if isinstance(notebook, dict) else None
    if not isinstance(cells, list):
        return [f"{name}: no `cells` list; expected nbformat 4"]
    errors: list[str] = []
    for number, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        if cell.get("execution_count") is not None:
            errors.append(f"{name}: cell {number}: execution_count is not null")
        if cell.get("outputs"):
            errors.append(f"{name}: cell {number}: outputs are not empty")
    return errors


def check(root: Path) -> list[str]:
    return [
        error
        for path in committed_notebooks(root)
        for error in notebook_errors(path, path.relative_to(root).as_posix())
    ]


def main() -> int:
    errors = check(ROOT)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        print("Clear notebook outputs before committing.", file=sys.stderr)
        return 1
    print("Notebook check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
