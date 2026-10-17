import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def code_cell(
    execution_count: int | None = None, outputs: list[Any] | None = None
) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": execution_count,
        "metadata": {},
        "outputs": outputs or [],
        "source": ["x = 1"],
    }


def write_notebook(path: Path, cells: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps({"cells": cells, "nbformat": 4, "nbformat_minor": 5}))
    return path


def test_clean_notebook_passes(notebooks: ModuleType, tmp_path: Path) -> None:
    markdown = {"cell_type": "markdown", "metadata": {}, "source": ["# Notes"]}
    path = write_notebook(tmp_path / "a.ipynb", [markdown, code_cell()])
    assert notebooks.notebook_errors(path, "a.ipynb") == []


def test_executed_cells_fail_with_cell_numbers(
    notebooks: ModuleType, tmp_path: Path
) -> None:
    output = {"output_type": "stream", "name": "stdout", "text": ["1\n"]}
    cells = [code_cell(), code_cell(execution_count=3), code_cell(outputs=[output])]
    path = write_notebook(tmp_path / "a.ipynb", cells)
    assert notebooks.notebook_errors(path, "nb/a.ipynb") == [
        "nb/a.ipynb: cell 2: execution_count is not null",
        "nb/a.ipynb: cell 3: outputs are not empty",
    ]


@pytest.mark.parametrize(
    "content",
    ["{not json", "[]", '{"nbformat": 4}'],
    ids=["invalid-json", "not-an-object", "no-cells"],
)
def test_malformed_notebook_fails(
    notebooks: ModuleType, tmp_path: Path, content: str
) -> None:
    path = tmp_path / "a.ipynb"
    path.write_text(content)
    [error] = notebooks.notebook_errors(path, "a.ipynb")
    assert error.startswith("a.ipynb: ")


def test_only_committed_notebooks_are_checked(
    notebooks: ModuleType, tmp_path: Path
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "notebooks").mkdir()
    write_notebook(tmp_path / "notebooks" / "tracked.ipynb", [code_cell(1)])
    write_notebook(tmp_path / "notebooks" / "untracked.ipynb", [code_cell(1)])
    subprocess.run(["git", "add", "notebooks/tracked.ipynb"], cwd=tmp_path, check=True)
    assert notebooks.check(tmp_path) == [
        "notebooks/tracked.ipynb: cell 1: execution_count is not null"
    ]
