/**
 * XCResult cache management.
 *
 * Handles storage, retrieval, and lifecycle of xcresult bundles for progressive disclosure.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * Recursively get total size of all files under a directory.
 *
 * @param {string} dirPath
 * @returns {number} total bytes
 */
function getDirSizeBytes(dirPath) {
  let total = 0;
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isFile()) {
      total += fs.statSync(fullPath).size;
    } else if (entry.isDirectory()) {
      total += getDirSizeBytes(fullPath);
    }
  }
  return total;
}

/**
 * Recursively copy a directory.
 *
 * @param {string} src
 * @param {string} dest
 */
function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

class XCResultCache {
  /**
   * @param {string|null} cacheDir - Custom cache directory
   */
  constructor(cacheDir = null) {
    this.cacheDir = cacheDir || path.join(os.homedir(), '.ios-simulator-skill', 'xcresults');
    fs.mkdirSync(this.cacheDir, { recursive: true });
  }

  /**
   * Generate timestamped xcresult ID.
   *
   * @param {string} prefix
   * @returns {string}
   */
  generateId(prefix = 'xcresult') {
    const now = new Date();
    const pad = (n, len = 2) => String(n).padStart(len, '0');
    const timestamp = [
      now.getFullYear(),
      pad(now.getMonth() + 1),
      pad(now.getDate()),
      '-',
      pad(now.getHours()),
      pad(now.getMinutes()),
      pad(now.getSeconds()),
    ].join('');
    return `${prefix}-${timestamp}`;
  }

  /**
   * Get full path for xcresult ID.
   *
   * @param {string} xcresultId
   * @returns {string}
   */
  getPath(xcresultId) {
    if (xcresultId.endsWith('.xcresult')) {
      return path.join(this.cacheDir, xcresultId);
    }
    return path.join(this.cacheDir, `${xcresultId}.xcresult`);
  }

  /**
   * Check if xcresult bundle exists.
   *
   * @param {string} xcresultId
   * @returns {boolean}
   */
  exists(xcresultId) {
    return fs.existsSync(this.getPath(xcresultId));
  }

  /**
   * Save xcresult bundle to cache.
   *
   * @param {string} sourcePath
   * @param {string|null} xcresultId
   * @returns {string} xcresult ID
   */
  save(sourcePath, xcresultId = null) {
    if (!fs.existsSync(sourcePath)) {
      throw new Error(`Source xcresult not found: ${sourcePath}`);
    }

    if (!xcresultId) {
      xcresultId = this.generateId();
    }

    const destPath = this.getPath(xcresultId);

    // Remove existing if present
    if (fs.existsSync(destPath)) {
      fs.rmSync(destPath, { recursive: true, force: true });
    }

    copyDirSync(sourcePath, destPath);
    return xcresultId;
  }

  /**
   * List recent xcresult bundles.
   *
   * @param {number} limit
   * @returns {Array<object>}
   */
  list(limit = 10) {
    if (!fs.existsSync(this.cacheDir)) {
      return [];
    }

    const entries = fs.readdirSync(this.cacheDir, { withFileTypes: true });
    const bundles = entries
      .filter((e) => e.isDirectory() && e.name.endsWith('.xcresult'))
      .map((e) => {
        const fullPath = path.join(this.cacheDir, e.name);
        const stat = fs.statSync(fullPath);
        return { name: e.name, fullPath, mtime: stat.mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, limit);

    return bundles.map((b) => {
      const sizeBytes = getDirSizeBytes(b.fullPath);
      return {
        id: path.basename(b.name, '.xcresult'),
        path: b.fullPath,
        created: new Date(b.mtime).toISOString(),
        size_mb: Math.round((sizeBytes / (1024 * 1024)) * 100) / 100,
      };
    });
  }

  /**
   * Clean up old xcresult bundles.
   *
   * @param {number} keepRecent
   * @returns {number} bundles removed
   */
  cleanup(keepRecent = 20) {
    if (!fs.existsSync(this.cacheDir)) {
      return 0;
    }

    const entries = fs.readdirSync(this.cacheDir, { withFileTypes: true });
    const bundles = entries
      .filter((e) => e.isDirectory() && e.name.endsWith('.xcresult'))
      .map((e) => {
        const fullPath = path.join(this.cacheDir, e.name);
        const stat = fs.statSync(fullPath);
        return { fullPath, mtime: stat.mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime);

    let removed = 0;
    for (const bundle of bundles.slice(keepRecent)) {
      fs.rmSync(bundle.fullPath, { recursive: true, force: true });
      removed++;
    }

    return removed;
  }

  /**
   * Get size of xcresult bundle in MB.
   *
   * @param {string} xcresultId
   * @returns {number}
   */
  getSizeMb(xcresultId) {
    const bundlePath = this.getPath(xcresultId);
    if (!fs.existsSync(bundlePath)) {
      return 0.0;
    }
    const sizeBytes = getDirSizeBytes(bundlePath);
    return Math.round((sizeBytes / (1024 * 1024)) * 100) / 100;
  }

  /**
   * Save stderr output alongside xcresult bundle.
   *
   * @param {string} xcresultId
   * @param {string} stderr
   */
  saveStderr(xcresultId, stderr) {
    if (!stderr) return;
    const stderrPath = path.join(this.cacheDir, `${xcresultId}.stderr`);
    fs.writeFileSync(stderrPath, stderr, 'utf8');
  }

  /**
   * Retrieve cached stderr output.
   *
   * @param {string} xcresultId
   * @returns {string}
   */
  getStderr(xcresultId) {
    const stderrPath = path.join(this.cacheDir, `${xcresultId}.stderr`);
    if (!fs.existsSync(stderrPath)) {
      return '';
    }
    return fs.readFileSync(stderrPath, 'utf8');
  }
}

module.exports = { XCResultCache };
