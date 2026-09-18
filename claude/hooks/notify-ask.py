#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for AskUserQuestion: sends a desktop notification
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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor
from project import sessionProjectName


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

if inputData.get("tool_name") != "AskUserQuestion":
    sys.exit(0)

if isEnabledFor("AskUser"):
    cwd = inputData.get("cwd", os.getcwd())
    # The notice needs only the project name, so the user can tell which
    # session is waiting. The question text adds noise, not signal.
    notify(
        "Question awaiting your answer",
        sessionProjectName(cwd),
        subtitle="Claude Code",
    )

sys.exit(0)
