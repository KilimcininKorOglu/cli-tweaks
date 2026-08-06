#!/usr/bin/env python3
"""
PreToolUse hook for ExitSpecMode: saves the plan and sends a desktop
notification while the plan waits for approval.

PreToolUse fires before the approval prompt blocks on the user, which is the
moment the notification is useful. PostToolUse would only fire after the user
already answered, making the notification pointless. The plan content is already
present in tool_input at this point, so the file is written here too, which means
a plan is archived whether or not it is later approved.

This hook must never block the tool: it always exits 0 and writes nothing to
stdout, so the approval prompt proceeds untouched.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
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

toolName = inputData.get("tool_name", "")
if toolName != "ExitSpecMode":
    sys.exit(0)

toolInput = inputData.get("tool_input", {})
title = toolInput.get("title", "untitled-plan")
plan = toolInput.get("plan", "")

if not plan:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())
projectName = _resolveProjectName(cwd)

# Create plans directory
plansDir = Path.home() / ".factory" / "plans" / projectName
plansDir.mkdir(parents=True, exist_ok=True)

# Sanitize title for filename
safeTitle = re.sub(r"[^\w\s-]", "", title.lower())
safeTitle = re.sub(r"[\s]+", "-", safeTitle).strip("-")
if not safeTitle:
    safeTitle = "untitled-plan"

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
filename = f"{timestamp}-{safeTitle}.md"
filepath = plansDir / filename

# Write plan file
content = f"# {title}\n\n"
content += f"*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
content += f"*Project: {projectName}*\n\n"
content += "---\n\n"
content += plan

filepath.write_text(content, encoding="utf-8")

# Send cross-platform notification
if isEnabledFor("PlanSave"):
    notify("Plan awaiting your approval", projectName, subtitle="Droid CLI")

sys.exit(0)
