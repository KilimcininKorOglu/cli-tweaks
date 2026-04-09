---
name: ldap
description: >-
  Detect LDAP injection vulnerabilities where user input is incorporated into
  LDAP search filters or Distinguished Name strings without proper escaping.
  Enables authentication bypass, unauthorized directory access, and information
  disclosure. Use when asked to find LDAP injection bugs.
---

# LDAP Injection Detection

You are performing a focused security assessment to find LDAP injection vulnerabilities. This skill uses a three-phase approach: **recon** (find LDAP query construction sites), **batched verify** (trace user input to those sites), and **merge** (write confirmed findings to `BUG-REPORT.md`).

---

## What is LDAP Injection

LDAP injection occurs when user-supplied input is incorporated into LDAP search filters or Distinguished Name (DN) strings through string concatenation or interpolation rather than proper escaping. This allows attackers to modify filter logic, bypass authentication, enumerate directory entries, and access unauthorized data.

The core pattern: *unescaped user input reaches an LDAP filter or DN construction.*

### What LDAP Injection IS

- Concatenating user input into an LDAP filter: `"(&(uid=" + username + ")(userPassword=" + password + "))"`
- F-string/template literal in filter: `f"(&(uid={username})(userPassword={password}))"`
- DN construction with user input: `"uid=" + username + ",ou=users,dc=example,dc=com"`
- Attack payload: `admin)(|(uid=*` → modifies filter to match ALL users, bypassing password

### What LDAP Injection is NOT

Do not flag these:
- **Hardcoded LDAP filters**: Filters built entirely from constants
- **LDAP connection setup**: Configuration without user-controlled filter values
- **Schema queries**: Querying LDAP schema with fixed filters
- **Properly escaped input**: Using `LdapEncoder.filterEncode()`, `escape_filter_chars()`, `ldap_escape()`
- **Input validated as UUID/email**: Strict validation preventing special characters

### Patterns That Prevent LDAP Injection

```java
// Java — LdapEncoder (Spring LDAP)
String safeUser = LdapEncoder.filterEncode(username);
String filter = "(&(uid=" + safeUser + ")(userPassword=" + safePass + "))";
```

```python
# Python — ldap3 escape
from ldap3.utils.conv import escape_filter_chars
safe_user = escape_filter_chars(username)
search_filter = f"(&(uid={safe_user})(userPassword={safe_pass}))"
```

```php
// PHP — ldap_escape
$safe_user = ldap_escape($username, '', LDAP_ESCAPE_FILTER);
$filter = "(&(uid=$safe_user)(userPassword=$safe_pass))";
```

```csharp
// C# — manual escaping of special chars
var safeUser = username.Replace("\\", "\\5c").Replace("*", "\\2a")
    .Replace("(", "\\28").Replace(")", "\\29").Replace("\0", "\\00");
```

### LDAP Special Characters

Characters requiring escaping in search filters: `*`, `(`, `)`, `\`, `NUL`
Characters requiring escaping in DNs: `,`, `+`, `"`, `\`, `<`, `>`, `;`

---

## Vulnerable vs. Secure Examples

### Java — JNDI

```java
// VULNERABLE: String concatenation in LDAP filter
String filter = "(&(uid=" + username + ")(userPassword=" + password + "))";
NamingEnumeration results = ctx.search("ou=users,dc=example,dc=com", filter, controls);

// SECURE: Escape before concatenation
String safeUser = LdapEncoder.filterEncode(username);
String safePass = LdapEncoder.filterEncode(password);
String filter = "(&(uid=" + safeUser + ")(userPassword=" + safePass + "))";
```

### Python — ldap3 / python-ldap

```python
# VULNERABLE: f-string interpolation
search_filter = f"(&(uid={username})(userPassword={password}))"
conn.search('ou=users,dc=example,dc=com', search_filter)

# SECURE: escape_filter_chars
from ldap3.utils.conv import escape_filter_chars
safe_user = escape_filter_chars(username)
safe_pass = escape_filter_chars(password)
search_filter = f"(&(uid={safe_user})(userPassword={safe_pass}))"
```

### PHP

```php
// VULNERABLE
$filter = "(&(uid=$username)(userPassword=$password))";
$result = ldap_search($conn, "ou=users,dc=example,dc=com", $filter);

// SECURE
$safe_user = ldap_escape($username, '', LDAP_ESCAPE_FILTER);
$safe_pass = ldap_escape($password, '', LDAP_ESCAPE_FILTER);
$filter = "(&(uid=$safe_user)(userPassword=$safe_pass))";
```

### C# — DirectorySearcher

```csharp
// VULNERABLE
var searcher = new DirectorySearcher();
searcher.Filter = $"(&(uid={username})(userPassword={password}))";

// SECURE
var safeUser = EscapeLdapFilter(username);
searcher.Filter = $"(&(uid={safeUser})(userPassword={safePass}))";
```

---

## Execution

### Phase 1: Find LDAP Query Construction Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location where an LDAP filter or DN is constructed with any dynamic variable. Return findings in your response.
>
> **What to search for**:
>
> 1. **LDAP library usage**: `ldap_search`, `ldap_bind`, `ldap_connect`, `LdapConnection`, `DirContext`, `InitialDirContext`, `SearchControls`, `ldap3`, `python-ldap`, `DirectorySearcher`, `SearchRequest`
>
> 2. **Filter construction with variables**: Any string containing `(&(`, `(|(`, `objectClass=` where a variable is interpolated or concatenated
>
> 3. **DN construction with variables**: Any string building a DN path (`uid=`, `cn=`, `ou=`, `dc=`) with user-controlled values
>
> **What to skip**: Hardcoded filters with no variables, LDAP connection configuration, schema queries
>
> **Output format** — return in your response:
>
> ```markdown
> # LDAP Recon: [Project Name]
>
> ## Summary
> Found [N] LDAP query construction sites.
>
> ## Construction Sites
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function or route]
> - **Query type**: [search filter / DN construction / bind operation]
> - **Construction pattern**: [string concat / f-string / template literal]
> - **Interpolated variable(s)**: `var_name`
> - **Code snippet**:
>   ```
>   [the vulnerable construction]
>   ```
> ```

### Phase 2: Batched Verify — Trace User Input to LDAP Sites

After Phase 1 completes, count numbered sites. If 3 or fewer, single subagent. Otherwise batch 3/subagent, parallel.

> **For each site, trace the interpolated variable backwards**:
>
> 1. **Direct user input**: HTTP params, request body, headers, cookies
> 2. **Indirect user input**: Derived through functions, intermediate assignments
> 3. **Server-side value**: Config, env, constant — NOT exploitable
>
> **Check for mitigations**:
> - Language-specific LDAP escape function applied? (`LdapEncoder.filterEncode`, `escape_filter_chars`, `ldap_escape`)
> - Input validated against strict pattern (UUID, email regex)?
> - Parameterized LDAP search API used?
>
> **Classification**:
> - **Vulnerable**: User input reaches LDAP filter/DN without escaping
> - **Likely Vulnerable**: Indirect flow or weak custom escaping
> - **Not Vulnerable**: Server-side only or proper escaping in place
> - **Needs Manual Review**: Cannot determine origin
>
> **Output format** — return in your response:
>
> ```markdown
> # LDAP Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / function**: [route or function]
> - **Issue**: [description of taint flow]
> - **Taint trace**: [step-by-step from source to LDAP call]
> - **Impact**: [auth bypass, directory enumeration, etc.]
> - **Remediation**: [use escape function]
> - **Dynamic test**: [payload example]
> ```

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - Separate each field with a blank line; end each entry with a `---` separator
4. Append the completion marker: `<!-- scan:ldap completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries.

**Severity mapping**:
- Authentication bypass via filter injection → CRITICAL
- Unauthorized directory enumeration → HIGH
- Limited scope filter manipulation → MEDIUM
- Injection in admin-only tools → LOW

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1. Phase 3 runs AFTER all batches.
- Batch size: 3 sites per subagent. If 1-3 total, single subagent. All parallel.
- LDAP injection is most critical in authentication flows — prioritize login/bind operations.
- Custom escaping (replacing only `*` or `(`) is insufficient — all 5 filter special characters must be escaped.
- DN injection has different special characters than filter injection — check both.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
