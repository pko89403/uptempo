# SSE Protocol Reference

## EventSource API Summary

Server-Sent Events provide a **unidirectional** (server → client) stream over HTTP/1.1+.

```javascript
const es = new EventSource('/events', { withCredentials: true });
es.onmessage = (e) => console.log(e.data);
es.addEventListener('update', (e) => console.log(e.data));
es.onerror = (e) => console.error('Connection error');
es.close(); // client-side disconnect
```

## Event Stream Format

Content-Type: `text/event-stream`  
Character encoding: **UTF-8** (required)

### Field Reference

| Field | Purpose | Example |
|-------|---------|---------|
| `data:` | Payload (multi-line via repeated `data:`) | `data: {"msg":"hi"}` |
| `event:` | Named event type (default: `message`) | `event: update` |
| `id:` | Event ID for reconnection | `id: 42` |
| `retry:` | Reconnect delay in ms | `retry: 3000` |
| `:` | Comment (ignored by client; keep-alive) | `: heartbeat` |

### Complete Event Example

```
id: 12345
event: user.created
data: {"id":"u_abc","name":"Alice"}

id: 12346
event: heartbeat
data:

```

Events are separated by **double newline** (`\n\n`).

## Reconnection with Last-Event-ID

1. Server sends `id:` with each event
2. Connection drops
3. Browser automatically reconnects
4. Browser sends `Last-Event-ID: 12345` header
5. Server resumes from that point

```
// Server reads the header to resume
const lastId = req.headers['last-event-id'];
```

Default reconnect delay: **~3 seconds** (override with `retry:` field).

## Keep-Alive Pattern

Send comment lines to prevent proxy/load-balancer timeouts:

```
: keep-alive

```

Recommended interval: **15–30 seconds** (most proxies timeout at 60s).

## Server Implementation Checklist

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no          # Disable nginx buffering
```

- Disable response buffering at all layers
- Flush after each event (`res.flush()` in Node.js)
- Handle `req.on('close')` to clean up subscriptions

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ 6+ | Full support |
| Firefox | ✅ 6+ | Full support |
| Safari | ✅ 5+ | Full support |
| Edge | ✅ 79+ | Chromium-based only |
| IE | ❌ | Use polyfill (`eventsource` npm) |

## SSE vs WebSocket

| Criteria | SSE | WebSocket |
|----------|-----|-----------|
| Direction | Server → Client | Bidirectional |
| Protocol | HTTP/1.1+ | `ws://` / `wss://` |
| Reconnection | Automatic | Manual |
| Data format | Text only (UTF-8) | Text + Binary |
| HTTP/2 multiplexing | ✅ | ❌ |
| Firewall friendly | ✅ (standard HTTP) | Sometimes blocked |
| Max connections (HTTP/1.1) | 6 per domain | No browser limit |

**Use SSE when:** notifications, feeds, status updates, log streaming  
**Use WebSocket when:** chat, gaming, collaborative editing, binary streams

## Common Pitfalls

- Missing `Cache-Control: no-cache` causes buffered responses
- HTTP/1.1 has **6 connection limit** per domain — use HTTP/2
- `EventSource` does not support custom headers — use fetch + `ReadableStream` for auth tokens
- Always set `id:` to enable reliable reconnection
