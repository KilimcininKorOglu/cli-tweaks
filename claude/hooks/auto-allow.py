#!/usr/bin/env python3
"""
PermissionRequest hook that auto-allows tools based on settings.json permissions.

Reads the allow list from ~/.claude/settings.json and automatically approves
matching tool requests without showing the permission prompt.

Hook Event: PermissionRequest
Input: JSON with tool_name, tool_input
Output: JSON with decision.behavior = "allow" or empty (show prompt)
"""

import json
import re
import sys
from pathlib import Path


def loadAllowList() -> list:
    """Load allow list from settings.json."""
    settingsFile = Path.home() / ".claude" / "settings.json"
    if not settingsFile.exists():
        return []
    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
        return data.get("permissions", {}).get("allow", [])
    except (json.JSONDecodeError, IOError):
        return []


def parsePattern(pattern: str) -> tuple:
    """
    Parse an allow pattern into (tool, command_prefix).

    Patterns:
    - "Bash(git:*)" -> ("Bash", "git")
    - "Bash(npm run:*)" -> ("Bash", "npm run")
    - "Write(*)" -> ("Write", "*")
    - "WebFetch" -> ("WebFetch", None)
    - "mcp__playwright__browser_click" -> ("mcp__playwright__browser_click", None)
    """
    # Pattern with parentheses: Tool(pattern)
    match = re.match(r'^(\w+)\((.+)\)$', pattern)
    if match:
        tool = match.group(1)
        inner = match.group(2)
        # Handle "command:*" or just "*"
        if inner == "*":
            return (tool, "*")
        if inner.endswith(":*"):
            return (tool, inner[:-2])  # Remove ":*"
        return (tool, inner)

    # Simple tool name without parentheses
    return (pattern, None)


def matchesPattern(toolName: str, toolInput: dict, pattern: str) -> bool:
    """Check if a tool request matches an allow pattern."""
    parsedTool, parsedPrefix = parsePattern(pattern)

    # Tool name must match
    if parsedTool != toolName:
        return False

    # No prefix means exact tool match (e.g., "WebFetch")
    if parsedPrefix is None:
        return True

    # Wildcard matches everything
    if parsedPrefix == "*":
        return True

    # For Bash, check command prefix
    if toolName == "Bash":
        command = toolInput.get("command", "")
        # Check if command starts with the prefix
        if command.startswith(parsedPrefix):
            return True
        # Also check if command starts with prefix after common patterns
        # e.g., "git commit" should match "git commit:*"
        return False

    # For other tools with patterns, check if any input matches
    # This handles cases like Write(*) where * means any path
    return True


def shouldAllow(toolName: str, toolInput: dict, allowList: list) -> bool:
    """Check if the tool request should be auto-allowed."""
    for pattern in allowList:
        if matchesPattern(toolName, toolInput, pattern):
            return True
    return False


def main():
    try:
        inputData = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        sys.exit(0)

    toolName = inputData.get("tool_name", "")
    toolInput = inputData.get("tool_input", {})

    if not toolName:
        sys.exit(0)

    allowList = loadAllowList()

    if shouldAllow(toolName, toolInput, allowList):
        output = {
            "decision": {
                "behavior": "allow"
            }
        }
        print(json.dumps(output))

    # No output = show normal permission prompt
    sys.exit(0)


if __name__ == "__main__":
    main()
