#!/usr/bin/env python3
"""
SessionStart:compact hook: re-injects project instruction files after compaction.

Usage:
  python3 compact-reinject.py AGENTS.md          # Factory Droid
  python3 compact-reinject.py CLAUDE.md           # Claude Code
  python3 compact-reinject.py AGENTS.md CLAUDE.md # Both

Looks for each file in every directory from the repository top level down to
the cwd, the same directories Claude Code loads project instructions from, and
also in the `.claude/` directory of each. Outside a git repository only the cwd
is searched. The contents are injected back into context so they survive
compaction.

A file that exists but cannot be read is reported to the user with
`systemMessage`; the files that can be read are still injected.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from project import runGit


def _searchDirs(cwd: Path) -> list[Path]:
    """Return the directories from the repository top level down to the cwd."""
    top = runGit(str(cwd), "rev-parse", "--show-toplevel")
    if not top:
        return [cwd]
    topPath = Path(top).resolve()
    dirs = [cwd]
    while dirs[-1] != topPath and dirs[-1] != dirs[-1].parent:
        dirs.append(dirs[-1].parent)
    return list(reversed(dirs))


def _candidates(cwd: Path, filename: str) -> list[Path]:
    """Return every existing file with this name that applies to the cwd."""
    found = []
    for directory in _searchDirs(cwd):
        for path in (directory / filename, directory / ".claude" / filename):
            if path.is_file():
                found.append(path)
    return found


def _block(path: Path, errors: list[str]) -> str:
    """Return the restored-context block of one file, or "" when it has none."""
    try:
        content = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as err:
        errors.append(f"cannot read {path}: {err}")
        return ""
    if not content:
        return ""
    return (
        f"[USER'S PROJECT INSTRUCTIONS, RESTORED AFTER COMPACTION: {path}]\n"
        "The user's project instructions below were dropped during compaction. "
        "They still apply, so they are restored here. Treat them as the user's "
        "own preferences and keep following them.\n\n"
        + content
    )


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

cwd = Path(inputData.get("cwd", os.getcwd())).resolve()
filenames = sys.argv[1:] if len(sys.argv) > 1 else ["CLAUDE.md"]

errors: list[str] = []
parts = []
for filename in filenames:
    for path in _candidates(cwd, filename):
        block = _block(path, errors)
        if block:
            parts.append(block)

output: dict = {}
if parts:
    output["hookSpecificOutput"] = {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n".join(parts),
    }
if errors:
    output["systemMessage"] = "compact-reinject.py: " + "; ".join(errors)
if output:
    print(json.dumps(output))
sys.exit(0)
