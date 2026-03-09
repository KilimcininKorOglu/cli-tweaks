#!/usr/bin/env python3
"""
SessionStart hook: injects global user instruction files into context.

Reads file paths from settings.json "globalInjectFiles" array (primary).
Falls back to hooks/hooks.json for backwards compatibility if settings.json
has no globalInjectFiles configured.
Injects contents at session start and after context compaction.
"""
import json
import os
import sys
from pathlib import Path

try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# Check hooks.json first (backwards compatibility), then settings.json (primary)
claudeDir = Path.home() / ".claude"
hooksFile = claudeDir / "hooks" / "hooks.json"
settingsFile = claudeDir / "settings.json"

fileList = []

# Check hooks.json (backwards compatibility)
if hooksFile.exists():
    try:
        data = json.loads(hooksFile.read_text(encoding="utf-8"))
        fileList = data.get("globalInjectFiles", [])
    except (json.JSONDecodeError, IOError):
        pass

# Fall back to settings.json (primary config)
if not fileList and settingsFile.exists():
    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
        fileList = data.get("globalInjectFiles", [])
    except (json.JSONDecodeError, IOError):
        pass

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
