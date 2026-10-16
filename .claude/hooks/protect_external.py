"""PreToolUse hook: block changes under data/external/.

Exit 2 blocks the tool call and shows stderr to Claude. The Bash check is a
conservative heuristic, not a security boundary.
"""

import json
import os
import re
import sys
from pathlib import PurePosixPath
from typing import Any

PROTECTED = ("data", "external")
MUTATING = re.compile(
    r"(^|[\s;&|(`])(rm|rmdir|mv|cp|ln|touch|truncate|tee|chmod|chown|install"
    r"|unlink|dd|rsync)(?=\s)"
    r"|\bsed\s+(-\S+\s+)*-i"
    r"|\bgit\s+(rm|mv|checkout|restore|clean|reset)\b"
    r"|-delete\b"
    r"|>"
)


def is_protected(path: str) -> bool:
    """Return True if path resolves to data/external/ or anything below it."""
    parts = PurePosixPath(os.path.realpath(path).replace("\\", "/")).parts
    return any(parts[i : i + 2] == PROTECTED for i in range(len(parts) - 1))


def command_mutates_protected(command: str) -> bool:
    """Return True if a shell command names data/external/ and may write."""
    return "/".join(PROTECTED) in command.replace("\\", "/") and bool(
        MUTATING.search(command)
    )


def check(event: dict[str, Any]) -> str | None:
    """Return a reason to block the tool call, or None to allow it."""
    tool_input = event.get("tool_input", {})
    if event.get("tool_name") == "Bash":
        if command_mutates_protected(tool_input.get("command", "")):
            return "Shell command may modify data/external/, which is immutable."
        return None
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if path and is_protected(path):
        return f"{path} is under data/external/, which is immutable."
    return None


def main() -> int:
    reason = check(json.load(sys.stdin))
    if reason:
        print(f"{reason} Ask the user to make this change.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
