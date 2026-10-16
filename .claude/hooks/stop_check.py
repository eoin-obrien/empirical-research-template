"""Stop hook: run `just check` before Claude finishes.

On failure, exit 2 sends the output back to Claude to fix. It blocks at most
once per stop, so a check Claude cannot fix does not loop.
"""

import json
import os
import subprocess
import sys
from typing import Any

TAIL_LINES = 40


def should_run(event: dict[str, Any]) -> bool:
    """Skip when Claude is already continuing because of this hook."""
    return not event.get("stop_hook_active", False)


def main() -> int:
    if not should_run(json.load(sys.stdin)):
        return 0
    result = subprocess.run(
        ["just", "check"],
        cwd=os.environ.get("CLAUDE_PROJECT_DIR"),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).splitlines()[-TAIL_LINES:]
        print("`just check` failed:\n" + "\n".join(output), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
