# CloudEvents & Event Streaming Reference

## CloudEvents 1.0 Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `specversion` | String | Always `"1.0"` |
| `type` | String | Event type (reverse-DNS) — e.g., `com.example.order.created` |
| `source` | URI-reference | Event origin — e.g., `/orders/service` |
| `id` | String | Unique per source — UUID recommended |

## Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `time` | Timestamp | RFC 3339 — e.g., `2024-01-15T10:30:00Z` |
| `datacontenttype` | String | MIME type of `data` — e.g., `application/json` |
| `dataschema` | URI | Schema URL for `data` payload |
| `subject` | String | Subject within source — e.g., `order-12345` |

## CloudEvents JSON Envelope

```json
{
  "specversion": "1.0",
  "type": "com.example.order.created",
  "source": "/orders/service",
  "id": "evt_a1b2c3d4",
  "time": "2024-01-15T10:30:00Z",
  "datacontenttype": "application/json",
  "dataschema": "https://schemas.example.com/order/v1.json",
  "subject": "order-12345",
  "data": {
    "orderId": "order-12345",
    "customerId": "cust-6789",
    "total": 99.99,
    "currency": "USD"
  }
}
```

## Transport Binding Differences

| Broker | Binding Mode | CloudEvents Attrs | Content |
|--------|-------------|-------------------|---------|
| **Kafka** | Structured or Binary | Binary: `ce_*` headers | Value = data |
| **AMQP** | Structured or Binary | Binary: `cloudEvents:*` app props | Body = data |
| **NATS** | Structured | All in JSON envelope | Full JSON |
| **HTTP** | Structured or Binary | Binary: `Ce-*` HTTP headers | Body = data |

### Kafka Binary Mode Example
```
Headers:
  ce_specversion: 1.0
  ce_type: com.example.order.created
  ce_source: /orders/service
  ce_id: evt_a1b2c3d4
  content-type: application/json
Key: order-12345
Value: {"orderId":"order-12345","total":99.99}
```

## Topic Naming Conventions

| Broker | Convention | Example |
|--------|-----------|---------|
| Kafka | `<domain>.<entity>.<event>` | `orders.order.created` |
| AMQP | `<domain>.<entity>.<event>` routing key | `orders.order.created` |
| NATS | Dot-delimited hierarchy | `orders.order.created` |
| MQTT | Slash-delimited hierarchy | `orders/order/created` |

Use **past tense** for event names: `created`, `updated`, `deleted`, `shipped`.

## Schema Evolution Strategies

| Strategy | Producer Change | Consumer Impact |
|----------|----------------|-----------------|
| **Backward** | Can read old data with new schema | New consumers read old events ✅ |
| **Forward** | Old schema can read new data | Old consumers read new events ✅ |
| **Full** | Both backward + forward | Maximum compatibility ✅ |
| **None** | No guarantees | Breaking changes possible ⚠️ |

### Rules for Safe Evolution
- ✅ Add optional fields with defaults
- ✅ Add new enum values (if consumer handles unknown)
- ❌ Remove required fields
- ❌ Rename fields (use `aliases` in Avro)
- ❌ Change field types

Use a **Schema Registry** (Confluent, Apicurio, AWS Glue) to enforce compatibility.

## Dead Letter Queue Patterns

```
┌──────────┐    fail     ┌──────────┐    N retries    ┌─────────┐
│  Source   │───────────→│ Consumer │────────────────→│   DLQ   │
│  Topic   │            │          │                  │  Topic  │
└──────────┘            └──────────┘                  └─────────┘
                                                          │
                                                    ┌─────┴─────┐
                                                    │  Monitor  │
                                                    │  + Alert  │
                                                    └───────────┘
```

### DLQ Best Practices
- Preserve original event + error metadata
- Include retry count and last error message
- Set TTL / expiration on DLQ messages
- Alert on DLQ depth thresholds
- Provide a replay mechanism for reprocessing

### DLQ Envelope
```json
{
  "originalEvent": { "...CloudEvents envelope..." },
  "error": {
    "message": "Schema validation failed",
    "code": "VALIDATION_ERROR",
    "timestamp": "2024-01-15T10:31:00Z",
    "retryCount": 3,
    "consumerGroup": "order-processor"
  }
}
```
