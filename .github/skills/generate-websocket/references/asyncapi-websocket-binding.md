# AsyncAPI WebSocket Binding Reference

## AsyncAPI 3.0 WebSocket Channel Binding

```yaml
asyncapi: 3.0.0
info:
  title: Chat Service
  version: 1.0.0

servers:
  production:
    host: ws.example.com
    protocol: ws
    security:
      - $ref: '#/components/securitySchemes/bearer'

channels:
  chat:
    address: /ws/chat
    bindings:
      ws:
        method: GET
        query:
          type: object
          properties:
            room:
              type: string
          required: [room]
        headers:
          type: object
          properties:
            Authorization:
              type: string
    messages:
      chatMessage:
        $ref: '#/components/messages/ChatMessage'
      typing:
        $ref: '#/components/messages/TypingIndicator'

operations:
  sendMessage:
    action: send
    channel:
      $ref: '#/channels/chat'
    messages:
      - $ref: '#/channels/chat/messages/chatMessage'
  receiveMessage:
    action: receive
    channel:
      $ref: '#/channels/chat'
    messages:
      - $ref: '#/channels/chat/messages/chatMessage'
      - $ref: '#/channels/chat/messages/typing'

components:
  messages:
    ChatMessage:
      payload:
        type: object
        properties:
          type: { const: "message" }
          content: { type: string }
          timestamp: { type: string, format: date-time }
        required: [type, content]
    TypingIndicator:
      payload:
        type: object
        properties:
          type: { const: "typing" }
          userId: { type: string }
```

## Connection Lifecycle

```
Client                          Server
  |--- HTTP GET /ws (Upgrade) --->|     1. Opening handshake
  |<-- 101 Switching Protocols ---|     2. Connection established
  |<========= Frames ==========>|     3. Data exchange
  |--- Close frame (1000) ------>|     4. Client initiates close
  |<-- Close frame (1000) ------|     5. Server acknowledges
  |--- TCP FIN ----------------->|     6. Connection closed
```

### Close Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 1000 | Normal closure | Clean disconnect |
| 1001 | Going away | Server shutdown / page nav |
| 1008 | Policy violation | Auth failure |
| 1011 | Unexpected condition | Server error |
| 1012 | Service restart | Server restarting |

## Heartbeat / Ping-Pong Pattern

```
Server sends:  Ping frame (opcode 0x9)
Client replies: Pong frame (opcode 0xA)  ← automatic in browsers
```

- Send ping every **30 seconds**
- If no pong within **10 seconds**, consider connection dead
- Application-level heartbeat alternative:

```json
{"type": "ping", "ts": 1700000000}
{"type": "pong", "ts": 1700000000}
```

## Subprotocol Negotiation

```
// Client requests subprotocols
new WebSocket('wss://example.com/ws', ['graphql-ws', 'json']);

// Server selects one in response header
Sec-WebSocket-Protocol: graphql-ws
```

Common subprotocols:
- `graphql-ws` — GraphQL over WebSocket
- `wamp.2.json` — WAMP v2
- `mqtt` — MQTT over WebSocket
- `ocpp2.0.1` — EV charging protocol

## Message Framing

| Type | Opcode | Use Case |
|------|--------|----------|
| Text | 0x1 | JSON, XML, plain text |
| Binary | 0x2 | Protobuf, CBOR, images |
| Ping | 0x9 | Keep-alive |
| Pong | 0xA | Ping response |
| Close | 0x8 | Connection teardown |

### Message Envelope Pattern

```json
{
  "type": "chat.message",
  "id": "msg_abc123",
  "payload": { "text": "Hello", "room": "general" },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Use `type` field for routing; `id` for idempotency and ack tracking.

## Best Practices

- Always use `wss://` (TLS) in production
- Implement exponential backoff for reconnection (1s, 2s, 4s… max 30s)
- Add jitter to prevent thundering herd on reconnect
- Set `maxPayload` limit server-side (e.g., 1MB)
- Authenticate on handshake, not per-message
- Use message compression (`permessage-deflate` extension) for large payloads
