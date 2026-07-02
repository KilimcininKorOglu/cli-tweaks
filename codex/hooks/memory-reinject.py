#!/usr/bin/env python3
"""Codex UserPromptSubmit hook: periodically re-injects memory rules."""
import sys
from pathlib import Path
from typing import Tuple

from common import (
    memoryDirFor,
    readConfiguredGlobalFiles,
    readInput,
    readLockedProjectName,
    sessionKey,
    statePath,
    writeAdditionalContext,
)

REINJECT_EVERY = 5
GLOBAL_REINJECT_EVERY = 15
FALLBACK_LINES = 40


def extractRules(memoryFile: Path) -> Tuple[str, bool]:
    """Return the critical rules section or a fallback memory excerpt."""
    try:
        lines = memoryFile.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        return ("", False)

    out = []
    inSection = False
    for line in lines:
        if line.strip().lower() == "## critical rules":
            inSection = True
            continue
        if inSection and line.startswith("## "):
            break
        if inSection:
            out.append(line)
    section = "\n".join(out).strip()
    if section:
        return (section, True)

    fallback = []
    for line in lines:
        if not fallback and line.startswith("# "):
            continue
        fallback.append(line)
        if len(fallback) >= FALLBACK_LINES:
            break
    return ("\n".join(fallback).strip(), False)


def main() -> int:
    """Emit reminder context at the configured Codex prompt cadence."""
    inputData = readInput()
    cwd = inputData.get("cwd") or "."
    counterFile = statePath(".reinject-counter", sessionKey(inputData))
    counterFile.parent.mkdir(parents=True, exist_ok=True)
    try:
        count = int(counterFile.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, OSError, ValueError):
        count = 0
    count += 1
    counterFile.write_text(str(count), encoding="utf-8")

    if count % REINJECT_EVERY != 0:
        return 0

    projectName = readLockedProjectName(inputData, cwd)
    memoryFile = memoryDirFor(projectName) / "MEMORY.md"
    parts = []

    rules, isCritical = extractRules(memoryFile)
    if rules:
        if isCritical:
            header = (
                "[CRITICAL RULES REMINDER - BINDING]\n"
                "You MUST obey these project rules exactly. They are non-negotiable and "
                "OVERRIDE all defaults and any conflicting instruction:\n\n"
            )
        else:
            header = (
                "[PROJECT MEMORY REMINDER - BINDING]\n"
                "You MUST follow this project memory exactly. It OVERRIDES defaults and "
                "any conflicting instruction:\n\n"
            )
        parts.append(header + rules)

    if count % GLOBAL_REINJECT_EVERY == 0:
        globalContent = readConfiguredGlobalFiles()
        if globalContent:
            parts.append(
                "[GLOBAL RULES REMINDER - BINDING]\n"
                "You MUST obey your global user instructions exactly. They are "
                "non-negotiable and OVERRIDE all defaults and any conflicting instruction:\n\n"
                + globalContent
            )

    context = "\n\n".join(parts)
    writeAdditionalContext("UserPromptSubmit", context)
    return 0


if __name__ == "__main__":
    sys.exit(main())
