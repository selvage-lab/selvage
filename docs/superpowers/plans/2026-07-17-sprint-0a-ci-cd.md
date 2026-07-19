# Sprint 0a: CI/CD Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 영속적인 CI/CD 파이프라인 구축 — feature PR 게이트 + develop push 시 TestPyPI 자동 배포 + Docker 통합 테스트 + main merge 시 PyPI 정식 배포 및 GitHub Release 자동화.

**Architecture:** `main + develop + feature/*` 3-티어 브랜치 정책. GitHub Actions 워크플로우 2종 (`ci.yml` PR 게이트, `release.yml` 배포 파이프라인). 기존 자산인 `scripts/build_testpypi_image.sh`와 `e2e/dockerfiles/testpypi/Dockerfile`을 Actions에서 호출해 재사용. 모든 workflow는 `actionlint`로 로컬 검증 후 push.

**Tech Stack:** GitHub Actions, pytest, ruff, `python -m build`, twine, Docker, TestPyPI/PyPI, actionlint

## Global Constraints

- Python 3.10+ (pyproject.toml `requires-python = ">=3.10"`)
- Apache-2.0 license
- pytest config 위치: `pyproject.toml`의 `[tool.pytest.ini_options]`
- 의존성 정의: `pyproject.toml`의 `[project.optional-dependencies]` (dev, e2e 그룹)
- 모든 GitHub Actions workflow YAML은 push 전 `actionlint`로 검증
- GitHub Secrets에 추가 필요: `TEST_PYPI_API_TOKEN`, `PYPI_API_TOKEN`
- 기존 테스트 823개 통과가 회귀 베이스라인
- 커밋 메시지: Conventional Commits (`feat:`, `chore:`, `ci:`, `docs:` 등)

## File Structure

**Create:**
- `.github/workflows/ci.yml` — PR 게이트 (pytest, ruff, build, coverage)
- `.github/workflows/release.yml` — TestPyPI(develop) + PyPI(main) 배포
- `.github/branch-protection.yml` — 브랜치 보호 규칙 선언 (문서용)
- `BRANCHING.md` — 브랜치 정책 문서
- `scripts/validate-workflows.sh` — actionlint 실행 래퍼

**Modify:**
- `pyproject.toml` — pytest 플러그션 설정 수정 (`asyncio_mode`, `env` 등 Unknown config 해결)
- `CONTRIBUTING.md` — feature/develop/main 워크플로우 추가
- `.gitignore` — Python 캐시, coverage, build 산물 확장 (이미 대부분 있음, 검토만)

**Test:**
- `tests/test_pytest_config.py` (신규) — pytest config가 valid한지 검증
- 각 workflow는 actionlint + dry-run(act)으로 검증

---

## Task 1: pytest 플러그인 설정 안정화

**Why first:** selvage 점검에서 `pytest.ini_options`에 3개 Unknown config 경고가 있었음 (`asyncio_mode`, `env`, `asyncio_default_fixture_loop_scope`). 플러그인 누락이면 CI에서 비동기 테스트가 정상 동작 안 함. 이걸 먼저 잡아야 다음 task들의 CI가 안 터짐.

**Files:**
- Modify: `pyproject.toml` (pytest 설정 + optional-dependencies)
- Test: `tests/test_pytest_config.py` (신규)

**Interfaces:**
- Consumes: 기존 `pyproject.toml`의 pytest 설정
- Produces: `pytest tests/` 실행 시 Unknown config 경고 0건, 비동기 테스트 정상 동작

- [ ] **Step 1: 현재 pytest 설정과 경고 확인**

```bash
cd /Users/demin_coder/Dev/selvage
grep -A 20 '\[tool.pytest.ini_options\]' pyproject.toml
pytest tests/ --collect-only 2>&1 | grep -i "unknown config"
```

Expected: `asyncio_mode`, `env`, `asyncio_default_fixture_loop_scope` 3개 경고.

- [ ] **Step 2: 실패 테스트 작성**

```python
# tests/test_pytest_config.py
"""pytest 설정이 valid한지 검증."""
import configparser
from pathlib import Path

import pytest


def test_pytest_config_no_unknown_options():
    """pyproject.toml의 [tool.pytest.ini_options]가 모두 인식되는지 확인."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    # toml 파싱 (Python 3.11+ tomllib, 이전 버전은 tomli fallback)
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    pytest_config = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert pytest_config, "[tool.pytest.ini_options] must exist"

    # Known pytest keys (https://docs.pytest.org/en/stable/reference/reference.html#ini-options-ref)
    # 플러그인 키는 해당 플러그인 설치 시에만 인식됨
    plugin_keys = {
        "asyncio_mode": "pytest-asyncio",
        "asyncio_default_fixture_loop_scope": "pytest-asyncio",
        "env": "pytest-env",
    }
    installed_plugins = _get_installed_plugins()

    for key, plugin in plugin_keys.items():
        if key in pytest_config:
            assert plugin in installed_plugins, (
                f"'{key}' requires '{plugin}' but it's not installed. "
                f"Add '{plugin}' to [project.optional-dependencies] dev."
            )


def _get_installed_plugins() -> set[str]:
    """pip list에서 pytest-* 플러그인 추출."""
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "list", "--format=freeze"],
            capture_output=True, text=True, check=True,
        )
        return {
            line.split("==")[0].lower()
            for line in result.stdout.splitlines()
            if line.startswith("pytest-")
        }
    except Exception:
        return set()
```

- [ ] **Step 3: 테스트 실행 (FAIL 예상)**

```bash
pytest tests/test_pytest_config.py -v
```

Expected: FAIL with `AssertionError: 'asyncio_mode' requires 'pytest-asyncio' but it's not installed`.

- [ ] **Step 4: 플러그인을 dev 의존성에 추가**

`pyproject.toml`의 `[project.optional-dependencies]`에서 `dev` 그룹에 추가:

```toml
[project.optional-dependencies]
dev = [
    "pytest==8.3.5",
    "pytest-cov==6.0.0",
    "pytest-asyncio==0.24.0",  # 추가
    "pytest-env==1.1.3",        # 추가
    "pytest-timeout==2.3.1",    # 이미 있을 수도, 확인
    # ... 기존
]
```

설치:

```bash
pip install -e ".[dev]"
```

- [ ] **Step 5: 테스트 재실행 (PASS 예상)**

```bash
pytest tests/test_pytest_config.py -v
pytest tests/ --collect-only 2>&1 | grep -i "unknown config"
```

Expected: test PASS, Unknown config 경고 0건.

- [ ] **Step 6: 전체 테스트 스위트 회귀 확인**

```bash
pytest tests/ --timeout=300 2>&1 | tail -10
```

Expected: `823 passed, 18 skipped` (또는 그 이상). 실패 시 해당 테스트 원인 조사 후 이 task에 step 추가.

- [ ] **Step 7: 커밋**

```bash
git add pyproject.toml tests/test_pytest_config.py
git commit -m "fix: install missing pytest plugins (pytest-asyncio, pytest-env) to clear Unknown config warnings"
```

---

## Task 2: develop 브랜치 + 브랜치 정책 문서

**Files:**
- Create: `BRANCHING.md`
- Modify: `CONTRIBUTING.md` (브랜치 워크플로우 섹션 추가)

**Interfaces:**
- Consumes: 현재 main 브랜치
- Produces: `origin/develop` 브랜치, 브랜치 정책 문서

- [ ] **Step 1: develop 브랜치 생성 및 push**

```bash
cd /Users/demin_coder/Dev/selvage
git checkout main
git pull origin main
git branch develop
git push -u origin develop
git checkout main
```

Expected: `origin/develop` 생성, 로컬 `develop` 브랜치 존재.

- [ ] **Step 2: BRANCHING.md 작성**

```markdown
# Branching Policy

selvage는 3-티어 브랜치 모델을 사용합니다.

## 브랜치 구조

| 브랜치 | 용도 | 권한 |
|---|---|---|
| `main` | 프로덕션 릴리스. tag `vX.Y.Z`로 PyPI 정식 배포 | 관리자만 머지 |
| `develop` | Sprint 통합 지점. TestPyPI 자동 배포 | 관리자 + 핵심 기여자 |
| `feature/*` | 개별 task 작업. PR → develop | 누구나 생성 |

## 워크플로우

1. **feature 브랜치 생성**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/sprint-N-<topic>
   ```

2. **작업 + 커밋** (Conventional Commits 준수)

3. **PR 생성**: `feature/* → develop`
   - CI 자동 실행 (pytest, ruff, build)
   - 모두 통과 시 머지 가능

4. **develop → main PR** (Sprint 종료 시)
   - 관리자가 squash merge
   - main push → PyPI 정식 배포 + tag + GitHub Release 자동

## 네이밍 컨벤션

- `feature/sprint-N-<topic>` — Sprint N의 개별 task (예: `feature/sprint-0a-ci-yaml`)
- `fix/<topic>` — 버그 수정
- `chore/<topic>` — 설정, 문서, 의존성
- `release/vX.Y.Z` — 릴리스 준비 (필요 시)

## 보호 규칙 (GitHub Settings)

- `main`: PR required, status checks (CI) required, dismiss stale reviews
- `develop`: PR required, status checks (CI) required
- `feature/*`: 자유 (fork-equivalent)
```

- [ ] **Step 3: CONTRIBUTING.md에 브랜치 섹션 추가**

`CONTRIBUTING.md`의 적절한 위치에 다음 섹션 삽입:

```markdown
## 브랜치 워크플로우

[BRANCHING.md](./BRANCHING.md)를 참조하세요. 요약:

1. `develop`에서 `feature/<topic>` 브랜치 생성
2. 작업 후 PR → `develop` (CI 통과 필요)
3. Sprint 종료 시 `develop` → `main` PR (관리자 먼지)
```

- [ ] **Step 4: 검증**

```bash
git branch -a | grep -E "(main|develop)"
cat BRANCHING.md | head -20
```

Expected: `main`, `develop`, `origin/main`, `origin/develop` 모두 표시.

- [ ] **Step 5: 커밋**

```bash
git add BRANCHING.md CONTRIBUTING.md
git commit -m "docs: add 3-tier branching policy (main + develop + feature/*)"
git push origin develop
```

---

## Task 3: actionlint 설치 + 워크플로우 검증 스크립트

**Why:** workflow YAML을 push 전에 로컬 검증해야 CI 실패를 줄일 수 있음. 모든 workflow 변경 시 이 스크립트를 먼저 돌림.

**Files:**
- Create: `scripts/validate-workflows.sh`

**Interfaces:**
- Consumes: `.github/workflows/*.yml`
- Produces: exit code 0 (valid) 또는 1 (invalid), stderr에 오류

- [ ] **Step 1: actionlint 설치 확인 또는 설치**

```bash
which actionlint || brew install actionlint
actionlint --version
```

Expected: 버전 출력. 설치 안 됐으면 `brew install actionlint`.

- [ ] **Step 2: validate-workflows.sh 작성**

```bash
#!/usr/bin/env bash
# Validate all GitHub Actions workflows with actionlint.
# Run before pushing any workflow change: ./scripts/validate-workflows.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if ! command -v actionlint >/dev/null 2>&1; then
  echo "ERROR: actionlint not installed. Run: brew install actionlint" >&2
  exit 1
fi

echo "Validating GitHub Actions workflows..."
# shellcheck disable=SC2046
if actionlint $(find .github/workflows -name '*.yml' -o -name '*.yaml'); then
  echo "OK: all workflows valid"
else
  echo "FAIL: workflow validation failed (see errors above)" >&2
  exit 1
fi
```

- [ ] **Step 3: 실행 권한 + 테스트**

```bash
chmod +x scripts/validate-workflows.sh
# 현재는 workflow 파일이 없으므로, 빈 디렉토리 케이스:
ls .github/workflows/ 2>/dev/null || mkdir -p .github/workflows
./scripts/validate-workflows.sh
```

Expected: `.github/workflows/`가 비어 있어도 OK이거나, actionlint가 "no files" 에러. 어느 쪽이든 Task 4에서 실제 workflow로 다시 테스트.

- [ ] **Step 4: 커밋**

```bash
git add scripts/validate-workflows.sh
git commit -m "chore: add actionlint workflow validation script"
```

---

## Task 4: CI 워크플로우 (ci.yml) — PR 게이트

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: pyproject.toml (의존성), tests/, ruff config
- Produces: PR에서 pytest/ruff/build/coverage 실행. PR 상태 체크.

- [ ] **Step 1: ci.yml 작성**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: pyproject.toml

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Lint (ruff)
        run: ruff check .

      - name: Format check (ruff)
        run: ruff format --check .

      - name: Test with pytest
        run: pytest tests/ --cov --cov-report=xml --cov-report=term-missing --timeout=300 -n auto
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload coverage
        if: matrix.python-version == '3.12'
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  build:
    name: Build package
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build sdist + wheel
        run: python -m build

      - name: Check package metadata
        run: twine check dist/*

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ github.sha }}
          path: dist/
          retention-days: 7
```

- [ ] **Step 2: actionlint로 검증**

```bash
./scripts/validate-workflows.sh
```

Expected: `OK: all workflows valid`. 실패 시 에러 읽고 수정.

- [ ] **Step 3: feature 브랜치에서 PR 생성**

```bash
git checkout -b feature/sprint-0a-ci-workflow develop
git add .github/workflows/ci.yml
git commit -m "ci: add PR gate workflow (pytest, ruff, build, coverage) on Python 3.10-3.13 matrix"
git push -u origin feature/sprint-0a-ci-workflow
gh pr create --base develop --title "ci: add CI workflow (Sprint 0a Task 4)" --body "PR gate for pytest/ruff/build/coverage. Matrix Python 3.10-3.13."
```

- [ ] **Step 4: GitHub Actions 탭에서 워크플로우 실행 확인**

```bash
gh run watch
```

Expected: `test (3.10)`, `test (3.11)`, ..., `build` 모두 green. 실패 시 로그 읽고 수정 후 추가 커밋.

- [ ] **Step 5: PR 승인 + develop로 머지**

```bash
gh pr merge --squash --delete-branch
git checkout develop
git pull origin develop
```

---

## Task 5: TestPyPI 자동 배포 (release.yml part 1)

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `scripts/build_testpypi_image.sh` (Actions 호환성 점검)

**Interfaces:**
- Consumes: GitHub Secret `TEST_PYPI_API_TOKEN`, 기존 `scripts/build_testpypi_image.sh`
- Produces: `develop` push 시 TestPyPI로 selvage 패키지 자동 업로드

- [ ] **Step 1: TestPyPI 계정 + API token 확인**

```bash
# https://test.pypi.org/manage/account/token/ 에서 token 발급
# GitHub repo Settings → Secrets and variables → Actions → New repository secret:
#   Name: TEST_PYPI_API_TOKEN
#   Value: pypi-YYYY...
gh secret list | grep TEST_PYPI_API_TOKEN
```

Expected: `TEST_PYPI_API_TOKEN` 표시. 없으면 사용자가 수동 추가 필요.

- [ ] **Step 2: build_testpypi_image.sh Actions 호환성 점검**

```bash
cat scripts/build_testpypi_image.sh
# 스크립트가 절대 경로 / 하드코딩 없이 상대 경로로 동작하는지 확인
# 필요 시 수정 (CWD 기반으로)
```

수정 필요 시 예:

```bash
#!/usr/bin/env bash
# scripts/build_testpypi_image.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

VERSION=$(python -c "from selvage.__version__ import __version__; print(__version__)")
TAG="selvage-testpypi:${VERSION}"
LATEST_TAG="selvage-testpypi:latest"

echo "Building ${TAG}..."
docker build \
  --build-arg SELVAGE_VERSION="${VERSION}" \
  -t "${TAG}" -t "${LATEST_TAG}" \
  -f e2e/dockerfiles/testpypi/Dockerfile \
  .

echo "Built ${TAG} and ${LATEST_TAG}"
```

- [ ] **Step 3: release.yml 작성 (TestPyPI 잡만 우선)**

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [develop, main]
  workflow_dispatch:
    inputs:
      target:
        description: 'Override target (testpypi or pypi)'
        required: false
        default: ''
        type: choice
        options:
          - ''
          - testpypi
          - pypi

permissions:
  contents: write
  id-token: write

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    name: Build package
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build sdist + wheel
        run: python -m build

      - name: Check package metadata
        run: twine check dist/*

      - name: Extract version
        id: version
        run: |
          VERSION=$(python -c "from selvage.__version__ import __version__; print(__version__)")
          echo "version=${VERSION}" >> "$GITHUB_OUTPUT"
          echo "Building version ${VERSION}"

      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  testpypi:
    name: Publish to TestPyPI
    needs: build
    if: github.ref == 'refs/heads/develop' || (github.event_name == 'workflow_dispatch' && github.event.inputs.target == 'testpypi')
    runs-on: ubuntu-latest
    environment: testpypi
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish to TestPyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
          TWINE_REPOSITORY_URL: https://test.pypi.org/legacy/
        run: |
          pip install --upgrade twine
          twine upload --repository-url https://test.pypi.org/legacy/ dist/*

      - name: Wait for TestPyPI propagation
        run: sleep 30

      - name: Build and test Docker image
        run: |
          pip install -e ".[e2e]"
          ./scripts/build_testpypi_image.sh

      - name: Run e2e tests against TestPyPI image
        run: |
          docker run --rm \
            -e OPENAI_API_KEY="${{ secrets.OPENAI_API_KEY }}" \
            -e ANTHROPIC_API_KEY="${{ secrets.ANTHROPIC_API_KEY }}" \
            selvage-testpypi:latest \
            pytest e2e/ --timeout=600 -v
```

- [ ] **Step 4: actionlint 검증**

```bash
./scripts/validate-workflows.sh
```

- [ ] **Step 5: feature 브랜치에서 PR**

```bash
git checkout -b feature/sprint-0a-testpypi-release develop
git add .github/workflows/release.yml scripts/build_testpypi_image.sh
git commit -m "ci: add TestPyPI auto-release on develop push with Docker e2e validation"
git push -u origin feature/sprint-0a-testpypi-release
gh pr create --base develop --title "ci: TestPyPI auto-release (Sprint 0a Task 5)" --body "..."
```

- [ ] **Step 6: develop 머지 후 TestPyPI 자동 배포 확인**

```bash
gh pr merge --squash --delete-branch
git checkout develop && git pull origin develop
gh run watch
```

Expected: `build` → `testpypi` job green. TestPyPI(https://test.pypi.org/project/selvage/)에서 현재 버전 확인. Docker `selvage-testpypi:latest` 빌드 로그 확인. e2e 테스트 통과.

---

## Task 6: PyPI 정식 배포 + tag + GitHub Release

**Files:**
- Modify: `.github/workflows/release.yml` (pypi 잡 추가)

**Interfaces:**
- Consumes: GitHub Secret `PYPI_API_TOKEN`, 이전 `build` 잡의 artifacts
- Produces: `main` merge 시 PyPI 정식 업로드 + git tag `vX.Y.Z` + GitHub Release

- [ ] **Step 1: PyPI API token 확인**

```bash
# https://pypi.org/manage/account/token/에서 발급 (별도 token 권장)
gh secret list | grep PYPI_API_TOKEN
```

없으면 사용자 수동 추가.

- [ ] **Step 2: release.yml에 pypi 잡 추가**

`release.yml`의 `testpypi` 잡 뒤에 `pypi` 잡 추가:

```yaml
  pypi:
    name: Publish to PyPI + tag + GitHub Release
    needs: build
    if: github.ref == 'refs/heads/main' || (github.event_name == 'workflow_dispatch' && github.event.inputs.target == 'pypi')
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
          TWINE_REPOSITORY_URL: https://upload.pypi.org/legacy/
        run: |
          pip install --upgrade twine
          twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

      - name: Create git tag
        run: |
          VERSION="${{ needs.build.outputs.version }}"
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag "v${VERSION}"
          git push origin "v${VERSION}"

      - name: Extract changelog section
        id: changelog
        run: |
          VERSION="${{ needs.build.outputs.version }}"
          # CHANGELOG.md에서 vX.Y.Z 섹션 추출
          python scripts/extract_changelog.py "${VERSION}" > release_notes.md || echo "Release v${VERSION}" > release_notes.md
          cat release_notes.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: v${{ needs.build.outputs.version }}
          body_path: release_notes.md
          files: dist/*
          draft: false
          prerelease: ${{ contains(needs.build.outputs.version, '-') }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 3: extract_changelog.py 작성**

```python
# scripts/extract_changelog.py
"""CHANGELOG.md에서 특정 버전 섹션을 추출.

Usage: python scripts/extract_changelog.py 0.4.2
"""
import re
import sys
from pathlib import Path


def extract(version: str) -> str:
    changelog = Path(__file__).parent.parent / "CHANGELOG.md"
    if not changelog.exists():
        return f"Release v{version}"

    content = changelog.read_text(encoding="utf-8")
    # ## [0.4.2] - 2026-07-17 형식 또는 ## v0.4.2 형식 매칭
    pattern = rf"##\s*\[?v?{re.escape(version)}\]?(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    if not match:
        return f"Release v{version}"
    return match.group(1).strip()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_changelog.py <version>", file=sys.stderr)
        sys.exit(1)
    print(extract(sys.argv[1]))
```

- [ ] **Step 4: actionlint 검증 + PR**

```bash
./scripts/validate-workflows.sh
git checkout -b feature/sprint-0a-pypi-release develop
git add .github/workflows/release.yml scripts/extract_changelog.py
git commit -m "ci: add PyPI production release + tag + GitHub Release on main merge"
git push -u origin feature/sprint-0a-pypi-release
gh pr create --base develop --title "ci: PyPI production release (Sprint 0a Task 6)" --body "..."
```

- [ ] **Step 5: develop → main PR + 릴리스 검증**

```bash
gh pr merge --squash --delete-branch  # develop로 먼지
git checkout develop && git pull
git checkout main && git pull
# Sprint 0a 종료 시 develop → main PR:
gh pr create --base main --head develop --title "release: v0.4.2 — Reactivation Sprint 0a" --body "..."
gh pr merge --squash
gh run watch
```

Expected: `main` push → `build` → `pypi` job green. PyPI(https://pypi.org/project/selvage/)에 새 버전 표시. git tag `v0.4.2` push됨. GitHub Release 생성됨.

---

## Task 7: CHANGELOG 자동화 (commitizen)

**Files:**
- Modify: `pyproject.toml` (commitizen 설정)
- Modify: `CHANGELOG.md` (포맷 표준화)
- Create: `scripts/bump-version.sh`

**Interfaces:**
- Consumes: conventional commits 히스토리
- Produces: `cz bump` 실행 시 semantic versioning + CHANGELOG 자동 갱신

- [ ] **Step 1: commitizen을 dev 의존성에 추가**

`pyproject.toml`에 추가:

```toml
[project.optional-dependencies]
dev = [
    # ... 기존
    "commitizen==4.1.0",
]

[tool.commitizen]
name = "cz_conventional_commits"
version = "0.4.1"
version_files = [
    "selvage/__version__.py:__version__",
    "pyproject.toml:version",
]
tag_format = "v$version"
update_changelog_on_bump = true
changelog_file = "CHANGELOG.md"
changelog_incremental = true
annotated_tag = true
```

- [ ] **Step 2: bump-version.sh 작성**

```bash
#!/usr/bin/env bash
# Semantic version bump + CHANGELOG update.
# Usage: ./scripts/bump-version.sh [major|minor|patch]
# Default: patch (no args → commitizen이 changelog 기반 결정)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BUMP="${1:-}"
ARGS=()
if [ -n "$BUMP" ]; then
  ARGS+=("--increment" "$BUMP")
fi

# commitizen이 버전 결정 + CHANGELOG 갱신 + 커밋 + 태그
cz bump "${ARGS[@]}"

# push
git push --follow-tags origin "$(git rev-parse --abbrev-ref HEAD)"
```

- [ ] **Step 3: CHANGELOG.md 포맷 점검**

```bash
head -30 CHANGELOG.md
```

`## [0.4.2] - YYYY-MM-DD` 형식인지 확인. 아니면 포맷 조정 (commitizen 호환).

- [ ] **Step 4: 테스트 bump (dry-run)**

```bash
pip install -e ".[dev]"
cz version --dry-run --patch  # 또는 cz bump --dry-run
./scripts/bump-version.sh --dry-run
```

Expected: 다음 버전 표시 (0.4.1 → 0.4.2). 실제 커밋은 안 함.

- [ ] **Step 5: PR**

```bash
git checkout -b feature/sprint-0a-commitizen develop
git add pyproject.toml scripts/bump-version.sh CHANGELOG.md
git commit -m "chore: add commitizen for semantic versioning and changelog automation"
git push -u origin feature/sprint-0a-commitizen
gh pr create --base develop --title "chore: commitizen integration (Sprint 0a Task 7)" --body "..."
```

- [ ] **Step 6: develop 머지 후 dry-run으로 동작 확인**

```bash
gh pr merge --squash --delete-branch
git checkout develop && git pull
cz changelog --dry-run
```

Expected: CHANGELOG에 반영될 변경 사항 요약 출력.

---

## Self-Review

### 1. Spec coverage (마스터 플랜 v1.1 Sprint 0a 체크리스트)

체크리스트 14개 항목 → task 매핑:

- [x] develop 브랜치 존재, main과 동기화 → Task 2 Step 1
- [x] feature/* 브랜치 정책 문서화 → Task 2 Step 2 (BRANCHING.md)
- [x] ci.yml 존재 → Task 4 Step 1
- [x] ci.yml이 feature PR에서 pytest 실행 → Task 4 (matrix Python 3.10-3.13)
- [x] ruff check 실행 → Task 4 ci.yml `Lint (ruff)` step
- [x] python -m build 실행 → Task 4 `build` job
- [x] coverage 보고 → Task 4 `--cov-report` + codecov
- [x] release.yml 존재 → Task 5 Step 3
- [x] develop push 시 TestPyPI 업로드 → Task 5 `testpypi` job
- [x] build_testpypi_image.sh Actions 호출 → Task 5 `Build and test Docker image` step
- [x] selvage-testpypi:latest Docker 빌드 → Task 5 (스크립트가 태깅)
- [x] e2e 통합 테스트 Docker 실행 → Task 5 `Run e2e tests` step
- [x] main merge 시 PyPI + tag + Release 자동화 → Task 6 `pypi` job
- [x] pytest tests/ 0 failure → Task 1 Step 6

14/14 covered.

### 2. Placeholder scan

- "TBD", "TODO", "implement later" → 없음
- "Add appropriate error handling" → 없음. 모든 step에 실제 코드 포함.
- "Similar to Task N" → 없음. 코드 반복.

### 3. Type consistency

- `version` output (Task 5 build job) → Task 6 pypi job에서 `needs.build.outputs.version`로 사용. 일치.
- `TEST_PYPI_API_TOKEN`, `PYPI_API_TOKEN` — 일관된 이름 사용.
- `dist/` artifact — build job에서 upload, testpypi/pypi job에서 download. 일치.

### 4. 추가 발견

- Task 5의 Docker e2e는 GitHub Actions runner에 Docker 기본 설치를 가정. ubuntu-latest는 OK.
- Task 6의 `softprops/action-gh-release@v2`는 GITHUB_TOKEN으로 release 생성. 별도 token 불필요.
- 모든 workflow에 `concurrency` 그룹으로 중복 실행 방지.
- `permissions: contents: write, id-token: write`는 tag/release에 필요.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-17-sprint-0a-ci-cd.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 각 task마다 codex/claude 하위 에이전트 디스패치 (orca worktree), task 사이에 검증. 빠른 iteration. 특히 Task 4-6 (workflow YAML)은 독립적이라 병렬 가능.

**2. Inline Execution** — 현재 세션에서 executing-plans 스킬로 순차 실행. checkpoint마다 사용자 리뷰.

**권장**: Subagent-Driven + 병렬 디스패치. 단, Task 1(pytest 안정화)과 Task 2(develop 브랜치)는 선행 직렬. Task 3-7은 feature 브랜치로 병렬 가능.

**다음 단계**: 어느 execution 옵션으로 갈지 결정 후, Task 1부터 시작. 단, 이 plan은 Sprint 1 AST 리서치(claude 하위 에이전트 백그라운드 실행 중)와 독립적이라 병렬 진행 가능.
