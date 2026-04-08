#!/usr/bin/env node
/**
 * iOS Simulator Clipboard Manager
 *
 * Copy text to simulator clipboard for testing paste flows.
 * Optimized for minimal token output.
 *
 * Usage: node scripts/clipboard.js --copy "text to copy"
 */

const { execFileSync } = require("child_process");
const { resolveUdid } = require("./common");

class ClipboardManager {
  /**
   * @param {string|null} udid - Optional device UDID (auto-detects if null)
   */
  constructor(udid = null) {
    this.udid = udid;
  }

  /**
   * Copy text to simulator clipboard.
   *
   * @param {string} text - Text to copy
   * @returns {boolean} Success status
   */
  copy(text) {
    const cmd = ["simctl", "pbcopy", this.udid || "booted", text];
    try {
      execFileSync("xcrun", cmd, { stdio: ["pipe", "pipe", "pipe"] });
      return true;
    } catch {
      return false;
    }
  }
}

function parseArgs() {
  const args = { copy: null, udid: null, testName: null, expected: null };
  const argv = process.argv.slice(2);

  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--copy":
        args.copy = argv[++i];
        break;
      case "--udid":
        args.udid = argv[++i];
        break;
      case "--test-name":
        args.testName = argv[++i];
        break;
      case "--expected":
        args.expected = argv[++i];
        break;
      case "--help":
        console.log(
          "Usage: node clipboard.js --copy <text> [--udid <udid>] [--test-name <name>] [--expected <text>]"
        );
        process.exit(0);
    }
  }

  if (!args.copy) {
    console.error("Error: --copy is required");
    process.exit(1);
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

  const manager = new ClipboardManager(udid);

  if (manager.copy(args.copy)) {
    let output = `Copied: "${args.copy}"`;
    if (args.testName) output += ` (test: ${args.testName})`;
    console.log(output);

    if (args.expected) console.log(`Expected: ${args.expected}`);

    console.log("\nNext steps:");
    console.log(
      "1. Tap text field with: node scripts/navigator.js --find-type TextField --tap"
    );
    console.log(
      "2. Paste with: node scripts/keyboard.js --key cmd+v"
    );
  } else {
    console.error("Failed to copy text to clipboard");
    process.exit(1);
  }
}

main();
