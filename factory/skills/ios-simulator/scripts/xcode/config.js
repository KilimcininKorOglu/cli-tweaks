/**
 * Configuration management for iOS Simulator Skill.
 *
 * Handles loading, validation, and auto-updating of project-local config files.
 */

const fs = require('fs');
const path = require('path');

const DEFAULT_CONFIG = {
  device: {
    preferred_simulator: null,
    preferred_os_version: null,
    fallback_to_any_iphone: true,
    last_used_simulator: null,
    last_used_at: null,
  },
};

class Config {
  /**
   * @param {object} data - Config data dict
   * @param {string} configPath - Path to config file
   */
  constructor(data, configPath) {
    this.data = data;
    this.configPath = configPath;
  }

  /**
   * Load config from project directory.
   *
   * @param {string|null} projectDir - Project root (defaults to cwd)
   * @returns {Config}
   */
  static load(projectDir = null) {
    if (!projectDir) {
      projectDir = process.cwd();
    }

    // Auto-detect skill directory name from actual installation location
    // This file is at: skill/scripts/xcode/config.js
    // Navigate up to skill/ directory and use its name
    const skillRoot = path.resolve(__dirname, '..', '..');
    const skillName = path.basename(skillRoot);

    const configPath = path.join(projectDir, '.claude', 'skills', skillName, 'config.json');

    // Load existing config
    if (fs.existsSync(configPath)) {
      try {
        const raw = fs.readFileSync(configPath, 'utf8');
        const data = JSON.parse(raw);

        // Merge with defaults (in case new fields added)
        const merged = Config._mergeWithDefaults(data);
        return new Config(merged, configPath);
      } catch (e) {
        if (e instanceof SyntaxError) {
          process.stderr.write(`Warning: Invalid JSON in ${configPath}: ${e.message}\n`);
          process.stderr.write('Using default config\n');
        } else {
          process.stderr.write(`Warning: Could not load config: ${e.message}\n`);
        }
        return new Config(JSON.parse(JSON.stringify(DEFAULT_CONFIG)), configPath);
      }
    }

    // Return default config (will be created on first save)
    return new Config(JSON.parse(JSON.stringify(DEFAULT_CONFIG)), configPath);
  }

  /**
   * Merge user config with defaults.
   *
   * @param {object} data - User config data
   * @returns {object}
   */
  static _mergeWithDefaults(data) {
    const merged = JSON.parse(JSON.stringify(DEFAULT_CONFIG));

    // Deep merge device section
    if (data.device) {
      Object.assign(merged.device, data.device);
    }

    return merged;
  }

  /**
   * Save config to file atomically.
   */
  save() {
    try {
      // Create parent directories
      const parentDir = path.dirname(this.configPath);
      fs.mkdirSync(parentDir, { recursive: true });

      // Atomic write: temp file + rename
      const tempPath = this.configPath + '.tmp';
      fs.writeFileSync(tempPath, JSON.stringify(this.data, null, 2) + '\n', 'utf8');

      // Atomic rename
      fs.renameSync(tempPath, this.configPath);
    } catch (e) {
      process.stderr.write(`Warning: Could not save config: ${e.message}\n`);
    }
  }

  /**
   * Update last used simulator and timestamp.
   *
   * @param {string} name - Simulator name
   */
  updateLastUsedSimulator(name) {
    this.data.device.last_used_simulator = name;
    this.data.device.last_used_at = new Date().toISOString();
  }

  /**
   * Get preferred simulator.
   *
   * @returns {string|null}
   */
  getPreferredSimulator() {
    const device = this.data.device || {};

    // Manual preference takes priority
    if (device.preferred_simulator) {
      return device.preferred_simulator;
    }

    // Auto-learned preference
    if (device.last_used_simulator) {
      return device.last_used_simulator;
    }

    return null;
  }

  /**
   * Check if fallback to any iPhone is enabled.
   *
   * @returns {boolean}
   */
  shouldFallbackToAnyIphone() {
    const device = this.data.device || {};
    return device.fallback_to_any_iphone !== undefined ? device.fallback_to_any_iphone : true;
  }
}

module.exports = { Config, DEFAULT_CONFIG };
