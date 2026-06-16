#!/usr/bin/env node
/**
 * Delete iOS simulators permanently.
 *
 * Key features:
 * - Delete by UDID or device name
 * - Safety confirmation (--yes to skip)
 * - Batch delete operations (all, by type, old)
 *
 * Usage: node scripts/simctlDelete.js --udid <udid> --yes
 */

const { execFileSync } = require("child_process");
const readline = require("readline");
const { listSimulators, resolveDeviceIdentifier } = require("./common");

function confirm(prompt) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer.toLowerCase() === "yes");
    });
  });
}

function deleteDevice(udid) {
  try {
    execFileSync("xcrun", ["simctl", "delete", udid], {
      encoding: "utf8", stdio: ["pipe", "pipe", "pipe"], timeout: 60000,
    });
    return { success: true, message: `Device deleted: ${udid} [disk space freed]` };
  } catch (e) {
    const stderr = e.stderr ? e.stderr.toString().trim() : e.message;
    return { success: false, message: `Deletion failed: ${stderr}` };
  }
}

async function deleteAll(skipConfirm) {
  const sims = listSimulators(null);
  if (!skipConfirm) {
    const ok = await confirm(`Permanently delete ALL ${sims.length} simulators? (type 'yes' to confirm): `);
    if (!ok) return { succeeded: 0, failed: sims.length };
  }
  let succeeded = 0, failed = 0;
  for (const sim of sims) {
    const { success } = deleteDevice(sim.udid);
    success ? succeeded++ : failed++;
  }
  return { succeeded, failed };
}

async function deleteByType(deviceType, skipConfirm) {
  const sims = listSimulators(null).filter((s) => s.name.toLowerCase().includes(deviceType.toLowerCase()));
  if (!sims.length) return { succeeded: 0, failed: 0 };
  if (!skipConfirm) {
    const ok = await confirm(`Permanently delete ${sims.length} ${deviceType} simulators? (type 'yes' to confirm): `);
    if (!ok) return { succeeded: 0, failed: sims.length };
  }
  let succeeded = 0, failed = 0;
  for (const sim of sims) {
    const { success } = deleteDevice(sim.udid);
    success ? succeeded++ : failed++;
  }
  return { succeeded, failed };
}

async function deleteOld(keepCount, skipConfirm) {
  const sims = listSimulators(null);
  const byType = {};
  for (const sim of sims) {
    if (!byType[sim.type]) byType[sim.type] = [];
    byType[sim.type].push(sim);
  }
  const toDelete = [];
  for (const typeSims of Object.values(byType)) {
    typeSims.sort((a, b) => b.runtime.localeCompare(a.runtime));
    toDelete.push(...typeSims.slice(keepCount));
  }
  if (!toDelete.length) return { succeeded: 0, failed: 0 };
  if (!skipConfirm) {
    const ok = await confirm(`Delete ${toDelete.length} older simulators, keeping ${keepCount} per type? (type 'yes' to confirm): `);
    if (!ok) return { succeeded: 0, failed: toDelete.length };
  }
  let succeeded = 0, failed = 0;
  for (const sim of toDelete) {
    const { success } = deleteDevice(sim.udid);
    success ? succeeded++ : failed++;
  }
  return { succeeded, failed };
}

function parseArgs() {
  const args = { udid: null, name: null, yes: false, all: false, type: null, old: null, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--udid": args.udid = argv[++i]; break;
      case "--name": args.name = argv[++i]; break;
      case "--yes": args.yes = true; break;
      case "--all": args.all = true; break;
      case "--type": args.type = argv[++i]; break;
      case "--old": args.old = parseInt(argv[++i], 10); break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node simctlDelete.js [--udid ID | --name NAME | --all | --type TYPE | --old N] [--yes] [--json]");
        process.exit(0);
    }
  }
  return args;
}

async function main() {
  const args = parseArgs();

  const outputBatch = (action, extra, { succeeded, failed }) => {
    const total = succeeded + failed;
    if (args.json) console.log(JSON.stringify({ action, ...extra, succeeded, failed, total }));
    else console.log(`Delete summary: ${succeeded}/${total} succeeded, ${failed} failed`);
    process.exit(failed === 0 ? 0 : 1);
  };

  if (args.all) return outputBatch("delete_all", {}, await deleteAll(args.yes));
  if (args.type) return outputBatch("delete_by_type", { type: args.type }, await deleteByType(args.type, args.yes));
  if (args.old !== null) return outputBatch("delete_old", { keepCount: args.old }, await deleteOld(args.old, args.yes));

  const deviceId = args.udid || args.name;
  if (!deviceId) { console.error("Error: Specify --udid, --name, --all, --type, or --old"); process.exit(1); }

  let udid;
  try { udid = resolveDeviceIdentifier(deviceId); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  if (!args.yes) {
    const ok = await confirm(`Permanently delete simulator ${udid}? (type 'yes' to confirm): `);
    if (!ok) { console.log("Deletion cancelled"); process.exit(0); }
  }

  const { success, message } = deleteDevice(udid);
  if (args.json) console.log(JSON.stringify({ action: "delete", deviceId, udid, success, message }));
  else console.log(message);
  process.exit(success ? 0 : 1);
}

main();
