# uv 기반 개발 및 배포 가이드

> 🚀 **2025년 현재 Python CLI 도구 개발을 위한 현대적 워크플로우**

이 문서는 **uv**를 활용한 Selvage 개발 및 배포 과정을 다룹니다. uv는 Rust로 작성된 초고속 Python 패키지 관리자로, pip보다 10-100배 빠른 성능을 제공합니다.

## 🎯 uv를 선택하는 이유

- **⚡ 압도적인 속도**: pip 대비 10-100배 빠른 패키지 설치
- **🔧 올인원 도구**: pip + pipx + poetry + pyenv 역할 통합
- **🛡️ 안전한 격리**: CLI 도구별 독립 환경 자동 생성
- **🌐 크로스 플랫폼**: macOS/Linux에서 일관된 동작

## 1. uv 설치

### macOS/Linux
```bash
# 공식 설치 스크립트 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 또는 Homebrew (macOS)
brew install uv

# 설치 확인
uv --version
```

## 2. 개발 환경 설정

### 기존 pip 방식
```bash
# 기존 방식 (느림)
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,e2e]
```

### uv 방식 (권장)
```bash
# uv 방식 (빠름)
uv sync --dev --extra e2e

# 실행
uv run selvage --help
```

## 3. 주요 uv 명령어

### 개발 의존성 관리
```bash
# 모든 의존성 동기화
uv sync

# 개발 의존성 포함
uv sync --dev

# 특정 extra 포함
uv sync --extra e2e

# 모든 옵션 포함
uv sync --dev --extra e2e
```

### 패키지 실행
```bash
# uv 환경에서 실행
uv run selvage review

# 테스트 실행
uv run pytest tests/

# 빌드 실행
uv run python -m build
```

### 도구 관리 (pipx 대체)
```bash
# 전역 도구 설치
uv tool install ruff
uv tool install black

# Selvage 전역 설치 (사용자용)
uv tool install selvage

# 도구 목록 확인
uv tool list
```

## 4. 패키지 빌드 (uv 방식)

```bash
# 빌드 도구 설치 없이 바로 빌드
uv build

# 또는 기존 방식
uv run python -m build
```

**장점**:
- build, twine 등 별도 설치 불필요
- 가상환경 자동 관리
- 의존성 충돌 방지

## 5. 테스트 실행

### 단위 테스트
```bash
# 기본 테스트
uv run pytest tests/

# 커버리지 포함
uv run pytest tests/ --cov

# 병렬 실행
uv run pytest tests/ -n auto
```

### E2E 테스트
```bash
# E2E 의존성 포함 동기화
uv sync --dev --extra e2e

# E2E 테스트 실행
uv run pytest e2e/

# Docker 이미지 빌드 후 테스트
./scripts/build_testpypi_image.sh
uv run pytest e2e/ -v
```

## 6. 배포 과정 (uv + 기존 도구 조합)

### TestPyPI 배포
```bash
# 1. 빌드
uv build

# 2. TestPyPI 업로드 (twine 사용)
uv run twine upload --repository testpypi dist/*
```

### TestPyPI에서 설치 테스트

⚠️ **중요**: `uv tool install`에서 `--index-url`과 `--extra-index-url`을 함께 사용하면 일반 PyPI가 우선될 수 있어 잘못된 버전이 설치될 수 있습니다.

#### 방법 1: 가상환경에서 테스트 (권장)
```bash
# 테스트용 임시 환경
uv venv testpypi-env
source testpypi-env/bin/activate

# TestPyPI에서 설치 (--no-deps 사용)
uv pip install --index-url https://test.pypi.org/simple/ --no-deps selvage

# 의존성은 pyproject.toml을 이용해서 설치 (더 정확하고 편리)
uv pip install -e .

# 설치 확인
selvage --version  # TestPyPI 최신 버전 확인
selvage --help

# 정리
deactivate
rm -rf testpypi-env
```

#### 방법 2: 일회성 실행
```bash
# TestPyPI에서 일회성 실행 (의존성 자동 해결은 어려움)
uvx --index-url https://test.pypi.org/simple/ selvage --version
uvx --index-url https://test.pypi.org/simple/ selvage --help
```

**권장사항**: **방법 1**이 가장 안정적이며, TestPyPI 최신 버전을 정확히 설치합니다.

**uv tool install 한계**: `uv tool install`은 현재 `--no-deps` 옵션을 지원하지 않아서 TestPyPI 테스트에는 부적합합니다.

### 실제 PyPI 배포
```bash
# PyPI 업로드
uv run twine upload --repository pypi dist/*
```

## 7. 사용자 설치 안내 (최신 트렌드)

### 권장 설치 방법
```bash
# 1순위: uv (빠르고 현대적)
uv tool install selvage

# 2순위: pipx (안전하고 표준적)
pipx install selvage

# 3순위: pip (전통적, 주의사항 있음)
pip install selvage  # ⚠️ macOS/Linux에서 에러 가능
```

## 8. 개발 워크플로우 비교

### 기존 pip 워크플로우
```bash
# 환경 설정 (느림)
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,e2e]

# 실행
selvage review
pytest tests/
python -m build
```

### uv 워크플로우 (권장)
```bash
# 환경 설정 (빠름)
uv sync --dev --extra e2e

# 실행 (가상환경 자동 관리)
uv run selvage review
uv run pytest tests/
uv build
```

## 9. 문제 해결

### uv 관련 이슈
```bash
# uv 업데이트
uv self update

# 캐시 정리
uv cache clean

# 환경 초기화
rm -rf .venv
uv sync --dev --extra e2e
```

### 성능 비교
```bash
# pip 방식 (예시: ~30초)
time pip install requests pydantic

# uv 방식 (예시: ~3초)
time uv add requests pydantic
```

## 10. CI/CD 최적화

### GitHub Actions에서 uv 사용
```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v1

- name: Install dependencies
  run: uv sync --dev --extra e2e

- name: Run tests
  run: uv run pytest tests/

- name: Build package
  run: uv build
```

## 결론

uv는 Python 개발의 패러다임을 바꾸는 도구입니다. Selvage 개발에서:

- **개발 속도 향상**: 의존성 설치 시간 대폭 단축
- **환경 관리 간소화**: 가상환경 자동 생성/관리
- **도구 통합**: 여러 도구를 uv 하나로 대체
- **미래 대응**: 2025년 Python 생태계 트렌드 선도

**권장사항**: 새로운 개발자는 uv 워크플로우부터 시작하고, 기존 개발자는 점진적으로 마이그레이션하세요.