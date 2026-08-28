#!/usr/bin/env python3
"""
Claude Code Stop and StopFailure hook: sends a desktop notification when the
turn ends.

`Stop` fires twice per turn whenever another Stop hook blocks the first stop,
which `memory-save.py` always does. The first firing carries
stop_hook_active=false and the turn continues after it, so notifying there would
announce an end that has not happened. This hook therefore acts only when
stop_hook_active is true, which is the stop that really ends the turn. Remove
that guard if `memory-save.py` ever stops being registered on `Stop`, because
then the single firing carries false.

`StopFailure` needs no such guard: an API error ends the turn at once and fires
only once.

This hook must never disturb the session: it always exits 0 and writes nothing to
stdout.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor

SUMMARY_MAX_CHARS = 60


def _resolveProjectName(cwd: str) -> str:
    """Return session-lock name, else git root basename, else cwd basename."""
    lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
    try:
        locked = lockFile.read_text(encoding="utf-8").strip()
        if locked:
            return locked
    except (FileNotFoundError, OSError):
        pass
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            return os.path.basename(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return os.path.basename(cwd)


def _summarize(message) -> str:
    """Return a one-line excerpt of the final assistant message, or "".

    The message is model-written text of unbounded length and may open with a
    markdown heading or a list marker, so the first meaningful line is stripped
    of its markup and then truncated.
    """
    if not isinstance(message, str):
        return ""
    for rawLine in message.splitlines():
        line = rawLine.strip().lstrip("#*->| ").strip()
        if not line:
            continue
        line = " ".join(line.split())
        if len(line) > SUMMARY_MAX_CHARS:
            line = line[:SUMMARY_MAX_CHARS - 1] + "…"
        return line
    return ""


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

eventName = inputData.get("hook_event_name", "Stop")
if eventName not in ("Stop", "StopFailure"):
    sys.exit(0)

# Only the second Stop of a turn is the real end. See the module docstring.
if eventName == "Stop" and not inputData.get("stop_hook_active", False):
    sys.exit(0)

if isEnabledFor("Stop"):
    cwd = inputData.get("cwd", os.getcwd())
    projectName = _resolveProjectName(cwd)
    if eventName == "StopFailure":
        # StopFailure carries `error`; the API error is what the user needs to
        # see, not whatever text the turn managed to produce before it died.
        summary = _summarize(inputData.get("error")) or _summarize(
            inputData.get("last_assistant_message")
        )
        title = "Turn failed"
        message = "{}: {}".format(projectName, summary) if summary else projectName
    else:
        # A normal turn end needs only the project name, so the user can tell
        # which session finished. The final message adds noise, not signal.
        title = "Turn finished"
        message = projectName
    notify(
        title,
        message,
        subtitle="Claude Code",
    )

sys.exit(0)
