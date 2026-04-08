#!/usr/bin/env node
/**
 * iOS Simulator Log Monitoring and Analysis
 *
 * Real-time log streaming with intelligent filtering and error detection.
 *
 * Usage:
 *   node scripts/logMonitor.js --app com.myapp.MyApp --follow
 *   node scripts/logMonitor.js --app com.myapp.MyApp --duration 30s
 *   node scripts/logMonitor.js --severity error,warning --last 5m
 */

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

class LogMonitor {
  constructor({ appBundleId = null, deviceUdid = null, severityFilter = null } = {}) {
    this.appBundleId = appBundleId;
    this.deviceUdid = deviceUdid || "booted";
    this.severityFilter = severityFilter || ["error", "warning", "info", "debug"];
    this.logLines = [];
    this.errors = [];
    this.warnings = [];
    this.infoMessages = [];
    this.errorCount = 0;
    this.warningCount = 0;
    this.infoCount = 0;
    this.debugCount = 0;
    this.totalLines = 0;
    this.seenMessages = new Set();
    this.logProcess = null;
    this.interrupted = false;
  }

  parseTimeDuration(str) {
    const match = str.toLowerCase().match(/^(\d+)([smh])$/);
    if (!match) throw new Error(`Invalid duration: ${str}. Use 30s, 5m, 1h`);
    const [, val, unit] = match;
    const v = parseInt(val, 10);
    if (unit === "s") return v;
    if (unit === "m") return v * 60;
    if (unit === "h") return v * 3600;
    return 0;
  }

  classifyLogLine(line) {
    const lower = line.toLowerCase();
    if (/\b(error|fault|failed|exception|crash)\b/.test(lower)) return "error";
    if (/\b(warning|warn|deprecated)\b/.test(lower)) return "warning";
    if (/\b(info|notice)\b/.test(lower)) return "info";
    return "debug";
  }

  deduplicateMessage(line) {
    let sig = line.replace(/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/g, "");
    sig = sig.replace(/\[\d+\]/g, "").replace(/\s+/g, " ").trim();
    if (this.seenMessages.has(sig)) return false;
    this.seenMessages.add(sig);
    return true;
  }

  processLogLine(line) {
    if (!line.trim()) return;
    this.totalLines++;
    this.logLines.push(line);

    const severity = this.classifyLogLine(line);
    if (!this.severityFilter.includes(severity)) return;

    if ((severity === "error" || severity === "warning") && !this.deduplicateMessage(line)) return;

    if (severity === "error") { this.errorCount++; this.errors.push(line); }
    else if (severity === "warning") { this.warningCount++; this.warnings.push(line); }
    else if (severity === "info") { this.infoCount++; if (this.infoMessages.length < 20) this.infoMessages.push(line); }
    else this.debugCount++;
  }

  streamLogs({ follow = false, duration = null, lastMinutes = null } = {}) {
    return new Promise((resolve) => {
      const cmd = ["simctl", "spawn", this.deviceUdid, "log", "stream"];
      if (this.appBundleId) {
        const appName = this.appBundleId.split(".").pop();
        cmd.push("--predicate", `processImagePath CONTAINS "${appName}"`);
      }

      process.on("SIGINT", () => { this.interrupted = true; if (this.logProcess) this.logProcess.kill(); });

      this.logProcess = spawn("xcrun", cmd, { stdio: ["pipe", "pipe", "pipe"] });
      const startTime = Date.now();

      let buffer = "";
      this.logProcess.stdout.on("data", (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          this.processLogLine(line);
          if (follow) {
            const severity = this.classifyLogLine(line);
            if (this.severityFilter.includes(severity)) process.stdout.write(line + "\n");
          }
        }

        if (duration && (Date.now() - startTime) / 1000 >= duration) {
          this.logProcess.kill();
        }
        if (this.interrupted) this.logProcess.kill();
      });

      this.logProcess.on("close", () => resolve(true));
      this.logProcess.on("error", () => resolve(false));
    });
  }

  getSummary(verbose = false) {
    const lines = [];
    lines.push(this.appBundleId ? `Logs for: ${this.appBundleId}` : "Logs for: All processes");
    lines.push(`Total lines: ${this.totalLines}`);
    lines.push(`Errors: ${this.errorCount}, Warnings: ${this.warningCount}, Info: ${this.infoCount}`);

    if (this.errors.length) {
      lines.push(`\nTop Errors (${this.errors.length}):`);
      this.errors.slice(0, 5).forEach((e) => lines.push(`  X ${e.slice(0, 120)}`));
    }
    if (this.warnings.length) {
      lines.push(`\nTop Warnings (${this.warnings.length}):`);
      this.warnings.slice(0, 5).forEach((w) => lines.push(`  ! ${w.slice(0, 120)}`));
    }
    if (verbose && this.logLines.length) {
      lines.push("\n=== Recent Log Lines ===");
      this.logLines.slice(-50).forEach((l) => lines.push(l));
    }
    return lines.join("\n");
  }

  getJsonOutput() {
    return {
      appBundleId: this.appBundleId,
      deviceUdid: this.deviceUdid,
      statistics: { totalLines: this.totalLines, errors: this.errorCount, warnings: this.warningCount, info: this.infoCount, debug: this.debugCount },
      errors: this.errors.slice(0, 20),
      warnings: this.warnings.slice(0, 20),
      sampleLogs: this.logLines.slice(-50),
    };
  }

  saveLogs(outputDir) {
    fs.mkdirSync(outputDir, { recursive: true });
    const timestamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 15).replace(/^(\d{8})(\d{6})/, "$1-$2");
    const appName = this.appBundleId ? this.appBundleId.split(".").pop() : "simulator";
    const logFile = path.join(outputDir, `${appName}-${timestamp}.log`);
    fs.writeFileSync(logFile, this.logLines.join("\n"));
    const jsonFile = path.join(outputDir, `${appName}-${timestamp}-summary.json`);
    fs.writeFileSync(jsonFile, JSON.stringify(this.getJsonOutput(), null, 2));
    return logFile;
  }
}

function parseArgs() {
  const args = { app: null, deviceUdid: null, severity: null, follow: false, duration: null, last: null, output: null, verbose: false, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--app": args.app = argv[++i]; break;
      case "--device-udid": args.deviceUdid = argv[++i]; break;
      case "--severity": args.severity = argv[++i]; break;
      case "--follow": args.follow = true; break;
      case "--duration": args.duration = argv[++i]; break;
      case "--last": args.last = argv[++i]; break;
      case "--output": args.output = argv[++i]; break;
      case "--verbose": args.verbose = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node logMonitor.js [--app BUNDLE_ID] [--follow|--duration 30s|--last 5m] [--severity error,warning] [--output DIR] [--json]");
        process.exit(0);
    }
  }
  return args;
}

async function main() {
  const args = parseArgs();
  const severityFilter = args.severity ? args.severity.split(",").map((s) => s.trim().toLowerCase()) : null;

  const monitor = new LogMonitor({ appBundleId: args.app, deviceUdid: args.deviceUdid, severityFilter });

  let duration = null;
  if (args.duration) duration = monitor.parseTimeDuration(args.duration);

  let lastMinutes = null;
  if (args.last) lastMinutes = monitor.parseTimeDuration(args.last) / 60;

  process.stderr.write("Monitoring logs...\n");
  if (args.app) process.stderr.write(`App: ${args.app}\n`);

  const success = await monitor.streamLogs({ follow: args.follow, duration, lastMinutes });
  if (!success) process.exit(1);

  if (args.output) {
    const logFile = monitor.saveLogs(args.output);
    process.stderr.write(`\nLogs saved to: ${logFile}\n`);
  }

  if (!args.follow) {
    if (args.json) console.log(JSON.stringify(monitor.getJsonOutput(), null, 2));
    else console.log("\n" + monitor.getSummary(args.verbose));
  }
}

main();
