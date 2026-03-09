#!/usr/bin/env python3
"""
Claude Code PostToolUse hook for ExitPlanMode: saves the plan to a file
and sends a cross-platform desktop notification.
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
if tool_name != "ExitPlanMode":
    sys.exit(0)

# ExitPlanMode doesn't have plan content in tool_input,
# but the plan is written to ~/.claude/plans/ by Claude Code itself.
# We send a notification and optionally copy to project directory.

cwd = input_data.get("cwd", os.getcwd())
project_name = os.path.basename(cwd)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Find the most recently modified plan file
plans_dir = Path.home() / ".claude" / "plans"
if plans_dir.exists():
    plan_files = sorted(plans_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if plan_files:
        latest_plan = plan_files[0]
        plan_name = latest_plan.stem

        # Copy to project-local plans directory
        project_plans = Path(cwd) / ".claude" / "plans"
        project_plans.mkdir(parents=True, exist_ok=True)
        dest = project_plans / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{plan_name}.md"

        content = latest_plan.read_text(encoding="utf-8")
        header = f"<!-- Saved: {timestamp} | Project: {project_name} -->\n\n"
        dest.write_text(header + content, encoding="utf-8")

        # Send cross-platform notification
        notify("Claude Code Plan Complete", f"Plan saved: {dest.name}", subtitle=project_name)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"Plan also saved to project: {dest}",
            }
        }
        print(json.dumps(output))

sys.exit(0)
