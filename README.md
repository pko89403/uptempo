# Uptempo

**Symphony 기반 코딩 에이전트** — Linear 이슈에서 네트워크 스키마 설계 요청을 받아
REST/OpenAPI, gRPC/Protobuf, Thrift, WebSocket 스키마 파일을 자동 생성하고 PR을 올립니다.

## 아키텍처

```
Linear (이슈 트래커)
  │
  ▼
Orchestrator (Python)         ← Linear 폴링, 동시성/재시도 관리
  ├── WorkflowLoader          ← WORKFLOW.md 파싱
  ├── Config                  ← 타입 기반 설정
  ├── Tracker                 ← Linear GraphQL 어댑터
  ├── WorkspaceManager        ← 이슈별 워크스페이스 관리
  └── AgentRunner             ← Codex app-server JSON-RPC
        │
        ▼
Schema Generator              ← openapi, proto, thrift, websocket

Demo Stack
  ├── api/                    ← FastAPI (스키마 기반 stub API)
  └── demo/                   ← Streamlit (시각화 + 테스트 UI)
```

## 빠른 시작

```bash
# 의존성 설치
pip install -e ".[dev]"

# 전체 품질 게이트
make all          # fmt + lint + test + typecheck

# 개별 명령
make fmt          # black + isort
make lint         # ruff
make test         # pytest
make typecheck    # mypy

# 데모 서버
uvicorn api.main:app --reload --port 8000
streamlit run demo/app.py --server.port 8501
```

## 개발 환경

이 프로젝트는 **bare repo + worktree + tmux** 구조로 개발합니다.

```bash
# worktree 관리
bash scripts/wt add feat/my-feature
bash scripts/wt list
bash scripts/wt launch feat/my-feature
bash scripts/wt merge feat/my-feature
bash scripts/wt remove feat/my-feature
```

자세한 내용은 [.github/copilot-instructions.md](.github/copilot-instructions.md)를 참고하세요.

## 라이선스

MIT
