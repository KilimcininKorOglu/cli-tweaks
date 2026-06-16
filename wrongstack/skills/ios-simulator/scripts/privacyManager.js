#!/usr/bin/env node
/**
 * iOS Privacy & Permissions Manager
 *
 * Grant/revoke app permissions for testing permission flows.
 * Supports 13+ services with audit trail tracking.
 *
 * Usage: node scripts/privacyManager.js --grant camera --bundle-id com.app
 */

const { execFileSync } = require("child_process");
const { resolveUdid } = require("./common");

const SUPPORTED_SERVICES = {
  camera: "Camera access",
  microphone: "Microphone access",
  location: "Location services",
  contacts: "Contacts access",
  photos: "Photos library access",
  calendar: "Calendar access",
  health: "Health data access",
  reminders: "Reminders access",
  motion: "Motion & fitness",
  keyboard: "Keyboard access",
  mediaLibrary: "Media library",
  calls: "Call history",
  siri: "Siri access",
};

class PrivacyManager {
  constructor(udid = null) {
    this.udid = udid;
  }

  _runPrivacyCmd(action, service, bundleId) {
    if (!SUPPORTED_SERVICES[service]) {
      console.error(`Error: Unknown service '${service}'`);
      console.error(`Supported: ${Object.keys(SUPPORTED_SERVICES).join(", ")}`);
      return false;
    }
    try {
      execFileSync(
        "xcrun",
        ["simctl", "privacy", this.udid || "booted", action, service, bundleId],
        { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }
      );
      return true;
    } catch {
      return false;
    }
  }

  grant(bundleId, service, scenario, step) {
    const ok = this._runPrivacyCmd("grant", service, bundleId);
    if (ok) logAudit("grant", bundleId, service, scenario, step);
    return ok;
  }

  revoke(bundleId, service, scenario, step) {
    const ok = this._runPrivacyCmd("revoke", service, bundleId);
    if (ok) logAudit("revoke", bundleId, service, scenario, step);
    return ok;
  }

  reset(bundleId, service, scenario, step) {
    const ok = this._runPrivacyCmd("reset", service, bundleId);
    if (ok) logAudit("reset", bundleId, service, scenario, step);
    return ok;
  }
}

function logAudit(action, bundleId, service, scenario, step) {
  const ts = new Date().toISOString();
  const loc = step ? ` (step ${step})` : "";
  const sc = scenario ? ` in ${scenario}` : "";
  console.log(`[Audit] ${ts}: ${action.toUpperCase()} ${service} for ${bundleId}${sc}${loc}`);
}

function parseArgs() {
  const args = { bundleId: null, grant: null, revoke: null, reset: null, list: false, scenario: null, step: null, udid: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--bundle-id": args.bundleId = argv[++i]; break;
      case "--grant": args.grant = argv[++i]; break;
      case "--revoke": args.revoke = argv[++i]; break;
      case "--reset": args.reset = argv[++i]; break;
      case "--list": args.list = true; break;
      case "--scenario": args.scenario = argv[++i]; break;
      case "--step": args.step = parseInt(argv[++i], 10); break;
      case "--udid": args.udid = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node privacyManager.js --bundle-id <id> [--grant|--revoke|--reset SERVICE] [--list] [--udid UDID]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  if (args.list) {
    console.log("Supported Privacy Services:\n");
    for (const [service, desc] of Object.entries(SUPPORTED_SERVICES)) {
      console.log(`  ${service.padEnd(15)} - ${desc}`);
    }
    console.log("\nExamples:");
    console.log("  node privacyManager.js --grant camera --bundle-id com.app");
    console.log("  node privacyManager.js --revoke location --bundle-id com.app");
    console.log("  node privacyManager.js --grant camera,photos --bundle-id com.app");
    process.exit(0);
  }

  if (!args.bundleId) { console.error("Error: --bundle-id is required"); process.exit(1); }

  let udid;
  try { udid = resolveUdid(args.udid); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const manager = new PrivacyManager(udid);

  let services, action, actionFn;
  if (args.grant) {
    services = args.grant.split(",").map((s) => s.trim());
    action = "grant";
    actionFn = (s) => manager.grant(args.bundleId, s, args.scenario, args.step);
  } else if (args.revoke) {
    services = args.revoke.split(",").map((s) => s.trim());
    action = "revoke";
    actionFn = (s) => manager.revoke(args.bundleId, s, args.scenario, args.step);
  } else if (args.reset) {
    services = args.reset.split(",").map((s) => s.trim());
    action = "reset";
    actionFn = (s) => manager.reset(args.bundleId, s, args.scenario, args.step);
  } else {
    console.error("Error: Specify --grant, --revoke, --reset, or --list");
    process.exit(1);
  }

  let allSuccess = true;
  for (const service of services) {
    if (!SUPPORTED_SERVICES[service]) {
      console.error(`Error: Unknown service '${service}'`);
      allSuccess = false;
      continue;
    }
    if (actionFn(service)) {
      console.log(`OK ${action} ${service}: ${SUPPORTED_SERVICES[service]}`);
    } else {
      console.error(`FAIL ${action} ${service}`);
      allSuccess = false;
    }
  }

  if (services.length > 1) console.log(`\nPermissions ${action}ed: ${services.join(", ")}`);
  if (args.scenario) console.log(`Test scenario: ${args.scenario}${args.step ? ` (step ${args.step})` : ""}`);
  if (!allSuccess) process.exit(1);
}

main();
