#!/usr/bin/env python3
"""
Claude Code PostToolUse hook for ExitPlanMode: sends a desktop notification
when a plan is completed.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from notify import notify, isEnabledFor


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

# Find plan file to get its name for notification
plansDir = Path.home() / ".claude" / "plans"
planName = None

if plansDir.exists():
    transcriptPath = inputData.get("transcript_path", "")
    if transcriptPath:
        slug = getSlugFromTranscript(transcriptPath)
        if slug:
            candidate = plansDir / f"{slug}.md"
            if candidate.exists():
                planName = slug

    # Fallback: most recently modified .md file
    if not planName:
        planFiles = sorted(plansDir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        if planFiles:
            planName = planFiles[0].stem

# Send notification
if planName and isEnabledFor("PlanSave"):
    notify("Plan Complete", planName, subtitle="Claude Code")

sys.exit(0)
