#!/usr/bin/env node
/**
 * iOS Keyboard Controller - Text Entry and Hardware Buttons
 *
 * Handles keyboard input, special keys, and hardware button simulation.
 *
 * Usage:
 *   node scripts/keyboard.js --type "hello@example.com"
 *   node scripts/keyboard.js --key return
 *   node scripts/keyboard.js --button home
 */

const { execFileSync } = require("child_process");
const { resolveUdid } = require("./common");

const SPECIAL_KEYS = {
  return: 40, enter: 40,
  delete: 42, backspace: 42,
  tab: 43, space: 44, escape: 41,
  up: 82, down: 81, left: 80, right: 79,
};

const HARDWARE_BUTTONS = {
  home: "HOME", lock: "LOCK", power: "LOCK",
  "volume-up": "VOLUME_UP", "volume-down": "VOLUME_DOWN",
  ringer: "RINGER", screenshot: "SCREENSHOT",
};

class KeyboardController {
  constructor(udid = null) {
    this.udid = udid;
  }

  typeText(text, delaySec = 0) {
    if (delaySec > 0) {
      for (const char of text) {
        if (!this._typeSingle(char)) return false;
        const end = Date.now() + delaySec * 1000;
        while (Date.now() < end) { }
      }
      return true;
    }
    return this._typeSingle(text);
  }

  _typeSingle(text) {
    const cmd = ["ui", "text", text];
    if (this.udid) cmd.push("--udid", this.udid);
    try { execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] }); return true; }
    catch { return false; }
  }

  pressKey(key, count = 1) {
    let keyCode = SPECIAL_KEYS[key.toLowerCase()];
    if (keyCode === undefined) {
      keyCode = parseInt(key, 10);
      if (isNaN(keyCode)) return false;
    }
    const cmd = ["ui", "key", String(keyCode)];
    if (this.udid) cmd.push("--udid", this.udid);
    try {
      for (let i = 0; i < count; i++) {
        execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] });
        if (count > 1) { const end = Date.now() + 100; while (Date.now() < end) { } }
      }
      return true;
    } catch { return false; }
  }

  pressKeySequence(keys) {
    const mapped = keys.map((k) => {
      const code = SPECIAL_KEYS[k.toLowerCase()];
      if (code !== undefined) return String(code);
      const num = parseInt(k, 10);
      if (!isNaN(num)) return String(num);
      return null;
    });
    if (mapped.some((m) => m === null)) return false;
    const cmd = ["ui", "key-sequence", ...mapped];
    if (this.udid) cmd.push("--udid", this.udid);
    try { execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] }); return true; }
    catch { return false; }
  }

  pressHardwareButton(button) {
    const buttonCode = HARDWARE_BUTTONS[button.toLowerCase()];
    if (!buttonCode) return false;
    const cmd = ["ui", "button", buttonCode];
    if (this.udid) cmd.push("--udid", this.udid);
    try { execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] }); return true; }
    catch { return false; }
  }

  clearText(selectAll = true) {
    if (selectAll) {
      const ok = this.pressKeySequence(["command", "a"]);
      if (ok) return this.pressKey("delete");
    }
    return this.pressKey("delete", 50);
  }

  pressKeyCombo(keys) {
    const lower = keys.map((k) => k.toLowerCase());
    if (lower.includes("cmd") || lower.includes("command")) {
      if (lower.includes("a")) return this.pressKeySequence(["command", "a"]);
      if (lower.includes("c")) return this.pressKeySequence(["command", "c"]);
      if (lower.includes("v")) return this.pressKeySequence(["command", "v"]);
      if (lower.includes("x")) return this.pressKeySequence(["command", "x"]);
    }
    return this.pressKeySequence(keys);
  }

  dismissKeyboard() {
    return this.pressKey("return");
  }
}

function parseArgs() {
  const args = { type: null, slow: false, key: null, keySequence: null, count: 1, button: null, clear: false, dismiss: false, udid: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--type": args.type = argv[++i]; break;
      case "--slow": args.slow = true; break;
      case "--key": args.key = argv[++i]; break;
      case "--key-sequence": args.keySequence = argv[++i]; break;
      case "--count": args.count = parseInt(argv[++i], 10); break;
      case "--button": args.button = argv[++i]; break;
      case "--clear": args.clear = true; break;
      case "--dismiss": args.dismiss = true; break;
      case "--udid": args.udid = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node keyboard.js [--type TEXT] [--key KEY] [--button BTN] [--clear] [--dismiss] [--udid UDID]");
        process.exit(0);
    }
  }
  return args;
}

function main() {
  const args = parseArgs();
  let udid;
  try { udid = resolveUdid(args.udid); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const ctrl = new KeyboardController(udid);

  if (args.type) {
    const delay = args.slow ? 0.1 : 0;
    if (ctrl.typeText(args.type, delay))
      console.log(`Typed: "${args.type}"${args.slow ? " (slowly)" : ""}`);
    else { console.error("Failed to type text"); process.exit(1); }
  } else if (args.key) {
    if (ctrl.pressKey(args.key, args.count))
      console.log(args.count > 1 ? `Pressed ${args.key} (${args.count}x)` : `Pressed ${args.key}`);
    else { console.error(`Failed to press ${args.key}`); process.exit(1); }
  } else if (args.keySequence) {
    const keys = args.keySequence.split(",");
    if (ctrl.pressKeySequence(keys)) console.log(`Pressed sequence: ${keys.join(" -> ")}`);
    else { console.error("Failed to press key sequence"); process.exit(1); }
  } else if (args.button) {
    if (ctrl.pressHardwareButton(args.button)) console.log(`Pressed ${args.button} button`);
    else { console.error(`Failed to press ${args.button}`); process.exit(1); }
  } else if (args.clear) {
    if (ctrl.clearText()) console.log("Cleared text field");
    else { console.error("Failed to clear text"); process.exit(1); }
  } else if (args.dismiss) {
    if (ctrl.dismissKeyboard()) console.log("Dismissed keyboard");
    else { console.error("Failed to dismiss keyboard"); process.exit(1); }
  } else {
    console.log("Usage: node keyboard.js [--type TEXT] [--key KEY] [--button BTN] [--clear] [--dismiss]");
    process.exit(1);
  }
}

main();
