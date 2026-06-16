"""
WrongStack hook compatibility shim.

WrongStack's hook wire format diverges from Claude Code in two layers:

1. Field names are camelCase (`toolName`, `toolInput`, `sessionId`) while our
   existing Python hook logic uses snake_case (`tool_name`, `tool_input`,
   `session_id`). For symmetry we read BOTH spellings and normalize to
   snake_case before handing the dict to a hook.
2. Outcome JSON is top-level: `{"decision": "block", "reason": "..."}` and
   `{"additionalContext": "..."}`. Claude's nested
   `{"hookSpecificOutput": {"additionalContext": "..."}}` and
   `{"decision": {"behavior": "block", "message": "..."}}` shapes are NOT
   recognized by WrongStack's shell-executor and would be silently dropped.

This module isolates those differences so each hook can stay focused on its
logic. It also centralizes:
- project name resolution (session lock > git root > cwd basename)
- per-session counter paths (keyed by WrongStack sessionId, not PPID)
- stop-marker read/write for the memory-save redesign (Stop is
  side-effects-only on WrongStack; we cannot block, so we leave a debug
  marker that session-start reads to soften the missing reminder).

All output helpers are final -- after calling one of them the caller should
`sys.exit(0)`. read_input() also exits 0 on broken/empty stdin (fail-safe).
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Paths (centralized so callers do not hardcode ~/.cli-tweaks/ layout)
# ---------------------------------------------------------------------------

def _stateDir(name: str) -> Path:
    return Path.home() / ".cli-tweaks" / name


def sessionLockPath(key: str) -> Path:
    """Return (do not create) the session-lock path for the given key.

    Key is normally WrongStack's sessionId; legacy PPID-based callers may pass
    str(os.getppid()) as a fallback.
    """
    return _stateDir(".session-locks") / key


def reinjectCounterPath(key: str) -> Path:
    return _stateDir(".reinject-counter") / key


def stopMarkerPath(key: str) -> Path:
    return _stateDir(".stop-reminded") / key


def logDir() -> Path:
    return _stateDir("logs")


def memoryDir(projectName: str) -> Path:
    return _stateDir("memory") / projectName


# ---------------------------------------------------------------------------
# Stdin / payload normalization
# ---------------------------------------------------------------------------

# Mapping from WrongStack camelCase to our internal snake_case. We accept BOTH
# spellings on read so that a hook built against the Claude format keeps
# working unchanged if a future port forgets to call read_input().
_FIELD_ALIASES = {
    "tool_name": "tool_name",
    "toolName": "tool_name",
    "tool_input": "tool_input",
    "toolInput": "tool_input",
    "tool_result": "tool_result",
    "toolResult": "tool_result",
    "session_id": "session_id",
    "sessionId": "session_id",
    "transcript_path": "transcript_path",
    "transcriptPath": "transcript_path",
    "user_prompt": "prompt",
    "prompt": "prompt",
    "cwd": "cwd",
    "event": "event",
    "stop_hook_active": "stop_hook_active",
}


def readInput() -> dict:
    """Read the WrongStack HookInput JSON from stdin and normalize to snake_case.

    Returns a dict with these keys (any may be missing): event, tool_name,
    tool_input, tool_result, prompt, cwd, session_id, transcript_path,
    stop_hook_active.

    Fails safe: on empty stdin, JSONDecodeError, or EOFError returns an empty
    dict. Callers should treat empty dict as "no payload, nothing to do" and
    exit 0 themselves.
    """
    try:
        raw = sys.stdin.read()
    except (OSError, EOFError):
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict = {}
    for srcKey, dstKey in _FIELD_ALIASES.items():
        if srcKey in data:
            # First-wins: snake_case takes precedence over camelCase alias.
            if dstKey not in out:
                out[dstKey] = data[srcKey]
    return out


# ---------------------------------------------------------------------------
# Outcome emission (top-level WrongStack shape)
# ---------------------------------------------------------------------------

def emitAdditionalContext(text: str) -> None:
    """Emit a top-level additionalContext outcome (SessionStart /
    UserPromptSubmit / PostToolUse). Caller should sys.exit(0) after."""
    sys.stdout.write(json.dumps({"additionalContext": text}))
    sys.stdout.write("\n")
    sys.stdout.flush()


def emitBlock(reason: str) -> None:
    """Emit a top-level block decision (PreToolUse / UserPromptSubmit).
    Caller should sys.exit(0) after."""
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}))
    sys.stdout.write("\n")
    sys.stdout.flush()


def emitAllow() -> None:
    """No-op allow outcome. Empty stdout, caller should sys.exit(0) after."""
    return


# ---------------------------------------------------------------------------
# Project name resolution
# ---------------------------------------------------------------------------

def _gitRootBasename(cwd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            return os.path.basename(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def resolveProjectName(cwd: str, sessionId: Optional[str] = None) -> str:
    """Pick a project name for memory paths in this order:

    1. Session lock file (writes by session-start, read by memory-reinject /
       memory-save). Lock key is the WrongStack sessionId when available,
       else the parent PID.
    2. Git root basename of cwd (single source of truth across all hooks
       in one session).
    3. Cwd basename as last resort.
    """
    keys: list = []
    if sessionId:
        keys.append(sessionId)
    keys.append(str(os.getppid()))
    for key in keys:
        path = sessionLockPath(key)
        try:
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
        except (FileNotFoundError, OSError):
            continue
    gitName = _gitRootBasename(cwd)
    if gitName:
        return gitName
    return os.path.basename(cwd or ".")


# ---------------------------------------------------------------------------
# Stop-marker side effects (memory-save redesign)
# ---------------------------------------------------------------------------

def writeStopMarker(sessionId: str, project: str) -> None:
    """Record that a Stop event fired for this session.

    WrongStack's Stop is "side effects only" -- decision.block is ignored, so
    the Claude pattern of "block the first stop, let the second through"
    cannot be reproduced. Instead we drop a marker file and append a log
    line; session-start reads the marker and softens the missing reminder
    on the next session.

    Always silent. Never raises (the agent loop must not break on this).
    """
    if not sessionId:
        return
    try:
        markerDir = stopMarkerPath("").parent
        markerDir.mkdir(parents=True, exist_ok=True)
        stopMarkerPath(sessionId).write_text(project, encoding="utf-8")
        logDir().mkdir(parents=True, exist_ok=True)
        logFile = logDir() / "memory-save.log"
        with logFile.open("a", encoding="utf-8") as fh:
            fh.write("{}\t{}\t{}\n".format(sessionId, project, "stop-reminded"))
    except (OSError, IOError):
        # Fail-safe: a broken log dir must not break the agent loop.
        return


def readStopMarker(sessionId: str) -> bool:
    """Return True if a previous Stop on this sessionId left a marker."""
    if not sessionId:
        return False
    try:
        return stopMarkerPath(sessionId).exists()
    except OSError:
        return False
