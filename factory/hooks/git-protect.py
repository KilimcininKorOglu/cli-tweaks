#!/usr/bin/env python3
"""
PreToolUse hook: blocks `git add -f` / `git add --force` on files
listed in the global gitignore. Prevents Claude from bypassing
gitignore protection with force-add.
"""
import json
import os
import re
import sys

try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

if data.get("tool_name") != "Bash":
    sys.exit(0)

command = data.get("tool_input", {}).get("command", "")

if not re.search(r"\bgit\s+add\b", command):
    sys.exit(0)

if not re.search(r"\s-f\b|\s--force\b", command):
    sys.exit(0)

gitignore_path = os.path.expanduser("~/.gitignore_global")
if not os.path.isfile(gitignore_path):
    sys.exit(0)

with open(gitignore_path, "r") as f:
    ignored_entries = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#") and not line.startswith("!")
    ]

matched = []
for entry in ignored_entries:
    clean = entry.rstrip("/").lstrip("*").lstrip(".")
    raw = entry.rstrip("/")
    if raw and raw in command:
        matched.append(entry)
    elif clean and clean in command:
        matched.append(entry)

if matched:
    reason = (
        f"BLOCKED: `git add -f` on protected file(s): {', '.join(matched)}. "
        f"These files are in the global gitignore for a reason. "
        f"Analyze the root cause of the error instead of force-adding."
    )
    # Exit code 2 forces a PreToolUse block: the agent ignores stdout, feeds
    # stderr back to the model as the reason, and aborts the tool call. The
    # previous {"decision": {"behavior": "block", ...}} JSON is not a recognized
    # PreToolUse outcome (that shape belongs to PermissionRequest / the Agent
    # SDK) and was silently ignored, so the force-add proceeded.
    print(reason, file=sys.stderr)
    sys.exit(2)

sys.exit(0)
