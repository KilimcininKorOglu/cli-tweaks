---
name: race-condition
description: "Detect race conditions and TOCTOU flaws where concurrent requests break a
  shared-state invariant: check-then-act on balances and stock, non-atomic
  counters, single-use tokens redeemed twice, and file check-then-use."
---

# Race Condition and TOCTOU Detection

You are performing a focused security assessment to find race conditions. This skill uses a three-phase approach: **recon** (find check-then-act sequences over shared state), **batched verify** (prove the window is reachable by concurrent callers and unguarded), and **merge** (write confirmed findings to `BUG-REPORT.md`).

---

## What is a Race Condition

A race condition occurs when two operations read the same shared state, both pass a check, and both act on the stale value. The window between the read and the write is the vulnerability. TOCTOU (time-of-check-to-time-of-use) is the same flaw over a file or a path instead of a row.

The core pattern: *an invariant is checked in application memory, then enforced by a later write that does not re-check it.*

### What a Race Condition IS

- Reading a balance, comparing it, then subtracting in a second statement
- Reading a counter, adding one in application code, then writing it back
- Checking `coupon.used == false`, then setting `used = true` in a separate write
- Checking stock, then decrementing it outside a transaction
- `os.Stat(path)` followed by `os.ReadFile(path)` or `os.Chmod(path)`
- Checking a rate-limit counter in one request, then incrementing it after the work

### What a Race Condition is NOT

Do not flag these:
- **Read-only paths**: concurrent reads that write nothing cannot race
- **Idempotent writes**: setting a field to a constant produces the same result at any interleaving
- **A single atomic statement**: `UPDATE t SET n = n + 1 WHERE id = ?` resolves in the database
- **A guarded window**: `SELECT ... FOR UPDATE`, `SERIALIZABLE`, an advisory lock, or a unique constraint that rejects the second write
- **A conditional update**: `UPDATE coupons SET used = true WHERE code = ? AND used = false` returning an affected-row count that the caller checks
- **Process-local state with one writer**: a value only one goroutine or worker ever writes

### Patterns That Prevent Race Conditions

```python
# Python/Django — row lock plus an in-database expression
with transaction.atomic():
    account = Account.objects.select_for_update().get(pk=pk)
    if account.balance >= amount:
        Account.objects.filter(pk=pk).update(balance=F("balance") - amount)
```

```sql
-- SQL — enforce the invariant in the write itself
UPDATE accounts SET balance = balance - :amount
 WHERE id = :id AND balance >= :amount;
-- zero affected rows means the caller must fail the request
```

```go
// Go — open the file, then act on the descriptor
f, err := os.OpenFile(path, os.O_RDONLY|syscall.O_NOFOLLOW, 0)
if err != nil { return err }
defer f.Close()
```

---

## Vulnerable vs. Secure Examples

### Node.js — non-atomic counter

```javascript
// VULNERABLE: read, add, write
const post = await Post.findById(id);
post.likes += 1;
await post.save();

// SECURE: atomic operator in the database
await Post.findByIdAndUpdate(id, { $inc: { likes: 1 } });
```

### Python — single-use token redeemed twice

```python
# VULNERABLE: check then mark
coupon = Coupon.objects.get(code=code)
if not coupon.used:
    apply_discount(order_id, coupon.discount)
    coupon.used = True
    coupon.save()

# SECURE: conditional update decides the winner
claimed = Coupon.objects.filter(code=code, used=False).update(used=True)
if claimed == 1:
    apply_discount(order_id, coupon.discount)
```

### Go — TOCTOU on a path

```go
// VULNERABLE: the path can be replaced between the two calls
if info, err := os.Stat(p); err == nil && info.Mode().IsRegular() {
    data, _ := os.ReadFile(p)
    use(data)
}

// SECURE: open once, inspect the descriptor
f, err := os.Open(p)
if err != nil { return err }
defer f.Close()
if st, err := f.Stat(); err == nil && st.Mode().IsRegular() {
    data, _ := io.ReadAll(f)
    use(data)
}
```

---

## Execution

### Phase 1: Find Check-Then-Act Sequences

Launch a subagent with the following instructions:

> **Goal**: Find every place where shared state is read, tested, and then written in a later statement. Return findings in your response.
>
> **What to search for**:
>
> 1. **Money and quota state**: `balance`, `credit`, `quota`, `limit`, `points`, `wallet`, `refund`, `withdraw`, `transfer`, `charge`
> 2. **Inventory state**: `stock`, `quantity`, `inventory`, `seats`, `slots`, `capacity`, `reserve`
> 3. **Single-use state**: `used`, `redeemed`, `consumed`, `claimed`, `invite`, `coupon`, `voucher`, `otp`, `reset_token`, `idempotency`
> 4. **Counters**: any field read into a variable, modified in application code, and written back
> 5. **File check-then-use**: `stat`, `exists`, `access`, `lstat`, `isFile` followed by `open`, `read`, `write`, `chmod`, `chown`, `rename`, `unlink` on the same path
> 6. **Lock vocabulary**: `FOR UPDATE`, `SERIALIZABLE`, `advisory_lock`, `Mutex`, `synchronized`, `atomic`, `Redlock`, `setnx` — record where these ARE used, so the verify phase can tell guarded code from unguarded code
>
> **What to skip**: read-only handlers, single-writer background jobs, in-process caches with no cross-request effect, test fixtures.
>
> **Output format** — return in your response:
>
> ```markdown
> # Race Recon: [Project Name]
>
> ## Summary
> Found [N] check-then-act sequences over shared state.
>
> ## Sequences
>
> ### 1. [Descriptive name]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Entry point**: [HTTP route, job, or CLI command that reaches it]
> - **Shared state**: [table.column, cache key, or path]
> - **Check**: [the read and the comparison]
> - **Act**: [the write that follows]
> - **Guard seen**: [transaction / row lock / atomic operator / none]
> - **Code snippet**:
>   ```
>   [the sequence]
>   ```
> ```

### Phase 2: Batched Verify — Prove the Window Is Exploitable

After Phase 1 completes, count numbered sequences. If 3 or fewer, use a single subagent. Otherwise split the sequences into batches of up to 3 and run them through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.

> **For each sequence, answer these in order**:
>
> 1. **Concurrency**: can two requests execute this code at the same time? A single-threaded runtime still races across processes, replicas, and awaited I/O. Note the model rather than assuming safety.
> 2. **Attacker control**: can one caller issue the two requests, or does the second request need another user?
> 3. **Guard**: does a transaction wrap BOTH the check and the write? Does the write re-test the condition? Is there a unique constraint, a conditional update with a checked affected-row count, or a distributed lock?
> 4. **Isolation level**: `READ COMMITTED` does not stop a lost update. Only claim safety when the guard is explicit in the code.
> 5. **Result**: what does the winner gain — double spend, free item, extra redemption, bypassed rate limit, escalated role?
>
> **Classification**:
> - **Vulnerable**: unguarded window reachable by a repeatable request with a concrete gain
> - **Likely Vulnerable**: unguarded window whose reachability or gain needs one unresolved fact
> - **Not Vulnerable**: guarded by a lock, a constraint, an atomic write, or a checked conditional update
> - **Needs Manual Review**: the guard depends on a runtime fact not visible in the repository, such as the deployed isolation level
>
> **Output format** — return in your response:
>
> ```markdown
> # Race Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Entry point**: [route or job]
> - **Issue**: [the unguarded window]
> - **Interleaving**: [request A step, request B step, resulting state]
> - **Gain**: [what the attacker obtains]
> - **Remediation**: [lock, atomic write, conditional update, or constraint]
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
- Money or credit double spend, or balance manipulation → CRITICAL
- Inventory oversell, single-use token redeemed twice, or privilege gained through the window → HIGH
- Rate-limit bypass, counter manipulation, or TOCTOU on a non-privileged path → MEDIUM
- Race in logging, analytics, or a counter with no security or money effect → LOW

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1. Phase 3 runs AFTER all batches.
- Batch size: 3 sequences per subagent. If 1-3 total, single subagent. Run the batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- A transaction alone is not a guard. `BEGIN` plus a plain `SELECT` still reads a stale value under `READ COMMITTED`.
- An `async`/`await` handler yields at every I/O call, so a single-threaded runtime interleaves requests inside the window.
- Never prove a race by firing concurrent requests at a running system. Prove it from the code path and describe the interleaving.
- Overlap with `business-logic` is expected. Report the concurrency window here and the workflow flaw there; deduplicate by root cause during the merge.

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
