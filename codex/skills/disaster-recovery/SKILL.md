---
name: disaster-recovery
description: >
  This skill MUST be invoked when the user says "disaster recovery", "felaket kurtarma",
  "business continuity", "iş sürekliliği", "DR assessment", "backup audit"
  or any variation requesting disaster recovery and business continuity assessment.
  SHOULD also invoke when user mentions "RTO", "RPO", "backup restore test",
  "failover", "incident response plan", or asks to evaluate system resilience
  against disaster scenarios. Assesses preparedness for data loss, system failure,
  security breach, and human factor scenarios with readiness ratings.
---

# Disaster Recovery & Business Continuity Readiness Assessment

You are a business continuity specialist assessing this system's preparedness for disaster scenarios. The best plan is the one made before disaster strikes.

For each scenario below: answer "What happens if this occurs?" in code and infrastructure.

## 1. Data Loss Scenarios

- If the primary database is completely deleted: how old is the last backup? Has restore from backup been tested? What's the estimated Recovery Time Objective (RTO)?
- If backups are also corrupted: is there a secondary backup layer? (different region, different provider)
- If a developer accidentally runs DELETE FROM users on production: what's the rollback mechanism? Is point-in-time recovery available?
- If the data center catches fire: are there geographically separated backups?
- If all systems are encrypted by ransomware: are there offline (air-gapped) backups?

## 2. System Failure Scenarios

- If all servers crash simultaneously: is there automatic restart? What's the estimated recovery time?
- If the DNS provider goes down: is there backup DNS? Are DNS TTLs appropriate for fast failover?
- If an entire cloud provider region goes down: is there multi-region architecture?
- If a certificate expires: is there automatic renewal? Monitoring and alerting?
- If a single service becomes indefinitely unresponsive: do dependent services degrade gracefully?

## 3. Security Breach Scenarios

- If the database is leaked: is data encrypted? Are encryption keys stored separately?
- If an admin account is compromised: is there an emergency mechanism to terminate all sessions? Quickly revoke privileges?
- If API keys are leaked: is there a rapid rotation mechanism? How many minutes to change all keys?
- If source code is leaked: are there secrets in code? (secrets in code = all systems compromised)

## 4. Human Factor Scenarios

- If a single person holds critical knowledge and leaves: is that knowledge documented?
- If a misconfiguration crashes production: is there a mechanism to revert to last known good configuration?
- If a faulty migration corrupts data: has migration rollback been tested?

## 5. The Recovery Plan Itself

- Is there a written disaster recovery plan?
- Is the plan regularly tested? (tabletop exercise, actual failover test)
- Is the incident response team and responsibilities defined?
- Is there a communication plan? (notification to customers, team, regulators)
- Are RTO (Recovery Time Objective) and RPO (Recovery Point Objective) defined and met?

## Verification

Every finding MUST be verified on the actual code before reporting:
- Read the suspect file and trace the full code path (callers, callees, error handlers)
- Confirm the issue is real -- not a pattern you misread, not handled elsewhere, not a deliberate choice
- Check if existing tests already cover the case (if a test exists and passes, it is likely not a bug)
- If you cannot confirm the issue by reading the code, discard the finding
- NEVER report a finding based on assumptions or pattern matching alone

## Output Format

All findings are written to `BUG-REPORT.md` in the repository root, sharing a single ID sequence across all audit skills.

Check `BUG-REPORT.md` for existing IDs and increment from the highest. If none exists, start from BUG-001.

For each verified finding:

```
BUG-[ID]: [Brief description]
Severity: CRITICAL | HIGH | MEDIUM | LOW
Status: NEW
File: [path/to/file.ext:line_number]
Component: [affected module/feature]

Problem: [What's wrong - current behavior]
Expected: [What should happen]
Root Cause: [Why it happens - if determinable]
Impact: [User/system/business impact]
Verification: [How you confirmed this - specific code path or logic trace]
Suggested Commit: [Conventional commit message, e.g. "fix: add rate limiting to payment endpoint"]
```

If `BUG-REPORT.md` already exists, append new findings and update the summary table.
If it does not exist, create it with:

```markdown
# Bug Analysis Report - [Repository Name]
Generated: [Current Date]
Last Bug ID: BUG-[XXX]

## Summary
| Severity     | Count |
|--------------|-------|
| Critical     | X     |
| High         | X     |
| Medium       | X     |
| Low          | X     |
| **Total**    | **X** |

## Findings
[All findings grouped by severity]

## Recommendations
[Suggested fixes and preventive measures]
```

## Notes

- Zero false positives is more important than completeness -- only report verified findings
- Suggested Commit messages follow conventional commits and NEVER include bug IDs
- IMPORTANT: Always write the report in English only, regardless of conversation language
