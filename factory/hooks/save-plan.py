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
from notify import notify

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

tool_name = input_data.get("tool_name", "")
if tool_name != "ExitSpecMode":
    sys.exit(0)

tool_input = input_data.get("tool_input", {})
title = tool_input.get("title", "untitled-plan")
plan = tool_input.get("plan", "")

if not plan:
    sys.exit(0)

# Derive project name from cwd
cwd = input_data.get("cwd", os.getcwd())
project_name = os.path.basename(cwd)

# Create plans directory
plans_dir = Path.home() / ".factory" / "plans" / project_name
plans_dir.mkdir(parents=True, exist_ok=True)

# Sanitize title for filename
safe_title = re.sub(r"[^\w\s-]", "", title.lower())
safe_title = re.sub(r"[\s]+", "-", safe_title).strip("-")
if not safe_title:
    safe_title = "untitled-plan"

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
filename = f"{timestamp}-{safe_title}.md"
filepath = plans_dir / filename

# Write plan file
content = f"# {title}\n\n"
content += f"*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
content += f"*Project: {project_name}*\n\n"
content += "---\n\n"
content += plan

filepath.write_text(content, encoding="utf-8")

# Send cross-platform notification
notify("Droid CLI Plan Complete", f"Plan saved: {filename}", subtitle=title)

# Output context for Droid
output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"Plan saved to: {filepath}",
    }
}
print(json.dumps(output))
sys.exit(0)
