#!/usr/bin/env node
/**
 * App State Capture for iOS Simulator
 *
 * Captures complete app state: screenshot, accessibility tree, and logs.
 *
 * Usage: node scripts/appStateCapture.js --app-bundle-id com.example.app --output ./debug
 */

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { captureScreenshot, countElements, getAccessibilityTree, resolveUdid } = require("./common");

class AppStateCapture {
  constructor({ appBundleId = null, udid = null, inline = false, screenshotSize = "half" } = {}) {
    this.appBundleId = appBundleId;
    this.udid = udid;
    this.inline = inline;
    this.screenshotSize = screenshotSize;
  }

  captureAccessibilityTree(outputPath) {
    try {
      const tree = getAccessibilityTree(this.udid, true);
      fs.writeFileSync(outputPath, JSON.stringify(tree, null, 2));
      return { captured: true, elementCount: countElements(tree) };
    } catch (e) {
      return { captured: false, error: e.message };
    }
  }

  captureLogs(outputPath, lineLimit = 100) {
    if (!this.appBundleId) return { captured: false, reason: "No app bundle ID specified" };
    const appName = this.appBundleId.split(".").pop();

    try {
      const output = execFileSync("xcrun", [
        "simctl", "spawn", this.udid || "booted", "log", "show",
        "--predicate", `process == "${appName}"`, "--last", "1m", "--style", "compact",
      ], { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 5000 });

      let lines = output.split("\n");
      if (lines.length > lineLimit) lines = lines.slice(-lineLimit);
      fs.writeFileSync(outputPath, lines.join("\n"));

      const warnings = lines.filter((l) => l.toLowerCase().includes("warning")).length;
      const errors = lines.filter((l) => l.toLowerCase().includes("error")).length;
      return { captured: true, lines: lines.length, warnings, errors };
    } catch (e) {
      return { captured: false, error: e.message };
    }
  }

  captureDeviceInfo() {
    try {
      const output = execFileSync("xcrun", ["simctl", "list", "devices", "booted"], {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      const info = {};
      for (const line of output.split("\n")) {
        if (line.includes("iPhone") || line.includes("iPad")) {
          const parts = line.trim().split("(");
          if (parts.length) {
            info.name = parts[0].trim();
            if (parts.length > 2) {
              info.udid = parts[1].replace(")", "").trim();
              info.state = parts[2].replace(")", "").trim();
            }
          }
          break;
        }
      }
      return info;
    } catch { return {}; }
  }

  captureAll(outputDir, logLines = 100, appName = null) {
    const timestamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 15).replace(/^(\d{8})(\d{6})/, "$1-$2");
    let captureDir = null;
    if (!this.inline) {
      captureDir = path.join(outputDir, `app-state-${timestamp}`);
      fs.mkdirSync(captureDir, { recursive: true });
    }

    const summary = { timestamp: new Date().toISOString(), screenshotMode: this.inline ? "inline" : "file" };
    if (captureDir) summary.outputDir = captureDir;

    // Screenshot
    const ssResult = captureScreenshot(this.udid, { size: this.screenshotSize, inline: this.inline, appName });
    if (this.inline) {
      summary.screenshot = { mode: "inline", base64: ssResult.base64Data, width: ssResult.width, height: ssResult.height, sizePreset: this.screenshotSize };
    } else {
      const ssPath = path.join(captureDir, "screenshot.png");
      fs.renameSync(ssResult.filePath, ssPath);
      summary.screenshot = { mode: "file", file: "screenshot.png", sizeBytes: ssResult.sizeBytes };
    }

    // Accessibility
    if (captureDir) {
      const accPath = path.join(captureDir, "accessibility-tree.json");
      summary.accessibility = this.captureAccessibilityTree(accPath);
    }

    // Logs
    if (this.appBundleId && captureDir) {
      const logsPath = path.join(captureDir, "app-logs.txt");
      summary.logs = this.captureLogs(logsPath, logLines);
    }

    // Device info
    const deviceInfo = this.captureDeviceInfo();
    if (Object.keys(deviceInfo).length) {
      summary.device = deviceInfo;
      if (captureDir) fs.writeFileSync(path.join(captureDir, "device-info.json"), JSON.stringify(deviceInfo, null, 2));
    }

    // Save summary
    if (captureDir) {
      fs.writeFileSync(path.join(captureDir, "summary.json"), JSON.stringify(summary, null, 2));
      this._createSummaryMd(captureDir, summary);
    }

    return summary;
  }

  _createSummaryMd(captureDir, summary) {
    let md = `# App State Capture\n\n**Timestamp:** ${summary.timestamp}\n\n`;
    if (summary.device) {
      md += `## Device\n- Name: ${summary.device.name || "Unknown"}\n- UDID: ${summary.device.udid || "N/A"}\n- State: ${summary.device.state || "Unknown"}\n\n`;
    }
    md += "## Screenshot\n![Current Screen](screenshot.png)\n\n";
    if (summary.accessibility) {
      md += "## Accessibility\n";
      md += summary.accessibility.captured ? `- Elements: ${summary.accessibility.elementCount}\n\n` : `- Error: ${summary.accessibility.error}\n\n`;
    }
    if (summary.logs) {
      md += "## Logs\n";
      if (summary.logs.captured) md += `- Lines: ${summary.logs.lines}\n- Warnings: ${summary.logs.warnings}\n- Errors: ${summary.logs.errors}\n\n`;
      else md += `- ${summary.logs.reason || summary.logs.error || "Not captured"}\n\n`;
    }
    md += "## Files\n- `screenshot.png` - Current screen\n- `accessibility-tree.json` - Full UI hierarchy\n";
    if (this.appBundleId) md += "- `app-logs.txt` - Recent app logs\n";
    md += "- `device-info.json` - Device details\n- `summary.json` - Complete capture metadata\n";
    fs.writeFileSync(path.join(captureDir, "summary.md"), md);
  }
}

function parseArgs() {
  const args = { appBundleId: null, output: ".", logLines: 100, udid: null, inline: false, size: "half", appName: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--app-bundle-id": args.appBundleId = argv[++i]; break;
      case "--output": args.output = argv[++i]; break;
      case "--log-lines": args.logLines = parseInt(argv[++i], 10); break;
      case "--udid": args.udid = argv[++i]; break;
      case "--inline": args.inline = true; break;
      case "--size": args.size = argv[++i]; break;
      case "--app-name": args.appName = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node appStateCapture.js [--app-bundle-id ID] [--output DIR] [--log-lines N] [--udid UDID] [--inline] [--size half]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();
  let udid;
  try { udid = resolveUdid(args.udid); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const capturer = new AppStateCapture({ appBundleId: args.appBundleId, udid, inline: args.inline, screenshotSize: args.size });

  try {
    const summary = capturer.captureAll(args.output, args.logLines, args.appName);

    if (args.json) { console.log(JSON.stringify(summary, null, 2)); return; }

    if (summary.outputDir) console.log(`State captured: ${summary.outputDir}/`);
    else console.log(`State captured (inline): ${summary.screenshot.width}x${summary.screenshot.height}`);

    if (summary.logs && summary.logs.captured && (summary.logs.errors > 0 || summary.logs.warnings > 0))
      console.log(`Issues found: ${summary.logs.errors} errors, ${summary.logs.warnings} warnings`);
    if (summary.accessibility && summary.accessibility.captured)
      console.log(`Elements: ${summary.accessibility.elementCount}`);
  } catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }
}

main();
