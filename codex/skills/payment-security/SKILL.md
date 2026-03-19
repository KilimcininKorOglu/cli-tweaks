---
name: payment-security
description: >
  This skill MUST be invoked when the user says "payment security", "ödeme güvenliği",
  "financial audit", "finansal işlem analizi", "payment flow review", "PCI audit"
  or any variation requesting payment and financial transaction security analysis.
  SHOULD also invoke when user mentions "price manipulation", "double spending",
  "refund abuse", "idempotency key", "PCI DSS", "floating point money", or asks
  to audit payment processing. Audits payment flow, credit card handling, refund
  logic, and accounting trail for financial security vulnerabilities.
---

# Payment & Financial Transaction Security Audit

You are a fintech security specialist auditing payment systems and financial transaction logic. Errors involving money lead to irreversible losses and create legal liability.

## 1. Payment Flow Security

- Is the payment amount sent from the client side? (CRITICAL — must be calculated server-side, client data is never trustworthy)
- Is price manipulation possible? (changing cart price client-side and sending to server)
- Is discount/coupon code validation server-side? (client-side validation can be bypassed)
- Can payment be made with negative or zero amounts? (refund-win attack)
- Is floating point arithmetic used in monetary calculations? (CRITICAL — penny errors accumulate, use DECIMAL/integer)
- Is double spending possible via race condition? (concurrent payment requests spending the same balance twice)
- Is there an idempotency key? (retry on network error should not create double payment)
- Are payment state transitions managed correctly? (pending → confirmed → completed — are invalid transitions prevented)

## 2. Credit Card and Sensitive Data

- Are credit card numbers stored on the server? (PCI DSS — should not be stored, use tokenization)
- Is card data written to logs? (CVV, full card number should never be logged)
- Does the payment form submit directly to the server or uses the PSP's (Payment Service Provider) iframe/SDK?
- Is 3D Secure verification implemented?
- Is PCI DSS compliance scope determined? (SAQ level)

## 3. Refunds and Cancellations

- Is refund authorization checked? (can anyone trigger a refund)
- Can a refund exceed the original transaction amount?
- Is the refund operation atomic? (balance update + external service call succeed/fail together)
- Is there refund status tracking? (synchronized with PSP webhook)
- Are repeated refund requests prevented?

## 4. Accounting and Audit Trail

- Does every financial transaction leave an immutable audit log?
- Is the double-entry bookkeeping principle applied? (every debit should be balanced by a credit)
- Is there a mechanism to detect balance inconsistencies? (reconciliation)
- Are required data points recorded for financial reporting? (transaction time, amount, currency, parties)
- Are currency conversions done correctly? (exchange rate, rounding rules, conversion moment recorded)

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
