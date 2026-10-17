"""The protocol freeze and its verification, in throwaway Git repositories."""

import json
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

NOW = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
PLAN_SHA256 = "1b4025dc7b8d27cf38df85e77b20ed44a00851a2c28b338560560d85deded8e3"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def commit_all(repo: Path, message: str = "change") -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "protocol").mkdir()
    (tmp_path / "protocol" / "manifest.toml").write_text('files = ["plan.qmd"]\n')
    (tmp_path / "plan.qmd").write_text("plan\n")
    commit_all(tmp_path, "protocol")
    return tmp_path


@pytest.fixture
def frozen(repo: Path, protocol_lock: ModuleType) -> Path:
    protocol_lock.freeze(repo, NOW)
    commit_all(repo, "freeze")
    return repo


def lock_path(repo: Path) -> Path:
    return repo / "protocol" / "lock.json"


def edit_lock(repo: Path, change: Callable[[dict[str, Any]], None]) -> None:
    lock = json.loads(lock_path(repo).read_text())
    change(lock)
    lock_path(repo).write_text(json.dumps(lock))


def commit_edited_lock(
    repo: Path, protocol_lock: ModuleType, change: Callable[[dict[str, Any]], None]
) -> None:
    """Freeze, edit the lock, and commit the edited lock as the first one."""
    protocol_lock.freeze(repo, NOW)
    edit_lock(repo, change)
    commit_all(repo, "freeze")


def write_consistent_lock(repo: Path, protocol_lock: ModuleType) -> None:
    """Write a lock that matches HEAD and the files on disk, as freeze would."""
    head = git(repo, "rev-parse", "HEAD")
    lock = protocol_lock.build_lock(repo, ["plan.qmd"], head, NOW)
    lock_path(repo).write_text(json.dumps(lock, indent=2) + "\n")


# Freezing.


def test_freeze_records_time_commit_files_and_hashes(
    repo: Path, protocol_lock: ModuleType
) -> None:
    head = git(repo, "rev-parse", "HEAD")
    protocol_lock.freeze(repo, NOW)
    expected = {
        "frozen_at": "2026-01-02T03:04:05+00:00",
        "git_commit": head,
        "files": ["plan.qmd"],
        "sha256": {"plan.qmd": PLAN_SHA256},
    }
    assert lock_path(repo).read_text() == json.dumps(expected, indent=2) + "\n"


def test_freeze_refuses_when_already_frozen(
    frozen: Path, protocol_lock: ModuleType
) -> None:
    with pytest.raises(protocol_lock.ProtocolError, match="already frozen"):
        protocol_lock.freeze(frozen, NOW)


@pytest.mark.parametrize("commit_deletion", [True, False])
def test_freeze_refuses_after_a_lock_was_committed(
    frozen: Path, protocol_lock: ModuleType, commit_deletion: bool
) -> None:
    lock_path(frozen).unlink()
    (frozen / "plan.qmd").write_text("revised plan\n")
    if commit_deletion:
        commit_all(frozen, "unfreeze and revise")
    with pytest.raises(protocol_lock.ProtocolError, match="cannot be frozen again"):
        protocol_lock.freeze(frozen, NOW)
    assert not lock_path(frozen).exists()


def test_freeze_refuses_uncommitted_changes(
    repo: Path, protocol_lock: ModuleType
) -> None:
    (repo / "plan.qmd").write_text("revised plan\n")
    with pytest.raises(protocol_lock.ProtocolError, match="Commit these files"):
        protocol_lock.freeze(repo, NOW)


def test_freeze_refuses_untracked_files(repo: Path, protocol_lock: ModuleType) -> None:
    (repo / "protocol" / "manifest.toml").write_text('files = ["plan.qmd", "x.qmd"]\n')
    (repo / ".gitignore").write_text("x.qmd\n")
    commit_all(repo)
    (repo / "x.qmd").write_text("ignored, so git status does not report it\n")
    with pytest.raises(protocol_lock.ProtocolError, match="not committed"):
        protocol_lock.freeze(repo, NOW)


@pytest.mark.parametrize(
    "manifest",
    [
        "files = []\n",
        'files = ["../plan.qmd"]\n',
        'files = ["/plan.qmd"]\n',
        'files = ["plan.qmd", "plan.qmd"]\n',
        "other = 1\n",
    ],
)
def test_manifest_is_validated(
    repo: Path, protocol_lock: ModuleType, manifest: str
) -> None:
    (repo / "protocol" / "manifest.toml").write_text(manifest)
    with pytest.raises(protocol_lock.ProtocolError):
        protocol_lock.declared_files(repo)


# Verifying.


def test_unfrozen_protocol_verifies(repo: Path, protocol_lock: ModuleType) -> None:
    assert protocol_lock.verify(repo) == "Protocol not frozen."


def test_frozen_protocol_verifies(frozen: Path, protocol_lock: ModuleType) -> None:
    assert "verified 1 file(s)" in protocol_lock.verify(frozen)


def test_uncommitted_lock_verifies(repo: Path, protocol_lock: ModuleType) -> None:
    protocol_lock.freeze(repo, NOW)
    assert "verified 1 file(s)" in protocol_lock.verify(repo)


def test_changed_frozen_file_fails(frozen: Path, protocol_lock: ModuleType) -> None:
    (frozen / "plan.qmd").write_text("revised plan\n")
    with pytest.raises(protocol_lock.ProtocolError, match="have changed"):
        protocol_lock.verify(frozen)


@pytest.mark.parametrize("commit_deletion", [True, False])
def test_removed_lock_fails(
    frozen: Path, protocol_lock: ModuleType, commit_deletion: bool
) -> None:
    lock_path(frozen).unlink()
    if commit_deletion:
        commit_all(frozen, "unfreeze")
    with pytest.raises(protocol_lock.ProtocolError, match="has been removed"):
        protocol_lock.verify(frozen)


@pytest.mark.parametrize("route", ["uncommitted", "committed", "deleted-then-re-added"])
def test_replacement_lock_fails_against_the_original(
    frozen: Path, protocol_lock: ModuleType, route: str
) -> None:
    if route == "deleted-then-re-added":
        lock_path(frozen).unlink()
        commit_all(frozen, "unfreeze")
    (frozen / "plan.qmd").write_text("revised plan\n")
    commit_all(frozen, "revise")
    write_consistent_lock(frozen, protocol_lock)
    if route != "uncommitted":
        commit_all(frozen, "refreeze")
    with pytest.raises(
        protocol_lock.ProtocolError, match="differs from the lock first"
    ):
        protocol_lock.verify(frozen)


def test_restored_original_lock_verifies(
    frozen: Path, protocol_lock: ModuleType
) -> None:
    original = git(frozen, "rev-parse", "HEAD")
    write_consistent_lock(frozen, protocol_lock)
    commit_all(frozen, "replace")
    git(frozen, "checkout", "-q", original, "--", "protocol/lock.json")
    assert "verified 1 file(s)" in protocol_lock.verify(frozen)


def test_reformatted_lock_fails(frozen: Path, protocol_lock: ModuleType) -> None:
    edit_lock(frozen, lambda lock: None)  # same content, different bytes
    with pytest.raises(
        protocol_lock.ProtocolError, match="differs from the lock first"
    ):
        protocol_lock.verify(frozen)


def test_shallow_clone_is_refused(
    frozen: Path, protocol_lock: ModuleType, tmp_path_factory: pytest.TempPathFactory
) -> None:
    clone = tmp_path_factory.mktemp("clone")
    git(clone, "clone", "-q", "--depth", "1", f"file://{frozen}", ".")
    with pytest.raises(protocol_lock.ProtocolError, match="shallow clone"):
        protocol_lock.verify(clone)


# The first committed lock is canonical, so its own contents are still checked.


def test_rewritten_hash_fails_against_commit(
    repo: Path, protocol_lock: ModuleType
) -> None:
    protocol_lock.freeze(repo, NOW)
    (repo / "plan.qmd").write_text("revised plan\n")
    revised = protocol_lock.sha256(b"revised plan\n")
    edit_lock(repo, lambda lock: lock["sha256"].update({"plan.qmd": revised}))
    commit_all(repo, "freeze with the revised plan's hash")
    with pytest.raises(protocol_lock.ProtocolError, match="at commit"):
        protocol_lock.verify(repo)


def test_dropped_hash_key_fails(repo: Path, protocol_lock: ModuleType) -> None:
    commit_edited_lock(repo, protocol_lock, lambda lock: lock["sha256"].clear())
    with pytest.raises(protocol_lock.ProtocolError, match="File sets disagree"):
        protocol_lock.verify(repo)


def test_file_added_to_manifest_after_freeze_fails(
    frozen: Path, protocol_lock: ModuleType
) -> None:
    (frozen / "extra.qmd").write_text("extra\n")
    (frozen / "protocol" / "manifest.toml").write_text(
        'files = ["plan.qmd", "extra.qmd"]\n'
    )
    with pytest.raises(protocol_lock.ProtocolError, match="File sets disagree"):
        protocol_lock.verify(frozen)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (lambda lock: lock.update(frozen_at=None), "frozen_at is not an ISO 8601"),
        (lambda lock: lock.update(git_commit=None), "git_commit is not a full"),
        (lambda lock: lock.update(files=None), "files must be a non-empty list"),
        (lambda lock: lock.update(sha256=None), "sha256 must map paths"),
        (lambda lock: lock.pop("git_commit"), "must have exactly the keys"),
        (lambda lock: lock.update(extra=True), "must have exactly the keys"),
        (
            lambda lock: lock.update(frozen_at="2026-01-02T03:04:05"),
            "frozen_at has no time zone",
        ),
    ],
    ids=[
        "null-time",
        "null-commit",
        "null-files",
        "null-hashes",
        "dropped-commit",
        "extra-key",
        "naive-time",
    ],
)
def test_lock_fields_cannot_be_nulled_or_dropped(
    repo: Path,
    protocol_lock: ModuleType,
    change: Callable[[dict[str, Any]], None],
    reason: str,
) -> None:
    commit_edited_lock(repo, protocol_lock, change)
    with pytest.raises(protocol_lock.ProtocolError, match=reason):
        protocol_lock.verify(repo)


def test_missing_commit_fails(repo: Path, protocol_lock: ModuleType) -> None:
    commit_edited_lock(
        repo, protocol_lock, lambda lock: lock.update(git_commit="0" * 40)
    )
    with pytest.raises(protocol_lock.ProtocolError, match="does not exist"):
        protocol_lock.verify(repo)


def test_commit_off_history_fails(repo: Path, protocol_lock: ModuleType) -> None:
    git(repo, "checkout", "-q", "--orphan", "elsewhere")
    elsewhere = commit_all(repo, "unrelated")
    git(repo, "checkout", "-q", "main")
    commit_edited_lock(
        repo, protocol_lock, lambda lock: lock.update(git_commit=elsewhere)
    )
    with pytest.raises(protocol_lock.ProtocolError, match="not an ancestor"):
        protocol_lock.verify(repo)
