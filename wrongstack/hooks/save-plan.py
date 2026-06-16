#!/usr/bin/env python3
"""
PostToolUse hook: sends a desktop notification when a plan/spec is finalized.

Heuristic matcher v1.

WrongStack's plan-exit tool name is not documented in the README surface we
audited. SpecParser is mentioned but the tool that triggers PostToolUse for
"the spec was finalized" is not named explicitly. Until we can confirm the
exact tool name against a real WrongStack install, we accept any PostToolUse
whose tool_name contains (case-insensitive) one of:

  plan, spec, exitplan, exitspec, exitspecmode

If none of those match, we silently no-op. This is intentionally permissive:
a false positive just shows a notification; a false negative means we miss
the plan-save event. Misses are easier to spot (the user expected a ping and
did not get one) than over-firing.

Unlike the Claude port, we do not need transcript_path: WrongStack does not
expose it in HookInput. We find the most recently modified .md under
~/.wrongstack/plans/ instead. If the dir is missing or empty, skip silently.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402
from notify import isEnabledFor, notify  # noqa: E402


PLAN_TOOL_HINTS = ("plan", "spec", "exitplan", "exitspec", "exitspecmode")
PLANS_DIR = Path.home() / ".wrongstack" / "plans"


def _looksLikePlanTool(toolName: str) -> bool:
    if not toolName:
        return False
    lowered = toolName.lower()
    return any(hint in lowered for hint in PLAN_TOOL_HINTS)


def _latestPlanName(plansDir: Path) -> str:
    try:
        if not plansDir.exists():
            return ""
        files = sorted(plansDir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    except OSError:
        return ""
    if not files:
        return ""
    return files[0].stem


def main() -> int:
    data = _compat.readInput()
    if data.get("event") != "PostToolUse":
        return 0
    toolName = data.get("tool_name") or ""
    if not _looksLikePlanTool(toolName):
        return 0

    planName = _latestPlanName(PLANS_DIR)
    if not planName:
        return 0

    if isEnabledFor("PlanSave"):
        notify("Plan Complete", planName, subtitle="WrongStack")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
