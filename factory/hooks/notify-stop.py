#!/usr/bin/env python3
"""
Droid Stop and StopFailure hook: sends a desktop notification when the
turn ends.

No Stop hook blocks the stop, so `Stop` fires once per turn and every firing is
the real end of the turn. The memory save runs in the memory-save mod after the
turn, not as a blocking Stop hook. If a blocking Stop hook is added again, the
first firing (stop_hook_active=false) no longer ends the turn, and this hook
must then act only on the firing with stop_hook_active=true.

`StopFailure` ends the turn at once and fires only once.

This hook must never disturb the session: it always exits 0 and writes nothing to
stdout.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor
from project import sessionProjectName

SUMMARY_MAX_CHARS = 60


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

if isEnabledFor("Stop"):
    cwd = inputData.get("cwd", os.getcwd())
    projectName = sessionProjectName(cwd)
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
        subtitle="Droid CLI",
    )

sys.exit(0)
