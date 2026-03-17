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

## Output Format

For each scenario produce:

1. **Readiness status** — red / yellow / green
2. **Gaps** — what's missing or insufficient
3. **Remediation plan** — concrete steps to close the gap
