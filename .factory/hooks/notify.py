"""
Cross-platform desktop notification helper for hooks.
Supports macOS, Linux, and Windows.
"""
import os
import platform
import shlex


def notify(title: str, message: str, subtitle: str = ""):
    system = platform.system()

    if system == "Darwin":
        parts = [f'display notification "{message}" with title "{title}"']
        if subtitle:
            parts[0] += f' subtitle "{subtitle}"'
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
