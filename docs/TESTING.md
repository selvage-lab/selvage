# 테스트 실행 가이드

이 프로젝트는 세 가지 종류의 테스트를 별도로 관리합니다.

## 1. 기본 테스트 (단위 테스트 + 통합 테스트)

```bash
# 기본 pytest 실행 - tests/ 디렉토리의 단위/통합 테스트만 실행
pytest

# 또는 명시적으로
pytest tests/
```

**포함되는 테스트:**

- `tests/` 디렉토리 하위의 모든 테스트 파일
- `e2e/` 디렉토리는 제외됨

## 2. E2E 테스트

```bash
# E2E 테스트만 별도 실행 (권장 방법)
cd e2e && pytest

# 또는 프로젝트 루트에서 디렉토리 지정
pytest e2e/
```

**포함되는 테스트:**

- `e2e/` 디렉토리의 모든 테스트 파일
- 컨테이너 기반 테스트, 실제 환경 통합 테스트

## 3. LLM 평가 테스트

```bash
# LLM 평가 테스트 실행 (권장 방법)
cd llm_eval && pytest

# 또는 프로젝트 루트에서 디렉토리 지정
pytest llm_eval/
```

**포함되는 테스트:**

- `llm_eval/` 디렉토리의 모든 테스트 파일
- DeepEval 기반 LLM 성능 평가 테스트

## 4. 모든 테스트 실행

```bash
# 모든 테스트를 순차적으로 실행 (방법 1)
pytest tests/ && cd e2e && pytest && cd ../llm_eval && pytest && cd ..

# 모든 테스트를 순차적으로 실행 (방법 2)
pytest tests/ && pytest e2e/ && pytest llm_eval/
```

## 마커를 사용한 선택적 실행

```bash
# 느린 테스트 제외
pytest -m "not slow"

# 특정 마커만 실행
pytest -m "unit"
pytest -m "integration"
pytest -m "e2e"
pytest -m "container"
```

## 설정 파일 설명

각 디렉토리에 해당하는 pytest.ini 파일이 위치합니다:

- `tests/pytest.ini`: 기본 테스트 설정 (단위/통합 테스트)
- `e2e/pytest.ini`: E2E 테스트 전용 설정 (컨테이너 테스트, 긴 타임아웃)
- `llm_eval/pytest.ini`: LLM 평가 테스트 전용 설정 (DeepEval 환경 변수, 긴 타임아웃)

각 설정 파일은 해당 테스트 유형에 최적화된 타임아웃, 실패 허용 개수, 환경 변수 등을 포함합니다.
