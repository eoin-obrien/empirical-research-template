from pathlib import Path
from types import ModuleType

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/repo/data/external",
        "/repo/data/external/survey.csv",
        "/repo/data/external/2024/survey.csv",
    ],
)
def test_external_paths_are_protected(protect: ModuleType, path: str) -> None:
    assert protect.is_protected(path)


@pytest.mark.parametrize(
    "path",
    [
        "/repo/data/interim/survey.csv",
        "/repo/data/externals/survey.csv",
        "/repo/results/raw/run.json",
        "/repo/external/data/survey.csv",
    ],
)
def test_other_paths_are_not_protected(protect: ModuleType, path: str) -> None:
    assert not protect.is_protected(path)


def test_symlink_into_external_is_protected(
    protect: ModuleType, tmp_path: Path
) -> None:
    external = tmp_path / "data" / "external"
    external.mkdir(parents=True)
    link = tmp_path / "shortcut"
    link.symlink_to(external)
    assert protect.is_protected(str(link / "survey.csv"))


@pytest.mark.parametrize(
    "command",
    [
        "rm data/external/survey.csv",
        "mv data/external/a.csv data/interim/a.csv",
        "echo x > data/external/a.csv",
        "sed -i s/a/b/ data/external/a.csv",
        "git rm data/external/a.csv",
        "find data/external -name '*.tmp' -delete",
        "cd /repo && rm -rf /repo/data/external",
    ],
)
def test_mutating_commands_are_blocked(protect: ModuleType, command: str) -> None:
    assert protect.command_mutates_protected(command)


@pytest.mark.parametrize(
    "command",
    [
        "cat data/external/survey.csv",
        "sha256sum data/external/*",
        "ls -la data/external",
        "rm data/interim/survey.csv",
    ],
)
def test_reading_commands_are_allowed(protect: ModuleType, command: str) -> None:
    assert not protect.command_mutates_protected(command)


@pytest.mark.parametrize(
    ("event", "blocked"),
    [
        (
            {"tool_name": "Write", "tool_input": {"file_path": "/r/data/external/a"}},
            True,
        ),
        (
            {"tool_name": "Edit", "tool_input": {"file_path": "/r/data/interim/a"}},
            False,
        ),
        (
            {
                "tool_name": "NotebookEdit",
                "tool_input": {"notebook_path": "/r/data/external/a.ipynb"},
            },
            True,
        ),
        ({"tool_name": "Bash", "tool_input": {"command": "rm data/external/a"}}, True),
        ({"tool_name": "Bash", "tool_input": {"command": "ls data/external"}}, False),
    ],
)
def test_check_decides_per_tool(
    protect: ModuleType, event: dict[str, object], blocked: bool
) -> None:
    assert (protect.check(event) is not None) == blocked


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/repo/src/research/x.py", "/repo/src/research/x.py"),
        ("/repo/src/research/x.pyi", "/repo/src/research/x.pyi"),
        ("/repo/docs/workflow.qmd", None),
    ],
)
def test_ruff_targets_only_python(
    ruff_changed: ModuleType, path: str, expected: str | None
) -> None:
    event = {"tool_name": "Edit", "tool_input": {"file_path": path}}
    assert ruff_changed.python_target(event) == expected


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        ({"stop_hook_active": False}, True),
        ({"stop_hook_active": True}, False),
        ({}, True),
    ],
)
def test_stop_check_blocks_at_most_once(
    stop_check: ModuleType, event: dict[str, object], expected: bool
) -> None:
    assert stop_check.should_run(event) == expected
