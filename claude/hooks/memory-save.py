#!/usr/bin/env python3
"""
Stop hook: reminds the agent to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks agent to save memory.
On second stop (stop_hook_active=true): allows agent to stop normally.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def _resolveProjectName(cwd):
    """Return git root basename if available, otherwise cwd basename."""
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


try:
    inputData = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# If already triggered once this turn, let agent stop
stopHookActive = inputData.get("stop_hook_active", False)
if stopHookActive:
    sys.exit(0)

cwd = inputData.get("cwd", os.getcwd())

# Read locked project name from session start, fallback to resolving fresh
lockFile = Path.home() / ".cli-tweaks" / ".session-locks" / str(os.getppid())
try:
    projectName = lockFile.read_text(encoding="utf-8").strip()
except (FileNotFoundError, OSError):
    projectName = _resolveProjectName(cwd)

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
    "  ## CRITICAL RULES        - non-negotiable active rules, imperative mood\n"
    "  ## Architecture & Config Facts - stable technical context (not rules)\n"
    "  ## Active Warnings       - pitfalls and recurring mistakes\n"
    "  ## Topic Files           - pointers to detail files (e.g. history.md)\n"
    "Keep each bullet to ONE focused rule or fact; strip narrative, examples, and dated "
    "context to a topic file (history.md, or a dedicated subject file for a large topic — "
    "listed under '## Topic Files'). TWO caps BOTH apply (under 200 lines AND under 50000 characters), "
    "so keep bullets concise and do NOT pad them into long single lines.\n"
)

if hasMemory:
    reason = (
        "MANDATORY before stopping — these are HARD rules, not suggestions; apply each:\n"
        "1. If you learned an ACTIVE RULE that changes future behavior (a build/test command, "
        "an architecture fact, a user preference, a workflow rule), you MUST record it in "
        "{dir}/MEMORY.md in imperative mood — under '## CRITICAL RULES' when it is a behavior rule.\n"
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
        "You MUST create {dir}/MEMORY.md following the template below, with rules in imperative "
        "mood. NEVER write commit hashes or dated history to MEMORY.md — historical detail goes "
        "to a topic file only (history.md by default, or a dedicated subject file for a large topic). "
        "Keep it lean — bounded by BOTH a line cap (under 200) and a character "
        "cap (under 50000) — and in English ONLY. Each bullet is ONE focused rule; no narrative or "
        "padding. Skip this ONLY if the session was genuinely trivial with nothing worth remembering.\n"
        + TEMPLATE
    ).format(dir=memoryDir)

if hasMemory and not hasCriticalSection:
    reason += (
        "\nMANDATORY MIGRATION: MEMORY.md is MISSING the '## CRITICAL RULES' section, "
        "so it is NOT in the required format. You MUST restructure the whole file this "
        "session into the four-section template, in this exact order:\n"
        "  ## CRITICAL RULES        - non-negotiable active rules, imperative mood\n"
        "  ## Architecture & Config Facts - stable technical context (not rules)\n"
        "  ## Active Warnings       - pitfalls and recurring mistakes\n"
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
