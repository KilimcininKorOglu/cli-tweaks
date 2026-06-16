#!/usr/bin/env python3
"""
PreToolUse hook: blocks `git add -f` / `git add --force` on files listed in
the global gitignore. Prevents the agent from bypassing gitignore
protection with force-add.

Wired as: matcher "Bash" on event PreToolUse.
Direct port of claude/hooks/git-protect.py -- the field-name and outcome-shape
divergences from Claude (camelCase `toolName`, top-level `decision: "block"`)
are absorbed by _compat.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402


def main() -> int:
    data = _compat.readInput()
    if data.get("tool_name") != "Bash":
        return 0

    command = (data.get("tool_input") or {}).get("command", "") or ""
    if not isinstance(command, str):
        return 0

    if not re.search(r"\bgit\s+add\b", command):
        return 0
    if not re.search(r"\s-f\b|\s--force\b", command):
        return 0

    gitignorePath = Path.home() / ".gitignore_global"
    if not gitignorePath.is_file():
        return 0

    try:
        with gitignorePath.open("r", encoding="utf-8") as f:
            ignoredEntries = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#") and not line.startswith("!")
            ]
    except (OSError, IOError):
        return 0

    matched: list = []
    for entry in ignoredEntries:
        raw = entry.rstrip("/")
        clean = raw.lstrip("*").lstrip(".")
        if raw and raw in command:
            matched.append(entry)
        elif clean and clean in command:
            matched.append(entry)

    if not matched:
        return 0

    reason = (
        "BLOCKED: `git add -f` on protected file(s): {files}. "
        "These files are in the global gitignore for a reason. "
        "Analyze the root cause of the error instead of force-adding."
    ).format(files=", ".join(matched))
    _compat.emitBlock(reason)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Fail-safe: never break the agent loop on a buggy hook.
        sys.exit(0)
