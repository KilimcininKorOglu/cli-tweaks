#!/usr/bin/env python3
"""Codex PreToolUse hook: blocks forced git-add of globally ignored files."""
import json
import os
import re
import sys
from typing import List

from common import readInput


def ignoredEntries(gitignorePath: str) -> List[str]:
    """Return active entries from the user's global gitignore file."""
    try:
        with open(gitignorePath, "r", encoding="utf-8") as handle:
            return [
                line.strip()
                for line in handle
                if line.strip() and not line.startswith("#") and not line.startswith("!")
            ]
    except OSError:
        return []


def matchedIgnoredEntries(command: str, entries: List[str]) -> List[str]:
    """Return global gitignore entries referenced by a shell command."""
    matched = []
    for entry in entries:
        clean = entry.rstrip("/").lstrip("*").lstrip(".")
        raw = entry.rstrip("/")
        if raw and raw in command:
            matched.append(entry)
        elif clean and clean in command:
            matched.append(entry)
    return matched


def emitBlock(reason: str) -> None:
    """Emit a Codex PreToolUse block decision."""
    output = {
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }
    print(json.dumps(output))


def main() -> int:
    """Block unsafe forced git-add commands before Codex runs Bash."""
    data = readInput()
    if data.get("tool_name") != "Bash":
        return 0

    toolInput = data.get("tool_input")
    command = toolInput.get("command", "") if isinstance(toolInput, dict) else ""
    if not re.search(r"\bgit\s+add\b", command):
        return 0
    if not re.search(r"\s-f\b|\s--force\b", command):
        return 0

    gitignorePath = os.path.expanduser("~/.gitignore_global")
    if not os.path.isfile(gitignorePath):
        return 0

    matched = matchedIgnoredEntries(command, ignoredEntries(gitignorePath))
    if matched:
        reason = (
            "BLOCKED: `git add -f` on protected file(s): {0}. "
            "These files are in the global gitignore for a reason. "
            "Analyze the root cause of the error instead of force-adding."
        ).format(", ".join(matched))
        emitBlock(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
