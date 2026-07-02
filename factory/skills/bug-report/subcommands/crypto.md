---
name: crypto
description: >-
  Detect cryptography weakness vulnerabilities using a two-phase approach:
  first find crypto usage sites (hashing, encryption, PRNG, TLS config), then
  verify whether weak algorithms, insecure modes, or poor key management are
  used. Use when asked to find crypto or cryptography bugs.
---

# Cryptography Weakness Detection

You are performing a focused security assessment to find cryptography weaknesses in a codebase. This skill uses a two-phase approach with subagents: **discovery** (find all cryptographic operations) then **verify** (confirm whether weak algorithms, insecure modes, hardcoded keys/IVs, weak PRNG, or disabled certificate validation are used).

---

## What is Cryptography Weakness

Cryptography weakness occurs when an application uses broken or improperly configured cryptographic primitives, enabling attackers to decrypt data, forge signatures, predict tokens, or perform man-in-the-middle attacks. The core pattern: *a cryptographic operation uses an algorithm, mode, key, or random source that does not provide the security guarantees the application assumes.*

### What Cryptography Weakness IS

- MD5 or SHA1 used for password hashing (trivially crackable with rainbow tables / GPU)
- ECB mode for block cipher encryption (reveals patterns in encrypted data)
- Hardcoded or static initialization vector (IV) or salt (makes encryption deterministic)
- `Math.random()`, `random.random()`, or `java.util.Random` for security tokens, session IDs, or cryptographic keys
- Disabled SSL/TLS certificate verification: `verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify: true`
- Weak key sizes: RSA < 2048 bits, AES < 128 bits, ECDSA < 256 bits
- Deprecated algorithms: DES, 3DES, RC4, RC2, Blowfish for encryption
- AES-CBC without HMAC (no authenticated encryption — vulnerable to padding oracle attacks)
- Hardcoded encryption keys in source code

### What Cryptography Weakness is NOT

Do not flag these:

- **MD5/SHA1 for non-security purposes**: file checksums, cache keys, content hashing, deduplication, ETag generation, git SHAs
- **Math.random() for non-security purposes**: random UI colors, shuffling non-sensitive lists, animation timing
- **Test certificates**: Self-signed certs and `verify=False` in clearly test-scoped code
- **Legacy compatibility with migration plan**: Documented use of older algorithm with active migration to stronger one
- **Content-addressable hashing**: Using SHA1 for content addressing (git model) where collision resistance is not the primary concern
- **HMAC-MD5/HMAC-SHA1**: HMAC construction makes these safer than raw hash (still worth noting but lower severity)

### Patterns That Prevent Cryptography Weakness

When you see these patterns, the code is likely **not vulnerable**:

**1. Strong password hashing**
```python
# bcrypt, argon2, or scrypt — proper password hashing
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

**2. Authenticated encryption (AES-GCM)**
```java
Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
```

**3. Cryptographic PRNG**
```javascript
const token = crypto.randomBytes(32).toString('hex');
```

**4. Random IV per encryption**
```javascript
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
```

---

## Vulnerable vs. Secure Examples

### Weak Password Hashing

```python
# VULNERABLE: MD5 for password storage
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()

# VULNERABLE: SHA1 for password storage
password_hash = hashlib.sha1(password.encode()).hexdigest()

# VULNERABLE: SHA256 without salt (fast hash, rainbow table vulnerable)
password_hash = hashlib.sha256(password.encode()).hexdigest()

# SECURE: bcrypt with cost factor
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# SECURE: argon2
from argon2 import PasswordHasher
ph = PasswordHasher()
password_hash = ph.hash(password)
```

### ECB Mode

```java
// VULNERABLE: ECB mode reveals patterns in encrypted data
Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");

// VULNERABLE: Default mode (often ECB in some implementations)
Cipher cipher = Cipher.getInstance("AES");

// SECURE: GCM mode (authenticated encryption)
Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
```

### Hardcoded IV / Salt

```javascript
// VULNERABLE: Static IV — makes encryption deterministic
const iv = Buffer.from('0000000000000000');
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);

// VULNERABLE: Hardcoded salt
const salt = 'mysalt123';
const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512');

// SECURE: Random IV per encryption
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);

// SECURE: Random salt per hash
const salt = crypto.randomBytes(16);
const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512');
```

### Weak PRNG for Security

```javascript
// VULNERABLE: Math.random for security tokens
const token = Math.random().toString(36).substring(2);
const sessionId = Math.random().toString(16).slice(2);

// SECURE: Cryptographic random
const token = crypto.randomBytes(32).toString('hex');
```

```python
# VULNERABLE: random module for security tokens
import random
token = ''.join(random.choices(string.ascii_letters, k=32))

# SECURE: secrets module
import secrets
token = secrets.token_hex(32)
```

```java
// VULNERABLE: java.util.Random for security
Random rand = new Random();
int otp = rand.nextInt(999999);

// SECURE: SecureRandom
SecureRandom rand = new SecureRandom();
int otp = rand.nextInt(999999);
```

### Disabled Certificate Validation

```python
# VULNERABLE: Disabling SSL verification
requests.get(url, verify=False)
urllib3.disable_warnings(InsecureRequestWarning)

# VULNERABLE: Custom SSL context with no verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
```

```javascript
// VULNERABLE: Disabling TLS verification
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// VULNERABLE: Per-request disable
const agent = new https.Agent({ rejectUnauthorized: false });
axios.get(url, { httpsAgent: agent });
```

```go
// VULNERABLE: Skipping TLS verification
tr := &http.Transport{
    TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
}
```

### Weak Key Sizes

```python
# VULNERABLE: RSA 1024-bit key
from Crypto.PublicKey import RSA
key = RSA.generate(1024)

# SECURE: RSA 2048-bit minimum (4096 recommended)
key = RSA.generate(4096)
```

### Deprecated Algorithms

```python
# VULNERABLE: DES encryption
from Crypto.Cipher import DES
cipher = DES.new(key, DES.MODE_ECB)

# VULNERABLE: RC4
from Crypto.Cipher import ARC4
cipher = ARC4.new(key)

# VULNERABLE: 3DES (TripleDES)
from Crypto.Cipher import DES3
cipher = DES3.new(key, DES3.MODE_CBC, iv)

# SECURE: AES-256-GCM
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
```

---

## Execution

### Phase 1: Find Cryptographic Usage Sites

Launch a subagent with the following instructions:

> **Goal**: Find every location in the codebase where cryptographic operations are performed — hashing, encryption/decryption, random number generation for security, TLS/SSL configuration, and key management. Write results to `Phase 1 findings`.
>
> **Context**: You will be given the project's architecture summary. Use it to understand the tech stack, authentication system, encryption needs, and external service communication.
>
> **What to search for — cryptographic usage patterns**:
>
> 1. **Hashing operations**:
>    - `hashlib.md5`, `hashlib.sha1`, `hashlib.sha256`, `crypto.createHash`
>    - `MessageDigest.getInstance("MD5")`, `MessageDigest.getInstance("SHA-1")`
>    - `bcrypt`, `argon2`, `scrypt`, `pbkdf2`
>    - Context: is the hash used for passwords, signatures, tokens, or non-security purposes?
>
> 2. **Encryption/decryption operations**:
>    - `crypto.createCipheriv`, `Cipher.getInstance`, `AES.new`, `Fernet`
>    - Cipher mode: `ECB`, `CBC`, `GCM`, `CTR`
>    - IV/nonce: is it hardcoded, static, or randomly generated?
>    - Key source: hardcoded, environment variable, KMS, or derived?
>
> 3. **Random number generation**:
>    - `Math.random()`, `random.random()`, `random.randint()`, `rand()`
>    - `java.util.Random`, `System.Random`
>    - Context: is the random value used for tokens, session IDs, OTPs, cryptographic keys?
>    - Secure alternatives present: `crypto.randomBytes`, `secrets`, `SecureRandom`
>
> 4. **TLS/SSL configuration**:
>    - `verify=False`, `verify_ssl=False`, `rejectUnauthorized: false`
>    - `InsecureSkipVerify: true`, `CERT_NONE`, `CERT_OPTIONAL`
>    - TLS version: `TLSv1`, `TLSv1.1`, `SSLv3`
>    - `NODE_TLS_REJECT_UNAUTHORIZED = '0'`
>
> 5. **Key management**:
>    - Hardcoded keys: `key = "mysecretkey"`, `const SECRET = "abc123"`
>    - Key size: RSA key generation with bit size, AES key length
>    - Key storage: keys in source code, config files, or proper secrets management
>
> **What to skip**:
> - MD5/SHA1 used explicitly for non-security purposes (cache keys, file checksums, ETags)
> - Math.random() for UI effects, animations, or non-security randomness
> - Test-only crypto configurations in test files
>
> **Output format** — return findings in your response in this format:
>
> ```markdown
> # Crypto Recon: [Project Name]
>
> ## Summary
> Found [N] cryptographic usage sites.
>
> ## Crypto Sites
>
> ### 1. [Descriptive name — e.g., "MD5 password hashing in auth service"]
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / endpoint**: [function name or context]
> - **Crypto operation**: [hashing / encryption / PRNG / TLS config / key management]
> - **Algorithm / method**: [MD5 / SHA1 / AES-ECB / Math.random / verify=False / etc.]
> - **Apparent purpose**: [password hashing / token generation / data encryption / API call / etc.]
> - **Code snippet**:
>   ```
>   [the cryptographic code]
>   ```
>
> [Repeat for each site]
> ```

### Phase 2: Batched Verify — Confirm Cryptographic Weaknesses

After Phase 1 completes, count the numbered site sections (`### 1.`, `### 2.`, ...) from Phase 1 findings.

**If 3 or fewer sites**: Launch a single subagent with all sites (skip batching).

**If more than 3 sites**: Split into batches of up to 3 each. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes. Each subagent returns findings in its response (NOT to a file).

Give each batch subagent the following instructions (include assigned sites from Phase 1):

> **Context**: You will be given the project's architecture summary and the Phase 1 recon output. Use the architecture to understand what data is being protected and the threat model.
>
> **For each crypto site, verify whether the implementation is actually weak**:
>
> 1. **Algorithm assessment**: Is the algorithm appropriate for its use case?
>    - MD5/SHA1 for passwords → VULNERABLE (use bcrypt/argon2/scrypt)
>    - MD5/SHA1 for signatures/HMAC → LIKELY VULNERABLE (use SHA-256+)
>    - MD5/SHA1 for checksums/cache → NOT VULNERABLE
>    - DES/3DES/RC4 for encryption → VULNERABLE (use AES-256)
>
> 2. **Mode assessment**: Is the cipher mode appropriate?
>    - ECB → VULNERABLE (reveals patterns)
>    - CBC without HMAC → LIKELY VULNERABLE (padding oracle)
>    - GCM/CCM → NOT VULNERABLE (authenticated encryption)
>
> 3. **IV/Salt/Nonce assessment**: Is randomness properly applied?
>    - Hardcoded or static IV → VULNERABLE (deterministic encryption)
>    - Hardcoded salt → VULNERABLE (rainbow table attack)
>    - Random per-operation → NOT VULNERABLE
>
> 4. **PRNG assessment**: Is the random source cryptographically secure?
>    - `Math.random()` / `random.random()` / `java.util.Random` for security → VULNERABLE
>    - Same for non-security → NOT VULNERABLE
>    - `crypto.randomBytes` / `secrets` / `SecureRandom` → NOT VULNERABLE
>
> 5. **TLS assessment**: Is certificate validation properly configured?
>    - `verify=False` in production HTTP client → VULNERABLE
>    - `verify=False` in test only → NOT VULNERABLE
>    - `InsecureSkipVerify` for internal services → LIKELY VULNERABLE
>
> 6. **Key management assessment**: Are keys properly managed?
>    - Hardcoded in source code → VULNERABLE
>    - From environment variable → acceptable (if not committed)
>    - From KMS/secrets manager → NOT VULNERABLE
>    - Key size < 2048 RSA / < 128 AES → VULNERABLE
>
> **Classification**:
> - **Vulnerable**: Weak cryptographic primitive used for a security-critical purpose with no compensating controls.
> - **Likely Vulnerable**: Suboptimal crypto with partial mitigation or unclear context.
> - **Not Vulnerable**: Strong algorithm/mode/key used correctly, or non-security usage of weaker primitive.
> - **Needs Manual Review**: Cannot determine the purpose or context of the crypto operation.
>
> **Output format** — return findings in your response using this format:
>
> ```markdown
> # Crypto Batch [N] Results
>
> ## Findings
>
> ### [VULNERABLE] Descriptive name
> - **File**: `path/to/file.ext` (lines X-Y)
> - **Function / context**: [where the crypto is used]
> - **Issue**: [e.g., "MD5 used for password hashing — trivially crackable with rainbow tables"]
> - **Algorithm**: [current] → **Recommended**: [replacement]
> - **Impact**: Password cracking, data decryption, token prediction, MitM attack
> - **Remediation**: Replace MD5 with bcrypt for passwords, AES-256-GCM for encryption, crypto.randomBytes for tokens
> - **Dynamic test**: [e.g., "Hash a known password with MD5 and verify against rainbow table lookup"]
>
> ### [LIKELY VULNERABLE] / [NOT VULNERABLE] / [NEEDS MANUAL REVIEW]
> [Similar format with appropriate fields]
> ```
>
> **Severity mapping** (for use in Phase 3 reporting):
> - Hardcoded encryption keys, ECB mode on sensitive data, disabled cert validation on auth endpoints → CRITICAL
> - MD5/SHA1 for passwords, static IV/salt, Math.random for security tokens → HIGH
> - AES-CBC without HMAC, weak key sizes, deprecated TLS versions → MEDIUM
> - Weak PRNG in low-sensitivity context, MD5 for non-security with misleading variable name → LOW

### Phase 3: Merge & Report

After all Phase 2 subagents complete:

1. Collect all batch responses.
2. Extract only **[VULNERABLE]** and **[LIKELY VULNERABLE]** findings.
3. Write confirmed findings to `BUG-REPORT.md` using the shared format from `../SKILL.md`:
   - Read existing `BUG-REPORT.md` to continue the ID sequence (start at BUG-001 if none exists)
   - Each finding as `### BUG-[ID]: [title]` with severity per the mapping above
   - For **Suggested Commit**: place BEFORE Problem field, wrap value in backticks, conventional commit message without BUG-IDs
   - For **Verification**: include the weak algorithm/configuration and recommended replacement
   - Separate each field with a blank line; end each entry with a `---` separator
4. Do NOT write [NOT VULNERABLE] or [NEEDS MANUAL REVIEW] entries to `BUG-REPORT.md`.

---

## Important Reminders

- Phase 1 returns findings in response — do not write to files.
- Phase 2 batches run AFTER Phase 1 completes. Phase 3 runs AFTER all batches complete.
- Batch size is **3 sites per subagent**. If 1-3 total, use a single subagent. Run batch subagents through a rolling worker pool with at most 2 concurrent subagents. Start up to 2 batch subagents initially, then launch the next pending batch immediately whenever one finishes.
- Each batch subagent receives only its assigned sites, not all Phase 1 findings.
- **Phase 1 is purely structural**: find all cryptographic usage sites regardless of whether they are secure. Do not evaluate strength in Phase 1 — that is Phase 2's job.
- **Phase 2 is verification**: for each site, assess algorithm strength, mode, key management, and context.
- The most critical crypto weakness is **hardcoded encryption keys** — if the key is in source code, all encrypted data is compromised when the repo leaks.
- MD5 and SHA1 for password hashing are trivially crackable. Even SHA-256 without salt is weak for passwords. Only bcrypt, argon2, scrypt, or PBKDF2 with high iteration count are acceptable for password storage.
- ECB mode is always wrong for multi-block data encryption. It encrypts each block independently, revealing patterns in the plaintext.
- Static IVs make encryption deterministic — identical plaintexts produce identical ciphertexts, enabling pattern analysis.
- `Math.random()` in JavaScript is NOT cryptographically secure. It uses a PRNG (often xorshift128+) that is predictable after observing a few outputs.
- Disabled certificate validation (`verify=False`) enables man-in-the-middle attacks on every request made through that client.
- Context matters: MD5 for a cache key is fine; MD5 for a password is catastrophic. Always determine the purpose of the cryptographic operation before classifying severity.
- When in doubt, classify as "Needs Manual Review" rather than "Not Vulnerable". False negatives are worse than false positives in security assessment.
