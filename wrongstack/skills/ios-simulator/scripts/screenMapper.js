#!/usr/bin/env node
/**
 * iOS Screen Mapper - Current Screen Analyzer
 *
 * Maps the current screen's UI elements for navigation decisions.
 * Token-efficient summaries (5-7 lines default).
 *
 * Usage: node scripts/screenMapper.js [--verbose] [--hints] [--json] [--udid UDID]
 */

const { getAccessibilityTree, resolveUdid } = require("./common");

const INTERACTIVE_TYPES = new Set([
  "Button", "Link", "TextField", "SecureTextField", "Cell",
  "Switch", "Slider", "Stepper", "SegmentedControl", "TabBar",
  "NavigationBar", "Toolbar",
]);

class ScreenMapper {
  constructor(udid = null) {
    this.udid = udid;
  }

  analyzeTree(node, depth = 0) {
    const analysis = {
      elementsByType: {},
      totalElements: 0,
      interactiveElements: 0,
      textFields: [],
      buttons: [],
      navigation: {},
      screenName: null,
      focusable: 0,
    };
    this._analyzeRecursive(node, analysis, depth);
    return analysis;
  }

  _analyzeRecursive(node, analysis, depth) {
    const elemType = node.type;
    const label = node.AXLabel || "";
    const value = node.AXValue || "";
    const identifier = node.AXUniqueId || "";

    if (elemType) {
      analysis.totalElements++;

      if (INTERACTIVE_TYPES.has(elemType)) {
        analysis.interactiveElements++;
        const elemInfo = label || value || identifier || "Unnamed";

        if (!analysis.elementsByType[elemType]) analysis.elementsByType[elemType] = [];
        analysis.elementsByType[elemType].push(elemInfo);

        if (elemType === "Button") analysis.buttons.push(elemInfo);
        else if (elemType === "TextField" || elemType === "SecureTextField") {
          analysis.textFields.push({ type: elemType, label: elemInfo, hasValue: !!value });
        } else if (elemType === "NavigationBar") {
          analysis.navigation.navTitle = label || "Navigation";
        } else if (elemType === "TabBar") {
          analysis.navigation.tabCount = (node.children || []).length;
        }

        if (node.enabled) analysis.focusable++;
      }
    }

    if (!analysis.screenName && identifier) {
      if (identifier.includes("ViewController") || identifier.includes("Screen")) {
        analysis.screenName = identifier;
      }
    }

    for (const child of node.children || []) {
      this._analyzeRecursive(child, analysis, depth + 1);
    }
  }

  formatSummary(analysis, verbose = false) {
    const lines = [];
    const screen = analysis.screenName || "Unknown Screen";
    lines.push(`Screen: ${screen} (${analysis.totalElements} elements, ${analysis.interactiveElements} interactive)`);

    if (analysis.buttons.length) {
      let btnList = analysis.buttons.slice(0, 5).map((b) => `"${b}"`).join(", ");
      if (analysis.buttons.length > 5) btnList += ` +${analysis.buttons.length - 5} more`;
      lines.push(`Buttons: ${btnList}`);
    }

    if (analysis.textFields.length) {
      const filled = analysis.textFields.filter((f) => f.hasValue).length;
      lines.push(`TextFields: ${analysis.textFields.length} (${filled} filled)`);
    }

    const navParts = [];
    if (analysis.navigation.navTitle) navParts.push(`NavBar: "${analysis.navigation.navTitle}"`);
    if (analysis.navigation.tabCount) navParts.push(`TabBar: ${analysis.navigation.tabCount} tabs`);
    if (navParts.length) lines.push(`Navigation: ${navParts.join(", ")}`);

    lines.push(`Focusable: ${analysis.focusable} elements`);

    if (verbose) {
      lines.push("\nElements by type:");
      for (const [type, items] of Object.entries(analysis.elementsByType)) {
        if (items.length) {
          lines.push(`  ${type}: ${items.length}`);
          items.slice(0, 3).forEach((item) => lines.push(`    - ${item}`));
          if (items.length > 3) lines.push(`    ... +${items.length - 3} more`);
        }
      }
    }
    return lines.join("\n");
  }

  getNavigationHints(analysis) {
    const hints = [];
    if (analysis.buttons.some((b) => b.toLowerCase().includes("login")))
      hints.push("Login screen detected - find TextFields for credentials");
    const unfilled = analysis.textFields.filter((f) => !f.hasValue);
    if (unfilled.length) hints.push(`${unfilled.length} empty text field(s) - may need input`);
    if (!analysis.buttons.length && !analysis.textFields.length)
      hints.push("No interactive elements - try swiping or going back");
    if (analysis.navigation.tabCount)
      hints.push(`Tab bar available with ${analysis.navigation.tabCount} tabs`);
    return hints;
  }
}

function parseArgs() {
  const args = { verbose: false, json: false, hints: false, udid: null };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--verbose": args.verbose = true; break;
      case "--json": args.json = true; break;
      case "--hints": args.hints = true; break;
      case "--udid": args.udid = argv[++i]; break;
      case "--help":
        console.log("Usage: node screenMapper.js [--verbose] [--hints] [--json] [--udid UDID]");
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

  const mapper = new ScreenMapper(udid);
  const tree = getAccessibilityTree(udid, true);
  const analysis = mapper.analyzeTree(tree);

  if (args.json) {
    console.log(JSON.stringify(analysis, null, 2));
  } else {
    console.log(mapper.formatSummary(analysis, args.verbose));
    if (args.hints) {
      const hints = mapper.getNavigationHints(analysis);
      if (hints.length) {
        console.log("\nHints:");
        hints.forEach((h) => console.log(`  - ${h}`));
      }
    }
  }
}

main();
