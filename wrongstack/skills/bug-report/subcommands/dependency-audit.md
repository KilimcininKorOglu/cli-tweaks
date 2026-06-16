---
name: dependency-audit
description: >-
  Audit project dependencies for supply chain risks: known CVEs in outdated
  packages, typosquatting, dependency confusion, malicious build scripts, and
  license compliance issues across all major package ecosystems.
---

# Supply Chain Security Audit (Dependency Audit)

You are performing a comprehensive supply chain security audit of all project dependencies. Unlike other scans, this is a **single-phase comprehensive audit** — not the 3-phase recon/verify model — because dependency analysis requires holistic examination of manifest files, lock files, and their relationships.

---

## What is Supply Chain Risk

Supply chain attacks target the dependency graph rather than application code. Attackers compromise or impersonate packages that applications depend on. The attack surface includes: known vulnerabilities in outdated packages (CVEs), typosquatting (packages with names similar to popular ones), dependency confusion (public package claiming a private package's name), and malicious build scripts (code that executes during `npm install` or `pip install`).

### What Supply Chain Risk IS

- Using a package version with a known CVE (e.g., `log4j` < 2.17.1, `lodash` < 4.17.21)
- Installing a typosquatted package: `lodassh` instead of `lodash`
- Missing lock file — allows dependency resolution to pull different versions at build time
- `postinstall` scripts in dependencies that make network calls or execute binaries
- Dependency confusion: private package name claimed on public registry
- Packages with no license or copyleft license (GPL, AGPL) in a permissive-licensed project
- Deprecated or unmaintained packages with no security patches

### What Supply Chain Risk is NOT

Do not flag these:

- **Dev-only dependencies** with vulnerabilities that never reach production builds (verify they are truly dev-only)
- **Transitive dependency CVEs** where the vulnerable code path is not reachable from the project
- **Fork references** that point to patched forks of vulnerable packages
- **Version constraint ranges** that resolve to patched versions in the lock file
- **Test fixtures** containing intentionally vulnerable packages for testing

---

## Execution

### Single-Phase Comprehensive Audit

Launch a subagent with the following instructions:

> **Goal**: Perform a full supply chain security audit of all project dependencies. Produce a comprehensive report covering CVEs, typosquatting risks, dependency confusion vectors, build script risks, and license issues.
>
> **Context**: You will be given the project's architecture summary. Use it to identify which ecosystems are in use and where manifest/lock files live.
>
> **Step 1: Discover Manifest and Lock Files**
>
> Search for all dependency files in the project:
>
> | Ecosystem  | Manifest Files                                            | Lock Files                                            |
> |------------|-----------------------------------------------------------|-------------------------------------------------------|
> | npm        | `package.json`                                            | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`   |
> | pip        | `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `setup.cfg` | `Pipfile.lock`, `poetry.lock`          |
> | cargo      | `Cargo.toml`                                              | `Cargo.lock`                                          |
> | go         | `go.mod`                                                  | `go.sum`                                              |
> | maven      | `pom.xml`, `build.gradle`, `build.gradle.kts`             | `gradle.lockfile`                                     |
> | composer   | `composer.json`                                           | `composer.lock`                                       |
> | gems       | `Gemfile`                                                 | `Gemfile.lock`                                        |
> | nuget      | `*.csproj`, `packages.config`                             | `packages.lock.json`                                  |
>
> Flag any manifest file that lacks a corresponding lock file — this is a supply chain risk (non-deterministic builds).
>
> **Step 2: Known Vulnerability Check**
>
> For each dependency, check version against known vulnerable patterns:
>
> **npm (critical patterns)**:
> - `lodash` < 4.17.21 — prototype pollution
> - `minimist` < 1.2.6 — prototype pollution
> - `json5` < 2.2.2 — prototype pollution
> - `node-fetch` < 2.6.7 — SSRF via redirect
> - `express` < 4.19.2 — open redirect
> - `jsonwebtoken` < 9.0.0 — algorithm confusion
> - `axios` < 1.6.0 — SSRF
> - `shell-quote` < 1.7.3 — command injection
> - `semver` < 7.5.2 — ReDoS
>
> **pip (critical patterns)**:
> - `pyyaml` < 6.0 — arbitrary code execution via `yaml.load()`
> - `requests` < 2.31.0 — various
> - `urllib3` < 2.0.6 — header injection
> - `cryptography` < 41.0.0 — multiple CVEs
> - `django` — version-specific CVEs (check against known ranges)
> - `flask` with `debug=True` in production
> - `pillow` < 10.0.0 — buffer overflow
>
> **cargo (critical patterns)**:
> - Cross-reference with RustSec advisory patterns
> - `hyper` < 0.14.10 — request smuggling
> - `regex` < 1.5.5 — ReDoS
>
> **go (critical patterns)**:
> - `golang.org/x/crypto` — check for known vulnerable versions
> - `golang.org/x/net` — check for HTTP/2 vulnerabilities
> - `replace` directives pointing to local paths or non-standard URLs
>
> **maven (critical patterns)**:
> - `log4j-core` < 2.17.1 — Log4Shell (CVE-2021-44228)
> - `jackson-databind` — polymorphic typing RCE
> - `spring-framework` < 5.3.18 — Spring4Shell
> - `commons-collections` — deserialization gadgets
> - `fastjson` < 1.2.83 — deserialization RCE
>
> **nuget (critical patterns)**:
> - `Newtonsoft.Json` with `TypeNameHandling` — deserialization RCE
> - `System.Text.Json` < 6.0.0 — various
>
> **Step 3: Typosquatting Check**
>
> For each dependency name, check for typosquatting indicators:
> - Name differs by 1-2 characters from a popular package
> - Hyphen/underscore confusion: `node-fetch` vs `node_fetch`
> - Scope confusion: `@types/react` vs `types-react`
> - Common character swaps: `l` → `1`, `o` → `0`, doubled letters
>
> **Step 4: Dependency Confusion Check**
>
> - Check `.npmrc`, `pip.conf`, `.pypirc`, `settings.xml` for registry configuration
> - Flag unscoped npm packages that might exist on public registry
> - Flag mixed registry sources without priority rules
> - Check if internal package names could be claimed on public registries
>
> **Step 5: Build Script Analysis**
>
> - npm: Check `postinstall`, `preinstall`, `prepare` scripts in dependencies
> - pip: Check `setup.py` for `os.system()`, `subprocess`, or network calls
> - cargo: Check for `build.rs` in dependencies
> - maven/gradle: Check for custom exec tasks in build plugins
>
> **Step 6: License Compliance**
>
> - Flag copyleft (GPL, AGPL, LGPL) dependencies in permissive-licensed (MIT, Apache, BSD) projects
> - Flag dependencies with no license specified
> - Flag license incompatibilities
>
> **Step 7: Staleness Check**
>
> - Flag dependencies not updated in 2+ years with no active maintenance
> - Flag deprecated packages with available replacements
> - Flag packages with known end-of-life dates
>
> **Classification**:
> - **Vulnerable**: Dependency with known CVE in the exact version used, AND the vulnerable code path is reachable.
> - **Likely Vulnerable**: Known CVE in version used, but reachability not confirmed.
> - **Risk**: Typosquatting, dependency confusion, suspicious build scripts, or license issues.
> - **Informational**: Outdated packages without known CVEs, minor license concerns.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Dependency Audit: [Project Name]
>
> ## Summary
> - Ecosystems scanned: [list]
> - Total dependencies: [N] (direct: [D], transitive: [T])
> - Critical: [N], High: [N], Medium: [N], Low: [N]
>
> ## Findings
>
> ### [VULNERABLE] Package@version — CVE description
> - **Ecosystem**: [npm / pip / cargo / go / maven / composer / gems / nuget]
> - **Manifest**: `path/to/package.json`
> - **Type**: [direct / transitive]
> - **CVE**: [CVE-XXXX-XXXXX]
> - **Issue**: [What the vulnerability allows]
> - **Remediation**: Upgrade to version X.Y.Z
>
> ### [RISK] Typosquatting / Dependency Confusion / Build Script / License
> - [Similar format with appropriate fields]
>
> ### [INFORMATIONAL] Outdated / Deprecated
> - [Similar format]
> ```
>
> **Severity mapping** (for use in reporting):
> - Known RCE CVE in actively used dependency → CRITICAL
> - Known data breach/privilege escalation CVE → HIGH
> - Typosquatting risk, dependency confusion, or conditionally exploitable CVE → MEDIUM
> - Outdated without CVE, license issue, or informational → LOW

### Merge & Report

After the audit subagent completes:

1. Collect the audit response.
2. Extract **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings, plus any **[RISK]** findings with MEDIUM or higher severity.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the exact package, version, CVE, and upgrade command
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [INFORMATIONAL] entries to `BUG-REPORT.md`.

---

## Important Reminders

- This is a **single-phase audit**, not the standard 3-phase recon/verify model. No batching is needed.
- Focus on **resolved versions** in lock files, not version constraints in manifests. A constraint of `^1.0.0` might resolve to a patched `1.2.3`.
- If no lock file exists, flag this as a separate finding — non-deterministic builds are a supply chain risk.
- Dev dependencies matter less than production dependencies, but still flag CRITICAL CVEs in dev deps (e.g., build tool RCE).
- Transitive dependency CVEs should be flagged only if the vulnerable code path is reachable from the project's direct usage.
- Typosquatting detection should compare against the top 1000 packages in each ecosystem. A package differing by 1 character from a popular package is suspicious.
- Dependency confusion is most relevant for organizations using private registries alongside public ones. Check `.npmrc`, `pip.conf`, and Maven `settings.xml` for mixed registry configuration.
- Build scripts (`postinstall`, `setup.py`) are the most dangerous supply chain vector — they execute arbitrary code during installation.
- When in doubt about whether a CVE is reachable, classify as "Likely Vulnerable" rather than skip it. False negatives are worse than false positives in security assessment.
