"""Freeze the protocol, or verify a frozen protocol.

`freeze` hashes the files declared in protocol/manifest.toml and writes
protocol/lock.json with the time, the Git commit, the file set and the
SHA-256 hashes. It refuses if a lock exists, if a lock was ever committed
in the history of HEAD, or if a declared file is not committed exactly as it
is on disk, so the commit holds what was hashed. There is no override.

`verify` passes if the protocol is unfrozen and no lock was ever committed.
Once a lock has been committed, the lock as first committed is canonical:
the lock on disk must be byte-identical to it. Every field is required and
checked against the manifest, the Git history and the working tree.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "protocol/manifest.toml"
LOCK = "protocol/lock.json"
LOCK_KEYS = {"frozen_at", "git_commit", "files", "sha256"}
COMMIT = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ProtocolError(Exception):
    """The protocol cannot be frozen, or its lock does not verify."""


def git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)


def git_text(root: Path, *args: str) -> str:
    result = git(root, *args)
    if result.returncode != 0:
        raise ProtocolError(f"git {' '.join(args)} failed: {result.stderr.decode()}")
    return result.stdout.decode().strip()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def declared_files(root: Path) -> list[str]:
    """Return the frozen files declared in the manifest, validated."""
    path = root / MANIFEST
    if not path.is_file():
        raise ProtocolError(f"{MANIFEST} is missing.")
    files = tomllib.loads(path.read_text()).get("files")
    if not isinstance(files, list) or not files:
        raise ProtocolError(f"{MANIFEST} must list at least one file under `files`.")
    for name in files:
        if not isinstance(name, str):
            raise ProtocolError(f"{MANIFEST}: {name!r} is not a path.")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or str(pure) != name:
            raise ProtocolError(
                f"{MANIFEST}: {name!r} is not a normalised relative path."
            )
    if len(set(files)) != len(files):
        raise ProtocolError(f"{MANIFEST} lists a file more than once.")
    return sorted(files)


def hash_files(root: Path, files: list[str]) -> dict[str, str]:
    missing = [f for f in files if not (root / f).is_file()]
    if missing:
        raise ProtocolError(f"Frozen files are missing: {', '.join(missing)}")
    return {f: sha256((root / f).read_bytes()) for f in files}


def build_lock(
    root: Path, files: list[str], commit: str, now: datetime
) -> dict[str, Any]:
    return {
        "frozen_at": now.isoformat(timespec="seconds"),
        "git_commit": commit,
        "files": files,
        "sha256": hash_files(root, files),
    }


def freeze(root: Path, now: datetime) -> dict[str, Any]:
    """Write the lock and return it."""
    if (root / LOCK).exists():
        raise ProtocolError(
            f"{LOCK} exists; the protocol is already frozen. "
            "Record changes as amendments in docs/amendments/."
        )
    if original := first_lock_commit(root):
        raise ProtocolError(
            f"{LOCK} was first committed at {original}; the protocol cannot be "
            f"frozen again. Restore it with `git checkout {original} -- {LOCK}` "
            "and record changes as amendments in docs/amendments/."
        )
    files = declared_files(root)
    if dirty := git_text(root, "status", "--porcelain", "--", MANIFEST, *files):
        raise ProtocolError(f"Commit these files before freezing:\n{dirty}")
    commit = git_text(root, "rev-parse", "HEAD")
    for name in [MANIFEST, *files]:
        if git(root, "cat-file", "-e", f"{commit}:{name}").returncode != 0:
            raise ProtocolError(f"{name} is not committed.")
    lock = build_lock(root, files, commit, now)
    (root / LOCK).write_text(json.dumps(lock, indent=2) + "\n")
    return lock


def load_lock(root: Path) -> dict[str, Any] | None:
    """Return the validated lock, or None if no lock file exists."""
    path = root / LOCK
    if not path.exists():
        return None
    try:
        lock = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ProtocolError(f"{LOCK} is not valid JSON: {error}") from error
    if not isinstance(lock, dict) or lock.keys() != LOCK_KEYS:
        raise ProtocolError(f"{LOCK} must have exactly the keys {sorted(LOCK_KEYS)}.")
    frozen_at, commit = lock["frozen_at"], lock["git_commit"]
    files, hashes = lock["files"], lock["sha256"]
    try:
        stamp = datetime.fromisoformat(frozen_at)
    except (TypeError, ValueError) as error:
        raise ProtocolError(f"{LOCK}: frozen_at is not an ISO 8601 time.") from error
    if stamp.tzinfo is None:
        raise ProtocolError(f"{LOCK}: frozen_at has no time zone.")
    if not isinstance(commit, str) or not COMMIT.match(commit):
        raise ProtocolError(f"{LOCK}: git_commit is not a full commit hash.")
    if (
        not isinstance(files, list)
        or not files
        or not all(isinstance(f, str) for f in files)
    ):
        raise ProtocolError(f"{LOCK}: files must be a non-empty list of paths.")
    if not isinstance(hashes, dict) or not all(
        isinstance(h, str) and SHA256.match(h) for h in hashes.values()
    ):
        raise ProtocolError(f"{LOCK}: sha256 must map paths to SHA-256 hashes.")
    return lock


def first_lock_commit(root: Path) -> str | None:
    """Return the oldest commit in the history of HEAD that added the lock.

    A shallow clone may not contain that commit, so it is refused.
    """
    if git_text(root, "rev-parse", "--is-shallow-repository") == "true":
        raise ProtocolError(
            "The repository is a shallow clone, so the lock's history cannot be "
            "checked. Fetch the full history (`git fetch --unshallow`)."
        )
    added = git_text(
        root, "log", "--full-history", "--diff-filter=A", "--format=%H", "--", LOCK
    )
    return added.splitlines()[-1] if added else None


def check_lineage(root: Path) -> None:
    """Fail unless the lock on disk is exactly the lock as first committed."""
    original = first_lock_commit(root)
    if original is None:
        return
    path = root / LOCK
    if not path.is_file():
        raise ProtocolError(
            f"{LOCK} was committed at {original} and has been removed. "
            f"Restore it with `git checkout {original} -- {LOCK}`."
        )
    if path.read_bytes() != git(root, "show", f"{original}:{LOCK}").stdout:
        raise ProtocolError(
            f"{LOCK} differs from the lock first committed at {original}, which "
            f"is canonical. Restore it with `git checkout {original} -- {LOCK}` "
            "and record changes as amendments in docs/amendments/."
        )


def verify(root: Path) -> str:
    """Return a status line, or raise ProtocolError describing the failure."""
    check_lineage(root)
    lock = load_lock(root)
    if lock is None:
        return "Protocol not frozen."

    declared = declared_files(root)
    if len(set(lock["files"])) != len(lock["files"]):
        raise ProtocolError(f"{LOCK} lists a file more than once.")
    if not (set(declared) == set(lock["files"]) == set(lock["sha256"])):
        raise ProtocolError(
            f"File sets disagree: {MANIFEST} declares {declared}, {LOCK} records "
            f"files {sorted(lock['files'])} and hashes {sorted(lock['sha256'])}."
        )

    commit = lock["git_commit"]
    if git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
        raise ProtocolError(f"Recorded commit {commit} does not exist.")
    if git(root, "merge-base", "--is-ancestor", commit, "HEAD").returncode != 0:
        raise ProtocolError(f"Recorded commit {commit} is not an ancestor of HEAD.")

    for name, recorded in sorted(lock["sha256"].items()):
        blob = git(root, "show", f"{commit}:{name}")
        if blob.returncode != 0:
            raise ProtocolError(f"{name} does not exist at commit {commit}.")
        if sha256(blob.stdout) != recorded:
            raise ProtocolError(f"{name} at commit {commit} does not match its hash.")

    current = hash_files(root, declared)
    changed = sorted(f for f in declared if current[f] != lock["sha256"][f])
    if changed:
        raise ProtocolError(
            f"Frozen files have changed: {', '.join(changed)}. Restore them and "
            "record the change as an amendment in docs/amendments/."
        )
    return (
        f"Protocol frozen at {lock['frozen_at']} ({commit[:12]}); "
        f"verified {len(declared)} file(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["freeze", "verify"])
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze":
            lock = freeze(ROOT, datetime.now(UTC))
            print(f"Froze {len(lock['files'])} file(s) at {lock['git_commit'][:12]}.")
            print(f"Commit {LOCK} now.")
        else:
            print(verify(ROOT))
    except ProtocolError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
