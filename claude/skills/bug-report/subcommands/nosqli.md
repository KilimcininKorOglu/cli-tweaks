---
name: nosqli
description: >-
  Detect NoSQL injection vulnerabilities using a two-phase approach:
  first find NoSQL query sites (MongoDB operator injection, $where JavaScript
  execution, Redis EVAL, Elasticsearch query_string), then trace whether
  user-supplied input reaches those sites. Use when asked to find NoSQL injection bugs.
---

# NoSQL Injection (NoSQLi) Detection

You are performing a focused security assessment to find NoSQL injection vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **discovery** (find all places where NoSQL queries are constructed with dynamic input) then **verify** (confirm whether user-supplied input reaches those query sites and can manipulate query logic).

---

## What is NoSQL Injection

NoSQL injection occurs when user-supplied input is incorporated into NoSQL database queries in a way that allows attackers to alter query logic. Unlike SQL injection, NoSQLi exploits operator injection (MongoDB `$gt`, `$ne`, `$regex`), JSON structure manipulation, and JavaScript execution contexts (`$where`, `$function`). The core pattern: *unvalidated user input reaches a NoSQL query where it can inject operators, modify query structure, or execute arbitrary code.*

### What NoSQLi IS

- MongoDB operator injection: `req.body.password` passed as `{ $ne: "" }` bypasses equality check
- `$where` JavaScript injection: user input concatenated into `$where` expression string
- JSON structure manipulation: user-controlled JSON body merged directly into query object
- Redis `EVAL` with user input in Lua script: `redis.eval(f"return redis.call('get', '{input}')")`
- Elasticsearch `query_string` with raw user input allowing Lucene syntax injection
- MongoDB `$regex` injection: user input as regex pattern enabling ReDoS or data extraction
- Auth bypass via operator injection: `{ username: "admin", password: { "$ne": "" } }`

### What NoSQLi is NOT

Do not flag these as NoSQLi:

- **SQL injection**: Injecting into SQL queries — separate vulnerability class
- **Safe ORM queries**: Mongoose with schema validation, Prisma MongoDB adapter, Spring Data MongoDB `Criteria` API
- **Hardcoded queries**: Query objects built entirely from constants, not user input
- **Internal service queries**: Database calls with parameters from trusted internal services
- **Aggregation with static pipeline**: Pipeline stages defined in code with only parameterized values

### Patterns That Prevent NoSQLi

When you see these patterns, the code is likely **not vulnerable**:

**1. Type validation before query**
```javascript
if (typeof req.body.username !== 'string' || typeof req.body.password !== 'string') {
  return res.status(400).json({ error: 'Invalid input' });
}
const user = await User.findOne({ username: req.body.username, password: req.body.password });
```

**2. Sanitization library**
```javascript
const mongoSanitize = require('express-mongo-sanitize');
app.use(mongoSanitize()); // Strips $ and . from req.body/query/params
```

**3. Schema validation (Mongoose)**
```javascript
const userSchema = new Schema({
  username: { type: String, required: true },
  password: { type: String, required: true }
});
// Schema enforces string type — objects with $ne cannot pass
```

**4. Standard query operators instead of $where**
```javascript
// Safe: using standard operators instead of JavaScript execution
const results = await collection.find({ category: req.query.category });
```

---

## Vulnerable vs. Secure Examples

### MongoDB — Operator Injection (Auth Bypass)

```javascript
// VULNERABLE: JSON body passed directly into query
app.post('/login', async (req, res) => {
  const user = await User.findOne({
    username: req.body.username,
    password: req.body.password
  });
  // Attack: POST {"username":"admin","password":{"$ne":""}}
  // Returns admin user — password field matches any non-empty value
});

// SECURE: Type validation
app.post('/login', async (req, res) => {
  if (typeof req.body.username !== 'string' || typeof req.body.password !== 'string') {
    return res.status(400).json({ error: 'Invalid input' });
  }
  const user = await User.findOne({
    username: req.body.username,
    password: await bcrypt.hash(req.body.password, salt)
  });
});
```

### MongoDB — $where JavaScript Injection

```javascript
// VULNERABLE: User input in $where string
app.get('/search', async (req, res) => {
  const results = await collection.find({
    $where: `this.category == '${req.query.category}'`
  });
  // Attack: ?category=' || true || '
  // Executes: this.category == '' || true || '' — returns all documents
});

// SECURE: Use standard query operators
app.get('/search', async (req, res) => {
  const results = await collection.find({
    category: req.query.category
  });
});
```

### MongoDB — $regex Injection

```javascript
// VULNERABLE: User input as regex
app.get('/search', async (req, res) => {
  const results = await collection.find({
    name: { $regex: req.query.pattern }
  });
  // Attack: ?pattern=.*  — returns all documents
  // Attack: ?pattern=^a(a+)+$  — ReDoS
});

// SECURE: Escape special characters
const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
app.get('/search', async (req, res) => {
  const results = await collection.find({
    name: { $regex: escapeRegex(req.query.pattern) }
  });
});
```

### Python — PyMongo

```python
# VULNERABLE: JSON-parsed body merged into query
@app.route('/search', methods=['POST'])
def search():
    query = request.json  # {"field": {"$gt": ""}} — attacker controls structure
    results = db.collection.find(query)
    return jsonify(list(results))

# SECURE: Build query with validated fields
@app.route('/search', methods=['POST'])
def search():
    name = request.json.get('name')
    if not isinstance(name, str):
        return abort(400)
    results = db.collection.find({"name": name})
    return jsonify(list(results))
```

### Redis — EVAL Injection

```python
# VULNERABLE: User input in Lua script
def get_cache(key):
    script = f"return redis.call('get', '{key}')"
    return redis_client.eval(script, 0)
# Attack: key = "') redis.call('flushall') --"

# SECURE: Use parameterized Redis commands
def get_cache(key):
    return redis_client.get(key)
```

### Elasticsearch — Query String Injection

```javascript
// VULNERABLE: Raw user input in query_string
app.get('/search', async (req, res) => {
  const results = await client.search({
    query: { query_string: { query: req.query.q } }
  });
  // Attack: ?q=*:* OR _exists_:password — access all docs or sensitive fields
});

// SECURE: Use match query (no Lucene syntax)
app.get('/search', async (req, res) => {
  const results = await client.search({
    query: { match: { content: req.query.q } }
  });
});
```

### Java — Spring Data MongoDB

```java
// VULNERABLE: Raw query from user input
@PostMapping("/search")
public List<User> search(@RequestBody String queryJson) {
    BasicQuery query = new BasicQuery(queryJson);  // Full operator injection
    return mongoTemplate.find(query, User.class);
}

// SECURE: Criteria API
@PostMapping("/search")
public List<User> search(@RequestParam String name) {
    Query query = new Query(Criteria.where("name").is(name));
    return mongoTemplate.find(query, User.class);
}
```

---

## Execution

### Phase 1: Find NoSQL Query Sites with Dynamic Input

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where a NoSQL query is constructed with any dynamic variable — regardless of where that variable comes from. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, database layer (MongoDB, Redis, Elasticsearch, etc.), and ORM/driver patterns.
>
> **What to search for — vulnerable query construction patterns**:
>
> 1. **MongoDB query objects with dynamic values from request**:
>    - `collection.find(req.body)`, `Model.findOne(req.body)`
>    - Query objects where fields are assigned from variables: `{ field: variable }`
>    - `collection.find(JSON.parse(userInput))`, `db.collection.find(query)` where query is user-built
>
> 2. **MongoDB operator-susceptible patterns**:
>    - Direct body/query param as query field value without type checking
>    - `$where` with string concatenation or interpolation: `$where: \`this.x == '${var}'\``
>    - `$regex` with user-supplied pattern
>    - `$expr`, `$function` with dynamic code
>
> 3. **Redis command injection**:
>    - `redis.eval()` with f-string/template literal script
>    - `redis.send_command()` with dynamic command construction
>    - String concatenation in Redis Lua scripts
>
> 4. **Elasticsearch injection**:
>    - `query_string` query type with user input
>    - `script` fields with user-supplied code
>    - Raw JSON query body from user input
>
> 5. **ORM raw/unsafe methods**:
>    - Mongoose `$where`, `.find()` with raw object from request
>    - Spring Data MongoDB `BasicQuery(userInput)`, raw query strings
>    - PyMongo `find()` with unsanitized dict from request
>
> **What to skip**:
> - Mongoose/Prisma schema-validated queries where types are enforced
> - Hardcoded query objects with no dynamic parts
> - Aggregation pipelines with static structure (only literal values parameterized)
> - Test/seed scripts that do not handle user input
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # NoSQLi Recon: [Project Name]
>
> ## Summary
> Found [N] locations where NoSQL queries use dynamic input.
>
> ## Query Sites
>
> ### 1. [Descriptive name — e.g., "Direct req.body in findOne query"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or route]
> - **Database / driver**: [MongoDB/Mongoose / Redis / Elasticsearch / etc.]
> - **Query method**: [find / findOne / aggregate / eval / query_string / etc.]
> - **Dynamic variable(s)**: `var_name` — [brief note on what it appears to be]
> - **Injection vector**: [operator injection / $where JS / JSON structure / Lua script / Lucene syntax]
> - **Code snippet**:
>   ```
>   [the vulnerable query construction]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Trace User Input to NoSQL Query Sites

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand request parsing, body parser configuration, and middleware chain.
>
> **For each query site, trace the dynamic variable(s) backwards to their origin**:
>
> 1. **Direct user input**: Is the variable assigned from request body, query params, headers, or cookies?
>    - Check body parser: does `req.body` parse JSON? (express `json()` middleware enables object injection)
>    - Check content type: does the endpoint accept `application/json`?
>
> 2. **Type checking**: Is there type validation between input and query?
>    - `typeof variable !== 'string'` check → prevents object/operator injection
>    - Schema validation (Joi, Zod, express-validator) → prevents structure manipulation
>    - Mongoose schema type enforcement → prevents operator injection at schema level
>
> 3. **Sanitization**: Is there a sanitization layer?
>    - `express-mongo-sanitize` middleware → strips `$` and `.` from input
>    - Custom sanitization function → check if it strips all operators
>    - Input length limits → insufficient alone but reduces attack surface
>
> 4. **Context assessment**: What does successful injection achieve?
>    - Authentication bypass → CRITICAL
>    - Data exfiltration (reading other users' data) → HIGH
>    - Filter bypass (seeing more results than intended) → MEDIUM
>    - Error-based info disclosure → LOW
>
> **Classification**:
> - **Vulnerable**: User input reaches query with no type validation or sanitization; operator injection is possible.
> - **Likely Vulnerable**: Some validation exists but is incomplete (e.g., checks username type but not password).
> - **Not Vulnerable**: Strict type validation, mongo-sanitize middleware, or Prisma/schema-enforced queries.
> - **Needs Manual Review**: Validation in external middleware or complex conditional flows.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # NoSQLi Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function name]
> - **Issue**: [e.g., "req.body.password passed to findOne without type check — operator injection possible"]
> - **Taint trace**: [Step-by-step from entry point to query site]
> - **Proof of concept**: `curl -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":{"$ne":""}}' http://target/login`
> - **Impact**: [Authentication bypass / data exfiltration / etc.]
> - **Remediation**: Add type validation (`typeof x === 'string'`), use express-mongo-sanitize, or switch to parameterized query pattern
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Authentication bypass via operator injection → CRITICAL
> - JavaScript execution via $where/$function injection → CRITICAL
> - Data exfiltration through query manipulation → HIGH
> - Filter/search bypass → MEDIUM

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the proof of concept payload and taint trace
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all NoSQL query sites with dynamic input, regardless of origin. Do not attempt to trace user input in Phase 1 — that is Phase 2's job.
- **Phase 2 is purely taint analysis**: for each site found in Phase 1, trace the dynamic variable back to its origin and check for type validation/sanitization.
- The most critical NoSQLi pattern is **operator injection in authentication queries** — `{ password: { $ne: "" } }` bypasses equality checks and is trivial to exploit.
- Body parser configuration matters: Express `json()` middleware parses JSON bodies into objects, enabling operator injection. Without JSON parsing, `req.body` fields are strings only.
- `$where` and `$function` enable **arbitrary JavaScript execution** on the database server — treat these as equivalent to RCE in severity.
- `express-mongo-sanitize` is the standard mitigation for MongoDB operator injection in Express apps — check if it is installed and applied globally.
- Mongoose schema validation prevents some attacks but NOT all. A `String` type in schema prevents object injection for that field, but `Mixed` or untyped fields remain vulnerable.
- Redis `EVAL` with string interpolation is equivalent to SQL injection in Redis context — the Lua script can execute arbitrary Redis commands.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
