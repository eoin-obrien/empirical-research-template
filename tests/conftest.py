import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str) -> ModuleType:
    """Import a module from a file outside the installed package."""
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def protect() -> ModuleType:
    return load_module(".claude/hooks/protect_external.py")


@pytest.fixture(scope="session")
def ruff_changed() -> ModuleType:
    return load_module(".claude/hooks/ruff_changed.py")


@pytest.fixture(scope="session")
def stop_check() -> ModuleType:
    return load_module(".claude/hooks/stop_check.py")


@pytest.fixture(scope="session")
def generator() -> ModuleType:
    return load_module("scripts/generate_variables.py")


@pytest.fixture(scope="session")
def freezer() -> ModuleType:
    return load_module("scripts/freeze_protocol.py")
