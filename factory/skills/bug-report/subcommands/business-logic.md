---
name: business-logic
description: >-
  Detect business logic vulnerabilities in a codebase using a two-phase
  approach: first perform threat modeling by analyzing the application's
  domain and generating specific attack scenarios (price manipulation,
  workflow bypass, limit violations, race conditions, reward abuse, etc.),
  then verify whether those threats are exploitable by checking for missing
  validations and enforcement.
  Use when asked to find business logic, logic flaws, or abuse-of-function bugs.
---

# Business Logic Vulnerability Detection

You are performing a focused security assessment to find business logic vulnerabilities in a codebase. This skill uses a two-phase approach with subagents: **threat modeling** (understand the domain and generate attack scenarios) then **verify** (check whether those attack scenarios are exploitable).

---

## What are Business Logic Vulnerabilities

Business logic vulnerabilities arise when an application's intended workflow, rules, or constraints can be manipulated to produce unintended outcomes — without exploiting technical flaws like injection or memory corruption. The attacker operates within the application's own features but uses them in ways the developers did not anticipate.

The core pattern: *the application accepts input that is syntactically valid and passes authentication/authorization, but violates a business rule that was never enforced in code.*

### What Business Logic Vulnerabilities ARE

- Submitting a negative quantity to a purchase endpoint, receiving a credit instead of a charge
- Applying the same one-time discount coupon multiple times in parallel requests
- Skipping the payment step in a multi-step checkout by replaying a later step's request
- Posting a rating of 9999 to a movie rating endpoint that should cap ratings at 5
- Transferring a negative amount to move money from the recipient to the sender
- Redeeming a referral bonus by referring yourself with a second account
- Re-using a single-use reset token or voucher that was never invalidated
- Purchasing an item that is out of stock due to a race condition between inventory check and reservation
- Accessing a premium subscription feature after downgrading to a free plan
- Winning an auction by retracting a high bid after others have been eliminated

### What Business Logic Vulnerabilities are NOT

Do not flag these as business logic issues:

- **SQL injection, XSS, RCE, XXE, SSRF, SSTI**: These are injection/technical flaws — separate skills cover them
- **Missing authentication**: Endpoint requires no login at all → that's "Unauthenticated Access"
- **IDOR**: Accessing another user's resource by changing an ID → that's a separate access-control class
- **Brute-force / rate limiting**: Generic rate-limit bypass on login → that's not a business logic flaw unless it enables specific business rule circumvention

---

## Business Logic Attack Categories

Use these categories to guide threat modeling. Not all categories apply to every application — identify which ones are relevant based on the architecture summary.

### 1. Price & Payment Manipulation
- Negative prices or zero prices on purchase endpoints
- Arbitrary price override in request body (mass assignment of price field)
- Currency or unit confusion (e.g., cents vs. dollars)
- Floating-point precision abuse in monetary arithmetic
- Applying discounts that reduce total below zero

### 2. Quantity & Numeric Limit Violations
- Negative quantities (ordering −5 items to receive a credit)
- Quantities exceeding per-user or per-order limits
- Integer overflow/underflow in quantity or balance calculations
- Out-of-range values for bounded fields (ratings, scores, percentages)

### 3. Workflow & Multi-Step Process Bypass
- Skipping mandatory steps in a sequential process (payment, email verification, ID check)
- Replaying a completion token from a previous successful flow to bypass steps
- Direct-access to a later-stage endpoint without completing earlier stages
- Submitting a terminal state transition without going through intermediate states (state machine violations)

### 4. Coupon, Discount & Voucher Abuse
- Applying the same coupon multiple times (single-use not enforced)
- Stacking discounts that were not intended to be combined
- Using an expired coupon or voucher
- Generating or guessing valid coupon codes

### 5. Race Conditions & Concurrency Abuse
- Double-spending: sending two concurrent purchase requests to consume a balance once
- Concurrent coupon redemption draining credit beyond allowed amount
- TOCTOU (time-of-check / time-of-use) on inventory: check passes for both requests, both reservations succeed
- Parallel withdrawal/transfer requests exceeding account balance

### 6. Refund & Chargeback Abuse
- Requesting a refund after the digital good has been consumed or downloaded
- Partial refund on an already-partially-refunded order
- Refund without returning physical item (if logic is not enforced server-side)

### 7. Reward, Referral & Loyalty Abuse
- Self-referral using a second account to earn a referral bonus
- Earning signup bonuses multiple times across multiple accounts
- Loyalty point farming through artificial activity
- Sharing or transferring non-transferable rewards

### 8. Subscription & Entitlement Bypass
- Accessing paid/premium features after downgrading or cancelling
- Trial period abuse (repeatedly creating new accounts for trial access)
- Feature flag or plan check performed only at subscription creation, not at feature access time
- Entitlement cached at session start and not re-evaluated after plan change

### 9. Auction & Bidding Logic
- Retracting a winning bid after competing bids have been rejected
- Shill bidding: artificially inflating price with controlled accounts
- Bypass of reserve price enforcement
- Bid manipulation via concurrent requests

### 10. Inventory & Stock Logic
- Purchasing out-of-stock items due to missing stock validation
- Reserving more stock than available via concurrent requests
- Negative inventory resulting from refund-without-restock logic
- Phantom inventory: item appears available but cannot be fulfilled

### 11. Time & Date Logic
- Using time-limited offers after expiration (expiry checked client-side or weakly server-side)
- Backdating transactions or bookings
- Exploiting "grace period" logic to extend benefits indefinitely
- System clock manipulation if server trusts client-supplied timestamps

### 12. Transfer & Balance Logic
- Transferring a negative amount (sender receives money from recipient)
- Self-transfer to exploit bonus or fee logic
- Transferring more than the available balance due to missing server-side check
- Rounding errors exploited across many micro-transactions

---

## Execution

### Phase 1: Threat Modeling — Domain Analysis & Attack Scenario Generation

Launch a subagent with the following instructions:

> **Goal**: Analyze the codebase to understand its business domain and generate a concrete, prioritized list of business logic attack scenarios specific to this application. Return findings in your response.
>
> **Context**: You will be given the project's architecture summary. Use it to understand what the application does, what features it has, and what business rules it is supposed to enforce. Focus entirely on understanding the domain — do not verify vulnerabilities yet.
>
> **Step 1 — Identify the business domain and features**:
>
> - What does this application do? (e-commerce, marketplace, SaaS, social platform, fintech, gaming, booking, etc.)
> - What financial or transactional features exist? (payments, subscriptions, credits, tokens, wallets, invoices, refunds)
> - What quantitative limits or rules exist? (ratings, scores, quantities, usage limits, quotas)
> - What multi-step workflows exist? (checkout, onboarding, KYC, booking, auctions)
> - What promotional or reward features exist? (coupons, referrals, loyalty points, bonuses, vouchers)
> - What role or tier distinctions exist? (free vs. paid, user vs. premium, trial vs. full)
> - What inventory or capacity constraints exist? (stock, seats, slots, bandwidth)
>
> To discover features, search for:
> - Route/endpoint definitions and their names
> - Model/entity names (Order, Payment, Subscription, Coupon, Wallet, Bid, etc.)
> - Business-rule-related field names (price, quantity, balance, rating, score, limit, quota, expiry, status)
> - Validation logic or constraint-related code
>
> **Step 2 — Generate attack scenarios**:
>
> For each relevant business domain area found, generate specific attack scenarios. Each scenario must be:
> - **Specific to this codebase** — name the actual endpoint, model, or feature involved
> - **Actionable** — describe exactly what an attacker would send/do
> - **Grounded** — reference the code or data model that makes this scenario plausible
>
> Use the attack categories below as a checklist. Only include categories that are relevant to this application:
>
> - **Price/payment manipulation**: Can a user send an arbitrary price in the request? Is price trusted from client?
> - **Quantity/value out of range**: Can a user send negative quantities, zero, or values exceeding defined limits?
> - **Workflow bypass**: Can a user skip a mandatory step in a multi-step process?
> - **Coupon/discount abuse**: Can a coupon be used multiple times or after expiration?
> - **Race conditions**: Are there check-then-act patterns on shared resources (inventory, balance, coupon usage)?
> - **Refund abuse**: Can a refund be requested after the product is consumed?
> - **Reward/referral abuse**: Can referral or signup bonuses be farmed?
> - **Entitlement bypass**: Are premium features checked at access time or only at subscription time?
> - **Transfer/balance logic**: Can negative transfers or self-transfers be made?
> - **Time/date logic**: Are time-limited offers enforced server-side?
> - **Inventory logic**: Is stock validated atomically before reservation?
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Business Logic Threat Model: [Project Name]
>
> ## Application Domain
> [2–3 sentence summary of what the application does and its key business features]
>
> ## Business Features Identified
> - [Feature 1]: [brief description, relevant models/endpoints]
> - [Feature 2]: ...
>
> ## Attack Scenarios
>
> ### Scenario 1: [Short title, e.g. "Negative quantity purchase for credit"]
> - **Category**: [e.g. Quantity & Numeric Limit Violations]
> - **Target**: [Endpoint or feature, e.g. `POST /api/orders`]
> - **Description**: [What an attacker would do and what outcome they expect]
> - **Relevant code**: [File and line range where the relevant logic lives]
> - **Business rule that should be enforced**: [What the application is supposed to do]
> - **Risk level**: [High / Medium / Low]
>
> ### Scenario 2: ...
>
> ## Categories Not Applicable
> [List any categories from the checklist that are not relevant to this application and why]
> ```

### Phase 2: Batched Verify — Check Whether Scenarios Are Exploitable

After Phase 1 completes, count the numbered scenario sections (`### Scenario 1`, `### Scenario 2`, ...) from Phase 1 findings.

**If 3 or fewer scenarios**: Launch a single subagent with all scenarios (skip batching).

**If more than 3 scenarios**: Split into batches of up to 3 each. Launch all batch subagents **in parallel**. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned scenarios from Phase 1):

>
> **Context**: You will be given the project's architecture summary and the threat model. Use the architecture summary to understand validation patterns, ORM usage, and where business rules are typically enforced.
>
> **For each scenario, perform the following checks**:
>
> **1. Is the business rule enforced server-side?**
> - Is the constraint validated in the backend handler, service layer, or ORM/database?
> - Or is it only validated client-side (frontend form validation, JavaScript min/max attributes)?
> - Client-side-only validation = exploitable.
>
> **2. Is the validation complete and covers all edge cases?**
> - Does it check for negative values where applicable?
> - Does it check upper bounds, not just lower bounds?
> - Does it handle concurrent requests (is the check atomic, or is there a TOCTOU window)?
> - Does it re-validate at the point of use, not just at an earlier step?
>
> **3. For workflow bypass scenarios**:
> - Does each step verify that previous required steps were completed?
> - Are step completion flags stored server-side (not just in a cookie or session that can be replayed)?
> - Can a terminal endpoint be called directly without going through earlier steps?
>
> **4. For coupon/voucher scenarios**:
> - Is the coupon marked as used atomically with the transaction (in the same DB transaction)?
> - Is concurrent redemption protected (SELECT FOR UPDATE, optimistic locking, atomic compare-and-swap)?
> - Is the expiry date checked server-side at redemption time?
>
> **5. For race condition scenarios**:
> - Is stock/balance check and decrement done atomically (in a single DB transaction or with row-level locking)?
> - Is there any idempotency key or deduplication logic to prevent duplicate concurrent requests?
>
> **Database-level protections to look for:**
> - `SELECT ... FOR UPDATE` (row-level lock) — prevents concurrent reads of same resource
> - Transaction isolation level: `SERIALIZABLE` prevents phantom reads, `READ COMMITTED` doesn't prevent TOCTOU
> - Optimistic locking: version column (`WHERE version = ?` then `SET version = version + 1`) — check if version mismatch is handled
> - Unique constraints: database-level uniqueness prevents duplicate creation
> - `INSERT ... ON CONFLICT DO NOTHING` (PostgreSQL) / `INSERT IGNORE` (MySQL)
>
> **Application-level protections:**
> - Mutex/semaphore around critical sections
> - Idempotency keys on payment/transfer endpoints
> - Redis-based distributed locks (`SETNX` with TTL)
> - Rate limiting per-user on sensitive operations
>
> **Framework-specific patterns:**
> - Django: `select_for_update()`, `F()` expressions for atomic updates
> - Rails: `with_lock`, `lock!`, optimistic locking via `lock_version`
> - Express/Node: No built-in locking — must use Redis or DB locks
> - Spring: `@Transactional(isolation = Isolation.SERIALIZABLE)`, `@Lock(LockModeType.PESSIMISTIC_WRITE)`
>
> **6. For entitlement/subscription scenarios**:
> - Is the user's current plan/tier checked at the point of feature access?
> - Or is it cached at login/session start and never re-evaluated?
>
> **7. For transfer/balance scenarios**:
> - Is there a server-side check that the transfer amount is positive?
> - Is there a server-side check that the sender has sufficient balance?
> - Are these checks done within a database transaction to prevent race conditions?
>
> **Classification**:
> - **Exploitable**: The business rule is absent, bypassable, or only enforced client-side.
> - **Likely Exploitable**: The rule exists but has gaps (race condition window, missing edge case, bypassable condition).
> - **Not Exploitable**: Proper server-side enforcement exists and covers edge cases.
> - **Needs Manual Review**: Cannot determine with confidence (complex logic, external service dependency, etc.).
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Business Logic Batch [N] Results
>
> ## Findings
>
> ### [EXPLOITABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Endpoint / feature**: [route or feature name]
> - **Scenario**: [attack description]
> - **Issue**: [missing/incomplete server-side validation]
> - **Impact**: [financial loss, privilege escalation, etc.]
> - **Remediation**: [server-side validation, atomic transactions, etc.]
> - **Dynamic test**: [curl command or race condition payload]
>
> ### [LIKELY EXPLOITABLE] / [NOT EXPLOITABLE] / [NEEDS MANUAL REVIEW]
> [Similar format]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Price manipulation, auth bypass, payment fraud → HIGH
> - Race condition double-spend → HIGH
> - Workflow bypass exposing sensitive features → MEDIUM-HIGH

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[EXPLOITABLE]** and **[LIKELY EXPLOITABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the full taint trace and a dynamic test command or payload
   - Separate each field with a blank line; end each entry with a `---` separator
4. Append the completion marker: `<!-- scan:business-logic completed -->`
5. Do NOT write [NOT EXPLOITABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 scenarios per subagent**. If 1-3 total, use a single subagent. Launch all batches **in parallel**.
- Each batch subagent receives only its assigned scenarios, not all Phase 1 findings.
- For payment systems, include the payment-specific checklist below in your Phase 1 threat modeling.
- Focus strictly on **business logic flaws** — do not flag injection bugs, auth bypass, or IDOR issues here.
- Threat modeling in Phase 1 should be **application-specific**: generic scenarios not grounded in the actual codebase are not useful.
- Server-side validation is the only valid protection. Client-side validation, frontend form constraints, and API documentation that says "must be positive" are not security controls.
- Race conditions on financial operations are high-severity even if they appear to require exact timing — automated tools (Turbo Intruder, concurrent curl) make them trivial to exploit.
- When in doubt, classify as "Needs Manual Review" rather than "Not Exploitable". False negatives in a security assessment are worse than false positives.
- Pay attention to ORM and database-level constraints (CHECK constraints, unique indexes, transactions with locking) — these can provide enforcement that is not visible in application code alone.

## Payment & Financial Systems Checklist

If the application processes payments, also audit the following:

**Payment flow**
- Is the payment amount calculated server-side? (CRITICAL — never trust client-supplied amount)
- Is floating point arithmetic used in monetary calculations? (CRITICAL — use DECIMAL/integer)
- Is there an idempotency key? (network retries must not create double payments)
- Are payment state transitions enforced? (pending → confirmed → completed — invalid transitions blocked)

**Card data & PCI DSS**
- Are credit card numbers stored on the server? (must not — use PSP tokenization)
- Is card data (CVV, PAN) written to logs?
- Does the payment form use the PSP's iframe/SDK rather than posting directly to the server?
- Is 3D Secure verification implemented?

**Refunds & cancellations**
- Is refund authorization checked? (only authorized roles can trigger refunds)
- Can a refund exceed the original transaction amount?
- Is the refund operation atomic? (balance update + PSP call must succeed/fail together)
- Are repeated refund requests prevented?

**Accounting & audit trail**
- Does every financial transaction leave an immutable audit log?
- Is double-entry bookkeeping applied? (every debit balanced by a credit)
- Is there a reconciliation mechanism to detect balance inconsistencies?
- Are currency conversions recorded with exchange rate and timestamp?