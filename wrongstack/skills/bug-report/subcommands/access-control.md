# Access Control Security Audit

This subcommand covers both **IDOR** (horizontal privilege escalation — authenticated user A accessing user B's resources) and **missing authentication / broken function-level authorization** (unauthenticated access + vertical privilege escalation — regular user accessing admin functions). Uses a two-phase subagent approach.

## Command

```bash
/bug-report access-control
```

---

## What This Covers

### Class 1: IDOR (Insecure Direct Object Reference)
The application uses a user-supplied identifier to access an object **without verifying the requesting user owns or is authorized for that specific object**.

- Changing `/api/orders/1001` to `/api/orders/1002` to see another user's order
- Deleting `DELETE /api/documents/555` for a document you don't own
- Modifying `{"account_id": 789}` to transfer from someone else's account

### Class 2: Unauthenticated Sensitive Endpoint
An endpoint performs a sensitive action with **no login required at all**.

- `GET /api/admin/users` returning all users with no token
- `DELETE /api/admin/users/5` deleting users anonymously

### Class 3: Broken Function-Level Authorization
Authenticated but **no role/permission check** on privileged endpoint. Any logged-in user can call admin functions.

### Class 4: Bypassable Authorization
Auth logic exists but can be bypassed — role check only on GET not DELETE, check skipped via `except:` list, middleware mounted after the route.

---

## Authorization Patterns That Prevent IDOR

```python
# Query scoped to current user
Order.objects.filter(id=order_id, user=request.user)       # Django
current_user.orders.find(params[:id])                       # Rails
Order.findOne({ _id: orderId, userId: req.user.id })        # Mongoose

# Explicit ownership check after fetch
order = Order.find(order_id)
if order.user_id != current_user.id:
    raise Forbidden
```

## Authorization Patterns That Prevent Missing Auth

```javascript
// Express: route group with auth + role middleware
router.use('/admin', auth, requireRole('admin'));

// Flask
@app.route('/admin/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        abort(403)
```

---

## Execution

### Phase 1: Recon — Map Endpoints and Object Access Patterns

Launch a subagent with the following instructions:

> **Goal**: Build a complete map of (1) all endpoints and their authentication/authorization posture, and (2) all endpoints that fetch, update, or delete objects by user-supplied identifier. Return findings in your response.
>
> **Part A — Endpoint inventory for auth/role checks**:
>
> Find every HTTP handler, REST endpoint, GraphQL mutation/query, RPC method, or WebSocket handler. For each:
> - Route/method/path
> - Authentication middleware present (yes/no)
> - Role/permission check present (yes/no)
> - Sensitivity level (admin/privileged/public)
>
> Collect the role/permission system: role constants, decorators (`@login_required`, `@admin_required`, `requireRole`), policy/gate objects, in-handler role checks.
>
> Flag sensitive endpoints: paths with `/admin`, `/management`, `/internal`, `/superadmin`; user management; system configuration; financial data for all users; aggregate data.
>
> **Part B — Object access patterns for IDOR**:
>
> Find every endpoint that retrieves, updates, or deletes a specific object using a user-supplied ID:
> - Path params: `:id`, `{id}`, `<int:id>`
> - ORM lookups: `find(id)`, `findById()`, `objects.get()`, `findOne()`, `findUnique()`
> - Raw queries: `WHERE id = ?`
> - Request body IDs: `req.body.userId`, `request.data['account_id']`
> - GraphQL resolvers accepting ID arguments
>
> **What to ignore**: intentionally public endpoints, static assets, `/health`/`/ping`, endpoints where only the authenticated user's own ID is used.
>
> **Part C — Privilege escalation patterns**:
>
> Check for paths where an attacker can elevate from one privilege level to a higher one:
> - **Role hierarchy traversal**: Can a user with role "editor" access "admin" functions by manipulating role parameters?
> - **Decorator/middleware stacking bypass**: Are there routes where auth middleware is applied but role check is missing?
> - **Horizontal to vertical escalation**: Can accessing another user's data (IDOR) also grant elevated privileges (e.g., accessing admin user's settings)?
> - **Admin function access without role check**: Sensitive operations (user deletion, config change, bulk export) that check authentication but not authorization level
> - **Parameter-based role switching**: Can `role=admin` or `isAdmin=true` be injected in request body to elevate privileges?
>
> **Output format** — return findings in your response:
>
> ```markdown
> # Access Control Recon: [Project Name]
>
> ## Auth System
> - Auth mechanism: [JWT / session / API key]
> - Auth decorators: [@login_required, auth, ...]
> - Roles identified: [admin, user, ...]
>
> ## Endpoint Inventory (Auth/Role)
> ### 1. [name] — METHOD /path — auth: yes/no — role check: yes/no — sensitivity: admin/standard
>
> ## Object Access Candidates (IDOR)
> ### 1. [name] — File: path:lines — Endpoint: METHOD /path/:id — Operation: read/update/delete — Object: [model]
> ```

### Phase 2: Batched Verify — Check Both IDOR and Auth/Role Issues

After Phase 1 completes, count the total numbered items from both Part A (endpoints) and Part B (IDOR candidates).

**If 3 or fewer items total**: Launch a single subagent with all items (skip batching).

**If more than 3 items**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned items from Phase 1):

> **For IDOR candidates (Part B from Phase 1)**, check:
>
> 1. Is the DB query scoped to the authenticated user? (`filter(id=x, user=request.user)`)
> 2. Is there an explicit ownership check after fetch? (`if resource.user_id != current_user.id`)
> 3. Is there an authorization policy/middleware that verifies ownership?
> 4. Are mutation endpoints (PUT/DELETE) checked the same as read endpoints?
> 5. Are bulk/batch endpoints checked per-item?
>
> **For auth/role candidates (Part A from Phase 1)**, check:
>
> 1. Is authentication actually required? Trace middleware chain — confirm it runs BEFORE the handler.
> 2. Is a role/permission check present on privileged endpoints?
> 3. Does the check apply to ALL HTTP methods (not just GET)?
> 4. Is the check conditional on user-controlled input?
> 5. Is the route accidentally outside the protected group?
>
> **Classification**:
> - **Vulnerable**: No ownership check (IDOR) / no auth or role check (missing-auth).
> - **Likely Vulnerable**: Check exists but incomplete, bypassable, or conditional.
> - **Not Vulnerable**: Proper checks in place.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Access Control Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint**: [METHOD /path]
> - **Type**: [IDOR / Missing Auth / Missing Role Check]
> - **Issue**: [description]
> - **Impact**: [What attacker can access/do]
> - **Remediation**: [ownership check, auth middleware, etc.]
> - **Dynamic test**: [curl command or payload]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - IDOR on financial, PII, or health data → HIGH
> - IDOR on non-sensitive data → MEDIUM
> - IDOR with write/delete capability → HIGH
> - Unauthenticated admin/data-mutating endpoint → CRITICAL-HIGH
> - Authenticated but missing role check on admin function → HIGH
> - Missing check on non-sensitive endpoint → MEDIUM

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full taint trace and a dynamic test command or payload
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 items per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Trace the full code path: route → middleware → controller → service → data access.
- Middleware order matters: middleware registered AFTER the route handler does not protect it.
- A missing check on one HTTP method (e.g., DELETE) is a full vulnerability even if GET is protected.
- `current_user.orders.find(id)` in Rails is safe — scoped association. `Order.find(id)` alone is not.
- In Express, having an `auth` middleware does NOT mean ownership is checked — auth only verifies identity.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
