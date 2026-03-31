# AI 코딩 에이전트 비교

Uptempo의 "이슈 트래커 → LLM → 코드/스키마 → PR" 파이프라인과 관련된 에이전트들.

---

## 1. SweepAI

- **Repo**: https://github.com/sweepai/sweep
- **Stars**: 8,000+
- **언어**: Python
- **핵심**: GitHub 이슈를 읽고 자동으로 PR 생성하는 AI 주니어 개발자.

### 아키텍처

```
GitHub Issue → Sweep Bot → Code Planning → Code Modification → PR
                   │
                   ├── 커스텀 코드 청킹 알고리즘
                   ├── XML 기반 구조화 프롬프팅
                   └── 유닛 테스트 + 린터 실행
```

### Uptempo에 참고할 점

- **이슈 → PR 워크플로우가 Uptempo와 가장 유사**
- 코드 의존성 분석 후 수정 범위 결정하는 방식
- GitHub App으로 배포 → Uptempo는 Linear 연동이지만 패턴 동일
- 멀티 이슈 비동기 병렬 처리
- 실패 시 자동 재시도 로직

### Uptempo와의 차이

| 관점 | SweepAI | Uptempo |
|------|---------|---------|
| 트래커 | GitHub Issues | Linear |
| 출력 | 코드 변경 (범용) | 네트워크 스키마 (특화) |
| 검증 | 유닛 테스트 + 린터 | Spectral + buf lint |
| LLM 통신 | OpenAI API 직접 호출 | Codex app-server JSON-RPC |

---

## 2. Aider

- **Repo**: https://github.com/Aider-AI/aider
- **Stars**: 42,584
- **언어**: Python
- **핵심**: 터미널 AI 페어 프로그래밍. Git 통합, 멀티 LLM 지원.

### 아키텍처

```
사용자 지시 → Aider → LLM 호출 → 코드 편집 → Git 커밋
                │
                ├── Repo Map (AST 기반 코드베이스 요약)
                ├── Unified Diff 기반 편집
                └── GPT-4, Claude, Gemini 등 멀티 LLM
```

### Uptempo에 참고할 점

- **Repo Map**: AST 파싱으로 코드베이스 구조를 LLM에 컨텍스트로 전달
  - Uptempo에서 기존 스키마 파일 분석 시 유사한 접근 가능
- **에디터 포맷**: whole-file vs unified-diff vs search/replace
  - 스키마 파일 수정 시 diff 기반 접근이 토큰 효율적
- **Git 통합**: 자동 커밋 + 커밋 메시지 생성
- **lint 연동**: 생성 후 자동 lint → 에러 발견 시 자동 재시도

---

## 3. SWE-agent (Princeton NLP)

- **Repo**: https://github.com/princeton-nlp/SWE-agent
- **Stars**: 16,000+
- **언어**: Python
- **핵심**: GitHub 이슈를 자동 분석·수정·PR 제출하는 연구 기반 에이전트.

### 아키텍처

```
GitHub Issue → SWE-agent → 환경 분석 → 코드 수정 → PR 제출
                   │
                   ├── Agent-Computer Interface (ACI)
                   ├── 커스텀 파일 뷰어/에디터
                   ├── Docker 기반 격리 실행
                   └── 린트 + 코드 리뷰 후 제출
```

### Uptempo에 참고할 점

- **Agent-Computer Interface**: 에이전트가 파일 시스템/터미널과 상호작용하는 인터페이스 설계
  - Uptempo의 `AgentRunner`가 Codex와 통신하는 방식과 유사
- **Docker 격리**: 각 이슈별 독립 환경
  - Uptempo의 `WorkspaceManager` (이슈별 디렉토리 격리)와 대응
- **벤치마크**: SWE-bench로 성능 측정
  - Uptempo도 스키마 품질 벤치마크 필요

---

## 4. Devin (Cognition AI)

- **URL**: https://devin.ai/
- **유형**: 상용 (비공개 소스)
- **핵심**: 최초의 완전 자율 AI 소프트웨어 엔지니어.

### Uptempo에 참고할 점

- **Slack/Jira 연동**: 메시지로 작업 지시 → Uptempo의 Linear 연동과 동일 패턴
- **독립 개발 환경**: 작업마다 클라우드 IDE 스핀업
- **대규모 마이그레이션**: 모놀리스 → 마이크로서비스 전환 사례
  - Uptempo가 대규모 스키마 마이그레이션에 활용 가능한 가능성

---

## 에이전트 패턴 비교

```
              ┌──────────────────────────────────────────────┐
              │              공통 파이프라인                    │
              │                                              │
              │  이슈/지시 → 컨텍스트 수집 → LLM 호출         │
              │      → 코드/스키마 생성 → 검증 → 제출          │
              └──────────────────────────────────────────────┘

              ┌──────────┬──────────┬──────────┬──────────┐
              │  Sweep   │  Aider   │ SWE-agent │ Uptempo  │
  ────────────┼──────────┼──────────┼──────────┼──────────┤
  입력         │ GH Issue │ 터미널   │ GH Issue │ Linear   │
  컨텍스트     │ 코드 청킹 │ Repo Map │ ACI      │ Workflow │
  LLM 통신    │ API 직접  │ API 직접 │ API 직접  │ JSON-RPC │
  출력         │ 코드 PR  │ Git 커밋 │ 코드 PR  │ 스키마 PR │
  격리         │ 없음     │ 로컬    │ Docker   │ Workspace│
  검증         │ 테스트   │ lint    │ lint     │ Spectral │
  재시도       │ ✅       │ ✅      │ ✅       │ ✅       │
              └──────────┴──────────┴──────────┴──────────┘
```

---

## 핵심 참고 사항

### 1. 프롬프트 설계

- **SweepAI**: XML 구조화 프롬프팅으로 안정적 출력
- **Aider**: 에디터 포맷(unified-diff)으로 토큰 절약
- Uptempo: WORKFLOW.md의 Liquid 템플릿 → 이 두 방식을 조합 검토

### 2. 실패 복구

모든 에이전트에 공통적인 패턴:
- 생성 → 검증 실패 → 에러 메시지를 LLM에 피드백 → 재생성
- Uptempo의 `ClaimStateMachine` (RUNNING → RETRY_QUEUED)과 동일

### 3. 컨텍스트 관리

- 기존 스키마 파일을 LLM 컨텍스트에 포함하여 일관성 유지
- Aider의 Repo Map 접근법을 스키마 디렉토리에 적용 가능
