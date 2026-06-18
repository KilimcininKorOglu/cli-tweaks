#!/usr/bin/env python3
"""
UserPromptSubmit hook: periodically re-injects rules to counter recency bias
in long conversations.

session-start.py injects full memory and global instructions once at startup.
Over a long session the model's attention drifts from that early block, so
rules get ignored. This hook re-surfaces the project memory '## CRITICAL
RULES' section every REINJECT_EVERY messages, and a designated global
instruction file every GLOBAL_REINJECT_EVERY messages.

Divergences from the Claude port:

- The per-session counter is keyed by WrongStack's sessionId (stable per
  session) instead of os.getppid(). Lock is written by session-start, read
  here. This mirrors the same hardening we did for the OpenCode plugin.
- The "global instruction file" is read from a `globalInstructionFile` key
  in `~/.cli-tweaks/wrongstack-config.json` (set by the user). Claude hard-
  codes `~/.claude/CLAUDE.md`; WrongStack has no such canonical file.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402


REINJECT_EVERY = 5
GLOBAL_REINJECT_EVERY = 15
FALLBACK_LINES = 40
WRONGSTACK_CONFIG_PATH = Path.home() / ".cli-tweaks" / "wrongstack-config.json"


def _extractRules(memoryFile: Path):
    """Return (content, isCriticalSection).

    Prefer the '## CRITICAL RULES' section. If absent (older project memory),
    fall back to the top of MEMORY.md so the reminder still works everywhere.
    """
    try:
        lines = memoryFile.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        return ("", False)

    # Preferred: the dedicated CRITICAL RULES section
    out = []
    inSection = False
    for line in lines:
        if line.strip().lower() == "## critical rules":
            inSection = True
            continue
        if inSection:
            if line.startswith("## "):
                break
            out.append(line)
    section = "\n".join(out).strip()
    if section:
        return (section, True)

    # Fallback: top of the file, skipping the H1 title
    fallback = []
    for line in lines:
        if not fallback and line.startswith("# "):
            continue
        fallback.append(line)
        if len(fallback) >= FALLBACK_LINES:
            break
    return ("\n".join(fallback).strip(), False)


def _readGlobalInstructionFile() -> str:
    """Return the user-designated global instruction file's content, or ''.

    The path comes from `globalInstructionFile` in wrongstack-config.json.
    We do not silently fall back to Claude's ~/.claude/CLAUDE.md or Factory's
    ~/.factory/AGENTS.md -- WrongStack users may not have either, and reading
    a different platform's file by surprise would be a leak.
    """
    if not WRONGSTACK_CONFIG_PATH.exists():
        return ""
    try:
        import json
        data = json.loads(WRONGSTACK_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError, ValueError):
        return ""
    raw = data.get("globalInstructionFile", "")
    if not isinstance(raw, str) or not raw.strip():
        return ""
    path = Path(os.path.expanduser(raw.strip()))
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, IOError):
        return ""


def main() -> int:
    data = _compat.readInput()
    cwd = data.get("cwd") or os.getcwd()
    sessionId = data.get("session_id")

    # Pick a counter key. Prefer sessionId; fall back to PPID so the cadence
    # still works if WrongStack omits the id for a subagent.
    counterKey = sessionId or str(os.getppid())

    # Increment per-session counter
    counterPath = _compat.reinjectCounterPath(counterKey)
    try:
        counterPath.parent.mkdir(parents=True, exist_ok=True)
        count = int(counterPath.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, OSError, ValueError):
        count = 0
    count += 1
    try:
        counterPath.write_text(str(count), encoding="utf-8")
    except (OSError, IOError):
        # If we cannot persist the counter, skip the reinjection to avoid
        # firing every turn.
        return 0

    if count % REINJECT_EVERY != 0:
        return 0

    projectName = _compat.resolveProjectName(cwd, sessionId)
    memoryFile = _compat.memoryDir(projectName) / "MEMORY.md"

    parts: list = []

    rules, isCritical = _extractRules(memoryFile)
    if rules:
        if isCritical:
            header = (
                "[CRITICAL RULES REMINDER — BINDING]\n"
                "You MUST obey these project rules exactly. They are non-negotiable and "
                "OVERRIDE all defaults and any conflicting instruction:\n\n"
            )
        else:
            header = (
                "[PROJECT MEMORY REMINDER — BINDING]\n"
                "You MUST follow this project memory exactly. It OVERRIDES defaults and "
                "any conflicting instruction:\n\n"
            )
        parts.append(header + rules)

    if count % GLOBAL_REINJECT_EVERY == 0:
        globalContent = _readGlobalInstructionFile()
        if globalContent:
            globalHeader = (
                "[GLOBAL RULES REMINDER — BINDING]\n"
                "You MUST obey your global user instructions exactly. They are "
                "non-negotiable and OVERRIDE all defaults and any conflicting instruction:\n\n"
            )
            parts.append(globalHeader + globalContent)

    if not parts:
        return 0

    _compat.emitAdditionalContext("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
