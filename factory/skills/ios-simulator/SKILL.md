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
bash scripts/sim_health_check.sh

# 2. Launch app
python scripts/app_launcher.py --launch com.example.app

# 3. Map screen elements
python scripts/screen_mapper.py

# 4. Tap button by text
python scripts/navigator.py --find-text "Login" --tap

# 5. Enter text in field
python scripts/navigator.py --find-type TextField --enter-text "user@test.com"

# 6. Check accessibility
python scripts/accessibility_audit.py
```

All scripts support `--help` for options and `--json` for machine-readable output.

## Navigation Priority

Always prefer the accessibility tree over screenshots:

| Method | Token Cost | Reliability | Use When |
|--------|-----------|-------------|----------|
| `screen_mapper.py` | ~10 tokens | High | Default — see what's on screen |
| `navigator.py --find-*` | ~5 tokens | High | Interact with elements |
| Screenshot | 1,600-6,300 tokens | Medium | Visual verification, bug reports, diff only |

## 21 Scripts by Category

### Build and Development (2)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `build_and_test.py` | Xcode build + test with result parsing | `--project`, `--scheme`, `--clean`, `--test` |
| `log_monitor.py` | Real-time log monitoring with filtering | `--app`, `--severity`, `--follow`, `--duration` |

### Navigation and Interaction (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `screen_mapper.py` | Analyze current screen, list elements | `--verbose`, `--hints` |
| `navigator.py` | Find + interact with elements semantically | `--find-text`, `--find-type`, `--find-id`, `--tap`, `--enter-text` |
| `gesture.py` | Swipes, scrolls, pinches, long press | `--swipe`, `--scroll`, `--pinch`, `--refresh` |
| `keyboard.py` | Text input + hardware buttons | `--type`, `--key`, `--button`, `--clear`, `--dismiss` |
| `app_launcher.py` | App lifecycle (launch, terminate, install) | `--launch`, `--terminate`, `--install`, `--open-url` |

### Testing and Analysis (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `accessibility_audit.py` | WCAG compliance check | `--verbose`, `--output` |
| `visual_diff.py` | Screenshot pixel comparison | `--threshold`, `--output`, `--details` |
| `test_recorder.py` | Auto-document test execution | `--test-name`, `--output` |
| `app_state_capture.py` | Debugging snapshot (screen + logs + hierarchy) | `--app-bundle-id`, `--output` |
| `sim_health_check.sh` | Environment verification | (no options) |

### Permissions and Advanced (4)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `clipboard.py` | Clipboard management for paste testing | `--copy`, `--expected` |
| `status_bar.py` | Override status bar appearance | `--preset`, `--time`, `--battery-level` |
| `push_notification.py` | Simulated push notifications | `--bundle-id`, `--title`, `--body`, `--payload` |
| `privacy_manager.py` | Grant/revoke app permissions (13 services) | `--bundle-id`, `--grant`, `--revoke`, `--reset` |

### Device Lifecycle (5)

| Script | Purpose | Key Options |
|--------|---------|-------------|
| `simctl_boot.py` | Boot simulator | `--udid`, `--name`, `--wait-ready`, `--all`, `--type` |
| `simctl_shutdown.py` | Shutdown simulator | `--udid`, `--name`, `--verify`, `--all` |
| `simctl_create.py` | Create new simulator | `--device`, `--runtime`, `--name` |
| `simctl_delete.py` | Delete simulator | `--udid`, `--name`, `--yes`, `--old N` |
| `simctl_erase.py` | Factory reset (preserves UDID) | `--udid`, `--name`, `--verify`, `--booted` |

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
python scripts/app_launcher.py --launch com.example.app
python scripts/screen_mapper.py
python scripts/navigator.py --find-type TextField --index 0 --enter-text "user@test.com"
python scripts/navigator.py --find-type SecureTextField --enter-text "password"
python scripts/navigator.py --find-text "Login" --tap
python scripts/accessibility_audit.py
```

### Permission Test

```bash
python scripts/privacy_manager.py --bundle-id com.example.app --grant camera,location
# Test app with permissions...
python scripts/privacy_manager.py --bundle-id com.example.app --revoke camera,location
```

### CI/CD Device Lifecycle

```bash
DEVICE_ID=$(python scripts/simctl_create.py --device "iPhone 16 Pro" --json | jq -r '.new_udid')
python scripts/build_and_test.py --project MyApp.xcodeproj --test
python scripts/simctl_delete.py --udid $DEVICE_ID --yes
```

## Quick Diagnostics

| Problem | Solution |
|---------|----------|
| Script can't find simulator | Run `sim_health_check.sh` — is any simulator booted? |
| Navigator can't find element | Run `screen_mapper.py --verbose` to see all elements |
| Build fails with scheme error | Check `--scheme` matches Xcode exactly (case-sensitive) |
| Permission grant fails | Use exact service names: `camera`, `location`, `photos`, `contacts` |
| Screenshot too expensive | Use `--screenshot-size quarter` for minimal token cost |
| IDB commands fail | IDB is optional — install with `brew tap facebook/fb && brew install idb-companion` |

## Requirements

- macOS 12+
- Xcode Command Line Tools (`xcode-select --install`)
- Python 3
- IDB (optional — `brew tap facebook/fb && brew install idb-companion`)
- Pillow (optional — `pip3 install pillow` for visual_diff.py)

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
