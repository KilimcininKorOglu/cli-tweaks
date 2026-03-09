"""
Cross-platform desktop notification helper for hooks.
Supports macOS, Linux, and Windows.

Set "hookNotify": true in ~/.claude/settings.json to enable notifications.
"""
import json
import os
import platform
import shlex
from pathlib import Path


def isEnabled() -> bool:
    """Check if notifications are enabled in settings.json."""
    settingsFile = Path.home() / ".claude" / "settings.json"
    if settingsFile.exists():
        try:
            data = json.loads(settingsFile.read_text(encoding="utf-8"))
            return data.get("hookNotify", False)
        except (json.JSONDecodeError, IOError):
            pass
    return False


def escapeApplescript(s: str) -> str:
    """Escape string for AppleScript double-quoted context."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, subtitle: str = ""):
    if not isEnabled():
        return

    system = platform.system()

    if system == "Darwin":
        safeTitle = escapeApplescript(title)
        safeMessage = escapeApplescript(message)
        safeSubtitle = escapeApplescript(subtitle)
        parts = [f'display notification "{safeMessage}" with title "{safeTitle}"']
        if subtitle:
            parts[0] += f' subtitle "{safeSubtitle}"'
        os.system(f"osascript -e '{parts[0]}'")

    elif system == "Linux":
        safe_title = shlex.quote(title)
        safe_msg = shlex.quote(message)
        os.system(f"notify-send {safe_title} {safe_msg}")

    elif system == "Windows":
        safe_title = title.replace("'", "''")
        safe_msg = message.replace("'", "''")
        os.system(
            f'powershell.exe -Command "'
            f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
            f"[System.Windows.Forms.MessageBox]::Show('{safe_msg}', '{safe_title}')"
            f'"'
        )
