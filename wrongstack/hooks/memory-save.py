#!/usr/bin/env python3
"""
PostToolUse + Stop hook: incrementally saves session memory to MEMORY.md.

PostToolUse strategy:
- Every TRIGGER_EVERY tool calls (default 10), parse new session log lines
  since the last run and append a "### Session" entry to MEMORY.md.
- Tracks byte offset in a progress marker file so each run only reads NEW lines.
- Avoids re-parsing the entire multi-MB session log on every call.

Stop strategy:
- On Stop event, parse any remaining new lines since the last checkpoint
  and finalize the MEMORY.md entry.
- Clean up all progress and staging files.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRIGGER_EVERY = 10  # Fire every N tool calls
SESSION_HISTORY_MARKER = "## Session History"

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _stateDir(name: str) -> Path:
    return Path.home() / ".cli-tweaks" / name


def _progressPath(sessionId: str) -> Path:
    return _stateDir(".session-progress") / sessionId


def _stagingPath(sessionId: str) -> Path:
    return _stateDir(".session-staging") / sessionId


# ---------------------------------------------------------------------------
# Session log discovery
# ---------------------------------------------------------------------------

def _sessionLog(sessionId: str) -> Optional[Path]:
    registryPath = Path.home() / ".wrongstack" / "session-registry.json"
    if registryPath.exists():
        try:
            reg = json.loads(registryPath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            reg = {}
    else:
        reg = {}

    entry = None
    for v in reg.values():
        if isinstance(v, dict) and v.get("sessionId") == sessionId:
            entry = v
            break
    if not entry and sessionId in reg:
        entry = reg[sessionId]

    if entry:
        slug = entry.get("projectSlug", "")
        base = Path.home() / ".wrongstack" / "projects" / slug / "sessions"
        rest = sessionId.split("/")[-1]
        datePart = sessionId.split("/")[0]
        log = base / datePart / (rest + ".jsonl")
        if log.exists() and log.stat().st_size > 512:
            return log

    # Fallback: scan projects dir
    projectsBase = Path.home() / ".wrongstack" / "projects"
    for projDir in projectsBase.iterdir():
        if not projDir.is_dir():
            continue
        sessionsDir = projDir / "sessions"
        if not sessionsDir.is_dir():
            continue
        for dateDir in sessionsDir.iterdir():
            if not dateDir.is_dir():
                continue
            for logFile in dateDir.glob("*.jsonl"):
                if logFile.stat().st_size > 512 and sessionId in logFile.stem:
                    return logFile
    return None


# ---------------------------------------------------------------------------
# Parse new session log lines since last checkpoint
# ---------------------------------------------------------------------------

def _parseNewLines(logPath: Path, byteOffset: int) -> tuple[dict, int]:
    """Read session log from byteOffset onward. Returns (parsed_data, new_offset).

    Parsed data:
      - user_inputs: list of text strings
      - tool_counts: dict of {tool_name: count}
      - last_ts: ISO timestamp of the last event seen
    """
    try:
        size = logPath.stat().st_size
        if byteOffset >= size:
            return {"user_inputs": [], "tool_counts": {}, "last_ts": None}, byteOffset
        with open(logPath, "rb") as fh:
            fh.seek(byteOffset)
            raw = fh.read()
        newOffset = byteOffset + len(raw)
    except OSError:
        return {"user_inputs": [], "tool_counts": {}, "last_ts": None}, byteOffset

    userInputs: list = []
    toolCounts: dict = {}
    lastTs: Optional[str] = None

    for line in raw.splitlines():
        if not line:
            continue
        try:
            obj = json.loads(line.decode("utf-8", errors="replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        evtType = obj.get("type", "")
        ts = obj.get("ts")

        if evtType == "user_input":
            content = obj.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            userInputs.append(text)
            elif isinstance(content, str):
                userInputs.append(content.strip())

        elif evtType == "tool_call_end":
            name = obj.get("name", "")
            if name:
                toolCounts[name] = toolCounts.get(name, 0) + 1
            if ts:
                lastTs = ts

        elif evtType == "llm_response":
            content = obj.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text and len(text) > 20:
                            userInputs.append(text)

        elif ts:
            lastTs = ts

    return {
        "user_inputs": userInputs,
        "tool_counts": toolCounts,
        "last_ts": lastTs,
    }, newOffset


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------

def _loadProgress(sessionId: str) -> dict:
    path = _progressPath(sessionId)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"sessionId": sessionId, "logPath": None, "byteOffset": 0, "toolCount": 0, "lastEntryTs": None}


def _saveProgress(sessionId: str, progress: dict) -> None:
    path = _progressPath(sessionId)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Build session entry
# ---------------------------------------------------------------------------

def _buildEntry(parsed: dict, projectName: str, ts: str) -> str:
    userInputs = parsed.get("user_inputs", [])
    toolCounts = parsed.get("tool_counts", {})
    topics = _summariseInputs(userInputs)

    tools = ", ".join(f"{k}({v})" for k, v in sorted(toolCounts.items()) if v > 0) if toolCounts else "none"
    dateStr = _formatTs(ts)

    return f"""### Session {dateStr}

**Topics discussed:**
{chr(10).join(f"- {t}" for t in topics[:10]) if topics else "- (no clear topics)"}

**Tools used:** {tools}
"""


def _summariseInputs(inputs: list) -> list:
    topics, seen = [], set()
    for inp in inputs:
        if not inp or len(inp) < 10:
            continue
        words = inp.split()
        key = " ".join(w for w in words[:3] if len(w) > 3).lower()
        if key and key not in seen:
            seen.add(key)
            topics.append(inp[:100].split("\n")[0])
    return topics


def _formatTs(ts: str) -> str:
    if not ts:
        return "unknown"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+0000")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16] if ts else "unknown"


# ---------------------------------------------------------------------------
# Memory merge — append to existing MEMORY.md under ## Session History
# ---------------------------------------------------------------------------

def _mergeIntoMemory(projectName: str, newEntry: str) -> None:
    memDir = _stateDir("memory") / projectName
    memFile = memDir / "MEMORY.md"
    marker = SESSION_HISTORY_MARKER

    try:
        memDir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    existing = ""
    if memFile.exists():
        try:
            existing = memFile.read_text(encoding="utf-8")
        except (OSError, IOError):
            existing = ""

    if not existing.strip():
        content = (
            f"# {projectName} Project Memory\n\n"
            "[NO MEMORY YET] Populate from session history below.\n\n"
            f"## Session History\n\n"
            f"{newEntry}\n\n"
            "## CRITICAL RULES\n\n"
            "## Architecture & Config Facts\n\n"
            "## Active Warnings\n\n"
            "## Topic Files\n"
        )
    elif marker not in existing:
        m = re.search(r"\n## ", existing)
        if m:
            content = existing[:m.start()] + "\n\n" + marker + "\n\n" + newEntry + existing[m.start():]
        else:
            content = existing.rstrip() + "\n\n" + marker + "\n\n" + newEntry
    else:
        beforeMarker = existing.split(marker, 1)[0]
        rest = existing.split(marker, 1)[1]
        header = beforeMarker + marker + "\n"

        nextTop = re.search(r"\n## [^ ]", rest)
        if nextTop:
            restBefore = rest[:nextTop.start()]
            restFrom = rest[nextTop.start():]
        else:
            restBefore = rest
            restFrom = ""

        if restBefore.strip():
            sessionBlocks = list(re.finditer(r"(?<=\n)### Session ", restBefore))
            if sessionBlocks:
                lastS = sessionBlocks[-1]
                tail = restBefore[lastS.start():]
                endMatch = re.search(r"\n## [^ ]", tail)
                insertAfter = lastS.start() + (endMatch.start() if endMatch else len(restBefore))
                newRest = restBefore[:insertAfter] + "\n" + newEntry + restFrom
            else:
                newRest = restBefore.rstrip() + "\n" + newEntry + restFrom
        else:
            newRest = newEntry + restFrom

        content = header + newRest

    try:
        memFile.write_text(content, encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# PostToolUse entry point
# ---------------------------------------------------------------------------

def _postToolUseMain(data: dict) -> int:
    sessionId = data.get("session_id")
    if not sessionId:
        return 0

    cwd = data.get("cwd") or os.getcwd()

    sys.path.insert(0, str(Path(__file__).parent))
    import _compat  # noqa: E402

    projectName = _compat.resolveProjectName(cwd, sessionId)

    # Load or create progress
    progress = _loadProgress(sessionId)
    progress["toolCount"] = progress.get("toolCount", 0) + 1

    # Check if we should trigger
    if progress["toolCount"] < TRIGGER_EVERY:
        _saveProgress(sessionId, progress)
        return 0

    # Reset counter
    progress["toolCount"] = 0

    # Find or re-find the session log
    logPath = progress.get("logPath")
    if not logPath:
        found = _sessionLog(sessionId)
        if not found:
            _saveProgress(sessionId, progress)
            return 0
        logPath = str(found)
        progress["logPath"] = logPath

    lp = Path(logPath)
    if not lp.exists():
        _saveProgress(sessionId, progress)
        return 0

    # Parse new lines since last offset
    byteOffset = progress.get("byteOffset", 0)
    parsed, newOffset = _parseNewLines(lp, byteOffset)

    # Nothing new? skip
    userInputs = parsed.get("user_inputs", [])
    toolCounts = parsed.get("tool_counts", {})
    lastTs = parsed.get("last_ts")

    if not userInputs and not toolCounts:
        progress["byteOffset"] = newOffset
        _saveProgress(sessionId, progress)
        return 0

    # Build entry
    entry = _buildEntry(
        parsed, projectName,
        lastTs or datetime.now(timezone.utc).isoformat()
    )

    # Merge into MEMORY.md
    _mergeIntoMemory(projectName, entry)

    # Update progress
    progress["byteOffset"] = newOffset
    if lastTs:
        progress["lastEntryTs"] = lastTs
    _saveProgress(sessionId, progress)
    return 0


# ---------------------------------------------------------------------------
# Stop entry point
# ---------------------------------------------------------------------------

def _stopMain(data: dict) -> int:
    sessionId = data.get("session_id") or str(os.getppid())
    cwd = data.get("cwd") or os.getcwd()

    sys.path.insert(0, str(Path(__file__).parent))
    import _compat  # noqa: E402

    projectName = _compat.resolveProjectName(cwd, sessionId)

    # Write stop marker
    _compat.writeStopMarker(sessionId, projectName)

    # Final parse: read any remaining new lines since last checkpoint
    progress = _loadProgress(sessionId)
    logPath = progress.get("logPath")
    if logPath:
        lp = Path(logPath)
        if lp.exists():
            byteOffset = progress.get("byteOffset", 0)
            parsed, _ = _parseNewLines(lp, byteOffset)
            userInputs = parsed.get("user_inputs", [])
            toolCounts = parsed.get("tool_counts", {})
            lastTs = parsed.get("last_ts")
            if userInputs or toolCounts:
                entry = _buildEntry(
                    parsed, projectName,
                    lastTs or datetime.now(timezone.utc).isoformat()
                )
                _mergeIntoMemory(projectName, entry)

    # Clean up progress and staging files
    for path in [_progressPath(sessionId), _stagingPath(sessionId)]:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    sys.path.insert(0, str(Path(__file__).parent))
    import _compat  # noqa: E402

    data = _compat.readInput()
    event = data.get("event", "")

    if event == "PostToolUse":
        return _postToolUseMain(data)
    elif event == "Stop":
        return _stopMain(data)
    else:
        # Called directly (e.g., from session-start as cleanup) — treat as Stop
        return _stopMain(data)


if __name__ == "__main__":
    sys.exit(main())
