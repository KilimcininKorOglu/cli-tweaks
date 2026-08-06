"""
Cross-platform desktop notification helper for hooks.
Supports macOS, Linux, and Windows.

Enable notifications per-feature in ~/.claude/settings.json:
  "hookNotifyPlanSave": true

The value must be JSON true. Any other value, including the string "false",
leaves the feature disabled and is reported as a configuration error.

Every notification path is fire-and-forget and bounded by a timeout, because
hooks run inside the agent's tool loop: a helper that waits on a user click, or
on a hung notification daemon, would stall the tool call it is attached to.
Child output is captured so it can never leak into the hook's own stdout.
"""
import json
import platform
import subprocess
import sys
from pathlib import Path

NOTIFY_TIMEOUT_SECONDS = 5


def _warn(message: str) -> None:
    """Report a helper failure on stderr, never on stdout."""
    print("notify: {}".format(message), file=sys.stderr)


def isEnabledFor(feature: str) -> bool:
    """Check if notifications are enabled for a specific feature.

    Checks hookNotify{Feature} setting.
    Example: isEnabledFor("PlanSave") checks hookNotifyPlanSave.

    Only JSON true enables a feature. A truthy non-boolean such as the string
    "false" is a configuration mistake, not an opt-in, so it is rejected and
    reported instead of silently switching notifications on.
    """
    settingsFile = Path.home() / ".claude" / "settings.json"
    if not settingsFile.exists():
        return False

    try:
        data = json.loads(settingsFile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _warn("{} is not valid JSON ({}); notifications disabled".format(settingsFile, exc))
        return False
    except OSError as exc:
        _warn("cannot read {} ({}); notifications disabled".format(settingsFile, exc))
        return False

    featureKey = "hookNotify{}".format(feature)
    value = data.get(featureKey, False)
    if value is True or value is False:
        return value

    _warn("{} must be true or false, got {!r}; treating as false".format(featureKey, value))
    return False


def escapeApplescript(s: str) -> str:
    """Escape string for AppleScript double-quoted context."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def escapePowershell(s: str) -> str:
    """Escape string for a PowerShell single-quoted literal."""
    return s.replace("'", "''")


def _run(command) -> bool:
    """Run a notification command, capturing its output and bounding the wait."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=NOTIFY_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        _warn("{} is not installed".format(command[0]))
        return False
    except subprocess.TimeoutExpired:
        _warn("{} timed out after {}s".format(command[0], NOTIFY_TIMEOUT_SECONDS))
        return False
    except OSError as exc:
        _warn("{} failed to start ({})".format(command[0], exc))
        return False

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        _warn("{} exited {} ({})".format(command[0], result.returncode, detail))
        return False
    return True


def notify(title: str, message: str, subtitle: str = "") -> bool:
    """Show a desktop notification. Returns True when it was delivered."""
    system = platform.system()

    if system == "Darwin":
        script = 'display notification "{}" with title "{}"'.format(
            escapeApplescript(message), escapeApplescript(title)
        )
        if subtitle:
            script += ' subtitle "{}"'.format(escapeApplescript(subtitle))
        return _run(["osascript", "-e", script])

    if system == "Linux":
        # notify-send has no subtitle field, so fold it into the body instead of
        # dropping it.
        body = "{}\n{}".format(subtitle, message) if subtitle else message
        return _run(["notify-send", title, body])

    if system == "Windows":
        # A toast is fire-and-forget. MessageBox would block until the user
        # clicked it, stalling the tool call this helper runs inside.
        safeTitle = escapePowershell(title)
        safeBody = escapePowershell(
            "{} - {}".format(subtitle, message) if subtitle else message
        )
        script = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
            " ContentType=WindowsRuntime] > $null; "
            "$x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
            "[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            "$t = $x.GetElementsByTagName('text'); "
            "$t.Item(0).AppendChild($x.CreateTextNode('{}')) > $null; "
            "$t.Item(1).AppendChild($x.CreateTextNode('{}')) > $null; "
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
            "'{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'"
            ").Show([Windows.UI.Notifications.ToastNotification]::new($x))"
        ).format(safeTitle, safeBody)
        return _run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script]
        )

    _warn("unsupported platform {}".format(system))
    return False
