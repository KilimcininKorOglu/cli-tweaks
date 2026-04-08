---
name: graphql
description: >-
  Detect GraphQL injection vulnerabilities in a codebase using a two-phase
  approach: first confirm GraphQL is in use and find sites where operation
  documents are built unsafely (concatenation, interpolation into query
  strings), then trace whether user input reaches those sites. If no GraphQL technology is found in Phase 1, Phase
  2 is skipped. Use when asked to find GraphQL injection, unsafe GraphQL
  document construction, or operation string injection bugs.
---

# GraphQL Injection Detection

You are performing a focused security assessment to find GraphQL injection vulnerabilities. This skill uses a two-phase approach with subagents: **recon** (confirm GraphQL usage and find every location where a GraphQL operation document is assembled unsafely) then **taint** (confirm whether user-supplied input reaches those assembly sites).

---

## What is GraphQL Injection

GraphQL injection occurs when user-controlled data is embedded into the **GraphQL document** (the query, mutation, or subscription string) rather than passed only through the **variables** map. The parser then interprets attacker-controlled syntax — new fields, aliases, directives, or fragments — which can bypass intent, reach unauthorized resolvers, or change server-side behavior when that document is executed or forwarded.

The core pattern: *unvalidated user input alters the structure or text of the GraphQL operation string passed to `execute`, `graphql`, a gateway client, or an HTTP body `query` field built from string operations.*

### What GraphQL Injection IS

- Concatenating or interpolating user input into an operation string: `` `query { user(id: "${id}") { name } }` ``, `"query { user(id: \"" + id + "\") { name } }"`
- Building the JSON `query` field for a downstream GraphQL HTTP request with string concat from request body or params
- Forwarding `req.body.query` (or similar) into another interpolated template that wraps or extends the operation
- Dynamic `gql` / `graphql-tag` template literals where a non-static expression changes document structure (not just a bound variable value inside a static document)
- Server-side code that selects or assembles operation text from user input (including "persisted query" ID → document maps without allowlisting)
- Wrappers around `graphql.execute()`, `graphqlHTTP`, Yoga/Apollo request pipeline where the first argument (document/source) is built from variables that could be user-influenced

### What GraphQL Injection is NOT

Do not flag these as GraphQL injection:

- **SQL injection in resolvers**: Resolver code that builds SQL from `args` — that is **SQL injection** (`sqli`), not this skill
- **NoSQL / command injection in resolvers**: Same — use the appropriate security scan skill
- **IDOR via GraphQL arguments**: Passing another user's ID in a **variables** JSON with a **static** document — authorization flaw, not document injection
- **Normal variable binding**: Static document with `{"query": "query($id: ID!) { user(id: $id) { name } }", "variables": {"id": userInput}}` — values are bound as variables; the document structure is fixed (still verify authorization in resolvers)
- **Introspection / field suggestion enabled**: Information disclosure and hardening topic; only flag as GraphQL injection if the finding is specifically about **injecting into the operation string**
- **Query depth / complexity DoS**: Rate limiting and cost analysis — different class

### Patterns That Prevent GraphQL Injection

**1. Static operation documents with variables**

```javascript
const GET_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) { name }
  }
`;
// execute(schema, GET_USER, null, context, { id: userId });
```

**2. Server uses standard HTTP handler; client sends document; server parses once**

The risk is not the mere presence of `req.body.query` on the server if the server only parses and executes it as the client's operation — injection in *that* path is client-side. Flag **server-side** construction of a **new** document that incorporates user strings before `execute` or before forwarding.

**3. Persisted queries / allowlisted operation IDs**

Document looked up by ID from a server-side registry; client cannot inject arbitrary document text.

**4. graphql-js `Source` with static string; dynamic values only in variableValues**

```javascript
graphql({ schema, source: staticQueryString, variableValues: { id: userId } });
```

---

## Vulnerable vs. Secure Examples

### Node.js — dynamic document for downstream API

```javascript
// VULNERABLE: user input in operation text
app.post('/proxy', async (req, res) => {
  const fragment = req.body.fragment;
  const query = `query { me { ${fragment} } }`;
  const data = await fetch('https://api.internal/graphql', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
});

// SECURE: static operation, user data only in variables
const PROXY_QUERY = `query ProxyMe { me { id name email } }`;
app.post('/proxy', async (req, res) => {
  const data = await fetch('https://api.internal/graphql', {
    method: 'POST',
    body: JSON.stringify({ query: PROXY_QUERY }),
  });
});
```

### Python — string format into execute

```python
# VULNERABLE
def run_custom_query(user_gql: str):
    document = f"query {{ user {{ {user_gql} }} }}"
    return graphql_sync(schema, document)

# SECURE: validate against allowlist of named operations or use static documents only
ALLOWED = {"id", "name", "email"}
fields = [f for f in requested_fields if f in ALLOWED]
document = "query { user { " + " ".join(ALLOWED.intersection(set(requested_fields))) + " } }"
# Better: fixed FieldNodes, not string building from user input
```

---

## Execution

### Phase 1: GraphQL Technology Recon and Injection Candidate Sites

Launch a subagent with the following instructions:

> **Goal**: (1) Determine whether this codebase uses GraphQL at all. (2) If it does, find every location where a GraphQL **operation document** (query/mutation/subscription source string) is built using string concatenation, interpolation, formatting, or dynamic assembly such that a variable could change the **document text** (not merely `variables` JSON). Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it for stack, API layout, and BFF/gateway patterns.
>
> **Part A — Is GraphQL used?**
>
> Search for:
> - Dependencies: `graphql`, `@apollo/server`, `apollo-server-express`, `@nestjs/graphql`, `graphql-yoga`, `@graphql-yoga/node`, `mercurius`, `strawberry-graphql`, `graphene`, `sangria`, `gqlgen`, `async-graphql`, `juniper`, `graphql-ruby`, Hot Chocolate / `GraphQL.Server`, etc.
> - Schema artifacts: `*.graphql`, `*.graphqls`, codegen config (e.g. GraphQL Code Generator)
> - Server routes or plugins mounting `/graphql` or similar
>
> Set the summary to exactly one of:
> - `GraphQL is used in this codebase.` (list libraries and main entry points)
> - `GraphQL is not used in this codebase.`
>
> **Part B — Injection candidate sites (only if GraphQL is used)**
>
> If GraphQL is **not** used, omit the "Injection Candidate Sites" section or state there are none. Do not invent candidates.
>
> If GraphQL **is** used, search for **unsafe document construction**:
>
> 1. **String concatenation / interpolation into operation text**:
>    - `` `query { ... ${x} ...}` ``, `"mutation { " + userFragment + " }"`
>    - `sprintf`, `format`, `%` formatting, `.format()` building `query` or `source` arguments
>
> 2. **Calls where the document argument is not a compile-time constant**:
>    - `graphql(schema, dynamicString, ...)`, `execute({ schema, document: parsedDynamic, ...})` where the string feeding `parse` or `execute` is built from non-static parts
>    - `graphqlHTTP({ schema, rootValue, context: (req) => ({ query: req.body.query + something }) })` patterns that **mutate** or **wrap** the query string with user data
>
> 3. **HTTP clients forwarding a constructed GraphQL body**:
>    - `JSON.stringify({ query: `...${userPart}...` })`, `axios.post(url, { query: builtFromInput })`
>
> 4. **Unsafe persisted / stored query lookup**:
>    - Operation text loaded by key from user input without allowlist → file path or DB value becomes document source
>
> **What to skip** (do not flag as Phase 1 candidates):
> - Fully static `source` / `query` strings; only `variableValues` / `variables` come from the request
> - Schema definition with `buildSchema` / SDL files with no user interpolation
> - Resolver implementations that only use args with parameterized DB APIs (optional: note "resolver uses ORM" but not a GraphQL injection candidate unless the **document** is built unsafely)
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # GraphQL Recon: [Project Name]
>
> ## Summary
> GraphQL is [used / not used] in this codebase.
> [If used: libraries, main server files, typical endpoint paths]
> Found [N] injection candidate site(s) where operation documents may be built unsafely. [If not used, say N/A or 0 and skip candidate list]
>
> ## GraphQL Surface (only if used)
> - **Libraries / frameworks**: ...
> - **Entry points**: ...
> - **Notable files**: ...
>
> ## Injection Candidate Sites
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: ...
> - **Execution / call pattern**: [graphql.execute / fetch with body / gql template / etc.]
> - **Construction pattern**: [concat / template literal / format / forwarded body mutation]
> - **Interpolated variable(s)**: ...
> - **Code snippet**:
>   ```
>   ...
>   ```
>
> [Repeat for each site; if none, write "No injection candidate sites found." under the heading]
> ```

### Phase 2: Batched Verify — Trace User Input to Injection Candidate Sites

After Phase 1 completes (and only if both gates passed: GraphQL used and at least one candidate site), count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

>
>
> **For each site, trace dynamic values backward**:
>
> 1. **Direct user input** — query params, path params, JSON body fields (including nested `query` if re-wrapped), headers, cookies
> 2. **Indirect user input** — helpers, middleware, context builders
> 3. **Second-order** — stored preferences or DB fields later used to build a document; trace write path
> 4. **Server-only** — config, env, hardcoded fragments — not exploitable from the client
>
> **Mitigations**:
> - Allowlist of fields or operation IDs before any string assembly
> - Parser validation that rejects unexpected definitions (still prefer no user-controlled document structure)
>
> **Classification**:
> - **Vulnerable**: User-controlled data reaches document construction with no effective mitigation
> - **Likely Vulnerable**: Probable taint or weak sanitization
> - **Not Vulnerable**: Server-side-only or effective allowlist / static document path
> - **Needs Manual Review**: Opaque flow
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # GraphQL Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or resolver]
> - **Issue**: [description of taint flow]
> - **Taint trace**: [Step-by-step from source to document construction]
> - **Impact**: [What attacker can do]
> - **Remediation**: [Static documents, allowlist, etc.]
> - **Dynamic test**: [curl command or payload]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Unauthorized data access / mutation → HIGH
> - Introspection / batching abuse → MEDIUM

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Verification**: include the full taint trace and a dynamic test command or payload
   - For **Suggested Commit**: conventional commit message without BUG-IDs
4. Append the completion marker: `<!-- scan:graphql completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- **If Phase 1 finds no GraphQL technology, skip Phase 2 and Phase 3**.
- **If GraphQL is used but Phase 1 finds no injection candidates, skip Phase 2 and Phase 3**.
- Phase 1 does **not** trace taint; Phase 2 does.
- Resolver-layer SQL/NoSQL issues belong to other skills; this skill targets **operation document** construction.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable".