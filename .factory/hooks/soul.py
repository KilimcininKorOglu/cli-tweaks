#!/usr/bin/env python3
"""
SessionStart hook: injects ~/.factory/SOUL.md into context at session
start and after context compaction.
"""
import json
import sys
from pathlib import Path

try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

soulFile = Path.home() / ".factory" / "SOUL.md"

if not soulFile.exists():
    sys.exit(0)

content = soulFile.read_text(encoding="utf-8").strip()
if not content:
    sys.exit(0)

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": content,
    }
}
print(json.dumps(output))
sys.exit(0)
