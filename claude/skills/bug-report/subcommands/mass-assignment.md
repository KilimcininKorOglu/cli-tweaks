---
name: mass-assignment
description: >-
  Detect mass assignment vulnerabilities using a three-phase approach:
  find request-to-model binding sites, verify unprotected fields
  (role escalation, price manipulation, admin flag injection),
  then merge confirmed findings. Use when asked to audit mass assignment or over-posting.
---

# Mass Assignment Detection

You are performing a focused security assessment to find mass assignment (over-posting) vulnerabilities in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all request-to-model binding sites) then **verify** (confirm whether unprotected fields allow privilege escalation or data manipulation) then **merge** (write confirmed findings).

---

## What is Mass Assignment

Mass assignment occurs when HTTP request body fields are bound directly to data model attributes without field filtering. Attackers can add extra fields to the request to modify attributes they should not have access to. The core pattern: *request body is spread or bound to a model/entity without an explicit allowlist of permitted fields, enabling attackers to set sensitive attributes like role, admin status, or price.*

### What Mass Assignment IS

- `User.create(req.body)` or `Object.assign(user, req.body)` — all body fields become model attributes
- Django `ModelForm` with `fields = '__all__'` — includes `is_staff`, `is_superuser`
- Laravel model without `$fillable` or `$guarded` — all fields mass-assignable
- Spring `@ModelAttribute` binding all request params to entity without `@InitBinder` or DTO
- ASP.NET `[FromBody] User user` without `[Bind]` attribute — all properties settable
- `Object.assign()`, spread operator (`...req.body`), or `_.merge()` into model objects
- Rails `params.permit!` or missing `strong_parameters` — all params accepted

### What Mass Assignment is NOT

Do not flag these:

- **DTO/ViewModel patterns**: Request bound to a DTO that only has safe fields — the DTO IS the protection
- **Admin endpoints**: Admin users legitimately setting all fields via admin panel
- **Schema validation stripping unknowns**: Zod `.strict()`, Joi `.options({ stripUnknown: true })`, or similar that reject/strip extra fields BEFORE model binding
- **Explicit field picking**: `{ name: req.body.name, email: req.body.email }` — manual field selection is the fix
- **Laravel with restrictive $fillable**: Model with `$fillable = ['name', 'email']` — only listed fields are assignable

### Patterns That Prevent Mass Assignment

When you see these patterns, the code is likely **not vulnerable**:

**1. Explicit field picking (Node.js)**
```javascript
const user = await User.create({
  name: req.body.name,
  email: req.body.email
});
```

**2. DTO pattern (Spring Boot)**
```java
@PostMapping("/users")
public User createUser(@RequestBody CreateUserDTO dto) {
    User user = new User();
    user.setName(dto.getName());
    user.setEmail(dto.getEmail());
    return userRepository.save(user);
}
```

**3. Strong parameters (Rails)**
```ruby
def user_params
  params.require(:user).permit(:name, :email, :bio)
end
User.create(user_params)
```

**4. Django explicit fields**
```python
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'bio']
```

**5. Schema validation stripping unknowns**
```javascript
const schema = z.object({ name: z.string(), email: z.string().email() }).strict();
const data = schema.parse(req.body);  // Rejects extra fields
const user = await User.create(data);
```

---

## Vulnerable vs. Secure Examples

### Node.js / Express — Spread into Model

```javascript
// VULNERABLE: All body fields become model attributes
app.post('/users', async (req, res) => {
  const user = await User.create(req.body);
  // Body: { name: "hacker", email: "h@x.com", role: "admin" }
  // Attacker becomes admin!
});

// VULNERABLE: Object.assign spreads all fields
app.put('/users/:id', async (req, res) => {
  const user = await User.findById(req.params.id);
  Object.assign(user, req.body);
  await user.save();
});

// SECURE: Pick only allowed fields
app.post('/users', async (req, res) => {
  const user = await User.create({
    name: req.body.name,
    email: req.body.email
  });
});
```

### Django — ModelForm with All Fields

```python
# VULNERABLE: fields = '__all__' includes is_staff, is_superuser
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = '__all__'

# VULNERABLE: exclude instead of explicit fields
class UserForm(ModelForm):
    class Meta:
        model = User
        exclude = ['password']  # Forgets is_staff, is_superuser!

# SECURE: Explicit field list
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'bio']
```

### Django REST Framework — Serializer

```python
# VULNERABLE: All fields exposed
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

# SECURE: Explicit fields
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'bio']
        read_only_fields = ['id', 'created_at']
```

### Laravel — Missing $fillable

```php
// VULNERABLE: No $fillable or $guarded
class User extends Model {
    // All fields are mass-assignable!
}
User::create($request->all());

// VULNERABLE: Overly broad $guarded
class User extends Model {
    protected $guarded = [];  // Nothing guarded = everything assignable
}

// SECURE: Restrictive $fillable
class User extends Model {
    protected $fillable = ['name', 'email'];
}
```

### Spring Boot — @ModelAttribute

```java
// VULNERABLE: All request params bound to entity
@PostMapping("/users")
public User createUser(@ModelAttribute User user) {
    return userRepository.save(user);
    // POST /users?name=hacker&email=h@x.com&role=ADMIN → admin account created
}

// SECURE: Use DTO
@PostMapping("/users")
public User createUser(@RequestBody CreateUserDTO dto) {
    User user = new User();
    user.setName(dto.getName());
    user.setEmail(dto.getEmail());
    return userRepository.save(user);
}
```

### ASP.NET — Missing Bind Attribute

```csharp
// VULNERABLE: All properties settable from request
[HttpPost]
public IActionResult Create([FromBody] User user) {
    _context.Users.Add(user);
    _context.SaveChanges();
}

// SECURE: Use [Bind] attribute
[HttpPost]
public IActionResult Create([Bind("Name,Email")] User user) {
    _context.Users.Add(user);
    _context.SaveChanges();
}

// SECURE: Use DTO/ViewModel
[HttpPost]
public IActionResult Create([FromBody] CreateUserDto dto) {
    var user = new User { Name = dto.Name, Email = dto.Email };
    _context.Users.Add(user);
    _context.SaveChanges();
}
```

### Rails — Missing Strong Parameters

```ruby
# VULNERABLE: permit! allows everything
def create
  @user = User.new(params[:user].permit!)
  @user.save
end

# SECURE: Explicit permit list
def create
  @user = User.new(user_params)
  @user.save
end

private
def user_params
  params.require(:user).permit(:name, :email, :bio)
end
```

---

## Execution

### Phase 1: Find Request-to-Model Binding Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where HTTP request body/params are bound to data models — ORM create/update calls, Object.assign, spread operators, ModelForm, Serializer, @ModelAttribute, [FromBody], $fillable/$guarded. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to identify the web framework, ORM, and model layer.
>
> **What to search for — mass assignment patterns**:
>
> 1. **Direct body-to-model binding**:
>    - Node.js: `Model.create(req.body)`, `Model.update(req.body)`, `Object.assign(model, req.body)`, `{ ...req.body }`, `_.merge(model, req.body)`
>    - Django: `ModelForm`, `Serializer` with `fields = '__all__'` or `exclude`
>    - Laravel: `Model::create($request->all())`, `$model->fill($request->all())`, `$model->update($request->all())`
>    - Rails: `Model.new(params[:model])`, `params.permit!`
>    - Spring: `@ModelAttribute`, `@RequestBody` with entity class (not DTO)
>    - ASP.NET: `[FromBody]` with entity class without `[Bind]`
>
> 2. **Model protection configuration**:
>    - Laravel: `$fillable`, `$guarded` arrays on models
>    - Django: `fields` and `exclude` in ModelForm/Serializer Meta
>    - Rails: `strong_parameters` in controllers
>    - Spring: `@InitBinder` with `setAllowedFields`/`setDisallowedFields`
>    - ASP.NET: `[Bind]` attribute on action parameters
>
> 3. **Schema validation before binding**:
>    - Zod, Joi, Yup, class-validator schemas applied before model creation
>    - Check if they use `.strict()` or `stripUnknown` to reject extra fields
>
> 4. **Sensitive model fields**:
>    - Identify models with sensitive fields: `role`, `isAdmin`, `is_staff`, `is_superuser`, `price`, `verified`, `permissions`, `balance`, `active`
>    - Check if these fields are protected from mass assignment
>
> **What to skip**:
> - Admin panel CRUD operations (admin users setting all fields is expected)
> - Test/seed data creation
> - Internal migration scripts
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Mass Assignment Recon: [Project Name]
>
> ## Summary
> Found [N] request-to-model binding sites. Framework: [Express/Django/Laravel/Spring/etc.].
>
> ## Binding Sites
>
> ### 1. [Descriptive name — e.g., "User creation with full req.body spread"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Framework / ORM**: [Mongoose / Sequelize / Django ORM / Eloquent / JPA / etc.]
> - **Binding method**: [req.body spread / ModelForm / $request->all() / @ModelAttribute / etc.]
> - **Model**: [User / Product / Order / etc.]
> - **Sensitive fields on model**: [role / isAdmin / price / verified / etc.]
> - **Protection present**: [none / $fillable / DTO / schema validation / strong_params]
> - **Code snippet**:
>   ```
>   [the binding code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm Unprotected Fields

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which models have sensitive fields and which endpoints are public-facing.
>
> **For each binding site, verify whether mass assignment is exploitable**:
>
> 1. **Check model schema for sensitive fields**: Does the model have fields like `role`, `isAdmin`, `is_staff`, `is_superuser`, `price`, `verified`, `balance`, `permissions`?
>    - Read the model definition to identify all fields
>    - If sensitive fields exist AND no field filtering → VULNERABLE
>
> 2. **Check field filtering**: Is there an allowlist of permitted fields?
>    - Node.js: explicit field picking, Zod/Joi schema with strict mode
>    - Django: `fields` list in ModelForm/Serializer (not `'__all__'`)
>    - Laravel: `$fillable` array on model (not empty `$guarded`)
>    - Rails: `strong_parameters` with explicit `permit` list
>    - Spring: DTO class or `@InitBinder` with `setAllowedFields`
>    - ASP.NET: `[Bind]` attribute or DTO/ViewModel
>    - If no filtering or filtering is too broad → VULNERABLE
>
> 3. **Check middleware/validation layer**: Is request validated before reaching model?
>    - Schema validation that rejects unknown fields (Zod `.strict()`, Joi `stripUnknown`)
>    - Custom middleware that whitelists body fields
>    - If schema validation strips unknowns BEFORE model binding → NOT VULNERABLE
>
> 4. **Check endpoint visibility**: Is the endpoint public or admin-only?
>    - Admin endpoints with proper auth → lower risk
>    - Public registration/profile endpoints → higher risk
>    - If admin-only with proper auth → NOT VULNERABLE (by design)
>
> 5. **Trace data flow**: Follow request body from controller to model
>    - Check for intermediate transformations that might strip fields
>    - Check for service layer that picks specific fields
>    - If any layer filters fields before model → NOT VULNERABLE
>
> **Classification**:
> - **Vulnerable**: Confirmed mass assignment — request body reaches model with sensitive fields unfiltered on public endpoint.
> - **Likely Vulnerable**: Missing field filtering, but sensitive fields not confirmed or endpoint access unclear.
> - **Not Vulnerable**: Proper field allowlist, DTO pattern, or schema validation stripping unknowns.
> - **Needs Manual Review**: Complex middleware chain or dynamic field filtering logic.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Mass Assignment Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / scope**: [route and HTTP method]
> - **Model**: [model name with sensitive fields listed]
> - **Issue**: [e.g., "User.create(req.body) allows setting role field — attacker can POST with role:'admin' to escalate privileges"]
> - **Exploitable fields**: [role / isAdmin / price / verified / etc.]
> - **Impact**: Privilege escalation, price manipulation, bypassing verification, unauthorized data modification
> - **Remediation**: Use explicit field picking, DTO pattern, or framework-specific protection ($fillable, strong_params, fields=[...])
> - **Proof of concept**: [e.g., "`curl -X POST /api/users -d '{\"name\":\"test\",\"role\":\"admin\"}'` — check if role is set to admin"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Mass assignment enabling role escalation to admin → CRITICAL
> - Mass assignment allowing price/balance manipulation → HIGH
> - Mass assignment setting verified/active status → HIGH
> - Mass assignment on non-critical fields (profile fields of other users) → MEDIUM
> - Mass assignment in admin-only endpoints or internal tools → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full exploit details and a proof of concept
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all request-to-model binding sites regardless of whether they are protected. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each binding site, determine whether sensitive fields can be mass-assigned.
- Role escalation is the most critical mass assignment exploit. If a User model has a `role` or `isAdmin` field and `User.create(req.body)` is used, any user can make themselves admin.
- DTO/ViewModel pattern is the gold standard defense. A dedicated class that only has the fields the endpoint should accept makes mass assignment impossible.
- `fields = '__all__'` in Django is a common mistake. It exposes every model field including `is_staff` and `is_superuser`. Always use an explicit field list.
- Laravel `$guarded = []` (empty guarded array) is equivalent to no protection — all fields become mass-assignable.
- Schema validation (Zod, Joi) only protects if it uses strict mode or strips unknown fields. A schema that only validates known fields but passes through unknowns does NOT prevent mass assignment.
- `Object.assign()` and spread operator (`...`) are the most common Node.js mass assignment vectors. They copy ALL enumerable properties.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
