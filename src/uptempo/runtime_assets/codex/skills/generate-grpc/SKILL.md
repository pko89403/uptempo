---
name: generate-grpc
description: Generate proto3 service contracts for gRPC-style interfaces in Uptempo.
---

# generate-grpc

Use for RPC, internal service-to-service APIs, strongly typed contracts, or streaming gRPC flows.

## Output

- write files under `proto/`
- include issue context in header comments
- keep package and naming choices consistent

## Validation

- run `buf lint` when available
- record any interoperability assumptions in the workpad
