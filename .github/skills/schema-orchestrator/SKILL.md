---
name: schema-orchestrator
description: >-
  Orchestrate multi-agent schema generation pipelines from Linear issues.
  META-SKILL — coordinate protocol detection, agent delegation, cross-validation,
  and finalization. Trigger on: orchestrate, generate schemas, schema pipeline,
  Linear issue, multi-protocol, team coordination, harness, autopilot,
  review-only, dry-run, fast, agent delegation, cross-validation, protocol
  detection, schema generation workflow.
---

# schema-orchestrator

Coordinate the end-to-end schema generation pipeline: analyze a Linear issue,
detect required protocols, delegate to specialized agents in parallel, run
cross-validation via schema-reviewer, and finalize output. Never generate
schemas directly — delegate, verify, and orchestrate.

## When to Use

Invoke this skill when:
- A new Linear issue arrives for schema generation
- Multiple protocols must be generated from a single issue
- Existing workspace schemas need cross-validation (`review-only`)
- Issue analysis is needed without generation (`dry-run`)
- Full autonomous pipeline execution is requested (`autopilot`)

## Input

| Field | Source | Required |
|-------|--------|----------|
| `issue.identifier` | Linear issue ID (e.g., `UPT-100`) | ✅ |
| `issue.title` | Linear issue title | ✅ |
| `issue.description` | Full issue body | ✅ |
| `issue.labels` | Labels array — used for protocol + priority detection | ✅ |
| `workspace` | Absolute path to workspace root | ✅ |

## Output

```
{workspace}/
  00_analysis.md                  # Phase 1 — protocol detection report
  openapi/                        # api-architect output
  proto/                          # grpc-engineer output
  graphql/                        # graphql-architect output
  events/                         # event-engineer output
  websocket/                      # realtime-engineer output (WS)
  sse/                            # realtime-engineer output (SSE)
  webhook/                        # integration-engineer output (Webhook)
  mqtt/                           # integration-engineer output (MQTT)
  trpc/                           # trpc-engineer output
  _review/
    review_report.md              # Phase 3 — cross-validation report
  _summary.md                     # Phase 4 — final pipeline summary
```

## Magic Keywords

Detect these keywords in `issue.title` or `issue.description`:

| Keyword | Behavior | Phases Affected |
|---------|----------|----------------|
| `autopilot` | Skip analysis confirmation, execute all phases non-stop | All |
| `review-only` | Skip delegation (Phase 2), validate existing schemas | Phase 3–4 only |
| `dry-run` | Analyze and report — do not generate or validate | Phase 1 only |
| `fast` | Increase concurrency to 6, disable retries | Phase 2 |

Parse keywords early — before Phase 1 routing decisions.

## Procedure

### Phase 0 — Initialization

1. Create workspace directory if it does not exist.
2. Scan issue title + description + labels for magic keywords.
3. Record pipeline start time for SLA tracking.
4. Initialize pipeline state:

```markdown
# Pipeline State
- issue: {issue.identifier}
- mode: {autopilot|review-only|dry-run|fast|standard}
- started: {ISO8601}
- phase: 0-init
```

### Phase 1 — Issue Analysis

Detect required protocols by matching keywords and labels against the
agent routing table:

| Agent | Protocols | Trigger Keywords |
|-------|-----------|-----------------|
| api-architect | REST / OpenAPI 3.1 | REST, CRUD, API, endpoint, resource, HTTP |
| realtime-engineer | SSE | SSE, streaming, real-time push, unidirectional, server-sent |
| realtime-engineer | WebSocket | WebSocket, bidirectional, chat, live, ws:// |
| grpc-engineer | gRPC / Protobuf | gRPC, Protobuf, RPC, internal service, buf, proto |
| graphql-architect | GraphQL SDL | GraphQL, query, mutation, SDL, Relay, federation |
| event-engineer | Kafka/RabbitMQ/NATS | Kafka, RabbitMQ, NATS, event, queue, pub/sub, async, domain event |
| integration-engineer | Webhook | Webhook, callback, external, SaaS integration |
| integration-engineer | MQTT | MQTT, IoT, device, telemetry, sensor |
| trpc-engineer | tRPC / Zod | tRPC, Zod, TypeScript API, type-safe, fullstack |

**Matching rules:**
- Case-insensitive keyword search in title + description
- Label names match directly (e.g., label `kafka` → event-engineer)
- A single issue may trigger multiple agents
- If no keywords match → default to `api-architect` (REST), set `x-default-protocol: true`
- Assign confidence: `high` (exact keyword) / `medium` (contextual inference)

Write analysis to `{workspace}/00_analysis.md`:

```markdown
# Issue Analysis: {issue.identifier}

## Detected Protocols

| Protocol | Agent | Confidence | Trigger |
|----------|-------|-----------|---------|
| REST/OpenAPI | api-architect | high | "CRUD endpoints" in description |
| Kafka Events | event-engineer | medium | "order events" label |

## Magic Keywords
- autopilot: false
- review-only: false
- dry-run: false
- fast: false

## Ambiguities
- None detected

## Delegation Plan
- Agents to invoke: [api-architect, event-engineer]
- Estimated concurrency: 2
```

If `dry-run` → stop here, output analysis, mark pipeline complete.

### Phase 2 — Agent Delegation

1. Build delegation list from Phase 1 analysis.
2. Launch agents in parallel using the `task` tool with `mode: "background"`:
   - Maximum concurrency: **4** (standard) or **6** (`fast` mode)
   - Each agent receives: issue context + workspace path + protocol-specific instructions
3. Wait for all background agents to complete.
4. Collect results:

```
Agent Results:
  api-architect    → ✅ openapi/orders.yaml (3 paths, 12 schemas)
  event-engineer   → ✅ events/orders-events.yaml (4 channels, 4 messages)
  grpc-engineer    → ❌ timeout after 300s
```

5. Handle failures:
   - **Single agent failure**: Retry once with error context injected.
   - **Retry failure**: Skip protocol, document in report, continue pipeline.
   - **Majority failure (>50% agents failed)**: Halt pipeline, escalate to user.

```
Retry:
  grpc-engineer (attempt 2) → inject error: "timeout after 300s"
  grpc-engineer (attempt 2) → ✅ proto/orders.proto
```

If `review-only` → skip this phase, proceed to Phase 3 with existing files.

### Phase 3 — Cross-Validation

1. Invoke `schema-reviewer` agent with all generated schema files.
2. schema-reviewer returns a structured report:

```json
{
  "verdict": "WARNING",
  "findings": [
    {
      "severity": "FAIL",
      "category": "naming-consistency",
      "file": "openapi/orders.yaml",
      "message": "Entity 'Order' uses snake_case but events use camelCase",
      "suggestion": "Standardize to camelCase across all schemas"
    },
    {
      "severity": "WARNING",
      "category": "missing-cross-reference",
      "file": "events/orders-events.yaml",
      "message": "OrderCreated event payload lacks orderId field present in REST schema"
    }
  ]
}
```

3. For each `FAIL` finding:
   a. Identify the responsible agent from the file path.
   b. Re-invoke that agent with the fix instruction (max **1 retry**).
   c. Re-validate the fixed file.
   d. If still `FAIL` after retry → downgrade to `WARNING`, proceed.

4. Write review report to `{workspace}/_review/review_report.md`:

```markdown
# Schema Review Report: {issue.identifier}

## Overall Verdict: PASS ✅ | WARNING ⚠️ | FAIL ❌

## Findings

### FAIL → Fixed
- [naming-consistency] openapi/orders.yaml — Fixed by api-architect (retry 1)

### WARNING (accepted)
- [missing-cross-reference] events/orders-events.yaml — Non-blocking

## Validation Summary
| Schema | Tool | Result |
|--------|------|--------|
| openapi/orders.yaml | Spectral | PASS |
| events/orders-events.yaml | asyncapi validate | PASS |
| proto/orders.proto | buf lint | PASS |
```

### Phase 4 — Finalization

1. Verify all expected protocol directories contain output files.
2. Preserve `{workspace}/_review/review_report.md` as audit trail.
3. Generate pipeline summary at `{workspace}/_summary.md`:

```markdown
# Pipeline Summary: {issue.identifier}

## Status: Complete ✅

## Generated Schemas
| Protocol | Agent | Files | Status |
|----------|-------|-------|--------|
| REST/OpenAPI | api-architect | openapi/orders.yaml | ✅ |
| Kafka Events | event-engineer | events/orders-events.yaml | ✅ |
| gRPC | grpc-engineer | proto/orders.proto | ✅ (retry) |

## Review Verdict: WARNING ⚠️
- 0 FAIL, 1 WARNING, 5 PASS

## Timeline
- Started: {ISO8601}
- Phase 1 (Analysis): 2s
- Phase 2 (Delegation): 45s
- Phase 3 (Validation): 12s
- Phase 4 (Finalization): 1s
- Total: 60s

## Linear Issue Update
- Status: In Progress → Done
- Comment posted with schema summary
```

4. Post summary comment to Linear issue:
   - List all generated schemas with file paths
   - Include review verdict
   - Note any skipped protocols with reason
5. Transition Linear issue status: `In Progress` → `Done`.
6. If any agents failed permanently: transition to `Done` with warning comment
   (not `Cancelled` unless majority failure).

## Workspace Directory Contract

```
{workspace}/
  00_analysis.md          # Always created (Phase 1)
  {protocol}/             # One per delegated agent (Phase 2)
    *.yaml|.proto|.graphql|.ts  # Schema files
    schemas/              # Standalone payload schemas (optional)
  _review/
    review_report.md      # Always created (Phase 3)
  _summary.md             # Always created (Phase 4)
```

File-based inter-agent communication:
- Agents write to their own protocol directory only
- schema-reviewer reads all protocol directories (read-only)
- Orchestrator reads/writes `00_analysis.md`, `_review/`, `_summary.md`
- No agent modifies another agent's output directory

## Concurrency Model

```
Standard mode (default):
  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
  │ Agent 1 │ │ Agent 2 │ │ Agent 3 │ │ Agent 4 │  (max 4)
  └─────────┘ └─────────┘ └─────────┘ └─────────┘
       ↓           ↓           ↓           ↓
  ═══════════════ barrier ═══════════════════
       ↓
  ┌───────────────┐
  │schema-reviewer│  (sequential — reads all outputs)
  └───────────────┘

Fast mode (keyword: fast):
  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐
  │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │  (max 6, no retries)
  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘
```

Timeout per agent: **300 seconds** (5 minutes).
On timeout: treat as failure, follow retry strategy.

## Error Handling

| Scenario | Strategy |
|----------|----------|
| No protocol detected | Default to REST via api-architect, mark `x-default-protocol: true` |
| Single agent failure | Retry once with error context. If retry fails, skip + document |
| Majority failure (>50%) | Halt pipeline, post failure details to Linear, await user decision |
| Cross-validation FAIL | Re-invoke responsible agent (1 retry). Downgrade to WARNING if unresolved |
| Agent timeout (>300s) | Treat as failure, follow retry strategy |
| Conflicting schemas | Flag in review, request reconciliation from both agents |
| Workspace already has files | Check `review-only` keyword. If not set, warn and proceed (overwrite) |
| Linear API unavailable | Continue pipeline, skip issue update, log warning |

## Escalation Policy

```
Agent failure count:
  0     → Phase 4 (finalize normally)
  1     → Phase 4 (finalize with warning)
  2-49% → Phase 4 (finalize with degraded status)
  ≥50%  → HALT — escalate to user
```

Escalation message format:
```markdown
⚠️ Pipeline halted for {issue.identifier}

{N}/{total} agents failed after retry:
- {agent1}: {error_summary}
- {agent2}: {error_summary}

Successful schemas preserved in {workspace}/.
Action required: resolve failures manually or re-run with `fast` keyword.
```

## Test Scenarios

### Happy Path
```
Issue: "Order Management API — REST + Kafka events"
Phase 1: Detect REST (high), Kafka (high)
Phase 2: api-architect ✅, event-engineer ✅
Phase 3: schema-reviewer → PASS
Phase 4: Commit + Linear → Done
```

### Retry Path
```
Issue: "Real-time Dashboard — SSE + GraphQL"
Phase 1: Detect SSE (high), GraphQL (high)
Phase 2: realtime-engineer ✅, graphql-architect ❌ (timeout)
Phase 2b: graphql-architect retry ✅
Phase 3: schema-reviewer → WARNING
Phase 4: Commit with warning + Linear → Done
```

### Escalation Path
```
Issue: "IoT Fleet — MQTT + gRPC + Kafka"
Phase 1: Detect MQTT (high), gRPC (high), Kafka (high)
Phase 2: integration-engineer ✅, grpc-engineer ❌, event-engineer ❌
Phase 2b: grpc-engineer retry ❌, event-engineer retry ✅
Result: 1/3 failed → below 50%, finalize with degraded status
```

### Dry-Run
```
Issue: "Payment Gateway — dry-run"
Phase 1: Detect REST (high), Webhook (high) → output 00_analysis.md
Pipeline complete — no schemas generated
```

## Collaboration Hooks

- **All protocol agents**: Delegate via `task` tool `mode: "background"`
- **schema-reviewer**: Invoke in Phase 3 for cross-protocol consistency audit
- **Linear API**: Read issue context (Phase 1), post summary + transition status (Phase 4)
