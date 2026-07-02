---
name: docker
description: >-
  Detect container security vulnerabilities using a three-phase approach:
  find Dockerfile and docker-compose files, verify misconfigurations
  (root user, secrets in layers, privileged mode, unsafe mounts),
  then merge confirmed findings. Use when asked to audit Docker/container security.
---

# Container Security Scan

You are performing a focused security assessment to find Docker and container security vulnerabilities in a codebase. This skill uses a three-phase approach with subagents: **discovery** (find all container configuration files) then **verify** (confirm whether configurations expose secrets, run as root, or grant excessive privileges) then **merge** (write confirmed findings).

---

## What is Container Insecurity

Containers provide process isolation, but misconfigured containers can expose secrets in image layers, run with host-level privileges, or mount sensitive host paths. The core pattern: *a container configuration weakens the isolation boundary or embeds sensitive data into a persistent, inspectable artifact.*

### What Container Insecurity IS

- Running containers as root without a `USER` directive in the final stage
- Secrets embedded in `ENV`, `ARG`, or `COPY`-ed `.env` files — persisted in image layers
- Using `ADD` instead of `COPY` (auto-extracts archives, fetches URLs)
- Missing `.dockerignore` allowing `.env`, `.git/`, private keys into build context
- `privileged: true` in docker-compose — full host kernel access
- Host filesystem mounts (`/:/host`, `/var/run/docker.sock`)
- Unverified base images without digest pinning (`FROM someuser/image:latest`)
- `host` network mode or PID namespace sharing

### What Container Insecurity is NOT

Do not flag these as container vulnerabilities:

- **Build-stage root**: Multi-stage builds running as root in build stage but non-root in final stage
- **CI/CD build containers**: Elevated privileges in ephemeral CI containers for build tasks
- **Development compose overrides**: `docker-compose.override.yml` with relaxed security for local dev
- **Official base images at version tags**: `FROM node:18-alpine` is acceptable (digest pinning is better but not required)
- **tmpfs mounts**: Temporary filesystem mounts do not expose host data

### Patterns That Prevent Container Exploits

When you see these patterns, the code is likely **not vulnerable**:

**1. Non-root user in final stage**
```dockerfile
FROM node:18-alpine AS build
RUN npm ci && npm run build

FROM node:18-alpine
RUN addgroup -S app && adduser -S app -G app
USER app
COPY --from=build /app/dist ./dist
```

**2. BuildKit secrets mount**
```dockerfile
RUN --mount=type=secret,id=db_password cat /run/secrets/db_password
```

**3. Hardened compose configuration**
```yaml
services:
  app:
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

---

## Vulnerable vs. Secure Examples

### Dockerfile — Running as Root

```dockerfile
# VULNERABLE: No USER directive — runs as root
FROM node:18
COPY . /app
RUN npm install
CMD ["node", "server.js"]

# SECURE: Non-root user
FROM node:18-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --chown=app:app . .
RUN npm ci --production
USER app
CMD ["node", "server.js"]
```

### Dockerfile — Secrets in Layers

```dockerfile
# VULNERABLE: Secret persists in image layer — visible via docker history
ENV DATABASE_PASSWORD=mysecretpassword
ARG API_KEY=sk_live_abc123
COPY .env /app/.env

# SECURE: Use BuildKit secrets or runtime env
RUN --mount=type=secret,id=db_password \
    cat /run/secrets/db_password > /tmp/pw && \
    setup-db.sh && rm /tmp/pw
```

### Dockerfile — ADD vs COPY

```dockerfile
# VULNERABLE: ADD auto-extracts and can fetch remote URLs
ADD https://example.com/app.tar.gz /app/
ADD . /app/

# SECURE: COPY is explicit — no extraction, no remote fetch
COPY . /app/
```

### Dockerfile — Unverified Base Image

```dockerfile
# VULNERABLE: Unverified third-party image, mutable tag
FROM someuser/myimage:latest

# SECURE: Official image with digest pin
FROM node:18-alpine@sha256:abc123def456...
```

### Docker Compose — Privileged Mode and Host Mounts

```yaml
# VULNERABLE: Full host access
services:
  app:
    privileged: true
    network_mode: host
    pid: host
    volumes:
      - /:/host
      - /var/run/docker.sock:/var/run/docker.sock
    cap_add:
      - ALL

# SECURE: Minimal privileges
services:
  app:
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp
```

### Missing .dockerignore

```
# Without .dockerignore, build context includes:
# .env, .git/, node_modules/, *.pem, *.key, .ssh/

# SECURE .dockerignore:
.env
.env.*
.git
.gitignore
node_modules
*.pem
*.key
.ssh
docker-compose*.yml
```

---

## Execution

### Phase 1: Find Container Configuration Files

Launch a subagent with the following instructions:

> **Goal**: Find every Docker-related configuration file in the codebase — Dockerfiles, docker-compose files, .dockerignore files, and container orchestration configs. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the deployment model and container usage.
>
> **What to search for — container configuration patterns**:
>
> 1. **Dockerfiles**:
>    - `Dockerfile`, `Dockerfile.*`, `*.dockerfile`
>    - Multi-stage build patterns, base image references
>    - `USER` directive presence/absence
>    - `ENV`, `ARG`, `COPY`, `ADD` commands with potential secrets
>
> 2. **Docker Compose files**:
>    - `docker-compose.yml`, `docker-compose.*.yml`, `compose.yml`, `compose.*.yml`
>    - `privileged`, `network_mode`, `pid`, `cap_add`, `cap_drop`, `security_opt`
>    - Volume mounts (especially host path mounts)
>    - `env_file` references
>
> 3. **.dockerignore files**:
>    - Presence/absence of `.dockerignore`
>    - Whether it excludes `.env`, `.git/`, private keys, credentials
>
> 4. **For each file found, extract**:
>    - Base images and whether pinned (tag, digest, or unpinned)
>    - USER directive presence and placement
>    - Secret-like values in ENV/ARG/COPY
>    - Privileged settings and volume mounts
>    - Security-related directives (cap_drop, read_only, no-new-privileges)
>
> **What to skip**:
> - Test fixtures or example Dockerfiles in documentation
> - Kubernetes manifests (separate concern)
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Container Recon: [Project Name]
>
> ## Summary
> Found [N] container configuration files.
>
> ## Configuration Files
>
> ### 1. [Descriptive name — e.g., "Production Dockerfile"]
> - **File**: `path/to/Dockerfile`
> - **Type**: [Dockerfile / docker-compose / .dockerignore]
> - **Base image**: [image:tag or image@digest]
> - **USER directive**: [present (user) / absent (runs as root)]
> - **Secret exposure risk**: [ENV/ARG with secrets / .env COPY / none detected]
> - **Privilege settings**: [privileged / host network / host mounts / minimal]
> - **Code snippet** (relevant sections):
>   ```dockerfile
>   [security-relevant lines]
>   ```
>
> [Repeat for each file]
> ```

### Phase 2: Batched Verify — Confirm Container Misconfigurations

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand which containers run in production vs. development.
>
> **For each container configuration, verify whether it creates an exploitable vulnerability**:
>
> 1. **Running as root**: Does the final stage lack a `USER` directive?
>    - Check ALL stages in multi-stage builds — only the final stage matters
>    - If production Dockerfile runs as root → VULNERABLE
>    - If build-only stage runs as root but final stage is non-root → NOT VULNERABLE
>
> 2. **Secrets in layers**: Are secrets embedded in the image?
>    - Check `ENV` and `ARG` for passwords, API keys, tokens
>    - Check `COPY` for `.env`, credential files, private keys
>    - Even deleted secrets persist in prior layers (`docker history` exposes them)
>    - If secrets in ENV/ARG/COPY → VULNERABLE
>
> 3. **ADD misuse**: Is `ADD` used where `COPY` would suffice?
>    - `ADD` with remote URLs → fetches unverified content
>    - `ADD` with archives → auto-extracts (unexpected behavior)
>    - If `ADD` with URL or used instead of `COPY` for local files → LIKELY VULNERABLE
>
> 4. **Missing .dockerignore**: Is `.dockerignore` absent or incomplete?
>    - Check if `.env`, `.git/`, `*.pem`, `*.key` would be included in build context
>    - If sensitive files not excluded → LIKELY VULNERABLE
>
> 5. **Privileged mode and host access**: Does compose grant excessive privileges?
>    - `privileged: true` → full host kernel access → VULNERABLE
>    - `/var/run/docker.sock` mount → container escape → VULNERABLE
>    - `network_mode: host` or `pid: host` → reduced isolation → LIKELY VULNERABLE
>    - Host root mount (`/:/host`) → full host filesystem access → VULNERABLE
>
> 6. **Unverified base images**: Are base images trustworthy?
>    - Third-party images without digest pinning → supply chain risk
>    - `latest` tag → non-reproducible builds
>    - Official images with version tags → acceptable
>
> **Classification**:
> - **Vulnerable**: Confirmed container misconfiguration with direct security impact (secrets in layers, privileged mode, host root mount).
> - **Likely Vulnerable**: Significant risk but context-dependent (running as root, missing .dockerignore, host network).
> - **Not Vulnerable**: Properly configured with non-root user, no secrets, minimal privileges.
> - **Needs Manual Review**: Complex multi-stage builds or orchestration-level security.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Container Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/Dockerfile` (lines X-Y)
> - **Issue**: [e.g., "Database password embedded in ENV directive — persists in image layer"]
> - **Misconfiguration type**: [secrets in layers / running as root / privileged mode / host mount / missing .dockerignore]
> - **Impact**: Secret exposure via docker history, container escape, host compromise
> - **Remediation**: Use BuildKit secrets mount, add USER directive, remove privileged mode, add .dockerignore
> - **Verification command**: [e.g., "`docker history --no-trunc image:tag` to see secrets in layers"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Secrets in image layers (ENV/ARG/COPY credentials) → CRITICAL
> - Privileged mode or Docker socket mount in production → CRITICAL
> - Host root filesystem mount → CRITICAL
> - Running as root in production container → HIGH
> - Missing .dockerignore exposing credentials → HIGH
> - Host network/PID namespace → MEDIUM
> - ADD instead of COPY, unverified base images, latest tag → MEDIUM
> - Missing resource limits, non-optimal layer ordering → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full misconfiguration details and a verification command
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all container configuration files regardless of whether they are secure. Do not evaluate safety in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each configuration file, determine whether it creates an exploitable misconfiguration.
- Secrets in image layers are the most critical Docker vulnerability — `docker history --no-trunc` reveals every ENV, ARG, and COPY command ever executed, even in "deleted" layers.
- Multi-stage builds are common. Only the final stage matters for runtime security. A build stage running as root to compile code is standard practice.
- `privileged: true` disables ALL security features (AppArmor, seccomp, capabilities) and gives full access to host devices. It is almost never needed in production.
- Docker socket mount (`/var/run/docker.sock`) allows container escape — a process inside the container can create new privileged containers on the host.
- `.dockerignore` is often forgotten. Without it, the entire build context (including `.env`, `.git/`, private keys) is sent to the Docker daemon and potentially embedded in the image.
- Development docker-compose overrides with relaxed security are expected. Only flag production-targeted configurations.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
