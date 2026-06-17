#!/usr/bin/env python3
"""
Stop hook: automatically saves session memory to memory/<projectName>/MEMORY.md.

Session log discovery + JSONL parsing + MEMORY.md merge.
WrongStack Stop event: decision:block is ignored, so we write directly.
"""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import _compat

# ── session log discovery ────────────────────────────────────────────────────

def _session_log_for_current_session(session_id: str, project_root: str) -> Optional[Path]:
    registry_path = Path.home() / ".wrongstack" / "session-registry.json"
    reg = {}
    if registry_path.exists():
        try:
            reg = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

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

    projects_base = Path.home() / ".wrongstack" / "projects"
    for proj_dir in projects_base.iterdir():
        if not proj_dir.is_dir():
            continue
        sessions_dir = proj_dir / "sessions"
        if not sessions_dir.is_dir():
            continue
        date_part = session_id.split("/")[0]
        time_part = session_id.split("/")[-1]
        log2 = sessions_dir / date_part / (time_part + ".jsonl")
        if log2.exists() and log2.stat().st_size > 512:
            return log2
        fname = session_id.replace("/", "-") + ".jsonl"
        log = sessions_dir / fname
        if log.exists() and log.stat().st_size > 512:
            return log

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
        date_part = active_sid.split("/")[0]
        time_part = active_sid.split("/")[-1]
        log2 = sessions_dir / date_part / (time_part + ".jsonl")
        if log2.exists() and log2.stat().st_size > 512:
            return log2

    return None


# ── JSONL parsing ───────────────────────────────────────────────────────────

_REALLY_SENSITIVE = re.compile(
    r"(?i)(api[_-]?key|secret|password|token|bearer|auth)|"
    r"(sk[-_]?[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36,}|"
    r"xox[baprs]-[a-zA-Z0-9]{10,}|amzn\.mfa\.[a-zA-Z0-9=]{50,})"
)


def _parse_session_log(log_path: Path) -> dict:
    events = []
    try:
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except OSError:
        return {"user_inputs": [], "llm_responses": [], "tool_counts": {}, "session_start": None, "session_end": None}

    user_inputs, llm_responses, tool_counts = [], [], {}
    session_start = session_end = None

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
                    if text and not _REALLY_SENSITIVE.search(text):
                        user_inputs.append(text)
        elif t == "llm_response":
            for block in e.get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if len(text) > 80 and not _REALLY_SENSITIVE.search(text):
                        llm_responses.append(text[:500])
        elif t == "tool_call_end":
            name = e.get("name", "?")
            if name and name != "?":
                tool_counts[name] = tool_counts.get(name, 0) + 1

    return {"user_inputs": user_inputs, "llm_responses": llm_responses, "tool_counts": tool_counts,
            "session_start": session_start, "session_end": session_end}


# ── topic extraction ─────────────────────────────────────────────────────

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


def _summarise_inputs(inputs):
    topics, seen = [], set()
    for inp in inputs:
        lo = inp.lower()
        for pat, label in _TOPIC_PATTERNS:
            if any(p in lo for p in pat) and label not in seen:
                topics.append(label)
                seen.add(label)
    return topics


def _format_ts(ts):
    if not ts:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return (ts[:16] if ts else "unknown") if ts else "unknown"


def _generate_memory_entry(parsed, project_name):
    inputs = parsed.get("user_inputs", [])
    responses = parsed.get("llm_responses", [])
    tools = parsed.get("tool_counts", {})
    start = parsed.get("session_start")
    end = parsed.get("session_end")
    date_str = _format_ts(start) if start else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    topics = _summarise_inputs(inputs)
    last_resp = responses[-1] if responses else ""

    lines = [f"### Session {date_str}\n"]
    lines.append(f"**Time:** {start[:16] if start else '?'} -> {end[:16] if end else '?'}\n")
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
        lines.append(f"**Tools used:** {', '.join(f'{n} ({c}x)' for n, c in top)}\n")
    lines.append("")
    return "\n".join(lines)


# ── MEMORY.md merging ────────────────────────────────────────────────────

def _build_memory_content(existing, new_entry, project_name):
    marker = "## Session History"

    if not existing.strip():
        return (
            "# {project} Project Memory\n\n"
            "[NO MEMORY YET] Populate from session history below.\n\n"
            "## Session History\n\n"
            "{{entry}}\n\n"
            "## CRITICAL RULES\n\n"
            "## Architecture & Config Facts\n\n"
            "## Active Warnings\n\n"
            "## Topic Files\n"
        ).format(project=project_name, entry=new_entry)

    if marker not in existing:
        m = re.search(r"\n\n## ", existing)
        if m:
            return existing[:m.start()] + "\n\n" + marker + "\n\n" + new_entry + existing[m.start():]
        first = re.search(r"\n## ", existing)
        if first:
            return existing[:first.start()] + marker + "\n\n" + new_entry + "\n\n" + existing[first.start():]
        return existing.rstrip() + "\n\n" + marker + "\n\n" + new_entry

    # split returns [before_marker, marker + rest]
    # before_marker ends right before the first char of the marker
    before_marker = existing.split(marker, 1)[0]
    rest = existing.split(marker, 1)[1]   # starts with \n\n...

    # header: before_marker + marker + \n
    # (before_marker already ends with \n\n before the marker)
    header = before_marker + marker + "\n"

    # Find insertion point: after the last ### Session block in the section
    next_top = re.search(r"\n## [^ ]", rest)
    if next_top:
        rest_before = rest[:next_top.start()]
        rest_from = rest[next_top.start():]
    else:
        rest_before = rest
        rest_from = ""

    if rest_before.strip():
        session_blocks = list(re.finditer(r"(?<=\n)### Session ", rest_before))
        if session_blocks:
            last_s = session_blocks[-1]
            tail = rest_before[last_s.start():]
            end_match = re.search(r"\n## [^ ]", tail)
            insert_after = last_s.start() + (end_match.start() if end_match else len(rest_before))
            new_rest = rest_before[:insert_after] + "\n" + new_entry + rest_from
        else:
            new_rest = rest_before.rstrip() + "\n" + new_entry + rest_from
    else:
        new_rest = new_entry + rest_from

    return header + new_rest


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    data = _compat.readInput()
    cwd = data.get("cwd") or os.getcwd()
    session_id = data.get("session_id") or str(os.getppid())
    project_name = _compat.resolveProjectName(cwd, session_id)

    _compat.writeStopMarker(session_id, project_name)

    log_path = _session_log_for_current_session(session_id, cwd)
    if log_path and log_path.exists() and log_path.stat().st_size > 512:
        parsed = _parse_session_log(log_path)
    else:
        parsed = {"user_inputs": [], "llm_responses": [], "tool_counts": {},
                  "session_start": None, "session_end": None}

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
