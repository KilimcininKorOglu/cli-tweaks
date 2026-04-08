#!/usr/bin/env node
/**
 * iOS App Launcher - App Lifecycle Control
 *
 * Launches, terminates, and manages iOS apps in the simulator.
 *
 * Usage: node scripts/appLauncher.js --launch com.example.app
 */

const { execFileSync } = require("child_process");
const { buildSimctlCommand, resolveUdid } = require("./common");

class AppLauncher {
  constructor(udid = null) {
    this.udid = udid;
  }

  launch(bundleId, waitForDebugger = false) {
    const cmd = buildSimctlCommand("launch", this.udid, bundleId);
    if (waitForDebugger) cmd.splice(1, 0, "--wait-for-debugger");

    try {
      const output = execFileSync("xcrun", cmd, {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      let pid = null;
      const parts = output.trim().split(":");
      if (parts.length > 1) {
        const parsed = parseInt(parts[1].trim(), 10);
        if (!isNaN(parsed)) pid = parsed;
      }
      return { success: true, pid };
    } catch {
      return { success: false, pid: null };
    }
  }

  terminate(bundleId) {
    try {
      execFileSync("xcrun", buildSimctlCommand("terminate", this.udid, bundleId), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return true;
    } catch { return false; }
  }

  install(appPath) {
    try {
      execFileSync("xcrun", buildSimctlCommand("install", this.udid, appPath), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return true;
    } catch { return false; }
  }

  uninstall(bundleId) {
    try {
      execFileSync("xcrun", buildSimctlCommand("uninstall", this.udid, bundleId), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return true;
    } catch { return false; }
  }

  openUrl(url) {
    try {
      execFileSync("xcrun", buildSimctlCommand("openurl", this.udid, url), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return true;
    } catch { return false; }
  }

  listApps() {
    try {
      const plistOutput = execFileSync("xcrun", buildSimctlCommand("listapps", this.udid), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      const jsonOutput = execFileSync("plutil", ["-convert", "json", "-o", "-", "-"], {
        encoding: "utf8", input: plistOutput, stdio: ["pipe", "pipe", "pipe"],
      });
      const data = JSON.parse(jsonOutput);
      const apps = [];
      for (const [bundleId, info] of Object.entries(data)) {
        if (info.ApplicationType === "Hidden") continue;
        apps.push({
          bundleId,
          name: info.CFBundleDisplayName || info.CFBundleName || bundleId,
          path: info.Path || "",
          version: info.CFBundleVersion || "Unknown",
          type: info.ApplicationType || "User",
        });
      }
      return apps;
    } catch { return []; }
  }

  getAppState(bundleId) {
    try {
      const output = execFileSync("xcrun", buildSimctlCommand("spawn", this.udid, "launchctl", "list"), {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return output.includes(bundleId) ? "running" : "not running";
    } catch { return "unknown"; }
  }

  restartApp(bundleId, delayMs = 1000) {
    this.terminate(bundleId);
    const end = Date.now() + delayMs;
    while (Date.now() < end) { /* wait */ }
    return this.launch(bundleId).success;
  }
}

function parseArgs() {
  const args = { launch: null, terminate: null, restart: null, install: null, uninstall: null, openUrl: null, list: false, state: null, waitForDebugger: false, udid: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--launch": args.launch = argv[++i]; break;
      case "--terminate": args.terminate = argv[++i]; break;
      case "--restart": args.restart = argv[++i]; break;
      case "--install": args.install = argv[++i]; break;
      case "--uninstall": args.uninstall = argv[++i]; break;
      case "--open-url": args.openUrl = argv[++i]; break;
      case "--list": args.list = true; break;
      case "--state": args.state = argv[++i]; break;
      case "--wait-for-debugger": args.waitForDebugger = true; break;
      case "--udid": args.udid = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node appLauncher.js [--launch|--terminate|--restart|--install|--uninstall|--open-url|--list|--state] [--udid UDID]");
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

  const launcher = new AppLauncher(udid);

  if (args.launch) {
    const { success, pid } = launcher.launch(args.launch, args.waitForDebugger);
    if (success) console.log(pid ? `Launched ${args.launch} (PID: ${pid})` : `Launched ${args.launch}`);
    else { console.error(`Failed to launch ${args.launch}`); process.exit(1); }
  } else if (args.terminate) {
    if (launcher.terminate(args.terminate)) console.log(`Terminated ${args.terminate}`);
    else { console.error(`Failed to terminate ${args.terminate}`); process.exit(1); }
  } else if (args.restart) {
    if (launcher.restartApp(args.restart)) console.log(`Restarted ${args.restart}`);
    else { console.error(`Failed to restart ${args.restart}`); process.exit(1); }
  } else if (args.install) {
    if (launcher.install(args.install)) console.log(`Installed ${args.install}`);
    else { console.error(`Failed to install ${args.install}`); process.exit(1); }
  } else if (args.uninstall) {
    if (launcher.uninstall(args.uninstall)) console.log(`Uninstalled ${args.uninstall}`);
    else { console.error(`Failed to uninstall ${args.uninstall}`); process.exit(1); }
  } else if (args.openUrl) {
    if (launcher.openUrl(args.openUrl)) console.log(`Opened URL: ${args.openUrl}`);
    else { console.error(`Failed to open URL: ${args.openUrl}`); process.exit(1); }
  } else if (args.list) {
    const apps = launcher.listApps();
    if (apps.length) {
      console.log(`Installed apps (${apps.length}):`);
      apps.slice(0, 10).forEach((a) => console.log(`  ${a.bundleId}: ${a.name} (v${a.version})`));
      if (apps.length > 10) console.log(`  ... and ${apps.length - 10} more`);
    } else console.log("No apps found or failed to list");
  } else if (args.state) {
    console.log(`${args.state}: ${launcher.getAppState(args.state)}`);
  } else {
    console.log("Usage: node appLauncher.js [--launch|--terminate|--restart|--install|--uninstall|--open-url|--list|--state] [--udid UDID]");
    process.exit(1);
  }
}

main();
