/**
 * Xcode build automation module.
 *
 * Provides structured, modular access to xcodebuild and xcresult functionality.
 */

const { BuildRunner } = require('./builder');
const { XCResultCache } = require('./cache');
const { Config } = require('./config');
const { OutputFormatter } = require('./reporter');
const { XCResultParser } = require('./xcresult');

module.exports = {
  BuildRunner,
  Config,
  OutputFormatter,
  XCResultCache,
  XCResultParser,
};
