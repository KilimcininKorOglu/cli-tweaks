#!/usr/bin/env python3
"""
SessionStart hook: loads auto memory into context at session start.

Reads ~/.claude/memory/<project>/MEMORY.md (first 200 lines) and injects
it as context along with instructions for the memory system.
"""
import json
import os
import sys
from pathlib import Path

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

cwd = input_data.get("cwd", os.getcwd())
project_name = os.path.basename(cwd)

memory_dir = Path.home() / ".claude" / "memory" / project_name
memory_file = memory_dir / "MEMORY.md"

# Load memory content (first 200 lines, like Claude Code)
memory_content = ""
if memory_file.exists():
    lines = memory_file.read_text(encoding="utf-8").splitlines()
    memory_content = "\n".join(lines[:200])

# List topic files
topic_files = []
if memory_dir.exists():
    topic_files = [
        f.name for f in memory_dir.glob("*.md")
        if f.name != "MEMORY.md" and f.is_file()
    ]

# Build context
parts = []

parts.append("""[AUTO MEMORY SYSTEM]
You have a persistent memory system that carries knowledge across sessions.
Memory location: {memory_dir}

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
- Write directly to {memory_dir}/MEMORY.md or topic files using file tools
- Keep MEMORY.md under 200 lines -- move details to topic files
- Use markdown headers and bullets for structure
- ALWAYS write in English regardless of conversation language""".format(
    memory_dir=memory_dir
))

if memory_content:
    parts.append("\n[LOADED MEMORY]\n" + memory_content)
else:
    parts.append("\n[NO MEMORY YET] This is the first session for project '{project}'. "
                 "Start building memory as you learn about this project.".format(
                     project=project_name))

if topic_files:
    listing = "\n".join("- " + f for f in topic_files)
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
