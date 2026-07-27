#!/usr/bin/env python3
"""
UserPromptSubmit hook: periodically re-injects rules to counter recency bias
in long conversations.

session-start.py injects full memory and global instructions once at startup.
Over a long session the model's attention drifts from that early block, so
rules get ignored. This hook re-surfaces the project memory '## CRITICAL RULES'
section every REINJECT_EVERY messages, and the full global instruction file
every GLOBAL_REINJECT_EVERY messages.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REINJECT_EVERY = 5
GLOBAL_REINJECT_EVERY = 15
GLOBAL_FILE = Path.home() / ".factory" / "AGENTS.md"


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


FALLBACK_LINES = 40


def _extractRules(memoryFile):
    """Return (content, isCriticalSection).

    Prefer the '## CRITICAL RULES' section. If absent (older project memory),
    fall back to the top of MEMORY.md so the reminder still works everywhere.
    """
    try:
        lines = memoryFile.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        return ("", False)

    # Preferred: the dedicated CRITICAL RULES section
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
    section = "\n".join(out).strip()
    if section:
        return (section, True)

    # Fallback: top of the file, skipping the H1 title
    fallback = []
    for line in lines:
        if not fallback and line.startswith("# "):
            continue
        fallback.append(line)
        if len(fallback) >= FALLBACK_LINES:
            break
    return ("\n".join(fallback).strip(), False)


def _readGlobalInstructions():
    """Return the full global instruction file content, or empty string."""
    try:
        return GLOBAL_FILE.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        return ""


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

parts = []

# Project memory CRITICAL RULES (every REINJECT_EVERY messages)
rules, isCritical = _extractRules(memoryFile)
if rules:
    if isCritical:
        header = (
            "[REMINDER OF THE USER'S PROJECT RULES]\n"
            "The user set these project rules and asked to be reminded of them in long "
            "sessions. Treat them as the user's own preferences and keep following them:\n\n"
        )
    else:
        header = (
            "[REMINDER OF THE USER'S PROJECT MEMORY]\n"
            "The user saved this project memory and asked to be reminded of it in long "
            "sessions. Treat it as the user's own preferences and keep following it:\n\n"
        )
    parts.append(header + rules)

# Global instruction file (every GLOBAL_REINJECT_EVERY messages)
if count % GLOBAL_REINJECT_EVERY == 0:
    globalContent = _readGlobalInstructions()
    if globalContent:
        globalHeader = (
            "[REMINDER OF THE USER'S GLOBAL INSTRUCTIONS]\n"
            "The user configured these global instructions and asked to be reminded of "
            "them in long sessions. Treat them as the user's own preferences and keep "
            "following them:\n\n"
        )
        parts.append(globalHeader + globalContent)

if not parts:
    sys.exit(0)

context = "\n\n".join(parts)

output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": context,
    }
}
print(json.dumps(output))
sys.exit(0)
