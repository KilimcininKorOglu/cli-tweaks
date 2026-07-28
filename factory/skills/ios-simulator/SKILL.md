---
name: ios-simulator
description: >
  This skill MUST be invoked when the user says "simulator", "simülatör",
  "iOS test", "simulator boot", "simctl", "app launch", "ekran analiz",
  "screen map", "accessibility audit", "erişilebilirlik", "push notification",
  "visual diff", "build and test", "xcode build", "simulator oluştur",
  "simulator sil", "app yükle", or any variation requesting iOS simulator
  automation, app testing, building, or device management. Provides 21
  production scripts for semantic UI navigation, build automation,
  accessibility testing, and simulator lifecycle management.
argument-hint: "<script-name> [options]"
---

# iOS Simulator Automation

Build, test, and automate iOS applications using accessibility-driven semantic navigation. Find and interact with elements by meaning, not pixel coordinates.

## Quick Start

```bash
# 1. Check environment
bash ${CLAUDE_SKILL_DIR}/scripts/sim_health_check.sh

# 2. Launch app
node ${CLAUDE_SKILL_DIR}/scripts/appLauncher.js --launch com.example.app

# 3. Map screen elements
node ${CLAUDE_SKILL_DIR}/scripts/screenMapper.js

# 4. Tap button by text
node ${CLAUDE_SKILL_DIR}/scripts/navigator.js --find-text "Login" --tap

# 5. Enter text in field
node ${CLAUDE_SKILL_DIR}/scripts/navigator.js --find-type TextField --enter-text "user@test.com"

# 6. Check accessibility
node ${CLAUDE_SKILL_DIR}/scripts/accessibilityAudit.js
```

All scripts support `--help` for options and `--json` for machine-readable output.

## Navigation Priority

Always prefer the accessibility tree over screenshots:

| Method | Token Cost | Reliability | Use When |
|--------|-----------|-------------|----------|
| `screenMapper.js` | ~10 tokens | High | Default — see what's on screen |
| `navigator.js --find-*` | ~5 tokens | High | Interact with elements |
| Screenshot | 1,600-6,300 tokens | Medium | Visual verification, bug reports, diff only |

## 21 Scripts by Category

### Build and Development (2)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `buildAndTest.js` | Xcode build + test with result parsing | `--project`, `--scheme`, `--clean`, `--test` |
| `logMonitor.js` | Real-time log monitoring with filtering | `--app`, `--severity`, `--follow`, `--duration` |

### Navigation and Interaction (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `screenMapper.js` | Analyze current screen, list elements | `--verbose`, `--hints` |
| `navigator.js` | Find + interact with elements semantically | `--find-text`, `--find-type`, `--find-id`, `--tap`, `--enter-text` |
| `gesture.js` | Swipes, scrolls, pinches, long press | `--swipe`, `--scroll`, `--pinch`, `--refresh` |
| `keyboard.js` | Text input + hardware buttons | `--type`, `--key`, `--button`, `--clear`, `--dismiss` |
| `appLauncher.js` | App lifecycle (launch, terminate, install) | `--launch`, `--terminate`, `--install`, `--open-url` |

### Testing and Analysis (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `accessibilityAudit.js` | WCAG compliance check | `--verbose`, `--output` |
| `visualDiff.js` | Screenshot pixel comparison | `--threshold`, `--output`, `--details` |
| `testRecorder.js` | Auto-document test execution | `--test-name`, `--output` |
| `appStateCapture.js` | Debugging snapshot (screen + logs + hierarchy) | `--app-bundle-id`, `--output` |
| `sim_health_check.sh` | Environment verification | (no options) |

### Permissions and Advanced (4)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `clipboard.js` | Clipboard management for paste testing | `--copy`, `--expected` |
| `statusBar.js` | Override status bar appearance | `--preset`, `--time`, `--battery-level` |
| `pushNotification.js` | Simulated push notifications | `--bundle-id`, `--title`, `--body`, `--payload` |
| `privacyManager.js` | Grant/revoke app permissions (13 services) | `--bundle-id`, `--grant`, `--revoke`, `--reset` |

### Device Lifecycle (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `simctlBoot.js` | Boot simulator | `--udid`, `--name`, `--wait-ready`, `--all`, `--type` |
| `simctlShutdown.js` | Shutdown simulator | `--udid`, `--name`, `--verify`, `--all` |
| `simctlCreate.js` | Create new simulator | `--device`, `--runtime`, `--name` |
| `simctlDelete.js` | Delete simulator | `--udid`, `--name`, `--yes`, `--old N` |
| `simctlErase.js` | Factory reset (preserves UDID) | `--udid`, `--name`, `--verify`, `--booted` |

## Common Patterns

**Auto-UDID:** Most scripts auto-detect the booted simulator. No need to specify `--udid` unless multiple are booted.

**Device name:** Use names instead of UDIDs: `--name "iPhone 16 Pro"` — scripts resolve automatically.

**Batch operations:** `--all` for all simulators, `--type iPhone` for device type filtering.

**Output modes:**
- Default: 3-5 lines (token-efficient)
- `--verbose`: full details
- `--json`: machine-readable for CI/CD

**Screenshot sizing:** `half` (default, ~1.6K tokens), `quarter` (~800 tokens), `full` (~5K tokens). Use `quarter` for quick checks.

## Typical Workflows

### Login Flow Test

```bash
node ${CLAUDE_SKILL_DIR}/scripts/appLauncher.js --launch com.example.app
node ${CLAUDE_SKILL_DIR}/scripts/screenMapper.js
node ${CLAUDE_SKILL_DIR}/scripts/navigator.js --find-type TextField --index 0 --enter-text "user@test.com"
node ${CLAUDE_SKILL_DIR}/scripts/navigator.js --find-type SecureTextField --enter-text "password"
node ${CLAUDE_SKILL_DIR}/scripts/navigator.js --find-text "Login" --tap
node ${CLAUDE_SKILL_DIR}/scripts/accessibilityAudit.js
```

### Permission Test

```bash
node ${CLAUDE_SKILL_DIR}/scripts/privacyManager.js --bundle-id com.example.app --grant camera,location
# Test app with permissions...
node ${CLAUDE_SKILL_DIR}/scripts/privacyManager.js --bundle-id com.example.app --revoke camera,location
```

### CI/CD Device Lifecycle

```bash
DEVICE_ID=$(node ${CLAUDE_SKILL_DIR}/scripts/simctlCreate.js --device "iPhone 16 Pro" --json | jq -r '.new_udid')
node ${CLAUDE_SKILL_DIR}/scripts/buildAndTest.js --project MyApp.xcodeproj --test
node ${CLAUDE_SKILL_DIR}/scripts/simctlDelete.js --udid $DEVICE_ID --yes
```

## Quick Diagnostics

| Problem | Solution |
|---------|----------|
| Script can't find simulator | Run `sim_health_check.sh` — is any simulator booted? |
| Navigator can't find element | Run `screenMapper.js --verbose` to see all elements |
| Build fails with scheme error | Check `--scheme` matches Xcode exactly (case-sensitive) |
| Permission grant fails | Use exact service names: `camera`, `location`, `photos`, `contacts` |
| Screenshot too expensive | Use `--screenshot-size quarter` for minimal token cost |
| IDB commands fail | IDB is optional — install with `brew tap facebook/fb && brew install idb-companion` |

## Requirements

- macOS 12+
- Xcode Command Line Tools (`xcode-select --install`)
- Python 3
- IDB (optional — `brew tap facebook/fb && brew install idb-companion`)
- Pillow (optional — `pip3 install pillow` for visualDiff.js)

## References

| Document | Topic |
|----------|-------|
| `references/simctl_quick.md` | simctl command reference |
| `references/idb_quick.md` | IDB command reference |
| `references/accessibility_checklist.md` | WCAG compliance checklist |
| `references/test_patterns.md` | Testing patterns and strategies |
| `references/troubleshooting.md` | Common issues and fixes |

## Design Principles

**Semantic navigation:** Find elements by meaning (text, type, accessibility ID) not pixel coordinates. Survives UI redesigns.

**Token efficiency:** 96% reduction vs raw tools. Default output is 3-5 lines.

**Accessibility-first:** Built on iOS accessibility APIs. More reliable than pixel coordinates and better for all users.

**Zero configuration:** Works immediately on any macOS with Xcode installed.

**Structured output:** JSON and formatted text, not raw logs. Easy to parse in CI/CD.
