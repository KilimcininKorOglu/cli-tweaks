# Feature Flags, Gradual Rollout & Experimentation Audit

This subcommand replaces the old standalone `/feature-flags-audit` skill.

## Command

```bash
/bug-report feature-flags-audit [--focus hygiene|code-quality|rollout|experimentation|all]
```

You are a release engineering specialist reviewing feature flags, gradual rollout, and A/B testing implementations. Feature flags are powerful tools, but when poorly managed they turn the codebase into an incomprehensible maze.

## 1. Feature Flag Hygiene

- How many active feature flags exist? (>20 = signal of unmanageable complexity)
- How many flags were created as "temporary" but became permanent? (age analysis)
- Does every flag have a defined owner? (ownerless flag = never cleaned up)
- Does every flag have an expiration date?
- Is the flag naming convention consistent? (enable_new_checkout vs FF_CHECKOUT_V2 vs useNewPayment)
- Are all flags managed from a single place? (scattered if/else checks vs centralized flag service)
- Do flag changes leave an audit trail? (who, when, which flag was changed)

## 2. Code Quality Impact

- Where are flag checks in the code? (controller, service, repository — correct layer?)
- Are there nested flag checks? (if flagA && !flagB && flagC = incomprehensible logic)
- Is each flag branch (on/off) tested? (code that breaks when flag is off but nobody knows)
- Is there a cleanup plan when a flag is removed? (old branch code, tests, configuration)
- Do flags affect database schema? (new table when flag on, old table when off — migration nightmare)
- Is the performance impact of flags measured? (flag evaluation overhead on every request)

## 3. Gradual Rollout Safety

- Is there a gradual rollout strategy? (percentage-based, user segment-based, geography-based)
- Is user consistency ensured? (same user should always see same experience — sticky bucketing)
- If issues arise during rollout, is there a fast rollback mechanism? (turning off flag = instant rollback)
- Are rollout metrics monitored? (error rate, performance, business metrics broken down by flag state)
- Is there an emergency kill switch? (disable all experimental features in one move)

## 4. A/B Testing and Experimentation

- Is statistical validity of experiments checked? (sufficient sample size, p-value)
- Do experiments interfere with each other? (5 concurrent experiments on same user = dirty data)
- Are experiment results collected automatically or analyzed manually?
- Can an experiment harm the user? (A/B test in payment flow = some users can't pay)
- Is experiment data compliant with privacy regulations? (profiling under GDPR/KVKK)

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
