---
name: iac
description: >-
  Detect Infrastructure-as-Code misconfigurations in Terraform, Kubernetes,
  Helm, and cloud provider templates. Covers public storage, permissive IAM,
  unencrypted resources, open security groups, and privileged workloads.
  Use when asked to audit infrastructure definitions.
---

# Infrastructure-as-Code Security Detection

You are performing a focused security assessment of Infrastructure-as-Code definitions. This skill uses a three-phase approach: **recon** (inventory IaC files and the resources they declare), **batched verify** (judge each resource against its exposure and data sensitivity), and **merge** (write confirmed findings to `BUG-REPORT.md`).

Container images and CI pipeline definitions belong to other subcommands. `docker` owns `Dockerfile` and `docker-compose`. `ci-cd` owns GitHub Actions, GitLab CI, and Jenkins. This subcommand owns the declarative infrastructure layer between them.

---

## What is an IaC Misconfiguration

An IaC misconfiguration is a declared resource whose security properties are weaker than the data or workload it carries. The declaration is the vulnerability: the cloud provider applies it exactly as written, so the flaw ships on every apply.

The core pattern: *a template grants broader access, weaker isolation, or weaker encryption than the workload requires.*

### What an IaC Misconfiguration IS

- A storage bucket or blob container with public read or public write access
- An IAM policy with `Action: "*"` and `Resource: "*"`
- A security group or firewall rule with `0.0.0.0/0` ingress on a non-public port
- A database instance with `publicly_accessible = true`
- A resource with encryption at rest or in transit disabled
- A Kubernetes workload with `privileged: true`, `hostPID`, `hostNetwork`, or a `hostPath` volume
- A hardcoded credential, token, or private key in a `.tf`, `.tfvars`, or manifest file
- A Kubernetes ServiceAccount bound to `cluster-admin`

### What an IaC Misconfiguration is NOT

Do not flag these:
- **A public bucket that serves public assets**: a static website origin or a public CDN bucket is public by design
- **A wildcard action scoped to one resource ARN**: breadth alone is not the finding, reachable authority is
- **A local development manifest**: a `kind`, `minikube`, or `docker-desktop` overlay that never reaches a shared cluster
- **A variable placeholder**: `password = var.db_password` reads a value, it does not hardcode one
- **A disabled resource**: `count = 0` or a commented block declares nothing
- **A module default overridden at the call site**: read the caller before judging the module

### Patterns That Prevent IaC Misconfigurations

```hcl
# Terraform — block public access at the account and bucket level
resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Terraform — scope the policy to one action set and one resource
data "aws_iam_policy_document" "reader" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.data.arn}/*"]
  }
}
```

```yaml
# Kubernetes — drop privileges and lock the root filesystem
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

---

## Vulnerable vs. Secure Examples

### Terraform — storage exposure

```hcl
# VULNERABLE: public ACL on a data bucket
resource "aws_s3_bucket" "data" {
  bucket = "customer-exports"
  acl    = "public-read"
}

# SECURE: private bucket plus a public access block
resource "aws_s3_bucket" "data" {
  bucket = "customer-exports"
}
resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  restrict_public_buckets = true
}
```

### Terraform — network exposure

```hcl
# VULNERABLE: database port open to the internet
resource "aws_security_group_rule" "db" {
  type        = "ingress"
  from_port   = 5432
  to_port     = 5432
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

# SECURE: reachable only from the application security group
resource "aws_security_group_rule" "db" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.app.id
}
```

### Kubernetes — host escape

```yaml
# VULNERABLE: privileged container mounting the host root
spec:
  containers:
    - name: agent
      securityContext:
        privileged: true
      volumeMounts:
        - name: host-root
          mountPath: /host
  volumes:
    - name: host-root
      hostPath:
        path: /

# SECURE: unprivileged container, no host mount
spec:
  containers:
    - name: agent
      securityContext:
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
```

### Kubernetes — RBAC breadth

```yaml
# VULNERABLE: workload ServiceAccount bound to cluster-admin
roleRef:
  kind: ClusterRole
  name: cluster-admin

# SECURE: namespaced Role with the verbs the workload uses
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
```

---

## Execution

### Phase 1: Inventory IaC Files and Declared Resources

Launch a subagent with the following instructions:

> **Goal**: Find every Infrastructure-as-Code file and list the security-relevant resources it declares. Return findings in your response.
>
> **What to search for**:
>
> 1. **Terraform**: `*.tf`, `*.tfvars`, `*.tf.json`, and any `modules/` directory
> 2. **Kubernetes**: manifests under `k8s/`, `kubernetes/`, `deploy/`, `manifests/`, plus `helm/` charts and their `values*.yaml`
> 3. **Cloud templates**: CloudFormation (`*.template.yaml`, `AWSTemplateFormatVersion`), ARM/Bicep, Pulumi programs, CDK stacks
> 4. **Service definitions**: `serverless.yml`, `fly.toml`, `app.yaml`, Cloud Run and ECS task definitions
>
> **For each file, record the declared resources in these classes**: storage, database, compute, network rule, IAM or RBAC binding, secret, and workload security context.
>
> **What to skip**: `Dockerfile` and `docker-compose*` (the `docker` subcommand owns them), CI workflow files (the `ci-cd` subcommand owns them), `.terraform/` provider caches, `*.tfstate` (report it separately if it is committed), and vendored chart dependencies.
>
> **Output format** — return in your response:
>
> ```markdown
> # IaC Recon: [Project Name]
>
> ## Summary
> Found [N] IaC files declaring [M] security-relevant resources.
> Stacks present: [Terraform / Kubernetes / Helm / CloudFormation / ...]
>
> ## Declared Resources
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.tf` (lines X-Y)
> - **Stack**: [Terraform / Kubernetes / ...]
> - **Resource type**: [aws_s3_bucket / Deployment / ClusterRoleBinding / ...]
> - **Environment**: [production / staging / local / unknown — from path, workspace, or variable]
> - **Security-relevant attributes**: [acl, encryption, cidr_blocks, securityContext, roleRef, ...]
> - **Code snippet**:
>   ```
>   [the declaration]
>   ```
> ```

### Phase 2: Batched Verify — Judge Exposure Against Purpose

After Phase 1 completes, count numbered resources. If 3 or fewer, use a single subagent. Otherwise split the resources into batches of up to 3 and run them through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.

> **For each resource, decide whether the declared exposure exceeds its purpose**:
>
> 1. **Reachability**: is the resource reachable from the internet, from another tenant, or only from inside a private network?
> 2. **Data sensitivity**: what does the resource hold or grant? Read the application code that uses it when the name is not decisive.
> 3. **Compensating declaration**: does a second resource restrict the first? A public access block, a bucket policy, a network policy, a `PodSecurityPolicy` replacement, or an admission controller counts.
> 4. **Environment**: does the file apply to production? A local overlay or a `dev` workspace changes severity, not correctness.
> 5. **Override**: is the value overridden by a variable, a `values.yaml`, a kustomize patch, or a call-site argument?
>
> **Classification**:
> - **Vulnerable**: production-reachable resource with confirmed excess exposure and no compensating declaration
> - **Likely Vulnerable**: excess exposure with an unresolved environment or override question
> - **Not Vulnerable**: exposure matches purpose, or a compensating declaration restricts it
> - **Needs Manual Review**: the decisive fact lives outside the repository, such as a cloud console setting or a cluster admission policy
>
> **Output format** — return in your response:
>
> ```markdown
> # IaC Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.tf` (lines X-Y)
> - **Resource**: [type and name]
> - **Issue**: [what the declaration grants]
> - **Exposure path**: [who reaches it, and how]
> - **Compensating controls checked**: [what was searched for and not found]
> - **Impact**: [data exposure, lateral movement, host escape, ...]
> - **Remediation**: [the corrected declaration]
> ```

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries.

**Severity mapping**:
- Hardcoded credential in a tracked IaC file, or a privileged workload with a host mount → CRITICAL
- Public storage holding user data, public database instance, or a wildcard IAM policy on a production account → HIGH
- Missing encryption at rest, missing network policy, or an over-broad namespaced Role → MEDIUM
- Missing resource limits, unpinned module version, or a finding limited to a non-production workspace → LOW

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1. Phase 3 runs AFTER all batches.
- Batch size: 3 resources per subagent. If 1-3 total, single subagent. Run the batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Read the module caller before judging a module default. A safe default overridden to `public-read` at the call site is a finding against the caller, not the module.
- A committed `*.tfstate` file is a finding on its own, because state holds resolved secret values.
- Never run `terraform apply`, `terraform plan`, `kubectl apply`, or `helm install` during this audit. Read the declarations only.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
