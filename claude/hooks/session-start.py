#!/usr/bin/env python3
"""
SessionStart hook: locks the project name for this session and injects the
global user instructions listed in `globalInjectFiles` of ~/.claude/settings.json.

The project memory (MEMORY.md) is not loaded here: the memory-save mod loads it
at startup, resume, /clear and compaction.

The lock is written at startup and resume. After /clear and compaction the
process is the same, so an existing lock is kept and the project name does not
follow a moved cwd. Every start also resets this session's reminder counter,
because the global instructions are injected here again.

An instruction file that is missing or cannot be read, and a lock or counter
that cannot be written, is reported to the user with `systemMessage`; the rest
of the hook still runs.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from instructions import globalInjectFiles, readInstructions
from project import (
    LOCK_DIR,
    REINJECT_COUNTER_DIR,
    removeStaleProcessFiles,
    resolveProjectName,
    sessionLockFile,
)

KEEP_LOCK_SOURCES = ("clear", "compact")


def _lockProject(cwd: str, source: str, errors: list[str]) -> None:
    """Write the project name lock, keeping the lock of a running session."""
    lockFile = sessionLockFile()
    if source in KEEP_LOCK_SOURCES and lockFile.exists():
        return
    try:
        lockFile.parent.mkdir(parents=True, exist_ok=True)
        lockFile.write_text(resolveProjectName(cwd), encoding="utf-8")
    except OSError as err:
        errors.append(f"cannot write the session lock {lockFile}: {err}")


def _resetReminderCounter(errors: list[str]) -> None:
    """Start the reminder count of memory-reinject.py again for this session."""
    counterFile = REINJECT_COUNTER_DIR / str(os.getppid())
    try:
        counterFile.unlink(missing_ok=True)
    except OSError as err:
        errors.append(f"cannot reset the prompt counter {counterFile}: {err}")


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())
errors: list[str] = []

# Drop the locks and reinject counters of sessions whose process has ended.
_lockProject(cwd, inputData.get("source", ""), errors)
_resetReminderCounter(errors)
errors += removeStaleProcessFiles(LOCK_DIR)
errors += removeStaleProcessFiles(REINJECT_COUNTER_DIR)

contents = readInstructions(globalInjectFiles(errors), errors)

output: dict = {}
if contents:
    output["hookSpecificOutput"] = {
        "hookEventName": "SessionStart",
        "additionalContext": (
            "[USER-CONFIGURED GLOBAL INSTRUCTIONS]\n"
            "The user set up the preferences below in their own config and asked "
            "that they apply to every session. Treat them as the user's standing "
            "instructions and follow them.\n\n" + "\n\n---\n\n".join(contents)
        ),
    }
if errors:
    output["systemMessage"] = "session-start.py: " + "; ".join(errors)
if output:
    print(json.dumps(output))
sys.exit(0)
