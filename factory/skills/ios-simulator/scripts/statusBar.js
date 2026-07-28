#!/usr/bin/env node
/**
 * iOS Status Bar Controller
 *
 * Override simulator status bar for clean screenshots and testing.
 * Control time, network, wifi, battery display.
 *
 * Usage: node scripts/statusBar.js --preset clean
 */

const { execFileSync } = require("child_process");
const { resolveUdid } = require("./common");

const PRESETS = {
  clean: {
    time: "9:41",
    dataNetwork: "5g",
    wifiMode: "active",
    batteryState: "charged",
    batteryLevel: 100,
  },
  testing: {
    time: "11:11",
    dataNetwork: "4g",
    wifiMode: "active",
    batteryState: "discharging",
    batteryLevel: 50,
  },
  "low-battery": {
    time: "9:41",
    dataNetwork: "5g",
    wifiMode: "active",
    batteryState: "discharging",
    batteryLevel: 20,
  },
  airplane: {
    time: "9:41",
    dataNetwork: "none",
    wifiMode: "failed",
    batteryState: "charged",
    batteryLevel: 100,
  },
};

class StatusBarController {
  /**
   * @param {string|null} udid
   */
  constructor(udid = null) {
    this.udid = udid;
  }

  /**
   * Override status bar appearance.
   *
   * @param {object} opts
   * @param {string|null} opts.time - HH:MM format
   * @param {string|null} opts.dataNetwork - none, 1x, 3g, 4g, 5g, lte, lte-a
   * @param {string|null} opts.wifiMode - active, searching, failed
   * @param {string|null} opts.batteryState - charging, charged, discharging
   * @param {number|null} opts.batteryLevel - 0-100
   * @returns {boolean}
   */
  override({ time, dataNetwork, wifiMode, batteryState, batteryLevel } = {}) {
    const cmd = ["simctl", "status_bar", this.udid || "booted", "override"];

    if (time) cmd.push("--time", time);
    if (dataNetwork) cmd.push("--dataNetwork", dataNetwork);
    if (wifiMode) cmd.push("--wifiMode", wifiMode);
    if (batteryState) cmd.push("--batteryState", batteryState);
    if (batteryLevel !== null && batteryLevel !== undefined)
      cmd.push("--batteryLevel", String(batteryLevel));

    try {
      execFileSync("xcrun", cmd, { stdio: ["pipe", "pipe", "pipe"] });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Clear status bar override and restore defaults.
   * @returns {boolean}
   */
  clear() {
    try {
      execFileSync(
        "xcrun",
        ["simctl", "status_bar", this.udid || "booted", "clear"],
        { stdio: ["pipe", "pipe", "pipe"] }
      );
      return true;
    } catch {
      return false;
    }
  }
}

function parseArgs() {
  const args = {
    preset: null,
    time: null,
    dataNetwork: null,
    wifiMode: null,
    batteryState: null,
    batteryLevel: null,
    clear: false,
    udid: null,
  };
  const argv = process.argv.slice(2);

  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--preset":
        args.preset = argv[++i];
        break;
      case "--time":
        args.time = argv[++i];
        break;
      case "--data-network":
        args.dataNetwork = argv[++i];
        break;
      case "--wifi-mode":
        args.wifiMode = argv[++i];
        break;
      case "--battery-state":
        args.batteryState = argv[++i];
        break;
      case "--battery-level":
        args.batteryLevel = parseInt(argv[++i], 10);
        break;
      case "--clear":
        args.clear = true;
        break;
      case "--udid":
        args.udid = argv[++i];
        break;
      case "--help":
        console.log(
          "Usage: node statusBar.js [--preset clean|testing|low-battery|airplane] " +
          "[--time HH:MM] [--data-network TYPE] [--battery-level N] " +
          "[--clear] [--udid UDID]"
        );
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();

  let udid;
  try {
    udid = resolveUdid(args.udid);
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }

  const controller = new StatusBarController(udid);

  if (args.clear) {
    if (controller.clear()) {
      console.log("Status bar override cleared - defaults restored");
    } else {
      console.error("Failed to clear status bar override");
      process.exit(1);
    }
  } else if (args.preset) {
    const preset = PRESETS[args.preset];
    if (!preset) {
      console.error(
        `Unknown preset: ${args.preset}. Available: ${Object.keys(PRESETS).join(", ")}`
      );
      process.exit(1);
    }
    if (controller.override(preset)) {
      console.log(`Status bar: ${args.preset} preset applied`);
      console.log(
        `  Time: ${preset.time}, Network: ${preset.dataNetwork}, Battery: ${preset.batteryLevel}%`
      );
    } else {
      console.error(`Failed to apply ${args.preset} preset`);
      process.exit(1);
    }
  } else if (
    args.time ||
    args.dataNetwork ||
    args.wifiMode ||
    args.batteryState ||
    args.batteryLevel !== null
  ) {
    if (controller.override(args)) {
      let output = "Status bar override applied:";
      if (args.time) output += ` Time=${args.time}`;
      if (args.dataNetwork) output += ` Network=${args.dataNetwork}`;
      if (args.batteryLevel !== null) output += ` Battery=${args.batteryLevel}%`;
      console.log(output);
    } else {
      console.error("Failed to override status bar");
      process.exit(1);
    }
  } else {
    console.log(
      "Usage: node statusBar.js [--preset clean|testing|low-battery|airplane] " +
      "[--time HH:MM] [--data-network TYPE] [--battery-level N] " +
      "[--clear] [--udid UDID]"
    );
    process.exit(1);
  }
}

main();
