#!/usr/bin/env python3
"""
NOT PORTED: WrongStack has no compaction event.

Claude and Factory expose a SessionStart:compact matcher that re-fires when
the context window is compacted, so the hook can re-inject CLAUDE.md /
AGENTS.md after summarization. WrongStack's documented lifecycle (per
docs/hooks.md and packages/core/src/types/hooks.ts) has exactly five events:

  PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop

There is no SessionStart:compact equivalent, and no `compact` matcher
modifier. We therefore cannot reproduce compact-reinject behavior on
WrongStack as of this version.

This stub is kept so that:
- the WrongStack hooks tree still mirrors the claude/factory layout
  one-to-one (operators see the same file names across platforms)
- a future WrongStack release that adds a compact event can be wired here
  without restructuring config.json
- any operator who tries to wire it into a SessionStart hook will see the
  no-op and the docstring explains why it does nothing

If you need compaction re-injection on WrongStack today, the workaround is
to lean on the regular SessionStart hook (session-start.py), which loads
the global instruction file and MEMORY.md fresh on every session start.
Long sessions that compact mid-flight will not see those re-injected until
the next session.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402


def main() -> int:
    # Read input for fail-safe logging; no outcome is emitted.
    data = _compat.readInput()
    event = data.get("event")
    if event is not None and event != "SessionStart":
        # We were wired to a non-SessionStart event by mistake. Stay silent.
        return 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
