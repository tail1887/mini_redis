# mini_redis (Python, docs-first)

Redis 발전 흐름(1~4세대)을 따라 범용 캐시 시스템을 단계적으로 만드는 프로젝트입니다.

## 현재 방식

- 초기 틀은 `Interface First` 방식으로 AI가 먼저 생성합니다.
- 팀은 생성된 틀을 바탕으로 4개 파트로 나눠 협업합니다.
- 구현 언어/스택은 Python 기준입니다.

## 기술 스택

- Language: `Python 3.12+`
- API: `FastAPI`
- Validation: `Pydantic v2`
- Redis Client: `redis-py`
- Test: `pytest`
- Load Test: `locust` 또는 `k6`

## 단계 로드맵

- 0단계: AI로 인터페이스/폴더/테스트 템플릿 + CI/CD 골격 생성
- 1단계: 기본 KV (`SET/GET/DEL/EXISTS`)
- 2단계: TTL (`EXPIRE/TTL/PERSIST`)
- 3단계: Prefix 무효화 + 운영 지표
- 4단계: 통합 회귀 + 부하 검증

## 단계별 AI 초기틀 원칙

- 모든 단계는 "문서 계약 확정 -> AI 초기틀 생성 -> 팀 검토 -> 구현" 순서로 진행합니다.
- 단계마다 AI가 코드 스켈레톤과 테스트 템플릿을 먼저 생성합니다.
- 팀은 생성물 검토 후 수정 목록을 합의한 다음 구현을 시작합니다.

### 단계별 AI 생성 범위

- 0단계: 프로젝트 골격, Dockerfile, CI/CD 파이프라인 초안, `/v1/health`
- 1단계: KV API/서비스/저장소 스켈레톤 + Unit/Integration 템플릿
- 2단계: TTL 모듈 스켈레톤 + 경계값/실패 테스트 템플릿
- 3단계: prefix 무효화/메트릭 스켈레톤 + 장애 시나리오 템플릿
- 4단계: 통합 회귀 테스트 세트 + 부하 테스트 스크립트 템플릿

## 비전공자 4분할 협업

- 파트 1: API/입력검증(요청-응답 형태 맞추기)
- 파트 2: 핵심 명령 구현(KV 기본 동작)
- 파트 3: TTL/무효화(만료와 삭제 정책)
- 파트 4: 테스트/문서(Unit/Integration/Failure/Load 결과 정리)

## 키 규칙

- 단계 1부터 모든 KV 키는 `<prefix>:<name>` 형식을 사용합니다.
- 예: `user:1`, `team:user:1`
- 금지 예: `user`, `user:`, `:1`, `user::1`

## 문서

- [기획](docs/01-product-planning.md)
- [아키텍처](docs/02-architecture.md)
- [API](docs/03-api-reference.md)
- [개발 가이드](docs/04-development-guide.md)
- [학습 가이드](docs/05-study-guide.md)
- [테스트 전략](docs/06-test-strategy.md)
- [릴리스 체크리스트](docs/07-release-checklist.md)
- [EC2 자동화 가이드](infra/README.md)

## Docker 실행

```bash
docker compose up -d --build
```

- Health check: `http://localhost:8000/v1/health`

## 배포 헬스체크 유틸

배포 후 헬스 확인은 아래 스크립트로 로컬/원격에서 동일하게 점검할 수 있습니다.

```bash
python -m scripts.deploy_health_check --url http://localhost:8000/v1/health --attempts 10 --interval 3 --timeout 2
```

## 발표 대시보드

- 페이지: `GET /dashboard`
- 실행 버튼 API: `POST /v1/dashboard/run-tests`
- 상태 조회 API: `GET /v1/dashboard/test-status`

`/dashboard`에서 버튼을 눌러 `pytest --json-report`를 실행하고, 페이즈별 테스트 요약이 실시간 갱신됩니다.

## 부하 테스트 템플릿

```bash
locust -f scripts/locustfile.py --headless -u 50 -r 10 -t 1m --host http://localhost:8000
```

```bash
k6 run scripts/load_test.js
```

## GitHub Actions 설정값 (CD-EC2)

아래 시크릿을 GitHub Repository Secrets에 등록해야 합니다.

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `EC2_APP_DIR`

EC2의 배포 디렉터리에는 `docker-compose.yml`과 `.env`(예: `.env.example` 참고)가 있어야 합니다.
