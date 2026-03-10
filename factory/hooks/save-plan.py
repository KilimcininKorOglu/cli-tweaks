#!/usr/bin/env python3
"""
PostToolUse hook for ExitSpecMode: saves the plan to a file and sends a notification.

When ExitSpecMode is called, this hook:
1. Extracts the plan title and content from tool_input
2. Saves it to ~/.factory/plans/<project>/<timestamp>-<title>.md
3. Sends a macOS desktop notification
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor

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

# Derive project name from cwd
cwd = inputData.get("cwd", os.getcwd())
projectName = os.path.basename(cwd)

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
    notify("Droid CLI Plan Complete", "Plan saved: {}".format(filename), subtitle=title)

# Output context for Droid
output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"Plan saved to: {filepath}",
    }
}
print(json.dumps(output))
sys.exit(0)
