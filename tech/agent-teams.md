# Agent Teams 워크플로우 패턴

> **출처**: [claude-code-ultimate-guide/agent-teams.md](https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/agent-teams.md)
> **상태**: Experimental (Claude Code v2.1.32+, Opus 4.6+)
> **핵심**: 여러 Claude 인스턴스가 병렬로 작업하고, 팀 리드가 자율 조정

---

## 개요

Agent Teams는 Claude Code의 멀티 에이전트 병렬 협업 기능.
하나의 팀 리드가 N개 에이전트를 스폰하고, Git 기반으로 조정하며, 결과를 합성한다.

```
사용자 → 팀 리드 (Claude)
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
 Agent 1   Agent 2   Agent 3
 (Backend) (Frontend) (Tests)
    │         │         │
    └─────────┼─────────┘
              ▼
         Git 자동 머지
              ▼
         팀 리드 합성
```

### 핵심 조정 메커니즘

- **Git-based**: 각 에이전트가 별도 브랜치에서 작업 → 자동 머지
- **Mailbox**: 에이전트 간 peer-to-peer 메시지 교환
- **1M 토큰/에이전트**: 각 에이전트당 ~30,000 라인 코드 처리

---

## Uptempo에 적용할 핵심 패턴

### 1. 태스크 분해 전략 — "경계가 명확한 분할"

**좋은 분해** (비중첩 파일셋):
```
Agent 1: OpenAPI 스키마 생성       → openapi/*.yaml
Agent 2: Protobuf 스키마 생성      → proto/*.proto
Agent 3: AsyncAPI/WebSocket 생성   → websocket/*.yaml
```

**나쁜 분해** (파일 충돌 위험):
```
Agent 1: User 모델 스키마
Agent 2: User API 엔드포인트
Agent 3: User 이벤트 스키마
→ 모두 같은 User 정의를 다루므로 일관성 문제
```

**Uptempo 적용**: 프로토콜별로 에이전트를 분리하면 파일 충돌 없이 병렬 생성 가능.
단, **프로토콜 간 일관성**은 별도 검증 에이전트가 필요.

### 2. Interface-First 접근 — "계약을 먼저, 구현은 나중에"

```
단계 1: 팀 리드가 내부 스키마 모델(IR) 정의
         → 공통 모델명, 필드, 타입 확정

단계 2: 각 에이전트가 IR을 자기 포맷으로 변환
         → Agent 1: IR → OpenAPI
         → Agent 2: IR → Protobuf
         → Agent 3: IR → AsyncAPI

단계 3: 교차 검증 에이전트가 일관성 확인
```

이것은 `architecture-patterns.md`의 "IR → 멀티 타겟" 패턴과 정확히 일치.

### 3. Read-Heavy vs Write-Heavy 트레이드오프

| 작업 유형 | 멀티 에이전트 적합성 | 이유 |
|----------|:---:|------|
| 코드 리뷰/분석 | ✅ | 읽기 위주, 병렬화 이점 큼 |
| 버그 추적 | ✅ | 독립적 가설 검증 가능 |
| 스키마 생성 (프로토콜별) | ✅ | **비중첩 파일셋** |
| 공유 타입 수정 | ❌ | 머지 충돌 위험 |
| 순차적 의존 작업 | ❌ | 병렬화 이점 없음 |

**Uptempo 시사점**: 스키마 생성은 프로토콜별로 **출력 디렉토리가 분리**되어 있으므로
멀티 에이전트에 이상적인 구조. 단, 공유 모델 정의는 단일 에이전트가 먼저 확정해야 함.

### 4. 병렬 가설 검증 — 디버깅 패턴

```
문제: 생성된 스키마 품질 이슈

Agent 1: 스키마 구조 검증 (Spectral / buf lint)
Agent 2: 프로토콜 간 일관성 검증 (모델명, 필드 타입)
Agent 3: 실제 사용 시나리오 테스트 (목 서버 생성 시도)

→ 3개 관점에서 동시에 검증, 1/3 시간
```

### 5. Iterative Retrieval — 서브 에이전트 컨텍스트 관리

서브 에이전트가 컨텍스트 부족 시 **최대 3회 추가 요청** 가능:

```
Cycle 1: 태스크 + 초기 컨텍스트 → 확신 있으면 출력, 없으면 추가 요청
Cycle 2: 요청된 컨텍스트 수신 → 확신 있으면 출력, 없으면 마지막 요청
Cycle 3: 최종 컨텍스트 → 불확실해도 최선의 출력 + 가정 명시
```

**서브 에이전트에 전달할 내용 구조**:

```markdown
## Objective (WHY)
[이 태스크가 존재하는 이유 — 해결하려는 문제]

## Task (WHAT)
[구체적으로 무엇을 할지]

## Context
- 접근 가능한 파일: [...]
- 알려진 제약: [...]
- 건드리지 말아야 할 것: [...]

## 추가 정보가 필요하면
최대 2회 추가 컨텍스트 요청 가능. 구체적으로:
- 필요한 정확한 파일/심볼 명시
- 왜 필요한지 설명
"[X]가 필요합니다. 이유: [Y]" 형식으로.

## Output format
[...]
```

**핵심 교훈**: WHAT만 주지 말고 **WHY도 함께** 전달해야 수정 사이클이 줄어듦.
Uptempo의 WORKFLOW.md Liquid 템플릿에 이 구조를 반영 가능.

### 6. 비용 트레이드오프

| 워크플로우 | 단일 에이전트 | 3 에이전트 | 배수 |
|-----------|:---:|:---:|:---:|
| 코드 리뷰 (소규모) | 10K 토큰 | 25K | 2.5x |
| 버그 조사 | 30K | 70K | 2.3x |
| 기능 구현 | 100K | 200K | 2x |
| 대규모 리팩토링 | 150K | 250K | 1.7x |

**경험칙**: 시간 절약 > 2x 토큰 비용 증가일 때만 정당화됨.

→ Ouroboros의 **PAL Router** (1x/10x/30x)와 결합하면:
- 간단한 스키마 → 단일 에이전트 + Frugal 모델
- 복잡한 멀티 프로토콜 → 팀 에이전트 + Frontier 모델

---

## 의사결정 프레임워크

```
시작
  │
  ├─ 단순 작업 (<5 파일)? ──YES──→ 단일 에이전트
  │
  ├─ 완전히 독립적? ──YES──→ 멀티 인스턴스 (별도 터미널)
  │
  ├─ 품질 분리 필요? ──YES──→ 듀얼 인스턴스 (계획+실행)
  │
  ├─ 읽기 위주 (분석/리뷰)? ──YES──→ Agent Teams ✓
  │
  ├─ 쓰기 위주 (공유 파일)? ──YES──→ 단일 에이전트
  │
  ├─ 예산 제한? ──YES──→ 단일 에이전트
  │
  └─ 복잡한 조정 필요? ──YES──→ Agent Teams ✓
                        ──NO──→ 단일 에이전트
```

### Uptempo 스키마 생성에 적용한 의사결정

```
Linear 이슈 수신
  │
  ├─ 단일 프로토콜 요청? ──YES──→ 단일 에이전트
  │     (예: "User API OpenAPI만")
  │
  ├─ 멀티 프로토콜 요청? ──YES──→ Agent Teams
  │     (예: "User 서비스 전체 스키마")
  │     │
  │     ├─ IR 정의 에이전트 (팀 리드)
  │     ├─ OpenAPI 에이전트
  │     ├─ Protobuf 에이전트
  │     └─ AsyncAPI 에이전트
  │
  └─ 스키마 리뷰/검증? ──YES──→ Agent Teams (읽기 위주)
        ├─ 구조 검증 에이전트
        ├─ 일관성 검증 에이전트
        └─ 사용 시나리오 검증 에이전트
```

---

## Beads vs Agent Teams vs Uptempo Worktree

| 관점 | Beads (Yegge) | Agent Teams (Anthropic) | Uptempo Worktree |
|------|:---:|:---:|:---:|
| 조정 | Event Sourcing | Git 기반 | 파일 시스템 격리 |
| 영속성 | SQLite (beads.db) | Git 커밋 | 디렉토리 |
| 통신 | MCP 서버 | Mailbox + Git | JSON-RPC |
| 복잡도 | 높음 | 중간 (실험적) | 낮음 |
| 가시성 | agent-chat UI | Claude Code 네이티브 | tmux |

**Uptempo 시사점**: 현재 `WorkspaceManager`의 이슈별 디렉토리 격리는
Agent Teams의 Git 기반 격리와 유사한 패턴. 향후 멀티 에이전트 확장 시
Git worktree 기반 격리를 활용하면 자연스러운 확장이 가능.

---

## 실제 사례 벤치마크

| 사례 | 결과 | 출처 |
|------|------|------|
| Fountain (스타트업) | **50% 속도 향상** | Anthropic 2026 보고서 |
| CRED (핀테크, 1500만 유저) | **2x 속도** | Anthropic 2026 보고서 |
| Paul Rayner (프로덕션) | 3개 동시 워크플로우 성공 | LinkedIn, 2026.02 |
| C 컴파일러 구축 (Anthropic) | 자율적으로 C 컴파일러 구축 | Anthropic Engineering |

---

## 핵심 주의사항

1. **머지 충돌**: 같은 파일을 여러 에이전트가 수정하면 발생 → **비중첩 분할 필수**
2. **컨텍스트 격리**: 에이전트 간 자동 컨텍스트 공유 없음 → **명시적 메시지 필요**
3. **비용**: 3 에이전트 = ~3x 토큰 비용 → **복잡한 작업에만 사용**
4. **실험적 기능**: 안정성 보장 없음, 변경/제거 가능
