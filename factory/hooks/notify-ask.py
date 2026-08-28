#!/usr/bin/env python3
"""
PreToolUse hook for AskUser: sends a desktop notification
when a question is put to the user.

PreToolUse fires before the question prompt blocks on the user, which is the
moment the notification is useful. PostToolUse would only fire after the user
already answered, making the notification pointless. This mirrors save-plan.py,
which notifies on the same event boundary for plan approval.

This hook must never block the tool: it always exits 0 and writes nothing to
stdout, so the question prompt proceeds untouched.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor


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


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

if inputData.get("tool_name") != "AskUser":
    sys.exit(0)

if isEnabledFor("AskUser"):
    cwd = inputData.get("cwd", os.getcwd())
    # The notice needs only the project name, so the user can tell which
    # session is waiting. The question text adds noise, not signal.
    notify(
        "Question awaiting your answer",
        _resolveProjectName(cwd),
        subtitle="Droid CLI",
    )

sys.exit(0)
