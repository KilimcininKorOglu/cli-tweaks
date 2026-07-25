#!/usr/bin/env python3
"""
Stop hook: reminds the agent to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks agent to save memory.
On second stop (stop_hook_active=true): allows agent to stop normally.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _project_name_from_git_common_dir(cwd):
    """Return the primary repository basename from git metadata, including worktrees."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return ""
        common_dir = Path(result.stdout.strip()).resolve()
        if common_dir.name == ".git":
            return common_dir.parent.name
        if common_dir.parent.name == "worktrees" and common_dir.parent.parent.name == ".git":
            return common_dir.parent.parent.parent.name
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def _resolveProjectName(cwd):
    """Return git root basename if available, otherwise cwd basename."""
    project_name = _project_name_from_git_common_dir(cwd)
    if project_name:
        return project_name
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
    return os.path.basename(cwd)


def _isValidProjectName(projectName):
    """Return whether a session lock value is safe to use as a project memory key."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", projectName):
        return False
    if projectName.startswith("agent-"):
        return False
    return True


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# If already triggered once this turn, let agent stop
stopHookActive = inputData.get("stop_hook_active", False)
if stopHookActive:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())

# Read locked project name from session start, fallback to resolving fresh.
# Agent subprocesses can inherit a lock keyed by their agent id. Ignore those
# values so memory remains attached to the real repository.
lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
try:
    lockedProjectName = lockFile.read_text(encoding="utf-8").strip()
except (FileNotFoundError, OSError):
    lockedProjectName = ""

resolvedProjectName = _resolveProjectName(cwd)
if lockedProjectName and _isValidProjectName(lockedProjectName):
    projectName = lockedProjectName
else:
    projectName = resolvedProjectName

memoryDir = Path.home() / ".cli-tweaks" / "memory" / projectName

# Ensure memory directory exists
memoryDir.mkdir(parents=True, exist_ok=True)

# Check if memory file exists
memoryFile = memoryDir / "MEMORY.md"
hasMemory = memoryFile.exists()

# Read the memory file once to drive two checks: content SIZE (offload prompt)
# and presence of the required '## CRITICAL RULES' section (format/migration).
# Size is measured in CHARACTERS, not lines: line count is gameable by cramming
# detail into long single-line bullets, so it is a poor proxy for real bloat.
MEMORY_SOFT_LIMIT_LINES = 180
MEMORY_SOFT_LIMIT_CHARS = 45000
# Per-bullet cap: aggregate caps (lines/chars) only catch TOTAL bloat, so a few
# 1500-char paragraph-bullets slip through while the file total stays small. A
# bullet this long soft-wraps in any editor and is unscannable. Flag each bullet
# over the cap so its detail gets split into focused bullets or pushed to a topic
# file, leaving MEMORY.md a lean index.
MEMORY_MAX_BULLET_CHARS = 600
lineCount = 0
charCount = 0
hasCriticalSection = False
longBullets = []
if hasMemory:
    try:
        memoryText = memoryFile.read_text(encoding="utf-8")
        memoryLines = memoryText.splitlines()
        lineCount = len(memoryLines)
        charCount = len(memoryText)
        hasCriticalSection = any(
            line.strip().lower() == "## critical rules" for line in memoryLines
        )
        for idx, line in enumerate(memoryLines, start=1):
            if line.startswith("- ") and len(line) > MEMORY_MAX_BULLET_CHARS:
                longBullets.append((idx, len(line), line[:55]))
    except (OSError, IOError):
        lineCount = 0
        charCount = 0

TEMPLATE = (
    "MEMORY.md MUST use exactly these four sections, in this order:\n"
    "  ## CRITICAL RULES        - non-negotiable project-scoped active rules, imperative mood\n"
    "  ## Architecture & Config Facts - project-scoped stable technical context, not rules\n"
    "  ## Active Warnings       - project-scoped pitfalls and recurring mistakes\n"
    "  ## Topic Files           - pointers to detail files (e.g. history.md)\n"
    "Only record project-scoped learnings in this project MEMORY.md. A learning is project-scoped "
    "only when it changes future behavior for this repository's code, commands, architecture, "
    "configuration, deployment, tests, or product preferences. Do not write global Claude Code "
    "behavior, shared skill workflow rules, general agent preferences, or cross-project policies "
    "to this project MEMORY.md. Put global rules in the appropriate global instruction or shared "
    "skill file instead. If the scope is unclear, do not write it here. Keep each bullet to ONE "
    "focused project rule or fact; strip narrative, examples, and dated context to a topic file "
    "(history.md, or a dedicated subject file for a large topic, listed under '## Topic Files'). "
    "TWO caps BOTH apply (under 200 lines AND under 50000 characters), so keep bullets concise "
    "and do NOT pad them into long single lines.\n"
)

if hasMemory:
    reason = (
        "MANDATORY before stopping — these are HARD rules, not suggestions; apply each:\n"
        "1. If you learned an ACTIVE PROJECT-SCOPED RULE that changes future behavior for "
        "this repository's code, commands, architecture, configuration, deployment, tests, "
        "or product preferences, you MUST record it in {dir}/MEMORY.md in imperative mood — "
        "under '## CRITICAL RULES' when it is a behavior rule. Do NOT write global Claude Code "
        "behavior, shared skill workflow rules, general agent preferences, or cross-project "
        "policies to this project MEMORY.md; put those in the appropriate global instruction "
        "or shared skill file instead. If the scope is unclear, do not write it here.\n"
        "2. NEVER write commit hashes, dated fix histories, completed-slice/feature DONE-records, "
        "or any archival narrative to MEMORY.md — these are FORBIDDEN there. ALL historical detail "
        "goes to a topic file ONLY — history.md by default, or a dedicated subject file when a topic "
        "grows large enough to warrant its own (list any new topic file under '## Topic Files'). "
        "Enforce this at WRITE time, not merely as an afterthought.\n"
        "3. MEMORY.md holds ONLY durable rules, patterns, and stable facts, each as ONE focused "
        "bullet — strip narrative, examples, dated context, and completed-work detail to a topic "
        "file (history.md, or a dedicated subject file for a large topic). "
        "TWO caps BOTH apply: keep it under 200 lines AND under 50000 characters. Do NOT cram "
        "multiple ideas into one long line to dodge the line cap — the character cap catches that. "
        "If either is exceeded, move the oldest/least-critical entries to history.md this same session.\n"
        "4. Write memory in English ONLY.\n"
        "If nothing new was learned and the file already obeys ALL of the above, just stop."
    ).format(dir=memoryDir)
else:
    reason = (
        "MANDATORY before stopping — this is a new project with no memory yet. "
        "You MUST create {dir}/MEMORY.md following the template below, with project-scoped "
        "rules in imperative mood. Record only learnings that change future behavior for this "
        "repository's code, commands, architecture, configuration, deployment, tests, or product "
        "preferences. Do NOT write global Claude Code behavior, shared skill workflow rules, "
        "general agent preferences, or cross-project policies to this project MEMORY.md; put those "
        "in the appropriate global instruction or shared skill file instead. If the scope is "
        "unclear, do not write it here. NEVER write commit hashes or dated history to MEMORY.md — "
        "historical detail goes to a topic file only (history.md by default, or a dedicated subject "
        "file for a large topic). Keep it lean — bounded by BOTH a line cap (under 200) and a "
        "character cap (under 50000) — and in English ONLY. Each bullet is ONE focused project "
        "rule or fact; no narrative or padding. Skip this ONLY if the session was genuinely trivial "
        "with nothing project-scoped worth remembering.\n"
        + TEMPLATE
    ).format(dir=memoryDir)

if hasMemory and not hasCriticalSection:
    reason += (
        "\nMANDATORY MIGRATION: MEMORY.md is MISSING the '## CRITICAL RULES' section, "
        "so it is NOT in the required format. You MUST restructure the whole file this "
        "session into the four-section template, in this exact order:\n"
        "  ## CRITICAL RULES        - non-negotiable project-scoped active rules, imperative mood\n"
        "  ## Architecture & Config Facts - project-scoped stable technical context, not rules\n"
        "  ## Active Warnings       - project-scoped pitfalls and recurring mistakes\n"
        "  ## Topic Files           - pointers to detail files (e.g. history.md)\n"
        "Preserve all real content, reorganize it under those sections, and convert "
        "rules to imperative mood. Do this before stopping."
    )

if hasMemory and (lineCount >= MEMORY_SOFT_LIMIT_LINES or charCount >= MEMORY_SOFT_LIMIT_CHARS):
    reason += (
        "\nMANDATORY OFFLOAD: MEMORY.md is now {ln} lines / {ch} characters — at or near a cap "
        "(BOTH limits apply: keep under 200 lines AND under 50000 characters). You MUST move the "
        "oldest/least-critical entries (resolved warnings, superseded facts, dated notes, "
        "completed-work records) to a topic file (history.md, or a dedicated subject file when a "
        "topic is large) THIS session, leaving MEMORY.md a "
        "lean index of ACTIVE rules and current architecture facts."
    ).format(ln=lineCount, ch=charCount)

if hasMemory and longBullets:
    offenders = "\n".join(
        "  - line {ln} ({ch} chars): {pre}...".format(ln=ln, ch=ch, pre=pre)
        for ln, ch, pre in longBullets
    )
    reason += (
        "\nMANDATORY BULLET SPLIT: {n} bullet(s) exceed {cap} characters — a single bullet this "
        "long soft-wraps in an editor and is unscannable. Each bullet MUST be ONE focused rule or "
        "fact. Fix each by EITHER splitting it into multiple focused bullets, OR moving its detail "
        "(recipe steps, examples, multi-aspect notes) to a topic file and leaving the load-bearing "
        "rule as a lean line with a '(detail in <topic>.md)' pointer. Prefer SPLITTING for "
        "'## CRITICAL RULES' (only that section is re-injected periodically, so its detail must "
        "stay in MEMORY.md) and OFFLOADING for architecture facts. The exception is an irreducible "
        "safety rule whose detail is the rule itself (e.g. an exact regex/command) — keep it whole. "
        "Over-cap bullets:\n{list}"
    ).format(n=len(longBullets), cap=MEMORY_MAX_BULLET_CHARS, list=offenders)

output = {
    "decision": "block",
    "reason": reason,
}
print(json.dumps(output))
sys.exit(0)
