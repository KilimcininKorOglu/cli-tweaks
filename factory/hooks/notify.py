"""
Cross-platform desktop notification helper for hooks.
Supports macOS, Linux, and Windows.

Enable notifications per-feature in ~/.factory/settings.json:
  "hookNotifyPlanSave": true
"""
import json
import platform
import subprocess
from pathlib import Path


def isEnabledFor(feature: str) -> bool:
    """Check if notifications are enabled for a specific feature.

    Checks hookNotify{Feature} setting.
    Example: isEnabledFor("PlanSave") checks hookNotifyPlanSave.
    """
    settingsFile = Path.home() / ".factory" / "settings.json"
    if settingsFile.exists():
        try:
            data = json.loads(settingsFile.read_text(encoding="utf-8"))
            featureKey = "hookNotify{}".format(feature)
            return data.get(featureKey, False)
        except (json.JSONDecodeError, IOError):
            pass
    return False


def escapeApplescript(s: str) -> str:
    """Escape string for AppleScript double-quoted context."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, subtitle: str = ""):
    system = platform.system()

    if system == "Darwin":
        safeTitle = escapeApplescript(title)
        safeMessage = escapeApplescript(message)
        safeSubtitle = escapeApplescript(subtitle)
        script = f'display notification "{safeMessage}" with title "{safeTitle}"'
        if subtitle:
            script += f' subtitle "{safeSubtitle}"'
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
        safe_title = title.replace("'", "''")
        safe_msg = message.replace("'", "''")
        try:
            subprocess.run(
                [
                    "powershell.exe",
                    "-Command",
                    "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                    f"[System.Windows.Forms.MessageBox]::Show('{safe_msg}', '{safe_title}')",
                ]
            )
        except FileNotFoundError:
            pass
