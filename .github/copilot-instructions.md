# Uptempo — Copilot Instructions

Uptempo는 **Symphony 기반 코딩 에이전트**로, Linear 이슈에서 네트워크 스키마 설계 요청을 받아
REST/OpenAPI, gRPC/Protobuf, Thrift, WebSocket 스키마 파일을 자동 생성하고 PR을 올립니다.

[openai/symphony SPEC.md](https://github.com/openai/symphony/blob/main/SPEC.md) 오케스트레이션
모델을 따릅니다: Linear 폴링 → 격리된 워크스페이스 생성 → 코딩 에이전트 실행 → 스키마 PR 생성.

## 아키텍처

```
Linear (이슈 트래커)
  │
  ▼
Orchestrator (Python)          ← Linear 폴링, 동시성/재시도 관리
  ├── WorkflowLoader           ← WORKFLOW.md 읽기 (YAML 프론트매터 + 프롬프트 템플릿)
  ├── Config                   ← 타입 기반 getter, $ENV 해석, 기본값 적용
  ├── Tracker (Linear 클라이언트) ← GraphQL 어댑터, 이슈 정규화
  ├── WorkspaceManager         ← 이슈별 디렉토리, 훅 라이프사이클
  └── AgentRunner              ← Codex app-server stdio JSON-RPC 프로세스 관리
        │
        ▼
Schema Generator (에이전트 도구)
  ├── openapi/    → OpenAPI 3.1 YAML (REST)
  ├── proto/      → .proto 파일 (gRPC)
  ├── thrift/     → .thrift IDL 파일
  └── websocket/  → AsyncAPI 3.0 YAML 또는 JSON Schema (WebSocket)

Demo Stack (스키마 기반 데모 서비스)
  ├── api/        → FastAPI 백엔드 (생성된 스키마 기반 stub API 서빙)
  └── demo/       → Streamlit 데모 페이지 (스키마 시각화 + API 테스트 UI)
```

### 데모 스택

스키마 자동 생성 후속 작업으로, 생성된 스키마를 즉시 체험할 수 있는 데모 환경을 제공합니다.

- **FastAPI 백엔드** (`api/`): 생성된 OpenAPI 스키마로부터 stub 엔드포인트를 자동 마운트하고,
  gRPC/Thrift 스키마의 메타데이터를 REST로 조회할 수 있는 API를 제공합니다.
- **Streamlit 데모** (`demo/`): 스키마 파일을 업로드하거나 선택하면 구조를 시각화하고,
  FastAPI 백엔드의 엔드포인트를 직접 호출해볼 수 있는 인터랙티브 UI입니다.

### 핵심 레이어 (Symphony 스펙 기반)

| 레이어          | 역할                                                                |
|-----------------|---------------------------------------------------------------------|
| Policy          | `WORKFLOW.md` 프롬프트 본문 — 프로토콜별 스키마 설계 지시사항        |
| Configuration   | YAML 프론트매터 → 타입 기반 런타임 설정                              |
| Coordination    | 오케스트레이터: 폴 루프, 적격성 판단, 동시성, 재시도, 조정           |
| Execution       | 워크스페이스 라이프사이클 + Codex app-server 서브프로세스             |
| Integration     | Linear GraphQL 어댑터                                                |
| Observability   | 구조화된 로그, 선택적 HTTP 대시보드 (`/api/v1/state`)                |

### 오케스트레이터 상태 머신

내부 클레임 상태 (Linear 상태와 다름):

- `Unclaimed` → `Claimed` → `Running` | `RetryQueued` → `Released`

성공적 워커 종료 시 1초 후 연속 재시도를 스케줄하여 이슈가 여전히 활성 상태인지 확인합니다
(다중 턴 지원). 실패 시 지수 백오프로 재시도하며 `agent.max_retry_backoff_ms`로 상한을 둡니다.

### Codex App-Server 프로토콜

stdio를 통한 줄 단위 JSON-RPC 통신:

1. `initialize` → 응답 대기
2. `initialized` 알림
3. `thread/start` → `thread_id` 획득
4. `turn/start` → `turn_id` 획득, `turn/completed` | `turn/failed`까지 이벤트 스트리밍

연속 턴은 동일 `thread_id`를 재사용하며, 최초 태스크 프롬프트를 재전송하지 않습니다.

## 빌드, 테스트, 린트

```bash
# 의존성 설치
pip install -e ".[dev]"

# 전체 품질 게이트
make all                    # 포맷 검사 + 린트 + 테스트 + 타입 검사

# 개별 명령
make fmt                    # 자동 포맷 (black + isort)
make lint                   # ruff + mypy
make test                   # 전체 테스트 스위트
pytest tests/test_foo.py    # 단일 테스트 파일
pytest tests/test_foo.py::test_bar -v   # 단일 테스트 함수

# 타입 검사
mypy src/

# 데모 서버 실행
uvicorn api.main:app --reload --port 8000    # FastAPI 백엔드
streamlit run demo/app.py --server.port 8501  # Streamlit 데모 페이지
```

## 컨벤션

### Symphony 스펙 정합성

- 구현은 [SPEC.md](https://github.com/openai/symphony/blob/main/SPEC.md)와 정합성을 유지합니다.
  스펙의 상위집합은 허용하지만 스펙과 충돌해서는 안 됩니다.
- 런타임 설정은 `WORKFLOW.md` 프론트매터에서 로드합니다. 설정 접근은 반드시 타입 기반 `Config`
  클래스를 통해 하고, 임의의 환경변수 직접 읽기는 지양합니다.
- 워크스페이스 안전성이 가장 중요합니다: 코딩 에이전트는 반드시 이슈별 워크스페이스 디렉토리
  안에서만 실행해야 하며, 워크스페이스 경로는 설정된 root 하위에 있어야 합니다.

### 스키마 생성 규칙

- **OpenAPI**: OpenAPI 3.1 YAML 생성. 워크스페이스 내 `openapi/` 디렉토리에 배치.
- **Protobuf**: proto3 `.proto` 파일 생성. `proto/`에 배치. 이슈에 타겟 언어가 명시되면
  `option go_package`, `option java_package` 등을 포함.
- **Thrift**: `.thrift` IDL 생성. `thrift/`에 배치.
- **WebSocket**: AsyncAPI 3.0 YAML 또는 JSON Schema 생성. `websocket/`에 배치.
- 모든 스키마 파일에 Linear 이슈 식별자를 참조하는 헤더 주석을 포함합니다.
- 커밋 전 생성된 스키마를 검증합니다 (proto는 `buf lint`, OpenAPI는 `spectral` 등).

### Python 스타일

- 모든 공개 함수(`def`)에 타입 힌트를 붙입니다. 비공개 헬퍼(`_func`)는 선택입니다.
- 도메인 모델(Issue, WorkflowDefinition, Config 등)은 `dataclasses` 또는 `pydantic`을 사용합니다.
- 오케스트레이터 폴 루프와 HTTP 호출에는 `asyncio` 비동기 I/O를 사용합니다.
- `structlog`으로 구조화된 로깅을 하며, `issue_id`와 `session_id` 컨텍스트 필드를 포함합니다.

### WORKFLOW.md 계약

프롬프트 템플릿은 Liquid 호환 구문을 사용합니다 (`{{ issue.title }}`, `{% if attempt %}`).
템플릿 변수:

- `issue` — 정규화된 이슈 필드 전체 (id, identifier, title, description, state, labels 등)
- `attempt` — 첫 실행 시 `null`, 재시도/연속 시 정수

### 워크스페이스 훅

- `after_create` — 워크스페이스 디렉토리 최초 생성 시 1회 실행 (예: git clone + 의존성 설치)
- `before_run` — 에이전트 시도마다 실행; 실패 시 해당 시도 중단
- `after_run` / `before_remove` — 실패해도 로그만 남기고 무시

### 에러 처리

- 디스패치 검증 실패: 새 디스패치를 건너뛰되 조정(reconciliation)은 계속 수행합니다.
- 워커 실패: 지수 백오프 재시도로 전환합니다.
- 트래커 API 실패: 현재 틱을 건너뛰고 다음 틱에서 재시도합니다.
- 프롬프트 렌더링 실패 (알 수 없는 변수/필터): 해당 실행 시도를 즉시 실패 처리합니다.

### 테스트 방침

- 스키마 생성 결과를 알려진 정상 결과(fixture)와 비교 테스트합니다.
- 단위 테스트에서 Linear GraphQL API와 Codex app-server 서브프로세스를 모킹합니다.
- 생성된 스키마 파일에 대해 스냅샷 테스트를 활용합니다.

### FastAPI 백엔드 (`api/`)

- 생성된 OpenAPI 스키마를 파싱하여 라우터를 동적으로 마운트합니다.
- gRPC/Thrift/WebSocket 스키마의 메타데이터(서비스, 메서드, 메시지 구조)를 REST 엔드포인트로
  조회할 수 있도록 합니다.
- Pydantic 모델로 요청/응답을 검증하며, 자동 생성된 `/docs` (Swagger UI)를 활용합니다.
- CORS 미들웨어를 설정하여 Streamlit 프론트엔드에서 접근 가능하게 합니다.

### Streamlit 데모 (`demo/`)

- `st.file_uploader` 또는 드롭다운으로 스키마 파일을 선택하는 인터페이스를 제공합니다.
- 스키마 구조를 트리 뷰 또는 테이블로 시각화합니다.
- FastAPI 백엔드 엔드포인트를 호출하여 실시간 응답을 보여주는 인터랙티브 테스트 패널을 포함합니다.
- `requests` 또는 `httpx`로 FastAPI 백엔드와 통신합니다.
