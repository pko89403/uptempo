# Protobuf & gRPC Style Reference

## Proto3 Style Guide (Google Official Summary)

- **Files**: `lower_snake_case.proto`, one service per file
- **Messages**: `PascalCase` — e.g., `CreateUserRequest`
- **Fields**: `lower_snake_case` — e.g., `user_name`
- **Enums**: `SCREAMING_SNAKE_CASE` values, `UNSPECIFIED = 0` first
- **Services**: `PascalCase` — e.g., `UserService`
- **RPCs**: `PascalCase` verb-noun — e.g., `GetUser`, `ListOrders`
- **Packages**: `lower.dotted` — e.g., `acme.user.v1`

```protobuf
syntax = "proto3";
package acme.user.v1;

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_SUSPENDED = 2;
}
```

## buf Lint Rule Categories

| Category | Rules | Use Case |
|----------|-------|----------|
| MINIMAL | Basic syntax, no breaking | CI gate minimum |
| DEFAULT | MINIMAL + style + naming | Recommended for teams |
| COMMENTS | Require doc comments on all public types | Public APIs |

```yaml
# buf.yaml
version: v2
lint:
  use:
    - DEFAULT
    - COMMENTS
  except:
    - PACKAGE_VERSION_SUFFIX
```

## Field Numbering Best Practices

| Range | Usage |
|-------|-------|
| 1–15 | Frequently used fields (1-byte tag encoding) |
| 16–2047 | Normal fields (2-byte tag) |
| 19000–19999 | **Reserved** (protobuf internal) |
| 536870912+ | **Reserved** (protobuf internal) |

- Never reuse deleted field numbers — use `reserved`
- Group related fields in contiguous ranges

```protobuf
message User {
  reserved 6, 8 to 10;
  reserved "old_field_name";
}
```

## Backward Compatibility Rules

### ✅ Safe Changes
- Add new fields (with new field numbers)
- Add new enum values
- Add new RPC methods
- Add new services
- Rename fields (wire format uses numbers, not names)

### ❌ Breaking Changes
- Change field number
- Change field type (e.g., `int32` → `string`)
- Remove/reuse field numbers without `reserved`
- Change `repeated` ↔ scalar
- Change service/method names (affects generated code)
- Remove enum values without `reserved`

## Well-Known Types

```protobuf
import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/empty.proto";
import "google/protobuf/any.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/wrappers.proto";
import "google/protobuf/field_mask.proto";
```

| Type | Use Case |
|------|----------|
| `Timestamp` | Absolute point in time (UTC) |
| `Duration` | Elapsed time span |
| `Empty` | No request/response body |
| `Any` | Polymorphic fields (avoid if possible) |
| `Struct` | Arbitrary JSON-like data |
| `FieldMask` | Partial updates (PATCH semantics) |
| `StringValue` etc. | Nullable wrappers for scalars |

## RPC Pattern Selection

| Pattern | Client | Server | Use Case |
|---------|--------|--------|----------|
| Unary | 1 req | 1 res | CRUD, lookups |
| Server streaming | 1 req | N res | Feeds, logs, large result sets |
| Client streaming | N req | 1 res | File upload, batch ingestion |
| Bidirectional | N req | N res | Chat, real-time sync |

```protobuf
service ChatService {
  rpc GetUser (GetUserRequest) returns (User);                    // Unary
  rpc ListEvents (ListEventsRequest) returns (stream Event);      // Server stream
  rpc UploadChunks (stream Chunk) returns (UploadResult);         // Client stream
  rpc Chat (stream ChatMessage) returns (stream ChatMessage);     // Bidi
}
```

## gRPC Status Codes

| Code | Name | HTTP Equiv | When to Use |
|------|------|-----------|-------------|
| 0 | OK | 200 | Success |
| 1 | CANCELLED | 499 | Client cancelled |
| 3 | INVALID_ARGUMENT | 400 | Bad request data |
| 5 | NOT_FOUND | 404 | Resource missing |
| 6 | ALREADY_EXISTS | 409 | Duplicate create |
| 7 | PERMISSION_DENIED | 403 | Authz failure |
| 8 | RESOURCE_EXHAUSTED | 429 | Rate limited |
| 12 | UNIMPLEMENTED | 501 | Method not supported |
| 13 | INTERNAL | 500 | Server bug |
| 14 | UNAVAILABLE | 503 | Transient failure (retry) |
| 16 | UNAUTHENTICATED | 401 | Missing/invalid creds |

Use `google.rpc.Status` with `details` for rich error models.
