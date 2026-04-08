/**
 * Common utilities shared across iOS simulator scripts.
 *
 * Organization:
 * - deviceUtils: Device detection, command building, coordinate transformation
 * - idbUtils: IDB-specific operations (accessibility tree, element manipulation)
 * - cacheUtils: Progressive disclosure caching for large outputs
 * - screenshotUtils: Screenshot capture with file and inline modes
 */

const {
  buildSimctlCommand,
  buildIdbCommand,
  getBootedDeviceUdid,
  resolveUdid,
  getDeviceScreenSize,
  resolveDeviceIdentifier,
  listSimulators,
  extractDeviceType,
  transformScreenshotCoords,
} = require("./deviceUtils");

const {
  getAccessibilityTree,
  flattenTree,
  countElements,
  getScreenSize,
} = require("./idbUtils");

const { ProgressiveCache, getCache } = require("./cacheUtils");

const {
  captureScreenshot,
  formatScreenshotResult,
  generateScreenshotName,
  getSizePreset,
  resizeScreenshot,
  getImageDimensions,
} = require("./screenshotUtils");

module.exports = {
  // deviceUtils
  buildSimctlCommand,
  buildIdbCommand,
  getBootedDeviceUdid,
  resolveUdid,
  getDeviceScreenSize,
  resolveDeviceIdentifier,
  listSimulators,
  extractDeviceType,
  transformScreenshotCoords,
  // idbUtils
  getAccessibilityTree,
  flattenTree,
  countElements,
  getScreenSize,
  // cacheUtils
  ProgressiveCache,
  getCache,
  // screenshotUtils
  captureScreenshot,
  formatScreenshotResult,
  generateScreenshotName,
  getSizePreset,
  resizeScreenshot,
  getImageDimensions,
};
