---
name: websocket
description: >-
  Detect WebSocket security vulnerabilities using a three-phase approach:
  find WebSocket handlers and connection setup, verify missing protections
  (origin validation, authentication, message injection, unencrypted transport),
  then merge confirmed findings. Use when asked to audit WebSocket security.
---

# WebSocket Security Scan

You are performing a focused security assessment to find WebSocket security vulnerabilities in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all WebSocket handlers and connection setup) then **verify** (confirm whether configurations allow hijacking, injection, or unauthorized access) then **merge** (write confirmed findings).

---

## What is WebSocket Insecurity

WebSocket provides persistent bidirectional communication, but it does not inherit all HTTP security mechanisms. Browsers do not enforce same-origin policy on WebSocket connections the way they do for XHR/fetch. The core pattern: *a WebSocket endpoint accepts connections without verifying the origin or authenticating the client, enabling cross-site WebSocket hijacking and unauthorized data access.*

### What WebSocket Insecurity IS

- Missing origin validation on WebSocket upgrade — any website can connect
- No authentication on WebSocket handshake — anonymous access to private data
- Cross-site WebSocket hijacking: attacker page opens WebSocket to victim's server using victim's cookies
- Message injection: unsanitized WebSocket messages used in SQL, shell, or template operations
- Unencrypted `ws://` in production — data visible to network attackers
- Missing message schema validation — malformed messages cause crashes or unexpected behavior
- No rate limiting on WebSocket messages — message flood DoS

### What WebSocket Insecurity is NOT

Do not flag these:

- **Development ws:// on localhost**: Using `ws://localhost` in development configuration
- **Public broadcast channels**: WebSocket channels intentionally public (live scores, stock tickers, public chat)
- **Token-based auth in URL**: Authentication via query parameter token is a valid WebSocket pattern (cookies are problematic for cross-origin WebSocket)
- **Server-to-server WebSocket**: Internal service communication on private networks
- **Socket.IO with default security**: Socket.IO 4.x enables CORS validation by default

### Patterns That Prevent WebSocket Exploits

When you see these patterns, the code is likely **not vulnerable**:

**1. Origin validation on upgrade**
```go
var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool {
        origin := r.Header.Get("Origin")
        return origin == "https://app.example.com"
    },
}
```

**2. Authentication on connection**
```javascript
wss.on('connection', (ws, req) => {
  const token = new URL(req.url, 'http://localhost').searchParams.get('token');
  if (!verifyToken(token)) {
    ws.close(1008, 'Unauthorized');
    return;
  }
  // ... handle authenticated connection
});
```

**3. Message schema validation**
```javascript
ws.on('message', (raw) => {
  const result = messageSchema.safeParse(JSON.parse(raw));
  if (!result.success) { ws.close(1003, 'Invalid message'); return; }
  handleMessage(result.data);
});
```

---

## Vulnerable vs. Secure Examples

### Go — Missing Origin Validation

```go
// VULNERABLE: Accepts connections from any origin
var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool {
        return true  // Any website can connect!
    },
}

// SECURE: Validate origin
var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool {
        origin := r.Header.Get("Origin")
        return origin == "https://app.example.com"
    },
}
```

### Node.js — Missing Authentication

```javascript
// VULNERABLE: No auth check — anyone can connect and receive data
wss.on('connection', (ws, req) => {
  ws.on('message', (msg) => {
    handleMessage(ws, msg);
  });
  sendUserData(ws);  // Sends private data to unauthenticated client
});

// SECURE: Verify auth on connection
wss.on('connection', (ws, req) => {
  const token = new URL(req.url, 'http://localhost').searchParams.get('token');
  if (!verifyToken(token)) {
    ws.close(1008, 'Unauthorized');
    return;
  }
  ws.on('message', (msg) => {
    handleMessage(ws, msg);
  });
  sendUserData(ws);
});
```

### Message Injection

```javascript
// VULNERABLE: WebSocket message used directly in database query
ws.on('message', (msg) => {
  const data = JSON.parse(msg);
  db.query(`SELECT * FROM ${data.table} WHERE id = ${data.id}`);  // SQL injection!
});

// SECURE: Validate and parameterize
ws.on('message', (msg) => {
  const data = JSON.parse(msg);
  const allowed = ['users', 'products'];
  if (!allowed.includes(data.table)) return;
  db.query('SELECT * FROM ?? WHERE id = ?', [data.table, data.id]);
});
```

### Socket.IO — Permissive CORS

```javascript
// VULNERABLE: Accepts connections from any origin
const io = require('socket.io')(server, {
  cors: { origin: '*' }
});

// SECURE: Restrict origins
const io = require('socket.io')(server, {
  cors: { origin: 'https://app.example.com' }
});
```

### Unencrypted WebSocket

```javascript
// VULNERABLE: Unencrypted WebSocket in production
const ws = new WebSocket('ws://api.example.com/ws');

// SECURE: Use wss:// in production
const ws = new WebSocket('wss://api.example.com/ws');
```

---

## Execution

### Phase 1: Find WebSocket Handlers

Launch a subagent with the following instructions:

> **Goal**: Find every WebSocket handler, connection setup, and related configuration in the codebase. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the WebSocket library/framework in use.
>
> **What to search for — WebSocket patterns**:
>
> 1. **WebSocket server setup**:
>    - `WebSocket`, `WebSocketServer`, `ws.Server`, `new WebSocket.Server`
>    - `socket.io`, `io(`, `io.connect(`, `Socket(`
>    - `gorilla/websocket`, `Upgrader`, `websocket.Upgrade`
>    - `SignalR`, `Hub`, `MapHub`
>    - `channels` (Django Channels), `ActionCable` (Rails)
>
> 2. **Connection and message handlers**:
>    - `on('connection'`, `on('connect'`, `onmessage`, `on('message'`
>    - `handleMessage`, `handleConnection`, `onOpen`, `onClose`
>
> 3. **Origin and auth configuration**:
>    - `CheckOrigin`, `verifyClient`, `allowedOrigins`, `cors`
>    - Token extraction from URL query params or headers during upgrade
>    - Cookie-based auth on WebSocket handshake
>
> 4. **Client-side WebSocket usage**:
>    - `new WebSocket('ws://`, `new WebSocket('wss://`
>    - `io.connect(`, `io(` with URL arguments
>    - Check for `ws://` (unencrypted) in production code
>
> **What to skip**:
> - Test/mock WebSocket servers in test files
> - WebSocket documentation or README references
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # WebSocket Recon: [Project Name]
>
> ## Summary
> Found [N] WebSocket handler sites. Library: [ws / socket.io / gorilla / SignalR / etc.].
>
> ## Handler Sites
>
> ### 1. [Descriptive name — e.g., "Chat WebSocket server without origin check"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Library / framework**: [ws / socket.io / gorilla / etc.]
> - **Handler type**: [server setup / connection handler / message handler / client connection]
> - **Origin validation**: [present / absent / permissive]
> - **Authentication**: [token / cookie / none detected]
> - **Transport**: [wss:// / ws:// / configurable]
> - **Code snippet**:
>   ```
>   [the WebSocket handler code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm WebSocket Vulnerabilities

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which WebSocket endpoints handle sensitive data.
>
> **For each WebSocket handler, verify whether it creates an exploitable vulnerability**:
>
> 1. **Missing origin validation**: Does the WebSocket upgrade accept any origin?
>    - `CheckOrigin: func(...) bool { return true }` → VULNERABLE
>    - No `verifyClient` callback → depends on framework defaults
>    - Socket.IO with `cors: { origin: '*' }` → VULNERABLE
>    - If missing origin check + cookie-based auth → cross-site WebSocket hijacking → VULNERABLE
>
> 2. **Missing authentication**: Can anonymous clients connect and access data?
>    - No token/session verification on connection event
>    - Data sent immediately after connection without auth check
>    - If private data accessible without auth → VULNERABLE
>
> 3. **Message injection**: Are WebSocket messages used unsafely?
>    - Message content in SQL queries, shell commands, template rendering
>    - `JSON.parse()` without schema validation followed by dynamic operations
>    - If message content reaches injection sink → VULNERABLE
>
> 4. **Unencrypted transport**: Is `ws://` used for production connections?
>    - Client code connecting via `ws://` to non-localhost
>    - Server configuration without TLS termination
>    - If production traffic over `ws://` → LIKELY VULNERABLE
>
> 5. **Missing message validation**: Are messages accepted without schema validation?
>    - No type checking, no schema validation (Zod, Joi, etc.)
>    - Direct property access on parsed message without validation
>    - If malformed messages can cause crashes → LIKELY VULNERABLE
>
> **Classification**:
> - **Vulnerable**: Confirmed WebSocket vulnerability with clear exploit path (cross-site hijacking, injection, unauthenticated data access).
> - **Likely Vulnerable**: Missing protection that is context-dependent (ws:// in production, no message validation).
> - **Not Vulnerable**: Proper origin validation, authentication, and message validation in place.
> - **Needs Manual Review**: Auth may be handled at proxy/gateway level or in middleware not visible in handler code.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # WebSocket Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / scope**: [WebSocket path or handler]
> - **Issue**: [e.g., "WebSocket server accepts connections from any origin with cookie auth — enables cross-site WebSocket hijacking"]
> - **Vulnerability type**: [missing origin check / missing auth / message injection / unencrypted transport]
> - **Impact**: Cross-site WebSocket hijacking, unauthorized data access, SQL/command injection via messages
> - **Remediation**: Validate origin against allowlist, require token auth on upgrade, validate message schema, use wss://
> - **Dynamic test**: [e.g., "Open WebSocket from attacker.com to target server — connection should be rejected"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Cross-site WebSocket hijacking (missing origin + cookie auth) on data endpoint → CRITICAL
> - Unauthenticated WebSocket access to private data → CRITICAL
> - Message injection (SQL, command, template) → HIGH
> - Missing origin validation without cookie auth → HIGH
> - Unencrypted ws:// in production → MEDIUM
> - Missing message schema validation → MEDIUM
> - Missing rate limiting on WebSocket messages → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full vulnerability details and a dynamic test
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all WebSocket handlers regardless of whether they are secure. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each handler, determine whether it creates an exploitable vulnerability.
- Cross-site WebSocket hijacking is the most critical WebSocket vulnerability. Unlike XHR, browsers DO send cookies with WebSocket upgrade requests, and same-origin policy does NOT block cross-origin WebSocket connections. If a server uses cookies for auth and does not validate the Origin header, any website can hijack the connection.
- Token-based auth via query parameter is the recommended pattern for WebSocket. Cookies are problematic because they are sent automatically with cross-origin upgrade requests.
- `ws://` is the WebSocket equivalent of `http://` — all traffic is plaintext. Always use `wss://` in production.
- Socket.IO 4.x does NOT allow cross-origin connections by default (changed from v2/v3). However, explicit `cors: { origin: '*' }` re-enables the vulnerability.
- Message validation is as important for WebSocket as input validation is for HTTP. Every message from a WebSocket client is user input and must be treated as untrusted.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
