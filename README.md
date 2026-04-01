# Uptempo

**Symphony에 영향을 받은 Uptempo orchestration runtime** — Linear 이슈를 읽고,
가장 적합한 네트워크 인터페이스/프로토콜을 발굴한 뒤, 그 선택을 뒷받침하는
스키마와 근거를 남기는 자동화 에이전트입니다.

Uptempo의 핵심은 단순 생성이 아닙니다.

- 어떤 인터페이스가 맞는지 **발굴**
- plausible한 대안을 **비교**
- 선택 이유를 **실험/검증으로 증명**
- 결과를 스키마 산출물과 함께 **Linear workflow** 안에서 다루기

즉, Uptempo는 "schema emitter"라기보다 **protocol discovery + schema execution**
에 더 가깝습니다.

## 아키텍처

```text
Linear (이슈 트래커)
  │
  ▼
Orchestrator (Python)           ← Linear 폴링, 동시성/재시도 관리
  ├── WorkflowLoader            ← built-in WORKFLOW.md 파싱
  ├── Config                    ← 타입 기반 설정
  ├── Tracker                   ← Linear GraphQL 어댑터
  ├── WorkspaceManager          ← 이슈별 워크스페이스 관리
  ├── AgentRunner               ← Codex app-server JSON-RPC
  └── runtime_assets/           ← 내장 workflow/codex/api/demo 자산
        │
        ▼
Protocol / Schema Execution     ← OpenAPI, gRPC, Thrift, WebSocket, GraphQL, events, etc.

Runtime Companion Modules
  ├── src/uptempo/runtime_assets/api/   ← FastAPI
  └── src/uptempo/runtime_assets/demo/  ← Streamlit
```

## 빠른 시작

```bash
# 의존성 설치
uv sync --all-extras

# 전체 품질 게이트
make all

# 오케스트레이터 실행
uv run python -m uptempo
```

실행 전에는 최소한 다음이 준비되어 있어야 합니다.

- `LINEAR_API_KEY`
- 내장 기본 워크플로우 `src/uptempo/runtime_assets/WORKFLOW.md`
- 필요 시 `UPTEMPO_WORKFLOW_PATH`로 명시적 override
- 필요 시 `UPTEMPO_WORKSPACE_SOURCE`로 워크스페이스 bootstrap source override
- Codex 실행 환경

기본 workspace bootstrap은 현재 Uptempo checkout을 명시적으로 clone합니다.
다른 source를 쓰고 싶으면 `UPTEMPO_WORKSPACE_SOURCE`에 로컬 경로 또는 Git URL을 지정하세요.

## 동작 방식

1. Uptempo가 Linear에서 활성 이슈를 폴링합니다.
2. 이슈 설명과 맥락을 바탕으로 적합한 프로토콜/인터페이스 후보를 해석합니다.
3. 내장 `WORKFLOW.md`(또는 명시적 override)의 운영 규칙에 따라 분석, 구현, 검증, PR 흐름을 진행합니다.
4. 결과로 스키마 산출물과 검증 근거를 남깁니다.

## 주요 산출물

Uptempo는 필요에 따라 다음 디렉터리들에 산출물을 남깁니다.

- `openapi/`
- `proto/`
- `thrift/`
- `websocket/`
- `sse/`
- `graphql/`
- `events/`
- `webhook/`
- `mqtt/`
- `trpc/`

## 워크플로우 기준

운영 흐름은 OpenAI Symphony, 특히 `elixir/WORKFLOW.md`의 영향을 강하게 받습니다.
다만 Uptempo는 여기에 다음을 추가합니다.

- protocol discovery
- alternative comparison
- evidence / experiment reporting

즉, **운영 discipline은 Symphony를 참고하고, 도메인 판단은 Uptempo에 맞게 확장**합니다.

## 개발자 참고

내부 harness, worktree 운영, Copilot/Codex skill surface 같은 개발자 전용 정보는
사용자 README의 핵심이 아닙니다. 그런 내용은 아래 문서를 참고하세요.

- Runtime Codex asset surface: [`src/uptempo/runtime_assets/codex/`](src/uptempo/runtime_assets/codex/)
- 개발/운영 규칙: [`.github/copilot-instructions.md`](.github/copilot-instructions.md)

## 라이선스

MIT
