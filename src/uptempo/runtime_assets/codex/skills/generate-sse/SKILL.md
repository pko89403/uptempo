---
name: generate-sse
description: Generate Server-Sent Events interface definitions for Uptempo tasks.
---

# generate-sse

Use when the use case is server-to-client streaming without bidirectional messaging.

## Output

- write specs under `sse/`
- model `text/event-stream` behavior explicitly
- document reconnection or event ordering assumptions when relevant
