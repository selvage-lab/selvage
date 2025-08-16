# ReviewDisplay UI 테스트 가이드

`ReviewDisplay` 클래스의 모든 UI 요소를 비용 걱정 없이 테스트할 수 있는 방법들을 제공합니다.

## 🚀 시작하기 전에 (권장 설정)

테스트 스크립트를 실행하기 전에 다음 중 하나의 방법으로 환경을 설정하는 것을 권장합니다:

### 방법 1: 개발 모드로 패키지 설치 (권장)

```bash
pip install -e .
```

### 방법 2: PYTHONPATH 환경변수 설정

```bash
# 프로젝트 루트에서
export PYTHONPATH="$PWD:$PYTHONPATH"
```

이렇게 설정하면 스크립트가 더 안전하고 표준적인 방식으로 실행됩니다.

## 📋 제공되는 테스트 방법

### 1. 전체 UI 테스트 (대화형)

모든 UI 요소를 순차적으로 확인할 수 있는 대화형 스크립트입니다.

```bash
python tests/ui/test_review_display.py
```

**특징:**

- 각 UI 요소를 차례대로 표시
- Enter 키로 다음 단계 진행
- 실제 API 호출 없음 (비용 발생하지 않음)
- 모든 UI 요소를 한번에 확인 가능

### 2. 개별 UI 테스트 (빠른 확인)

특정 UI 요소만 빠르게 확인할 수 있는 스크립트입니다.

```bash
# 사용법
python tests/ui/test_ui_individual.py <테스트_타입>

# 예시들
python tests/ui/test_ui_individual.py model_info      # 모델 정보 UI
python tests/ui/test_ui_individual.py log_saved      # 로그 저장 완료 UI
python tests/ui/test_ui_individual.py review_complete # 리뷰 완료 통합 UI
python tests/ui/test_ui_individual.py progress       # 리뷰 진행 상황 UI
python tests/ui/test_ui_individual.py models         # 사용 가능한 모델 목록 UI
```

**특징:**

- 원하는 UI 요소만 즉시 확인
- 빠른 개발 및 디버깅에 유용
- 명령행 인자로 쉽게 선택

### 3. 단위 테스트 (자동화 검증)

출력 내용을 자동으로 검증하는 정식 단위 테스트입니다.

```bash
python -m pytest tests/test_review_display.py -v
```

**특징:**

- Rich Console 출력 캡처 및 검증
- CI/CD 파이프라인에서 활용 가능
- 코드 변경 시 자동 검증

## 🎨 테스트할 수 있는 UI 요소들

### 1. 모델 정보 UI (`model_info`)

```
╭────────────── 리뷰 AI 모델 ──────────────╮
│ Claude 3.5 Sonnet                        │
│ 코드 분석과 리뷰에 특화된 고성능 AI 모델 │
╰──────────────────────────────────────────╯
```

### 2. 로그 저장 완료 UI (`log_saved`)

```
╭───────────────── 결과 저장 ──────────────────╮
│ 저장 완료                                    │
│ ~/Development/.../2024-01-15_code_revi....md │
╰──────────────────────────────────────────────╯
```

### 3. 리뷰 완료 통합 UI (`review_complete`)

```
╭─────────────────────────────── 코드 리뷰 완료 ───────────────────────────────╮
│                                                                              │
│         모델: Claude 3.5 Sonnet                                              │
│         코드 분석과 리뷰에 특화된 고성능 AI 모델                             │
│                                                                              │
│         비용: $0.095 (15.4k → 3.2k tokens)                                   │
│         ※ 추정 비용이므로 각 AI 서비스에서 정확한 비용을 확인하세요.         │
│                                                                              │
│         저장: ~/Development/.../2024-01-15_code_revi....md                   │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 4. 리뷰 진행 상황 UI (`progress`)

- 애니메이션 진행률 표시
- 모델 정보와 함께 표시
- 실제 리뷰 프로세스와 동일한 UI

### 5. 사용 가능한 모델 목록 UI (`models`)

- 프로바이더별 테이블 형태
- 모델명, 별칭, 설명, 컨텍스트 정보
- 사용법 안내 포함

## 🔧 개발 워크플로우

### UI 수정 시 권장 워크플로우:

1. **코드 수정** → `selvage/src/utils/review_display.py` 편집
2. **빠른 확인** → `python scripts/test_ui_individual.py <타입>`
3. **전체 검증** → `python scripts/test_review_display.py`
4. **자동 테스트** → `python -m pytest tests/test_review_display.py`

### 새로운 UI 요소 추가 시:

1. `ReviewDisplay` 클래스에 메서드 추가
2. `scripts/test_ui_individual.py`에 테스트 함수 추가
3. `scripts/test_review_display.py`에 통합 테스트 추가
4. `tests/test_review_display.py`에 단위 테스트 추가

## 💡 장점

### ✅ 비용 절약

- 실제 API 호출 없이 UI 확인
- Mock 데이터로 모든 시나리오 테스트

### ✅ 빠른 개발

- UI 수정 후 즉시 확인 가능
- 개별 요소만 선택적으로 테스트

### ✅ 안정성

- 자동화된 단위 테스트로 회귀 방지
- Rich Console 출력까지 검증

### ✅ 사용성

- 대화형/개별/자동화 테스트 모두 지원
- 명확한 사용법과 예시 제공

## 🚀 Quick Start

가장 빠르게 시작하려면:

```bash
# 리뷰 완료 UI 확인
python scripts/test_ui_individual.py review_complete

# 진행률 UI 확인
python scripts/test_ui_individual.py progress

# 전체 UI 둘러보기
python scripts/test_review_display.py
```
