---
name: hardcoded-secrets
description: >-
  Detect hardcoded sensitive data (API keys, access tokens, private keys,
  passwords, connection strings) in source code using a three-phase approach:
  recon (find secret candidates via regex and variable name patterns),
  batched verify (confirm real secrets and assess exposure in parallel
  subagents, 3 candidates each), and merge (write confirmed findings to
  BUG-REPORT.md). Use when asked to find hardcoded secrets, leaked API keys,
  exposed credentials, or hardcoded passwords.
---

# Hardcoded Secrets Detection

You are performing a focused security assessment to find hardcoded sensitive data in a codebase. This skill uses a three-phase approach with subagents: **recon** (find all potential secret candidates), **batched verify** (confirm each is a real secret and assess exposure, in parallel batches of 3), and **merge** (consolidate results into `BUG-REPORT.md`).

---

## What Are Hardcoded Secrets

Hardcoded secrets are sensitive credentials -- API keys, access tokens, private keys, passwords, signing secrets, database connection strings -- embedded directly in source code as string literals instead of being loaded from environment variables or secret managers.

The core question: *Is this a real credential committed to the repository?*

### Severity by Exposure

| Exposure | Severity | Rationale |
|----------|----------|-----------|
| Frontend/client code (browser JS, mobile app source) | CRITICAL | Extractable by any external attacker |
| Backend code in a public repository | HIGH | Accessible to anyone who finds the repo |
| Backend code in a private repository | MEDIUM | Exposed to all repo collaborators, risk if repo leaks |
| Test/development key in non-test code | LOW | May indicate prod keys follow same pattern |

### What IS a Hardcoded Secret

- API key string literals: `const apiKey = "AKIA1234567890EXAMPLE"`
- Token assignments: `token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`
- Password literals: `password = "s3cretP@ss!"`
- Private key blocks: `-----BEGIN RSA PRIVATE KEY-----`
- Connection strings with credentials: `postgresql://admin:p4ssw0rd@db.example.com/prod`
- JWT signing secrets: `JWT_SECRET = "my-super-secret-key-12345"`
- Base64-encoded credentials in auth headers

### What is NOT a Hardcoded Secret

Do not flag these:

- **Environment variable reads**: `process.env.API_KEY`, `os.environ["SECRET"]`, `ENV["KEY"]`
- **Placeholder values**: `"your-api-key-here"`, `"TODO"`, `"xxx"`, `"changeme"`, `"REPLACE_ME"`, `"<api_key>"`, `"dummy"`, `"test"`, `"example"`, `"sample"`
- **Empty strings**: `""`, `''`
- **Public keys** (non-private cryptographic keys are designed to be shared)
- **Publishable API keys**: Stripe `pk_live_*`, Firebase client config `apiKey`, Google Maps browser key
- **Type definitions**: `apiKey: string` (no actual value)
- **Documentation strings**: Comments describing what a key looks like
- **Hash values**: SHA256/MD5 checksums, content hashes
- **Build constants**: Version strings, build IDs, commit hashes
- **Test fixtures**: Keys clearly inside test files used only for testing

---

## Types of Secrets to Search For

### High-Confidence Regex Patterns

| Secret Type                    | Pattern                                              |
|--------------------------------|------------------------------------------------------|
| AWS Access Key ID              | `AKIA[0-9A-Z]{16}`                                  |
| AWS Secret Access Key          | 40-char base64 string near an `AKIA` key             |
| Google API Key                 | `AIza[0-9A-Za-z\-_]{35}`                             |
| Google OAuth Client Secret     | `GOCSPX-[0-9A-Za-z\-_]{28}`                          |
| GitHub Token                   | `ghp_[0-9A-Za-z]{36}`, `github_pat_[0-9A-Za-z_]{82}` |
| GitLab Token                   | `glpat-[0-9A-Za-z\-_]{20}`                           |
| Slack Token                    | `xoxb-`, `xoxp-`, `xoxa-`, `xoxr-`                   |
| Slack Webhook URL              | `hooks.slack.com/services/T[A-Z0-9]+/B[A-Z0-9]+/`    |
| Stripe Secret Key              | `sk_live_[0-9A-Za-z]{24,}`, `sk_test_[0-9A-Za-z]{24,}` |
| SendGrid API Key               | `SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}`        |
| Twilio Account SID             | `AC[0-9a-f]{32}`                                     |
| OpenAI API Key                 | `sk-[A-Za-z0-9]{48}`, `sk-proj-[A-Za-z0-9\-_]{100,}` |
| Anthropic API Key              | `sk-ant-[A-Za-z0-9\-_]{90,}`                         |
| Private Key Header             | `-----BEGIN (RSA\|EC\|OPENSSH\|DSA)?PRIVATE KEY-----` |
| DB Connection String           | `(postgresql\|mysql\|mongodb\|redis)://[^:]+:[^@]+@`  |
| Heroku API Key                 | UUID format in Heroku context                         |
| Azure Storage Key              | ~88 char base64 string assigned to storage key var    |
| Mailgun API Key                | `key-[0-9a-zA-Z]{32}`                                |
| Firebase Admin/Server Key      | Service account JSON with `private_key` field         |

### Variable Name Patterns (Require Value Inspection)

Search for variables with these name patterns and check if the assigned value looks like a real credential:

- `api_key`, `apiKey`, `API_KEY`
- `secret`, `SECRET`, `secret_key`, `secretKey`, `SECRET_KEY`
- `access_token`, `accessToken`, `ACCESS_TOKEN`
- `auth_token`, `authToken`, `AUTH_TOKEN`
- `private_key`, `privateKey`, `PRIVATE_KEY`
- `password`, `PASSWORD`, `passwd`, `PASSWD`
- `client_secret`, `clientSecret`, `CLIENT_SECRET`
- `signing_key`, `signingKey`, `SIGNING_KEY`
- `encryption_key`, `encryptionKey`, `ENCRYPTION_KEY`
- `connection_string`, `connectionString`, `DATABASE_URL`
- `bearer_token`, `BEARER_TOKEN`

---

## Execution

### Phase 1: Recon -- Find Secret Candidates

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where a hardcoded secret (API key, access token, private key, password, signing secret, connection string) appears as a string literal. Return all findings in your response.
>
> **What to search for**:
>
> Scan the entire codebase. Flag ALL potential secrets regardless of frontend vs. backend location -- exposure assessment is Phase 2's job.
>
> 1. **High-confidence regex patterns**: AWS keys (`AKIA`), Google API keys (`AIza`), GitHub tokens (`ghp_`, `github_pat_`), Slack tokens (`xoxb-`, `xoxp-`), Stripe keys (`sk_live_`, `sk_test_`), SendGrid (`SG.`), OpenAI (`sk-`), Anthropic (`sk-ant-`), private key headers (`-----BEGIN.*PRIVATE KEY-----`), connection strings with embedded passwords (`://user:pass@`)
>
> 2. **Variable assignment patterns**: Variables named `apiKey`, `api_key`, `secret`, `token`, `password`, `client_secret`, `signing_key` etc. assigned string literal values that look like real credentials (20+ random characters, hex strings, base64)
>
> 3. **Inline string literals**: Long random alphanumeric strings (32+ chars) in auth contexts, base64-encoded strings in authentication code, UUIDs used as API keys
>
> **What to skip**: environment variable reads (`process.env.*`, `os.environ[*]`), type definitions with no values, obvious placeholders (`"your-key-here"`, `"changeme"`, `"TODO"`, empty strings), comments, public keys, hash checksums, files in `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `__pycache__/`
>
> **Output format** -- return in your response:
>
> ```markdown
> # Hardcoded Secrets Recon: [Project Name]
>
> ## Summary
> Found [N] potential hardcoded secret candidates.
>
> ## Candidates
>
> ### 1. [Descriptive name -- e.g., "AWS Access Key in API config"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Secret type**: [AWS key / Google API key / Generic API key / Private key / Password / JWT secret / Connection string / etc.]
> - **Variable/context**: [variable name or context]
> - **Detection method**: [regex match / variable name pattern / inline literal]
> - **Code snippet**:
>   ```
>   [line(s) with secret REDACTED: "AKIA****WXYZ"]
>   ```
>
> [Repeat for each candidate]
> ```

### Phase 2: Batched Verify -- Confirm Real Secrets and Assess Exposure

After Phase 1 completes, count the numbered candidate sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer candidates**: Launch a single subagent with all candidates (skip batching).

**If more than 3 candidates**: Split into batches of up to 3 each. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions:

> **Goal**: Verify the following hardcoded secret candidates. For each one, determine (1) whether it is a real secret and (2) assess its exposure level. Return findings in your response.
>
> **Your assigned candidates** (from the recon phase):
>
> [Paste full text of assigned candidate sections, preserving original numbering]
>
> **For each candidate, answer TWO questions:**
>
> **Question 1: Is this a real secret?**
> - Does the string have the entropy and format of a real key/token? (20+ random characters)
> - Is it a placeholder? ("your-key-here", "changeme", "test", "example", "TODO", "xxx")
> - Is it a test/dev key? (Stripe `sk_test_*`, sandbox credentials)
> - Is it a public/publishable key by design? (Stripe `pk_live_*`, Firebase client `apiKey`)
> - Is it an environment variable reference picked up by mistake?
> - Is it a hash, checksum, or non-secret identifier?
>
> **Question 2: What is the exposure level?**
> - **Frontend/client-side**: Browser JS (React, Vue, Angular, Svelte), Next.js client components (`"use client"`), mobile app source, files in `public/`/`static/`/`assets/`, Electron source, HTML inline scripts → CRITICAL
> - **Backend in likely-public repo**: Server-side code that may be in a public GitHub repo → HIGH
> - **Backend in private context**: Server-side only, private repo assumed → MEDIUM
> - **Test/dev key not in test files**: Test credential outside test directory → LOW
>
> **Classification**:
> - **Vulnerable**: Confirmed real secret with confirmed exposure path
> - **Likely Vulnerable**: Appears real but cannot fully confirm (ambiguous import chain, uncertain if production key)
> - **Not Vulnerable**: Placeholder, test key, public key, or env var reference
> - **Needs Manual Review**: Cannot determine if real or exposure level
>
> **Output format** -- return in your response:
>
> ```markdown
> # Hardcoded Secrets Batch [N] Results
>
> ## Findings
>
> ### [CLASSIFICATION] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Secret type**: [type]
> - **Exposure**: [Frontend/Backend-public/Backend-private/Test]
> - **Issue**: [description]
> - **Impact**: [what attacker can do]
> - **Evidence**: [code snippet, REDACTED]
> - **Remediation**: [fix recommendation]
> - **Verification**: [how to confirm]
> ```

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity based on exposure level
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - Include all fields: Severity, Status, File, Component, Suggested Commit, Problem, Expected, Root Cause, Impact, Verification
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

**Severity mapping for BUG-REPORT.md**:
- Frontend/client-side secret → CRITICAL
- Backend secret in public context → HIGH
- Backend secret in private context → MEDIUM
- Test/dev key in wrong location → LOW

---

## Important Reminders

- Phase 2 must run AFTER Phase 1 completes -- it depends on the recon output.
- Phase 3 must run AFTER all Phase 2 batches complete.
- Batch size is **3 candidates per subagent**. If 1-3 total, use a single subagent.
- Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Each batch subagent receives only its assigned candidates, not all findings.
- **REDACT secrets in output**: Always partially redact secret values (e.g., `AKIA****WXYZ`, `sk_live_****abcd`). Never write full secret values.
- Firebase client config (`apiKey`, `authDomain`, `projectId`) is NOT a secret -- only flag Firebase admin/service account keys.
- Stripe publishable keys (`pk_live_*`, `pk_test_*`) are NOT secrets -- only flag secret keys (`sk_live_*`, `sk_test_*`).
- `NEXT_PUBLIC_*`, `REACT_APP_*`, `VITE_*` env var references are NOT hardcoded -- only flag if the actual value is in source code.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable".

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
