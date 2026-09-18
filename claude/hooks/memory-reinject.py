#!/usr/bin/env python3
"""
UserPromptSubmit hook: re-injects the global instruction files every
GLOBAL_REINJECT_EVERY prompts, to counter recency drift in long conversations.

session-start.py injects the files listed in `globalInjectFiles` of
~/.claude/settings.json at every session start. Over a long session the
model's attention drifts from that early block, so this hook re-surfaces the
same files periodically.

The project memory is not re-injected here: the memory-save mod loads MEMORY.md
at startup, resume, /clear and compaction only, so the context does not grow
with repeated copies.

The counter is keyed by the Claude Code process id. session-start.py resets it
at every session start and deletes the counters of processes that have ended.
A counter or an instruction file that cannot be read or written is reported to
the user with `systemMessage`.
"""
import json
import os
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, str(Path(__file__).parent))
from instructions import globalInjectFiles, readInstructions
from project import REINJECT_COUNTER_DIR

GLOBAL_REINJECT_EVERY = 15


def _report(message: str) -> NoReturn:
    """Show a hook problem to the user and end the hook without context."""
    print(json.dumps({"systemMessage": "memory-reinject.py: " + message}))
    sys.exit(0)


def _store(counterFile: Path, count: int) -> None:
    """Write the prompt counter, reporting a failed write."""
    try:
        counterFile.parent.mkdir(parents=True, exist_ok=True)
        counterFile.write_text(str(count), encoding="utf-8")
    except OSError as err:
        _report(f"cannot write the prompt counter {counterFile}: {err}")


def _nextCount(counterFile: Path) -> int:
    """Increment and store this session's prompt counter."""
    try:
        count = int(counterFile.read_text(encoding="utf-8").strip())
    except FileNotFoundError:
        count = 0
    except (OSError, UnicodeDecodeError, ValueError) as err:
        # Start the count again, so the next prompt does not hit the same error.
        _store(counterFile, 1)
        _report(f"cannot read the prompt counter {counterFile}, counting starts again: {err}")
    count += 1
    _store(counterFile, count)
    return count


try:
    json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

count = _nextCount(REINJECT_COUNTER_DIR / str(os.getppid()))
if count % GLOBAL_REINJECT_EVERY != 0:
    sys.exit(0)

errors: list[str] = []
contents = readInstructions(globalInjectFiles(errors), errors)

output: dict = {}
if contents:
    output["hookSpecificOutput"] = {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": (
            "[REMINDER OF THE USER'S GLOBAL INSTRUCTIONS]\n"
            "The user configured these global instructions and asked to be reminded of "
            "them in long sessions. Treat them as the user's own preferences and keep "
            "following them:\n\n" + "\n\n---\n\n".join(contents)
        ),
    }
if errors:
    output["systemMessage"] = "memory-reinject.py: " + "; ".join(errors)
if output:
    print(json.dumps(output))
sys.exit(0)
