#!/usr/bin/env python3
"""
Stop hook: reminds Droid to save learnings to memory before ending.

On first stop (stop_hook_active=false): blocks and asks Droid to save memory.
On second stop (stop_hook_active=true): allows Droid to stop normally.
"""
import json
import os
import sys
from pathlib import Path

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)

# If already triggered once this turn, let Droid stop
stop_hook_active = input_data.get("stop_hook_active", False)
if stop_hook_active:
    sys.exit(0)

cwd = input_data.get("cwd", os.getcwd())
project_name = os.path.basename(cwd)
memory_dir = Path.home() / ".factory" / "memory" / project_name

# Ensure memory directory exists
memory_dir.mkdir(parents=True, exist_ok=True)

# Check if memory file exists
memory_file = memory_dir / "MEMORY.md"
has_memory = memory_file.exists()

if has_memory:
    reason = (
        "Before stopping: if you learned anything new or useful in this session "
        "(build commands, architecture insights, debugging solutions, user preferences, "
        "workflow patterns), update your memory at {dir}/MEMORY.md or create/update "
        "topic files there. If nothing new was learned, just stop without changes. "
        "Keep MEMORY.md under 200 lines."
    ).format(dir=memory_dir)
else:
    reason = (
        "Before stopping: this is a new project with no memory yet. "
        "Create {dir}/MEMORY.md with key learnings from this session: "
        "project overview, build/test commands, architecture notes, "
        "user preferences you observed. Keep it concise (under 200 lines). "
        "If this was a trivial session with nothing worth remembering, just stop."
    ).format(dir=memory_dir)

output = {
    "decision": "block",
    "reason": reason,
}
print(json.dumps(output))
sys.exit(0)
