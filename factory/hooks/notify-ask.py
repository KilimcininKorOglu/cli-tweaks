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

HEADER_MAX_CHARS = 60


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


def _describeQuestions(toolInput: dict) -> str:
    """Return a short label for the pending questions, or an empty string.

    The label carries the first question's header so the user knows what is
    being asked without switching to the terminal. Headers are model-written
    text of unbounded length, so it is truncated.
    """
    questions = toolInput.get("questions")
    if not isinstance(questions, list) or not questions:
        return ""

    first = questions[0]
    header = first.get("header", "") if isinstance(first, dict) else ""
    if not isinstance(header, str):
        return ""
    header = " ".join(header.split())
    if not header:
        return ""
    if len(header) > HEADER_MAX_CHARS:
        header = header[:HEADER_MAX_CHARS - 1] + "…"

    remaining = len(questions) - 1
    if remaining > 0:
        return "{} (+{} more)".format(header, remaining)
    return header


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

if inputData.get("tool_name") != "AskUser":
    sys.exit(0)

if isEnabledFor("AskUser"):
    cwd = inputData.get("cwd", os.getcwd())
    projectName = _resolveProjectName(cwd)
    toolInput = inputData.get("tool_input")
    label = _describeQuestions(toolInput) if isinstance(toolInput, dict) else ""
    message = "{}: {}".format(projectName, label) if label else projectName
    notify(
        "Question awaiting your answer",
        message,
        subtitle="Droid CLI",
    )

sys.exit(0)
