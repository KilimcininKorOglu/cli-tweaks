---
name: idor
description: >-
  Detect Insecure Direct Object Reference (IDOR) vulnerabilities in a codebase
  using a two-phase recon-then-verify approach with subagents. Checks endpoints
  for missing ownership or authorization checks on user-supplied identifiers. Use when asked to find IDOR or authorization bypass bugs.
---

# IDOR (Insecure Direct Object Reference) Detection

You are performing a focused security assessment to find IDOR vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **recon** (find candidate endpoints) then **verify** (check authorization).

---

## What is IDOR

IDOR occurs when an application uses a user-supplied identifier (ID, slug, filename, etc.) to directly access an object **without verifying the requesting user is authorized to access that specific object**. The application authenticates the user but fails to check ownership or permissions on the requested resource.

The core pattern: *authenticated user A can access or modify resources belonging to user B by changing an identifier in the request.*

### What IDOR IS

- Changing `/api/orders/1001` to `/api/orders/1002` and seeing another user's order
- Sending `DELETE /api/documents/555` to delete a document you don't own
- Modifying `{"account_id": 789}` in a request body to transfer money from someone else's account
- Changing a file download parameter `?file_id=42` to access another user's private file
- Updating another user's profile via `PUT /api/users/other-user-id`

### What IDOR is NOT

Do not flag these as IDOR:

- **Missing authentication**: Endpoint requires no login at all → that's "Unauthenticated Access", a different class
- **Broken function-level access control**: Regular user accessing `/admin/dashboard` → that's vertical privilege escalation, not IDOR
- **Public resources**: Accessing `/api/posts/123` where posts are intentionally public is not IDOR
- **Parameter tampering on non-object fields**: Changing `role=admin` or `price=0` in a request → that's mass assignment or business logic, not IDOR
- **SQL injection via ID fields**: `?id=1 OR 1=1` → that's SQLi, not IDOR

### Authorization Patterns That Prevent IDOR

When you see these patterns, the endpoint is likely **not vulnerable**:

**1. Query scoped to current user (most common fix)**
```
# The query itself ensures only the user's own records are returned
Order.objects.filter(id=order_id, user=request.user)       # Django
current_user.orders.find(params[:id])                       # Rails
Order.findOne({ _id: orderId, userId: req.user.id })        # Mongoose
SELECT * FROM orders WHERE id = ? AND user_id = ?           # Raw SQL
```

**2. Explicit ownership check after fetch**
```
order = Order.find(order_id)
if order.user_id != current_user.id:
    raise Forbidden
```

**3. Policy / ability / authorization middleware**
```
authorize('view', order)                    # Laravel Policy
can?(:read, @order)                         # CanCanCan (Rails)
@PreAuthorize("@auth.ownsOrder(#orderId)")  # Spring Security
```

**4. Tenant/organization scoping**
```
# Multi-tenant apps that scope all queries to the tenant
tenant = get_current_tenant(request)
Order.objects.filter(id=order_id, tenant=tenant)
```

---

## Vulnerable vs. Secure Examples

### Python — Django

```python
# VULNERABLE: fetches any order by ID, no ownership check
def get_order(request, order_id):
    order = Order.objects.get(id=order_id)
    return JsonResponse(model_to_dict(order))

# SECURE: query scoped to requesting user
def get_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return JsonResponse(model_to_dict(order))
```

### Python — Flask / SQLAlchemy

```python
# VULNERABLE
@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return jsonify(doc.serialize())

# SECURE
@app.route('/api/documents/<int:doc_id>')
@login_required
def get_document(doc_id):
    doc = Document.query.filter_by(id=doc_id, owner_id=current_user.id).first_or_404()
    return jsonify(doc.serialize())
```

### Node.js — Express / Mongoose

```javascript
// VULNERABLE
router.get('/api/orders/:id', auth, async (req, res) => {
  const order = await Order.findById(req.params.id);
  res.json(order);
});

// SECURE
router.get('/api/orders/:id', auth, async (req, res) => {
  const order = await Order.findOne({ _id: req.params.id, userId: req.user.id });
  if (!order) return res.status(404).json({ error: 'Not found' });
  res.json(order);
});
```

### Node.js — Express / Prisma

```javascript
// VULNERABLE
router.get('/api/invoices/:id', auth, async (req, res) => {
  const invoice = await prisma.invoice.findUnique({ where: { id: req.params.id } });
  res.json(invoice);
});

// SECURE
router.get('/api/invoices/:id', auth, async (req, res) => {
  const invoice = await prisma.invoice.findFirst({
    where: { id: req.params.id, userId: req.user.id }
  });
  if (!invoice) return res.status(404).json({ error: 'Not found' });
  res.json(invoice);
});
```

### Ruby on Rails

```ruby
# VULNERABLE
def show
  @order = Order.find(params[:id])
end

# SECURE
def show
  @order = current_user.orders.find(params[:id])
end
```

### Java — Spring Boot

```java
// VULNERABLE
@GetMapping("/api/accounts/{id}")
public Account getAccount(@PathVariable Long id) {
    return accountRepo.findById(id).orElseThrow();
}

// SECURE
@GetMapping("/api/accounts/{id}")
public Account getAccount(@PathVariable Long id, Authentication auth) {
    Account acct = accountRepo.findById(id).orElseThrow();
    if (!acct.getOwnerId().equals(auth.getName()))
        throw new AccessDeniedException("Forbidden");
    return acct;
}
```

### Go

```go
// VULNERABLE
func GetOrder(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    order, _ := db.GetOrder(id)
    json.NewEncoder(w).Encode(order)
}

// SECURE
func GetOrder(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    userID := r.Context().Value("userID").(string)
    order, _ := db.GetOrderByUser(id, userID)
    json.NewEncoder(w).Encode(order)
}
```

### PHP — Laravel

```php
// VULNERABLE
public function show($id) {
    return Invoice::findOrFail($id);
}

// SECURE (scoped query)
public function show($id) {
    return auth()->user()->invoices()->findOrFail($id);
}

// SECURE (policy)
public function show($id) {
    $invoice = Invoice::findOrFail($id);
    $this->authorize('view', $invoice);
    return $invoice;
}
```

### C# — ASP.NET Core

```csharp
// VULNERABLE
[HttpGet("api/profiles/{id}")]
public async Task<IActionResult> GetProfile(int id) {
    var profile = await _db.Profiles.FindAsync(id);
    return Ok(profile);
}

// SECURE
[HttpGet("api/profiles/{id}")]
public async Task<IActionResult> GetProfile(int id) {
    var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    var profile = await _db.Profiles.FirstOrDefaultAsync(p => p.Id == id && p.UserId == userId);
    if (profile == null) return NotFound();
    return Ok(profile);
}
```

---

## Execution

### Phase 1: Recon — Find Candidate Endpoints

Launch a subagent with the following instructions:

> **Goal**: Find every endpoint, controller action, or handler that retrieves, modifies, or deletes a specific object using a user-supplied identifier. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, frameworks, route definitions, and data access patterns.
>
> **What to search for**:
>
> 1. **Route definitions** that contain ID parameters:
>    - Path parameters: `:id`, `{id}`, `<int:id>`, `[id]`
>    - Search patterns: route/path/endpoint definitions with parameter placeholders
>
> 2. **Controller/handler methods** that accept ID arguments and use them to fetch or mutate objects:
>    - ORM lookups: `find(id)`, `findById()`, `get(id=)`, `objects.get()`, `findOne()`, `findUnique()`, `findFirst()`, `query.get()`, `where(id:)`
>    - Raw queries: `SELECT ... WHERE id = ?`, etc.
>    - Also look for delete, update operations with user-supplied IDs
>
> 3. **Request body or query parameter IDs** used in operations:
>    - `req.body.userId`, `req.query.id`, `request.data['account_id']`, etc.
>
> 4. **GraphQL resolvers and mutations** that accept ID arguments
>
> 5. **File/resource access by user-supplied path or filename**
>
> **What to ignore**:
> - Endpoints that are intentionally public (no auth required by design)
> - Admin-only endpoints behind role-based checks (these are a different class)
> - Endpoints where the only ID used is the authenticated user's own ID (e.g., `GET /api/me/profile`)
> - Static asset serving
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # IDOR Recon: [Project Name]
>
> ## Summary
> Found [N] candidate endpoints that use user-supplied identifiers to access objects.
>
> ## Candidates
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint**: `METHOD /path/:param`
> - **Identifier source**: [path param / query param / body field]
> - **Operation**: [read / update / delete]
> - **Object accessed**: [model/table name]
> - **Code snippet**:
>   ```
>   [relevant code]
>   ```
>
> [Repeat for each candidate]
> ```

### Phase 2: Verify — Check Authorization

Launch a second subagent **after Phase 1 completes**, providing Phase 1 findings as context. Instructions:

>
> **Context**: You will be given the project's architecture summary and the recon results. Use the architecture summary to understand the auth mechanism, middleware stack, and ORM patterns.
>
> **For each candidate endpoint, check**:
>
> 1. **Is the database query scoped to the authenticated user?**
>    - Does the query include a `user_id` / `owner_id` / `tenant_id` filter matching the current user?
>    - Is the query done through an association (e.g., `current_user.orders.find(id)`)?
>
> 2. **Is there an explicit ownership/permission check after fetching?**
>    - Does the code compare `resource.user_id == current_user.id` (or equivalent)?
>    - Is there a policy/ability/authorization check?
>
> 3. **Is there authorization middleware applied to this route?**
>    - Is there middleware that verifies object ownership before the handler runs?
>    - Trace the middleware chain — don't assume a middleware name implies it checks ownership
>
> 4. **For mutations (update/delete), are the same checks present?**
>    - Sometimes read endpoints are protected but write endpoints are not
>
> 5. **Edge cases to check**:
>    - Does the auth check exist but only run conditionally (e.g., skipped for certain content types)?
>    - Is the check present in one branch of an if/else but missing in another?
>    - Can the check be bypassed by sending the ID in an alternative field?
>    - Are bulk/batch endpoints checked per-item or just at the batch level?
>
> **Classification**:
> - **Vulnerable**: No authorization check found for the specific object. User A can access User B's resources.
> - **Likely Vulnerable**: Auth check exists but appears incomplete, bypassable, or conditional.
> - **Not Vulnerable**: Proper authorization check is in place.
> - **Needs Manual Review**: Cannot determine with confidence (e.g., complex middleware chain, authorization happens in a service layer that's hard to trace).
>
> **Output format** — write confirmed findings to `BUG-REPORT.md` using the shared report format from `../SKILL.md`. Read existing `BUG-REPORT.md` first to continue the ID sequence (start at BUG-001 if none exists).
>
> **Severity mapping**:
> - Financial, PII, or health data → HIGH
> - Non-sensitive data → MEDIUM
> - Write/delete capability → HIGH
>
> For **Verification**: include the full taint trace and a dynamic test command or payload.
> For **Suggested Commit**: conventional commit message without BUG-IDs.
>
> Do **NOT** write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 2 must run AFTER Phase 1 completes — it depends on Phase 1 results.
- Focus on **horizontal privilege escalation** (user-to-user). Vertical escalation (user-to-admin) is a different skill.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
- Trace the full code path: route → middleware → controller → service → data access. Authorization can happen at any layer.
- Pay attention to framework conventions. In Rails, `current_user.orders.find(id)` is safe. In Express, just having `auth` middleware doesn't mean ownership is checked.