---
name: Review Schemas
description: "Run cross-protocol consistency checks on all schemas in the current workspace."
on:
  slash_command:
    name: review-schemas
tools:
  github:
    toolsets: [default]
---

# Review Schemas Workflow

Run cross-protocol consistency checks on all schemas in the current workspace and produce a structured review report.

## Example Invocation

```
/review-schemas
/review-schemas depth=standard
/review-schemas depth=lightweight
```

---

## Phase 1 — Discovery

Scan the workspace for schema files across all 9 protocol directories. The `SchemaReviewer` class (`src/uptempo/reviewer/checker.py`) maps each protocol to its expected directory:

| Protocol | Directory |
|----------|-----------|
| REST | `openapi/` |
| SSE | `sse/` |
| WebSocket | `websocket/` |
| gRPC | `proto/` |
| GraphQL | `graphql/` |
| Kafka / RabbitMQ / NATS | `events/` |
| Webhook | `webhook/` |
| MQTT | `mqtt/` |
| tRPC | `trpc/` |

For each directory that exists, mark the protocol as **covered**. Missing directories are recorded in the `skipped[]` list with the reason `"directory '<name>' not found in workspace"`.

The output of this phase is a `ProtocolCoverage` model (`src/uptempo/reviewer/models.py`) — a set of 9 boolean flags indicating which protocols have schemas present.

---

## Phase 2 — Individual Review

Check each discovered protocol's schemas for spec compliance using the following checks:

### Naming Convention Check (`check_naming_conventions`)

Validates convention per protocol family:

| Convention | Protocols |
|------------|-----------|
| **camelCase** | REST (OpenAPI), SSE, GraphQL, Webhook, MQTT |
| **snake_case** | gRPC (Protobuf) |
| **PascalCase** | tRPC (TypeScript/Zod) |
| **camelCase** (topic names: kebab-case) | Kafka/Events |

Each violation produces a `Finding` with:
- `verdict`: WARNING or FAIL depending on severity
- `category`: `naming_convention`
- `protocols`: The affected protocol(s)
- `location`: File path and line/field reference
- `fix`: Suggested corrected name

### Format & Lint Check

Validate each schema file against its format specification:
- OpenAPI files → valid YAML with required `openapi`, `info`, `paths` keys
- Proto files → valid `.proto` syntax with `syntax`, `package`, `service` declarations
- GraphQL files → valid SDL with `type Query` root
- tRPC files → valid TypeScript with Zod schema imports

---

## Phase 3 — Cross-Protocol Review

Run checks that span multiple protocols to ensure consistency across the entire schema surface.

### Cross-Protocol Mapping (`check_cross_protocol_mapping`)

Ensure the same domain concept uses consistent naming and typing everywhere it appears. For example, if a `User` entity exists in the REST OpenAPI schema, the same entity should appear as `User` in GraphQL, `user` (snake_case) in Protobuf, and `User` (PascalCase) in tRPC — all with equivalent field sets.

### Security Coverage (`check_security_coverage`)

Verify that auth schemes are applied consistently:
- If REST defines `bearerAuth`, then gRPC should use metadata-based auth, GraphQL should have directive-based auth, and WebSocket should validate tokens during the handshake.
- Flag any protocol that exposes operations without authentication when sibling protocols protect equivalent operations.

### Error Code Mapping (`check_error_code_mapping`)

Validate that error codes map correctly between protocols:

| HTTP | gRPC | GraphQL | tRPC |
|------|------|---------|------|
| 400 | INVALID_ARGUMENT | BAD_USER_INPUT | BAD_REQUEST |
| 401 | UNAUTHENTICATED | UNAUTHENTICATED | UNAUTHORIZED |
| 403 | PERMISSION_DENIED | FORBIDDEN | FORBIDDEN |
| 404 | NOT_FOUND | NOT_FOUND | NOT_FOUND |
| 409 | ALREADY_EXISTS | CONFLICT | CONFLICT |
| 500 | INTERNAL | INTERNAL_SERVER_ERROR | INTERNAL_SERVER_ERROR |

### Backward Compatibility (`check_backward_compatibility`)

If previous schema versions exist in the workspace, detect breaking changes:
- Removed fields or endpoints
- Changed field types (e.g., `string` → `integer`)
- Tightened validation (e.g., optional → required)
- Removed enum values

---

## Phase 4 — Report

Generate a structured `ReviewReport` (`src/uptempo/reviewer/models.py`) containing:

```
ReviewReport:
  review_status: "passed" | "needs_revision" | "failed"
  review_depth: "full" | "standard" | "lightweight"
  summary: "<N> finding(s) across <M> protocol(s)"
  findings[]:
    - verdict: PASS | WARNING | FAIL
      severity: critical | high | medium | low
      category: cross_protocol_mapping | naming_convention | backward_compatibility | security | format_lint
      protocols: [list of affected protocols]
      description: Human-readable explanation
      location: File path or schema reference
      fix: Suggested fix (optional)
  protocol_coverage:
    rest: true/false
    sse: true/false
    websocket: true/false
    grpc: true/false
    graphql: true/false
    kafka: true/false
    webhook: true/false
    mqtt: true/false
    trpc: true/false
  skipped[]:
    - protocol: <name>
      reason: <why it was skipped>
```

### Review Depth Levels

| Depth | Checks Run |
|-------|------------|
| `full` | naming_conventions, cross_protocol_mapping, security_coverage, error_code_mapping, backward_compatibility |
| `standard` | security_coverage, cross_protocol_mapping |
| `lightweight` | naming_conventions only |

Status is determined by findings:
- Any `FAIL` finding → `review_status = "failed"`
- Any `WARNING` finding (no FAILs) → `review_status = "needs_revision"`
- No findings or all `PASS` → `review_status = "passed"`

---

## Phase 5 — Output

Print a summary table followed by detailed findings.

### Summary Table

```
┌────────────┬──────────┬──────────┬───────┐
│ Protocol   │ Coverage │ Findings │ Worst │
├────────────┼──────────┼──────────┼───────┤
│ REST       │ ✅       │ 2        │ WARN  │
│ SSE        │ ✅       │ 0        │ PASS  │
│ WebSocket  │ ❌       │ —        │ —     │
│ gRPC       │ ✅       │ 1        │ FAIL  │
│ GraphQL    │ ✅       │ 0        │ PASS  │
│ Kafka      │ ❌       │ —        │ —     │
│ Webhook    │ ❌       │ —        │ —     │
│ MQTT       │ ❌       │ —        │ —     │
│ tRPC       │ ✅       │ 1        │ WARN  │
├────────────┼──────────┼──────────┼───────┤
│ TOTAL      │ 5/9      │ 4        │ FAIL  │
└────────────┴──────────┴──────────┴───────┘

Review Status: failed
Review Depth: full
```

### Detailed Findings

For each finding, print:

```
[FAIL] (critical) cross_protocol_mapping
  Protocols: rest, grpc
  Location: openapi/users.yaml#/components/schemas/User
  Description: Field "userId" in REST uses string type but gRPC User.user_id uses int64.
  Fix: Align on string type across both protocols or use a shared ID type.

[WARNING] (medium) naming_convention
  Protocols: trpc
  Location: trpc/routers/user.ts:14
  Description: Field "user_name" uses snake_case; tRPC schemas should use PascalCase for types.
  Fix: Rename to "UserName" for type definitions.
```
