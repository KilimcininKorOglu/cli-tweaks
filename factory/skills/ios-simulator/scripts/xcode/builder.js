/**
 * Xcode build execution.
 *
 * Handles xcodebuild command construction and execution with xcresult generation.
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const { XCResultCache } = require('./cache');
const { Config } = require('./config');

class BuildRunner {
  /**
   * @param {object} opts
   * @param {string|null} opts.projectPath
   * @param {string|null} opts.workspacePath
   * @param {string|null} opts.scheme
   * @param {string} opts.configuration
   * @param {string|null} opts.simulator
   * @param {XCResultCache|null} opts.cache
   */
  constructor({
    projectPath = null,
    workspacePath = null,
    scheme = null,
    configuration = 'Debug',
    simulator = null,
    cache = null,
  } = {}) {
    this.projectPath = projectPath;
    this.workspacePath = workspacePath;
    this.scheme = scheme;
    this.configuration = configuration;
    this.simulator = simulator;
    this.cache = cache || new XCResultCache();
  }

  /**
   * Auto-detect build scheme from project/workspace.
   *
   * @returns {string|null}
   */
  autoDetectScheme() {
    const cmd = ['-list'];

    if (this.workspacePath) {
      cmd.push('-workspace', this.workspacePath);
    } else if (this.projectPath) {
      cmd.push('-project', this.projectPath);
    } else {
      return null;
    }

    try {
      const stdout = execFileSync('xcodebuild', cmd, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let inSchemesSection = false;
      for (const rawLine of stdout.split('\n')) {
        const line = rawLine.trim();

        if (line.includes('Schemes:')) {
          inSchemesSection = true;
          continue;
        }

        if (inSchemesSection && line && !line.startsWith('Build')) {
          return line;
        }
      }
    } catch (e) {
      process.stderr.write(`Error auto-detecting scheme: ${e.message}\n`);
    }

    return null;
  }

  /**
   * Get xcodebuild destination string.
   *
   * @returns {string}
   */
  getSimulatorDestination() {
    // Priority 1: CLI flag
    if (this.simulator) {
      return `platform=iOS Simulator,name=${this.simulator}`;
    }

    // Priority 2-3: Config preferences
    try {
      let projectDir = null;
      if (this.projectPath) {
        projectDir = path.dirname(this.projectPath);
      } else if (this.workspacePath) {
        projectDir = path.dirname(this.workspacePath);
      }

      const config = Config.load(projectDir);
      const preferred = config.getPreferredSimulator();

      if (preferred) {
        if (this._simulatorExists(preferred)) {
          return `platform=iOS Simulator,name=${preferred}`;
        }
        process.stderr.write(`Warning: Preferred simulator '${preferred}' not available\n`);
        if (config.shouldFallbackToAnyIphone()) {
          process.stderr.write('Falling back to auto-detection...\n');
        } else {
          return `platform=iOS Simulator,name=${preferred}`;
        }
      }
    } catch (e) {
      process.stderr.write(`Warning: Could not load config: ${e.message}\n`);
    }

    // Priority 4-5: Auto-detect
    return this._autoDetectSimulator();
  }

  /**
   * Check if simulator with given name exists and is available.
   *
   * @param {string} name
   * @returns {boolean}
   */
  _simulatorExists(name) {
    try {
      const stdout = execFileSync('xcrun', ['simctl', 'list', 'devices', 'available', 'iOS'], {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      return stdout.split('\n').some((line) => line.includes(name) && line.includes('('));
    } catch (e) {
      return false;
    }
  }

  /**
   * Extract simulator name from destination string.
   *
   * @param {string} destination
   * @returns {string|null}
   */
  _extractSimulatorNameFromDestination(destination) {
    const match = destination.match(/name=([^,]+)/);
    if (match) {
      return match[1].trim();
    }
    return null;
  }

  /**
   * Auto-detect best available iOS simulator.
   *
   * @returns {string}
   */
  _autoDetectSimulator() {
    try {
      const stdout = execFileSync('xcrun', ['simctl', 'list', 'devices', 'available', 'iOS'], {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      for (const line of stdout.split('\n')) {
        if (line.includes('iPhone') && line.includes('(')) {
          const name = line.split('(')[0].trim();
          if (name) {
            return `platform=iOS Simulator,name=${name}`;
          }
        }
      }

      return 'generic/platform=iOS Simulator';
    } catch (e) {
      process.stderr.write(`Warning: Could not auto-detect simulator: ${e.message}\n`);
      return 'generic/platform=iOS Simulator';
    }
  }

  /**
   * Build the project.
   *
   * @param {boolean} clean
   * @returns {[boolean, string, string]} [success, xcresultId, stderr]
   */
  build(clean = false) {
    // Auto-detect scheme if needed
    if (!this.scheme) {
      this.scheme = this.autoDetectScheme();
      if (!this.scheme) {
        process.stderr.write('Error: Could not auto-detect scheme. Use --scheme\n');
        return [false, '', ''];
      }
    }

    // Generate xcresult ID and path
    const xcresultId = this.cache.generateId();
    const xcresultPath = this.cache.getPath(xcresultId);

    // Build command
    const cmd = ['-quiet'];
    if (clean) cmd.push('clean');
    cmd.push('build');

    if (this.workspacePath) {
      cmd.push('-workspace', this.workspacePath);
    } else if (this.projectPath) {
      cmd.push('-project', this.projectPath);
    } else {
      process.stderr.write('Error: No project or workspace specified\n');
      return [false, '', ''];
    }

    cmd.push(
      '-scheme', this.scheme,
      '-configuration', this.configuration,
      '-destination', this.getSimulatorDestination(),
      '-resultBundlePath', xcresultPath
    );

    // Execute build
    try {
      let stdout = '';
      let stderr = '';
      let success = false;

      try {
        stdout = execFileSync('xcodebuild', cmd, {
          encoding: 'utf8',
          stdio: ['pipe', 'pipe', 'pipe'],
        });
        success = true;
      } catch (e) {
        // execFileSync throws on non-zero exit
        success = false;
        stdout = e.stdout || '';
        stderr = e.stderr || '';
      }

      // xcresult bundle should be created even on failure
      if (!fs.existsSync(xcresultPath)) {
        process.stderr.write('Warning: xcresult bundle was not created\n');
        return [success, '', stderr];
      }

      // Auto-update config with last used simulator (on success only)
      if (success) {
        this._updateConfigSimulator();
      }

      return [success, xcresultId, stderr];
    } catch (e) {
      process.stderr.write(`Error executing build: ${e.message}\n`);
      return [false, '', String(e)];
    }
  }

  /**
   * Run tests.
   *
   * @param {string|null} testSuite
   * @returns {[boolean, string, string]} [success, xcresultId, stderr]
   */
  test(testSuite = null) {
    // Auto-detect scheme if needed
    if (!this.scheme) {
      this.scheme = this.autoDetectScheme();
      if (!this.scheme) {
        process.stderr.write('Error: Could not auto-detect scheme. Use --scheme\n');
        return [false, '', ''];
      }
    }

    // Generate xcresult ID and path
    const xcresultId = this.cache.generateId();
    const xcresultPath = this.cache.getPath(xcresultId);

    // Build command
    const cmd = ['-quiet', 'test'];

    if (this.workspacePath) {
      cmd.push('-workspace', this.workspacePath);
    } else if (this.projectPath) {
      cmd.push('-project', this.projectPath);
    } else {
      process.stderr.write('Error: No project or workspace specified\n');
      return [false, '', ''];
    }

    cmd.push(
      '-scheme', this.scheme,
      '-destination', this.getSimulatorDestination(),
      '-resultBundlePath', xcresultPath
    );

    if (testSuite) {
      cmd.push('-only-testing', testSuite);
    }

    // Execute tests
    try {
      let stdout = '';
      let stderr = '';
      let success = false;

      try {
        stdout = execFileSync('xcodebuild', cmd, {
          encoding: 'utf8',
          stdio: ['pipe', 'pipe', 'pipe'],
        });
        success = true;
      } catch (e) {
        success = false;
        stdout = e.stdout || '';
        stderr = e.stderr || '';
      }

      // xcresult bundle should be created even on failure
      if (!fs.existsSync(xcresultPath)) {
        process.stderr.write('Warning: xcresult bundle was not created\n');
        return [success, '', stderr];
      }

      // Auto-update config with last used simulator (on success only)
      if (success) {
        this._updateConfigSimulator();
      }

      return [success, xcresultId, stderr];
    } catch (e) {
      process.stderr.write(`Error executing tests: ${e.message}\n`);
      return [false, '', String(e)];
    }
  }

  /**
   * Update config with last used simulator after successful build/test.
   */
  _updateConfigSimulator() {
    try {
      let projectDir = null;
      if (this.projectPath) {
        projectDir = path.dirname(this.projectPath);
      } else if (this.workspacePath) {
        projectDir = path.dirname(this.workspacePath);
      }

      const config = Config.load(projectDir);
      const destination = this.getSimulatorDestination();
      const simulatorName = this._extractSimulatorNameFromDestination(destination);

      if (simulatorName) {
        config.updateLastUsedSimulator(simulatorName);
        config.save();
      }
    } catch (e) {
      process.stderr.write(`Warning: Could not update config: ${e.message}\n`);
    }
  }
}

module.exports = { BuildRunner };
