# 프로토콜 추천 엔진 설계

> 사용자는 프로토콜을 모른다. Uptempo가 유스케이스에서 프로토콜을 추천한다.

---

## 문제

- 대부분 사용자는 REST API 정도만 안다 (그것도 정확히는 아님)
- gRPC, AsyncAPI, Thrift, WebSocket 은 이름조차 생소
- "어떤 프로토콜이 필요한지" 스스로 판단할 수 없다
- 현재 Uptempo는 사용자가 프로토콜을 지정해야 함 → 병목

## 해결 방향: Ouroboros식 인터뷰 → 프로토콜 자동 추천

사용자가 유스케이스를 자연어로 설명하면,
Uptempo가 적합한 프로토콜 조합을 추천하고 스키마를 생성한다.

---

## 추천 흐름

```
사용자: "유저 알림 시스템 만들어줘"
                │
                ▼
        ┌───────────────┐
        │  인터뷰 엔진   │
        │  (소크라테스식)  │
        └───────┬───────┘
                │
    질문 1: "알림은 실시간으로 보여야 하나요?"
         → "네, 즉시 보여야 해요"
                │
    질문 2: "클라이언트가 브라우저인가요, 서버인가요?"
         → "브라우저요"
                │
    질문 3: "알림을 받기만 하나요, 읽음 확인도 보내나요?"
         → "읽음 확인도 보내야 해요"
                │
                ▼
        ┌───────────────┐
        │  프로토콜 추천  │
        └───────┬───────┘
                │
    추천 결과:
    ├── REST (OpenAPI)  → 알림 CRUD (생성/조회/삭제)
    ├── WebSocket       → 실시간 양방향 (알림 수신 + 읽음 확인)
    └── 이유: "브라우저 실시간 + 양방향 → WebSocket 필요"
                │
                ▼
        사용자 확인 → 스키마 생성
```

---

## 프로토콜 결정 규칙

### 유스케이스 → 프로토콜 매핑

| 시그널 | 추천 프로토콜 | 이유 |
|--------|-------------|------|
| CRUD 데이터 조작 | **REST (OpenAPI)** | 표준, 모든 클라이언트 호환 |
| 브라우저 실시간 + 단방향 | **SSE** | HTTP 기반, 간단, 재연결 내장 |
| 브라우저 실시간 + 양방향 | **WebSocket (AsyncAPI)** | 지속 연결, 양방향 메시지 |
| 내부 서비스 간 동기 호출 | **gRPC (Protobuf)** | 고성능, 타입 안전, 스트리밍 |
| 내부 서비스 간 비동기 이벤트 | **Kafka/이벤트 스키마** | 느슨한 결합, 이벤트 소싱 |
| 외부 서비스 이벤트 알림 | **Webhook** | 콜백 기반, SaaS 연동 표준 |
| IoT / 경량 디바이스 | **MQTT** | 저대역폭, 배터리 효율 |
| 복잡한 프론트 데이터 조합 | **GraphQL** | 오버페칭 방지, 유연한 쿼리 |

### 결정 트리

```
Q1: 클라이언트가 무엇인가?
├── 브라우저/모바일 앱 → Q2로
├── 내부 서버/마이크로서비스 → Q4로
├── IoT 디바이스 → MQTT
└── 외부 SaaS → Webhook

Q2: 실시간 통신이 필요한가?
├── 아니오 → REST (OpenAPI)
└── 예 → Q3으로

Q3: 양방향 통신이 필요한가?
├── 단방향 (서버→클라이언트) → SSE
└── 양방향 → WebSocket (AsyncAPI)

Q4: 통신 패턴은?
├── 요청-응답 (동기) → gRPC (Protobuf)
├── 이벤트 발행 (비동기) → 이벤트 스키마 (Kafka/NATS)
└── 둘 다 → gRPC + 이벤트 스키마
```

---

## 인터뷰 질문 설계

### 핵심 질문 (최소 3개, 최대 7개)

질문은 **기술 용어를 사용하지 않는다**. 사용자의 언어로 묻는다.

```yaml
questions:
  - id: client_type
    text: "이 API를 누가 사용하나요?"
    options:
      - "웹 브라우저 (프론트엔드)"      → browser
      - "모바일 앱"                      → mobile
      - "다른 백엔드 서버"               → server
      - "IoT 기기 (센서, 디바이스)"      → iot
      - "외부 서비스 (Stripe, Slack 등)" → external

  - id: realtime
    text: "데이터가 실시간으로 변해야 하나요?"
    options:
      - "아니요, 요청할 때만 보여주면 돼요"        → false
      - "네, 변경사항이 바로 보여야 해요"           → true
      - "일부만 실시간이에요 (예: 채팅은 실시간)"   → partial

  - id: direction
    condition: realtime == true || realtime == partial
    text: "실시간 부분에서, 데이터가 어느 방향으로 흐르나요?"
    options:
      - "서버 → 클라이언트 (알림, 피드)"             → server_to_client
      - "클라이언트 ↔ 서버 (채팅, 게임)"             → bidirectional
      - "잘 모르겠어요"                              → unknown → bidirectional

  - id: performance
    condition: client_type == server
    text: "서버 간 호출에서 가장 중요한 것은?"
    options:
      - "속도 (밀리초 단위 응답)"                    → speed → gRPC
      - "유연성 (다양한 언어로 호출)"                → flexibility → REST
      - "대용량 데이터 전송 (파일, 스트리밍)"         → streaming → gRPC_stream

  - id: async_events
    condition: client_type == server
    text: "서비스 간 이벤트 알림이 필요한가요?"
    example: "예: 주문 생성됨 → 결제 서비스에 알림"
    options:
      - "네, 이벤트 기반으로 동작해야 해요"           → true
      - "아니요, 직접 호출이면 충분해요"              → false

  - id: data_complexity
    condition: client_type == browser || client_type == mobile
    text: "화면마다 필요한 데이터가 많이 다른가요?"
    example: "목록 페이지는 이름만, 상세 페이지는 전부 필요"
    options:
      - "네, 화면마다 다른 데이터 조합이 필요해요"    → true → GraphQL 고려
      - "아니요, 대부분 비슷한 데이터에요"            → false → REST
```

### 모호성 점수 (Ouroboros 차용)

```
Ambiguity = 1 - Σ(clarity_i × weight_i)

client_type:   가중치 0.35  (가장 중요한 분기)
realtime:      가중치 0.25
direction:     가중치 0.20
performance:   가중치 0.10
async_events:  가중치 0.10

임계값: ≤ 0.2 → 프로토콜 추천 가능
        > 0.2 → 추가 질문 필요
```

---

## 추천 결과 포맷

인터뷰 완료 후, 사용자에게 보여줄 추천:

```markdown
## 🎯 추천 프로토콜

당신의 "유저 알림 시스템"에 다음 프로토콜을 추천합니다:

### ✅ REST API (OpenAPI 3.1)
- **용도**: 알림 생성, 조회, 삭제, 설정 변경
- **이유**: 표준적인 데이터 CRUD 작업

### ✅ WebSocket (AsyncAPI 3.0)
- **용도**: 실시간 알림 수신 + 읽음 확인
- **이유**: 브라우저에서 양방향 실시간 통신 필요

### ❌ gRPC — 불필요
- **이유**: 내부 서버 간 통신 없음 (브라우저 클라이언트)

### ❌ MQTT — 불필요
- **이유**: IoT 디바이스 아님

---
이대로 스키마를 생성할까요? [Y/n]
```

---

## 구현 단계

### Phase 1: 규칙 기반 추천 엔진
- 결정 트리 기반 (위 규칙)
- WORKFLOW.md에 질문 템플릿 추가
- Linear 이슈에 질문을 코멘트로 달고, 답변 기다림

### Phase 2: LLM 기반 인터뷰
- Ouroboros처럼 소크라테스식 자유 형식 인터뷰
- LLM이 이슈 설명에서 시그널 자동 추출
- 모호한 부분만 추가 질문

### Phase 3: 자동 감지
- 기존 코드베이스 분석 (Brownfield)
- `package.json`에 `socket.io` → WebSocket 필요 추론
- `*.proto` 파일 존재 → gRPC 유지
- 질문 없이 자동 추천

---

## 핵심 원칙

1. **기술 용어를 사용하지 않는다** — "gRPC가 필요한가요?" ❌ → "서버 간 속도가 중요한가요?" ✅
2. **추천에 이유를 단다** — "WebSocket 추천" ❌ → "브라우저에서 양방향 실시간이 필요하므로 WebSocket" ✅
3. **불필요한 것을 명시한다** — 왜 안 쓰는지도 설명해야 사용자가 배운다
4. **점진적 공개** — 처음엔 REST만, 필요 시 다른 프로토콜 추가 제안
