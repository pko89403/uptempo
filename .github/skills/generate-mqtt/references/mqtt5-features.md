# MQTT 5.0 Features Reference

## QoS Level Comparison

| QoS | Name | Delivery Guarantee | Flow | Use Case |
|-----|------|--------------------|------|----------|
| 0 | At most once | Fire-and-forget | PUBLISH → | Telemetry, metrics |
| 1 | At least once | Ack'd, may duplicate | PUBLISH → ← PUBACK | Notifications, alerts |
| 2 | Exactly once | 4-step handshake | PUBLISH → ← PUBREC → PUBREL → ← PUBCOMP | Financial transactions |

**Default to QoS 1** — it's the best balance of reliability and performance.
QoS 2 has 2x the round-trips; only use when duplicates cause real harm.

## Topic Hierarchy Best Practices

```
{org}/{domain}/{entity}/{id}/{attribute}
```

### Examples
```
acme/factory/sensor/temp-001/temperature
acme/factory/sensor/temp-001/humidity
acme/fleet/vehicle/truck-42/location
acme/home/room/living/light/status
```

### Rules
- Use `/` as level separator
- Use lowercase kebab-case
- Keep depth ≤ 7 levels
- Never start with `/` (creates empty first level)
- Never use spaces or special characters

## Wildcard Patterns

| Wildcard | Symbol | Scope | Example |
|----------|--------|-------|---------|
| Single-level | `+` | One level | `acme/factory/sensor/+/temperature` |
| Multi-level | `#` | All remaining | `acme/factory/#` |

```
acme/factory/sensor/+/temperature
  ✅ acme/factory/sensor/temp-001/temperature
  ✅ acme/factory/sensor/temp-002/temperature
  ❌ acme/factory/sensor/temp-001/humidity

acme/factory/#
  ✅ acme/factory/sensor/temp-001/temperature
  ✅ acme/factory/machine/press-01/status
  ✅ acme/factory
```

`#` must be the **last** character in the subscription filter.

## MQTT 5 New Features

### User Properties
Key-value metadata on any packet (PUBLISH, CONNECT, etc.):
```
PUBLISH topic: acme/orders/created
  User Property: correlation-id = "req-abc123"
  User Property: content-type = "application/json"
  User Property: trace-id = "4bf92f3577..."
```

### Content Type
```
Content Type: application/json
```
Indicates payload format — broker passes through, does not interpret.

### Response Topic & Correlation Data
Enables **request-response** over MQTT:
```
// Request
PUBLISH topic: services/user/get
  Response Topic: reply/client-42/inbox
  Correlation Data: "req-001"
  Payload: {"userId": "u_123"}

// Response
PUBLISH topic: reply/client-42/inbox
  Correlation Data: "req-001"
  Payload: {"name": "Alice"}
```

### Message Expiry Interval
```
Message Expiry Interval: 3600  // seconds
```
Broker discards the message if not delivered within TTL.
Useful for time-sensitive alerts and commands.

### Shared Subscriptions
Load-balance messages across consumer group members:
```
$share/{group-name}/{topic-filter}

Example:
$share/order-processors/acme/orders/+/created
```
Each message is delivered to **one** member of the group (round-robin).

## Last Will and Testament (LWT)

Configured at CONNECT time; broker publishes if client disconnects ungracefully:

```
Will Topic:   acme/devices/sensor-01/status
Will Payload: {"status": "offline", "timestamp": "2024-01-15T10:30:00Z"}
Will QoS:     1
Will Retain:  true
Will Delay Interval: 30   // MQTT 5: wait 30s before publishing (grace period)
```

Use retained LWT to maintain device presence state.

## Clean Start vs Session Expiry

| MQTT 3.1.1 | MQTT 5 | Behavior |
|------------|--------|----------|
| `Clean Session: true` | `Clean Start: true` + `Session Expiry: 0` | No persistent session |
| `Clean Session: false` | `Clean Start: false` + `Session Expiry: N` | Resume session, expire after N seconds |
| — | `Clean Start: true` + `Session Expiry: N` | New session, persist for N seconds |

```
Session Expiry Interval: 3600      // Keep session for 1 hour after disconnect
Session Expiry Interval: 4294967295 // Never expire (~136 years)
Session Expiry Interval: 0         // Destroy on disconnect (default)
```

## Retained Messages

```
PUBLISH topic: devices/sensor-01/status
  Retain: true
  Payload: {"status": "online", "battery": 87}
```

- **New subscribers** immediately receive the last retained message
- **Clear** a retained message by publishing empty payload with retain flag
- Only **one** retained message per topic (latest wins)
- Use for: device status, config, last known values

## Quick Checklist

- [ ] Use QoS 1 unless you have a specific reason not to
- [ ] Design topic hierarchy before writing code
- [ ] Set Message Expiry on time-sensitive messages
- [ ] Configure LWT for device presence tracking
- [ ] Use Shared Subscriptions for horizontal scaling
- [ ] Set appropriate Session Expiry for intermittent clients
- [ ] Use retained messages for "current state" topics
