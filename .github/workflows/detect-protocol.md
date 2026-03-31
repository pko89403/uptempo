---
name: Detect Protocol
description: "Analyze issue text and return detected protocols with confidence scores."
on:
  slash_command:
    name: detect-protocol
tools:
  github:
    toolsets: [default]
---

# Detect Protocol Workflow

Quick protocol detection that analyzes issue text and returns detected protocols with confidence scores. Use this to preview which agents would be invoked before running a full schema generation.

## Example Invocation

```
/detect-protocol https://linear.app/team/issue/ABC-123
/detect-protocol "We need a REST API for user management with WebSocket for real-time notifications and Kafka for domain events"
```

---

## Phase 1 — Input

Accept one of the following:

| Format | Handling |
|--------|----------|
| **Linear issue URL** | Fetch title, description, and labels via the tracker module (`src/uptempo/tracker/`) |
| **Raw text** | Use the text directly as the issue description; title and labels will be empty |

---

## Phase 2 — Analysis

Invoke the `ProtocolDetector` class from `src/uptempo/orchestrator/protocol_detector.py`.

### Detection Algorithm

1. **Text normalization** — Concatenate issue title and description, convert to lowercase.
2. **Keyword scan** — For each of the 9 protocol rules in `PROTOCOL_RULES`, check which keywords appear in the text or in the issue labels.
3. **Confidence scoring** — For each protocol with at least one keyword match:
   ```
   keyword_ratio = matched_keywords / total_keywords_in_rule
   confidence = min(0.4 + keyword_ratio × 0.4, 0.8)
   ```
4. **Label boost** — If any issue label matches the protocol's `confidence_boost_labels`, add `+0.15` (capped at `1.0`).
5. **Default** — If no protocol matches at all, return `rest` / `api-architect` with confidence `0.3`.

### Keyword Reference

| Protocol | Keywords | Boost Labels |
|----------|----------|--------------|
| REST | rest, crud, api, endpoint, resource, http, get, post, put, delete, patch | api, rest, backend |
| SSE | sse, server-sent, event-stream, eventsource, streaming, real-time push, unidirectional | realtime, sse, streaming |
| WebSocket | websocket, ws://, wss://, bidirectional, chat, real-time, socket | realtime, websocket, ws |
| gRPC | grpc, protobuf, proto, rpc, buf, internal service | grpc, protobuf, internal |
| GraphQL | graphql, query, mutation, subscription, sdl, relay, federation, apollo | graphql, federation, apollo |
| Kafka | kafka, rabbitmq, nats, event, queue, pub/sub, async, domain event, message broker, cqrs, event sourcing | events, kafka, messaging, async |
| Webhook | webhook, callback, external, saas, integration, hook, notification | webhook, integration, external |
| MQTT | mqtt, iot, device, telemetry, sensor, lwt, qos | iot, mqtt, device |
| tRPC | trpc, zod, typescript api, type-safe, fullstack, next.js api | trpc, typescript, fullstack |

---

## Phase 3 — Output

Print a table of detected protocols sorted by confidence (highest first):

```
┌────────────┬────────────┬──────────────────────┬───────────────────────┐
│ Protocol   │ Confidence │ Agent                │ Matched Keywords      │
├────────────┼────────────┼──────────────────────┼───────────────────────┤
│ REST       │ 72%        │ api-architect        │ rest, api, endpoint   │
│ WebSocket  │ 58%        │ realtime-engineer    │ websocket, real-time  │
│ Kafka      │ 47%        │ event-engineer       │ event, async          │
│ GraphQL    │ 40%        │ graphql-architect    │ query                 │
└────────────┴────────────┴──────────────────────┴───────────────────────┘
```

---

## Phase 4 — Recommendation

Based on confidence thresholds, categorize each detected protocol:

| Confidence | Action | Label |
|------------|--------|-------|
| **≥ 0.5** | **Invoke** — Agent will be dispatched automatically by `/generate-schema` | 🟢 Invoke |
| **0.3 – 0.49** | **Consider** — Protocol was detected but with low confidence; review before invoking | 🟡 Consider |
| **< 0.3** | Not shown (below detection threshold) | — |

### Example Recommendation Output

```
Recommendation
──────────────
🟢 Invoke:   REST (api-architect), WebSocket (realtime-engineer)
🟡 Consider: Kafka (event-engineer), GraphQL (graphql-architect)

Next step: Run /generate-schema to generate schemas for all invokable protocols.
           Add --include=kafka to also include low-confidence protocols.
```

### Agent Quick Reference

Each recommended agent maps to a skill that generates the protocol schema:

| Agent | Skill | Schema Output |
|-------|-------|---------------|
| `api-architect` | `generate-openapi` | OpenAPI 3.1 YAML in `openapi/` |
| `realtime-engineer` | `generate-sse` | SSE event schemas in `sse/` |
| `realtime-engineer` | `generate-websocket` | WebSocket message schemas in `websocket/` |
| `grpc-engineer` | `generate-grpc` | Protobuf `.proto` files in `proto/` |
| `graphql-architect` | `generate-graphql` | GraphQL SDL in `graphql/` |
| `event-engineer` | `generate-event-schema` | AsyncAPI / Avro schemas in `events/` |
| `integration-engineer` | `generate-webhook` | Webhook payload schemas in `webhook/` |
| `integration-engineer` | `generate-mqtt` | MQTT topic/payload schemas in `mqtt/` |
| `trpc-engineer` | `generate-trpc` | tRPC router + Zod schemas in `trpc/` |
