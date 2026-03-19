# 03. API 레퍼런스

## 1) 공통 규약

- Base Path: `/v1`
- Content-Type: `application/json`
- 성공 응답:

```json
{ "success": true, "data": {} }
```

- 실패 응답:

```json
{ "success": false, "error": { "code": "ERROR_CODE", "message": "..." } }
```

- 입력 검증 실패: HTTP `400`, `INVALID_INPUT`
- 미존재 키 조회 실패: HTTP `404`, `KEY_NOT_FOUND`
- 예상치 못한 서버 오류: HTTP `500`, `INTERNAL_ERROR`

### 표준 에러 코드
- `INVALID_INPUT`
- `KEY_NOT_FOUND`
- `TTL_INVALID`
- `PREFIX_INVALID`
- `INTERNAL_ERROR`

## 2) 0~5단계 엔드포인트 로드맵

| 단계 | 엔드포인트 | 설명 |
| --- | --- | --- |
| 0 | `GET /v1/health` | 기본 상태 확인 |
| 1 | `POST /kv/set`, `GET /kv/get`, `DELETE /kv/del`, `GET /kv/exists` | 핵심 KV |
| 2 | `POST /kv/expire`, `GET /kv/ttl`, `POST /kv/persist` | TTL/만료 |
| 3 | `POST /kv/invalidate-prefix`, `GET /metrics/cache` | 범위 무효화/지표 |
| 4 | `GET /system/readiness` | 릴리스 준비 상태 |
| 5 | `GET /system/durability` | 내구성 설정/파일 상태 확인 |

원칙:
- 각 단계 시작 전에 AI가 해당 단계 엔드포인트 스캐폴딩과 테스트 템플릿을 먼저 생성한다.
- 구현은 생성된 초안 검토/수정 후 진행한다.

## 3) 엔드포인트 요약

### 3.0 `GET /v1/health`
응답: `{ "success": true, "data": { "status": "ok" } }`

### 3.1 `POST /v1/kv/set`
요청: `{ "key": "user:1", "value": "kim" }`  
응답: `{ "success": true, "data": { "stored": true } }`

### 3.2 `GET /v1/kv/get?key={key}`
응답: `{ "key": "...", "value": "..." }` 또는 `KEY_NOT_FOUND`

### 3.3 `DELETE /v1/kv/del?key={key}`
응답: `{ "deleted": true|false }`

### 3.4 `GET /v1/kv/exists?key={key}`
응답: `{ "exists": true|false }`

#### 단계 1 기본 응답 예시 (AI 틀)

`POST /v1/kv/set` 성공:

```json
{ "success": true, "data": { "stored": true } }
```

`GET /v1/kv/get` 실패(키 없음):

```json
{ "success": false, "error": { "code": "KEY_NOT_FOUND", "message": "key not found" } }
```

`GET /v1/kv/get` 실패(입력 오류):

```json
{ "success": false, "error": { "code": "INVALID_INPUT", "message": "key is required" } }
```

### 3.5 `POST /v1/kv/expire`
요청: `{ "key": "user:1", "seconds": 60 }`  
응답: `{ "updated": true|false }`
실패: `seconds <= 0` 이면 HTTP `400`, `TTL_INVALID`

### 3.6 `GET /v1/kv/ttl?key={key}`
응답: `{ "success": true, "data": { "ttl": -2|-1|N } }`  
규칙: `-2`(미존재/만료), `-1`(만료 없음), `N>=0`(남은 초)
설명: 미존재/만료도 실패가 아니라 성공 응답으로 처리하고 `ttl = -2`를 반환한다.

### 3.7 `POST /v1/kv/persist`
요청: `{ "key": "user:1" }`  
응답: `{ "updated": true|false }`

### 3.8 `POST /v1/kv/invalidate-prefix`
요청: `{ "prefix": "user:" }`  
응답: `{ "deletedCount": 2 }`
실패: live key가 하나도 매치되지 않으면 HTTP `400`, `PREFIX_INVALID`

### 3.9 `GET /v1/metrics/cache`
응답: `{ "success": true, "data": { "hits": 10, "misses": 3, "deletes": 2, "invalidations": 1, "errors": 0 } }`
설명: `hits`는 조회/존재확인 성공 수, `misses`는 조회/존재확인 실패 수, `deletes`는 실제 삭제 성공 수, `invalidations`는 prefix 무효화 성공 수, `errors`는 입력/서버 오류 수를 뜻한다.

### 3.10 `GET /v1/system/readiness`
응답: `{ "success": true, "data": { "ready": true|false, "stage": 5, "summary": "..." } }`
설명: `RELEASE_READY=true` 환경 변수가 설정되어야 `ready=true`가 된다.

### 3.11 `GET /v1/system/durability`
응답: `{ "success": true, "data": { "enabled": true|false, "aofPath": "...", "snapshotPath": "...", "aofExists": true|false, "snapshotExists": true|false, "snapshotEvery": N } }`
설명: 내구성 모드(AOF/스냅샷) 활성 여부와 파일 상태를 반환한다.

## 4) 입력 검증 규칙

- `key`: 필수, 네임스페이스 포맷 `<prefix>:<name>` 필수
- `key` 세부 규칙: 최소 1개의 `:` 포함, 앞/뒤 세그먼트 비어 있으면 안 됨, 공백 금지
- `value`: 문자열
- `seconds`: 양의 정수
- `prefix`: 필수, 빈 문자열 금지, `:`로 끝나야 함, 빈 세그먼트/공백 금지
- `invalidate-prefix`: prefix와 정확히 일치하는 namespace의 live key만 삭제하고, 만료된 키는 삭제 개수에서 제외

예시:
- 허용 `key`: `user:1`, `team:user:1`
- 거부 `key`: `user`, `user:`, `:1`, `user::1`
- 허용 `prefix`: `user:`, `team:user:`
- 거부 `prefix`: `user`, `:`, `user::`
- 거부 `seconds`: `0`, `-1`

## 5) 단계별 API 게이트(성공 기준/리스크/완료 조건)

| 단계 | 성공 기준 | 리스크 | 완료 조건 |
| --- | --- | --- | --- |
| 0 | 공통 응답/에러 스키마 고정 | 팀별 포맷 불일치 | 기본 엔드포인트가 공통 스키마 준수 |
| 1 | KV 계약 확정 | 입력 검증 누락 | 정상/오류 예시 문서화 완료 |
| 2 | TTL 규칙 합의 | 만료 해석 혼선 | 경계 케이스 계약 명시 |
| 3 | prefix 안전 규칙 명시 | 광범위 삭제 위험 | 빈 prefix 방지 포함 |
| 4 | readiness 판정 기준 확정 | 상태 판단 모호 | 릴리스 기준 필드 문서화 |
| 5 | durability 상태 노출 계약 확정 | 복구 상태 가시성 부족 | 내구성 상태 필드 문서화 |

## 6) 테스트 분류 연계

- Unit: 파라미터 검증, TTL 규칙, prefix 검증
- Integration: 엔드포인트별 요청/응답 계약
- Failure: 잘못된 입력, 미존재/만료, 위험한 무효화 요청
- Load: 단계 4에서 req/s, p95, error rate 검증

## 7) 4인 협업 역할 분담(API 관점)

| 역할 | 책임 |
| --- | --- |
| PM | API 변경 일정/릴리스 범위 조율 |
| TL | API/도메인 경계 및 호환성 결정 |
| DEV | 엔드포인트 구현 및 계약 준수 |
| QA | 계약 기반 테스트/게이트 운영 |
