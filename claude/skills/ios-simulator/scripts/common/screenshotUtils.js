#!/usr/bin/env node
/**
 * Screenshot utilities with dual-mode support.
 *
 * Provides unified screenshot handling with:
 * - File-based mode: Persistent artifacts for test documentation
 * - Inline base64 mode: Vision-based automation for agent analysis
 * - Size presets: Token optimization (full/half/quarter/thumb)
 * - Semantic naming: {appName}_{screenName}_{state}_{timestamp}.png
 *
 * Resize uses macOS sips (no external dependencies).
 *
 * Used by:
 * - testRecorder.js - Step-based screenshot recording
 * - appStateCapture.js - State snapshot captures
 */

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

/**
 * Generate semantic screenshot filename.
 *
 * @param {object} opts
 * @param {string|null} opts.appName
 * @param {string|null} opts.screenName
 * @param {string|null} opts.state
 * @param {string|null} opts.timestamp
 * @param {string} opts.extension
 * @returns {string} Semantic filename
 */
function generateScreenshotName({
  appName = null,
  screenName = null,
  state = null,
  timestamp = null,
  extension = "png",
} = {}) {
  if (!timestamp) {
    const now = new Date();
    timestamp = now.toISOString().replace(/[-:T]/g, "").slice(0, 15);
    timestamp = timestamp.replace(/^(\d{8})(\d{6})/, "$1-$2");
  }

  if (appName || screenName || state) {
    const parts = [appName, screenName, state].filter(Boolean);
    return `${parts.join("_")}_${timestamp}.${extension}`;
  }
  return `screenshot_${timestamp}.${extension}`;
}

/**
 * Get scale factors for size preset.
 *
 * @param {string} size - 'full', 'half', 'quarter', 'thumb'
 * @returns {{scaleX: number, scaleY: number}}
 */
function getSizePreset(size = "half") {
  const presets = {
    full: { scaleX: 1.0, scaleY: 1.0 },
    half: { scaleX: 0.5, scaleY: 0.5 },
    quarter: { scaleX: 0.25, scaleY: 0.25 },
    thumb: { scaleX: 0.1, scaleY: 0.1 },
  };
  return presets[size] || presets.half;
}

/**
 * Resize screenshot using macOS sips (no PIL dependency).
 *
 * @param {string} inputPath - Path to original screenshot
 * @param {string|null} outputPath - Output path (uses input if null)
 * @param {string} size - 'full', 'half', 'quarter', 'thumb'
 * @returns {{outputPath: string, width: number, height: number}}
 */
function resizeScreenshot(inputPath, outputPath = null, size = "half") {
  if (!fs.existsSync(inputPath)) {
    throw new Error(`Screenshot not found: ${inputPath}`);
  }

  if (size === "full") {
    const dest = outputPath || inputPath;
    if (outputPath && outputPath !== inputPath) {
      fs.copyFileSync(inputPath, outputPath);
    }
    const dims = getImageDimensions(dest);
    return { outputPath: dest, ...dims };
  }

  // Get original dimensions via sips
  const origDims = getImageDimensions(inputPath);
  const { scaleX, scaleY } = getSizePreset(size);
  const newW = Math.round(origDims.width * scaleX);
  const newH = Math.round(origDims.height * scaleY);

  // Determine output
  if (!outputPath) {
    const ext = path.extname(inputPath);
    const stem = path.basename(inputPath, ext);
    outputPath = path.join(path.dirname(inputPath), `${stem}_${size}${ext}`);
  }

  // Copy then resize with sips (macOS built-in)
  fs.copyFileSync(inputPath, outputPath);
  execFileSync("sips", [
    "--resampleWidth",
    String(newW),
    "--resampleHeight",
    String(newH),
    outputPath,
  ], { stdio: ["pipe", "pipe", "pipe"] });

  return { outputPath, width: newW, height: newH };
}

/**
 * Get image dimensions using sips (macOS built-in).
 *
 * @param {string} filePath
 * @returns {{width: number, height: number}}
 */
function getImageDimensions(filePath) {
  try {
    const output = execFileSync(
      "sips",
      ["-g", "pixelWidth", "-g", "pixelHeight", filePath],
      { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }
    );
    const wMatch = output.match(/pixelWidth:\s*(\d+)/);
    const hMatch = output.match(/pixelHeight:\s*(\d+)/);
    return {
      width: wMatch ? parseInt(wMatch[1], 10) : 390,
      height: hMatch ? parseInt(hMatch[1], 10) : 844,
    };
  } catch {
    return { width: 390, height: 844 };
  }
}

/**
 * Capture screenshot with flexible output modes.
 *
 * @param {string} udid - Device UDID
 * @param {object} opts
 * @param {string|null} opts.outputPath
 * @param {string} opts.size - 'full', 'half', 'quarter', 'thumb'
 * @param {boolean} opts.inline - Return base64 instead of saving
 * @param {string|null} opts.appName
 * @param {string|null} opts.screenName
 * @param {string|null} opts.state
 * @returns {object} Result with mode-specific fields
 */
function captureScreenshot(
  udid,
  {
    outputPath = null,
    size = "half",
    inline = false,
    appName = null,
    screenName = null,
    state = null,
  } = {}
) {
  const tempPath = "/tmp/ios_simulator_screenshot.png";

  try {
    execFileSync("xcrun", ["simctl", "io", udid, "screenshot", tempPath], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    if (inline) {
      let finalPath = tempPath;
      let width, height;

      if (size !== "full") {
        const resized = resizeScreenshot(tempPath, null, size);
        finalPath = resized.outputPath;
        width = resized.width;
        height = resized.height;
      } else {
        const dims = getImageDimensions(tempPath);
        width = dims.width;
        height = dims.height;
      }

      const base64Data = fs.readFileSync(finalPath).toString("base64");

      // Cleanup
      try { fs.unlinkSync(tempPath); } catch { /* ignore */ }
      if (finalPath !== tempPath) {
        try { fs.unlinkSync(finalPath); } catch { /* ignore */ }
      }

      return {
        mode: "inline",
        base64Data,
        mimeType: "image/png",
        width,
        height,
        sizePreset: size,
      };
    }

    // File mode
    if (!outputPath) {
      outputPath = generateScreenshotName({ appName, screenName, state });
    }

    let finalPath, width, height;
    if (size !== "full") {
      const resized = resizeScreenshot(tempPath, outputPath, size);
      finalPath = resized.outputPath;
      width = resized.width;
      height = resized.height;
    } else {
      fs.renameSync(tempPath, outputPath);
      finalPath = outputPath;
      const dims = getImageDimensions(finalPath);
      width = dims.width;
      height = dims.height;
    }

    const sizeBytes = fs.statSync(finalPath).size;

    return {
      mode: "file",
      filePath: finalPath,
      sizeBytes,
      width,
      height,
      sizePreset: size,
    };
  } catch (e) {
    throw new Error(`Screenshot capture error: ${e.message}`);
  }
}

/**
 * Format screenshot result for human-readable output.
 *
 * @param {object} result - Result from captureScreenshot()
 * @returns {string}
 */
function formatScreenshotResult(result) {
  if (result.mode === "file") {
    return (
      `Screenshot: ${result.filePath}\n` +
      `Dimensions: ${result.width}x${result.height}\n` +
      `Size: ${result.sizeBytes} bytes`
    );
  }
  return (
    `Screenshot (inline): ${result.width}x${result.height}\n` +
    `Base64 length: ${result.base64Data.length} chars`
  );
}

module.exports = {
  generateScreenshotName,
  getSizePreset,
  resizeScreenshot,
  getImageDimensions,
  captureScreenshot,
  formatScreenshotResult,
};
