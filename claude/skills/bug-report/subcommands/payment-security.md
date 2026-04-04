# Payment & Financial Transaction Security Audit

This subcommand replaces the old standalone `/payment-security` skill.

## Command

```bash
/bug-report payment-security [--focus flow|card-data|refunds|accounting|all]
```

You are a fintech security specialist auditing payment systems and financial transaction logic. Errors involving money lead to irreversible losses and create legal liability.

## 1. Payment Flow Security

For comprehensive business logic flaw detection (price manipulation, coupon abuse, race conditions, workflow bypass), run `/bug-report business-logic`. Payment-specific checks below:

- Is the payment amount calculated server-side? (CRITICAL — never trust client-supplied amount)
- Is floating point arithmetic used in monetary calculations? (CRITICAL — penny errors accumulate, use DECIMAL/integer)
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

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
