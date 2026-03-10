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
from datetime import datetime
from pathlib import Path

DEBUG = True
DEBUG_FILE = Path.home() / ".claude" / "auto-allow-debug.log"


def debugLog(message: str):
    """Write debug message to log file."""
    if not DEBUG:
        return
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("[{}] {}\n".format(timestamp, message))
    except IOError:
        pass


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


def findMatchingPattern(toolName: str, toolInput: dict, allowList: list) -> str:
    """Find the first matching pattern from allow list, or empty string if none."""
    for pattern in allowList:
        if matchesPattern(toolName, toolInput, pattern):
            return pattern
    return ""


def main():
    debugLog("Hook triggered")
    try:
        inputData = json.load(sys.stdin)
        debugLog("Input: {}".format(json.dumps(inputData)))
    except (json.JSONDecodeError, IOError) as e:
        debugLog("Failed to parse input: {}".format(str(e)))
        sys.exit(0)

    toolName = inputData.get("tool_name", "")
    toolInput = inputData.get("tool_input", {})

    debugLog("Tool: {}, Input: {}".format(toolName, json.dumps(toolInput)))

    if not toolName:
        debugLog("No tool_name, exiting")
        sys.exit(0)

    allowList = loadAllowList()
    debugLog("Allow list has {} patterns".format(len(allowList)))

    matchedPattern = findMatchingPattern(toolName, toolInput, allowList)

    if matchedPattern:
        debugLog("MATCHED: {}".format(matchedPattern))
        output = {
            "decision": {
                "behavior": "allow",
                "message": "Auto-allowed by pattern: {}".format(matchedPattern)
            }
        }
        print(json.dumps(output))
    else:
        debugLog("NO MATCH - showing prompt")

    # No output = show normal permission prompt
    sys.exit(0)


if __name__ == "__main__":
    main()
