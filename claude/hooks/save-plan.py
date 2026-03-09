#!/usr/bin/env python3
"""
Claude Code PostToolUse hook for ExitPlanMode: saves the plan to a file
and sends a cross-platform desktop notification.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify


def getSlugFromTranscript(transcriptPath: str) -> str:
    """Extract slug from transcript file by finding first entry with slug field."""
    try:
        with open(transcriptPath, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                slug = entry.get("slug")
                if slug:
                    return slug
    except (OSError, json.JSONDecodeError):
        pass
    return ""


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

toolName = inputData.get("tool_name", "")
if toolName != "ExitPlanMode":
    sys.exit(0)

# ExitPlanMode doesn't have plan content in tool_input,
# but the plan is written to ~/.claude/plans/ by Claude Code itself.
# We send a notification and optionally copy to project directory.

cwd = inputData.get("cwd", os.getcwd())
projectName = os.path.basename(cwd)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
plansDir = Path.home() / ".claude" / "plans"

if not plansDir.exists():
    sys.exit(0)

# Try to find plan file by slug from transcript (most reliable)
planFile = None
transcriptPath = inputData.get("transcript_path", "")
if transcriptPath:
    slug = getSlugFromTranscript(transcriptPath)
    if slug:
        candidate = plansDir / f"{slug}.md"
        if candidate.exists():
            planFile = candidate

# Fallback: most recently modified .md file
if not planFile:
    planFiles = sorted(plansDir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if planFiles:
        planFile = planFiles[0]

if not planFile:
    sys.exit(0)

planName = planFile.stem

# Copy to project-local plans directory
projectPlans = Path(cwd) / ".claude" / "plans"
projectPlans.mkdir(parents=True, exist_ok=True)
dest = projectPlans / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{planName}.md"

content = planFile.read_text(encoding="utf-8")
header = f"<!-- Saved: {timestamp} | Project: {projectName} -->\n\n"
dest.write_text(header + content, encoding="utf-8")

# Send cross-platform notification
notify("Claude Code Plan Complete", f"Plan saved: {dest.name}", subtitle=projectName)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"Plan also saved to project: {dest}",
    }
}
print(json.dumps(output))

sys.exit(0)
