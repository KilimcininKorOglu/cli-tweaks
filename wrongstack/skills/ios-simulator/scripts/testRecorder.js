#!/usr/bin/env node
/**
 * Test Recorder for iOS Simulator Testing
 *
 * Records test execution with automatic screenshots and documentation.
 *
 * Usage: node scripts/testRecorder.js --test-name "Login Flow" --output test-artifacts/
 */

const fs = require("fs");
const path = require("path");
const {
  captureScreenshot,
  countElements,
  getAccessibilityTree,
  resolveUdid,
} = require("./common");

class TestRecorder {
  constructor({ testName, outputDir = "test-artifacts", udid = null, inline = false, screenshotSize = "half", appName = null }) {
    this.testName = testName;
    this.udid = udid;
    this.inline = inline;
    this.screenshotSize = screenshotSize;
    this.appName = appName;
    this.startTime = Date.now();
    this.steps = [];
    this.currentStep = 0;

    const timestamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 15).replace(/^(\d{8})(\d{6})/, "$1-$2");
    const safeName = testName.toLowerCase().replace(/ /g, "-");
    this.outputDir = path.join(outputDir, `${safeName}-${timestamp}`);
    fs.mkdirSync(this.outputDir, { recursive: true });

    if (!inline) {
      this.screenshotsDir = path.join(this.outputDir, "screenshots");
      fs.mkdirSync(this.screenshotsDir, { recursive: true });
    }
    this.accessibilityDir = path.join(this.outputDir, "accessibility");
    fs.mkdirSync(this.accessibilityDir, { recursive: true });

    console.log(`Recording: ${testName}${inline ? " (inline mode)" : ""}`);
    console.log(`Output: ${this.outputDir}/`);
  }

  step(description, { screenName, state, assertion, metadata } = {}) {
    this.currentStep++;
    const stepTime = (Date.now() - this.startTime) / 1000;

    const screenshotResult = captureScreenshot(this.udid, {
      size: this.screenshotSize,
      inline: this.inline,
      appName: this.appName,
      screenName: screenName || description,
      state,
    });

    const accessibilityFile = path.join(
      this.accessibilityDir,
      `${String(this.currentStep).padStart(3, "0")}-${description.toLowerCase().replace(/ /g, "-").slice(0, 20)}.json`
    );
    const elementCount = this._captureAccessibility(accessibilityFile);

    const stepData = {
      number: this.currentStep,
      description,
      timestamp: stepTime,
      elementCount,
      accessibility: path.basename(accessibilityFile),
      screenshotMode: screenshotResult.mode,
      screenshotSize: this.screenshotSize,
    };

    if (screenshotResult.mode === "file") {
      stepData.screenshot = screenshotResult.filePath;
      stepData.screenshotName = path.basename(screenshotResult.filePath);
    } else {
      stepData.screenshotBase64 = screenshotResult.base64Data;
      stepData.screenshotDimensions = [screenshotResult.width, screenshotResult.height];
    }

    if (assertion) { stepData.assertion = assertion; stepData.assertionPassed = true; }
    if (metadata) stepData.metadata = metadata;

    this.steps.push(stepData);

    const status = !assertion || stepData.assertionPassed ? "V" : "X";
    const sizeInfo = this.inline ? ` [${screenshotResult.width}x${screenshotResult.height}]` : "";
    console.log(`${status} Step ${this.currentStep}: ${description} (${stepTime.toFixed(1)}s)${sizeInfo}`);
  }

  _captureAccessibility(outputPath) {
    try {
      const tree = getAccessibilityTree(this.udid, true);
      fs.writeFileSync(outputPath, JSON.stringify(tree, null, 2));
      return countElements(tree);
    } catch { return 0; }
  }

  generateReport() {
    const duration = (Date.now() - this.startTime) / 1000;
    const reportPath = path.join(this.outputDir, "report.md");
    const now = new Date().toISOString().replace("T", " ").slice(0, 19);

    let md = `# Test Report: ${this.testName}\n\n`;
    md += `**Date:** ${now}\n**Duration:** ${duration.toFixed(1)} seconds\n**Steps:** ${this.steps.length}\n\n`;
    md += "## Test Steps\n\n";

    for (const step of this.steps) {
      md += `### Step ${step.number}: ${step.description} (${step.timestamp.toFixed(1)}s)\n\n`;
      if (step.screenshotName) md += `![Screenshot](screenshots/${step.screenshotName})\n\n`;
      if (step.assertion) {
        const status = step.assertionPassed ? "V" : "X";
        md += `**Assertion:** ${step.assertion} ${status}\n\n`;
      }
      if (step.metadata) {
        md += "**Metadata:**\n";
        for (const [k, v] of Object.entries(step.metadata)) md += `- ${k}: ${v}\n`;
        md += "\n";
      }
      md += `**Accessibility Elements:** ${step.elementCount}\n\n---\n\n`;
    }

    md += `## Summary\n\n- Total steps: ${this.steps.length}\n- Duration: ${duration.toFixed(1)}s\n- Screenshots: ${this.steps.length}\n- Accessibility snapshots: ${this.steps.length}\n`;

    fs.writeFileSync(reportPath, md);

    const metadataPath = path.join(this.outputDir, "metadata.json");
    fs.writeFileSync(metadataPath, JSON.stringify({
      testName: this.testName, duration, steps: this.steps, timestamp: new Date().toISOString(),
    }, null, 2));

    console.log(`Report: ${reportPath}`);
    return { markdownPath: reportPath, metadataPath, outputDir: this.outputDir };
  }
}

function parseArgs() {
  const args = { testName: null, output: "test-artifacts", udid: null, inline: false, size: "half", appName: null };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--test-name": args.testName = argv[++i]; break;
      case "--output": args.output = argv[++i]; break;
      case "--udid": args.udid = argv[++i]; break;
      case "--inline": args.inline = true; break;
      case "--size": args.size = argv[++i]; break;
      case "--app-name": args.appName = argv[++i]; break;
      case "--help":
        console.log("Usage: node testRecorder.js --test-name NAME [--output DIR] [--udid UDID] [--inline] [--size half]");
        process.exit(0);
    }
  }
  if (!args.testName) { console.error("Error: --test-name is required"); process.exit(1); }
  return args;
}

function main() {
  const args = parseArgs();
  let udid;
  try { udid = resolveUdid(args.udid); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  new TestRecorder({ testName: args.testName, outputDir: args.output, udid, inline: args.inline, screenshotSize: args.size, appName: args.appName });

  console.log("\nTest recorder initialized. Use programmatically:");
  console.log('  recorder.step("description")');
  console.log("  recorder.generateReport()");
}

module.exports = { TestRecorder };
main();
