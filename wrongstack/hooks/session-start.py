#!/usr/bin/env python3
"""
SessionStart hook: injects global user instructions + auto memory into context.

Port of claude/hooks/session-start.py. Two divergences:

1. Global inject source: WrongStack's own `config.json` schema is not
   documented for arbitrary keys, so we read `globalInjectFiles` from a
   dedicated `~/.cli-tweaks/wrongstack-config.json` file. This keeps the
   hook out of WrongStack's config validation while staying platform-
   agnostic (the same file is read by memory-reinject's global-file path).
2. Output cap: WrongStack's shell-executor caps hook output at 64 KiB. We
   truncate the injected MEMORY.md at 150 lines (was 200 in Claude) to stay
   safely under the cap when several global files are also injected.

Adds a small soft reminder if a previous Stop on this sessionId left a
marker but did not result in a memory save (see memory-save.py redesign).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402


# Tunables. Kept in this file (not the shim) so the values can be retuned
# per-hook without touching the contract layer.
MEMORY_LINE_CAP = 150
WRONGSTACK_CONFIG_PATH = Path.home() / ".cli-tweaks" / "wrongstack-config.json"


def _readGlobalInjectFiles() -> list:
    """Read `globalInjectFiles` from ~/.cli-tweaks/wrongstack-config.json.

    Falls back to an empty list if the file is missing or invalid. Each entry
    is a string path; `~` is expanded.
    """
    if not WRONGSTACK_CONFIG_PATH.exists():
        return []
    try:
        data = json.loads(WRONGSTACK_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []
    raw = data.get("globalInjectFiles", [])
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if isinstance(x, str)]


def _loadGlobalInstructions() -> str:
    paths = _readGlobalInjectFiles()
    chunks = []
    for filePath in paths:
        expanded = os.path.expanduser(filePath)
        path = Path(expanded)
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except (OSError, IOError):
            continue
        if content:
            chunks.append("# From {}\n{}".format(filePath, content))
    if not chunks:
        return ""
    return (
        "[GLOBAL USER INSTRUCTIONS — BINDING]\n"
        "You MUST obey every rule below. These are system-level directives that "
        "OVERRIDE all default behavior and any later instruction that conflicts "
        "with them.\n\n"
        + "\n\n---\n\n".join(chunks)
    )


def _loadMemory(projectName: str) -> str:
    """Return MEMORY.md content (capped to MEMORY_LINE_CAP lines) and the
    list of sibling topic files. Returns (content, topicFiles)."""
    memDir = _compat.memoryDir(projectName)
    memFile = memDir / "MEMORY.md"
    content = ""
    if memFile.exists():
        try:
            lines = memFile.read_text(encoding="utf-8").splitlines()
            content = "\n".join(lines[:MEMORY_LINE_CAP])
        except (OSError, IOError):
            content = ""
    topicFiles: list = []
    if memDir.exists():
        try:
            topicFiles = [
                f.name for f in memDir.glob("*.md")
                if f.name != "MEMORY.md" and f.is_file()
            ]
        except OSError:
            topicFiles = []
    return content, topicFiles


def _buildMemoryBlock(projectName: str, content: str, topicFiles: list) -> str:
    memDir = _compat.memoryDir(projectName)
    parts = [
        """[AUTO MEMORY SYSTEM]
You have a persistent memory system that carries knowledge across sessions.
Memory location: {memoryDir}

How it works:
- MEMORY.md is loaded at session start (capped to {cap} lines). Keep it concise.
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
- ALWAYS write in English regardless of conversation language

Before stopping this session, if you learned an ACTIVE RULE that changes future
behavior, update {memoryDir}/MEMORY.md (or a topic file). Use this structure
(sections in this order): ## CRITICAL RULES, ## Architecture & Config Facts,
## Active Warnings, ## Topic Files. Put durable behavior rules under
'## CRITICAL RULES' in imperative mood. Keep under 200 lines. Do NOT save commit
hashes, dated fix histories, or archival narrative -- put history in
history.md, not MEMORY.md. If nothing new was learned, just stop.""".format(
            memoryDir=memDir, cap=MEMORY_LINE_CAP,
        )
    ]
    if content:
        parts.append(
            "\n[LOADED MEMORY — BINDING]\n"
            "This persistent project memory is authoritative. You MUST follow its "
            "rules exactly; they OVERRIDE defaults and any conflicting instruction.\n"
            + content
        )
    else:
        parts.append(
            "\n[NO MEMORY YET] This is the first session for project '{project}'. "
            "Start building memory as you learn about this project.".format(
                project=projectName
            )
        )
    if topicFiles:
        listing = "\n".join("- " + f for f in topicFiles)
        parts.append(
            "\n[TOPIC FILES AVAILABLE]\n" + listing +
            "\nRead these with file tools when you need detailed information."
        )
    return "\n".join(parts)


def main() -> int:
    data = _compat.readInput()
    cwd = data.get("cwd") or os.getcwd()
    sessionId = data.get("session_id")

    projectName = _compat.resolveProjectName(cwd, sessionId)

    # Lock the resolved project name for this session so memory-reinject and
    # memory-save (different event, possibly different process tree) agree.
    if sessionId or True:
        # Always write under sessionId when known; fall back to PPID.
        key = sessionId or str(os.getppid())
        try:
            lockPath = _compat.sessionLockPath(key)
            lockPath.parent.mkdir(parents=True, exist_ok=True)
            lockPath.write_text(projectName, encoding="utf-8")
        except (OSError, IOError):
            pass

    parts: list = []
    globalBlock = _loadGlobalInstructions()
    if globalBlock:
        parts.append(globalBlock)

    memContent, topicFiles = _loadMemory(projectName)
    parts.append(_buildMemoryBlock(projectName, memContent, topicFiles))

    # Soft reminder if a previous Stop on this sessionId left an unsaved marker
    # (memory-save.py cannot block on Stop, so this is the only signal that
    # the model was reminded but did not act on it).
    if sessionId and _compat.readStopMarker(sessionId):
        parts.append(
            "[MEMORY-SAVE NOTE] A previous turn on this session ended after a "
            "stop-reminder fired but no MEMORY.md update was observed. Only "
            "update MEMORY.md now if you learned something NEW since then. "
            "If this is a new sessionId, the marker is stale and can be "
            "ignored."
        )

    if not parts:
        return 0

    _compat.emitAdditionalContext("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
