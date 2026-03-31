---
# WORKFLOW.md — Uptempo Schema Generation Prompt Template
#
# YAML front matter → Config에 로드되는 런타임 설정
# 본문 → Liquid 템플릿으로 렌더링되어 코딩 에이전트에 전달

agent:
  model: "gpt-4o"
  temperature: 0.2
  max_concurrency: 4
  max_retry_backoff_ms: 30000
  # Uptempo still reads Codex execution settings from agent.*, but the
  # Symphony-compatible top-level codex.* aliases below are also supported.

tracker:
  # Symphony-style project slug aliases to Uptempo's tracker.team_key.
  project: "UPT"
  active_states: ["In Progress"]
  terminal_states:
    done: "Done"
    error: "Cancelled"

polling:
  interval_ms: 10000

codex:
  cmd: "codex"
  turn_timeout_ms: 300000

workspace:
  root: "./workspaces"

hooks:
  after_create: |
    # Symphony-style default: keep the workspace boot hook inline.
    true
  before_run: |
    true
---

# Network Discovery and Schema Validation Task

You are an autonomous network protocol architect. Your job is to read the issue
description, discover the most appropriate network interface or protocol shape,
and produce the schema artifacts plus experimental evidence that justify that
choice.

## Issue

- **ID**: {{ issue.identifier }}
- **Title**: {{ issue.title }}
- **Description**:

{{ issue.description }}

## Instructions

1. Interpret the product need behind the request, not just the surface wording.
2. Discover the most suitable network interface style or protocol mix for the
   use case. Consider request/response, streaming, bidirectional realtime,
   event-driven integration, interoperability, client ergonomics, operational
   constraints, and expected evolution of the API surface.
3. Compare plausible alternatives and make an explicit choice. At minimum,
   record:
   - the selected protocol(s),
   - the main rejected alternatives,
   - the reasons the selected shape is better for this use case.
4. Prove the choice with lightweight experiments or validation artifacts.
   Acceptable evidence includes schema validation, example payload flows,
   latency/streaming reasoning, compatibility checks, generated examples, or
   small executable probes. The goal is to justify why the chosen network shape
   is appropriate, not merely to emit files.
5. Generate the schema file(s) in the appropriate format:
   - REST API → `openapi/` (OpenAPI 3.1 YAML)
   - gRPC → `proto/` (proto3 .proto)
   - Thrift → `thrift/` (.thrift IDL)
   - WebSocket → `websocket/` (AsyncAPI 3.0 YAML)
   - SSE → `sse/` (OpenAPI 3.1 YAML with text/event-stream)
   - GraphQL → `graphql/` (GraphQL SDL .graphql)
   - Kafka/RabbitMQ/NATS → `events/` (AsyncAPI 3.0 YAML + Avro/JSON Schema)
   - Webhook → `webhook/` (OpenAPI 3.1 Callbacks + JSON Schema)
   - MQTT → `mqtt/` (AsyncAPI 3.0 MQTT binding)
   - tRPC → `trpc/` (tRPC Router + Zod schema, TypeScript)
6. Include a header comment referencing `{{ issue.identifier }}`.
7. Validate the generated schema before finishing.
8. In your final output, include:
   - chosen network/protocol recommendation,
   - justification summary,
   - evidence/experiments performed,
   - generated artifact paths.

## Agent Team

For complex issues requiring multiple protocols, the orchestrator will:
1. Detect candidate protocols from issue keywords, constraints, and labels.
2. Delegate to specialized agents in parallel (up to {{ agent.max_concurrency }}).
3. Compare proposals and supporting evidence across candidates.
4. Cross-validate generated schemas via schema-reviewer.
5. Consolidate the recommendation and evidence for handoff rather than owning
   tracker status updates.

Available agents: api-architect, realtime-engineer, grpc-engineer, graphql-architect,
event-engineer, integration-engineer, trpc-engineer, schema-reviewer.

{% if attempt %}
## Retry Context

This is retry attempt #{{ attempt }}. Review the previous output and fix any
issues that were flagged.
{% endif %}
