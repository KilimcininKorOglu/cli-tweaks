#!/usr/bin/env node
/**
 * Create iOS simulators dynamically.
 *
 * Key features:
 * - Create by device type (iPhone 16 Pro, iPad Air, etc.)
 * - Specify iOS version (17.0, 18.0, etc.)
 * - Custom device naming
 * - Return newly created device UDID
 * - List available device types and runtimes
 *
 * Usage: node scripts/simctlCreate.js --device "iPhone 16 Pro" [--runtime 18.0] [--name MyDevice]
 */

const { execFileSync } = require("child_process");

function getDeviceTypes() {
  try {
    const output = execFileSync("xcrun", ["simctl", "list", "devicetypes", "-j"], {
      encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
    });
    const data = JSON.parse(output);
    return (data.devicetypes || []).map((d) => ({
      name: d.name || "",
      identifier: d.identifier || "",
    }));
  } catch { return []; }
}

function getRuntimes() {
  try {
    const output = execFileSync("xcrun", ["simctl", "list", "runtimes", "-j"], {
      encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
    });
    const data = JSON.parse(output);
    return (data.runtimes || [])
      .filter((r) => (r.identifier || "").includes("iOS") || (r.name || "").includes("iOS"))
      .map((r) => ({ name: r.name || "", identifier: r.identifier || "" }))
      .sort((a, b) => b.identifier.localeCompare(a.identifier));
  } catch { return []; }
}

function create(deviceType, iosVersion = null, customName = null) {
  const types = getDeviceTypes();
  if (!types.length) return { success: false, message: "Failed to get available device types", newUdid: null };

  const matched = types.find((dt) => dt.name.toLowerCase().includes(deviceType.toLowerCase()));
  if (!matched) return { success: false, message: `Device type '${deviceType}' not found. Use --list-devices.`, newUdid: null };

  const runtimes = getRuntimes();
  if (!runtimes.length) return { success: false, message: "Failed to get available runtimes", newUdid: null };

  let runtimeId = null;
  if (iosVersion) {
    const rt = runtimes.find((r) => r.name.includes(iosVersion));
    if (!rt) return { success: false, message: `iOS version '${iosVersion}' not found. Use --list-runtimes.`, newUdid: null };
    runtimeId = rt.identifier;
  } else {
    runtimeId = runtimes[0].identifier;
  }

  const deviceName = customName || `${matched.identifier.split(".").pop()}-${iosVersion || "latest"}`;

  try {
    const output = execFileSync(
      "xcrun", ["simctl", "create", deviceName, matched.identifier, runtimeId],
      { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 60000 }
    );
    const newUdid = output.trim();
    return {
      success: true,
      message: `Device created: ${deviceName} (${deviceType}) iOS ${iosVersion || "latest"} UDID: ${newUdid}`,
      newUdid,
    };
  } catch (e) {
    const stderr = e.stderr ? e.stderr.toString().trim() : e.message;
    return { success: false, message: `Creation failed: ${stderr}`, newUdid: null };
  }
}

function parseArgs() {
  const args = { device: null, runtime: null, name: null, listDevices: false, listRuntimes: false, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--device": args.device = argv[++i]; break;
      case "--runtime": args.runtime = argv[++i]; break;
      case "--name": args.name = argv[++i]; break;
      case "--list-devices": args.listDevices = true; break;
      case "--list-runtimes": args.listRuntimes = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simctlCreate.js [--device TYPE] [--runtime VER] [--name NAME] [--list-devices] [--list-runtimes] [--json]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  if (args.listDevices) {
    const devices = getDeviceTypes();
    if (args.json) { console.log(JSON.stringify({ devices })); }
    else {
      console.log(`Available device types (${devices.length}):`);
      devices.slice(0, 20).forEach((d) => console.log(`  - ${d.name}`));
      if (devices.length > 20) console.log(`  ... and ${devices.length - 20} more`);
    }
    process.exit(0);
  }

  if (args.listRuntimes) {
    const runtimes = getRuntimes();
    if (args.json) { console.log(JSON.stringify({ runtimes })); }
    else {
      console.log(`Available iOS runtimes (${runtimes.length}):`);
      runtimes.forEach((r) => console.log(`  - ${r.name}`));
    }
    process.exit(0);
  }

  if (!args.device) {
    console.error("Error: Specify --device, --list-devices, or --list-runtimes");
    process.exit(1);
  }

  const { success, message, newUdid } = create(args.device, args.runtime, args.name);

  if (args.json) {
    console.log(JSON.stringify({ action: "create", deviceType: args.device, runtime: args.runtime, success, message, newUdid }));
  } else {
    console.log(message);
  }
  process.exit(success ? 0 : 1);
}

main();
