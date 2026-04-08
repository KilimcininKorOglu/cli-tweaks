#!/usr/bin/env node
/**
 * iOS Simulator Listing with Progressive Disclosure
 *
 * Lists available simulators with token-efficient summaries.
 * Achieves 96% token reduction (57k→2k tokens) for common queries.
 *
 * Usage: node scripts/simList.js [--get-details CACHE_ID] [--suggest] [--device-type iPhone] [--json]
 */

const { execFileSync } = require("child_process");
const { getCache } = require("./common");

class SimulatorLister {
  constructor() {
    this.cache = getCache();
  }

  listSimulators() {
    try {
      const output = execFileSync("xcrun", ["simctl", "list", "devices", "--json"], {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      return JSON.parse(output);
    } catch {
      return { devices: {} };
    }
  }

  parseDevices(simData) {
    const devices = [];
    for (const [runtimeStr, deviceList] of Object.entries(simData.devices || {})) {
      const runtimeName = runtimeStr.replace(" Simulator", "").trim();
      for (const device of deviceList) {
        devices.push({
          name: device.name,
          udid: device.udid,
          state: device.state,
          runtime: runtimeName,
          isAvailable: device.isAvailable || false,
        });
      }
    }
    return devices;
  }

  getConciseSummary(devices) {
    const booted = devices.filter((d) => d.state === "Booted");
    const available = devices.filter((d) => d.isAvailable);
    const iphone = available.filter((d) => d.name.includes("iPhone"));

    const cacheId = this.cache.save(
      { devices, timestamp: new Date().toISOString() },
      "simulator-list"
    );

    return {
      cacheId,
      summary: {
        totalDevices: devices.length,
        availableDevices: available.length,
        bootedDevices: booted.length,
      },
      quickAccess: {
        booted: booted.slice(0, 3),
        recommendedIphone: iphone.slice(0, 3),
      },
    };
  }

  getFullList(cacheId, deviceType = null, runtime = null) {
    const data = this.cache.get(cacheId);
    if (!data) return null;
    let devices = data.devices || [];
    if (deviceType) devices = devices.filter((d) => d.name.includes(deviceType));
    if (runtime) devices = devices.filter((d) => d.runtime.toLowerCase().includes(runtime.toLowerCase()));
    return devices;
  }

  suggestSimulators(limit = 4) {
    const simData = this.listSimulators();
    const devices = this.parseDevices(simData);
    const scored = devices.map((device) => {
      let score = 0;
      if (device.state === "Booted") score += 10;
      if (device.isAvailable) score += 5;
      if (device.runtime.includes("18")) score += 3;
      else if (device.runtime.includes("17")) score += 2;
      if (device.name.includes("iPhone")) score += 1;
      return { device, score };
    });
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.device);
  }
}

function formatDevice(device) {
  const stateIcon = device.state === "Booted" ? "V" : " ";
  const availIcon = device.isAvailable ? "●" : "○";
  const udidShort = (device.udid || "").slice(0, 8) + "...";
  return `${stateIcon} ${availIcon} ${device.name} (${device.runtime}) [${udidShort}]`;
}

function parseArgs() {
  const args = { getDetails: null, suggest: false, deviceType: null, runtime: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--get-details": args.getDetails = argv[++i]; break;
      case "--suggest": args.suggest = true; break;
      case "--device-type": args.deviceType = argv[++i]; break;
      case "--runtime": args.runtime = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simList.js [--get-details CACHE_ID] [--suggest] [--device-type TYPE] [--runtime VER] [--json]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();
  const lister = new SimulatorLister();

  if (args.getDetails) {
    const devices = lister.getFullList(args.getDetails, args.deviceType, args.runtime);
    if (!devices) { console.error(`Error: Cache ID not found or expired: ${args.getDetails}`); process.exit(1); }
    if (args.json) console.log(JSON.stringify(devices, null, 2));
    else {
      console.log(`Simulators (${devices.length}):\n`);
      devices.forEach((d) => console.log(`  ${formatDevice(d)}`));
    }
  } else if (args.suggest) {
    const suggestions = lister.suggestSimulators();
    if (args.json) console.log(JSON.stringify(suggestions, null, 2));
    else {
      console.log("Recommended Simulators:\n");
      suggestions.forEach((d, i) => console.log(`${i + 1}. ${formatDevice(d)}`));
    }
  } else {
    const simData = lister.listSimulators();
    const devices = lister.parseDevices(simData);
    const summary = lister.getConciseSummary(devices);

    if (args.json) console.log(JSON.stringify(summary, null, 2));
    else {
      const { cacheId, summary: s, quickAccess: q } = summary;
      console.log(`Simulator Summary [${cacheId}]`);
      console.log(`|- Total: ${s.totalDevices} devices`);
      console.log(`|- Available: ${s.availableDevices}`);
      console.log(`|- Booted: ${s.bootedDevices}`);
      if (q.booted.length) {
        console.log();
        q.booted.forEach((d) => console.log(`  ${formatDevice(d)}`));
      }
      console.log(`\nUse --get-details ${cacheId} for full list`);
    }
  }
}

main();
