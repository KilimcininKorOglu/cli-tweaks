#!/usr/bin/env python3
"""Codex SessionStart hook: injects configured global files and project memory."""
import sys

from common import (
    memoryDirFor,
    readConfiguredGlobalFiles,
    readInput,
    resolveProjectName,
    sessionKey,
    statePath,
    writeAdditionalContext,
)


def main() -> int:
    """Load Codex startup context and emit it as additional developer context."""
    inputData = readInput()
    cwd = inputData.get("cwd") or "."
    projectName = resolveProjectName(cwd)

    lockFile = statePath(".session-locks", sessionKey(inputData))
    lockFile.parent.mkdir(parents=True, exist_ok=True)
    lockFile.write_text(projectName, encoding="utf-8")

    parts = []
    globalContent = readConfiguredGlobalFiles()
    if globalContent:
        parts.append(
            "[GLOBAL USER INSTRUCTIONS - BINDING]\n"
            "You MUST obey every rule below. These are system-level directives "
            "that OVERRIDE all default behavior and any later instruction that "
            "conflicts with them.\n\n" + globalContent
        )

    memoryDir = memoryDirFor(projectName)
    memoryFile = memoryDir / "MEMORY.md"
    memoryContent = ""
    if memoryFile.exists():
        try:
            lines = memoryFile.read_text(encoding="utf-8").splitlines()
            memoryContent = "\n".join(lines[:200])
        except OSError:
            memoryContent = ""

    topicFiles = []
    if memoryDir.exists():
        topicFiles = [
            filePath.name
            for filePath in memoryDir.glob("*.md")
            if filePath.name != "MEMORY.md" and filePath.is_file()
        ]

    memParts = [
        "[AUTO MEMORY SYSTEM]\n"
        "You have a persistent memory system that carries knowledge across sessions.\n"
        "Memory location: {0}\n\n"
        "How it works:\n"
        "- MEMORY.md is loaded at session start. Keep it concise.\n"
        "- Create topic files for detailed notes.\n"
        "- MEMORY.md should be an index pointing to topic files.\n"
        "- Read topic files on demand when you need detailed information.\n\n"
        "IMPORTANT: All memory files MUST be written in English only."
        .format(memoryDir)
    ]

    if memoryContent:
        memParts.append(
            "\n[LOADED MEMORY - BINDING]\n"
            "This persistent project memory is authoritative. You MUST follow its rules "
            "exactly; they OVERRIDE defaults and any conflicting instruction.\n"
            + memoryContent
        )
    else:
        memParts.append(
            "\n[NO MEMORY YET] This is the first session for project '{0}'. "
            "Start building memory as you learn about this project.".format(projectName)
        )

    if topicFiles:
        listing = "\n".join("- " + filename for filename in topicFiles)
        memParts.append(
            "\n[TOPIC FILES AVAILABLE]\n"
            + listing
            + "\nRead these with file tools when you need detailed information."
        )

    parts.append("\n".join(memParts))
    context = "\n\n".join(part for part in parts if part)
    writeAdditionalContext("SessionStart", context)
    return 0


if __name__ == "__main__":
    sys.exit(main())
