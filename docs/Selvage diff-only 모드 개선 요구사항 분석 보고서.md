현재 요구사항을 분석하고 구현 방안을 검토하겠습니다. 먼저 프로젝트의 현재 상태를 자세히 파악해보겠습니다.
Ran tool

Read file: selvage/src/diff_parser/parser.py

Read file: selvage/src/diff_parser/models/file_diff.py

Read file: selvage/src/diff_parser/models/hunk.py

Read file: selvage/src/utils/file_utils.py

Read file: selvage/src/utils/file_utils.py

Ran tool

Ran tool

Ran tool

Read file: pyproject.toml

Ran tool

Ran tool

# Selvage diff-only 모드 개선 요구사항 분석 보고서

## 📋 현재 상황 분석

### 현재 구조

- **diff-only 모드**: CLI 옵션으로 제공되며, `use_full_context = not diff_only`로 동작
- **파일 컨텍스트 로딩**: 전체 파일을 읽거나 전혀 읽지 않는 이진 선택 구조
- **parser.py**: `use_full_context` 플래그에 따라 `load_file_content()` 호출 여부 결정
- **FileDiff 모델**: `calculate_changes()`를 통해 추가/삭제 라인 수 계산 가능

### 주요 문제점

1. **사용자 경험 문제**: 매번 diff-only 모드를 수동으로 선택해야 하는 불편함
2. **비효율적 리소스 사용**: 작은 변경사항(1-2줄)에도 전체 파일 로딩으로 인한 비용 증가
3. **리뷰 품질 저하**: 불필요한 컨텍스트로 인한 LLM 성능 저하 및 처리 시간 증가

## 🎯 요구사항 정리

### 핵심 목표

- diff-only 옵션 제거 후 **자동화된 적응형 컨텍스트 제공**
- 변경사항의 특성에 따른 **스마트 컨텍스트 수준 결정**
- **비용 최적화** 및 **리뷰 품질 향상**

### 기능 요구사항

1. 변경 라인 수, 파일 크기 등을 기반으로 한 컨텍스트 수준 자동 결정
2. 여러 hunk가 있는 파일에 대한 통합적 처리
3. tree-sitter 또는 유사 도구를 활용한 함수/클래스 블록 단위 추출

## 🔧 구현 방안

### Phase 1: 휴리스틱 기반 구현 (즉시 적용 가능)

#### 1.1 CLI 수정

```python
# 제거할 옵션들
--diff-only (제거)
--clear-cache (유지)
--skip-cache (유지)
```

#### 1.2 컨텍스트 수준 결정 로직

```python
class ContextLevel(Enum):
    DIFF_ONLY = "diff_only"           # 변경된 라인만
    SURROUNDING = "surrounding"       # 변경 라인 + 주변 컨텍스트
    FUNCTION_BLOCK = "function_block" # 함수/클래스 블록 전체
    FULL_FILE = "full_file"          # 전체 파일

def determine_context_level(file_diff: FileDiff) -> ContextLevel:
    """변경사항 특성에 따른 컨텍스트 수준 결정"""
    total_changes = file_diff.additions + file_diff.deletions

    if total_changes <= 2:
        return ContextLevel.DIFF_ONLY
    elif total_changes <= 10:
        return ContextLevel.SURROUNDING
    elif total_changes <= 50:
        return ContextLevel.FUNCTION_BLOCK
    else:
        return ContextLevel.FULL_FILE
```

#### 1.3 선택적 컨텍스트 로더 구현

```python
def load_contextual_content(
    filename: str,
    repo_path: str,
    hunks: list[Hunk],
    context_level: ContextLevel
) -> str | None:
    """컨텍스트 수준에 따른 선택적 파일 내용 로딩"""

    if context_level == ContextLevel.DIFF_ONLY:
        return None
    elif context_level == ContextLevel.FULL_FILE:
        return load_file_content(filename, repo_path)
    elif context_level == ContextLevel.SURROUNDING:
        return extract_surrounding_lines(filename, repo_path, hunks)
    elif context_level == ContextLevel.FUNCTION_BLOCK:
        return extract_function_blocks(filename, repo_path, hunks)
```

### Phase 2: Tree-sitter 기반 고도화 (향후 구현)

#### 2.1 의존성 추가

```toml
# pyproject.toml에 추가
dependencies = [
    # ... 기존 의존성들 ...
    "tree-sitter==0.21.3",
    "tree-sitter-python==0.21.0",
    "tree-sitter-javascript==0.21.4",
    # 필요한 언어별 파서들...
]
```

#### 2.2 고급 블록 추출기 구현

```python
class TreeSitterBlockExtractor:
    """Tree-sitter를 사용한 정확한 함수/클래스 블록 추출"""

    def extract_containing_blocks(
        self,
        filename: str,
        line_numbers: list[int]
    ) -> str:
        """변경된 라인들을 포함하는 함수/클래스 블록들 추출"""
        # tree-sitter를 사용한 AST 분석
        # 해당 라인을 포함하는 최소 함수/클래스 블록 식별
        # 중복 제거된 블록들 반환
```

## 📊 예상 효과

### 정량적 효과

- **토큰 사용량 감소**: 작은 변경에 대해 최대 80-90% 토큰 절약
- **처리 시간 단축**: 평균 30-50% 리뷰 시간 감소 예상
- **API 비용 절감**: 월 평균 40-60% 비용 절약

### 정성적 효과

- **사용자 경험 개선**: 수동 옵션 선택 불필요
- **리뷰 품질 향상**: 적절한 컨텍스트로 더 정확한 리뷰
- **자동화 수준 향상**: 지능적 컨텍스트 결정

## 🚧 구현 우선순위

### 1순위: 기본 휴리스틱 구현

- [ ] CLI에서 diff-only 옵션 제거
- [ ] ContextLevel enum 및 결정 로직 구현
- [ ] 선택적 컨텍스트 로더 기본 버전 구현
- [ ] 기존 테스트 케이스 업데이트

### 2순위: 컨텍스트 추출 로직 고도화

- [ ] 주변 라인 추출기 구현
- [ ] 간단한 함수 블록 감지 (들여쓰기 기반)
- [ ] 다중 hunk 처리 로직

### 3순위: Tree-sitter 통합 (선택적)

- [ ] tree-sitter 의존성 추가
- [ ] 언어별 파서 구현
- [ ] 정확한 AST 기반 블록 추출

## ⚠️ 주의사항

1. **기존 캐시 시스템과의 호환성** 확인 필요
2. **다양한 프로그래밍 언어**에 대한 테스트 필요
3. **대용량 파일** 처리 시 성능 고려
4. **에러 핸들링** 강화 (파일 읽기 실패, 파싱 오류 등)

## 🔄 마이그레이션 계획

1. **기존 사용자**: diff-only 옵션이 자동으로 적용되도록 점진적 전환
2. **설정 파일**: 기존 diff-only 설정 값 무시 및 경고 메시지 표시
3. **문서화**: 새로운 자동 컨텍스트 결정 로직에 대한 가이드 제공

이 보고서를 바탕으로 단계적 구현을 진행하면 사용자 경험과 성능을 크게 개선할 수 있을 것으로 예상됩니다.
