"""
Cross-platform desktop notification helper for hooks.
Supports macOS, Linux, and Windows.

WrongStack-specific: enable notifications per-feature in
~/.cli-tweaks/wrongstack-config.json:
  "hookNotifyPlanSave": true

We read from this file (not ~/.wrongstack/config.json) so the hook stays
out of WrongStack's reserved config schema. The same file is also read
by session-start.py for globalInjectFiles.
"""
import json
import os
import platform
import shlex
from pathlib import Path


WRONGSTACK_CONFIG_PATH = Path.home() / ".cli-tweaks" / "wrongstack-config.json"


def isEnabledFor(feature: str) -> bool:
    """Check if notifications are enabled for a specific feature.

    Checks hookNotify{Feature} setting.
    Example: isEnabledFor("PlanSave") checks hookNotifyPlanSave.
    """
    if not WRONGSTACK_CONFIG_PATH.exists():
        return False
    try:
        data = json.loads(WRONGSTACK_CONFIG_PATH.read_text(encoding="utf-8"))
        featureKey = "hookNotify{}".format(feature)
        return bool(data.get(featureKey, False))
    except (json.JSONDecodeError, IOError):
        return False


def escapeApplescript(s: str) -> str:
    """Escape string for AppleScript double-quoted context."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def notify(title: str, message: str, subtitle: str = ""):
    system = platform.system()

    if system == "Darwin":
        safeTitle = escapeApplescript(title)
        safeMsg = escapeApplescript(message)
        safeSub = escapeApplescript(subtitle)
        parts = [f'display notification "{safeMsg}" with title "{safeTitle}"']
        if subtitle:
            parts[0] += f' subtitle "{safeSub}"'
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
