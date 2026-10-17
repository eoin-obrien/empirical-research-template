from pathlib import Path
from types import ModuleType


def test_committed_notebooks_are_cleared(root: Path, notebooks: ModuleType) -> None:
    assert notebooks.check(root) == [], "clear notebook outputs before committing"
