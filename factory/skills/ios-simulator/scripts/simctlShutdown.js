#!/usr/bin/env node
/**
 * Shutdown iOS simulators with optional state verification.
 *
 * Key features:
 * - Shutdown by UDID or device name
 * - Verify shutdown completion with timeout
 * - Batch shutdown operations (all, by type)
 *
 * Usage: node scripts/simctlShutdown.js --udid <udid> [--verify] [--timeout 30]
 */

const { execFileSync } = require("child_process");
const { listSimulators, resolveDeviceIdentifier } = require("./common");

class SimulatorShutdown {
  constructor(udid = null) {
    this.udid = udid;
  }

  shutdown(verify = true, timeoutSeconds = 30) {
    if (!this.udid) return { success: false, message: "Error: Device UDID not specified" };

    const startTime = Date.now();

    // Check if already shutdown
    const booted = listSimulators("booted");
    if (!booted.some((s) => s.udid === this.udid)) {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      return { success: true, message: `Device already shutdown: ${this.udid} [checked in ${elapsed}s]` };
    }

    // Execute shutdown
    try {
      execFileSync("xcrun", ["simctl", "shutdown", this.udid], {
        encoding: "utf8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 30000,
      });
    } catch (e) {
      const stderr = e.stderr ? e.stderr.toString().trim() : e.message;
      return { success: false, message: `Shutdown failed: ${stderr}` };
    }

    if (verify) {
      const verifyResult = this._verifyShutdown(timeoutSeconds);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      if (verifyResult.success) {
        return { success: true, message: `Device shutdown confirmed: ${this.udid} [${elapsed}s total]` };
      }
      return verifyResult;
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return { success: true, message: `Device shutdown: ${this.udid} [${elapsed}s] (use --verify to wait for confirmation)` };
  }

  _verifyShutdown(timeoutSeconds = 30) {
    const startTime = Date.now();
    const pollInterval = 500;
    let checks = 0;

    while ((Date.now() - startTime) / 1000 < timeoutSeconds) {
      checks++;
      try {
        const booted = listSimulators("booted");
        if (!booted.some((s) => s.udid === this.udid)) {
          const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
          return { success: true, message: `Device shutdown verified: ${this.udid} [${elapsed}s, ${checks} checks]` };
        }
      } catch { /* retry */ }
      const end = Date.now() + pollInterval;
      while (Date.now() < end) { /* busy wait */ }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return { success: false, message: `Shutdown verification timeout within ${elapsed}s (${checks} checks)` };
  }

  static shutdownAll() {
    const sims = listSimulators("booted");
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      const s = new SimulatorShutdown(sim.udid);
      const { success } = s.shutdown(false);
      success ? succeeded++ : failed++;
    }
    return { succeeded, failed };
  }

  static shutdownByType(deviceType) {
    const sims = listSimulators("booted");
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      if (sim.name.toLowerCase().includes(deviceType.toLowerCase())) {
        const s = new SimulatorShutdown(sim.udid);
        const { success } = s.shutdown(false);
        success ? succeeded++ : failed++;
      }
    }
    return { succeeded, failed };
  }
}

function parseArgs() {
  const args = { udid: null, name: null, verify: false, timeout: 30, all: false, type: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--udid": args.udid = argv[++i]; break;
      case "--name": args.name = argv[++i]; break;
      case "--verify": args.verify = true; break;
      case "--timeout": args.timeout = parseInt(argv[++i], 10); break;
      case "--all": args.all = true; break;
      case "--type": args.type = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simctlShutdown.js [--udid ID | --name NAME | --all | --type TYPE] [--verify] [--timeout N] [--json]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  if (args.all) {
    const { succeeded, failed } = SimulatorShutdown.shutdownAll();
    const total = succeeded + failed;
    if (args.json) console.log(JSON.stringify({ action: "shutdown_all", succeeded, failed, total }));
    else console.log(`Shutdown summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    process.exit(failed === 0 ? 0 : 1);
  }

  if (args.type) {
    const { succeeded, failed } = SimulatorShutdown.shutdownByType(args.type);
    const total = succeeded + failed;
    if (args.json) console.log(JSON.stringify({ action: "shutdown_by_type", type: args.type, succeeded, failed, total }));
    else console.log(`Shutdown ${args.type} summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    process.exit(failed === 0 ? 0 : 1);
  }

  const deviceId = args.udid || args.name;
  if (!deviceId) {
    console.error("Error: Specify --udid, --name, --all, or --type");
    process.exit(1);
  }

  let udid;
  try { udid = resolveDeviceIdentifier(deviceId); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const s = new SimulatorShutdown(udid);
  const { success, message } = s.shutdown(args.verify, args.timeout);

  if (args.json) console.log(JSON.stringify({ action: "shutdown", deviceId, udid, success, message }));
  else console.log(message);
  process.exit(success ? 0 : 1);
}

main();
