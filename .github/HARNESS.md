# Uptempo Harness — 개발 도구 가이드

> ⚠️ **이 문서는 Uptempo 제품이 아닌 "개발 하네스"를 설명합니다.**
> 제품 코드(`src/uptempo/`)의 아키텍처는 → [`copilot-instructions.md`](copilot-instructions.md)

## 목차 — 필요한 것부터 찾아가세요

| 뭘 하고 싶은가? | 섹션 |
|----------------|------|
| 처음 시작하기 | [Quick Start](#quick-start) |
| 어떤 에이전트가 있는지 보기 | [Agent Roster](#agent-roster) |
| 특정 프로토콜 스키마 생성하기 | [Protocol → Output Mapping](#protocol--output-mapping) |
| 스킬 목록 보기 | [Skill Inventory](#skill-inventory) |
| 전체 파이프라인 이해하기 | [Workflow Phases](#workflow-phases) |
| 디렉토리 구조 이해하기 | [Directory Structure](#directory-structure) |
| 훅/자동화 설정 보기 | [Hooks](#hooks) |
| 코딩 규칙 확인하기 | [Rules](#rules-path-specific) |
| Copilot CLI 적응 방법 | [Copilot CLI Adaptation Notes](#copilot-cli-adaptation-notes) |

---

## Product vs. Harness 경계

```
┌─ Product (src/uptempo/) ──────────────┐   ┌─ Harness (.github/) ─────────────┐
│                                        │   │                                   │
│  schema/      10개 스키마 제너레이터     │   │  agents/     9개 에이전트 페르소나  │
│  config/      설정 로딩                 │   │  skills/     10개 스킬 프롬프트    │
│  tracker/     Linear API 연동           │   │  hooks/      라이프사이클 자동화   │
│  workspace/   워크스페이스 관리          │   │  workflows/  슬래시 커맨드 파이프라인│
│  orchestrator/ 폴 루프 + 상태 머신      │   │  rules/      경로별 코딩 규칙     │
│  agent/       Codex 에이전트 실행       │   │  harness/    리뷰어 + 프로토콜 라우팅│
│                                        │   │                                   │
│  → 사용자에게 배포되는 코드              │   │  → Copilot CLI로 개발할 때 사용    │
└────────────────────────────────────────┘   └───────────────────────────────────┘
```

## Architecture

**Pattern**: Expert Pool + Producer-Reviewer

```
                           ┌─────────────────────┐
                           │    orchestrator      │
                           │  (phase detection,   │
                           │   agent routing)     │
                           └──────────┬──────────┘
                                      │ delegates
            ┌─────────────────────────┼─────────────────────────┐
            │              │          │          │               │
     ┌──────▼──────┐ ┌────▼────┐ ┌───▼───┐ ┌───▼────┐ ┌───────▼───────┐
     │api-architect│ │realtime │ │ grpc  │ │graphql │ │ integration   │
     │  (OpenAPI)  │ │engineer │ │engineer│ │architect│ │  engineer     │
     │             │ │(SSE+WS) │ │(Proto)│ │ (SDL)  │ │(Webhook+MQTT) │
     └──────┬──────┘ └────┬────┘ └───┬───┘ └───┬────┘ └───────┬───────┘
            │              │         │          │               │
            │         ┌────▼────┐    │          │               │
            │         │  trpc   │    │          │               │
            │         │engineer │    │          │               │
            │         │  (Zod)  │    │          │               │
            │         └────┬────┘    │          │               │
            │              │         │          │               │
            └──────────────┴─────────┴──────────┴───────────────┘
                                      │ all outputs
                           ┌──────────▼──────────┐
                           │   schema-reviewer    │
                           │  (cross-protocol QA) │
                           │  READ-ONLY auditor   │
                           └──────────────────────┘
```

## Quick Start

Invoke the orchestrator from the Copilot CLI:

```
@orchestrator Generate schemas for issue UPT-42
```

The orchestrator will:
1. Analyze the issue description for protocol keywords
2. Detect required protocols (e.g., REST + gRPC + WebSocket)
3. Delegate to the matching agents in parallel via `task` tool
4. Collect outputs and run `schema-reviewer` for cross-validation
5. Produce a unified report and commit the schemas

You can also invoke individual agents directly:

```
@api-architect Design a REST API for user management
@grpc-engineer Create proto3 service definitions for auth
@realtime-engineer Design SSE endpoints for live notifications
```

## Agent Roster

| # | Agent | Protocols | Skill(s) | Description |
|---|-------|-----------|----------|-------------|
| 1 | `orchestrator` | All (meta) | `schema-orchestrator` | Entry point — detects phase, routes to agents, synthesizes results |
| 2 | `api-architect` | REST / OpenAPI 3.1 | `generate-openapi` | CRUD endpoints, DTOs, error envelopes, auth schemes, versioning |
| 3 | `realtime-engineer` | SSE + WebSocket | `generate-sse`, `generate-websocket` | Event streams, bidirectional channels, connection lifecycle |
| 4 | `grpc-engineer` | gRPC / Protobuf | `generate-grpc` | Proto3 IDL, streaming RPCs, buf lint, gRPC-Gateway transcoding |
| 5 | `graphql-architect` | GraphQL SDL | `generate-graphql` | Type system, Relay connections, Federation, subscriptions |
| 6 | `event-engineer` | Kafka / RabbitMQ / NATS | `generate-event-schema` | AsyncAPI 3.0, broker bindings, CloudEvents, schema evolution |
| 7 | `integration-engineer` | Webhook + MQTT | `generate-webhook`, `generate-mqtt` | SaaS callbacks, HMAC signatures, IoT topic hierarchies |
| 8 | `trpc-engineer` | tRPC / Zod | `generate-trpc` | Type-safe routers, Zod validation, middleware chains |
| 9 | `schema-reviewer` | All (read-only) | *(none)* | Cross-protocol audit, naming checks, breaking change detection |

## Skill Inventory

| # | Skill | Paired Agent | Output Format | Validation |
|---|-------|--------------|---------------|------------|
| 1 | `schema-orchestrator` | orchestrator | Pipeline coordination | N/A (meta-skill) |
| 2 | `generate-openapi` | api-architect | OpenAPI 3.1 YAML | Spectral |
| 3 | `generate-sse` | realtime-engineer | OpenAPI 3.1 YAML | Spectral |
| 4 | `generate-websocket` | realtime-engineer | AsyncAPI 3.0 YAML | asyncapi validate |
| 5 | `generate-grpc` | grpc-engineer | proto3 `.proto` | buf lint |
| 6 | `generate-graphql` | graphql-architect | GraphQL SDL `.graphql` | graphql-js validate |
| 7 | `generate-event-schema` | event-engineer | AsyncAPI 3.0 YAML + Avro | asyncapi validate |
| 8 | `generate-webhook` | integration-engineer | OpenAPI 3.1 YAML | Spectral |
| 9 | `generate-mqtt` | integration-engineer | AsyncAPI 3.0 YAML | asyncapi validate |
| 10 | `generate-trpc` | trpc-engineer | TypeScript (`.ts`) | tsc --noEmit |

## Hooks

Hooks fire autonomously on lifecycle events — no manual invocation needed.

| Hook | Event | Action | Exit Code |
|------|-------|--------|-----------|
| `secrets-guard` | PreToolUse | Scan for API keys, private keys, passwords | 0 = clean, **2 = BLOCK** |
| `schema-lint` | PostToolUse | Validate `.py`, `.proto`, `.yaml`, `.graphql` | 0 = pass, 1 = fail |
| `auto-format` | PostToolUse | Run black/isort/buf/prettier on changed files | Always 0 (best-effort) |
| `session-context` | sessionStart | Print worktree, branch, protocol coverage | Always 0 |

**Event flow**: `sessionStart` → user works → `PreToolUse` (guard) → tool runs →
`PostToolUse` (lint + format).

## Workflows (Slash Commands)

| Command | Workflow | Description |
|---------|----------|-------------|
| `/generate-schema` | `generate-schema.md` | Full pipeline: issue → detect → agents → review → commit |
| `/review-schemas` | `review-schemas.md` | Cross-protocol consistency audit on workspace schemas |
| `/detect-protocol` | `detect-protocol.md` | Quick analysis: issue text → protocol confidence table |

## Rules (Path-Specific)

Rules auto-load when editing files matching their `paths` globs.

| Rule | Priority | Scope | Focus |
|------|----------|-------|-------|
| `harness-files` | 15 | `.github/{agents,skills,hooks,workflows,rules}/**` | Frontmatter format, naming, progressive disclosure |
| `schema-generators` | 10 | `src/uptempo/schema/**/*.py` | ABC compliance, stateless generators, type hints |
| `proto-files` | 8 | `**/*.proto` | proto3 style guide, backward compatibility, naming |
| `test-files` | 5 | `tests/**/*.py` | pytest patterns, AAA structure, fixtures, coverage |

## Directory Structure

```
.github/
├── copilot-instructions.md          # 제품 아키텍처 (→ src/uptempo/)
├── HARNESS.md                       # ← 이 파일 (개발 하네스 가이드)
│
├── agents/                          # WHO — 에이전트 페르소나 (9개)
│   ├── orchestrator.md
│   ├── api-architect.md
│   ├── realtime-engineer.md
│   ├── grpc-engineer.md
│   ├── graphql-architect.md
│   ├── event-engineer.md
│   ├── integration-engineer.md
│   ├── trpc-engineer.md
│   └── schema-reviewer.md
│
├── skills/                          # HOW — 스킬 절차서 (10개)
│   ├── schema-orchestrator/SKILL.md
│   ├── generate-openapi/SKILL.md
│   ├── generate-sse/SKILL.md
│   ├── generate-websocket/SKILL.md
│   ├── generate-grpc/SKILL.md
│   ├── generate-graphql/SKILL.md
│   ├── generate-event-schema/SKILL.md
│   ├── generate-webhook/SKILL.md
│   ├── generate-mqtt/SKILL.md
│   └── generate-trpc/SKILL.md
│
├── hooks/                           # WHEN — 라이프사이클 자동화
│   ├── hooks.json
│   ├── secrets-guard/
│   ├── schema-lint/
│   ├── auto-format/
│   └── session-context/
│
├── workflows/                       # WHAT — 슬래시 커맨드 파이프라인
│   ├── generate-schema.md
│   ├── review-schemas.md
│   └── detect-protocol.md
│
├── rules/                           # WHERE — 경로별 코딩 규칙
│   ├── schema-generators.md
│   ├── proto-files.md
│   ├── test-files.md
│   └── harness-files.md
│
└── harness/                         # 하네스 전용 코드 + 테스트
    ├── reviewer/                    # 크로스 프로토콜 리뷰 로직
    │   ├── checker.py
    │   └── models.py
    ├── protocol-routing/            # 이슈 → 에이전트 라우팅
    │   └── protocol_detector.py
    └── tests/                       # 하네스 테스트
        ├── test_checker.py
        ├── test_models.py
        └── test_protocol_detector.py
```

### Folder Interaction Model

```
                     ┌──────────┐
                     │  rules/  │ ─── path-matched rules auto-load
                     └────┬─────┘     when editing matching files
                          │
  ┌───────────┐     ┌─────▼─────┐     ┌────────────┐
  │ workflows/│────▶│  agents/  │────▶│  skills/    │
  │ (trigger) │     │  (who)    │     │  (how)      │
  └───────────┘     └─────┬─────┘     └──────┬──────┘
                          │                   │
                     ┌────▼─────┐             │
                     │  hooks/  │◀────────────┘
                     │ (events) │  fires on tool use
                     └──────────┘
```

- **Workflows** trigger agent pipelines (slash commands)
- **Agents** invoke skills to perform concrete work
- **Skills** produce file outputs that trigger hooks
- **Hooks** run autonomously on lifecycle events (lint, format, guard)
- **Rules** auto-load when the agent edits files matching `paths` globs

## Copilot CLI Adaptation Notes

This harness adapts the Claude Code agent/skill pattern for the **GitHub
Copilot CLI** environment. Key differences:

### Agent Files: `.github/agents/` (not `.claude/agents/`)

Each agent `.md` file uses **Copilot CLI frontmatter**:

```yaml
---
name: agent-name              # Matches filename (without .md)
description: 'Pushy description with trigger keywords...'
tools:                         # Skills this agent can invoke
  - skill-name
model: claude-sonnet-4         # LLM model for this agent
---
```

- **`description` is "pushy"** — it contains explicit trigger keywords so the
  Copilot CLI's Progressive Disclosure can match user intent to the right agent.
- **`tools` lists skill names** that the agent may invoke during execution.
- **`model` is required** — currently all agents use `claude-sonnet-4`.

### Skill Files: `.github/skills/` (not `.claude/skills/`)

Each skill lives in a named directory with a `SKILL.md`:

```yaml
---
name: skill-name               # Matches directory name
description: 'Pushy description with trigger keywords...'
---
```

### Inter-Agent Communication

- **No `TeamCreate` / `SendMessage`** — use the `task` tool with `mode:
  "background"` for parallel agent execution, or `mode: "sync"` for sequential.
- **File-based data passing** — agents write outputs to workspace directories
  (e.g., `workspaces/{issue}/openapi/`), and downstream agents read from there.
- **Result aggregation** — the orchestrator collects outputs from all agents
  and passes them to the schema-reviewer for cross-validation.

### Progressive Disclosure

Agent and skill descriptions are intentionally verbose with trigger keywords.
This allows the Copilot CLI to surface the right agent when the user's prompt
matches domain-specific terms (e.g., "Kafka" → event-engineer, "proto" →
grpc-engineer).

## Protocol → Output Mapping

| Protocol | Output Directory | File Format | Validation Command |
|----------|-----------------|-------------|-------------------|
| REST / OpenAPI | `openapi/` | OpenAPI 3.1 YAML | `npx @stoplight/spectral-cli lint` |
| SSE | `sse/` | OpenAPI 3.1 YAML | `npx @stoplight/spectral-cli lint` |
| WebSocket | `websocket/` | AsyncAPI 3.0 YAML | `npx @asyncapi/cli validate` |
| gRPC / Protobuf | `proto/` | proto3 `.proto` | `buf lint` |
| GraphQL | `graphql/` | SDL `.graphql` | `npx graphql-js validate` |
| Kafka / RabbitMQ / NATS | `events/` | AsyncAPI 3.0 YAML + Avro | `npx @asyncapi/cli validate` |
| Webhook | `webhooks/` | OpenAPI 3.1 YAML | `npx @stoplight/spectral-cli lint` |
| MQTT | `mqtt/` | AsyncAPI 3.0 YAML | `npx @asyncapi/cli validate` |
| tRPC / Zod | `trpc/` | TypeScript `.ts` | `tsc --noEmit` |

## Workflow Phases

### Phase 1: Issue Analysis → `00_analysis.md`

The orchestrator reads the Linear issue, extracts protocol requirements, and
produces an analysis document listing detected protocols, entity models, and
agent assignments.

### Phase 2: Agent Delegation (parallel)

Protocol agents run in parallel via the `task` tool. Each agent:
1. Reads the analysis document and issue description
2. Invokes its paired skill to generate schema files
3. Writes output to the protocol-specific directory
4. Reports completion status back to the orchestrator

### Phase 3: Cross-Validation → `_review/review_report.md`

The `schema-reviewer` agent performs a read-only audit across all generated
schemas:
- Data model consistency (field names, types, cardinality)
- Naming convention enforcement (per-protocol rules)
- Backward compatibility checks
- Security attribute coverage
- Cross-protocol field mapping alignment

Produces a structured report with `PASS` / `WARNING` / `FAIL` verdicts.

### Phase 4: Finalization → Commit + Issue Update

The orchestrator:
1. Reviews the audit report
2. If all checks pass: commits schemas, updates Linear issue status
3. If failures exist: routes fixes back to the responsible agents (retry loop)
4. Updates the Linear issue with a summary of generated schemas
