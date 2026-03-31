# Webhook Security & Reliability Reference

## HMAC-SHA256 Signature Verification Flow

```
1. Sender computes:  HMAC-SHA256(secret, raw_body)
2. Sender includes:  X-Signature-256: sha256=<hex_digest>
3. Receiver computes: HMAC-SHA256(secret, raw_body)
4. Receiver compares: timing-safe equality check
```

### Node.js Implementation

```javascript
const crypto = require('crypto');

function verifySignature(payload, signature, secret) {
  const expected = 'sha256=' +
    crypto.createHmac('sha256', secret).update(payload, 'utf8').digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

**Critical**: Always use raw request body (not parsed JSON) for signature computation.

## Timestamp-Based Replay Protection

```
X-Webhook-Timestamp: 1705312200
X-Webhook-Signature: sha256=abc123...

// Verification:
1. signed_payload = `${timestamp}.${body}`
2. sig = HMAC-SHA256(secret, signed_payload)
3. Reject if |now - timestamp| > 300 seconds (5-minute tolerance)
```

This prevents captured signatures from being replayed after the time window.

## Idempotency Key Patterns

```
X-Webhook-ID: evt_a1b2c3d4e5
```

### Receiver-Side Deduplication

```sql
-- Check before processing
SELECT 1 FROM processed_webhooks WHERE event_id = $1;

-- Record after processing (with TTL cleanup)
INSERT INTO processed_webhooks (event_id, processed_at)
VALUES ($1, NOW())
ON CONFLICT DO NOTHING;
```

Store processed IDs for **at least 72 hours** to cover retry windows.

## Retry Policy Best Practices

### Exponential Backoff + Jitter

```
Attempt 1:  immediate
Attempt 2:  ~1 min    (60s + random 0-30s)
Attempt 3:  ~5 min    (300s + random 0-60s)
Attempt 4:  ~30 min   (1800s + random 0-120s)
Attempt 5:  ~2 hours  (7200s + random 0-300s)
```

### Retry Conditions

| Response | Action |
|----------|--------|
| 2xx | Success — stop retrying |
| 410 Gone | Unsubscribe endpoint permanently |
| 4xx (other) | Do NOT retry (client error) |
| 5xx | Retry with backoff |
| Timeout (>30s) | Retry with backoff |
| Connection refused | Retry with backoff |

**Disable endpoint** after N consecutive failures (e.g., 5 days of failures).

## Subscription Verification Challenge

### Hub-Initiated (WebSub pattern)
```
GET /webhook-endpoint?hub.mode=subscribe
    &hub.topic=orders
    &hub.challenge=random_token_abc123
    &hub.lease_seconds=86400

Response: 200 OK
Body: random_token_abc123
```

### Registration-Time Verification
```json
POST /api/webhooks
{
  "url": "https://receiver.example.com/hook",
  "events": ["order.created"],
  "secret": "whsec_..."
}
// Platform sends test event; endpoint must respond 200
```

## Common SaaS Webhook Patterns

| Provider | Signature Header | Algorithm | Timestamp |
|----------|-----------------|-----------|-----------|
| **GitHub** | `X-Hub-Signature-256` | HMAC-SHA256 | ❌ |
| **Stripe** | `Stripe-Signature` | HMAC-SHA256 | `t=` in header |
| **Twilio** | `X-Twilio-Signature` | HMAC-SHA1 (URL+params) | ❌ |
| **Slack** | `X-Slack-Signature` | HMAC-SHA256 | `X-Slack-Request-Timestamp` |
| **Shopify** | `X-Shopify-Hmac-SHA256` | HMAC-SHA256 (base64) | ❌ |

### Stripe Signature Format
```
Stripe-Signature: t=1705312200,v1=abc123hex,v0=legacy_hex
// signed_payload = `${t}.${raw_body}`
// sig = HMAC-SHA256(endpoint_secret, signed_payload)
```

## Webhook Receiver Best Practices

1. **Respond fast**: Return `200/202` within 5 seconds; process async
2. **Verify always**: Check signature before any processing
3. **Log everything**: Store raw payload + headers for debugging
4. **Idempotent handlers**: Same event delivered twice = same outcome
5. **Queue internally**: Push to job queue, respond immediately

```
┌────────┐  POST   ┌──────────┐  enqueue  ┌─────────┐  process  ┌──────────┐
│ Sender │───────→│ Receiver │──────────→│  Queue  │─────────→│ Handler  │
└────────┘  200 ← └──────────┘           └─────────┘          └──────────┘
              <5s        verify sig
```

6. **Use HTTPS only** — reject plain HTTP webhook registrations
7. **Allowlist IPs** when the sender publishes IP ranges (GitHub, Stripe)
