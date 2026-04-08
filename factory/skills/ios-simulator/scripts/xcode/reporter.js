/**
 * Build/test output formatting.
 *
 * Provides multiple output formats with progressive disclosure support.
 */

class OutputFormatter {
  /**
   * Format ultra-minimal output (5-10 tokens on success, more on failure).
   *
   * @param {object} opts
   * @param {string} opts.status
   * @param {number} opts.errorCount
   * @param {number} opts.warningCount
   * @param {string} opts.xcresultId
   * @param {object|null} opts.testInfo
   * @param {string[]|null} opts.hints
   * @param {object[]|null} opts.errors
   * @param {object[]|null} opts.failedTests
   * @returns {string}
   */
  static formatMinimal({
    status,
    errorCount,
    warningCount,
    xcresultId,
    testInfo = null,
    hints = null,
    errors = null,
    failedTests = null,
  }) {
    const lines = [];

    if (testInfo) {
      const total = testInfo.total || 0;
      const passed = testInfo.passed || 0;
      const failed = testInfo.failed || 0;
      const duration = testInfo.duration || 0.0;

      const testStatus = failed === 0 ? 'PASS' : 'FAIL';
      lines.push(`Tests: ${testStatus} (${passed}/${total} passed, ${duration.toFixed(1)}s) [${xcresultId}]`);
    } else {
      lines.push(`Build: ${status} (${errorCount} errors, ${warningCount} warnings) [${xcresultId}]`);
    }

    // Surface errors inline on failure
    if (status === 'FAILED' && errors && errors.length > 0) {
      lines.push('');
      lines.push(OutputFormatter.formatErrors(errors, 5));
    }

    // Surface failed tests inline on failure
    if (failedTests && failedTests.length > 0) {
      lines.push('');
      lines.push(OutputFormatter.formatTestFailures(failedTests, 5));
    }

    // Add hints if provided and build failed
    if (hints && hints.length > 0 && status === 'FAILED') {
      lines.push('');
      lines.push(...hints);
    }

    return lines.join('\n');
  }

  /**
   * Format failed test details.
   *
   * @param {object[]} failedTests
   * @param {number} limit
   * @returns {string}
   */
  static formatTestFailures(failedTests, limit = 5) {
    if (!failedTests || failedTests.length === 0) {
      return 'No test failures found.';
    }

    const lines = [`Failed tests (${failedTests.length}):`];
    lines.push('');

    const shown = failedTests.slice(0, limit);
    shown.forEach((test, i) => {
      const name = test.test_name || 'Unknown';
      const message = test.failure_message || '';
      lines.push(`${i + 1}. ${name}`);
      if (message) {
        lines.push(`   ${message}`);
      }
      lines.push('');
    });

    if (failedTests.length > limit) {
      lines.push(`... and ${failedTests.length - limit} more failures`);
    }

    return lines.join('\n');
  }

  /**
   * Format error details.
   *
   * @param {object[]} errors
   * @param {number} limit
   * @returns {string}
   */
  static formatErrors(errors, limit = 10) {
    if (!errors || errors.length === 0) {
      return 'No errors found.';
    }

    const lines = [`Errors (${errors.length}):`];
    lines.push('');

    const shown = errors.slice(0, limit);
    shown.forEach((error, i) => {
      const message = error.message || 'Unknown error';
      const location = error.location || {};

      const locParts = [];
      if (location.file) {
        locParts.push(location.file.replace('file://', ''));
      }
      if (location.line) {
        locParts.push(`line ${location.line}`);
      }

      const locationStr = locParts.length > 0 ? locParts.join(':') : 'unknown location';

      lines.push(`${i + 1}. ${message}`);
      lines.push(`   Location: ${locationStr}`);
      lines.push('');
    });

    if (errors.length > limit) {
      lines.push(`... and ${errors.length - limit} more errors`);
    }

    return lines.join('\n');
  }

  /**
   * Format warning details.
   *
   * @param {object[]} warnings
   * @param {number} limit
   * @returns {string}
   */
  static formatWarnings(warnings, limit = 10) {
    if (!warnings || warnings.length === 0) {
      return 'No warnings found.';
    }

    const lines = [`Warnings (${warnings.length}):`];
    lines.push('');

    const shown = warnings.slice(0, limit);
    shown.forEach((warning, i) => {
      const message = warning.message || 'Unknown warning';
      const location = warning.location || {};

      const locParts = [];
      if (location.file) {
        locParts.push(location.file.replace('file://', ''));
      }
      if (location.line) {
        locParts.push(`line ${location.line}`);
      }

      const locationStr = locParts.length > 0 ? locParts.join(':') : 'unknown location';

      lines.push(`${i + 1}. ${message}`);
      lines.push(`   Location: ${locationStr}`);
      lines.push('');
    });

    if (warnings.length > limit) {
      lines.push(`... and ${warnings.length - limit} more warnings`);
    }

    return lines.join('\n');
  }

  /**
   * Format build log (show last N lines).
   *
   * @param {string} log
   * @param {number} lineCount
   * @returns {string}
   */
  static formatLog(log, lineCount = 50) {
    if (!log) {
      return 'No build log available.';
    }

    const logLines = log.trim().split('\n');

    if (logLines.length <= lineCount) {
      return log;
    }

    const excerpt = logLines.slice(-lineCount);
    return `... (showing last ${lineCount} lines of ${logLines.length})\n\n${excerpt.join('\n')}`;
  }

  /**
   * Format data as JSON.
   *
   * @param {object} data
   * @returns {string}
   */
  static formatJson(data) {
    return JSON.stringify(data, null, 2);
  }

  /**
   * Generate actionable hints based on error types.
   *
   * @param {object[]} errors
   * @returns {string[]}
   */
  static generateHints(errors) {
    const hints = [];
    const errorTypes = new Set();

    for (const error of errors) {
      errorTypes.add(error.type || 'unknown');
    }

    if (errorTypes.has('provisioning')) {
      hints.push('Provisioning profile issue detected:');
      hints.push('  \u2022 Ensure you have a valid provisioning profile for iOS Simulator');
      hints.push('  \u2022 For simulator builds, use CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO');
      hints.push("  \u2022 Or specify simulator explicitly: --simulator 'iPhone 16 Pro'");
    }

    if (errorTypes.has('signing')) {
      hints.push('Code signing issue detected:');
      hints.push('  \u2022 For simulator builds, code signing is not required');
      hints.push('  \u2022 Ensure build settings target iOS Simulator, not physical device');
      hints.push('  \u2022 Check destination: platform=iOS Simulator,name=<device>');
    }

    if (errorTypes.size === 0 || errorTypes.has('build')) {
      if (errors.some((e) => (e.message || '').toLowerCase().includes('destination'))) {
        hints.push('Device selection issue detected:');
        hints.push('  \u2022 List available simulators: xcrun simctl list devices available');
        hints.push("  \u2022 Specify simulator: --simulator 'iPhone 16 Pro'");
      }
    }

    return hints;
  }

  /**
   * Format verbose output with error/warning details.
   *
   * @param {object} opts
   * @param {string} opts.status
   * @param {number} opts.errorCount
   * @param {number} opts.warningCount
   * @param {string} opts.xcresultId
   * @param {object[]|null} opts.errors
   * @param {object[]|null} opts.warnings
   * @param {object|null} opts.testInfo
   * @returns {string}
   */
  static formatVerbose({
    status,
    errorCount,
    warningCount,
    xcresultId,
    errors = null,
    warnings = null,
    testInfo = null,
  }) {
    const lines = [];

    if (testInfo) {
      const total = testInfo.total || 0;
      const passed = testInfo.passed || 0;
      const failed = testInfo.failed || 0;
      const duration = testInfo.duration || 0.0;

      const testStatus = failed === 0 ? 'PASS' : 'FAIL';
      lines.push(`Tests: ${testStatus}`);
      lines.push(`  Total: ${total}`);
      lines.push(`  Passed: ${passed}`);
      lines.push(`  Failed: ${failed}`);
      lines.push(`  Duration: ${duration.toFixed(1)}s`);
    } else {
      lines.push(`Build: ${status}`);
    }

    lines.push(`XCResult: ${xcresultId}`);
    lines.push('');

    if (errors && errors.length > 0) {
      lines.push(OutputFormatter.formatErrors(errors, 5));
      lines.push('');
    }

    if (warnings && warnings.length > 0) {
      lines.push(OutputFormatter.formatWarnings(warnings, 5));
      lines.push('');
    }

    lines.push(`Summary: ${errorCount} errors, ${warningCount} warnings`);

    return lines.join('\n');
  }
}

module.exports = { OutputFormatter };
