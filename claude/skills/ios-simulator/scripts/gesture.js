#!/usr/bin/env node
/**
 * iOS Gesture Controller - Swipes and Complex Gestures
 *
 * Directional swipes, scrolls, pinches, pull-to-refresh, long press.
 * Auto-detects screen size from device.
 *
 * Usage: node scripts/gesture.js --swipe up [--udid UDID]
 */

const { execFileSync } = require("child_process");
const { getScreenSize, getDeviceScreenSize, resolveUdid, transformScreenshotCoords } = require("./common");

class GestureController {
  constructor(udid = null) {
    this.udid = udid;
    this.screenSize = getScreenSize(udid);
  }

  swipe(direction, distanceRatio = 0.7) {
    const { width, height } = this.screenSize;
    const cx = Math.round(width / 2), cy = Math.round(height / 2);
    let start, end;

    if (direction === "up") { start = [cx, Math.round(height * 0.7)]; end = [cx, Math.round(height * (1 - distanceRatio + 0.3))]; }
    else if (direction === "down") { start = [cx, Math.round(height * 0.3)]; end = [cx, Math.round(height * (distanceRatio))]; }
    else if (direction === "left") { start = [Math.round(width * 0.8), cy]; end = [Math.round(width * (1 - distanceRatio + 0.2)), cy]; }
    else if (direction === "right") { start = [Math.round(width * 0.2), cy]; end = [Math.round(width * distanceRatio), cy]; }
    else return false;

    return this.swipeBetween(start, end);
  }

  swipeBetween(start, end, durationMs = 300) {
    const cmd = ["ui", "swipe", String(start[0]), String(start[1]), String(end[0]), String(end[1])];
    if (durationMs !== 300) cmd.push("--duration", String(durationMs));
    if (this.udid) cmd.push("--udid", this.udid);
    try { execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] }); return true; }
    catch { return false; }
  }

  scroll(direction, amount = 3) {
    for (let i = 0; i < amount; i++) {
      if (!this.swipe(direction, 0.3)) return false;
      const end = Date.now() + 200; while (Date.now() < end) { }
    }
    return true;
  }

  tapAndHold(x, y, durationSec = 2.0) {
    const cmd = ["ui", "tap", String(x), String(y)];
    if (this.udid) cmd.push("--udid", this.udid);
    try { execFileSync("idb", cmd, { stdio: ["pipe", "pipe", "pipe"] }); }
    catch { return false; }
    const end = Date.now() + durationSec * 1000; while (Date.now() < end) { }
    return true;
  }

  pinch(direction = "out", center = null) {
    if (!center) {
      const { width, height } = this.screenSize;
      center = [Math.round(width / 2), Math.round(height / 2)];
    }
    const offset = direction === "out" ? 100 : 50;
    let s1, e1, s2, e2;
    if (direction === "out") {
      s1 = [center[0] - 20, center[1] - 20]; e1 = [center[0] - offset, center[1] - offset];
      s2 = [center[0] + 20, center[1] + 20]; e2 = [center[0] + offset, center[1] + offset];
    } else {
      s1 = [center[0] - offset, center[1] - offset]; e1 = [center[0] - 20, center[1] - 20];
      s2 = [center[0] + offset, center[1] + offset]; e2 = [center[0] + 20, center[1] + 20];
    }
    return this.swipeBetween(s1, e1) && this.swipeBetween(s2, e2);
  }

  refresh() {
    const { width } = this.screenSize;
    return this.swipeBetween([Math.round(width / 2), 100], [Math.round(width / 2), 400]);
  }
}

function parseArgs() {
  const args = { swipe: null, swipeFrom: null, swipeTo: null, scroll: null, scrollAmount: 3, longPress: null, duration: 2.0, pinch: null, refresh: false, screenshotCoords: false, screenshotWidth: null, screenshotHeight: null, udid: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--swipe": args.swipe = argv[++i]; break;
      case "--swipe-from": args.swipeFrom = argv[++i]; break;
      case "--swipe-to": args.swipeTo = argv[++i]; break;
      case "--scroll": args.scroll = argv[++i]; break;
      case "--scroll-amount": args.scrollAmount = parseInt(argv[++i], 10); break;
      case "--long-press": args.longPress = argv[++i]; break;
      case "--duration": args.duration = parseFloat(argv[++i]); break;
      case "--pinch": args.pinch = argv[++i]; break;
      case "--refresh": args.refresh = true; break;
      case "--screenshot-coords": args.screenshotCoords = true; break;
      case "--screenshot-width": args.screenshotWidth = parseInt(argv[++i], 10); break;
      case "--screenshot-height": args.screenshotHeight = parseInt(argv[++i], 10); break;
      case "--udid": args.udid = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node gesture.js [--swipe DIR] [--scroll DIR] [--long-press x,y] [--pinch in|out] [--refresh] [--udid UDID]");
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

  const ctrl = new GestureController(udid);

  if (args.swipe) {
    if (ctrl.swipe(args.swipe)) console.log(`Swiped ${args.swipe}`);
    else { console.error(`Failed to swipe ${args.swipe}`); process.exit(1); }
  } else if (args.swipeFrom && args.swipeTo) {
    let start = args.swipeFrom.split(",").map(Number);
    let end = args.swipeTo.split(",").map(Number);
    if (args.screenshotCoords && args.screenshotWidth && args.screenshotHeight) {
      const ds = getDeviceScreenSize(udid);
      const t1 = transformScreenshotCoords(start[0], start[1], args.screenshotWidth, args.screenshotHeight, ds.width, ds.height);
      const t2 = transformScreenshotCoords(end[0], end[1], args.screenshotWidth, args.screenshotHeight, ds.width, ds.height);
      start = [t1.x, t1.y]; end = [t2.x, t2.y];
    }
    if (ctrl.swipeBetween(start, end)) console.log(`Swiped from (${start}) to (${end})`);
    else { console.error("Failed to swipe"); process.exit(1); }
  } else if (args.scroll) {
    if (ctrl.scroll(args.scroll, args.scrollAmount)) console.log(`Scrolled ${args.scroll} (${args.scrollAmount}x)`);
    else { console.error(`Failed to scroll ${args.scroll}`); process.exit(1); }
  } else if (args.longPress) {
    const [x, y] = args.longPress.split(",").map(Number);
    if (ctrl.tapAndHold(x, y, args.duration)) console.log(`Long pressed at (${x}, ${y}) for ${args.duration}s`);
    else { console.error("Failed to long press"); process.exit(1); }
  } else if (args.pinch) {
    if (ctrl.pinch(args.pinch)) console.log(args.pinch === "out" ? "Zoomed in" : "Zoomed out");
    else { console.error(`Failed to pinch ${args.pinch}`); process.exit(1); }
  } else if (args.refresh) {
    if (ctrl.refresh()) console.log("Performed pull to refresh");
    else { console.error("Failed to refresh"); process.exit(1); }
  } else {
    console.log("Usage: node gesture.js [--swipe DIR] [--scroll DIR] [--long-press x,y] [--pinch in|out] [--refresh]");
    process.exit(1);
  }
}

main();
