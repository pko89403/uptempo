# 멀티 프로토콜 API 도구

Uptempo가 생성하는 스키마들을 테스트·목킹·프록시하는 데 활용할 수 있는 도구들.

---

## 1. Microcks (CNCF Sandbox)

- **Repo**: https://github.com/microcks/microcks
- **Stars**: 1,850
- **언어**: Java
- **핵심**: **OpenAPI + AsyncAPI + GraphQL + gRPC** 목 서버 & 계약 테스트.

### 지원 프로토콜

| 프로토콜 | 스펙 형식 | 기능 |
|---------|----------|------|
| REST | OpenAPI 3.x, Swagger 2.x | 목 서버 + 계약 테스트 |
| gRPC | Protobuf | 목 서버 + 테스트 |
| GraphQL | GraphQL Schema | 목 서버 |
| 이벤트 | AsyncAPI 2.x/3.x | Kafka/MQTT/WebSocket 목 |
| SOAP | WSDL | 레거시 지원 |

### Uptempo 통합 시나리오

```
Uptempo 스키마 생성
  ├── openapi/*.yaml  ─┐
  ├── proto/*.proto    ─┤──→ Microcks Import ──→ 자동 목 서버
  └── websocket/*.yaml ─┘      │
                               ├── 계약 테스트 실행
                               └── API 시뮬레이션 제공
```

- Uptempo가 생성한 스키마를 Microcks에 자동 임포트하면 **즉시 목 서버**가 뜸
- 프론트엔드 팀은 스키마 생성 즉시 목 API로 개발 시작 가능
- CI/CD에서 스키마 변경 시 계약 테스트 자동 실행

---

## 2. Zilla (Aklivity)

- **Repo**: https://github.com/aklivity/zilla
- **Stars**: 680
- **언어**: Java
- **핵심**: 멀티 프로토콜 엣지 & 서비스 프록시. 선언적 설정으로 프로토콜 변환.

### 지원 프로토콜 매핑

```
REST (OpenAPI)  ──┐
gRPC (Protobuf) ──┤
SSE             ──┤──→ Zilla Proxy ──→ Apache Kafka
MQTT            ──┤
WebSocket       ──┘
```

### Uptempo에 참고할 점

- **선언적 프로토콜 바인딩**: YAML 설정으로 프로토콜 간 변환 정의
- Uptempo 스키마 기반으로 Zilla 설정 파일 자동 생성 가능
- OpenAPI 스키마 → REST 엔드포인트 → Kafka 토픽 자동 매핑

---

## 3. Specmatic

- **Repo**: https://github.com/specmatic/specmatic
- **Stars**: 364
- **언어**: Kotlin
- **핵심**: API 스펙을 **실행 가능한 계약 테스트**로 변환. No-code.

### 지원 스펙

- OpenAPI 3.x
- AsyncAPI
- gRPC/Protobuf
- GraphQL
- JDBC, Redis

### Uptempo에 참고할 점

- **스키마 = 테스트**: 별도 테스트 코드 없이 스펙 자체가 테스트
- 생성된 OpenAPI/AsyncAPI를 Specmatic에 넘기면 자동 테스트 실행
- **하위 호환성 검사**: 스키마 변경 시 기존 소비자 영향 분석
- CI/CD 통합으로 스키마 품질 게이트 구성

---

## 4. Centrifugo

- **Repo**: https://github.com/centrifugal/centrifugo
- **Stars**: 10,119
- **언어**: Go
- **핵심**: 실시간 메시징 서버. SSE + WebSocket + gRPC + HTTP-streaming + WebTransport.

### Uptempo에 참고할 점

- Uptempo의 WebSocket 스키마가 실제 런타임에서 어떻게 사용되는지의 레퍼런스
- **프로토콜 추상화 레이어**: 클라이언트는 WebSocket/SSE/HTTP 중 선택, 서버는 동일 로직
- PubSub 모델 기반 → AsyncAPI 스키마와 자연스럽게 매핑

---

## 5. Serverless Workflow / Synapse

- **Repo**: https://github.com/serverlessworkflow/synapse
- **Stars**: 303
- **언어**: C#
- **핵심**: 서버리스 워크플로우 관리. REST, gRPC, GraphQL, WebSocket, AsyncAPI, CloudEvents 통합.

### Uptempo에 참고할 점

- **멀티 프로토콜 오케스트레이션** 패턴
- CloudEvents 표준으로 이벤트 스키마 통일
- 워크플로우 DSL → Uptempo의 WORKFLOW.md와 유사한 선언적 접근

---

## 6. Standard Webhooks

- **Repo**: https://github.com/standard-webhooks/standard-webhooks
- **Stars**: 1,626
- **핵심**: Webhook 전송/수신 **표준 스펙**. OpenAPI + AsyncAPI 기반.

### Uptempo에 참고할 점

- Webhook 스키마 생성 시 이 표준을 따르면 호환성 보장
- 서명 검증 (`Webhook-Signature` 헤더) 스키마 정의 참고
- Svix (3,151⭐) 가 이 표준의 구현체

---

## 7. Svix Webhooks

- **Repo**: https://github.com/svix/svix-webhooks
- **Stars**: 3,151
- **언어**: Rust
- **핵심**: 엔터프라이즈급 Webhook 전송 서비스. Kafka/RabbitMQ/Redis 지원.

### Uptempo에 참고할 점

- Webhook 스키마의 실제 구현 참조
- 재시도 전략, 서명 검증, 이벤트 타입 정의 패턴
- OpenAPI로 Webhook 이벤트 타입을 정의하는 방식

---

## 통합 파이프라인 구상

```
                    Uptempo (스키마 생성)
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        OpenAPI 3.1   Protobuf v3   AsyncAPI 3.0
              │            │            │
    ┌─────────┤      ┌─────┤      ┌─────┤
    ▼         ▼      ▼     ▼      ▼     ▼
 Microcks  Specmatic  buf  gRPC  Microcks  asyncapi-gen
 (목서버)  (계약테스트) (lint) (코드) (목서버)  (코드/문서)
    │         │              │      │
    └─────────┴──────────────┴──────┘
                     │
              Zilla (런타임 프록시)
                     │
              ┌──────┼──────┐
              ▼      ▼      ▼
            REST   gRPC   Kafka/MQTT
```
