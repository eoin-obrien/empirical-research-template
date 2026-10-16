"""PostToolUse hook: format and lint a Python file Claude just wrote.

Exit 2 shows Ruff's output to Claude. The edit itself has already happened.
"""

import json
import subprocess
import sys
from typing import Any

PYTHON_SUFFIXES = (".py", ".pyi")


def python_target(event: dict[str, Any]) -> str | None:
    """Return the edited file if it is Python, else None."""
    path = event.get("tool_input", {}).get("file_path")
    if isinstance(path, str) and path.endswith(PYTHON_SUFFIXES):
        return path
    return None


def main() -> int:
    path = python_target(json.load(sys.stdin))
    if path is None:
        return 0
    for args in (["format", path], ["check", path]):
        result = subprocess.run(
            ["uv", "run", "--no-sync", "ruff", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(result.stdout + result.stderr, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
