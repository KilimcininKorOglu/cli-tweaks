#!/usr/bin/env python3
"""
Stop hook: reminds Droid to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks Droid to save memory.
On second stop (stop_hook_active=true): allows Droid to stop normally.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def _resolveProjectName(cwd):
    """Return git root basename if available, otherwise cwd basename."""
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

# If already triggered once this turn, let Droid stop
stopHookActive = inputData.get("stop_hook_active", False)
if stopHookActive:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())

# Read locked project name from session start, fallback to resolving fresh
lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
try:
    projectName = lockFile.read_text(encoding="utf-8").strip()
except (FileNotFoundError, OSError):
    projectName = _resolveProjectName(cwd)

memoryDir = Path.home() / ".cli-tweaks" / "memory" / projectName

# Ensure memory directory exists
memoryDir.mkdir(parents=True, exist_ok=True)

# Check if memory file exists
memoryFile = memoryDir / "MEMORY.md"
hasMemory = memoryFile.exists()

if hasMemory:
    reason = (
        "Before stopping: if you learned an ACTIVE RULE that changes future behavior "
        "(build/test commands, an architecture fact, a user preference, a workflow rule), "
        "update {dir}/MEMORY.md or a topic file. Write rules in imperative mood. "
        "Put durable behavior rules under the '## CRITICAL RULES' section. "
        "Do NOT save commit hashes, dated fix histories, or archival narrative — "
        "put any historical detail in history.md, not MEMORY.md. "
        "If nothing new was learned, just stop without changes. "
        "Keep MEMORY.md under 200 lines. IMPORTANT: Always write memory in English only."
    ).format(dir=memoryDir)
else:
    reason = (
        "Before stopping: this is a new project with no memory yet. "
        "Create {dir}/MEMORY.md with a '## CRITICAL RULES' section at the top "
        "(active rules in imperative mood: build/test commands, architecture facts, "
        "user preferences, workflow rules). Do NOT save commit hashes or dated history. "
        "Keep it concise (under 200 lines). IMPORTANT: Always write memory in English only. "
        "If this was a trivial session with nothing worth remembering, just stop."
    ).format(dir=memoryDir)

output = {
    "decision": "block",
    "reason": reason,
}
print(json.dumps(output))
sys.exit(0)
