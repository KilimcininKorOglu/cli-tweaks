#!/usr/bin/env python3
"""Codex SessionStart compact hook: re-injects project instruction files."""
import os
import sys
from pathlib import Path

from common import readInput, writeAdditionalContext


def main() -> int:
    """Read requested project instruction files and emit compact context."""
    inputData = readInput()
    cwd = inputData.get("cwd") or os.getcwd()
    filenames = sys.argv[1:] if len(sys.argv) > 1 else ["AGENTS.md"]

    parts = []
    for filename in filenames:
        filePath = Path(cwd) / filename
        if not filePath.exists() or not filePath.is_file():
            continue
        try:
            content = filePath.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if content:
            parts.append(
                "[RE-INJECTED AFTER COMPACTION: {0} - BINDING]\n"
                "These project instructions were dropped during compaction and are "
                "restored below. They remain fully in effect. You MUST follow them "
                "exactly; they OVERRIDE defaults and any conflicting instruction.\n\n"
                "{1}".format(filename, content)
            )

    context = "\n\n".join(parts)
    writeAdditionalContext("SessionStart", context)
    return 0


if __name__ == "__main__":
    sys.exit(main())
