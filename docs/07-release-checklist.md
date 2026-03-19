# 07. Release Checklist (Stage 4~5)

릴리스 직전/직후 체크를 표준화하기 위한 템플릿입니다.

## 1) 사전 조건

- [ ] `master` 최신 동기화 완료
- [ ] 단계 1~3 기능 PR 모두 머지 완료
- [ ] 주요 문서(`docs/01~06`) 최신 상태 확인

## 2) 품질 게이트

- [ ] Unit/Integration/Failure 테스트 통과
- [ ] 회귀 테스트 묶음(`tests/test_regression_suite.py`) 통과
- [ ] 배포 헬스체크 유틸(`python -m scripts.deploy_health_check`) 성공

## 3) 성능 게이트

- [ ] Locust 또는 k6 스크립트로 부하 테스트 실행
- [ ] 기준 지표 기록
  - [ ] req/s
  - [ ] p95 latency
  - [ ] error rate
- [ ] 이전 기준 대비 퇴행(regression) 여부 확인

## 4) 배포 게이트

- [ ] CI(`test-and-build`) 성공 확인
- [ ] CD 실행 후 `/v1/health` 정상 확인
- [ ] CD 실패 시 롤백 절차 실행 가능 여부 확인

## 5) 런북/복구 준비

- [ ] 장애 대응 담당자 지정
- [ ] 복구 절차 템플릿 테스트(`tests/test_deploy_recovery_templates.py`) 기준 점검
- [ ] 실패 시 커뮤니케이션 채널/템플릿 준비

## 6) 동시성/내구성 게이트 (Stage 5)

- [ ] 동시성 테스트(`tests/test_kv_store_concurrency.py`) 통과
- [ ] 내구성 복구 테스트(`tests/test_kv_store_durability.py`) 통과
- [ ] 운영 상태 API(`GET /v1/system/durability`) 계약 확인
- [ ] 운영 환경 변수(`KV_PERSISTENCE_DIR`, `KV_SNAPSHOT_EVERY`) 점검
- [ ] 재시작 복구 데모(쓰기 -> 프로세스 재시작 -> 조회) 확인

## 7) 릴리스 승인 기록

- [ ] 승인자:
- [ ] 승인 시각:
- [ ] 릴리스 버전/커밋:
- [ ] 잔여 리스크:
