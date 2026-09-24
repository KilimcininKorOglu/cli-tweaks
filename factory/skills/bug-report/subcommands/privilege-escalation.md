---
name: privilege-escalation
description: "Detect privilege escalation vectors where a user raises their own authority:
  role fields accepted from request bodies, role claims trusted from tokens,
  admin routes without a role guard, and default or seeded admin accounts."
---

# Privilege Escalation Detection

You are performing a focused security assessment to find privilege escalation vectors. This skill uses a three-phase approach: **recon** (map the authority model and every place a role is assigned or read), **batched verify** (trace who can influence each assignment), and **merge** (write confirmed findings to `BUG-REPORT.md`).

`access-control` covers horizontal access to another user's resources (IDOR) and missing authentication. This subcommand covers vertical elevation: the same user acquiring higher authority than their account holds.

---

## What is Privilege Escalation

Privilege escalation occurs when the authority attached to a request is decided by a value the requester controls, or when a privileged route is not guarded at all. The check may exist and still fail, because it reads its input from the attacker.

The core pattern: *the role that authorizes the action comes from the request instead of from the server's own record of the account.*

### What Privilege Escalation IS

- Passing the whole request body into a user create or update call, so `role`, `is_admin`, or `plan` is writable
- Reading `role` from a decoded token and authorizing on it without re-reading the account
- An admin route registered outside the group that carries the role middleware
- A role check that runs on the URL prefix rather than on the resolved handler
- A seeded or migrated account with a fixed password that exists in production
- An invite, impersonation, or support-login flow that grants the target's authority without binding it to an approver
- A permission cached at login and never re-read after the account is downgraded

### What Privilege Escalation is NOT

Do not flag these:
- **An admin assigning roles**: a route that requires an admin role and then sets another user's role is the feature
- **A service-to-service identity with broad rights**: an internal caller authenticated by a separate credential is by design
- **A role field in a response**: reading a role back is disclosure at most, not elevation
- **A seed script guarded to development**: a fixture behind an environment check that production cannot satisfy
- **Test fixtures**: role assignment in test setup code
- **A claim that is re-verified**: a token role used for routing but re-checked against the database before the sensitive action

### Patterns That Prevent Privilege Escalation

```javascript
// Node — build the record from an allowlist, never from the body
const user = await User.create({
  name: req.body.name,
  email: req.body.email,
  role: "user",
});
```

```python
# Python — authorize on the stored account, not on the token claim
@login_required
def admin_panel():
    account = User.query.get(current_user.id)
    if account.role != "admin":
        abort(403)
```

```go
// Go — every admin route inherits the guard from the group
admin := r.Group("/admin", authMiddleware, requireRole("admin"))
admin.GET("/users", handlers.ListAllUsers)
```

---

## Vulnerable vs. Secure Examples

### Node.js — role accepted from the body

```javascript
// VULNERABLE: mass assignment reaches the role column
app.post("/api/users", async (req, res) => {
  const user = await User.create(req.body);      // body may carry role: "admin"
  res.json(user);
});

// SECURE: explicit fields, server-set role
app.post("/api/users", async (req, res) => {
  const user = await User.create({ name: req.body.name, email: req.body.email, role: "user" });
  res.json(user);
});
```

### Python — token claim trusted as authority

```python
# VULNERABLE: the claim decides, and the claim travels with the client
claims = decode_jwt(request.headers["Authorization"])
if claims["role"] == "admin":
    return render_admin()

# SECURE: the claim identifies, the database authorizes
claims = decode_jwt(request.headers["Authorization"])
account = User.query.get(claims["sub"])
if account.role != "admin":
    abort(403)
```

### Go — unguarded admin route

```go
// VULNERABLE: registered outside the guarded group
r.GET("/admin/settings", handlers.GetSettings)

// SECURE: inside the group that applies auth and role checks
admin.GET("/settings", handlers.GetSettings)
```

---

## Execution

### Phase 1: Map the Authority Model

Launch a subagent with the following instructions:

> **Goal**: Describe how authority is stored, transported, and checked, then list every site that assigns or reads a role. Return findings in your response.
>
> **What to search for**:
>
> 1. **Authority storage**: columns and fields named `role`, `roles`, `is_admin`, `is_staff`, `is_superuser`, `permissions`, `scopes`, `plan`, `tier`, `user_type`, `privilege`
> 2. **Assignment sites**: user create and update handlers, registration, profile update, invite acceptance, admin user management, ORM calls that pass a whole request object or dictionary
> 3. **Read sites**: every guard, middleware, decorator, policy, or inline comparison that decides on a role, and the source it reads from (token claim, session, database row, cache)
> 4. **Route registration**: every route whose path or handler name contains `admin`, `internal`, `manage`, `staff`, `ops`, `debug`, `console`, and which middleware chain it carries
> 5. **Seeded accounts**: migrations, seeders, fixtures, and bootstrap code that create a user with a fixed password or an elevated role
> 6. **Impersonation**: `login_as`, `switch_user`, `sudo`, `impersonate`, support-login helpers
>
> **What to skip**: response serializers that only return a role, and role assignment inside tests.
>
> **Output format** — return in your response:
>
> ```markdown
> # Privilege Escalation Recon: [Project Name]
>
> ## Authority Model
> - **Roles present**: [list]
> - **Storage**: [table.column / claim / config]
> - **Transport**: [session cookie / JWT / API key / header]
> - **Enforcement**: [middleware name, decorator, policy class]
>
> ## Sites
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Kind**: [assignment / read / route registration / seed / impersonation]
> - **Route or function**: [name]
> - **Authority source**: [request body / token claim / database row / config]
> - **Guard on the path**: [middleware list, or none]
> - **Code snippet**:
>   ```
>   [the site]
>   ```
> ```

### Phase 2: Batched Verify — Trace Who Controls the Authority

After Phase 1 completes, count numbered sites. If 3 or fewer, use a single subagent. Otherwise split the sites into batches of up to 3 and run them through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.

> **For each site, answer these in order**:
>
> 1. **Reachability**: which caller reaches this site — anonymous, any authenticated user, or an existing admin?
> 2. **Input control**: can that caller set the authority value? Check the serializer, the allowlist, the ORM call, and any `strong_parameters`, `fillable`, `guarded`, or schema validation between the request and the write.
> 3. **Verification**: for a read site, is the authority re-read from the server's record before the sensitive action, or is the transported value final?
> 4. **Guard coverage**: for a route, walk the registration and confirm the role middleware applies. A guard on a sibling group does not cover this route.
> 5. **Production reach**: for a seeded account, does the guard on the seeder prevent it from running in production, and is the password fixed?
> 6. **Result**: what does the caller gain — admin panel, another tenant's data, billing tier, moderation powers?
>
> **Classification**:
> - **Vulnerable**: a lower-authority caller sets or forges the authority, and a privileged action follows
> - **Likely Vulnerable**: the path exists with one unresolved guard question
> - **Not Vulnerable**: authority is server-set and re-verified, or the caller already holds that authority
> - **Needs Manual Review**: enforcement happens outside the repository, such as in an API gateway or a service mesh policy
>
> **Output format** — return in your response:
>
> ```markdown
> # Privilege Escalation Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Starting authority**: [anonymous / authenticated user / tenant member]
> - **Gained authority**: [admin / staff / other tenant / higher plan]
> - **Issue**: [how the authority is set or forged]
> - **Path**: [request field or claim → assignment or check → privileged action]
> - **Remediation**: [allowlist the fields, re-read the account, move the route behind the guard]
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
- Any user reaches admin authority, or an admin route has no guard → CRITICAL
- Forged role claim accepted, or a fixed-password admin account reachable in production → HIGH
- Elevation that needs an authenticated account plus a specific condition, or a stale permission cache → MEDIUM
- Elevation inside an internal tool, or with a strong compensating control on the privileged action → LOW

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1. Phase 3 runs AFTER all batches.
- Batch size: 3 sites per subagent. If 1-3 total, single subagent. Run the batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Read the framework's mass-assignment defaults before judging an assignment site. Some ORMs ignore unknown fields, and some write every key they receive.
- A signed token is not a trusted authority. A signature proves the issuer, not that the role was current at request time.
- Overlap with `mass-assignment` and `access-control` is expected. Report the elevation here, the writable-field mechanism there, and deduplicate by root cause during the merge.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
