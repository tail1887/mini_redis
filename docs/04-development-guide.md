# 04. 개발 가이드

## 1) 운영 원칙

- 문서 우선: 구현 전 `01/02/03/06` 합의
- 단계 우선: 0 -> 1 -> 2 -> 3 -> 4 -> 5 순서 준수
- 품질 우선: 테스트 게이트 미통과 시 단계 종료 불가
- 동기화 우선: 코드 변경 시 문서/테스트 동시 갱신
- 시작 방식: 0단계는 **AI로 초기 틀 생성 후 시작**

## 2) 기본 개발 흐름

1. Interface First 방식으로 **AI로 초기 틀 생성 후 시작**(API/폴더/테스트 템플릿)
2. 팀이 초안 검토 후 수정사항 확정
3. 해당 단계 전용 AI 초기틀 추가 생성(1~5단계 반복)
4. 파트별 구현 진행(코드 + 테스트 동시 작성)
5. Unit/Integration/Failure 검증
6. 단계 4~5에서 Load/Recovery 검증 후 게이트 판정

## 3) 브랜치/커밋 규칙

- 브랜치: `feature/<name>`, `fix/<name>`, `docs/<name>`, `test/<name>`, `chore/<name>`
- 로컬 명령:
  - `uv venv`
  - `.venv\\Scripts\\activate`
  - `uv pip install -r requirements.txt`
  - `pytest -q`
  - `locust -f scripts/locustfile.py` (또는 `k6 run scripts/load_test.js`)
  - `python scripts/benchmark_db_vs_cache.py` (no-cache vs with-cache 비교 지표)
  - (대안) `python -m venv .venv && pip install -r requirements.txt`

## 4) 확장 계획별 4분할(기능 학습 중심)

### 공통 원칙

- 각 확장 단계 시작 전, AI가 먼저 스캐폴딩(코드/테스트/문서 초안)을 생성한다.
- 4분할은 "역할"이 아니라 "기능" 기준으로 나눈다.
- 각 담당자는 기능 구현 + 해당 기능 테스트를 직접 수행한다.
- 문서 보강은 단계 마지막 통합 임무에서 한 번에 수행한다.
- 최종 통합/머지 판단은 팀 리더(통합 전담)가 수행한다.

### 단계 0 (초기 틀) 테스트 결과

- 구조 준비 결과: 인터페이스/폴더/테스트 템플릿 생성 완료
- API 기동 결과: `GET /v1/health` 정상 응답(200)
- CI 기본 결과: `pytest` 실행 + 이미지 빌드 성공
- 최신 실행 결과: `pytest -q tests/test_health.py` -> `1 passed`

### 단계 1 (KV 기본) 분할

AI 틀잡기 임무:

- `set/get/del/exists` 라우터/서비스/스토어 함수 시그니처 생성
- 성공/실패 응답 예시와 기본 테스트 템플릿 생성


| 파트  | 담당자 | 기능           | 기능 설명       | 담당 임무                                  |
| --- | --- | ------------ | ----------- | -------------------------------------- |
| 파트1 | 박태정 | `set/get`    | 저장/조회 기본 흐름 | 요청 검증, 비정상 입력 처리, unit/integration 테스트 |
| 파트2 | 유중일 | `del/exists` | 삭제/존재확인 흐름  | 삭제 결과 규칙, 미존재 처리, unit 테스트             |
| 파트3 | 송영진 | 공통 에러/응답     | API 계약 통일   | 에러 코드 매핑, 응답 스키마 고정, failure 테스트       |
| 파트4 | 구름   | 키 네임스페이스     | 키 충돌 방지 기반  | 키 포맷 규칙 적용, prefix 검증 테스트              |


단계 1 키 네임스페이스 규칙:
- 키는 `<prefix>:<name>` 형식으로만 허용한다.
- `prefix`는 하나 이상의 namespace segment로 구성하고 `:`로 끝나는 형태로 해석한다.
- 키와 prefix 모두 공백, 빈 세그먼트(`user::1`, `user::`)를 허용하지 않는다.

단계 1 통합 임무(통합 전담):

- 파트1~4 결과를 하나의 브랜치에 통합
- 단계1 전체 회귀 테스트 실행 및 누락 테스트 보강
- `docs/03`, `docs/04`, `docs/06` 문서 보강
- 다음 단계 진입 여부 판정

단계 1 테스트 결과:

- Unit 결과: `SET/GET/DEL/EXISTS` 핵심 케이스 통과
- Failure 결과: 네임스페이스 규칙 위반(`user`, `user::1` 등) 차단 확인
- Integration 결과: API -> Service -> Store 흐름 정상 동작 확인
- 계약 결과: `INVALID_INPUT`, `KEY_NOT_FOUND` 응답 매핑 일치
- 최신 실행 결과: `31 passed` (`tests/test_kv_service_unit.py`, `tests/test_key_namespace.py`, `tests/test_error_responses.py`, `tests/test_kv_del_exists.py`, `tests/test_kv_templates.py`)

### 단계 2 (TTL) 분할

AI 틀잡기 임무:

- `expire/ttl/persist` 스켈레톤 및 경계값 테스트 뼈대 생성
- 시간 경계(만료 직전/직후) 시나리오 템플릿 생성


| 파트  | 담당자 | 기능          | 기능 설명        | 담당 임무                          |
| --- | --- | ----------- | ------------ | ------------------------------ |
| 파트1 | 박태정 | `expire`    | 키에 만료시간 부여   | 입력 검증, 음수/0 방어, unit 테스트       |
| 파트2 | 유중일 | `ttl`       | 남은 만료시간 조회   | `-2/-1/N` 규칙 구현, 경계 테스트        |
| 파트3 | 송영진 | `persist`   | 만료 제거        | 만료 제거 후 상태 검증, 회귀 테스트          |
| 파트4 | 구름   | 만료 정책 보조 로직 | 만료 상태 일관성 유지 | 만료 상태 전환/정리 보조 로직, failure 테스트 |

단계 2 파트1 `expire` 규칙:
- `seconds`는 양의 정수만 허용한다.
- `seconds <= 0` 요청은 `TTL_INVALID`로 거절한다.
- 존재하지 않는 키의 `expire` 요청은 성공 응답에서 `updated: false`를 반환한다.


단계 2 통합 임무(통합 전담):

- TTL 전체 플로우(`expire/ttl/persist`) 통합 검증
- 시간 경계 플래키 테스트 재실행 및 안정화
- `docs/03`, `docs/04`, `docs/06` 문서 보강
- 다음 단계 진입 여부 판정

단계 2 테스트 결과:

- Unit 결과: `expire/ttl/persist` 로직 케이스 통과
- 규칙 결과: `ttl = -2/-1/N` 규칙 검증 통과
- 경계 결과: 만료 직전/직후 시나리오 통과(플래키 재실행 포함)
- Failure 결과: `seconds <= 0` 요청 `TTL_INVALID` 처리 확인
- 최신 실행 결과: `26 passed, 3 skipped` (`tests/test_kv_expire_part1.py`, `tests/test_ttl.py`, `tests/test_kv_persist_part3.py`, `tests/test_ttl_failure_cleanup.py`, `tests/test_ttl_time_boundary_templates.py`, `tests/test_kv_ttl_scaffold.py`)

### 단계 3 (무효화/운영성) 분할

AI 틀잡기 임무:

- `invalidate-prefix`와 metrics 수집 모듈 초안 생성
- 과삭제/과소삭제 실패 케이스 테스트 템플릿 생성


| 파트  | 담당자 | 기능                  | 기능 설명                    | 담당 임무                |
| --- | --- | ------------------- | ------------------------ | -------------------- |
| 파트1 | 박태정 | `invalidate-prefix` | 특정 prefix 키 묶음 삭제        | prefix 검증, 삭제 범위 테스트 |
| 파트2 | 유중일 | cache metrics       | hit/miss/delete/error 집계 | 수치 집계 로직, API 노출 테스트 |
| 파트3 | 송영진 | 네임스페이스 규칙           | 키 충돌 방지                  | prefix 규칙 문서화, 예외 처리 |
| 파트4 | 구름   | 운영 안전장치             | 과삭제/과소삭제 방지              | 보호 조건 구현, 장애 테스트     |

단계 3 파트4 운영 안전장치:
- `invalidate-prefix`는 prefix와 정확히 매치되는 namespace의 live key만 삭제한다.
- live key가 하나도 매치되지 않으면 `PREFIX_INVALID`로 실패시켜 과소삭제를 바로 드러낸다.
- 만료된 키는 삭제 대상과 삭제 개수에서 제외해 운영 판단이 왜곡되지 않게 한다.


단계 3 통합 임무(통합 전담):

- 무효화/메트릭/보호 로직 통합 후 장애 시나리오 재검증
- 운영성 지표 정상 수집 여부 확인
- `docs/03`, `docs/04`, `docs/06` 문서 보강
- 다음 단계 진입 여부 판정

단계 3 테스트 결과:

- Integration 결과: `invalidate-prefix`, `GET /v1/metrics/cache` 동작 확인
- Failure 결과: 과삭제/과소삭제 방지 시나리오 통과
- 보호 로직 결과: live key 미매치 시 `PREFIX_INVALID` 처리 확인
- 운영성 결과: `hits/misses/deletes/invalidations/errors` 집계 검증 통과
- 최신 실행 결과: `14 passed, 2 skipped` (`tests/test_kv_invalidate_part1.py`, `tests/test_cache_metrics.py`, `tests/test_invalidate_failure_templates.py`, `tests/test_invalidate_prefix_safeguards.py`, `tests/test_kv_invalidate_metrics_scaffold.py`)

### 단계 4 (성능/릴리스 준비) 분할

AI 틀잡기 임무:

- 회귀 테스트 묶음/부하 테스트 스크립트 초안 생성
- 릴리스 체크리스트 템플릿 생성
- `GET /v1/system/readiness` 릴리스 게이트 엔드포인트 초안 생성


| 파트  | 담당자 | 기능          | 기능 설명     | 담당 임무                      |
| --- | --- | ----------- | --------- | -------------------------- |
| 파트1 | 박태정 | 부하 시나리오     | 처리량/지연 검증 | load 스크립트 작성, 기준선 수집       |
| 파트2 | 유중일 | 회귀 테스트      | 기존 기능 보호  | 단계1~3 회귀 케이스 고정            |
| 파트3 | 송영진 | 배포 점검       | 배포 안정성 확보 | CD/health 점검, 실패 복구 절차 테스트 |
| 파트4 | 구름   | 성능 분석 보조 로직 | 병목 원인 가시화 | 지표 수집 코드/스크립트, 성능 비교 테스트   |

단계 4 파트3 배포 점검 기준:
- 배포 직후 헬스체크를 단발성이 아닌 재시도(예: 최대 10회)로 검증한다.
- 헬스체크 실패 시 이전 이미지로 롤백한 뒤 재검증한다.
- 롤백 성공 시에도 배포 실패로 기록해 후속 점검이 가능하도록 한다.
- 복구 절차 테스트 템플릿(`tests/test_deploy_recovery_templates.py`)을 유지한다.


단계 4 통합 임무(통합 전담):

- 부하/회귀/배포 점검 결과 통합 및 릴리스 후보 판정
- 최종 성능 기준(req/s, p95, error rate) 충족 여부 확인
- `docs/01~06` 최종 문서 보강 및 일관성 검수
- 배포 파이프라인 최종 건전성 확인

단계 4 테스트 결과:

- 회귀 테스트 결과: 단계 1~3 핵심 시나리오 통과
- 배포 복구 테스트 결과: 헬스체크 재시도 + 실패 시 롤백 절차 확인
- 통합 테스트 실행 결과: `14 passed, 2 skipped` (`tests/test_regression_suite.py`, `tests/test_system_readiness.py`, `tests/test_deploy_health_check.py`, `tests/test_deploy_recovery_templates.py`, `tests/test_benchmark_endpoints.py`, `tests/test_dashboard_api.py`)
- 성능 측정 결과: `python scripts/benchmark_db_vs_cache.py` 실행으로 `req/s`, `p95 latency`, `error rate` 산출
- 부하 테스트 실행 결과: `locust -f scripts/locustfile.py --headless -u 50 -r 10 -t 30s --host http://127.0.0.1:8000 --only-summary`
- 부하 테스트 요약(aggregated): `req/s 150.94`, `failures 0.00%`, `p95 7ms`
- 판정 기준: `docs/06` 성능 게이트(7~8절)와 동일
- 성능 결과:
  - `no-cache: req/s 30.43, p95 33.49ms, error 0.0%`
  - `with-cache: req/s 728.74, p95 1.86ms, error 0.0%`

### 단계 5 (동시성/내구성) 분할

AI 틀잡기 임무:

- 스토어 동시성 보호(`thread-safe`)와 AOF/스냅샷 복구 스켈레톤 생성
- 레이스/재시작 복구 테스트 템플릿 생성
- `GET /v1/system/durability` 운영 상태 엔드포인트 초안 생성

| 파트  | 담당자 | 기능                         | 기능 설명               | 담당 임무                                      |
| --- | --- | -------------------------- | ------------------- | ------------------------------------------ |
| 파트1 | 박태정 | 동시성 보호                     | 프로세스 내부 레이스 방지      | store 락 정책 정리, 병렬 요청 안정성 테스트               |
| 파트2 | 유중일 | AOF 로그                     | 쓰기 연산 내구성 확보        | 변경 연산 기록/재생 로직 구현, 복구 테스트                  |
| 파트3 | 송영진 | 스냅샷 + 재시작 복구               | 복구 속도/안정성 보강        | 스냅샷 저장/로드 구현, AOF와 결합 시나리오 검증              |
| 파트4 | 구름   | 운영 가시성/가이드                | 내구성 상태 확인 및 운영 기준화 | `durability` API 검증, 배포/운영 체크리스트 문서화        |

단계 5 파트2/3 내구성 기준:
- 쓰기 연산은 AOF에 append 되어야 하며, 재시작 시 AOF replay로 상태를 복원한다.
- 스냅샷 주기(`snapshot_every`)가 설정된 경우 스냅샷 생성 후 AOF를 비워 복구 시간을 단축한다.
- 재시작 시 만료된 키는 복원 대상에서 제외해 stale 데이터가 재노출되지 않게 한다.

단계 5 통합 임무(통합 전담):

- 동시성/내구성 구현 통합 후 재시작 복구 시나리오 재검증
- `docs/03`, `docs/04`, `docs/06`, `docs/07` 문서 보강
- 단계 5 운영 가이드 승인 여부 판정

단계 5 테스트 결과:

- Unit 결과: store 락 적용 후 병렬 `set/get/expire/persist` 일관성 검증 통과
- Recovery 결과: 서버 재시작 후 AOF/스냅샷 기반 복구 시나리오 통과
- Integration 결과: `GET /v1/system/durability` 응답 계약 검증 통과
- 최신 실행 결과: `7 passed` (`tests/test_kv_store_durability.py`, `tests/test_system_durability.py`, `tests/test_system_readiness.py`)

## 5) 0~5단계 실행 로드맵


| 단계  | 실행 초점                        | 성공 기준        | 리스크      | 완료 조건                 |
| --- | ---------------------------- | ------------ | -------- | --------------------- |
| 0   | AI 초기 틀 + Docker CI/CD 골격 생성 | 초안 품질 검토 완료  | 초안 품질 편차 | 수정 목록 합의, 파이프라인 동작 확인 |
| 1   | 핵심 KV 구현                     | 계약 기반 동작 일치  | 입력 검증 누락 | 단계 1 테스트 통과           |
| 2   | TTL 기능 구현                    | 시간 경계 케이스 안정 | 플래키 테스트  | TTL 실패 시나리오 통과        |
| 3   | 무효화/운영성                      | 범위 삭제 안전성 확보 | 과삭제/과소삭제 | 통합+장애 시나리오 통과         |
| 4   | 통합/성능/릴리스                    | 성능 기준 충족     | 병목 미확인   | 회귀+부하 검증 완료           |
| 5   | 동시성/내구성 보강                   | 레이스 무결성 + 복구 보장 | 락 경합/파일 손상 | 복구+운영성 검증 완료          |


## 5-1) CI/CD (Docker + EC2) 최소 구성

- CI: `pytest`, 정적 검사, Docker 이미지 빌드
- CD: 이미지 레지스트리 push 후 EC2에서 `docker compose up -d`
- 배포 완료 기준: `/v1/health` 응답 정상

## 6) 리뷰 체크리스트

- API 계약/오류 규칙 위반 여부
- Unit/Integration/Failure/Load 테스트 누락 여부
- 단계 범위 초과 구현 여부
- 리스크 대응 및 후속 액션 기록 여부

## 7) 단계 게이트 산출물

- 완료 기능 목록
- 테스트 결과(Unit/Integration/Failure/Load)
- 잔여 리스크 및 완화 계획
- 다음 단계 진입 가능 여부

## 8) 통합 체크리스트

- 각 파트 PR이 단계 범위 내에서만 변경되었는지 확인
- 기능별 테스트(Unit/Failure) 통과 결과 첨부 여부 확인
- API 문서(`docs/03`)와 구현 응답 형식 일치 확인
- 단계별 AI 초기틀 대비 변경사항(추가/삭제/수정) 기록 확인
- 최종 통합 전 EC2 배포 파이프라인 건전성(최근 run) 확인

## 9) 단계별 종료조건(최종 게이트)

각 확장 단계(1~5)는 아래 4가지 조건을 모두 만족해야 종료된다.

- 리뷰 체크리스트(6번) 항목 100% 충족
- 단계 게이트 산출물(7번) 4개 모두 제출
- 통합 체크리스트(8번) 항목 100% 충족
- 5번 로드맵 표의 해당 단계 성공 기준 충족

미충족 항목이 1개라도 있으면 다음 단계로 진입하지 않는다.
