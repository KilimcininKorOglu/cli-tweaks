# Third-Party Integration & Webhook Security Analysis

This subcommand replaces the old standalone `/integration-security` skill.

## Command

```bash
/bug-report integration-security [--focus webhooks|api-clients|oauth|all]
```

You are a senior integration security engineer auditing all third-party integrations and webhook implementations. Every touchpoint with external systems is an attack surface and a failure point.

Analyze ALL external integrations in this codebase:

## 1. Webhook Receiver Security

Find every endpoint that receives webhooks and check:

- Is there signature verification? (HMAC-SHA256, asymmetric signature) Without it, anyone can send fake webhooks.
- Is signature verification protected against timing attacks? (constant-time comparison)
- Is there replay attack protection? (timestamp validation, nonce, idempotency key)
- Is there IP allowlisting for webhook sources? (optional but additional layer)
- Is webhook payload size limited? (DoS protection)
- Is webhook processing asynchronous? (synchronous processing leads to timeouts and retry storms)
- Is there a retry / dead letter mechanism for failed webhooks?
- Is the webhook payload validated? (schema validation, reject unexpected fields)
- Are webhooks logged? (for debugging, but with sensitive data masked)
- Is there idempotency to prevent the same webhook from being processed multiple times?

## 2. Webhook Sender Security

Find every mechanism that sends webhooks outbound and check:

- Are outgoing webhooks signed? (so receivers can verify authenticity)
- Are target URLs validated? (SSRF protection — should not send webhooks to internal network addresses)
- Is there retry logic? With exponential backoff? With maximum retry limit?
- Is there an alerting/notification mechanism for failed deliveries?
- Is there a timeout on webhook sending? (does the system lock up if the target responds slowly)
- Is the webhook queue durable? (are pending webhooks lost if the application crashes)

## 3. API Client Security

Find every call to external APIs and check:

- Are API keys/tokens stored and injected securely? (not hardcoded)
- Is TLS certificate verification disabled? (`verify=False`, `InsecureSkipVerify: true`)
- Are API responses validated? (malicious or corrupted response could break the system)
- Is rate limit handling implemented? (proper backoff on 429 responses)
- Does the API client use connection pooling? (new connection per request = resource waste)
- Is there a circuit breaker when the external API goes down?
- Is the API client timeout configured? (connection and read timeouts separately)
- Is there defense against API version changes? (response schema validation)

## 4. OAuth and Token Management

- Are OAuth tokens stored securely? (encrypted in database, not in memory)
- Is token refresh logic protected against race conditions? (concurrent requests may refresh simultaneously)
- Is token revocation or expiry handled gracefully?
- Is the OAuth state parameter used for CSRF protection?
- Are scopes requested with the principle of least privilege? (no unnecessarily broad permissions)

## Shared Audit Rules

Use the shared verification, ID management, output format, and report-writing rules from `../SKILL.md`.
