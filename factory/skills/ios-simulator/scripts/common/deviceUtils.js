#!/usr/bin/env node
/**
 * Shared device and simulator utilities.
 *
 * Common patterns for interacting with simulators via xcrun simctl and IDB.
 * Standardizes command building and device targeting to prevent errors.
 *
 * Used by:
 * - appLauncher.js (8 call sites) - App lifecycle commands
 * - Multiple scripts (15+ locations) - IDB command building
 * - navigator.js, gesture.js - Coordinate transformation
 * - testRecorder.js, appStateCapture.js - Auto-UDID detection
 */

const { execFileSync } = require("child_process");

/**
 * Build xcrun simctl command with proper device handling.
 *
 * Standardizes command building to prevent device targeting bugs.
 * Automatically uses "booted" if no UDID provided.
 *
 * @param {string} operation - simctl operation (launch, terminate, install, etc.)
 * @param {string|null} udid - Device UDID (uses 'booted' if null)
 * @param {...string} args - Additional command arguments
 * @returns {string[]} Complete command args ready for execFileSync
 */
function buildSimctlCommand(operation, udid, ...args) {
  const cmd = ["simctl", operation, udid || "booted"];
  cmd.push(...args.map(String));
  return cmd;
}

/**
 * Build IDB command with proper device targeting.
 *
 * Standardizes IDB command building across all scripts using IDB.
 * Handles device UDID consistently.
 *
 * @param {string} operation - IDB operation path (e.g., "ui tap", "ui text")
 * @param {string|null} udid - Device UDID (omits --udid flag if null)
 * @param {...string} args - Additional command arguments
 * @returns {string[]} Complete command args ready for execFileSync
 */
function buildIdbCommand(operation, udid, ...args) {
  const cmd = operation.split(" ");
  cmd.push(...args.map(String));
  if (udid) {
    cmd.push("--udid", udid);
  }
  return cmd;
}

/**
 * Auto-detect currently booted simulator UDID.
 *
 * Queries xcrun simctl for booted devices and returns first match.
 *
 * @returns {string|null} UDID of booted simulator, or null if none booted
 */
function getBootedDeviceUdid() {
  try {
    const output = execFileSync(
      "xcrun",
      ["simctl", "list", "devices", "booted"],
      { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }
    );
    const match = output.match(/\(([A-F0-9-]{36})\)/);
    return match ? match[1] : null;
  } catch {
    return null;
  }
}

/**
 * Resolve device UDID with auto-detection fallback.
 *
 * If udidArg is provided, returns it immediately.
 * If null, attempts to auto-detect booted simulator.
 *
 * @param {string|null} udidArg - Explicit UDID from command line, or null
 * @returns {string} Valid UDID string
 * @throws {Error} If no UDID provided and no booted simulator found
 */
function resolveUdid(udidArg) {
  if (udidArg) return udidArg;

  const bootedUdid = getBootedDeviceUdid();
  if (bootedUdid) return bootedUdid;

  throw new Error(
    "No device UDID provided and no simulator is currently booted.\n" +
    "Boot a simulator or provide --udid explicitly:\n" +
    "  xcrun simctl boot <device-name>\n" +
    "  node scripts/script_name.js --udid <device-udid>"
  );
}

/**
 * Get actual screen dimensions for device via accessibility tree.
 *
 * Queries IDB accessibility tree to determine actual device resolution.
 * Falls back to iPhone 14 defaults (390x844) if detection fails.
 *
 * @param {string} udid - Device UDID
 * @returns {{width: number, height: number}} Screen dimensions in pixels
 */
function getDeviceScreenSize(udid) {
  try {
    const cmd = buildIdbCommand("ui describe-all", udid, "--json");
    const output = execFileSync("idb", cmd, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    const data = JSON.parse(output);
    const tree = Array.isArray(data) && data.length > 0 ? data[0] : data;

    if (tree && tree.frame) {
      return {
        width: parseInt(tree.frame.width, 10) || 390,
        height: parseInt(tree.frame.height, 10) || 844,
      };
    }
    return { width: 390, height: 844 };
  } catch {
    return { width: 390, height: 844 };
  }
}

/**
 * Resolve device name or partial UDID to full UDID.
 *
 * Supports multiple identifier formats:
 * - Full UDID: "ABC-123-DEF456..." (36 character UUID)
 * - Device name: "iPhone 16 Pro" (matches full name)
 * - Partial match: "iPhone 16" (matches first device containing this string)
 * - Special: "booted" (resolves to currently booted device)
 *
 * @param {string} identifier - Device UDID, name, or "booted"
 * @returns {string} Full device UDID
 * @throws {Error} If identifier cannot be resolved
 */
function resolveDeviceIdentifier(identifier) {
  if (identifier.toLowerCase() === "booted") {
    const booted = getBootedDeviceUdid();
    if (booted) return booted;
    throw new Error(
      "No simulator is currently booted. " +
      "Boot a simulator first: xcrun simctl boot <device-udid>"
    );
  }

  if (/^[A-F0-9-]{36}$/i.test(identifier)) {
    return identifier.toUpperCase();
  }

  const simulators = listSimulators(null);
  const lowerIdent = identifier.toLowerCase();

  const exact = simulators.find((s) => s.name.toLowerCase() === lowerIdent);
  if (exact) return exact.udid;

  const partial = simulators.find((s) =>
    s.name.toLowerCase().includes(lowerIdent)
  );
  if (partial) return partial.udid;

  throw new Error(
    `Device '${identifier}' not found. ` +
    "Use 'xcrun simctl list devices' to see available simulators."
  );
}

/**
 * List iOS simulators with optional state filtering.
 *
 * @param {string|null} state - Optional filter: "available", "booted", or null for all
 * @returns {Array<{name: string, udid: string, state: string, runtime: string, type: string}>}
 */
function listSimulators(state) {
  try {
    const output = execFileSync(
      "xcrun",
      ["simctl", "list", "devices", "-j"],
      { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }
    );
    const data = JSON.parse(output);
    const simulators = [];

    for (const [iosVersion, devices] of Object.entries(
      data.devices || {}
    )) {
      for (const device of devices) {
        simulators.push({
          name: device.name || "Unknown",
          udid: device.udid || "",
          state: device.state || "Unknown",
          runtime: iosVersion,
          type: extractDeviceType(device.name || ""),
        });
      }
    }

    if (state === "booted") {
      return simulators.filter((s) => s.state === "Booted");
    }
    if (state === "available") {
      return simulators.filter((s) => s.state === "Shutdown");
    }
    if (state === null || state === undefined) {
      return simulators;
    }
    return simulators.filter(
      (s) => s.state.toLowerCase() === state.toLowerCase()
    );
  } catch (e) {
    throw new Error(`Failed to list simulators: ${e.message}`);
  }
}

/**
 * Extract device type from device name.
 *
 * @param {string} deviceName - Full device name (e.g., "iPhone 16 Pro")
 * @returns {string} Device type string
 */
function extractDeviceType(deviceName) {
  if (deviceName.includes("iPhone")) return "iPhone";
  if (deviceName.includes("iPad")) return "iPad";
  if (deviceName.includes("Watch") || deviceName.includes("Apple Watch"))
    return "Watch";
  if (deviceName.includes("TV") || deviceName.includes("Apple TV"))
    return "TV";
  return "Unknown";
}

/**
 * Transform screenshot coordinates to device coordinates.
 *
 * Handles the case where a screenshot was downscaled and needs to be
 * transformed back to actual device pixel coordinates for accurate tapping.
 *
 * @param {number} x - X coordinate in screenshot
 * @param {number} y - Y coordinate in screenshot
 * @param {number} screenshotWidth - Screenshot width
 * @param {number} screenshotHeight - Screenshot height
 * @param {number} deviceWidth - Actual device width
 * @param {number} deviceHeight - Actual device height
 * @returns {{x: number, y: number}} Device coordinates
 */
function transformScreenshotCoords(
  x,
  y,
  screenshotWidth,
  screenshotHeight,
  deviceWidth,
  deviceHeight
) {
  return {
    x: Math.round((x / screenshotWidth) * deviceWidth),
    y: Math.round((y / screenshotHeight) * deviceHeight),
  };
}

module.exports = {
  buildSimctlCommand,
  buildIdbCommand,
  getBootedDeviceUdid,
  resolveUdid,
  getDeviceScreenSize,
  resolveDeviceIdentifier,
  listSimulators,
  extractDeviceType,
  transformScreenshotCoords,
};
