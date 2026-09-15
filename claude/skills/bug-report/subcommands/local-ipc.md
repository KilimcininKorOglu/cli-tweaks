---
name: local-ipc
description: >-
  Detect local trust-boundary failures in desktop and mobile applications:
  webview-to-native bridges, deep links and custom URL schemes, Unix sockets,
  named pipes, XPC, Binder and D-Bus endpoints, exported components, and
  privileged helpers. Use when asked to audit a desktop or mobile app.
---

# Local IPC and Desktop/Mobile Boundary Detection

You are performing a focused security assessment of local trust boundaries. This skill uses a three-phase approach: **recon** (map processes, channels, and entry points), **batched verify** (test each channel for peer identity and per-operation authorization), and **merge** (write confirmed findings to `BUG-REPORT.md`).

Run this subcommand only when the repository ships a desktop app, a mobile app, a webview host, a browser extension native host, or a local daemon. A pure server-side web project has no local IPC surface, and this subcommand reports nothing for it.

---

## What is a Local Boundary Failure

A local boundary failure occurs when a process accepts a request from a less privileged peer and acts on it as if the peer were itself. A local path, a process name, a package name, a claimed sender field, or a loopback address is not peer authentication.

The core pattern: *a privileged local endpoint decides authority from data the caller supplies instead of from an operating-system identity.*

### What a Local Boundary Failure IS

- A preload script exposing a generic `invoke(channel, ...args)` to remote web content
- A webview bridge whose origin is checked only at first navigation, not at invocation
- A Unix socket, named pipe, or loopback port that serves any local process without checking peer credentials
- An exported Android activity, service, receiver, or content provider that performs an app-internal operation
- A custom URL scheme handler that completes authentication, imports data, or switches accounts without binding to the current session
- A privileged helper that executes a command, path, or service name chosen by the caller
- An updater that verifies a signature over metadata rather than over the installed bytes
- A token file, credential store, or crash log readable by another OS user or another app profile

### What a Local Boundary Failure is NOT

Do not flag these:
- **Same-user data at rest without a named lower-privileged reader**: name the peer that gains access, or it is not a finding
- **A loopback endpoint with OS-backed peer identity and per-operation authorization**
- **A component that looks exported in source but is disabled in the final tracked manifest**
- **A bridge that remote content cannot reach**: no navigation path, no finding
- **A helper that re-normalizes and re-authorizes the final resource**, whatever the caller sent
- **A path check that looks racy but uses descriptor-relative, no-follow file APIs**

### Patterns That Prevent Local Boundary Failures

```javascript
// Electron — expose named operations, never a generic channel
contextBridge.exposeInMainWorld("api", {
  listProjects: () => ipcRenderer.invoke("projects:list"),
});
// main process: validate the sender on every handler
ipcMain.handle("projects:list", (event) => {
  if (event.senderFrame.url !== PACKAGED_ORIGIN) throw new Error("denied");
  return listProjects();
});
```

```xml
<!-- Android — keep app-internal components unexported -->
<service android:name=".SyncService" android:exported="false" />
```

```go
// Go — read the peer's OS identity from the socket
ucred, err := unix.GetsockoptUcred(fd, unix.SOL_SOCKET, unix.SO_PEERCRED)
if err != nil || ucred.Uid != allowedUID { return errDenied }
```

---

## Vulnerable vs. Secure Examples

### Electron — generic bridge

```javascript
// VULNERABLE: content picks the channel and the arguments
contextBridge.exposeInMainWorld("ipc", {
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
});

// SECURE: one function per operation, arguments validated in the main process
contextBridge.exposeInMainWorld("api", {
  openProject: (id) => ipcRenderer.invoke("project:open", String(id)),
});
```

### Deep link — unbound callback

```swift
// VULNERABLE: the link completes sign-in with whatever token it carries
func handle(url: URL) {
    let token = url.queryValue("token")
    session.complete(with: token)
}

// SECURE: bind to a one-time state value created by this session
func handle(url: URL) {
    guard let state = url.queryValue("state"), state == pendingState else { return }
    session.complete(with: url.queryValue("token"))
}
```

### Privileged helper — caller-selected target

```c
// VULNERABLE: the helper runs what the caller names
run_command(request->command, request->args);

// SECURE: fixed operation set, target re-derived and authorized in the helper
switch (request->op) {
  case OP_RELOAD_CONFIG: reload_config(SYSTEM_CONFIG_PATH); break;
  default: return DENIED;
}
```

---

## Execution

### Phase 1: Map Processes, Channels, and Entry Points

Launch a subagent with the following instructions:

> **Goal**: Inventory every local process boundary, channel, and externally reachable entry point. Return findings in your response. If the project ships no desktop app, mobile app, webview host, or local daemon, say so and stop.
>
> **What to search for**:
>
> 1. **Runtime hosts**: `electron`, `tauri`, `nw.js`, `WKWebView`, `WebView`, `CEF`, `QtWebEngine`, native app targets, `*.xcodeproj`, `build.gradle` app modules
> 2. **Bridges**: `contextBridge`, `preload`, `ipcMain`, `ipcRenderer`, `postMessage` handlers, `addJavascriptInterface`, `WKScriptMessageHandler`, Tauri `#[command]` and its allowlist or capability files
> 3. **Local channels**: Unix sockets, named pipes, XPC services, Binder services, D-Bus names, `localhost`/`127.0.0.1` listeners, shared memory, native-messaging host manifests
> 4. **Entry points from other apps**: Android `intent-filter` and `android:exported`, iOS `CFBundleURLSchemes` and universal links, Windows protocol handlers, `.desktop` `MimeType` entries, file associations, drag-and-drop and clipboard handlers
> 5. **Privileged components**: `SMJobBless` helpers, `launchd` and `systemd` units, Windows services, installers, updaters, `setuid` binaries, polkit actions
> 6. **Security settings**: `contextIsolation`, `nodeIntegration`, `sandbox`, `webSecurity`, `allowFileAccessFromFileURLs`, entitlements, `android:allowBackup`, ATS exceptions
>
> **Output format** — return in your response:
>
> ```markdown
> # Local IPC Recon: [Project Name]
>
> ## Summary
> Platforms shipped: [Electron / Tauri / iOS / Android / Linux daemon / none]
> Found [N] channels and [M] external entry points.
>
> ## Channels and Entry Points
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Kind**: [bridge / socket / exported component / URL scheme / helper / updater]
> - **Privilege of the serving process**: [user / elevated / root / system]
> - **Realistic caller**: [remote web content / another app / another OS user / sandboxed child]
> - **Operations offered**: [list]
> - **Peer identity mechanism seen**: [peer credentials / entitlement / signature / none]
> - **Code snippet**:
>   ```
>   [the declaration or handler]
>   ```
> ```

### Phase 2: Batched Verify — Test Identity and Authorization

After Phase 1 completes, count numbered channels. If 3 or fewer, use a single subagent. Otherwise split them into batches of up to 3 and run them through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.

> **For each channel, answer these in order**:
>
> 1. **Reachability**: can the named caller actually reach it? For a bridge, find the navigation path that loads remote, redirected, popup, or subframe content. For an exported component, read the final tracked manifest.
> 2. **Peer identity**: does the serving side read an operating-system identity — peer credentials, audit token, signature, entitlement, package signature — or does it trust a field in the message?
> 3. **Per-operation authorization**: is each operation authorized against the final principal and the final resource, or is the channel authorized once at connect time?
> 4. **Argument handling**: can the caller select the command, path, URL, account, or service that the privileged side acts on? Follow the value to its final sink, after normalization.
> 5. **Session binding**: for deep links and callbacks, is the action bound to a one-time value created by the current session, and does it expire?
> 6. **Lifecycle**: does the data or authority survive logout, account switch, backup, or restore?
> 7. **Result**: what does the caller obtain — code execution, another account's data, a privileged file write, a stolen authentication callback?
>
> **Classification**:
> - **Vulnerable**: a named lower-privileged caller reaches a privileged operation with a concrete result
> - **Likely Vulnerable**: the path exists with one unresolved packaging or navigation question
> - **Not Vulnerable**: peer identity and per-operation authorization both hold, or the caller cannot reach the channel
> - **Needs Manual Review**: the decisive fact is signing, a merged manifest, an installed ACL, or device policy that the repository does not contain
>
> **Output format** — return in your response:
>
> ```markdown
> # Local IPC Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Attacker capability**: [remote page in a webview / another installed app / lower-privileged OS user]
> - **Boundary crossed**: [renderer → main / app → app / user → root]
> - **Issue**: [missing peer identity, generic operation selection, unbound callback, ...]
> - **Path**: [entry → handler → privileged sink]
> - **Result**: [what the caller gains]
> - **Remediation**: [named operations, peer credential check, session binding, manifest change]
> ```

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries.

**Severity mapping**:
- Remote content or a low-privileged local caller reaches arbitrary privileged code execution → CRITICAL
- Cross-user or cross-app data access, privileged helper abuse, stolen authentication callback, arbitrary privileged file write → HIGH
- Limited unauthorized local action, exported component leaking app-internal state, data surviving logout → MEDIUM
- Narrow disclosure or mutation under unusual conditions → LOW

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1. Phase 3 runs AFTER all batches.
- Batch size: 3 channels per subagent. If 1-3 total, single subagent. Run the batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Name the attacker before writing a finding. "A local user could read this file" is not a boundary crossing unless a less privileged principal is named.
- Validate a webview origin at invocation time. A check that runs only on first navigation misses every later redirect.
- Read the final tracked manifest, not an intermediate one. A merged manifest can export a component the module file marks private.
- Signing, entitlements, installed ACLs, and device policy usually live outside the repository. Record them as unresolved instead of assuming either outcome.
- Never install, launch, or drive the packaged application to prove a finding. Read the source and the manifests.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
