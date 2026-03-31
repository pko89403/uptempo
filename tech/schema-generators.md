# 멀티 프로토콜 스키마 생성 도구

Uptempo의 핵심 기능인 "단일 요청 → 여러 프로토콜 스키마 생성"과 관련된 도구들.

---

## 1. TypeSpec (Microsoft)

- **Repo**: https://github.com/microsoft/typespec
- **Stars**: 5,000+
- **언어**: TypeScript
- **핵심**: MS가 만든 API 설계 DSL. **하나의 소스에서 OpenAPI + Protobuf + JSON Schema 동시 생성**.

### Uptempo에 참고할 점

- **단일 소스 → 멀티 타겟** 철학이 Uptempo와 가장 유사
- TypeSpec은 DSL을 직접 작성하지만, Uptempo는 자연어(이슈) → LLM → 스키마로 생성
- TypeSpec의 **emitter 플러그인 구조** 참고 가능
  - `@typespec/openapi3` — OpenAPI 3.x 출력
  - `@typespec/protobuf` — Protobuf 출력
  - 커스텀 emitter 확장 가능

### 예시: 단일 TypeSpec → 멀티 출력

```typespec
@service({ title: "Pet Store" })
namespace PetStore;

model Pet {
  id: int32;
  name: string;
  tag?: string;
}

op listPets(): Pet[];
op createPet(@body pet: Pet): Pet;
```

→ OpenAPI YAML + Protobuf .proto + JSON Schema 동시 생성

---

## 2. OpenAPI Generator

- **Repo**: https://github.com/OpenAPITools/openapi-generator
- **Stars**: 25,000+
- **언어**: Java
- **핵심**: OpenAPI 스펙에서 **50+ 언어**의 클라이언트/서버 코드 생성. Protobuf 스키마도 지원.

### Uptempo에 참고할 점

- `protobuf-schema` 제너레이터로 OpenAPI → Protobuf 변환 가능
- 템플릿 기반 코드 생성 (Mustache 템플릿) → Uptempo의 Liquid 템플릿과 유사
- **검증 파이프라인**: 생성 후 lint/validate 단계가 내장
- CLI + 라이브러리 모드 모두 지원

### Uptempo와의 차이

| 관점 | OpenAPI Generator | Uptempo |
|------|-------------------|---------|
| 입력 | OpenAPI YAML/JSON | 자연어 (Linear 이슈) |
| 생성 주체 | 템플릿 엔진 | LLM (GPT-4o / Claude) |
| 출력 범위 | 주로 코드 (일부 스키마) | 스키마 파일 중심 |
| 검증 | 내장 | Spectral, buf lint 등 외부 |

---

## 3. NYTimes/openapi2proto

- **Repo**: https://github.com/nytimes/openapi2proto
- **Stars**: 1,000+
- **언어**: Go
- **핵심**: OpenAPI (Swagger) → Protobuf v3 + gRPC 서비스 정의 변환.

### Uptempo에 참고할 점

- OpenAPI ↔ Protobuf 매핑 규칙 참고
  - `string` → `string`, `integer` → `int32`, `number` → `float`
  - `$ref` → `message` 중첩
  - HTTP 메서드 → gRPC 서비스 메서드
- **파이프라인 조합 가능**: Uptempo가 OpenAPI를 먼저 생성 → openapi2proto로 Protobuf 자동 파생

---

## 4. AsyncAPI Generator

- **Repo**: https://github.com/asyncapi/generator
- **Stars**: 1,037
- **언어**: JavaScript
- **핵심**: AsyncAPI 정의에서 문서, 코드 등 생성. 템플릿 확장 가능.

### Uptempo에 참고할 점

- Uptempo의 `WebSocketGenerator`가 AsyncAPI 3.0을 출력하므로 직접 연동 가능
- 생성된 AsyncAPI를 AsyncAPI Generator에 넘기면 → 문서, 클라이언트 코드 자동 생성
- **템플릿 레지스트리** 구조 참고: 커뮤니티가 템플릿을 기여하는 확장 모델

### AsyncAPI 관련 도구 체인

| 도구 | 역할 |
|------|------|
| `asyncapi/cli` (268⭐) | AsyncAPI 검증/번들/변환 |
| `asyncapi/protobuf-schema-parser` | AsyncAPI에 Protobuf 페이로드 스키마 통합 |
| `asyncapi/openapi-schema-parser` | AsyncAPI에 OpenAPI 스키마 참조 |

---

## 5. Redocly CLI

- **Repo**: https://github.com/Redocly/redocly-cli
- **Stars**: 1,422
- **언어**: TypeScript
- **핵심**: OpenAPI/AsyncAPI 린트 + 번들 + 문서 생성 CLI.

### Uptempo에 참고할 점

- Spectral의 대안으로 OpenAPI/AsyncAPI 검증에 사용 가능
- **커스텀 린트 룰** 정의 가능 → Uptempo 스키마 품질 기준 설정
- `arazzo` (API 워크플로우 스펙) 지원 → 여러 API 간 연동 시나리오 정의

---

## 비교 요약

```
                    ┌─────────────────┐
                    │  자연어 (이슈)   │ ← Uptempo 입력
                    └────────┬────────┘
                             │ LLM
                    ┌────────▼────────┐
                    │ Uptempo 스키마   │ ← 현재 위치
                    │ 생성 엔진        │
                    └──┬──┬──┬──┬─────┘
          ┌────────────┘  │  │  └────────────┐
          ▼               ▼  ▼               ▼
    ┌──────────┐  ┌──────┐ ┌───────┐  ┌──────────┐
    │ OpenAPI  │  │Proto │ │Thrift │  │ AsyncAPI │
    │ 3.1 YAML │  │buf v3│ │ IDL   │  │ 3.0 YAML │
    └────┬─────┘  └──┬───┘ └───────┘  └────┬─────┘
         │           │                      │
         ▼           ▼                      ▼
   openapi-gen   buf/protoc          asyncapi-gen
   (코드 생성)   (코드 생성)          (코드/문서)
```

### 전략적 고려

1. **TypeSpec과의 차별점**: TypeSpec은 사람이 DSL을 작성 → Uptempo는 AI가 직접 생성
2. **후속 파이프라인 연동**: 생성된 스키마를 openapi-generator, asyncapi-generator에 연결하면 코드까지 자동 생성 가능
3. **검증 도구 통합**: Spectral + buf lint + Redocly CLI를 검증 레이어에 조합
