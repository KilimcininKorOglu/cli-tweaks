#!/usr/bin/env python3
"""
UserPromptSubmit hook: periodically re-injects the CRITICAL RULES section
from project memory to counter recency bias in long conversations.

session-start.py injects full memory once at startup. Over a long session the
model's attention drifts from that early block, so rules get ignored. This hook
re-surfaces only the '## CRITICAL RULES' section every Nth user message.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REINJECT_EVERY = 5


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


def _extractCriticalRules(memoryFile):
    """Extract the '## CRITICAL RULES' section body from MEMORY.md."""
    try:
        lines = memoryFile.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        return ""
    out = []
    inSection = False
    for line in lines:
        if line.strip().lower() == "## critical rules":
            inSection = True
            continue
        if inSection:
            if line.startswith("## "):
                break
            out.append(line)
    return "\n".join(out).strip()


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())

# Increment per-session counter (keyed by parent PID)
counterFile = Path.home() / ".cli-tweaks" / ".reinject-counter" / str(os.getppid())
counterFile.parent.mkdir(parents=True, exist_ok=True)
try:
    count = int(counterFile.read_text(encoding="utf-8").strip())
except (FileNotFoundError, OSError, ValueError):
    count = 0
count += 1
counterFile.write_text(str(count), encoding="utf-8")

# Only re-inject every Nth message
if count % REINJECT_EVERY != 0:
    sys.exit(0)

# Resolve project name: prefer the session lock, fallback to git root / cwd
lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
try:
    projectName = lockFile.read_text(encoding="utf-8").strip()
except (FileNotFoundError, OSError):
    projectName = _resolveProjectName(cwd)

memoryFile = Path.home() / ".cli-tweaks" / "memory" / projectName / "MEMORY.md"
rules = _extractCriticalRules(memoryFile)

if not rules:
    sys.exit(0)

context = (
    "[CRITICAL RULES REMINDER]\n"
    "These project rules are non-negotiable. Follow them exactly:\n\n"
    + rules
)

output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": context,
    }
}
print(json.dumps(output))
sys.exit(0)
