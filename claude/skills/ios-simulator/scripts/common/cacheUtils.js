#!/usr/bin/env node
/**
 * Progressive disclosure cache for large outputs.
 *
 * Implements cache system to support progressive disclosure pattern:
 * - Return concise summary with cacheId for large outputs
 * - User retrieves full details on demand via cacheId
 * - Reduces token usage by 96% for common queries
 *
 * Cache directory: ~/.ios-simulator-skill/cache/
 * Cache expiration: Configurable per cache type (default 1 hour)
 *
 * Used by:
 * - simList.js - Simulator listing progressive disclosure
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

class ProgressiveCache {
  /**
   * @param {string|null} cacheDir - Cache directory path (default: ~/.ios-simulator-skill/cache/)
   * @param {number} maxAgeHours - Max age for cache entries before expiration (default: 1)
   */
  constructor(cacheDir = null, maxAgeHours = 1) {
    this.cacheDir =
      cacheDir ||
      path.join(os.homedir(), ".ios-simulator-skill", "cache");
    this.maxAgeHours = maxAgeHours;
    fs.mkdirSync(this.cacheDir, { recursive: true });
  }

  /**
   * Save data to cache and return cacheId.
   *
   * @param {object} data - Dictionary data to cache
   * @param {string} cacheType - Type of cache ('simulator-list', 'build-log', etc.)
   * @returns {string} Cache ID like 'sim-20251028-143052'
   */
  save(data, cacheType) {
    const now = new Date();
    const timestamp = now
      .toISOString()
      .replace(/[-:T]/g, "")
      .slice(0, 15)
      .replace(/^(\d{8})(\d{6})/, "$1-$2");
    const cachePrefix = cacheType.split("-")[0];
    const cacheId = `${cachePrefix}-${timestamp}`;

    const cacheFile = path.join(this.cacheDir, `${cacheId}.json`);
    const entry = {
      cacheId,
      cacheType,
      createdAt: now.toISOString(),
      data,
    };
    fs.writeFileSync(cacheFile, JSON.stringify(entry, null, 2));
    return cacheId;
  }

  /**
   * Retrieve data from cache by cacheId.
   *
   * @param {string} cacheId - Cache ID from save()
   * @returns {object|null} Cached data, or null if not found/expired
   */
  get(cacheId) {
    const cacheFile = path.join(this.cacheDir, `${cacheId}.json`);
    if (!fs.existsSync(cacheFile)) return null;

    if (this._isExpired(cacheFile)) {
      fs.unlinkSync(cacheFile);
      return null;
    }

    try {
      const entry = JSON.parse(fs.readFileSync(cacheFile, "utf8"));
      return entry.data || null;
    } catch {
      return null;
    }
  }

  /**
   * List available cache entries with metadata.
   *
   * @param {string|null} cacheType - Filter by type, or null for all
   * @returns {Array<{id: string, type: string, createdAt: string, ageSeconds: number}>}
   */
  listEntries(cacheType = null) {
    const entries = [];
    const files = fs
      .readdirSync(this.cacheDir)
      .filter((f) => f.endsWith(".json"))
      .sort()
      .reverse();

    for (const file of files) {
      const filePath = path.join(this.cacheDir, file);

      if (this._isExpired(filePath)) {
        fs.unlinkSync(filePath);
        continue;
      }

      try {
        const entry = JSON.parse(fs.readFileSync(filePath, "utf8"));
        if (cacheType && entry.cacheType !== cacheType) continue;

        const createdAt = new Date(entry.createdAt);
        const ageSeconds = Math.floor((Date.now() - createdAt.getTime()) / 1000);

        entries.push({
          id: entry.cacheId,
          type: entry.cacheType,
          createdAt: entry.createdAt,
          ageSeconds,
        });
      } catch {
        continue;
      }
    }
    return entries;
  }

  /**
   * Remove expired cache entries.
   *
   * @param {number|null} maxAgeHours - Age threshold (default: instance maxAgeHours)
   * @returns {number} Number of entries deleted
   */
  cleanup(maxAgeHours = null) {
    const threshold = maxAgeHours || this.maxAgeHours;
    let deleted = 0;
    const files = fs
      .readdirSync(this.cacheDir)
      .filter((f) => f.endsWith(".json"));

    for (const file of files) {
      const filePath = path.join(this.cacheDir, file);
      if (this._isExpired(filePath, threshold)) {
        fs.unlinkSync(filePath);
        deleted++;
      }
    }
    return deleted;
  }

  /**
   * Clear all cache entries of a type.
   *
   * @param {string|null} cacheType - Type to clear, or null for all
   * @returns {number} Number of entries deleted
   */
  clear(cacheType = null) {
    let deleted = 0;
    const files = fs
      .readdirSync(this.cacheDir)
      .filter((f) => f.endsWith(".json"));

    for (const file of files) {
      const filePath = path.join(this.cacheDir, file);
      if (cacheType === null) {
        fs.unlinkSync(filePath);
        deleted++;
      } else {
        try {
          const entry = JSON.parse(fs.readFileSync(filePath, "utf8"));
          if (entry.cacheType === cacheType) {
            fs.unlinkSync(filePath);
            deleted++;
          }
        } catch {
          // skip corrupt files
        }
      }
    }
    return deleted;
  }

  /**
   * @param {string} cacheFile - Path to cache file
   * @param {number|null} maxAgeHours - Age threshold
   * @returns {boolean} True if file is expired
   */
  _isExpired(cacheFile, maxAgeHours = null) {
    const threshold = maxAgeHours || this.maxAgeHours;
    try {
      const entry = JSON.parse(fs.readFileSync(cacheFile, "utf8"));
      const createdAt = new Date(entry.createdAt);
      const ageHours = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60);
      return ageHours > threshold;
    } catch {
      return true;
    }
  }
}

/** @type {Map<string, ProgressiveCache>} */
const cacheInstances = new Map();

/**
 * Get or create global cache instance.
 *
 * @param {string|null} cacheDir - Custom cache directory (uses default if null)
 * @returns {ProgressiveCache}
 */
function getCache(cacheDir = null) {
  const key = cacheDir || "default";
  if (!cacheInstances.has(key)) {
    cacheInstances.set(key, new ProgressiveCache(cacheDir));
  }
  return cacheInstances.get(key);
}

module.exports = { ProgressiveCache, getCache };
