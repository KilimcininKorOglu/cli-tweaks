/**
 * XCResult bundle parser.
 *
 * Extracts structured data from xcresult bundles using xcresulttool.
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class XCResultParser {
  /**
   * @param {string|null} xcresultPath - Path to xcresult bundle
   * @param {string} stderr - Optional stderr output for fallback parsing
   */
  constructor(xcresultPath, stderr = '') {
    this.xcresultPath = xcresultPath;
    this.stderr = stderr;

    if (xcresultPath && !fs.existsSync(xcresultPath)) {
      throw new Error(`XCResult bundle not found: ${xcresultPath}`);
    }
  }

  /**
   * Get build results as JSON.
   *
   * @returns {object|null}
   */
  getBuildResults() {
    return this._runXcresulttool(['get', 'build-results']);
  }

  /**
   * Get test results summary as JSON.
   *
   * @returns {object|null}
   */
  getTestResults() {
    return this._runXcresulttool(['get', 'test-results', 'summary']);
  }

  /**
   * Get failed test details from xcresult bundle.
   *
   * @returns {object[]}
   */
  getFailedTests() {
    try {
      const data = this._runXcresulttool(['get', 'test-results', 'tests']);
      if (!data) return [];

      const failed = [];
      const nodes = Array.isArray(data) ? data : (data.testNodes || []);
      this._collectFailedTests(nodes, failed);
      return failed;
    } catch (e) {
      process.stderr.write(`Warning: Could not parse failed tests: ${e.message}\n`);
      return [];
    }
  }

  /**
   * Recursively collect failed test cases from test node tree.
   *
   * @param {Array} nodes
   * @param {object[]} failed
   */
  _collectFailedTests(nodes, failed) {
    if (!Array.isArray(nodes)) return;

    for (const node of nodes) {
      if (typeof node !== 'object' || node === null) continue;

      const isTestCase = node.nodeType === 'Test Case';
      const isFailed = node.result === 'Failed';

      if (isTestCase && isFailed) {
        failed.push({
          test_name: node.name || 'Unknown',
          failure_message: node.details || '',
        });
      }

      // Recurse into children
      const children = node.children || [];
      this._collectFailedTests(children, failed);
    }
  }

  /**
   * Get build log as plain text.
   *
   * @returns {string|null}
   */
  getBuildLog() {
    const result = this._runXcresulttool(['get', 'log', '--type', 'build'], false);
    return result || null;
  }

  /**
   * Count errors and warnings from build results.
   *
   * @returns {[number, number]} [errorCount, warningCount]
   */
  countIssues() {
    let errorCount = 0;
    let warningCount = 0;

    const buildResults = this.getBuildResults();

    if (buildResults) {
      try {
        // Try top-level errors/warnings first (newer xcresult format)
        if (Array.isArray(buildResults.errors)) {
          errorCount = buildResults.errors.length;
        }
        if (Array.isArray(buildResults.warnings)) {
          warningCount = buildResults.warnings.length;
        }

        // If not found, try legacy format: actions[0].buildResult.issues
        if (errorCount === 0 && warningCount === 0) {
          const actions = ((buildResults.actions || {})._values) || [];
          if (actions.length > 0) {
            const buildResult = actions[0].buildResult || {};
            const issues = buildResult.issues || {};

            const errorSummaries = ((issues.errorSummaries || {})._values) || [];
            errorCount = errorSummaries.length;

            const warningSummaries = ((issues.warningSummaries || {})._values) || [];
            warningCount = warningSummaries.length;
          }
        }
      } catch (e) {
        process.stderr.write(`Warning: Could not parse issue counts from xcresult: ${e.message}\n`);
      }
    }

    // If no errors found in xcresult but stderr available, count stderr errors
    if (errorCount === 0 && this.stderr) {
      const stderrErrors = this._parseStderrErrors();
      errorCount = stderrErrors.length;
    }

    return [errorCount, warningCount];
  }

  /**
   * Get detailed error information.
   *
   * @returns {object[]}
   */
  getErrors() {
    const buildResults = this.getBuildResults();
    const errors = [];

    if (buildResults) {
      try {
        // Try top-level errors first (newer xcresult format)
        if (Array.isArray(buildResults.errors)) {
          for (const error of buildResults.errors) {
            errors.push({
              message: error.message || 'Unknown error',
              type: error.issueType || 'error',
              location: this._extractLocationFromUrl(error.sourceURL),
            });
          }
        }

        // If not found, try legacy format
        if (errors.length === 0) {
          const actions = ((buildResults.actions || {})._values) || [];
          if (actions.length > 0) {
            const buildResult = actions[0].buildResult || {};
            const issues = buildResult.issues || {};
            const errorSummaries = ((issues.errorSummaries || {})._values) || [];

            for (const error of errorSummaries) {
              errors.push({
                message: (error.message || {})._value || 'Unknown error',
                type: (error.issueType || {})._value || 'error',
                location: this._extractLocation(error),
              });
            }
          }
        }
      } catch (e) {
        process.stderr.write(`Warning: Could not parse errors from xcresult: ${e.message}\n`);
      }
    }

    // If no errors found in xcresult but stderr available, parse stderr
    if (errors.length === 0 && this.stderr) {
      return this._parseStderrErrors();
    }

    return errors;
  }

  /**
   * Get detailed warning information.
   *
   * @returns {object[]}
   */
  getWarnings() {
    const buildResults = this.getBuildResults();
    if (!buildResults) return [];

    const warnings = [];

    try {
      // Try top-level warnings first (newer xcresult format)
      if (Array.isArray(buildResults.warnings)) {
        for (const warning of buildResults.warnings) {
          warnings.push({
            message: warning.message || 'Unknown warning',
            type: warning.issueType || 'warning',
            location: this._extractLocationFromUrl(warning.sourceURL),
          });
        }
      }

      // If not found, try legacy format
      if (warnings.length === 0) {
        const actions = ((buildResults.actions || {})._values) || [];
        if (actions.length === 0) return [];

        const buildResult = actions[0].buildResult || {};
        const issues = buildResult.issues || {};
        const warningSummaries = ((issues.warningSummaries || {})._values) || [];

        for (const warning of warningSummaries) {
          warnings.push({
            message: (warning.message || {})._value || 'Unknown warning',
            type: (warning.issueType || {})._value || 'warning',
            location: this._extractLocation(warning),
          });
        }
      }
    } catch (e) {
      process.stderr.write(`Warning: Could not parse warnings: ${e.message}\n`);
    }

    return warnings;
  }

  /**
   * Extract file location from issue (legacy format).
   *
   * @param {object} issue
   * @returns {object}
   */
  _extractLocation(issue) {
    const location = { file: null, line: null, column: null };

    try {
      const docLocation = issue.documentLocationInCreatingWorkspace || {};
      location.file = (docLocation.url || {})._value || null;
      location.line = (docLocation.startingLineNumber || {})._value || null;
      location.column = (docLocation.startingColumnNumber || {})._value || null;
    } catch (e) {
      // ignore
    }

    return location;
  }

  /**
   * Extract file location from sourceURL (newer xcresult format).
   *
   * @param {string|null} sourceUrl
   * @returns {object}
   */
  _extractLocationFromUrl(sourceUrl) {
    const location = { file: null, line: null, column: null };

    if (!sourceUrl) return location;

    try {
      if (sourceUrl.includes('#')) {
        const [filePart, fragment] = sourceUrl.split('#', 2);

        location.file = filePart.replace('file://', '');

        const params = {};
        for (const param of fragment.split('&')) {
          if (param.includes('=')) {
            const [key, value] = param.split('=', 2);
            params[key] = value;
          }
        }

        location.line = params.StartingLineNumber !== undefined
          ? parseInt(params.StartingLineNumber, 10) + 1
          : null;
        location.column = params.StartingColumnNumber !== undefined
          ? parseInt(params.StartingColumnNumber, 10) + 1
          : null;
      } else {
        location.file = sourceUrl.replace('file://', '');
      }
    } catch (e) {
      // ignore
    }

    return location;
  }

  /**
   * Run xcresulttool command.
   *
   * @param {string[]} args
   * @param {boolean} parseJson
   * @returns {object|string|null}
   */
  _runXcresulttool(args, parseJson = true) {
    if (!this.xcresultPath) return null;

    const cmd = ['xcresulttool', ...args, '--path', this.xcresultPath];

    try {
      const stdout = execFileSync('xcrun', cmd, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      if (parseJson) {
        return JSON.parse(stdout);
      }
      return stdout;
    } catch (e) {
      process.stderr.write(`Error running xcresulttool: ${e.message}\n`);
      if (e.stderr) {
        process.stderr.write(`stderr: ${e.stderr}\n`);
      }
      return null;
    }
  }

  /**
   * Parse common errors from stderr output as fallback.
   *
   * @returns {object[]}
   */
  _parseStderrErrors() {
    const errors = [];

    if (!this.stderr) return errors;

    // Pattern 0: Swift/Clang compilation errors
    const compilationPattern = /^(.+?):(\d+):(\d+):\s*error:\s*(.+?)$/gm;
    let match;
    while ((match = compilationPattern.exec(this.stderr)) !== null) {
      errors.push({
        message: match[4].trim(),
        type: 'compilation',
        location: {
          file: match[1],
          line: parseInt(match[2], 10),
          column: parseInt(match[3], 10),
        },
      });
    }

    // Pattern 1: xcodebuild top-level errors
    const xcodebuildPattern = /xcodebuild:\s*error:\s*(.*?)(?:\n\n|$)/gs;
    while ((match = xcodebuildPattern.exec(this.stderr)) !== null) {
      let message = match[1].trim();
      message = message.split('\n').map((l) => l.trim()).filter(Boolean).join(' ');
      errors.push({
        message,
        type: 'build',
        location: { file: null, line: null, column: null },
      });
    }

    // Pattern 2: Provisioning profile errors
    const provisioningPattern = /error:.*?provisioning profile.*?(?:doesn't|does not|cannot).*?(.+?)(?:\n|$)/gi;
    while ((match = provisioningPattern.exec(this.stderr)) !== null) {
      errors.push({
        message: `Provisioning profile error: ${match[1].trim()}`,
        type: 'provisioning',
        location: { file: null, line: null, column: null },
      });
    }

    // Pattern 3: Code signing errors
    const signingPattern = /error:.*?(?:code sign|signing).*?(.+?)(?:\n|$)/gi;
    while ((match = signingPattern.exec(this.stderr)) !== null) {
      errors.push({
        message: `Code signing error: ${match[1].trim()}`,
        type: 'signing',
        location: { file: null, line: null, column: null },
      });
    }

    // Pattern 4: Generic compilation errors (only if nothing captured yet)
    if (errors.length === 0) {
      const genericPattern = /^(?:\*\*\s)?(?:error|❌):\s*(.+?)(?:\n|$)/gm;
      while ((match = genericPattern.exec(this.stderr)) !== null) {
        errors.push({
          message: match[1].trim(),
          type: 'build',
          location: { file: null, line: null, column: null },
        });
      }
    }

    // Pattern 5: Specific "No profiles" error
    if (this.stderr.includes('No profiles for')) {
      const noProfilePattern = /No profiles for '(.*?)' were found/g;
      while ((match = noProfilePattern.exec(this.stderr)) !== null) {
        errors.push({
          message: `No provisioning profile found for bundle ID '${match[1]}'`,
          type: 'provisioning',
          location: { file: null, line: null, column: null },
        });
      }
    }

    return errors;
  }
}

module.exports = { XCResultParser };
