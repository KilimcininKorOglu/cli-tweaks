---
name: sqli
description: >-
  Detect SQL injection vulnerabilities in a codebase using a two-phase approach:
  first find unsafe SQL construction sites (string concat, f-strings, unsafe ORM
  methods), then trace whether user-supplied input reaches those sites. Use when asked to find SQLi or database injection bugs.
---

# SQL Injection (SQLi) Detection

You are performing a focused security assessment to find SQL injection vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **construction** (find all places where SQL queries are built unsafely) then **taint** (confirm whether user-supplied input reaches those construction sites).

---

## What is SQL Injection

SQL injection occurs when user-supplied input is incorporated into SQL queries through string concatenation or interpolation rather than parameterized binding. This allows attackers to alter query logic, bypass authentication, extract sensitive data, modify or delete records, and in some configurations execute OS commands.

The core pattern: *unvalidated, unparameterized user input reaches a SQL query execution call.*

### What SQLi IS

- Concatenating user input directly into a SQL string: `"SELECT * FROM users WHERE name = '" + username + "'"`
- Using string formatting to build queries: `f"SELECT * FROM orders WHERE id = {order_id}"`
- Dynamic `ORDER BY` / `GROUP BY` / table/column names from user input with no allowlist validation
- ORM raw query methods with unsanitized input: `User.objects.raw(f"SELECT * WHERE id={id}")`, `$queryRawUnsafe(input)`
- Second-order injection: input is stored in the DB and later used in a raw query without re-sanitization

### What SQLi is NOT

Do not flag these as SQLi:

- **IDOR**: Changing `?id=1` to `?id=2` to access another user's data — that's Insecure Direct Object Reference, a separate class
- **Mass assignment**: Setting extra ORM model fields from user input — different vulnerability
- **XSS via database**: Storing a `<script>` tag in the DB that's later rendered unescaped — that's XSS, not SQLi
- **NoSQL injection**: Injecting into MongoDB operators — similar concept but a distinct vulnerability class
- **Safe ORM queries**: Parameterized ORM lookups like `User.objects.filter(id=user_id)` or `User.find(params[:id])` — do not flag these

### Patterns That Prevent SQLi

When you see these patterns, the code is likely **not vulnerable**:

**1. Parameterized queries / prepared statements (most common fix)**
```
# Python — cursor.execute with tuple binding
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Node.js — mysql2 / pg placeholder binding
db.query("SELECT * FROM users WHERE id = ?", [userId])
pool.query("SELECT * FROM users WHERE id = $1", [userId])

# Java — PreparedStatement
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);

# Go — database/sql placeholder
db.QueryRow("SELECT * FROM users WHERE id = $1", userID)

# PHP — PDO with named params
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(['id' => $userId]);

# C# — SqlCommand with parameters
cmd.CommandText = "SELECT * FROM users WHERE id = @id";
cmd.Parameters.AddWithValue("@id", userId);
```

**2. ORM query builder (safe by default)**
```
# Django ORM
User.objects.filter(id=user_id)

# ActiveRecord (Rails)
User.find(params[:id])
User.where(name: params[:name])

# Prisma (tagged template literal form of $queryRaw)
await prisma.$queryRaw`SELECT * FROM users WHERE id = ${userId}`

# Laravel Eloquent (non-raw)
User::find($id)
```

**3. Allowlist validation for dynamic identifiers**
```
# Dynamic ORDER BY — validate column name against a hardcoded set before interpolating
ALLOWED_COLUMNS = {'name', 'created_at', 'price'}
if sort_col not in ALLOWED_COLUMNS:
    raise ValueError("Invalid column")
query = f"SELECT * FROM products ORDER BY {sort_col}"  # safe only after allowlist check
```

---

## Vulnerable vs. Secure Examples

### Python — Django (raw SQL)

```python
# VULNERABLE: f-string interpolation in raw()
def search_users(request):
    username = request.GET.get('username')
    users = User.objects.raw(f"SELECT * FROM auth_user WHERE username = '{username}'")
    return JsonResponse(list(users.values()), safe=False)

# SECURE: parameterized raw()
def search_users(request):
    username = request.GET.get('username')
    users = User.objects.raw("SELECT * FROM auth_user WHERE username = %s", [username])
    return JsonResponse(list(users.values()), safe=False)
```

### Python — Flask / SQLAlchemy

```python
# VULNERABLE: f-string into text()
@app.route('/search')
def search():
    name = request.args.get('name')
    result = db.session.execute(text(f"SELECT * FROM products WHERE name = '{name}'"))
    return jsonify(result.fetchall())

# SECURE: named bound parameter
@app.route('/search')
def search():
    name = request.args.get('name')
    result = db.session.execute(
        text("SELECT * FROM products WHERE name = :name"), {"name": name}
    )
    return jsonify(result.fetchall())
```

### Python — sqlite3 / psycopg2

```python
# VULNERABLE
def get_user(username):
    cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")
    return cursor.fetchone()

# SECURE
def get_user(username):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()
```

### Node.js — mysql2

```javascript
// VULNERABLE: template literal in query string
app.get('/user', async (req, res) => {
  const { id } = req.query;
  const [rows] = await db.query(`SELECT * FROM users WHERE id = ${id}`);
  res.json(rows);
});

// SECURE: placeholder binding
app.get('/user', async (req, res) => {
  const { id } = req.query;
  const [rows] = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  res.json(rows);
});
```

### Node.js — pg (PostgreSQL)

```javascript
// VULNERABLE
app.get('/orders', async (req, res) => {
  const status = req.query.status;
  const result = await pool.query(`SELECT * FROM orders WHERE status = '${status}'`);
  res.json(result.rows);
});

// SECURE
app.get('/orders', async (req, res) => {
  const status = req.query.status;
  const result = await pool.query('SELECT * FROM orders WHERE status = $1', [status]);
  res.json(result.rows);
});
```

### Ruby on Rails

```ruby
# VULNERABLE: string interpolation in where()
def search
  @users = User.where("name = '#{params[:name]}'")
end

# VULNERABLE: find_by_sql with interpolation
def find_user
  @user = User.find_by_sql("SELECT * FROM users WHERE email = '#{params[:email]}'")
end

# SECURE: parameterized where()
def search
  @users = User.where("name = ?", params[:name])
  # or using hash form: User.where(name: params[:name])
end
```

### Java — Spring JDBC

```java
// VULNERABLE: string concatenation
public User findUser(String username) {
    String sql = "SELECT * FROM users WHERE username = '" + username + "'";
    return jdbcTemplate.queryForObject(sql, userRowMapper);
}

// SECURE: parameterized query
public User findUser(String username) {
    return jdbcTemplate.queryForObject(
        "SELECT * FROM users WHERE username = ?", userRowMapper, username
    );
}
```

### Go — database/sql

```go
// VULNERABLE: fmt.Sprintf to build query
func GetUserByName(name string) (*User, error) {
    query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
    row := db.QueryRow(query)
    // ...
}

// SECURE: parameterized query
func GetUserByName(name string) (*User, error) {
    row := db.QueryRow("SELECT * FROM users WHERE name = $1", name)
    // ...
}
```

### PHP — PDO

```php
// VULNERABLE: string concatenation
function getUser($id) {
    $stmt = $pdo->query("SELECT * FROM users WHERE id = " . $id);
    return $stmt->fetch();
}

// SECURE: prepared statement
function getUser($id) {
    $stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
    $stmt->execute(['id' => $id]);
    return $stmt->fetch();
}
```

### C# — ADO.NET

```csharp
// VULNERABLE: string concatenation
public User GetUser(string username) {
    using var cmd = new SqlCommand(
        "SELECT * FROM Users WHERE Username = '" + username + "'", conn);
    return ReadUser(cmd.ExecuteReader());
}

// SECURE: parameterized command
public User GetUser(string username) {
    using var cmd = new SqlCommand(
        "SELECT * FROM Users WHERE Username = @username", conn);
    cmd.Parameters.AddWithValue("@username", username);
    return ReadUser(cmd.ExecuteReader());
}
```

### Dynamic ORDER BY / Column Names (all stacks)

```python
# VULNERABLE: unsanitized user input as column name (parameterization can't help here)
sort_col = request.args.get('sort', 'name')
cursor.execute(f"SELECT * FROM products ORDER BY {sort_col}")

# SECURE: allowlist validation before interpolation
ALLOWED_SORT_COLS = {'name', 'price', 'created_at'}
sort_col = request.args.get('sort', 'name')
if sort_col not in ALLOWED_SORT_COLS:
    return abort(400)
cursor.execute(f"SELECT * FROM products ORDER BY {sort_col}")
```

---

## Execution

### Phase 1: Find Vulnerable SQL Construction Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where a SQL query is constructed in a vulnerable way — using string concatenation, interpolation, or formatting with any variable (regardless of where that variable comes from). Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, database layer, ORM patterns, and query execution methods.
>
> **What to search for — vulnerable query construction patterns**:
>
> Look for SQL query execution calls where the query string argument is built dynamically rather than being a static string with placeholder parameters. Flag ANY dynamic variable embedded into the query — you are not yet tracing whether the variable is user-controlled; that is Phase 2's job.
>
> 1. **String concatenation into a SQL execution call**:
>    - `cursor.execute("SELECT ... WHERE id = " + var)`
>    - `$pdo->query("SELECT * FROM users WHERE id = " . $var)`
>    - `jdbcTemplate.query("SELECT * WHERE username = '" + var + "'")`
>
> 2. **F-strings / template literals used as a query argument**:
>    - `cursor.execute(f"SELECT * WHERE name = '{var}'")`
>    - `` db.query(`SELECT * WHERE id = ${var}`) ``
>    - `db.QueryRow(fmt.Sprintf("SELECT * WHERE id = '%s'", var))`
>
> 3. **String formatting functions used to build the query**:
>    - `cursor.execute("SELECT * WHERE id = %s" % var)` (note: `%` formatting, NOT parameterized binding)
>    - `cursor.execute("SELECT * WHERE id = {}".format(var))`
>    - `String.format("SELECT * WHERE id = '%s'", var)` (Java)
>    - `sprintf("SELECT * WHERE id = %s", $var)` (PHP)
>
> 4. **ORM raw/unsafe methods called with a dynamically built string** (not a static template with bound params):
>    - Django: `Model.objects.raw(f"...")`, `RawSQL(f"...")`, `extra(where=[f"..."])`
>    - ActiveRecord: `where("col = '#{var}'")`  (Ruby interpolation inside string arg)
>    - Sequelize: `` sequelize.query(`...${var}...`) ``, `literal(var)`
>    - TypeORM: `` createQueryBuilder().where(`col = '${var}'`) ``, `.query("..." + var)`
>    - Prisma: `$queryRawUnsafe(...)`, `$executeRawUnsafe(...)`
>    - Entity Framework: `FromSqlRaw("..." + var)`, `ExecuteSqlRaw("..." + var)`
>
> 5. **Dynamic identifiers** — any variable used as a column name, table name, `ORDER BY` / `GROUP BY` value in a query string (parameterization cannot protect identifiers; only allowlist validation can):
>    - `f"SELECT * FROM {table_var}"`
>    - `` `SELECT * FROM ${tableVar}` ``
>    - `f"SELECT * ORDER BY {sort_col}"`
>
> **What to skip** (these are safe construction patterns — do not flag):
> - Static query strings with no dynamic parts: `cursor.execute("SELECT * FROM users WHERE id = %s", (val,))`
> - ORM safe query builder methods: `.filter()`, `.where(col: val)`, `.findOne()`, `.findUnique()`, `prisma.$queryRaw` with tagged template literals
> - Properly parameterized raw queries where the string itself is static and values are passed as a separate argument list: `execute("SELECT * WHERE id = %s", (val,))`, `query("SELECT * WHERE id = ?", [val])`
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # SQLi Recon: [Project Name]
>
> ## Summary
> Found [N] locations where SQL queries are constructed in a vulnerable way.
>
> ## Vulnerable Construction Sites
>
> ### 1. [Descriptive name — e.g., "String concat in get_user query"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Query execution method**: [cursor.execute / db.query / raw / etc.]
> - **Construction pattern**: [string concat / f-string / template literal / % format / .format() / fmt.Sprintf / ORM raw]
> - **Interpolated variable(s)**: `var_name` — [brief note on what it appears to represent, e.g., "looks like a sort column" or "unknown origin"]
> - **Code snippet**:
>   ```
>   [the vulnerable query construction + execution call]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Trace User Input to Vulnerable Construction Sites

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

>
> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand request entry points, middleware, and how data flows through the application.
>
> **For each construction site, trace the interpolated variable(s) backwards to their origin**:
>
> 1. **Direct user input** — the variable is assigned directly from a request source with no transformation:
>    - HTTP query params: `request.GET.get(...)`, `req.query.x`, `params[:x]`, `$_GET['x']`, `c.Query("x")`
>    - Path parameters: `request.path_params['id']`, `req.params.id`, `params[:id]`, `$_GET['id']`
>    - Request body / form fields: `request.POST.get(...)`, `req.body.x`, `params[:x]`, `$_POST['x']`
>    - HTTP headers: `request.headers.get(...)`, `req.headers['x']`
>    - Cookies: `request.COOKIES.get(...)`, `req.cookies.x`
>
> 2. **Indirect user input** — the variable is derived from user input through transformations, function calls, or intermediate assignments. Trace the full chain:
>    - Variable assigned from a function return value → check that function's parameter origin
>    - Variable passed as a function argument → check the call site(s)
>    - Variable read from a class attribute or shared state set elsewhere → find the setter
>    - Variable conditionally assigned — check all branches
>
> 3. **Second-order input** — the variable is read from the database, but the stored value originally came from user input:
>    - Find where this value was written to the DB — was it stored from a user-supplied field?
>    - Was it sanitized or parameterized at write time?
>
> 4. **Server-side / hardcoded value** — the variable comes from config, an environment variable, a hardcoded constant, or server-side logic with no user influence — this site is NOT exploitable.
>
> **For each construction site, also check for mitigations that would prevent exploitation even if user input does reach it**:
> - Is the variable validated against an allowlist before use? (Only effective for dynamic identifiers like column/table names)
> - Is there a type cast that constrains the value? (e.g., `int(val)` — effective only in purely numeric SQL contexts)
> - Is there a custom escaping function? Note: custom escaping (`mysql_real_escape_string`, `addslashes`, homegrown sanitizers) is **not** equivalent to parameterization — still flag as Likely Vulnerable
>
> **Classification**:
> - **Vulnerable**: User input demonstrably reaches the interpolated variable with no effective mitigation.
> - **Likely Vulnerable**: User input probably reaches the variable (indirect flow) or only weak mitigation (custom escaping) is present.
> - **Not Vulnerable**: The variable is server-side only, OR effective parameterization / allowlist validation is in place.
> - **Needs Manual Review**: Cannot determine the variable's origin with confidence (passes through opaque helpers, complex conditional flows, or external libraries).
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # SQLi Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function name]
> - **Issue**: [e.g., "HTTP query param `username` flows directly into f-string SELECT query"]
> - **Taint trace**: [Step-by-step from entry point to construction site]
> - **Impact**: [What attacker can do]
> - **Remediation**: [Parameterized query, ORM equivalent, or allowlist for identifiers]
> - **Dynamic test**: [sqlmap command or manual curl payload]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Authentication/admin endpoint → CRITICAL
> - General data extraction → HIGH

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
4. Append the completion marker: `<!-- scan:sqli completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: flag any dynamic variable embedded in a SQL query string, regardless of origin. Do not attempt to trace user input in Phase 1 — that is Phase 2's job.
- **Phase 2 is purely taint analysis**: for each site found in Phase 1, trace the interpolated variable back to its origin. If it comes from a user-controlled source, the site is a real vulnerability.
- Focus on **raw SQL and ORM raw/unsafe methods**. Standard ORM query builder calls (`.filter()`, `.where(col: val)`, `.find()`) are safe by default — do not flag them.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
- Taint can flow indirectly: a request parameter may be extracted in a middleware, stored in a shared object, passed through several helper functions, and finally reach the query construction. Trace the full chain.
- Custom escaping (including `mysql_real_escape_string`, `addslashes`, or homegrown sanitizers) is **not** equivalent to parameterization — flag as Likely Vulnerable even if escaping is present.
- For dynamic identifiers (column/table names), parameterization cannot help — the only safe fix is allowlist validation. Flag any dynamic identifier without an allowlist, regardless of whether it appears user-controlled.
- Second-order injection is easy to miss: a value stored in the DB from user input may later be read and used unsafely in a raw query elsewhere in the codebase. In Phase 2, treat DB-read values as potentially tainted and trace back to where they were written.