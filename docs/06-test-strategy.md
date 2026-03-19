# 06. 테스트 전략

## 1) 목적

- 0~5단계 전 구간에서 동일한 품질 게이트를 적용한다.
- 테스트를 Unit/Integration/Failure/Load로 명확히 구분한다.
- 단계 완료를 "기능 구현"이 아니라 "검증 완료"로 판단한다.

## 2) 테스트 분류 정의

- Unit: 함수/모듈 단위 규칙 검증
- Integration: API->Service->Store 전체 흐름 검증
- Failure: 입력 오류/경계/장애 상황 검증
- Load: 처리량(req/s), 지연(p95), 오류율 검증

## 3) 공통 게이트

진입 조건:
- 단계 목표와 완료 조건이 문서화됨
- API 계약 최신화 완료
- 해당 단계 AI 초기틀 생성 및 리뷰 완료

종료 조건:
- Unit/Integration/Failure/Load 결과 모두 기록
- Critical/High 결함 0건
- 잔여 리스크와 대응 계획 기록

## 4) 0~5단계 테스트 로드맵

| 단계 | Unit | Integration | Failure | Load | 성공 기준 | 리스크 | 완료 조건 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 공통 검증 유틸 | `health` 경로 | 필수값 누락 | 기준선 측정 | 실행 루틴 재현 가능 | 환경 편차 | 템플릿 확정 + CI/CD 성공 |
| 1 | `SET/GET/DEL/EXISTS`, 키 namespace/prefix 규칙 | 기본 KV 흐름 | 미존재/입력 오류, namespace 위반 | 기본 읽기/쓰기 | 핵심 명령 자동화 | 예외 누락 | 단계1 리포트 승인 |
| 2 | TTL 계산/해석 | 만료 전후 전환 | 음수/경계 시간 | TTL 다량 조회 | 시간 시나리오 안정 | 플래키 증가 | TTL 케이스 통과 |
| 3 | prefix 매칭 | 무효화 전후 상태 | 과삭제/과소삭제 | 무효화 혼합 부하 | 범위 안전성 입증 | 무효화 폭주 | 장애 시나리오 승인 |
| 4 | 회귀 핵심 규칙 | 통합 시나리오 | 복구 동작 | 최종 성능 검증 | 기준 성능 달성 | 병목 은닉 | 릴리스 후보 승인 |
| 5 | 락/AOF/스냅샷 로직 | 재시작 전후 상태 | 로그 손상/경합 상황 | 재시작 혼합 부하 | 복구 일관성 입증 | I/O 지연 증가 | 복구 시나리오 승인 |

단계 1 추가 체크:
- `key`가 `<prefix>:<name>` 형식을 지키는지 unit test로 검증
- 잘못된 prefix/query 입력이 `INVALID_INPUT`으로 매핑되는지 failure test로 검증

## 4-1) 단계별 AI 초기틀 검증 항목

단계 2 파트1 추가 체크:
- `expire`가 비양수 `seconds`를 `TTL_INVALID`로 거절하는지 확인
- `expire` unit test에서 기존 키/미존재 키 동작이 분리 검증되는지 확인

단계 4 파트3 추가 체크:
- CD 배포 후 `/v1/health`를 재시도 기반으로 검증하는지 확인
- 헬스체크 실패 시 이전 이미지 롤백 절차가 자동 수행되는지 확인
- 롤백 성공 시 서비스가 복구되더라도 배포 파이프라인은 실패로 종료되어 알림이 남는지 확인

단계 4 파트1/2/4 추가 체크:
- 회귀 테스트 묶음(`tests/test_regression_suite.py`)이 단계 1~3 핵심 플로우를 모두 커버하는지 확인
- 부하 스크립트(`scripts/locustfile.py`, `scripts/load_test.js`)가 동일한 주요 엔드포인트를 검증하는지 확인
- 성능 분석 시 req/s, p95, error rate를 공통 포맷으로 기록하는지 확인

단계 5 추가 체크:
- `tests/test_kv_store_concurrency.py`에서 병렬 요청 상태 일관성이 유지되는지 확인
- `tests/test_kv_store_durability.py`에서 AOF replay/스냅샷 복구가 재시작 후 동일 상태를 보장하는지 확인
- `tests/test_system_durability.py`에서 내구성 상태 API 계약이 유지되는지 확인

단계 3 파트4 추가 체크:
- `invalidate-prefix`가 sibling namespace를 삭제하지 않는지 failure test로 확인
- live key 미매치와 expired key cleanup이 삭제 개수 왜곡 없이 처리되는지 장애 테스트로 확인

- AI가 생성한 테스트 템플릿이 현재 API 계약과 일치하는지 확인
- 누락된 실패 케이스(경계값/잘못된 입력) 보강
- 기존 회귀 테스트와 충돌 여부 확인
- 리뷰 완료 전 구현 브랜치 머지 금지

## 5) 4인 협업 역할 분담(테스트 관점)

| 역할 | 책임 |
| --- | --- |
| PM | 단계별 게이트 일정/우선순위 조정 |
| TL | 테스트 자동화/품질 기준 기술 승인 |
| DEV | 테스트 가능한 코드 작성 및 실패 원인 수정 |
| QA | 테스트 설계/실행/리포트 및 게이트 판정 |

## 6) 결과 리포트 최소 항목

- 단계 번호
- 실행 일시와 환경
- 통과/실패 요약(Unit/Integration/Failure/Load)
- 주요 결함 및 조치
- 잔여 리스크와 다음 단계 권고

## 7) 성능 게이트 기준 (발표/릴리스 공통)

Load 결과는 아래 3개를 고정 지표로 기록한다.

- 처리량: `req/s` (높을수록 좋음)
- 지연: `p95 latency` (낮을수록 좋음)
- 안정성: `error rate` (낮을수록 좋음)

권장 최소 기준(로컬 기준선):

- no-cache: `req/s >= 25`, `p95 <= 40ms`, `error rate = 0%`
- with-cache: `req/s >= 500`, `p95 <= 5ms`, `error rate = 0%`
- 개선 배율: with-cache의 req/s가 no-cache 대비 `10x` 이상

## 8) 최신 성능 측정 결과 (기준선)

실행 명령:

```bash
python scripts/benchmark_db_vs_cache.py
```

실측 결과:

| 시나리오 | avg latency | p95 latency | req/s | error rate |
| --- | ---: | ---: | ---: | ---: |
| no-cache | 32.86ms | 33.49ms | 30.43 | 0.0% |
| with-cache | 1.37ms | 1.86ms | 728.74 | 0.0% |

판정:

- no-cache 기준 충족
- with-cache 기준 충족
- 처리량 개선 배율 약 `23.9x`로 개선 배율 기준 충족
