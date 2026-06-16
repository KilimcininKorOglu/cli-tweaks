#!/usr/bin/env node
/**
 * Intelligent Simulator Selector
 *
 * Suggests the best available iOS simulators based on:
 * - Recently used (from config)
 * - Latest iOS version
 * - Common models for testing
 * - Boot status
 *
 * Usage: node scripts/simulatorSelector.js --suggest [--json] [--count 4]
 */

const { execFileSync } = require("child_process");

const COMMON_MODELS = [
  "iPhone 16 Pro",
  "iPhone 16",
  "iPhone 15 Pro",
  "iPhone 15",
  "iPhone SE (3rd generation)",
];

class SimulatorSelector {
  constructor() {
    this.simulators = [];
    this.lastUsedSimulator = null;
    try {
      const { Config } = require("./xcode/config");
      const config = Config.load();
      this.lastUsedSimulator = config.getPreferredSimulator ? config.getPreferredSimulator() : null;
    } catch { /* config not available */ }
  }

  listSimulators() {
    try {
      const output = execFileSync("xcrun", ["simctl", "list", "devices", "--json"], {
        encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
      });
      const data = JSON.parse(output);
      const simulators = [];

      for (const [runtime, devices] of Object.entries(data.devices || {})) {
        const iosMatch = runtime.match(/iOS-(\d+-\d+)/);
        if (!iosMatch) continue;
        const iosVersion = iosMatch[1].replace("-", ".");

        for (const device of devices) {
          if (!device.isAvailable || !device.name.includes("iPhone")) continue;
          simulators.push({
            name: device.name,
            udid: device.udid,
            iosVersion,
            status: (device.state || "").charAt(0).toUpperCase() + (device.state || "").slice(1),
            reasons: [],
          });
        }
      }
      this.simulators = simulators;
      return simulators;
    } catch (e) {
      console.error(`Error listing simulators: ${e.message}`);
      return [];
    }
  }

  getSuggestions(count = 4) {
    if (!this.simulators.length) return [];

    const latestIos = this.simulators.reduce((max, s) =>
      s.iosVersion > max ? s.iosVersion : max, "0"
    );

    const scored = this.simulators.map((sim) => {
      let score = 0;
      if (this.lastUsedSimulator && this.lastUsedSimulator === sim.name) score += 100;
      if (sim.iosVersion === latestIos) score += 50;
      const modelIdx = COMMON_MODELS.findIndex((m) => sim.name.includes(m));
      if (modelIdx >= 0) score += 30 - modelIdx * 2;
      if (sim.status === "Booted") score += 10;
      score += parseFloat(sim.iosVersion.replace(".", "")) * 0.1;
      return { sim, score };
    });

    scored.sort((a, b) => b.score - a.score);
    const suggestions = scored.slice(0, count).map((s) => s.sim);

    suggestions.forEach((sim, i) => {
      if (i === 0) sim.reasons.push("Recommended");
      if (this.lastUsedSimulator && this.lastUsedSimulator === sim.name) sim.reasons.push("Recently used");
      if (sim.iosVersion === latestIos) sim.reasons.push("Latest iOS");
      const modelIdx = COMMON_MODELS.findIndex((m) => sim.name.includes(m));
      if (modelIdx >= 0) sim.reasons.push(`#${modelIdx + 1} common model`);
      if (sim.status === "Booted") sim.reasons.push("Currently running");
    });

    return suggestions;
  }

  bootSimulator(udid) {
    try {
      execFileSync("xcrun", ["simctl", "boot", udid], { stdio: ["pipe", "pipe", "pipe"] });
      return true;
    } catch (e) {
      console.error(`Error booting simulator: ${e.message}`);
      return false;
    }
  }
}

function formatSuggestions(suggestions, jsonFormat = false) {
  if (jsonFormat) return JSON.stringify({ suggestions: suggestions.map((s) => ({
    device: s.name, udid: s.udid, ios: s.iosVersion, status: s.status, reasons: s.reasons,
  }))}, null, 2);

  if (!suggestions.length) return "No simulators available";

  const lines = ["Available Simulators:\n"];
  suggestions.forEach((sim, i) => {
    lines.push(`${i + 1}. ${sim.name} (iOS ${sim.iosVersion})`);
    if (sim.reasons.length) lines.push(`   ${sim.reasons.join(", ")}`);
    lines.push(`   UDID: ${sim.udid}`, "");
  });
  return lines.join("\n");
}

function parseArgs() {
  const args = { suggest: false, list: false, boot: null, json: false, count: 4 };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--suggest": args.suggest = true; break;
      case "--list": args.list = true; break;
      case "--boot": args.boot = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--count": args.count = parseInt(argv[++i], 10); break;
      case "--help":
        console.log("Usage: node simulatorSelector.js [--suggest|--list|--boot UDID] [--json] [--count N]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();
  const selector = new SimulatorSelector();

  if (args.boot) {
    const ok = selector.bootSimulator(args.boot);
    if (ok) console.log(`Booted simulator: ${args.boot}`);
    process.exit(ok ? 0 : 1);
  }

  if (args.list) {
    const sims = selector.listSimulators();
    console.log(formatSuggestions(sims, args.json));
    process.exit(0);
  }

  // Default: suggest
  selector.listSimulators();
  const suggestions = selector.getSuggestions(args.count);
  console.log(formatSuggestions(suggestions, args.json));
}

main();
