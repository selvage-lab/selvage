# Selvage End-to-End 테스트 가이드

이 문서는 selvage의 end-to-end (E2E) 테스트 환경 구성 및 실행 방법에 대해 설명합니다.

## 📋 목차

1. [개요](#개요)
2. [환경 설정](#환경-설정)
3. [테스트 실행 방법](#테스트-실행-방법)
4. [맥OS 환경 테스트](#macos-환경-테스트)
5. [Linux 컨테이너 테스트](#linux-컨테이너-테스트)
6. [CI/CD 통합](#cicd-통합)
7. [트러블슈팅](#트러블슈팅)

## 🎯 개요

Selvage E2E 테스트는 다음과 같은 시나리오를 검증합니다:

- **CLI 명령어 기능**: `selvage --help`, `selvage config`, `selvage models` 등
- **Git 통합**: 실제 Git repository에서의 diff 분석 및 리뷰
- **설정 관리**: 설정 파일 생성, 읽기, 쓰기
- **멀티플랫폼 호환성**: Linux 환경에서의 동작
- **오류 처리**: 잘못된 입력에 대한 적절한 오류 메시지

## ⚙️ 환경 설정

### 1. 기본 요구사항

```bash
# Python 3.10 이상
python --version

# Git (리뷰 기능 테스트용)
git --version

# 선택사항: Docker (Linux 컨테이너 테스트용)
docker --version
```

### 2. 의존성 설치

```bash
# 기본 의존성
pip install -e .

# E2E 테스트 전용 의존성
pip install -e ".[dev,e2e]"
```

### 3. 테스트 환경 설정

E2E 테스트는 격리된 환경에서 실행되므로 기존 설정에 영향을 주지 않습니다:

- **임시 설정 디렉토리**: 각 테스트마다 고유한 설정 디렉토리 사용
- **임시 Git repository**: 테스트용 Git repository 자동 생성
- **환경변수 격리**: 테스트 중 환경변수 백업 및 복원

## 🚀 테스트 실행 방법

### 기본 실행

```bash
pytest tests/e2e/ -v
```

### pytest 직접 사용

```bash
# 특정 테스트 파일 실행
pytest tests/e2e/test_e2e_cli_basic.py -v

# 특정 테스트 클래스 실행
pytest tests/e2e/test_e2e_cli_basic.py::TestSelvageCLIBasic -v

# 마커를 사용한 필터링
pytest tests/e2e/ -m "not container" -v  # 컨테이너 테스트 제외
pytest tests/e2e/ -m "e2e" -v            # E2E 테스트만 실행
```

## 🐳 Linux 컨테이너 테스트

### Docker 기반 테스트

```bash
# testcontainers 설치 (아직 안 했다면)
pip install testcontainers

# 컨테이너 테스트 실행
./scripts/run_e2e_tests.sh container

# 또는 pytest 직접 사용
pytest tests/e2e/test_e2e_container.py -v
```

### 수동 Docker 테스트

### 다양한 Linux 배포판 테스트

```bash
# Alpine Linux
docker run -it --rm -v $(pwd):/app -w /app alpine:latest sh
apk add --no-cache python3 py3-pip git
pip install -e .
python -m selvage --help

# CentOS
docker run -it --rm -v $(pwd):/app -w /app centos:8 bash
dnf install -y python3 python3-pip git
pip install -e .
python -m selvage --help
```

## 🔄 CI/CD 통합

### GitHub Actions 예시

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: [3.9, 3.10, 3.11]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r requirements-e2e.txt

      - name: Run E2E tests (without containers)
        run: |
          pytest tests/e2e/ -v -m "not container"

      - name: Run container tests (Ubuntu only)
        if: matrix.os == 'ubuntu-latest'
        run: |
          pytest tests/e2e/test_e2e_container.py -v
```

### 로컬 pre-commit 설정

```bash
# .pre-commit-config.yaml에 추가
repos:
  - repo: local
    hooks:
      - id: e2e-tests
        name: E2E Tests
        entry: ./scripts/run_e2e_tests.sh fast
        language: system
        pass_filenames: false
        always_run: true
```

## 🔧 트러블슈팅

### 일반적인 문제들

#### 1. Docker 관련 오류

```bash
# Docker 서비스 상태 확인
docker info

# Docker 권한 문제 (Linux)
sudo usermod -aG docker $USER
# 로그아웃 후 다시 로그인

# Docker Desktop 재시작 (macOS)
killall Docker && open /Applications/Docker.app
```

#### 2. testcontainers 설치 문제

```bash
# testcontainers 재설치
pip uninstall testcontainers
pip install testcontainers>=4.0.0

# 대체 설치 방법
pip install testcontainers[core]
```

#### 3. Python 경로 문제

```bash
# 현재 Python 경로 확인
which python
which pip

# 가상환경 확인
echo $VIRTUAL_ENV

# PATH 확인
echo $PATH
```

#### 4. Git 설정 문제

```bash
# Git 사용자 정보 설정
git config --global user.email "test@example.com"
git config --global user.name "Test User"

# Git 상태 확인
git status
```

### 디버깅 도구

#### 상세한 로그 출력

```bash
# pytest 상세 출력
pytest tests/e2e/ -v -s --tb=long

# 실패한 테스트만 재실행
pytest tests/e2e/ --lf -v

# 특정 테스트의 상세 정보
pytest tests/e2e/test_e2e_cli_basic.py::TestSelvageCLIBasic::test_selvage_help -v -s
```

#### 환경 정보 수집

```bash
# 시스템 정보
python --version
pip --version
git --version
docker --version

# 설치된 패키지 확인
pip list | grep -E "(selvage|pytest|testcontainers)"

# 환경변수 확인
env | grep -E "(VIRTUAL_ENV|PATH|SELVAGE)"
```

## 📈 성능 최적화

### 병렬 테스트 실행

```bash
# pytest-xdist 사용
pip install pytest-xdist
pytest ./e2e/ -n auto -v
```

### 테스트 캐싱

```bash
# pytest 캐시 사용
pytest ./e2e/ --cache-show
pytest ./e2e/ --cache-clear  # 캐시 초기화
```

### 선택적 테스트 실행

```bash
# 마지막 실패한 테스트만
pytest ./e2e/ --lf

# 실패한 테스트부터 시작
pytest ./e2e/ --ff

# 키워드로 필터링
pytest ./e2e/ -k "not container"
```

---

## 📞 지원

문제가 발생하거나 개선 사항이 있다면:

1. **이슈 생성**: GitHub Issues에 상세한 정보와 함께 문제 보고
2. **로그 첨부**: 오류 메시지와 환경 정보 포함
3. **재현 단계**: 문제를 재현할 수 있는 최소한의 단계 제공

테스트 환경 구성에 대한 추가 질문이나 개선 제안은 언제든 환영합니다!
