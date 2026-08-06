#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for ExitPlanMode: sends a desktop notification when
a plan is put up for approval.

PreToolUse fires before the approval prompt blocks on the user, which is the
moment the notification is useful. PostToolUse would only fire after the user
already answered, making the notification pointless.

This hook must never block the tool: it always exits 0 and writes nothing to
stdout, so the approval prompt proceeds untouched.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor


def _resolveProjectName(cwd):
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

if inputData.get("tool_name") != "ExitPlanMode":
    sys.exit(0)

if isEnabledFor("PlanSave"):
    cwd = inputData.get("cwd", os.getcwd())
    notify(
        "Plan awaiting your approval",
        _resolveProjectName(cwd),
        subtitle="Claude Code",
    )

sys.exit(0)
