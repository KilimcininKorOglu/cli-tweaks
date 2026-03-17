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

## Output Format

For each finding produce:

1. **File:line** — exact location in codebase
2. **Financial risk scenario** — how money could be lost or stolen
3. **Estimated potential loss** — approximate financial impact
4. **Fix** — concrete recommendation with code
