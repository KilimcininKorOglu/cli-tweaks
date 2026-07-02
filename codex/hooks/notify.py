"""Cross-platform desktop notification helper for Codex hooks."""
import json
import platform
import subprocess
from pathlib import Path


def isEnabledFor(feature: str) -> bool:
    """Return whether notifications are enabled for a specific feature."""
    settingsFile = Path.home() / ".codex" / "cli-tweaks.json"
    if settingsFile.exists():
        try:
            data = json.loads(settingsFile.read_text(encoding="utf-8"))
            featureKey = "hookNotify{0}".format(feature)
            return bool(data.get(featureKey, False))
        except (json.JSONDecodeError, OSError):
            pass
    return False


def escapeApplescript(value: str) -> str:
    """Escape a string for AppleScript double-quoted context."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, subtitle: str = "") -> None:
    """Send a desktop notification when the host platform supports it."""
    system = platform.system()

    if system == "Darwin":
        safeTitle = escapeApplescript(title)
        safeMessage = escapeApplescript(message)
        safeSubtitle = escapeApplescript(subtitle)
        script = 'display notification "{0}" with title "{1}"'.format(safeMessage, safeTitle)
        if subtitle:
            script += ' subtitle "{0}"'.format(safeSubtitle)
        try:
            subprocess.run(["osascript", "-e", script])
        except FileNotFoundError:
            pass
    elif system == "Linux":
        try:
            subprocess.run(["notify-send", title, message])
        except FileNotFoundError:
            pass
    elif system == "Windows":
        safeTitle = title.replace("'", "''")
        safeMessage = message.replace("'", "''")
        try:
            subprocess.run(
                [
                    "powershell.exe",
                    "-Command",
                    "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                    "[System.Windows.Forms.MessageBox]::Show('{0}', '{1}')".format(safeMessage, safeTitle),
                ]
            )
        except FileNotFoundError:
            pass
