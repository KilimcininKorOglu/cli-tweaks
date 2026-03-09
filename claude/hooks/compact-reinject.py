#!/usr/bin/env python3
"""
SessionStart:compact hook: re-injects project instruction files after compaction.

Usage:
  python3 compact-reinject.py AGENTS.md          # Factory Droid
  python3 compact-reinject.py CLAUDE.md           # Claude Code
  python3 compact-reinject.py AGENTS.md CLAUDE.md # Both

Reads the specified files from the project directory (cwd) and injects
their content back into context so they survive compaction.
"""
import json
import os
import sys
from pathlib import Path

try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())
filenames = sys.argv[1:] if len(sys.argv) > 1 else ["CLAUDE.md"]

parts = []
for filename in filenames:
    filepath = Path(cwd) / filename
    if filepath.exists():
        content = filepath.read_text(encoding="utf-8").strip()
        if content:
            parts.append(f"[RE-INJECTED AFTER COMPACTION: {filename}]\n{content}")

if not parts:
    sys.exit(0)

context = "\n\n".join(parts)

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}
print(json.dumps(output))
sys.exit(0)
