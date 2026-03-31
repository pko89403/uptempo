# Uptempo에 적용 가능한 아키텍처 패턴

외부 프로젝트에서 추출한, Uptempo 개발에 직접 참고할 수 있는 패턴들.

---

## 1. 단일 소스 → 멀티 타겟 생성 (TypeSpec 패턴)

### 현재 Uptempo 방식

```
자연어 이슈 → LLM → [OpenAPI, Protobuf, Thrift, AsyncAPI] 각각 독립 생성
```

### TypeSpec에서 배울 점: Emitter 플러그인 아키텍처

```
                  ┌─────────────────┐
                  │ 중간 표현 (IR)    │
                  │ = 내부 스키마 모델 │
                  └──────┬──────────┘
              ┌──────────┼──────────┬──────────┐
              ▼          ▼          ▼          ▼
         OpenAPI    Protobuf    Thrift    AsyncAPI
         Emitter    Emitter    Emitter    Emitter
```

### 적용 제안

LLM이 프로토콜별로 독립 생성하면 **불일치 위험**이 있음.
대안: LLM이 **중간 표현(내부 스키마 모델)** 을 먼저 생성 → 각 포맷으로 변환.

```python
# 예시: 내부 모델 → 멀티 타겟
class InternalSchema:
    services: list[ServiceDef]
    models: list[ModelDef]
    endpoints: list[EndpointDef]

class OpenApiEmitter:
    def emit(self, schema: InternalSchema) -> str: ...

class ProtoEmitter:
    def emit(self, schema: InternalSchema) -> str: ...
```

**장점**: 프로토콜 간 일관성 보장, LLM 호출 1회로 충분
**단점**: IR 설계 복잡도, 프로토콜별 세밀한 표현 손실 가능

---

## 2. 이슈→PR 에이전트 파이프라인 (SweepAI 패턴)

### SweepAI의 핵심 단계

```
1. 이슈 파싱 → 요구사항 추출
2. 코드베이스 분석 → 관련 파일 식별
3. 변경 계획 생성 → LLM에 구조화 프롬프트
4. 코드 생성 → XML 구조화 출력
5. 검증 → 테스트/린트 실행
6. 실패 시 → 에러를 LLM에 피드백 → 재생성
7. PR 생성 → 리뷰어 할당
```

### Uptempo에 적용

```
1. Linear 이슈 파싱 → 네트워크 스키마 요구사항 추출
2. 기존 스키마 분석 → 관련/의존 스키마 식별  ← 현재 미구현
3. WORKFLOW.md 렌더링 → 구조화 프롬프트
4. Codex 에이전트 실행 → 스키마 생성
5. 검증 → Spectral + buf lint
6. 실패 시 → 에러를 다음 턴에 피드백  ← ClaimStateMachine
7. PR 생성                              ← 현재 미구현
```

**추가 구현 필요**: 2번(기존 스키마 컨텍스트)과 7번(PR 자동 생성)

---

## 3. 컨텍스트 수집 패턴 (Aider의 Repo Map)

### Aider 방식

```python
# AST 파싱으로 코드베이스 요약
repo_map = {
    "src/auth.py": ["class AuthService", "def login()", "def verify_token()"],
    "src/user.py": ["class User", "class UserRepo", "def create_user()"],
}
# → LLM에 컨텍스트로 전달 (전체 코드보다 훨씬 적은 토큰)
```

### Uptempo 스키마 맵 적용

```python
# 기존 스키마 파일 요약
schema_map = {
    "openapi/user-service.yaml": {
        "paths": ["/users", "/users/{id}"],
        "schemas": ["User", "UserCreate", "UserUpdate"],
    },
    "proto/user.proto": {
        "services": ["UserService"],
        "messages": ["User", "CreateUserRequest"],
    },
}
# → LLM이 새 스키마 생성 시 기존 모델 재사용, 네이밍 일관성 유지
```

---

## 4. 검증-피드백 루프 (공통 패턴)

모든 AI 코딩 에이전트에서 발견되는 핵심 패턴:

```
생성 → 검증 → [성공] → 완료
              → [실패] → 에러 메시지를 LLM에 전달 → 재생성 (최대 N회)
```

### Uptempo 검증 체인 설계

```python
validators = [
    SpectralValidator(),     # OpenAPI 린트
    BufLintValidator(),      # Protobuf 린트
    ThriftCompiler(),        # Thrift 구문 검증
    AsyncApiValidator(),     # AsyncAPI 검증
    CrossSchemaConsistency() # 프로토콜 간 일관성 검증  ← 차별점
]

for validator in validators:
    result = validator.validate(workspace)
    if not result.ok:
        # 에러를 다음 에이전트 턴에 주입
        agent.feedback(result.errors)
```

**`CrossSchemaConsistency`가 핵심 차별점**:
- OpenAPI의 `User` 모델과 Protobuf의 `User` 메시지가 동일한 필드를 가지는지 검증
- 이 기능은 TypeSpec, openapi-generator 등 기존 도구에 없음

---

## 5. 워크스페이스 격리 패턴

### 비교

| 프로젝트 | 격리 방식 |
|---------|----------|
| SWE-agent | Docker 컨테이너 |
| Devin | 클라우드 IDE |
| Uptempo | 디렉토리 (WorkspaceManager) |

### 향후 확장 고려

```
현재: workspaces/{issue_id}/
         ├── openapi/
         ├── proto/
         ├── thrift/
         └── websocket/

확장안: Docker 기반 격리
  - buf, spectral, thrift compiler 등 도구 버전 고정
  - 이슈 간 의존성 충돌 방지
  - CI/CD 환경과 동일한 검증 환경 보장
```

---

## 6. 프로토콜별 통신 패턴 참고

Uptempo가 생성하는 각 프로토콜의 **실제 런타임 사용 패턴**:

### REST (OpenAPI)

```yaml
# Uptempo가 생성 → 실제로 이렇게 사용됨
paths:
  /users:
    get:    # 목록 조회 (Microcks 목 서버 자동 생성)
    post:   # 생성 (Specmatic 계약 테스트 자동 실행)
```

참고: Kong(43K⭐), Zilla를 API 게이트웨이로 사용

### gRPC (Protobuf)

```protobuf
// Uptempo가 생성 → buf lint로 검증 → protoc로 코드 생성
service UserService {
  rpc GetUser(GetUserRequest) returns (User);
}
```

참고: go-micro-boilerplate(276⭐), nestjs-microservices(369⭐)

### WebSocket (AsyncAPI)

```yaml
# Uptempo가 생성 → Centrifugo/Zilla에서 런타임 사용
channels:
  user/notifications:
    subscribe:
      message:
        $ref: '#/components/messages/UserNotification'
```

참고: Centrifugo(10K⭐), Microcks의 AsyncAPI 목킹

---

## 핵심 시사점 요약

| # | 패턴 | 출처 | Uptempo 적용 |
|---|------|------|-------------|
| 1 | 중간 표현(IR) → 멀티 타겟 | TypeSpec | 프로토콜 간 일관성 보장 |
| 2 | 이슈→PR 전체 파이프라인 | SweepAI | PR 자동 생성 구현 |
| 3 | Schema Map 컨텍스트 | Aider | 기존 스키마 인식 |
| 4 | 검증-피드백 루프 | 공통 | CrossSchemaConsistency |
| 5 | 워크스페이스 격리 | SWE-agent | Docker 기반 확장 |
| 6 | 런타임 통합 | Microcks+Zilla | 생성→목킹→테스트→프록시 |
