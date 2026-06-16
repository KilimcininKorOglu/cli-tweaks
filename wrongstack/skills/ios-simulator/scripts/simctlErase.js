#!/usr/bin/env node
/**
 * Erase iOS simulators (factory reset).
 *
 * Performs a factory reset while preserving device UUID.
 * Faster than delete + create for CI/CD cleanup.
 *
 * Usage: node scripts/simctlErase.js --udid <udid> [--verify] [--timeout 30]
 */

const { execFileSync } = require("child_process");
const { listSimulators, resolveDeviceIdentifier } = require("./common");

class SimulatorEraser {
  constructor(udid = null) {
    this.udid = udid;
  }

  erase(verify = true, timeoutSeconds = 30) {
    if (!this.udid) return { success: false, message: "Error: Device UDID not specified" };

    const startTime = Date.now();

    try {
      execFileSync("xcrun", ["simctl", "erase", this.udid], {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 60000,
      });
    } catch (e) {
      const stderr = e.stderr ? e.stderr.toString().trim() : e.message;
      return { success: false, message: `Erase failed: ${stderr}` };
    }

    if (verify) {
      const verifyResult = this._verifyErase(timeoutSeconds);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      if (verifyResult.success) {
        return { success: true, message: `Device erased: ${this.udid} [factory reset complete, ${elapsed}s]` };
      }
      return verifyResult;
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return { success: true, message: `Device erase initiated: ${this.udid} [${elapsed}s] (use --verify to wait)` };
  }

  _verifyErase(timeoutSeconds = 30) {
    const startTime = Date.now();
    const pollInterval = 500;
    let checks = 0;

    while ((Date.now() - startTime) / 1000 < timeoutSeconds) {
      checks++;
      try {
        execFileSync("xcrun", ["simctl", "spawn", this.udid, "launchctl", "list"], {
          encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 5000,
        });
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        return { success: true, message: `Erase verified: ${this.udid} [${elapsed}s, ${checks} checks]` };
      } catch { /* not ready */ }
      const end = Date.now() + pollInterval;
      while (Date.now() < end) { /* busy wait */ }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    return { success: false, message: `Erase verification timeout within ${elapsed}s (${checks} checks)` };
  }

  static eraseAll() {
    const sims = listSimulators(null);
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      const { success } = new SimulatorEraser(sim.udid).erase(false);
      success ? succeeded++ : failed++;
    }
    return { succeeded, failed };
  }

  static eraseByType(deviceType) {
    const sims = listSimulators(null);
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      if (sim.name.toLowerCase().includes(deviceType.toLowerCase())) {
        const { success } = new SimulatorEraser(sim.udid).erase(false);
        success ? succeeded++ : failed++;
      }
    }
    return { succeeded, failed };
  }

  static eraseBooted() {
    const sims = listSimulators("booted");
    let succeeded = 0, failed = 0;
    for (const sim of sims) {
      const { success } = new SimulatorEraser(sim.udid).erase(false);
      success ? succeeded++ : failed++;
    }
    return { succeeded, failed };
  }
}

function parseArgs() {
  const args = { udid: null, name: null, verify: false, timeout: 30, all: false, type: null, booted: false, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--udid": args.udid = argv[++i]; break;
      case "--name": args.name = argv[++i]; break;
      case "--verify": args.verify = true; break;
      case "--timeout": args.timeout = parseInt(argv[++i], 10); break;
      case "--all": args.all = true; break;
      case "--type": args.type = argv[++i]; break;
      case "--booted": args.booted = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simctlErase.js [--udid ID | --name NAME | --all | --type TYPE | --booted] [--verify] [--timeout N] [--json]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  const outputBatch = (action, extra, { succeeded, failed }) => {
    const total = succeeded + failed;
    if (args.json) console.log(JSON.stringify({ action, ...extra, succeeded, failed, total }));
    else console.log(`Erase summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    process.exit(failed === 0 ? 0 : 1);
  };

  if (args.all) return outputBatch("erase_all", {}, SimulatorEraser.eraseAll());
  if (args.type) return outputBatch("erase_by_type", { type: args.type }, SimulatorEraser.eraseByType(args.type));
  if (args.booted) return outputBatch("erase_booted", {}, SimulatorEraser.eraseBooted());

  const deviceId = args.udid || args.name;
  if (!deviceId) { console.error("Error: Specify --udid, --name, --all, --type, or --booted"); process.exit(1); }

  let udid;
  try { udid = resolveDeviceIdentifier(deviceId); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const { success, message } = new SimulatorEraser(udid).erase(args.verify, args.timeout);

  if (args.json) console.log(JSON.stringify({ action: "erase", deviceId, udid, success, message }));
  else console.log(message);
  process.exit(success ? 0 : 1);
}

main();
