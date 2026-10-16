from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml


@pytest.fixture(scope="module")
def manifest(root: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load((root / "provenance.yml").read_text())
    return loaded


def test_manifest_has_required_sections(manifest: dict[str, Any]) -> None:
    assert {"project", "template", "sources", "protocol"} <= manifest.keys()
    assert {"files", "frozen_at", "git_commit", "sha256"} <= manifest["protocol"].keys()


def test_frozen_protocol_is_unchanged(
    root: Path, manifest: dict[str, Any], freezer: ModuleType
) -> None:
    protocol = manifest["protocol"]
    if protocol["frozen_at"] is None:
        pytest.skip("protocol not frozen")
    current = freezer.hash_files(root, list(protocol["sha256"]))
    assert current == protocol["sha256"], "frozen protocol files have changed"


# The freeze mechanism itself.


def unfrozen() -> dict[str, Any]:
    return {
        "protocol": {
            "files": ["protocol.qmd"],
            "frozen_at": None,
            "git_commit": None,
            "sha256": {},
        }
    }


def test_freeze_records_hashes_commit_and_time(
    freezer: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "protocol.qmd").write_text("plan\n")
    hashes = freezer.hash_files(tmp_path, ["protocol.qmd"])
    now = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    protocol = freezer.freeze(unfrozen(), hashes, "abc123", now)["protocol"]
    assert protocol["sha256"] == {
        "protocol.qmd": "1b4025dc7b8d27cf38df85e77b20ed44a00851a2c28b338560560d85deded8e3"
    }
    assert protocol["git_commit"] == "abc123"
    assert protocol["frozen_at"] == "2026-01-02T03:04:05+00:00"


def test_freeze_refuses_to_refreeze(freezer: ModuleType) -> None:
    manifest = unfrozen()
    manifest["protocol"]["frozen_at"] = "2026-01-01T00:00:00+00:00"
    with pytest.raises(ValueError, match="already frozen"):
        freezer.freeze(manifest, {}, "abc123", datetime.now(UTC))
