---
description: "Enforce proto3 style guide and backward compatibility for .proto files"
paths:
  - "**/*.proto"
priority: 8
---

# Protocol Buffer Rules

## Syntax & Packaging

- Always declare `syntax = "proto3";` at the top of every file.
- Set package names to lowercase dot-separated strings matching the directory structure (e.g., `uptempo.schemas.v1`).
- Add `option go_package` and `option java_package` for cross-language support.
- Keep import paths relative to the buf module root.

## Naming Conventions

- Name services in PascalCase with a `Service` suffix (e.g., `UserService`).
- Name RPC methods in PascalCase, verb-first (e.g., `GetUser`, `ListOrders`, `CreatePayment`).
- Name messages in PascalCase (e.g., `UserRequest`, `OrderResponse`).
- Name fields in snake_case (e.g., `user_id`, `created_at`).
- Name enum values in UPPER_SNAKE_CASE with the enum name as prefix (e.g., `STATUS_ACTIVE`, `STATUS_INACTIVE`).
- Set the first enum value to zero with an `_UNSPECIFIED` suffix (e.g., `STATUS_UNSPECIFIED = 0`).

## Backward Compatibility

- Never change field numbers in existing messages.
- Never remove or rename fields — deprecate them with the `reserved` keyword.

## Type & Structure Guidelines

- Use `google.protobuf.Timestamp` for time fields, not int64 or string.
- Define one service per file; messages may be co-located or separated.
