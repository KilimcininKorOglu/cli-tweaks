#!/usr/bin/env python3
"""
SessionStart hook: loads auto memory into context at session start.

Reads ~/.cli-tweaks/memory/<project>/MEMORY.md (first 200 lines) and injects
it as context along with instructions for the memory system.
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
projectName = os.path.basename(cwd)

memoryDir = Path.home() / ".cli-tweaks" / "memory" / projectName
memoryFile = memoryDir / "MEMORY.md"

# Load memory content (first 200 lines, like Claude Code)
memoryContent = ""
if memoryFile.exists():
    lines = memoryFile.read_text(encoding="utf-8").splitlines()
    memoryContent = "\n".join(lines[:200])

# List topic files
topicFiles = []
if memoryDir.exists():
    topicFiles = [
        f.name for f in memoryDir.glob("*.md")
        if f.name != "MEMORY.md" and f.is_file()
    ]

# Build context
parts = []

parts.append("""[AUTO MEMORY SYSTEM]
You have a persistent memory system that carries knowledge across sessions.
Memory location: {memoryDir}

How it works:
- MEMORY.md is loaded at session start (first 200 lines). Keep it concise.
- Create topic files (e.g., debugging.md, patterns.md) for detailed notes.
- MEMORY.md should be an index pointing to topic files.
- Read topic files on demand when you need the information.

IMPORTANT: All memory files (MEMORY.md and topic files) MUST be written in English only.
This ensures consistency and searchability across sessions.

When to save memory:
- Build commands, test commands, or project setup steps you discovered
- Architecture decisions or patterns you identified
- Debugging insights or tricky bugs you solved
- User preferences or coding style you observed
- Workflow habits (e.g., "user prefers Turkish responses")
- DO NOT save trivial or obvious information
- DO NOT save sensitive data (passwords, keys, tokens)

How to save:
- Write directly to {memoryDir}/MEMORY.md or topic files using file tools
- Keep MEMORY.md under 200 lines -- move details to topic files
- Use markdown headers and bullets for structure
- ALWAYS write in English regardless of conversation language""".format(
    memoryDir=memoryDir
))

if memoryContent:
    parts.append("\n[LOADED MEMORY]\n" + memoryContent)
else:
    parts.append("\n[NO MEMORY YET] This is the first session for project '{project}'. "
                 "Start building memory as you learn about this project.".format(
                     project=projectName))

if topicFiles:
    listing = "\n".join("- " + f for f in topicFiles)
    parts.append("\n[TOPIC FILES AVAILABLE]\n" + listing +
                 "\nRead these with file tools when you need detailed information.")

context = "\n".join(parts)

output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context,
    }
}
print(json.dumps(output))
sys.exit(0)
