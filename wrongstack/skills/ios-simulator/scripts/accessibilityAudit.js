#!/usr/bin/env node
/**
 * iOS Simulator Accessibility Audit
 *
 * Scans the current simulator screen for accessibility compliance issues.
 * Token-optimized output.
 *
 * Usage: node scripts/accessibilityAudit.js [--verbose] [--output FILE] [--udid UDID]
 */

const fs = require("fs");
const { flattenTree, getAccessibilityTree, resolveUdid } = require("./common");

const CRITICAL_RULES = {
  missingLabel: (e) => ["Button", "Link"].includes(e.type) && !e.AXLabel,
  emptyButton: (e) => e.type === "Button" && !e.AXLabel && !e.AXValue,
  imageNoAlt: (e) => e.type === "Image" && !e.AXLabel,
};

const WARNING_RULES = {
  missingHint: (e) => ["Slider", "TextField"].includes(e.type) && !e.help,
  missingTraits: (e) => e.type && !e.traits,
};

const INFO_RULES = {
  noIdentifier: (e) => !e.AXUniqueId,
  deepNesting: (e) => (e.depth || 0) > 5,
};

const DESCRIPTIONS = {
  missingLabel: "Interactive element missing accessibility label",
  emptyButton: "Button has no text or label",
  imageNoAlt: "Image missing alternative text",
  missingHint: "Complex control missing hint",
  missingTraits: "Element missing accessibility traits",
  noIdentifier: "Missing accessibility identifier",
  deepNesting: "Deeply nested (>5 levels)",
};

const FIXES = {
  missingLabel: "Add accessibilityLabel",
  emptyButton: "Set button title or accessibilityLabel",
  imageNoAlt: "Add accessibilityLabel with description",
  missingHint: "Add accessibilityHint",
  missingTraits: "Set appropriate accessibilityTraits",
  noIdentifier: "Add accessibilityIdentifier for testing",
  deepNesting: "Simplify view hierarchy",
};

function auditElement(element) {
  const issues = [];

  for (const [rule, fn] of Object.entries(CRITICAL_RULES)) {
    if (fn(element)) {
      issues.push({ severity: "critical", rule, elementType: element.type || "Unknown", issue: DESCRIPTIONS[rule], fix: FIXES[rule] });
    }
  }

  if (!issues.length) {
    for (const [rule, fn] of Object.entries(WARNING_RULES)) {
      if (fn(element)) {
        issues.push({ severity: "warning", rule, elementType: element.type || "Unknown", issue: DESCRIPTIONS[rule], fix: FIXES[rule] });
      }
    }
  }

  if (!issues.length) {
    for (const [rule, fn] of Object.entries(INFO_RULES)) {
      if (fn(element)) {
        issues.push({ severity: "info", rule, elementType: element.type || "Unknown", issue: DESCRIPTIONS[rule], fix: FIXES[rule] });
      }
    }
  }

  return issues;
}

function audit(udid, verbose = false) {
  const tree = getAccessibilityTree(udid, true);
  const elements = flattenTree(tree);

  const allIssues = [];
  for (const element of elements) {
    for (const issue of auditElement(element)) {
      allIssues.push({
        ...issue,
        element: {
          type: element.type || "Unknown",
          label: element.AXLabel ? element.AXLabel.slice(0, 30) : null,
        },
      });
    }
  }

  const critical = allIssues.filter((i) => i.severity === "critical").length;
  const warning = allIssues.filter((i) => i.severity === "warning").length;
  const info = allIssues.filter((i) => i.severity === "info").length;

  const result = {
    summary: { total: elements.length, issues: allIssues.length, critical, warning, info },
  };

  if (verbose) {
    result.issues = allIssues;
  } else {
    // Top 3 issues grouped by rule
    const grouped = {};
    for (const issue of allIssues) {
      if (!grouped[issue.rule]) {
        grouped[issue.rule] = { severity: issue.severity, rule: issue.rule, count: 0, fix: issue.fix };
      }
      grouped[issue.rule].count++;
    }
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    result.topIssues = Object.values(grouped)
      .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity] || b.count - a.count)
      .slice(0, 3);
  }

  return result;
}

function parseArgs() {
  const args = { udid: null, output: null, verbose: false, json: false };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--udid": args.udid = argv[++i]; break;
      case "--output": args.output = argv[++i]; break;
      case "--verbose": args.verbose = true; break;
      case "--json": args.json = true; break;
      case "--help":
        console.log("Usage: node accessibilityAudit.js [--verbose] [--output FILE] [--udid UDID]");
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

  let result;
  try { result = audit(udid, args.verbose); }
  catch (e) { console.error(`Error: ${e.message}`); process.exit(1); }

  if (args.output) {
    fs.writeFileSync(args.output, JSON.stringify(result, null, 2));
    const s = result.summary;
    console.log(`Audit complete: ${s.issues} issues (${s.critical} critical)`);
    console.log(`Report saved to: ${args.output}`);
  } else if (args.verbose || args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    const s = result.summary;
    console.log(`Elements: ${s.total}, Issues: ${s.issues}`);
    console.log(`Critical: ${s.critical}, Warning: ${s.warning}, Info: ${s.info}`);
    if (result.topIssues && result.topIssues.length) {
      console.log("\nTop issues:");
      result.topIssues.forEach((i) => console.log(`  [${i.severity}] ${i.rule} (${i.count}x) - ${i.fix}`));
    }
  }

  if (result.summary.critical > 0) process.exit(1);
}

main();
