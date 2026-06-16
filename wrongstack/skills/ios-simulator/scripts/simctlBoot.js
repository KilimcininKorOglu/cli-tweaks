#!/usr/bin/env node
/**
 * Boot iOS simulators and wait for readiness.
 *
 * Key features:
 * - Boot by UDID or device name
 * - Wait for device readiness with configurable timeout
 * - Measure boot performance
 * - Batch boot operations (boot all, boot by type)
 *
 * Usage: node scripts/simctlBoot.js --udid <udid> [--wait-ready] [--timeout 120]
 */

const { execFileSync } = require("child_process");
const {
  getBootedDeviceUdid,
  listSimulators,
  resolveDeviceIdentifier,
} = require("./common");

class SimulatorBooter {
  constructor(udid = null) {
    this.udid = udid;
  }

  boot(waitReady = false, timeoutSeconds = 120) {
    if (!this.udid) return { success: false, message: "Error: Device UDID not specified" };

    const startTime = Date.now();

    // Check if already booted
    try {
      const booted = getBootedDeviceUdid();
      if (booted === this.udid) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        return { success: true, message: `Device already booted: ${this.udid} [checked in ${elapsed}s]` };
      }
    } catch { /* no booted device */ }

    // Execute boot
    try {
      execFileSync("xcrun", ["simctl", "boot", this.udid], {
        encoding: "utf8",
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 30000,
      });
    } catch (e) {
      const stderr = e.stderr ? e.stderr.toString().trim() : e.message;
      return { success: false, message: `Boot failed: ${stderr}` };
    }

    if (waitReady) {
      const readyResult = this._waitForReady(timeoutSeconds);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      if (readyResult.success) {
        return { success: true, message: `Device booted and ready: ${this.udid} [${elapsed}s total]` };
      }
      return readyResult;
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return {
      success: true,
      message: `Device booted: ${this.udid} [boot in ${elapsed}s] (use --wait-ready to wait for availability)`,
    };
  }

  _waitForReady(timeoutSeconds = 120) {
    const startTime = Date.now();
    const pollInterval = 500;
    let checks = 0;

    while ((Date.now() - startTime) / 1000 < timeoutSeconds) {
      checks++;
      try {
        execFileSync(
          "xcrun",
          ["simctl", "spawn", this.udid, "launchctl", "list"],
          { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 5000 }
        );
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        return { success: true, message: `Device ready: ${this.udid} [${elapsed}s, ${checks} checks]` };
      } catch { /* not ready */ }

      const sleepMs = pollInterval;
      const end = Date.now() + sleepMs;
      while (Date.now() < end) { /* busy wait */ }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return { success: false, message: `Boot timeout: Device did not reach ready state within ${elapsed}s (${checks} checks)` };
  }

  static bootAll() {
    const sims = listSimulators("available");
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      const booter = new SimulatorBooter(sim.udid);
      const { success } = booter.boot(false);
      success ? succeeded++ : failed++;
    }
    return { succeeded, failed };
  }

  static bootByType(deviceType) {
    const sims = listSimulators("available");
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      if (sim.name.toLowerCase().includes(deviceType.toLowerCase())) {
        const booter = new SimulatorBooter(sim.udid);
        const { success } = booter.boot(false);
        success ? succeeded++ : failed++;
      }
    }
    return { succeeded, failed };
  }
}

function parseArgs() {
  const args = { udid: null, name: null, waitReady: false, timeout: 120, all: false, type: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--udid": args.udid = argv[++i]; break;
      case "--name": args.name = argv[++i]; break;
      case "--wait-ready": args.waitReady = true; break;
      case "--timeout": args.timeout = parseInt(argv[++i], 10); break;
      case "--all": args.all = true; break;
      case "--type": args.type = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simctlBoot.js [--udid ID | --name NAME | --all | --type TYPE] [--wait-ready] [--timeout N] [--json]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  if (args.all) {
    const { succeeded, failed } = SimulatorBooter.bootAll();
    const total = succeeded + failed;
    if (args.json) {
      console.log(JSON.stringify({ action: "boot_all", succeeded, failed, total }));
    } else {
      console.log(`Boot summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    }
    process.exit(failed === 0 ? 0 : 1);
  }

  if (args.type) {
    const { succeeded, failed } = SimulatorBooter.bootByType(args.type);
    const total = succeeded + failed;
    if (args.json) {
      console.log(JSON.stringify({ action: "boot_by_type", type: args.type, succeeded, failed, total }));
    } else {
      console.log(`Boot ${args.type} summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    }
    process.exit(failed === 0 ? 0 : 1);
  }

  const deviceId = args.udid || args.name;
  if (!deviceId) {
    console.error("Error: Specify --udid, --name, --all, or --type");
    process.exit(1);
  }

  let udid;
  try {
    udid = resolveDeviceIdentifier(deviceId);
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }

  const booter = new SimulatorBooter(udid);
  const { success, message } = booter.boot(args.waitReady, args.timeout);

  if (args.json) {
    console.log(JSON.stringify({ action: "boot", deviceId, udid, success, message }));
  } else {
    console.log(message);
  }
  process.exit(success ? 0 : 1);
}

main();
