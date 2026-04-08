#!/usr/bin/env node
/**
 * iOS Push Notification Simulator
 *
 * Send simulated push notifications to test notification handling.
 *
 * Usage: node scripts/pushNotification.js --bundle-id com.app --title "Alert" --body "Message"
 */

const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { resolveUdid } = require("./common");

class PushNotificationSender {
  constructor(udid = null) {
    this.udid = udid;
  }

  send(bundleId, payload) {
    let payloadData;

    if (typeof payload === "string") {
      if (fs.existsSync(payload)) {
        payloadData = JSON.parse(fs.readFileSync(payload, "utf8"));
      } else {
        try {
          payloadData = JSON.parse(payload);
        } catch {
          console.error(`Error: Invalid JSON payload: ${payload}`);
          return false;
        }
      }
    } else {
      payloadData = payload;
    }

    if (!payloadData.aps) {
      payloadData = { aps: payloadData };
    }

    const tempPath = path.join(os.tmpdir(), `push_${Date.now()}.json`);
    try {
      fs.writeFileSync(tempPath, JSON.stringify(payloadData));
      execFileSync(
        "xcrun",
        ["simctl", "push", this.udid || "booted", bundleId, tempPath],
        { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }
      );
      fs.unlinkSync(tempPath);
      return true;
    } catch (e) {
      try { fs.unlinkSync(tempPath); } catch { /* ignore */ }
      console.error(`Error sending push notification: ${e.message}`);
      return false;
    }
  }

  sendSimple(bundleId, { title, body, badge, sound = true } = {}) {
    const apsPayload = {};
    if (title || body) {
      const alert = {};
      if (title) alert.title = title;
      if (body) alert.body = body;
      apsPayload.alert = alert;
    }
    if (badge !== null && badge !== undefined) apsPayload.badge = badge;
    if (sound) apsPayload.sound = "default";

    return this.send(bundleId, { aps: apsPayload });
  }
}

function parseArgs() {
  const args = { bundleId: null, title: null, body: null, badge: null, noSound: false, payload: null, testName: null, expected: null, udid: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--bundle-id": args.bundleId = argv[++i]; break;
      case "--title": args.title = argv[++i]; break;
      case "--body": args.body = argv[++i]; break;
      case "--badge": args.badge = parseInt(argv[++i], 10); break;
      case "--no-sound": args.noSound = true; break;
      case "--payload": args.payload = argv[++i]; break;
      case "--test-name": args.testName = argv[++i]; break;
      case "--expected": args.expected = argv[++i]; break;
      case "--udid": args.udid = argv[++i]; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node pushNotification.js --bundle-id <id> [--title TEXT] [--body TEXT] [--badge N] [--payload JSON] [--udid UDID]");
        process.exit(0);
    }
  }
  if (!args.bundleId) { console.error("Error: --bundle-id is required"); process.exit(1); }
  return args;
}

function main() {
  const args = parseArgs();

  let udid;
  try { udid = resolveUdid(args.udid); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  const sender = new PushNotificationSender(udid);
  let success;

  if (args.payload) {
    success = sender.send(args.bundleId, args.payload);
  } else {
    success = sender.sendSimple(args.bundleId, {
      title: args.title,
      body: args.body,
      badge: args.badge,
      sound: !args.noSound,
    });
  }

  if (success) {
    let output = "Push notification sent";
    if (args.testName) output += ` (test: ${args.testName})`;
    console.log(output);

    if (args.expected) console.log(`Expected: ${args.expected}`);

    if (args.title) console.log(`  Title: ${args.title}`);
    if (args.body) console.log(`  Body: ${args.body}`);
    if (args.badge) console.log(`  Badge: ${args.badge}`);

    console.log("\nVerify notification handling:");
    console.log(`1. Check app log: node scripts/logMonitor.js --app ${args.bundleId}`);
    console.log(`2. Capture state: node scripts/appStateCapture.js --app-bundle-id ${args.bundleId}`);
  } else {
    console.error("Failed to send push notification");
    process.exit(1);
  }
}

main();
