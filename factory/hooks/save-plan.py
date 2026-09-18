#!/usr/bin/env python3
"""
Droid PreToolUse hook for ExitSpecMode: saves the plan and sends a desktop
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
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor
from project import sessionProjectName


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

if inputData.get("tool_name") != "ExitSpecMode":
    sys.exit(0)

toolInput = inputData.get("tool_input", {})
title = toolInput.get("title", "untitled-plan")
plan = toolInput.get("plan", "")

if not plan:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())
projectName = sessionProjectName(cwd)

plansDir = Path.home() / ".factory" / "plans" / projectName
plansDir.mkdir(parents=True, exist_ok=True)

safeTitle = re.sub(r"[^\w\s-]", "", title.lower())
safeTitle = re.sub(r"[\s]+", "-", safeTitle).strip("-")
if not safeTitle:
    safeTitle = "untitled-plan"

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
filepath = plansDir / f"{timestamp}-{safeTitle}.md"

content = f"# {title}\n\n"
content += f"*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
content += f"*Project: {projectName}*\n\n"
content += "---\n\n"
content += plan

filepath.write_text(content, encoding="utf-8")

if isEnabledFor("PlanSave"):
    notify(
        "Plan awaiting your approval",
        projectName,
        subtitle="Droid CLI",
    )

sys.exit(0)
