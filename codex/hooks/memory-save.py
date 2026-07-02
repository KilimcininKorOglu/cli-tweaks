#!/usr/bin/env python3
"""Codex Stop hook: continues once to require memory hygiene before stopping."""
import json
import sys
from pathlib import Path
from typing import List, Tuple

from common import memoryDirFor, readInput, readLockedProjectName

MEMORY_SOFT_LIMIT_LINES = 180
MEMORY_SOFT_LIMIT_CHARS = 45000
MEMORY_MAX_BULLET_CHARS = 600


def memoryStats(memoryFile: Path) -> Tuple[bool, int, int, bool, List[Tuple[int, int, str]]]:
    """Return memory existence, size, required-section state, and long bullets."""
    if not memoryFile.exists():
        return (False, 0, 0, False, [])
    try:
        memoryText = memoryFile.read_text(encoding="utf-8")
    except OSError:
        return (True, 0, 0, False, [])

    lines = memoryText.splitlines()
    hasCriticalSection = any(line.strip().lower() == "## critical rules" for line in lines)
    longBullets = []
    for idx, line in enumerate(lines, start=1):
        if line.startswith("- ") and len(line) > MEMORY_MAX_BULLET_CHARS:
            longBullets.append((idx, len(line), line[:55]))
    return (True, len(lines), len(memoryText), hasCriticalSection, longBullets)


def buildReason(memoryDir: Path, memoryFile: Path) -> str:
    """Build the Codex continuation prompt for memory hygiene."""
    hasMemory, lineCount, charCount, hasCriticalSection, longBullets = memoryStats(memoryFile)
    template = (
        "MEMORY.md MUST use exactly these four sections, in this order:\n"
        "  ## CRITICAL RULES - non-negotiable active rules, imperative mood\n"
        "  ## Architecture & Config Facts - stable technical context, not rules\n"
        "  ## Active Warnings - pitfalls and recurring mistakes\n"
        "  ## Topic Files - pointers to detail files such as history.md\n"
        "Keep each bullet to ONE focused rule or fact. Strip narrative, examples, and dated context "
        "to a topic file. Keep MEMORY.md under 200 lines and under 50000 characters. "
        "Write memory in English only."
    )

    if hasMemory:
        reason = (
            "MANDATORY before stopping: apply each rule below.\n"
            "1. If you learned an active rule that changes future behavior, record it in {0}/MEMORY.md in imperative mood.\n"
            "2. Never write commit hashes, dated fix histories, completed-work records, or archival narrative to MEMORY.md.\n"
            "3. Put historical detail in a topic file only, usually history.md, and list new topic files under ## Topic Files.\n"
            "4. Keep MEMORY.md as durable rules, stable facts, and active warnings only, with one focused bullet per line.\n"
            "5. Keep MEMORY.md under 200 lines and under 50000 characters.\n"
            "6. Write memory in English only.\n"
            "If nothing new was learned and the file already obeys every rule above, stop after this continuation."
        ).format(memoryDir)
    else:
        reason = (
            "MANDATORY before stopping: create {0}/MEMORY.md if this session learned durable rules, stable facts, "
            "or active warnings. Use the template below. Skip only if the session was genuinely trivial.\n"
            "{1}"
        ).format(memoryDir, template)

    if hasMemory and not hasCriticalSection:
        reason += "\nMANDATORY MIGRATION: MEMORY.md is missing ## CRITICAL RULES. Restructure it into the required template before stopping."

    if hasMemory and (lineCount >= MEMORY_SOFT_LIMIT_LINES or charCount >= MEMORY_SOFT_LIMIT_CHARS):
        reason += (
            "\nMANDATORY OFFLOAD: MEMORY.md is now {0} lines and {1} characters. Move the oldest or least-critical entries "
            "to a topic file before stopping."
        ).format(lineCount, charCount)

    if hasMemory and longBullets:
        offenders = "\n".join(
            "  - line {0} ({1} chars): {2}...".format(lineNum, charNum, preview)
            for lineNum, charNum, preview in longBullets
        )
        reason += (
            "\nMANDATORY BULLET SPLIT: {0} bullet(s) exceed {1} characters. Split focused rules or move detail to topic files.\n{2}"
        ).format(len(longBullets), MEMORY_MAX_BULLET_CHARS, offenders)

    return reason


def main() -> int:
    """Continue the Codex turn once when memory hygiene needs attention."""
    inputData = readInput()
    if inputData.get("stop_hook_active", False):
        return 0

    cwd = inputData.get("cwd") or "."
    projectName = readLockedProjectName(inputData, cwd)
    memoryDir = memoryDirFor(projectName)
    memoryDir.mkdir(parents=True, exist_ok=True)
    reason = buildReason(memoryDir, memoryDir / "MEMORY.md")

    output = {
        "decision": "block",
        "reason": reason,
    }
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
