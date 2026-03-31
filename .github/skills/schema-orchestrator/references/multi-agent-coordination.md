# Multi-Agent Coordination Patterns Reference

## Expert Pool Pattern: Routing by Capability

Route tasks to the most capable agent based on skill matching:

```
┌────────────┐    analyze    ┌────────────────┐    dispatch    ┌─────────────┐
│ Orchestrator│──────────────→│ Capability Map │──────────────→│ Expert Agent│
└────────────┘               └────────────────┘               └─────────────┘
```

### Routing Heuristics
- **Keyword matching**: map request terms to agent skill tags
- **Pattern detection**: file extensions, protocol keywords, schema formats
- **Confidence scoring**: rank agents by relevance, dispatch to highest
- **Fallback chain**: if primary agent fails, try next-best match

```yaml
capabilities:
  generate-openapi:   [REST, OpenAPI, HTTP, CRUD]
  generate-grpc:      [gRPC, protobuf, streaming, RPC]
  generate-graphql:   [GraphQL, query, mutation, subscription]
  generate-sse:       [SSE, EventSource, server-sent, streaming]
  generate-websocket: [WebSocket, real-time, bidirectional, AsyncAPI]
```

## Producer-Reviewer Pattern: Generate Then Validate

Two-phase quality assurance using separate agent roles:

```
Phase 1: PRODUCE                    Phase 2: REVIEW
┌──────────┐  schema  ┌──────────┐  validate  ┌──────────┐  feedback  ┌──────────┐
│ Producer │────────→│  Output  │───────────→│ Reviewer │──────────→│ Producer │
│  Agent   │         │  (file)  │            │  Agent   │           │ (revise) │
└──────────┘         └──────────┘            └──────────┘           └──────────┘
```

### Review Criteria
- **Structural**: Does the output match the expected schema/format?
- **Semantic**: Are names, types, and relationships correct?
- **Completeness**: Are all requested elements present?
- **Consistency**: Does it align with other generated artifacts?

### Iteration Control
- Set maximum revision rounds (e.g., 3)
- Track which issues were fixed vs. introduced
- Escalate to user if reviewer and producer disagree after max rounds

## Parallel Delegation with Background Tasks

Launch independent agents simultaneously for throughput:

```
Orchestrator
  ├── [background] Agent A → generate OpenAPI spec
  ├── [background] Agent B → generate AsyncAPI spec
  └── [background] Agent C → generate shared schemas
       │
       ▼
  Collect all results → Merge → Validate cross-references
```

### Parallelization Rules
- ✅ Parallel: independent schema generation for different protocols
- ✅ Parallel: lint + test on separate files
- ❌ Sequential: schema generation → then code that depends on it
- ❌ Sequential: create file → then read/modify same file

### Synchronization
- Wait for all background agents before merging
- Handle partial failures: continue with successful results
- Log which agents completed and which failed

## File-Based Inter-Agent Communication

Agents share state through the filesystem:

```
.github/skills/<skill>/
  ├── skill.md              # Agent reads instructions
  ├── templates/             # Agent reads templates
  ├── references/            # Agent reads supplementary knowledge
  └── output/                # Agent writes generated artifacts
```

### Conventions
- **Write atomically**: write to temp name, then rename
- **Use clear markers**: include metadata headers in generated files
- **Avoid conflicts**: each agent writes to its own output directory
- **Signal completion**: create a `.done` marker or return success status

### Passing Context Between Agents
```markdown
<!-- Agent A writes context for Agent B -->
## Generation Context
- Source: user prompt analysis
- Protocol: REST + WebSocket hybrid
- Entities: User, Order, Product
- Auth: OAuth 2.0 + API key
```

## Retry and Escalation Strategies

```
Attempt 1: Run agent with original prompt
    ↓ (fail)
Attempt 2: Run agent with refined prompt + error context
    ↓ (fail)
Attempt 3: Run agent with simplified scope
    ↓ (fail)
Escalate: Report to user with partial results + error summary
```

### Retry Guidelines
| Failure Type | Retry? | Strategy |
|-------------|--------|----------|
| Validation error | ✅ | Feed error back into prompt |
| Timeout | ✅ | Reduce scope, increase timeout |
| Missing context | ✅ | Gather more context, retry |
| Fundamental misunderstanding | ❌ | Escalate to user |
| Tool/infra failure | ✅ | Wait and retry (backoff) |

### Error Context Template
```
Previous attempt failed with:
- Error: [specific error message]
- Partial output: [what was generated]
- Fix needed: [specific correction required]
Please regenerate addressing this issue.
```

## Result Synthesis and Conflict Resolution

When multiple agents produce results that must be merged:

### Merge Strategy
1. **Collect** all agent outputs
2. **Detect conflicts** (e.g., same entity defined differently)
3. **Resolve** using priority rules:
   - Most specific agent wins (e.g., gRPC agent's protobuf > generic)
   - User-specified constraints override agent defaults
   - Later revisions override earlier ones
4. **Validate** merged result as a whole

### Conflict Types
| Conflict | Resolution |
|----------|-----------|
| Naming mismatch | Normalize to orchestrator's naming convention |
| Type disagreement | Prefer the more specific/constrained type |
| Missing cross-reference | Generate linking schema ($ref / import) |
| Duplicate definitions | Deduplicate into shared components |

## Phase Detection Heuristics

Determine the current workflow phase to select the right strategy:

| Phase | Indicators | Strategy |
|-------|-----------|----------|
| **Analysis** | No output files yet, user prompt being parsed | Expert Pool routing |
| **Generation** | Templates being populated, files being created | Parallel delegation |
| **Validation** | Output files exist, checking for errors | Producer-Reviewer |
| **Refinement** | Errors found, revising output | Retry with feedback |
| **Completion** | All validations pass, assembling final result | Result synthesis |

### Phase Transition Signals
- Analysis → Generation: capability match found, agent selected
- Generation → Validation: output file written successfully
- Validation → Refinement: validation errors detected
- Refinement → Validation: revised output written (loop)
- Validation → Completion: all checks pass
