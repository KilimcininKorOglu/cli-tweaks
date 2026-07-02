"""Shared helpers for Codex hook ports."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def readInput() -> Dict[str, Any]:
    """Read one Codex hook JSON payload from stdin."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def resolveProjectName(cwd: str) -> str:
    """Return the git root basename if available, otherwise the cwd basename."""
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


def sessionKey(inputData: Dict[str, Any]) -> str:
    """Return the stable Codex session key for shared hook state."""
    rawSessionId = inputData.get("session_id")
    if isinstance(rawSessionId, str) and rawSessionId.strip():
        return rawSessionId.strip()
    return str(os.getppid())


def statePath(name: str, key: str) -> Path:
    """Return a shared state file path under the cli-tweaks state directory."""
    return Path.home() / ".cli-tweaks" / name / key


def readLockedProjectName(inputData: Dict[str, Any], cwd: str) -> str:
    """Return the project name locked by SessionStart, with a cwd fallback."""
    lockFile = statePath(".session-locks", sessionKey(inputData))
    try:
        projectName = lockFile.read_text(encoding="utf-8").strip()
        if projectName:
            return projectName
    except (FileNotFoundError, OSError):
        pass
    return resolveProjectName(cwd)


def memoryDirFor(projectName: str) -> Path:
    """Return the shared project memory directory."""
    return Path.home() / ".cli-tweaks" / "memory" / projectName


def codexConfigPath() -> Path:
    """Return the cli-tweaks Codex configuration path."""
    return Path.home() / ".codex" / "cli-tweaks.json"


def readCodexConfig() -> Dict[str, Any]:
    """Return optional cli-tweaks Codex settings."""
    configFile = codexConfigPath()
    try:
        data = json.loads(configFile.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def globalInjectFiles() -> List[str]:
    """Return configured global instruction files for Codex hooks."""
    data = readCodexConfig()
    rawFiles = data.get("globalInjectFiles", [])
    if not isinstance(rawFiles, list):
        return []
    return [item for item in rawFiles if isinstance(item, str) and item.strip()]


def readConfiguredGlobalFiles() -> str:
    """Return combined content from configured Codex global instruction files."""
    contents = []
    for filePath in globalInjectFiles():
        path = Path(os.path.expanduser(filePath))
        if not path.exists() or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if content:
            contents.append("# From {0}\n{1}".format(filePath, content))
    return "\n\n---\n\n".join(contents)


def writeAdditionalContext(eventName: str, context: str) -> None:
    """Emit Codex hook JSON that adds developer context."""
    if not context:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": eventName,
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
