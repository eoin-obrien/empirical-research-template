"""Freeze the protocol: record SHA-256 hashes, time and commit in provenance.yml.

Refuses if the protocol is already frozen, or if a listed file has
uncommitted changes, so the recorded commit contains exactly what was hashed.
"""

import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance.yml"


def hash_files(root: Path, paths: list[str]) -> dict[str, str]:
    return {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}


def freeze(
    manifest: dict[str, Any], hashes: dict[str, str], commit: str, now: datetime
) -> dict[str, Any]:
    protocol = manifest["protocol"]
    if protocol["frozen_at"] is not None:
        raise ValueError(
            f"Protocol already frozen at {protocol['frozen_at']}. "
            "Record changes as deviations in docs/protocol.qmd."
        )
    protocol["frozen_at"] = now.isoformat(timespec="seconds")
    protocol["git_commit"] = commit
    protocol["sha256"] = hashes
    return manifest


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> int:
    manifest = yaml.safe_load(MANIFEST.read_text())
    files: list[str] = manifest["protocol"]["files"]
    if dirty := git("status", "--porcelain", "--", *files):
        print(f"Commit these files before freezing:\n{dirty}", file=sys.stderr)
        return 1
    try:
        frozen = freeze(
            manifest,
            hash_files(ROOT, files),
            git("rev-parse", "HEAD"),
            datetime.now(UTC),
        )
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    MANIFEST.write_text(yaml.safe_dump(frozen, sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
