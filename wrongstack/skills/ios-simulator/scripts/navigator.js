#!/usr/bin/env node
/**
 * iOS Simulator Navigator - Smart Element Finder and Interactor
 *
 * Finds and interacts with UI elements using accessibility data.
 * Semantic navigation instead of fragile pixel coordinates.
 *
 * Usage:
 *   node scripts/navigator.js --find-text "Login" --tap
 *   node scripts/navigator.js --find-type TextField --enter-text "user@test.com"
 *   node scripts/navigator.js --find-id "submitButton" --tap
 */

const { execFileSync } = require("child_process");
const {
  getAccessibilityTree,
  getDeviceScreenSize,
  resolveUdid,
  transformScreenshotCoords,
} = require("./common");

class Element {
  constructor({ type, label, value, identifier, frame, traits, enabled }) {
    this.type = type || "Unknown";
    this.label = label || null;
    this.value = value || null;
    this.identifier = identifier || null;
    this.frame = frame || {};
    this.traits = traits || [];
    this.enabled = enabled !== false;
  }

  get center() {
    const x = Math.round((this.frame.x || 0) + (this.frame.width || 0) / 2);
    const y = Math.round((this.frame.y || 0) + (this.frame.height || 0) / 2);
    return { x, y };
  }

  get description() {
    const lbl = this.label || this.value || this.identifier || "Unnamed";
    return `${this.type} "${lbl}"`;
  }
}

class Navigator {
  constructor(udid = null) {
    this.udid = udid;
    this._treeCache = null;
  }

  getTree(forceRefresh = false) {
    if (this._treeCache && !forceRefresh) return this._treeCache;
    this._treeCache = getAccessibilityTree(this.udid, true);
    return this._treeCache;
  }

  _flattenTree(node, elements = []) {
    if (node.type) {
      elements.push(new Element({
        type: node.type,
        label: node.AXLabel,
        value: node.AXValue,
        identifier: node.AXUniqueId,
        frame: node.frame,
        traits: node.traits,
        enabled: node.enabled,
      }));
    }
    for (const child of node.children || []) {
      this._flattenTree(child, elements);
    }
    return elements;
  }

  listElements(forceRefresh = false) {
    return this._flattenTree(this.getTree(forceRefresh));
  }

  findElement({ text, elementType, identifier, index = 0, fuzzy = true } = {}) {
    const elements = this._flattenTree(this.getTree());
    const matches = [];

    for (const elem of elements) {
      if (!elem.enabled) continue;
      if (elementType && elem.type !== elementType) continue;
      if (identifier && elem.identifier !== identifier) continue;
      if (text) {
        const elemText = `${elem.label || ""} ${elem.value || ""}`;
        if (fuzzy) { if (!elemText.toLowerCase().includes(text.toLowerCase())) continue; }
        else if (elem.label !== text && elem.value !== text) continue;
      }
      matches.push(elem);
    }
    return matches.length > index ? matches[index] : null;
  }

  tap(element) {
    const { x, y } = element.center;
    return this.tapAt(x, y);
  }

  tapAt(x, y) {
    const cmd = ["ui", "tap", String(x), String(y)];
    if (this.udid) cmd.push("--udid", this.udid);
    try {
      execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] });
      return true;
    } catch { return false; }
  }

  enterText(text, element = null) {
    if (element) {
      if (!this.tap(element)) return false;
      const end = Date.now() + 500;
      while (Date.now() < end) { /* wait for focus */ }
    }
    const cmd = ["ui", "text", text];
    if (this.udid) cmd.push("--udid", this.udid);
    try {
      execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] });
      return true;
    } catch { return false; }
  }

  findAndTap({ text, elementType, identifier, index = 0 } = {}) {
    const element = this.findElement({ text, elementType, identifier, index });
    if (!element) {
      const criteria = [];
      if (text) criteria.push(`text='${text}'`);
      if (elementType) criteria.push(`type=${elementType}`);
      if (identifier) criteria.push(`id=${identifier}`);
      return { success: false, message: `Not found: ${criteria.join(", ")}` };
    }
    if (this.tap(element)) {
      const { x, y } = element.center;
      return { success: true, message: `Tapped: ${element.description} at (${x}, ${y})` };
    }
    return { success: false, message: `Failed to tap: ${element.description}` };
  }

  findAndEnterText({ textToEnter, findText, elementType = "TextField", identifier, index = 0 } = {}) {
    const element = this.findElement({ text: findText, elementType, identifier, index });
    if (!element) return { success: false, message: "TextField not found" };
    if (this.enterText(textToEnter, element))
      return { success: true, message: `Entered text in: ${element.description}` };
    return { success: false, message: "Failed to enter text" };
  }
}

function parseArgs() {
  const args = { findText: null, findExact: null, findType: null, findId: null, index: 0, tap: false, tapAt: null, enterText: null, screenshotCoords: false, screenshotWidth: null, screenshotHeight: null, udid: null, list: false, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--find-text": args.findText = argv[++i]; break;
      case "--find-exact": args.findExact = argv[++i]; break;
      case "--find-type": args.findType = argv[++i]; break;
      case "--find-id": args.findId = argv[++i]; break;
      case "--index": args.index = parseInt(argv[++i], 10); break;
      case "--tap": args.tap = true; break;
      case "--tap-at": args.tapAt = argv[++i]; break;
      case "--enter-text": args.enterText = argv[++i]; break;
      case "--screenshot-coords": args.screenshotCoords = true; break;
      case "--screenshot-width": args.screenshotWidth = parseInt(argv[++i], 10); break;
      case "--screenshot-height": args.screenshotHeight = parseInt(argv[++i], 10); break;
      case "--udid": args.udid = argv[++i]; break;
      case "--list": args.list = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node navigator.js [--find-text|--find-type|--find-id] [--tap|--enter-text] [--tap-at x,y] [--list] [--udid UDID]");
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

  const nav = new Navigator(udid);

  if (args.list) {
    const elements = nav.listElements();
    const tappable = elements.filter((e) => e.enabled && ["Button", "Link", "Cell", "TextField", "SecureTextField"].includes(e.type));
    console.log(`Tappable elements (${tappable.length}):`);
    tappable.slice(0, 10).forEach((e) => {
      const { x, y } = e.center;
      console.log(`  ${e.type}: "${e.label || e.value || "Unnamed"}" (${x}, ${y})`);
    });
    if (tappable.length > 10) console.log(`  ... and ${tappable.length - 10} more`);
    process.exit(0);
  }

  if (args.tapAt) {
    const [rawX, rawY] = args.tapAt.split(",").map(Number);
    let x = rawX, y = rawY;
    if (args.screenshotCoords) {
      if (!args.screenshotWidth || !args.screenshotHeight) {
        console.error("Error: --screenshot-coords requires --screenshot-width and --screenshot-height");
        process.exit(1);
      }
      const deviceSize = getDeviceScreenSize(udid);
      const transformed = transformScreenshotCoords(x, y, args.screenshotWidth, args.screenshotHeight, deviceSize.width, deviceSize.height);
      x = transformed.x; y = transformed.y;
      console.log(`Transformed screenshot coords (${rawX}, ${rawY}) to device coords (${x}, ${y})`);
    }
    if (nav.tapAt(x, y)) console.log(`Tapped at (${x}, ${y})`);
    else { console.error(`Failed to tap at (${x}, ${y})`); process.exit(1); }
  } else if (args.tap) {
    const text = args.findText || args.findExact;
    const { success, message } = nav.findAndTap({ text, elementType: args.findType, identifier: args.findId, index: args.index });
    console.log(message);
    if (!success) process.exit(1);
  } else if (args.enterText) {
    const text = args.findText || args.findExact;
    const { success, message } = nav.findAndEnterText({
      textToEnter: args.enterText, findText: text, elementType: args.findType || "TextField", identifier: args.findId, index: args.index,
    });
    console.log(message);
    if (!success) process.exit(1);
  } else {
    const text = args.findText || args.findExact;
    const fuzzy = !!args.findText;
    const element = nav.findElement({ text, elementType: args.findType, identifier: args.findId, index: args.index, fuzzy });
    if (element) {
      const { x, y } = element.center;
      console.log(`Found: ${element.description} at (${x}, ${y})`);
    } else { console.log("Element not found"); process.exit(1); }
  }
}

main();
