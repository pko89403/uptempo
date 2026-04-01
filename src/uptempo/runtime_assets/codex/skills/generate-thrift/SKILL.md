---
name: generate-thrift
description: Generate Thrift IDL contracts for Uptempo compatibility or legacy integration tasks.
---

# generate-thrift

Use when interoperability or existing platform constraints point to Thrift.

## Output

- write IDL files under `thrift/`
- document service boundaries and serialization assumptions
- record why Thrift was selected over gRPC or REST
