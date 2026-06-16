#!/usr/bin/env node
/**
 * Visual Diff Tool for iOS Simulator Screenshots
 *
 * Compares two screenshots pixel-by-pixel to detect visual changes.
 * Uses macOS sips for image processing (no Pillow/sharp dependency).
 * For full diff image generation, requires optional `sharp` npm package.
 *
 * Usage: node scripts/visualDiff.js baseline.png current.png [--threshold 0.01]
 *
 * NOTE: This script performs basic dimension + byte-level comparison.
 * For pixel-level diff image generation, the Python version with Pillow
 * provides richer output. This JS version focuses on pass/fail detection.
 */

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function getImageDimensions(filePath) {
  try {
    const output = execFileSync("sips", ["-g", "pixelWidth", "-g", "pixelHeight", filePath], {
      encoding: "utf8", stdio: ["pipe", "pipe", "pipe"],
    });
    const wMatch = output.match(/pixelWidth:\s*(\d+)/);
    const hMatch = output.match(/pixelHeight:\s*(\d+)/);
    return {
      width: wMatch ? parseInt(wMatch[1], 10) : 0,
      height: hMatch ? parseInt(hMatch[1], 10) : 0,
    };
  } catch { return { width: 0, height: 0 }; }
}

function compare(baselinePath, currentPath, threshold = 0.01) {
  if (!fs.existsSync(baselinePath)) { console.error(`Error: Baseline not found: ${baselinePath}`); process.exit(1); }
  if (!fs.existsSync(currentPath)) { console.error(`Error: Current not found: ${currentPath}`); process.exit(1); }

  const baselineDims = getImageDimensions(baselinePath);
  const currentDims = getImageDimensions(currentPath);

  if (baselineDims.width !== currentDims.width || baselineDims.height !== currentDims.height) {
    return {
      error: "Image dimensions do not match",
      baselineSize: [baselineDims.width, baselineDims.height],
      currentSize: [currentDims.width, currentDims.height],
    };
  }

  // Byte-level comparison for basic diff detection
  const baselineData = fs.readFileSync(baselinePath);
  const currentData = fs.readFileSync(currentPath);

  let diffBytes = 0;
  const minLen = Math.min(baselineData.length, currentData.length);
  for (let i = 0; i < minLen; i++) {
    if (baselineData[i] !== currentData[i]) diffBytes++;
  }
  diffBytes += Math.abs(baselineData.length - currentData.length);

  const totalPixels = baselineDims.width * baselineDims.height;
  // Approximate: each pixel ~4 bytes (RGBA), diff bytes / 4 ≈ changed pixels
  const approxDiffPixels = Math.round(diffBytes / 4);
  const diffPercentage = totalPixels > 0 ? (approxDiffPixels / totalPixels) * 100 : 0;
  const passed = diffPercentage <= threshold * 100;

  return {
    dimensions: [baselineDims.width, baselineDims.height],
    totalPixels,
    differentPixels: approxDiffPixels,
    differencePercentage: Math.round(diffPercentage * 100) / 100,
    thresholdPercentage: threshold * 100,
    passed,
    verdict: passed ? "PASS" : "FAIL",
  };
}

function parseArgs() {
  const args = { baseline: null, current: null, output: ".", threshold: 0.01, details: false, json: false };
  const argv = process.argv.slice(2);
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--output": args.output = argv[++i]; break;
      case "--threshold": args.threshold = parseFloat(argv[++i]); break;
      case "--details": args.details = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node visualDiff.js <baseline.png> <current.png> [--threshold 0.01] [--output DIR] [--details]");
        process.exit(0);
        break;
      default:
        if (!argv[i].startsWith("--")) positional.push(argv[i]);
    }
  }
  if (positional.length >= 2) { args.baseline = positional[0]; args.current = positional[1]; }
  if (!args.baseline || !args.current) {
    console.error("Error: Two image paths required (baseline and current)");
    process.exit(1);
  }
  return args;
}

function main() {
  const args = parseArgs();
  fs.mkdirSync(args.output, { recursive: true });

  const result = compare(args.baseline, args.current, args.threshold);

  if (result.error) {
    console.error(`Error: ${result.error}`);
    console.error(`Baseline: ${result.baselineSize}`);
    console.error(`Current: ${result.currentSize}`);
    process.exit(1);
  }

  // Save JSON report
  const reportPath = path.join(args.output, "diff-report.json");
  fs.writeFileSync(reportPath, JSON.stringify({
    baseline: path.basename(args.baseline),
    current: path.basename(args.current),
    results: result,
  }, null, 2));

  if (args.details || args.json) {
    console.log(JSON.stringify({
      summary: { baseline: args.baseline, current: args.current, threshold: args.threshold, passed: result.passed },
      results: result,
      artifacts: { report: reportPath },
    }, null, 2));
  } else {
    console.log(`Difference: ${result.differencePercentage}% (${result.verdict})`);
    if (result.differentPixels > 0) console.log(`Changed pixels: ~${result.differentPixels.toLocaleString()}`);
    console.log(`Report saved to: ${reportPath}`);
  }

  process.exit(result.passed ? 0 : 1);
}

main();
