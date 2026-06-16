#!/usr/bin/env python3
"""
Stop hook: leaves a debug marker and a log line.

REDESIGN vs the Claude port.

Claude's `memory-save.py` blocks the first stop and injects a continuation
prompt that asks the agent to update MEMORY.md. WrongStack's Stop event is
"side effects only" -- `decision: "block"` is ignored. We therefore cannot
gate the agent on every turn; instead we:

1. Write a session-keyed marker at `~/.cli-tweaks/.stop-reminded/<sid>`.
2. Append one line to `~/.cli-tweaks/logs/memory-save.log`.
3. Emit no outcome JSON (WrongStack would discard anything we tried).

The agent's "save learnings" reminder now lives in `session-start.py`'s
additionalContext, where the model sees it once per session and on every
re-injection. A subsequent session that picks up the same sessionId will
see a soft "previous stop was reminded but did not update" note in
session-start and can decide whether anything is still worth saving.

The MEMORY template is intentionally NOT embedded here -- the reminder is
system-prompt-level, not event-level, because that is the only place
WrongStack actually surfaces it.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402


def main() -> int:
    data = _compat.readInput()
    cwd = data.get("cwd") or os.getcwd()
    sessionId = data.get("session_id")
    projectName = _compat.resolveProjectName(cwd, sessionId)
    _compat.writeStopMarker(sessionId, projectName)
    # No outcome. WrongStack would ignore a block here, and emitAllow is
    # semantically misleading (Stop has no "allow" decision).
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
