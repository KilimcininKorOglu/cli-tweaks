#!/usr/bin/env python3
"""
Stop hook: automatically saves session memory to memory/<projectName>/MEMORY.md.

Design:
- Read the session's JSONL log to extract what was discussed and done.
- Generate a structured memory entry with topics, findings, and actions.
- Append to MEMORY.md under a "## Session History" section.
- If no log is found (session ended too fast), write a minimal entry.
- Sensible redaction: skips API keys, tokens, passwords in user input.

WrongStack's Stop event is "side effects only" (decision:block is ignored),
so we write memory here rather than blocking to ask the model.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import _compat  # noqa: E402

# ── sensitive-value redaction ────────────────────────────────────────────────

_REALLY_SENSITIVE = re.compile(
    r"(?i)"
    r"(api[_-]?key|secret[_-]?key|password|token|bearer|auth)"
    r"|"
    r"(sk[-_]?[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|"
    r"xox[baprs]-[a-zA-Z0-9]{10,}|"
    r"amzn\.mfa\.[a-zA-Z0-9=]{50,})"
)


def _is_sensitive(text: str) -> bool:
    return bool(_REALLY_SENSITIVE.search(text))


# ── session log discovery ────────────────────────────────────────────────────

def _session_log_for_current_session(
    session_id: str, project_root: str
) -> Optional[Path]:
    """
    Find the JSONL log for the given session_id.

    Strategy:
    1. Look up the session registry -> projectSlug -> construct path directly.
    2. Scan ~/.wrongstack/projects/*/sessions/ for a .jsonl file whose
       basename (without .jsonl) matches session_id (with / replaced by -).
    3. Fall back to 'active.json' for each project.
    """
    registry_path = Path.home() / ".wrongstack" / "session-registry.json"
    reg = {}
    if registry_path.exists():
        try:
            reg = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    # Step 1: direct registry lookup
    entry = None
    for v in reg.values():
        if isinstance(v, dict) and v.get("sessionId") == session_id:
            entry = v
            break
    if not entry and session_id in reg:
        entry = reg[session_id]

    if entry:
        slug = entry.get("projectSlug", "")
        base = Path.home() / ".wrongstack" / "projects" / slug / "sessions"
        fname = session_id.replace("/", "-") + ".jsonl"
        log = base / fname
        if log.exists() and log.stat().st_size > 512:
            return log
        date_part = session_id.split("/")[0]
        time_part = session_id.split("/")[-1]
        log2 = base / date_part / (time_part + ".jsonl")
        if log2.exists() and log2.stat().st_size > 512:
            return log2

    # Step 2: scan all project sessions directories
    projects_base = Path.home() / ".wrongstack" / "projects"
    for proj_dir in projects_base.iterdir():
        if not proj_dir.is_dir():
            continue
        sessions_dir = proj_dir / "sessions"
        if not sessions_dir.is_dir():
            continue
        fname = session_id.replace("/", "-") + ".jsonl"
        log = sessions_dir / fname
        if log.exists() and log.stat().st_size > 512:
            return log
        date_part = session_id.split("/")[0]
        time_part = session_id.split("/")[-1]
        log2 = sessions_dir / date_part / (time_part + ".jsonl")
        if log2.exists() and log2.stat().st_size > 512:
            return log2

    # Step 3: active.json fallback
    for proj_dir in projects_base.iterdir():
        if not proj_dir.is_dir():
            continue
        sessions_dir = proj_dir / "sessions"
        active = sessions_dir / "active.json"
        if not active.exists():
            continue
        try:
            info = json.loads(active.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        active_sid = info.get("sessionId", "")
        if not active_sid or active_sid == session_id:
            continue
        fname = active_sid.replace("/", "-") + ".jsonl"
        log = sessions_dir / fname
        if log.exists() and log.stat().st_size > 512:
            return log
        date_part = active_sid.split("/")[0]
        time_part = active_sid.split("/")[-1]
        log2 = sessions_dir / date_part / (time_part + ".jsonl")
        if log2.exists() and log2.stat().st_size > 512:
            return log2

    return None


# ── JSONL parsing ────────────────────────────────────────────────────────────

def _parse_session_log(log_path: Path) -> dict:
    """Return summary dict from a session JSONL file."""
    events = []
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        return {
            "user_inputs": [], "llm_responses": [],
            "tool_counts": {}, "session_start": None, "session_end": None,
        }

    user_inputs: list[str] = []
    llm_responses: list[str] = []
    tool_counts: dict[str, int] = {}
    session_start: Optional[str] = None
    session_end: Optional[str] = None

    for e in events:
        t = e.get("type")
        if t == "session_start":
            session_start = e.get("ts")
        elif t == "session_end":
            session_end = e.get("ts")
        elif t == "user_input":
            for block in e.get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text and not _is_sensitive(text):
                        user_inputs.append(text)
        elif t == "llm_response":
            for block in e.get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if len(text) > 80 and not _is_sensitive(text):
                        llm_responses.append(text[:500])
        elif t == "tool_call_end":
            name = e.get("name", "?")
            if name and name != "?":
                tool_counts[name] = tool_counts.get(name, 0) + 1

    return {
        "user_inputs": user_inputs,
        "llm_responses": llm_responses,
        "tool_counts": tool_counts,
        "session_start": session_start,
        "session_end": session_end,
    }


# ── topic extraction ──────────────────────────────────────────────────────────

_TOPIC_PATTERNS = [
    (("understand", "project", "overview"), "Project overview research"),
    (("hooks", "hook"), "Hooks system analysis"),
    (("memory",), "Memory system investigation"),
    (("bug", "issue", "problem"), "Bug investigation"),
    (("git", "branch", "commit"), "Git operations"),
    (("fix", "repair", "update"), "Code fix or update"),
    (("research", "analyse", "analyze"), "Research and analysis"),
    (("build", "install", "setup"), "Build or setup"),
    (("read", "file", "directory"), "File/directory exploration"),
    (("test", "testing"), "Testing"),
]


def _summarise_inputs(inputs: list[str]) -> list[str]:
    topics = []
    seen = set()
    for inp in inputs:
        lower = inp.lower()
        for pattern, label in _TOPIC_PATTERNS:
            if any(p in lower for p in pattern) and label not in seen:
                topics.append(label)
                seen.add(label)
    return topics


# ── timestamp formatting ─────────────────────────────────────────────────────

def _format_ts(ts: Optional[str]) -> str:
    if not ts:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return ts[:16] if ts else "unknown"


# ── memory entry generation ───────────────────────────────────────────────────

def _generate_memory_entry(parsed: dict, project_name: str) -> str:
    inputs = parsed.get("user_inputs", [])
    responses = parsed.get("llm_responses", [])
    tools = parsed.get("tool_counts", {})
    start = parsed.get("session_start")
    end = parsed.get("session_end")
    date_str = _format_ts(start) if start else datetime.now(
        timezone.utc).strftime("%Y-%m-%d")

    topics = _summarise_inputs(inputs)
    last_resp = responses[-1] if responses else ""

    lines = [f"### Session {date_str}\n"]
    lines.append(
        f"**Time:** {start[:16] if start else '?'} -> {end[:16] if end else '?'}\n"
    )

    if topics:
        lines.append("**Topics discussed:**")
        for t in topics:
            lines.append(f"- {t}")
        lines.append("")

    if last_resp:
        summary = last_resp.split("\n")[0][:200].strip()
        if summary:
            lines.append(f"**Outcome:** {summary}\n")

    if tools:
        top = sorted(tools.items(), key=lambda x: -x[1])[:6]
        tool_str = ", ".join(f"{n} ({c}x)" for n, c in top)
        lines.append(f"**Tools used:** {tool_str}\n")

    lines.append("")
    return "\n".join(lines)


# ── MEMORY.md merging ────────────────────────────────────────────────────────

def _build_memory_content(
    existing: str, new_entry: str, project_name: str
) -> str:
    """
    Merge new_entry into existing MEMORY.md content.

    Handles three cases:
    1. Empty file -> fresh template
    2. Marker absent -> insert after title / before first heading
    3. Marker present -> append after last ### Session block
    """
    marker = "## Session History"

    if not existing.strip():
        template = (
            "# {project} Project Memory\n"
            "\n"
            "[NO MEMORY YET] Populate from session history below.\n"
            "\n"
            "## Session History\n"
            "\n"
            "{entry}"
            "\n"
            "## CRITICAL RULES\n"
            "\n"
            "## Architecture & Config Facts\n"
            "\n"
            "## Active Warnings\n"
            "\n"
            "## Topic Files\n"
        )
        return template.format(project=project_name, entry=new_entry)

    if marker not in existing:
        # Insert ## Session History + entry after the title block,
        # before any existing top-level ## heading.
        # The title block ends at the first blank line followed by a ## heading.
        m = re.search(r"\n\n## ", existing)
        if m:
            idx = m.start()
            return existing[:idx] + "\n\n" + marker + "\n\n" + new_entry + existing[idx:]
        # Fallback: append before first ## heading anywhere
        first = re.search(r"\n## ", existing)
        if first:
            return existing[:first.start()] + marker + "\n\n" + new_entry + "\n\n" + existing[first.start():]
        # No headings at all — append at end
        return existing.rstrip() + "\n\n" + marker + "\n\n" + new_entry

    # Marker exists: insert after the last ### Session block
    parts = existing.split(marker, 1)
    header = parts[0] + marker + "\n"
    rest = parts[1]

    next_heading = re.search(r"\n## [^ ]", rest)
    if next_heading:
        idx = next_heading.start()
        rest_before = rest[:idx]
        rest_from = rest[idx:]
    else:
        rest_before = rest
        rest_from = ""

    if rest_before.strip():
        last_session = list(re.finditer(r"(?<=\n)### Session ", rest_before))
        if last_session:
            last_start = last_session[-1].start()
            tail = rest_before[last_start:]
            end_match = re.search(r"\n## [^ ]", tail)
            insert_pos = last_start + (
                end_match.start() if end_match else len(rest_before)
            )
            new_rest = (
                rest_before[:insert_pos]
                + "\n"
                + new_entry
                + rest_from
            )
        else:
            new_rest = rest_before.rstrip() + "\n" + new_entry + rest_from
    else:
        new_rest = new_entry + rest_from

    return parts[0] + header + new_rest


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    data = _compat.readInput()
    cwd = data.get("cwd") or os.getcwd()
    session_id = data.get("session_id") or str(os.getppid())
    project_name = _compat.resolveProjectName(cwd, session_id)

    # Write stop marker (keep existing behaviour)
    _compat.writeStopMarker(session_id, project_name)

    # Locate session log
    log_path = _session_log_for_current_session(session_id, cwd)

    if log_path and log_path.exists() and log_path.stat().st_size > 512:
        parsed = _parse_session_log(log_path)
    else:
        parsed = {
            "user_inputs": [], "llm_responses": [],
            "tool_counts": {}, "session_start": None, "session_end": None,
        }

    entry = _generate_memory_entry(parsed, project_name)

    mem_dir = _compat.memoryDir(project_name)
    mem_file = mem_dir / "MEMORY.md"

    try:
        mem_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    existing = ""
    if mem_file.exists():
        try:
            existing = mem_file.read_text(encoding="utf-8")
        except (OSError, IOError):
            existing = ""

    new_content = _build_memory_content(existing, entry, project_name)

    try:
        mem_file.write_text(new_content, encoding="utf-8")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
