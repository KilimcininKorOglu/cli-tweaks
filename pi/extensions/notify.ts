/**
 * Cross-platform desktop notifications for Pi Agent.
 *
 * Supports macOS (osascript), Linux (notify-send), and Windows (PowerShell).
 * Other extensions can use the exported notify function via pi.events.
 *
 * Usage from other extensions:
 *   pi.events.on("cli-tweaks:notify", ({ title, message }) => {});
 *   pi.events.emit("cli-tweaks:notify-request", { title: "...", message: "..." });
 */
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execSync } from "child_process";
import { platform } from "os";

function escapeApplescript(text: string): string {
  return text
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"');
}

function notify(title: string, message: string): void {
  const os = platform();
  try {
    if (os === "darwin") {
      const safeTitle = escapeApplescript(title);
      const safeMessage = escapeApplescript(message);
      execSync(
        `osascript -e 'display notification "${safeMessage}" with title "${safeTitle}"'`,
        { timeout: 5000 },
      );
    } else if (os === "linux") {
      const safeTitle = title.replace(/'/g, "'\\''");
      const safeMessage = message.replace(/'/g, "'\\''");
      execSync(`notify-send '${safeTitle}' '${safeMessage}'`, {
        timeout: 5000,
      });
    } else if (os === "win32") {
      const safeTitle = title.replace(/'/g, "''");
      const safeMessage = message.replace(/'/g, "''");
      const ps = `[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; ` +
        `$n = New-Object System.Windows.Forms.NotifyIcon; ` +
        `$n.Icon = [System.Drawing.SystemIcons]::Information; ` +
        `$n.Visible = $true; ` +
        `$n.ShowBalloonTip(5000, '${safeTitle}', '${safeMessage}', 'Info'); ` +
        `Start-Sleep -Seconds 1; $n.Dispose()`;
      execSync(`powershell -Command "${ps}"`, { timeout: 10000 });
    }
  } catch {
    // Notification failure is non-critical
  }
}

export default function (pi: ExtensionAPI) {
  pi.events.on(
    "cli-tweaks:notify-request",
    (data: { title: string; message: string }) => {
      notify(data.title, data.message);
    },
  );
}

export { notify };
