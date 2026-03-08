#!/usr/bin/env python3
"""
SessionStart hook: injects global user instruction files into context.

Reads file paths from settings.json "globalInjectFiles" array and injects
their contents at session start and after context compaction.
"""
import json
import os
import sys
from pathlib import Path

try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# Read settings.json to get file list
settingsFile = Path.home() / ".factory" / "settings.json"
if not settingsFile.exists():
    sys.exit(0)

try:
    settings = json.loads(settingsFile.read_text(encoding="utf-8"))
except (json.JSONDecodeError, IOError):
    sys.exit(0)

fileList = settings.get("globalInjectFiles", [])
if not fileList:
    sys.exit(0)

# Collect contents from all files
contents = []
for filePath in fileList:
    # Expand ~ to home directory
    expanded = os.path.expanduser(filePath)
    path = Path(expanded)
    
    if not path.exists():
        continue
    
    try:
        content = path.read_text(encoding="utf-8").strip()
        if content:
            contents.append(f"# From {filePath}\n{content}")
    except IOError:
        continue

if not contents:
    sys.exit(0)

combined = "\n\n---\n\n".join(contents)

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": f"[GLOBAL USER INSTRUCTIONS]\n{combined}",
    }
}
print(json.dumps(output))
sys.exit(0)
