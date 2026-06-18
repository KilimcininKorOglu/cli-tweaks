#!/usr/bin/env python3
"""
Stop hook: reminds the agent to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks agent to save memory.
On second stop (stop_hook_active=true): allows agent to stop normally.
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

# If already triggered once this turn, let agent stop
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

# Count lines to decide whether to prompt offloading old entries to topic files.
# Threshold is below the 200-line cap so the agent trims BEFORE overflowing.
MEMORY_SOFT_LIMIT = 180
lineCount = 0
if hasMemory:
    try:
        lineCount = len(memoryFile.read_text(encoding="utf-8").splitlines())
    except (OSError, IOError):
        lineCount = 0

TEMPLATE = (
    "Use this MEMORY.md structure (sections in this order):\n"
    "  ## CRITICAL RULES        - non-negotiable active rules, imperative mood\n"
    "  ## Architecture & Config Facts - stable technical context (not rules)\n"
    "  ## Active Warnings       - pitfalls and recurring mistakes\n"
    "  ## Topic Files           - pointers to detail files (e.g. history.md)\n"
    "Write each bullet on a single line; do NOT hard-wrap text mid-bullet. "
    "Hard-wrapping inflates the line count and weakens the 40-line fallback reminder.\n"
)

if hasMemory:
    reason = (
        "Before stopping: if you learned an ACTIVE RULE that changes future behavior "
        "(build/test commands, an architecture fact, a user preference, a workflow rule), "
        "update {dir}/MEMORY.md or a topic file. Write rules in imperative mood. "
        "Put durable behavior rules under the '## CRITICAL RULES' section. "
        "Do NOT save commit hashes, dated fix histories, or archival narrative — "
        "put any historical detail in history.md, not MEMORY.md. "
        "MIGRATION: if MEMORY.md has no '## CRITICAL RULES' section, restructure the "
        "whole file into the template below this session (preserve all real content, "
        "just reorganize and convert rules to imperative mood). "
        "If nothing new was learned and the format is already correct, just stop. "
        "Keep MEMORY.md under 200 lines. IMPORTANT: Always write memory in English only.\n"
        + TEMPLATE
    ).format(dir=memoryDir)
else:
    reason = (
        "Before stopping: this is a new project with no memory yet. "
        "Create {dir}/MEMORY.md following the template below. "
        "Write rules in imperative mood. Do NOT save commit hashes or dated history. "
        "Keep it concise (under 200 lines). IMPORTANT: Always write memory in English only. "
        "If this was a trivial session with nothing worth remembering, just stop.\n"
        + TEMPLATE
    ).format(dir=memoryDir)

if hasMemory and lineCount >= MEMORY_SOFT_LIMIT:
    reason += (
        "\nOFFLOAD: MEMORY.md is now {n} lines, near the 200-line cap. "
        "Move the OLDEST or least-critical entries (resolved warnings, superseded "
        "facts, dated notes) into a topic file (e.g. history.md), keeping MEMORY.md "
        "a lean index of ACTIVE rules and current architecture facts."
    ).format(n=lineCount)

output = {
    "decision": "block",
    "reason": reason,
}
print(json.dumps(output))
sys.exit(0)
