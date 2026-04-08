#!/usr/bin/env node
/**
 * Build and Test Automation for Xcode Projects
 *
 * Ultra token-efficient build automation with progressive disclosure via xcresult bundles.
 *
 * Features:
 * - Minimal default output (5-10 tokens)
 * - Progressive disclosure for error/warning/log details
 * - Native xcresult bundle support
 * - Clean modular architecture
 *
 * Usage Examples:
 *   # Build (minimal output)
 *   node scripts/buildAndTest.js --project MyApp.xcodeproj
 *   # Output: Build: SUCCESS (0 errors, 3 warnings) [xcresult-20251018-143052]
 *
 *   # Get error details
 *   node scripts/buildAndTest.js --get-errors xcresult-20251018-143052
 *
 *   # Get warnings
 *   node scripts/buildAndTest.js --get-warnings xcresult-20251018-143052
 *
 *   # Get build log
 *   node scripts/buildAndTest.js --get-log xcresult-20251018-143052
 *
 *   # Get everything as JSON
 *   node scripts/buildAndTest.js --get-all xcresult-20251018-143052 --json
 *
 *   # List recent builds
 *   node scripts/buildAndTest.js --list-xcresults
 *
 *   # Verbose mode (for debugging)
 *   node scripts/buildAndTest.js --project MyApp.xcodeproj --verbose
 */

const fs = require('fs');
const path = require('path');
const { BuildRunner, OutputFormatter, XCResultCache, XCResultParser } = require('./xcode');

/**
 * Parse CLI arguments from process.argv.
 *
 * @returns {object}
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    project: null,
    workspace: null,
    scheme: null,
    configuration: 'Debug',
    simulator: null,
    clean: false,
    test: false,
    suite: null,
    getErrors: null,
    getWarnings: null,
    getLog: null,
    getAll: null,
    listXcresults: false,
    verbose: false,
    json: false,
    help: false,
  };

  let i = 0;
  while (i < args.length) {
    const arg = args[i];

    switch (arg) {
      case '--project':
        parsed.project = args[++i];
        break;
      case '--workspace':
        parsed.workspace = args[++i];
        break;
      case '--scheme':
        parsed.scheme = args[++i];
        break;
      case '--configuration':
        parsed.configuration = args[++i];
        break;
      case '--simulator':
        parsed.simulator = args[++i];
        break;
      case '--clean':
        parsed.clean = true;
        break;
      case '--test':
        parsed.test = true;
        break;
      case '--suite':
        parsed.suite = args[++i];
        break;
      case '--get-errors':
        parsed.getErrors = args[++i];
        break;
      case '--get-warnings':
        parsed.getWarnings = args[++i];
        break;
      case '--get-log':
        parsed.getLog = args[++i];
        break;
      case '--get-all':
        parsed.getAll = args[++i];
        break;
      case '--list-xcresults':
        parsed.listXcresults = true;
        break;
      case '--verbose':
        parsed.verbose = true;
        break;
      case '--json':
        parsed.json = true;
        break;
      case '--help':
      case '-h':
        parsed.help = true;
        break;
      default:
        process.stderr.write(`Unknown argument: ${arg}\n`);
        process.exit(1);
    }

    i++;
  }

  return parsed;
}

/**
 * Print help text.
 */
function printHelp() {
  const help = `
Build and test Xcode projects with progressive disclosure

Build/Test Options:
  --project PATH        Path to .xcodeproj file
  --workspace PATH      Path to .xcworkspace file
  --scheme NAME         Build scheme (auto-detected if not specified)
  --configuration NAME  Build configuration (default: Debug)
  --simulator NAME      Simulator name (default: iPhone 15)
  --clean               Clean before building
  --test                Run tests
  --suite NAME          Specific test suite to run

Progressive Disclosure Options:
  --get-errors ID       Get error details from xcresult
  --get-warnings ID     Get warning details from xcresult
  --get-log ID          Get build log from xcresult
  --get-all ID          Get all details from xcresult
  --list-xcresults      List recent xcresult bundles

Output Options:
  --verbose             Show detailed output
  --json                Output as JSON
  --help, -h            Show this help message

Examples:
  # Build project (minimal output)
  node scripts/buildAndTest.js --project MyApp.xcodeproj

  # Run tests
  node scripts/buildAndTest.js --project MyApp.xcodeproj --test

  # Get error details from previous build
  node scripts/buildAndTest.js --get-errors xcresult-20251018-143052

  # Get all details as JSON
  node scripts/buildAndTest.js --get-all xcresult-20251018-143052 --json

  # List recent builds
  node scripts/buildAndTest.js --list-xcresults
`.trim();

  console.log(help);
}

/**
 * Main entry point.
 *
 * @returns {number} exit code
 */
function main() {
  const args = parseArgs();

  if (args.help) {
    printHelp();
    return 0;
  }

  // Initialize cache
  const cache = new XCResultCache();

  // Handle list mode
  if (args.listXcresults) {
    const xcresults = cache.list();
    if (args.json) {
      console.log(JSON.stringify(xcresults, null, 2));
    } else if (xcresults.length === 0) {
      console.log('No xcresult bundles found');
    } else {
      console.log(`Recent XCResult bundles (${xcresults.length}):`);
      console.log();
      for (const xc of xcresults) {
        console.log(`  ${xc.id}`);
        console.log(`    Created: ${xc.created}`);
        console.log(`    Size: ${xc.size_mb} MB`);
        console.log();
      }
    }
    return 0;
  }

  // Handle retrieval modes
  const xcresultId = args.getErrors || args.getWarnings || args.getLog || args.getAll;

  if (xcresultId) {
    const xcresultPath = cache.getPath(xcresultId);

    if (!xcresultPath || !fs.existsSync(xcresultPath)) {
      process.stderr.write(`Error: XCResult bundle not found: ${xcresultId}\n`);
      process.stderr.write('Use --list-xcresults to see available bundles\n');
      return 1;
    }

    // Load cached stderr for progressive disclosure
    const cachedStderr = cache.getStderr(xcresultId);
    const parser = new XCResultParser(xcresultPath, cachedStderr);

    // Get errors
    if (args.getErrors) {
      const errors = parser.getErrors();
      if (args.json) {
        console.log(JSON.stringify(errors, null, 2));
      } else {
        console.log(OutputFormatter.formatErrors(errors));
      }
      return 0;
    }

    // Get warnings
    if (args.getWarnings) {
      const warnings = parser.getWarnings();
      if (args.json) {
        console.log(JSON.stringify(warnings, null, 2));
      } else {
        console.log(OutputFormatter.formatWarnings(warnings));
      }
      return 0;
    }

    // Get log
    if (args.getLog) {
      const log = parser.getBuildLog();
      if (log) {
        console.log(OutputFormatter.formatLog(log));
      } else {
        process.stderr.write('No build log available\n');
        return 1;
      }
      return 0;
    }

    // Get all
    if (args.getAll) {
      const [errorCount, warningCount] = parser.countIssues();
      const errors = parser.getErrors();
      const warnings = parser.getWarnings();
      const buildLog = parser.getBuildLog();

      if (args.json) {
        const data = {
          xcresult_id: xcresultId,
          error_count: errorCount,
          warning_count: warningCount,
          errors,
          warnings,
          log_preview: buildLog ? buildLog.substring(0, 1000) : null,
        };
        console.log(JSON.stringify(data, null, 2));
      } else {
        console.log(`XCResult: ${xcresultId}`);
        console.log(`Errors: ${errorCount}, Warnings: ${warningCount}`);
        console.log();
        if (errors.length > 0) {
          console.log(OutputFormatter.formatErrors(errors, 10));
          console.log();
        }
        if (warnings.length > 0) {
          console.log(OutputFormatter.formatWarnings(warnings, 10));
          console.log();
        }
        if (buildLog) {
          console.log('Build Log (last 30 lines):');
          console.log(OutputFormatter.formatLog(buildLog, 30));
        }
      }
      return 0;
    }
  }

  // Build/test mode
  if (!args.project && !args.workspace) {
    // Try to auto-detect in current directory
    const cwd = process.cwd();
    const entries = fs.readdirSync(cwd);

    const workspaces = entries.filter((e) => e.endsWith('.xcworkspace'));
    const projects = entries.filter((e) => e.endsWith('.xcodeproj'));

    if (workspaces.length > 0) {
      args.workspace = path.join(cwd, workspaces[0]);
    } else if (projects.length > 0) {
      args.project = path.join(cwd, projects[0]);
    } else {
      process.stderr.write('Error: No project or workspace specified and none found in current directory\n');
      printHelp();
      return 1;
    }
  }

  // Initialize builder
  const builder = new BuildRunner({
    projectPath: args.project,
    workspacePath: args.workspace,
    scheme: args.scheme,
    configuration: args.configuration,
    simulator: args.simulator,
    cache,
  });

  // Execute build or test
  let success, resultId, stderr;

  if (args.test) {
    [success, resultId, stderr] = builder.test(args.suite);
  } else {
    [success, resultId, stderr] = builder.build(args.clean);
  }

  if (!resultId && !stderr) {
    process.stderr.write('Error: Build/test failed without creating xcresult or error output\n');
    return 1;
  }

  // Save stderr to cache for progressive disclosure
  if (resultId && stderr) {
    cache.saveStderr(resultId, stderr);
  }

  // Parse results
  const xcresultPath = resultId ? cache.getPath(resultId) : null;
  const parser = new XCResultParser(xcresultPath, stderr);
  const [errorCount, warningCount] = parser.countIssues();

  // Format output
  const status = success ? 'SUCCESS' : 'FAILED';

  // Collect errors on failure (used by all output modes)
  const errors = !success ? parser.getErrors() : null;
  const hints = errors ? OutputFormatter.generateHints(errors) : null;

  // Collect test info and failed tests when testing
  let testInfo = null;
  let failedTests = null;

  if (args.test && xcresultPath) {
    const testResults = parser.getTestResults();
    if (testResults) {
      testInfo = {
        total: testResults.total || 0,
        passed: testResults.passed || 0,
        failed: testResults.failed || 0,
        duration: testResults.duration || 0.0,
      };
    }
    if (!success) {
      failedTests = parser.getFailedTests();
    }
  }

  if (args.verbose) {
    // Verbose mode with error/warning details
    const verboseErrors = errorCount > 0 ? errors : null;
    const verboseWarnings = warningCount > 0 ? parser.getWarnings() : null;

    const output = OutputFormatter.formatVerbose({
      status,
      errorCount,
      warningCount,
      xcresultId: resultId || 'N/A',
      errors: verboseErrors,
      warnings: verboseWarnings,
      testInfo,
    });
    console.log(output);
  } else if (args.json) {
    // JSON mode
    const data = {
      success,
      xcresult_id: resultId || null,
      error_count: errorCount,
      warning_count: warningCount,
    };
    if (testInfo) data.test_info = testInfo;
    if (!success) {
      if (errors) data.errors = errors.slice(0, 10);
      if (failedTests) data.failed_tests = failedTests.slice(0, 10);
    }
    if (hints) data.hints = hints;
    console.log(JSON.stringify(data, null, 2));
  } else {
    // Minimal mode (default)
    const output = OutputFormatter.formatMinimal({
      status,
      errorCount,
      warningCount,
      xcresultId: resultId || 'N/A',
      testInfo,
      hints,
      errors,
      failedTests,
    });
    console.log(output);
  }

  return success ? 0 : 1;
}

process.exit(main());
