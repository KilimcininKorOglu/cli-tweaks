#!/usr/bin/env python3
"""
Stop hook: reminds the agent to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks agent to save memory.
On second stop (stop_hook_active=true): allows agent to stop normally.
"""
import json
import os
import sys
from pathlib import Path

try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# If already triggered once this turn, let agent stop
stopHookActive = inputData.get("stop_hook_active", False)
if stopHookActive:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())
projectName = os.path.basename(cwd)
memoryDir = Path.home() / ".cli-tweaks" / "memory" / projectName

# Ensure memory directory exists
memoryDir.mkdir(parents=True, exist_ok=True)

# Check if memory file exists
memoryFile = memoryDir / "MEMORY.md"
hasMemory = memoryFile.exists()

if hasMemory:
    reason = (
        "Before stopping: if you learned anything new or useful in this session "
        "(build commands, architecture insights, debugging solutions, user preferences, "
        "workflow patterns), update your memory at {dir}/MEMORY.md or create/update "
        "topic files there. If nothing new was learned, just stop without changes. "
        "Keep MEMORY.md under 200 lines. IMPORTANT: Always write memory in English only."
    ).format(dir=memoryDir)
else:
    reason = (
        "Before stopping: this is a new project with no memory yet. "
        "Create {dir}/MEMORY.md with key learnings from this session: "
        "project overview, build/test commands, architecture notes, "
        "user preferences you observed. Keep it concise (under 200 lines). "
        "IMPORTANT: Always write memory in English only. "
        "If this was a trivial session with nothing worth remembering, just stop."
    ).format(dir=memoryDir)

output = {
    "decision": "block",
    "reason": reason,
}
print(json.dumps(output))
sys.exit(0)
