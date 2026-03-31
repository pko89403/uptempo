# Ouroboros 분석

> **Repo**: https://github.com/Q00/ouroboros
> **버전**: v0.26.6 (2026-03-30)
> **언어**: Python 3.12+ (Rust TUI 포함)
> **라이선스**: MIT
> **한줄 요약**: AI 코딩 에이전트를 위한 **Specification-first 워크플로우 엔진**

---

## 핵심 철학

> "Stop prompting. Start specifying."
> AI 코딩의 병목은 AI 능력이 아니라 **사람의 명확성**이다.

Ouroboros는 코드를 작성하기 전에 **"무엇을 만들 것인지"를 정의하는 과정**을 자동화한다.
소크라테스식 질문 → 스펙 결정화 → 실행 → 평가의 순환 루프를 돌며 진화한다.

---

## 아키텍처

```
Interview → Seed → Execute → Evaluate
    ↑                           ↓
    └──── Evolutionary Loop ────┘
```

### 6단계 파이프라인

| 단계 | 모듈 | 역할 |
|------|------|------|
| **1. Big Bang** | `bigbang/` | 소크라테스식 인터뷰, 모호성 점수화 (Ambiguity ≤ 0.2 게이트) |
| **2. PAL Router** | `routing/` | 3단계 LLM 비용 최적화: Frugal(1x) → Standard(10x) → Frontier(30x) |
| **3. Execution** | `execution/` | Double Diamond 분해: Discover → Define → Design → Deliver |
| **4. Resilience** | `resilience/` | 정체 감지 (spinning, oscillation, diminishing returns) + 5개 lateral persona |
| **5. Evaluation** | `evaluation/` | 3단계 검증: Mechanical($0) → Semantic → Multi-Model Consensus |
| **6. Evolution** | `evolution/` | Wonder/Reflect 사이클, 온톨로지 수렴 감지 (유사도 ≥ 0.95) |

### src/ouroboros/ 디렉토리 구조

```
src/ouroboros/
├── agents/          # 9개 AI 에이전트 정의 (.md 파일)
├── bigbang/         # 인터뷰, 모호성 점수화, brownfield 탐색
├── routing/         # PAL Router — 3단계 비용 최적화
├── execution/       # Double Diamond, 계층적 AC 분해
├── evaluation/      # Mechanical → Semantic → Consensus
├── evolution/       # Wonder/Reflect, 수렴 감지
├── resilience/      # 4패턴 정체 감지, 5개 lateral persona
├── observability/   # 3요소 드리프트 측정, 자동 회고
├── persistence/     # Event Sourcing (SQLAlchemy + aiosqlite)
├── orchestrator/    # 런타임 추상화 (Claude Code, Codex CLI)
├── core/            # 타입, 에러, Seed, 온톨로지, 보안
├── providers/       # LiteLLM 어댑터 (100+ 모델)
├── mcp/             # MCP 클라이언트/서버
├── plugin/          # 플러그인 시스템 (skill/agent 자동 발견)
├── pm/              # PM 모드 (PRD 생성)
├── strategies/      # 실행 전략
├── tui/             # 터미널 UI 대시보드
├── cli/             # Typer 기반 CLI
└── verification/    # 검증 모듈
```

---

## Nine Minds — 9개 에이전트

| 에이전트 | 역할 | 핵심 질문 |
|---------|------|----------|
| **Socratic Interviewer** | 질문만 한다, 절대 만들지 않음 | *"당신이 가정하고 있는 것은?"* |
| **Ontologist** | 증상이 아닌 본질을 찾음 | *"이것이 정말로 무엇인가?"* |
| **Seed Architect** | 대화에서 스펙 결정화 | *"완전하고 모호하지 않은가?"* |
| **Evaluator** | 3단계 검증 | *"올바른 것을 만들었는가?"* |
| **Contrarian** | 모든 가정에 도전 | *"반대가 참이라면?"* |
| **Hacker** | 비관습적 경로 탐색 | *"실제로 진짜인 제약은?"* |
| **Simplifier** | 복잡성 제거 | *"동작하는 가장 단순한 것은?"* |
| **Researcher** | 코딩 중단, 조사 시작 | *"실제 증거가 있는가?"* |
| **Architect** | 구조적 원인 식별 | *"처음부터 다시 만든다면?"* |

---

## 핵심 기술 메커니즘

### 1. 모호성 게이트 (Ambiguity Score)

```
Ambiguity = 1 - Σ(clarity_i × weight_i)
```

| 차원 | Greenfield 가중치 | Brownfield 가중치 |
|------|:---:|:---:|
| 목표 명확성 | 40% | 35% |
| 제약 명확성 | 30% | 25% |
| 성공 기준 | 30% | 25% |
| 컨텍스트 명확성 | — | 15% |

**임계값: ≤ 0.2** → 이 이하일 때만 Seed 생성 허용.

### 2. 온톨로지 수렴 (Evolution 종료 조건)

```
Similarity = 0.5 × name_overlap + 0.3 × type_match + 0.2 × exact_match
```

**임계값: ≥ 0.95** → 연속 세대가 동일한 스키마를 생산하면 루프 종료.

추가 종료 신호:
- 3세대 연속 유사도 ≥ 0.95 (정체)
- Gen N ≈ Gen N-2 (진동)
- 70%+ 질문 중복 (반복적 피드백)
- 30세대 하드캡 (안전밸브)

### 3. PAL Router — 비용 최적화

```
Frugal (1x)  →  실패 시 자동 에스컬레이션  →  Standard (10x)
Standard (10x) →  실패 시 자동 에스컬레이션 →  Frontier (30x)
Frontier (30x) →  성공 시 자동 다운그레이드  →  Standard (10x)
```

### 4. 드리프트 측정

```
Drift = 0.5 × Goal + 0.3 × Constraint + 0.2 × Ontology
임계값: ≤ 0.3
```

---

## 기술 스택

| 카테고리 | 기술 |
|---------|------|
| **언어** | Python 3.12+, Rust (TUI) |
| **CLI** | Typer + Rich |
| **데이터** | Pydantic v2, SQLAlchemy[asyncio] + aiosqlite |
| **LLM** | LiteLLM (100+ 모델), Anthropic SDK |
| **영속성** | Event Sourcing (이벤트 기반 상태 관리) |
| **런타임** | Claude Code, Codex CLI (플러거블 백엔드) |
| **통합** | MCP 클라이언트/서버 |
| **로깅** | structlog |
| **재시도** | stamina |
| **TUI** | Textual (Python), Rust crate (ouroboros-tui) |
| **빌드** | Hatchling + hatch-vcs |
| **대시보드** | Streamlit + Plotly + Pandas (옵션) |

---

## 통신 패턴

| 통신 | 프로토콜 | 용도 |
|------|---------|------|
| CLI ↔ MCP 서버 | **MCP (Model Context Protocol)** | 스킬/에이전트 실행, 세션 관리 |
| Ouroboros ↔ LLM | **LiteLLM HTTP API** | 다중 프로바이더 LLM 호출 |
| Ouroboros ↔ Claude Code | **Claude Agent SDK** | 런타임 백엔드 오케스트레이션 |
| 상태 관리 | **Event Sourcing (SQLite)** | 모든 상태 변경을 이벤트로 기록 |
| MCP 서버 | **SSE Transport** | MCP 서버-클라이언트 통신 |

---

## Uptempo와의 비교

| 관점 | Ouroboros | Uptempo |
|------|-----------|---------|
| **목적** | 모호한 아이디어 → 검증된 코드베이스 | 이슈 요청 → 네트워크 스키마 |
| **입력** | 자연어 (대화) | Linear 이슈 |
| **핵심 프로세스** | 소크라테스식 인터뷰 → Seed → 실행 → 평가 | 폴링 → LLM → 스키마 생성 → 검증 |
| **에이전트** | 9개 전문 에이전트 (역할 분리) | 단일 Codex 에이전트 |
| **검증** | 3단계 (Mechanical→Semantic→Consensus) | 도구별 (Spectral, buf lint) |
| **진화** | 온톨로지 수렴까지 반복 (≥0.95) | 재시도 (exponential backoff) |
| **런타임** | Claude Code / Codex CLI (플러거블) | Codex app-server (JSON-RPC) |
| **영속성** | Event Sourcing (SQLite) | 파일 시스템 (워크스페이스) |
| **비용 최적화** | PAL Router (1x/10x/30x) | 없음 (단일 모델) |

---

## Uptempo에 참고할 핵심 패턴

### 1. 모호성 게이트 → 스키마 품질 게이트

Ouroboros의 Ambiguity Score를 스키마 생성 전 **요구사항 완전성 검사**에 적용:

```python
# 이슈 분석 → 명확성 점수 산출
ambiguity = calculate_ambiguity(issue)
if ambiguity > 0.2:
    # Linear에 추가 질문 코멘트 달기
    tracker.add_comment(issue_id, "다음 항목이 불명확합니다: ...")
    return  # 스키마 생성 보류
```

→ "불충분한 이슈에서 스키마를 무작정 만들지 않는다" 가 핵심.

### 2. Multi-Agent 역할 분리 → 스키마 생성 에이전트 분리

현재 Uptempo는 단일 에이전트가 모든 스키마를 생성. Ouroboros처럼 역할 분리 가능:

```
Analyst Agent     → 이슈에서 요구사항 추출
Architect Agent   → 내부 스키마 모델(IR) 설계
Generator Agent   → IR → OpenAPI/Protobuf/AsyncAPI 변환
Reviewer Agent    → 생성된 스키마 교차 검증
```

### 3. PAL Router → LLM 비용 최적화

간단한 스키마는 저렴한 모델, 복잡한 스키마는 강력한 모델:

```
단순 CRUD API → Frugal (GPT-4o-mini)     비용 1x
중간 복잡도   → Standard (GPT-4o)         비용 10x
복잡한 gRPC   → Frontier (Claude Opus)    비용 30x
```

### 4. Event Sourcing → 스키마 생성 이력 추적

현재 Uptempo의 파일 시스템 기반 워크스페이스 대신:

```
이벤트 기록:
  schema.generation.started   {issue_id, timestamp}
  schema.openapi.generated    {file, version}
  schema.proto.validated      {result: pass}
  schema.generation.completed {all_schemas, duration}
```

→ 이력 추적, 롤백, 세대별 비교 가능

### 5. 수렴 감지 → 스키마 안정성 판단

에이전트가 반복 생성할 때 스키마가 안정되었는지 자동 판단:

```python
similarity = compare_schemas(gen_n, gen_n_minus_1)
if similarity >= 0.95:
    # 스키마가 수렴 → 최종 버전으로 확정
    finalize_schema(gen_n)
```

### 6. Brownfield 탐색 → 기존 스키마 인식

Ouroboros의 brownfield 기능처럼, 기존 프로젝트의 스키마 파일을 자동 감지:

```
기존 openapi/*.yaml 발견 → 모델명/엔드포인트 추출
기존 proto/*.proto 발견 → 메시지/서비스 추출
→ LLM 컨텍스트에 포함하여 일관성 유지
```

---

## 주요 의사결정 참고

| Ouroboros 결정 | 이유 | Uptempo 적용 가능성 |
|---------------|------|-------------------|
| Event Sourcing 채택 | 모든 상태 변경 추적 + 세션 복구 | ✅ 스키마 생성 이력/롤백에 유용 |
| LiteLLM 어댑터 | 100+ 모델 지원, 프로바이더 락인 방지 | ✅ Codex 단일 의존 탈피 |
| MCP 프로토콜 | Claude Code/Codex CLI 통합 표준 | ⚠️ 현재 JSON-RPC로 충분하나 향후 고려 |
| Pydantic 엄격 검증 | 페이즈 간 데이터 안전성 | ✅ 이미 사용 중 |
| 9개 에이전트 역할 분리 | 단일 에이전트 한계 극복 | ✅ 스키마 생성 품질 향상 |
| 모호성 정량화 | "충분히 명확한가?" 를 주관이 아닌 수학으로 | ✅ 이슈 품질 게이트에 적용 |
