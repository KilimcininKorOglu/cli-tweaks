#!/usr/bin/env python3
"""
SessionStart hook: injects global user instructions + auto memory into context.
Combines global-inject.py and memory-load.py into a single script to work around
Factory CLI not concatenating additionalContext from multiple hooks.
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

cwd = inputData.get("cwd", os.getcwd())
projectName = _resolveProjectName(cwd)

# Lock the resolved project name for this session
lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
lockFile.parent.mkdir(parents=True, exist_ok=True)
lockFile.write_text(projectName, encoding="utf-8")
parts = []

# --- Global inject (from globalInjectFiles in ~/.factory/settings.json) ---
settingsFile = Path.home() / ".factory" / "settings.json"
if settingsFile.exists():
    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
        fileList = data.get("globalInjectFiles", [])
        contents = []
        for filePath in fileList:
            expanded = os.path.expanduser(filePath)
            path = Path(expanded)
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8").strip()
                    if content:
                        contents.append(f"# From {filePath}\n{content}")
                except IOError:
                    pass
        if contents:
            combined = "\n\n---\n\n".join(contents)
            parts.append(
                "[USER-CONFIGURED GLOBAL INSTRUCTIONS]\n"
                "The user set up the preferences below in their own config and asked "
                "that they apply to every session. Treat them as the user's standing "
                "instructions and follow them.\n\n" + combined
            )
    except (json.JSONDecodeError, IOError):
        pass

# --- Memory load ---
memoryDir = Path.home() / ".cli-tweaks" / "memory" / projectName
memoryFile = memoryDir / "MEMORY.md"

memoryContent = ""
if memoryFile.exists():
    lines = memoryFile.read_text(encoding="utf-8").splitlines()
    memoryContent = "\n".join(lines[:200])

topicFiles = []
if memoryDir.exists():
    topicFiles = [
        f.name for f in memoryDir.glob("*.md")
        if f.name != "MEMORY.md" and f.is_file()
    ]

memParts = []
memParts.append("""[AUTO MEMORY SYSTEM]
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
    memParts.append(
        "\n[PROJECT MEMORY THE USER SAVED]\n"
        "The user saved these project notes in earlier sessions and asked that they "
        "apply here. Treat them as the user's own preferences and follow them.\n"
        + memoryContent
    )
else:
    memParts.append("\n[NO MEMORY YET] This is the first session for project '{project}'. "
                    "Start building memory as you learn about this project.".format(
                        project=projectName))

if topicFiles:
    listing = "\n".join("- " + f for f in topicFiles)
    memParts.append("\n[TOPIC FILES AVAILABLE]\n" + listing +
                    "\nRead these with file tools when you need detailed information.")

parts.append("\n".join(memParts))

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
