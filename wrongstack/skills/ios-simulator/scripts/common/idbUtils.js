#!/usr/bin/env node
/**
 * Shared IDB utility functions.
 *
 * Common IDB operations used across multiple scripts.
 *
 * Used by:
 * - navigator.js - Accessibility tree navigation
 * - screenMapper.js - UI element analysis
 * - accessibilityAudit.js - WCAG compliance checking
 * - testRecorder.js - Test documentation
 * - appStateCapture.js - State snapshots
 * - gesture.js - Touch gesture operations
 */

const { execFileSync } = require("child_process");

/**
 * Fetch accessibility tree from IDB.
 *
 * The accessibility tree represents the complete UI hierarchy of the current
 * screen, with all element properties needed for semantic navigation.
 *
 * @param {string|null} udid - Device UDID (uses booted simulator if null)
 * @param {boolean} nested - Include nested structure (default true)
 * @returns {object} Root element of accessibility tree
 */
function getAccessibilityTree(udid = null, nested = true) {
  const cmd = ["ui", "describe-all", "--json"];
  if (nested) cmd.push("--nested");
  if (udid) cmd.push("--udid", udid);

  try {
    const output = execFileSync("idb", cmd, {
      encoding: "utf8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    const treeData = JSON.parse(output);
    if (Array.isArray(treeData) && treeData.length > 0) {
      return treeData[0];
    }
    return treeData;
  } catch (e) {
    process.stderr.write(
      `Error: Failed to get accessibility tree: ${e.message}\n`
    );
    process.exit(1);
  }
}

/**
 * Flatten nested accessibility tree into list of elements.
 *
 * Converts the hierarchical accessibility tree into a flat list where each
 * element includes its depth for context.
 *
 * @param {object} node - Root node of tree
 * @param {number} depth - Current depth (internal, start at 0)
 * @param {Array|null} elements - Accumulator list (internal)
 * @returns {Array<object>} Flat list of elements with "depth" key
 */
function flattenTree(node, depth = 0, elements = null) {
  if (elements === null) elements = [];

  const nodeCopy = { ...node, depth };
  delete nodeCopy.children;
  elements.push(nodeCopy);

  for (const child of node.children || []) {
    flattenTree(child, depth + 1, elements);
  }

  return elements;
}

/**
 * Count total elements in tree (recursive).
 *
 * @param {object} node - Root node of tree
 * @returns {number} Total element count including root and all descendants
 */
function countElements(node) {
  let count = 1;
  for (const child of node.children || []) {
    count += countElements(child);
  }
  return count;
}

/**
 * Get screen dimensions from accessibility tree.
 *
 * @param {string|null} udid - Device UDID (uses booted if null)
 * @returns {{width: number, height: number}} Screen dimensions
 */
function getScreenSize(udid = null) {
  const DEFAULT_WIDTH = 390;
  const DEFAULT_HEIGHT = 844;

  try {
    const tree = getAccessibilityTree(udid, false);
    const frame = tree.frame || {};
    return {
      width: parseInt(frame.width, 10) || DEFAULT_WIDTH,
      height: parseInt(frame.height, 10) || DEFAULT_HEIGHT,
    };
  } catch {
    return { width: DEFAULT_WIDTH, height: DEFAULT_HEIGHT };
  }
}

module.exports = {
  getAccessibilityTree,
  flattenTree,
  countElements,
  getScreenSize,
};
