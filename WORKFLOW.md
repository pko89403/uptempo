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

tracker:
  team_key: "UPT"
  poll_interval_ms: 10000
  eligible_states: ["In Progress"]
  done_state: "Done"
  error_state: "Cancelled"

workspace:
  root: "./workspaces"

hooks:
  after_create: |
    # Symphony-style default: keep the workspace boot hook inline.
    true
  before_run: |
    true
---

# Schema Generation Task

You are a network schema generator. Your job is to read the issue description
and produce the requested schema files.

## Issue

- **ID**: {{ issue.identifier }}
- **Title**: {{ issue.title }}
- **Description**:

{{ issue.description }}

## Instructions

1. Analyze the issue description to determine the required schema type(s).
2. Generate the schema file(s) in the appropriate format:
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
3. Include a header comment referencing `{{ issue.identifier }}`.
4. Validate the generated schema before committing.

## Agent Team

For complex issues requiring multiple protocols, the orchestrator will:
1. Detect required protocols from issue keywords and labels.
2. Delegate to specialized agents in parallel (up to {{ agent.max_concurrency }}).
3. Cross-validate generated schemas via schema-reviewer.
4. Consolidate results and update issue status.

Available agents: api-architect, realtime-engineer, grpc-engineer, graphql-architect,
event-engineer, integration-engineer, trpc-engineer, schema-reviewer.

{% if attempt %}
## Retry Context

This is retry attempt #{{ attempt }}. Review the previous output and fix any
issues that were flagged.
{% endif %}
