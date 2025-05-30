# Selvage E2E (End-to-End) 테스트 가이드

이 디렉토리에는 Selvage의 전체 워크플로우를 검증하는 E2E 테스트들이 포함되어 있습니다.

## 📋 테스트 구조

### 🔧 **기본 E2E 테스트**

- `test_e2e_container_full.py`: 완전한 컨테이너 기반 E2E 테스트
  - 설치부터 리뷰까지 전체 워크플로우
  - Python 버전별 호환성 테스트
  - Python 3.9 비호환성 테스트
  - 설정 관리 테스트

### 📦 **TestPyPI 통합 테스트** ⭐ **NEW**

- `e2e_testpypi_integration.py`: TestPyPI 배포 후 패키지 검증 테스트
  - TestPyPI에서 실제 패키지 설치 및 기능 테스트
  - 실제 사용자 환경과 동일한 설치 과정 검증
  - **하드코딩된 의존성 관리**: 안정적인 테스트 실행을 위해 의존성 목록을 명시적으로 관리
  - CLI 기능, 설정 관리, 모듈 import 완성도 테스트
  - 다양한 Python 버전에서의 호환성 검증 (Python 3.10-3.13)
  - **사용 시점**: TestPyPI에 패키지 업로드 후, 실제 PyPI 배포 전

**주요 개선사항**:

- 🔧 **프로젝트 마운트**: 현재 디렉토리를 컨테이너에 마운트하여 실제 프로젝트 설정 사용
- 📋 **안정적인 의존성**: 하드코딩된 의존성 목록으로 shell escaping 문제 해결 및 안정성 향상
- 🐍 **CI/CD 최적화**: 복잡한 스크립트 없이 명시적 의존성으로 환경 차이 최소화
- 🛡️ **일관성 보장**: 테스트 환경과 실제 프로덕션 환경의 100% 일치

**의존성 업데이트 가이드**:

- `pyproject.toml`의 `dependencies` 섹션 변경 시, 테스트 파일의 의존성 목록도 동일하게 업데이트 필요
- 변경 위치: `_install_selvage_from_testpypi()` 함수 및 관련 테스트 함수들

### 🚨 **에러 시나리오 테스트**

- `test_e2e_error_scenarios.py`: 예외 상황 및 에러 처리 테스트
  - 잘못된 API 키 처리
  - 빈 저장소 처리
  - Git 저장소가 아닌 디렉토리 처리
  - 대용량 파일 처리
  - 잘못된 모델 설정 처리

### 🔄 **현실적인 워크플로우 테스트**

- `test_e2e_realistic_workflows.py`: 실제 개발자 사용 시나리오 테스트
  - 다중 언어 파일 리뷰 워크플로우
  - Git 브랜치 워크플로우 통합
  - 점진적 개발 과정 시뮬레이션
  - 실제 버그 수정 시나리오

### 🛠️ **기본 CLI 테스트**

- `test_e2e_cli_basic.py`: 기본적인 CLI 기능 테스트

## 🚀 실행 방법

### **전체 E2E 테스트 실행**

```bash
cd e2e
pytest
```

### **특정 테스트 파일 실행**

```bash
# 기본 컨테이너 테스트만
pytest test_e2e_container_full.py

# TestPyPI 통합 테스트만 (TestPyPI 업로드 후)
pytest test_e2e_testpypi_integration.py

# 에러 시나리오 테스트만
pytest test_e2e_error_scenarios.py

# 현실적인 워크플로우 테스트 (시간이 오래 걸림)
pytest test_e2e_realistic_workflows.py
```

### **TestPyPI 배포 워크플로우** 🎯

TestPyPI에 패키지를 업로드한 후 다음 순서로 테스트하세요:

```bash
# 1. TestPyPI에 패키지 업로드
python -m build
twine upload --repository testpypi dist/*

# 2. TestPyPI 통합 테스트 실행
cd e2e
pytest test_e2e_testpypi_integration.py -v

# 3. 특정 테스트만 실행 (옵션)
pytest test_e2e_testpypi_integration.py::test_testpypi_installation_basic
pytest test_e2e_testpypi_integration.py::test_testpypi_full_integration_suite

# 4. Python 버전별 호환성 테스트 (시간이 오래 걸림)
pytest test_e2e_testpypi_integration.py::test_testpypi_python_compatibility -v
```

### **마커별 테스트 실행**

```bash
# 빠른 테스트만 (slow 마커 제외)
pytest -m "not slow"

# 에러 시나리오 테스트만
pytest -m "error_scenario"

# 워크플로우 테스트만
pytest -m "workflow"

# 컨테이너 테스트만
pytest -m "container"
```

### **특정 테스트 함수 실행**

```bash
# 설정 테스트만
pytest test_e2e_container_full.py::test_selvage_config_in_container

# Python 호환성 테스트만
pytest test_e2e_container_full.py::test_selvage_python_compatibility

# Python 비호환성 테스트만
pytest test_e2e_container_full.py::test_selvage_python_incompatibility
```

## 🔧 환경 설정

### **필수 요구사항**

- Docker가 설치되어 실행 중이어야 함
- Python 3.10 이상
- `GEMINI_API_KEY` 환경변수 설정 (리뷰 테스트용)

### **의존성 설치**

```bash
pip install pytest testcontainers pytest-timeout
```

### **환경변수 설정**

```bash
# Gemini API 키 설정 (리뷰 테스트에 필요)
export GEMINI_API_KEY="your_gemini_api_key_here"
```

## 📊 CI/CD 통합

### **GitHub Actions (현재 비활성화됨)** ⚠️

> **💡 참고**: GitHub Actions 워크플로우는 현재 비활성화되어 있습니다.  
> 활성화하려면 `.github/workflows/e2e-cross-platform.yml.disabled` 파일을 `.github/workflows/e2e-cross-platform.yml`로 이름을 변경하세요.

```bash
# GitHub Actions 활성화 (준비되었을 때)
mv .github/workflows/e2e-cross-platform.yml.disabled .github/workflows/e2e-cross-platform.yml
```

프로젝트에는 크로스 플랫폼 E2E 테스트를 위한 GitHub Actions 워크플로우가 준비되어 있습니다:

`.github/workflows/e2e-cross-platform.yml.disabled`:

- **크로스 플랫폼**: Ubuntu, macOS, Windows에서 테스트
- **Python 버전**: 3.10, 3.11, 3.12 + 3.9 비호환성 테스트
- **자동 트리거**:
  - `main`, `develop` 브랜치 push
  - Pull Request 생성
  - 매일 02:00 UTC (한국시간 11:00) 스케줄 실행

#### **GitHub Actions 활성화 전 확인사항**

1. **GEMINI_API_KEY Secret 설정**: GitHub 레포지토리 설정에서 Secrets 추가 필요
2. **Workflow 권한**: GitHub Actions 활성화 상태 확인
3. **API 사용량**: 각 플랫폼별 테스트로 API 호출이 증가함

### **로컬에서 CI 환경 시뮬레이션**

```bash
# Ubuntu 환경 시뮬레이션
docker run -it --rm -v $(pwd):/app ubuntu:22.04 bash
cd /app && apt-get update && apt-get install -y python3 python3-pip git
pip3 install -e . && python3 -m selvage --help

# Windows 환경은 GitHub Actions에서만 테스트
```

## 🔍 테스트 세부 정보

### **컨테이너 기반 테스트**

- **격리된 환경**: 각 테스트는 독립된 Docker 컨테이너에서 실행
- **실제 환경 시뮬레이션**: 프로덕션과 유사한 Linux 환경
- **완전한 설치 과정**: pip install부터 실제 사용까지

### **에러 처리 검증**

- **API 키 오류**: 잘못된 API 키로 적절한 에러 메시지 확인
- **Git 환경 오류**: 비Git 디렉토리에서의 에러 처리
- **리소스 제한**: 대용량 파일 처리 시 안정성 확인

### **워크플로우 테스트 시나리오**

- **다중 언어 지원**: Python, JavaScript, Markdown, JSON 파일 리뷰
- **Git 브랜치 워크플로우**: feature 브랜치에서의 개발과 리뷰
- **점진적 개발**: 코드가 발전하는 과정의 각 단계별 리뷰
- **버그 수정 리뷰**: 실제 버그 패턴과 수정사항 검증

## 🐛 문제 해결

### **일반적인 문제들**

#### **Docker 관련 오류**

```bash
# Docker가 실행 중인지 확인
docker ps

# Docker 권한 오류 (Linux)
sudo usermod -aG docker $USER
# 로그아웃 후 다시 로그인
```

#### **API 키 관련 오류**

```bash
# API 키가 설정되었는지 확인
echo $GEMINI_API_KEY

# API 키 설정
export GEMINI_API_KEY="your_key_here"
```

#### **testcontainers 관련 오류**

```bash
# testcontainers 재설치
pip uninstall testcontainers
pip install testcontainers

# 컨테이너 정리
docker system prune -f
```

### **로그 확인**

```bash
# 상세한 로그와 함께 실행
pytest -v -s

# 실패한 테스트만 다시 실행
pytest --lf

# 특정 테스트의 출력 확인
pytest test_e2e_container_full.py::test_selvage_config_in_container -s
```

## 📈 개선 계획

### **추가 예정인 테스트**

- [ ] 네트워크 연결 실패 시나리오
- [ ] 다양한 Git 워크플로우 (merge, rebase, cherry-pick 등)
- [ ] 여러 LLM 모델 교체 테스트 (OpenAI ↔ Gemini)
- [ ] 사용자 인터페이스 테스트 (Streamlit)
- [ ] 대용량 프로젝트 워크플로우 (monorepo)

### **테스트 개선**

- [ ] 더 현실적인 코드 샘플
- [ ] 실제 오픈소스 프로젝트 패턴 반영
- [ ] 언어별 특화 테스트 (TypeScript, Go, Rust 등)

---

**💡 팁**: 개발 중에는 `pytest -m "not slow"`로 빠른 테스트만 실행하고,
PR 전에는 전체 테스트를 실행하는 것을 권장합니다.
