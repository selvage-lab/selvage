# Selvage 컨텍스트 최적화 분석 및 확장 방안

## 개요

이 문서는 Selvage의 기존 컨텍스트 최적화 로직을 분석하고, "변경 대비 과도한 컨텍스트" 문제를 해결하기 위한 확장 방안을 제시합니다.

## 1. 기존 컨텍스트 최적화 로직 분석

### 1.1 핵심 구현 위치
- **파일**: `selvage/src/utils/prompts/prompt_generator.py`
- **메서드**: `PromptGenerator._create_full_context_code_review_prompt()`
- **핵심 로직**: 라인 139-142

### 1.2 현재 최적화 조건
```python
elif file.line_count == file.additions:
    file_content = ""
else:
    file_content = file.file_content
```

**적용 케이스**:
- 새 파일 생성: `line_count == additions`
- 파일 전면 재작성: 기존 내용 완전 삭제 후 새 내용 추가

**설계 의도**: 
- `file_content`와 `hunks`의 `after_code`에 동일한 내용이 중복되는 것을 방지
- 토큰 사용량 최적화 및 처리 효율성 향상

### 1.3 검증된 테스트 케이스
- **새 파일**: `line_count=3, additions=3, deletions=0`
- **재작성 파일**: `line_count=3, additions=3, deletions=5`
- 두 케이스 모두 `file_content = ""` 처리

### 1.4 현재 구현의 장단점

**장점**:
- ✅ 수학적으로 정확한 조건 (`line_count == additions`)
- ✅ 포괄적인 테스트 케이스로 검증
- ✅ 중복 제거로 토큰 사용량 감소
- ✅ 자동화된 적용

**단점**:
- ❌ 새 파일과 전면 재작성 케이스만 커버
- ❌ 부분적 변경에 대한 최적화 부족
- ❌ 이진 선택 (전체 파일 또는 생략)
- ❌ 언어별 특성 미고려

## 2. 새로운 컨텍스트 최적화 로직 설계

### 2.1 문제 정의 및 분석

#### 핵심 문제
- **변경 대비 과도한 컨텍스트**: 1-2줄 변경에 수백 줄 파일 전체 제공
- **복합 변경 시나리오**: 여러 hunk가 있을 때 각각 다른 복잡도
- **기준 설정의 모호성**: 1-2줄 기준의 적절성 검토 필요

#### 세부 시나리오
1. **단일 hunk, 1-2줄 변경**: 가장 단순한 케이스
2. **여러 hunk, 각각 1-2줄 변경**: 분산된 소규모 변경
3. **혼합 케이스**: 일부 hunk는 단순, 일부는 복잡
4. **연속 변경**: 인접한 라인들의 변경

### 2.2 다단계 컨텍스트 전략

#### 컨텍스트 제공 레벨
```
Level 1: 변경 라인 + 주변 3줄 (MINIMAL_CONTEXT)
Level 2: 변경 라인 + 함수/클래스 전체 (FUNCTION_CONTEXT)
Level 3: 전체 파일 (FULL_CONTEXT)
```

#### 복잡도 점수 체계
```python
복잡도 점수 = 변경_라인_점수 + hunk_개수_점수 + 분산도_점수

변경_라인_점수 = min((additions + deletions) // 2, 5)  # 최대 5점
hunk_개수_점수 = min(hunk_count, 3)                    # 최대 3점
분산도_점수 = 파일_크기_고려한_상대적_분산도            # 최대 2점
```

##### 분산도 점수 상세 계산
```python
def _calculate_dispersion_score(self, hunks: List[Hunk], file_line_count: int) -> int:
    """파일 크기를 고려한 분산도 점수 계산"""
    if len(hunks) <= 1:
        return 0
    
    # 각 hunk의 상대적 위치 계산 (0.0 ~ 1.0)
    hunk_positions = [hunk.old_start for hunk in hunks]
    hunk_positions.sort()
    relative_positions = [pos / file_line_count for pos in hunk_positions]
    
    # 상대적 간격 계산
    relative_gaps = []
    for i in range(1, len(relative_positions)):
        gap = relative_positions[i] - relative_positions[i-1]
        relative_gaps.append(gap)
    
    avg_relative_gap = sum(relative_gaps) / len(relative_gaps)
    spread = max(relative_positions) - min(relative_positions)
    
    # 파일 크기별 가중치 적용
    size_weight = 1.0
    if file_line_count < 50:
        size_weight = 0.5    # 작은 파일은 분산도 영향 적음
    elif file_line_count > 500:
        size_weight = 1.5    # 큰 파일은 분산도 영향 큼
    
    # 점수 계산
    base_score = 0
    if avg_relative_gap <= 0.1 and spread <= 0.2:  # 파일의 10% 내 간격, 20% 내 분포
        base_score = 0  # 집중된 변경
    elif avg_relative_gap <= 0.3 and spread <= 0.5:  # 파일의 30% 내 간격, 50% 내 분포
        base_score = 1  # 중간 분산
    else:
        base_score = 2  # 높은 분산
    
    final_score = base_score * size_weight
    return min(int(final_score), 2)  # 최대 2점으로 제한
```

**분산도 점수의 중요성**:
1. **컨텍스트 필요성**: 변경이 파일 전체에 분산되어 있으면 전체 맥락이 중요
2. **파일 크기 고려**: 같은 라인 간격이라도 파일 크기에 따라 의미가 다름
3. **상대적 위치**: 절대적 라인 번호가 아닌 파일 내 상대적 위치로 판단

**예시**:
- 100줄 파일에서 10줄, 30줄 변경: 상대적 간격 0.2 (20%) → 점수 1
- 1000줄 파일에서 100줄, 120줄 변경: 상대적 간격 0.02 (2%) → 점수 0

#### 전략 선택 기준
- **점수 0-3**: Level 1 (MINIMAL_CONTEXT - 주변 3줄)
- **점수 4-6**: Level 2 (FUNCTION_CONTEXT - 함수/클래스 전체)
- **점수 7+**: Level 3 (FULL_CONTEXT - 전체 파일)

### 2.3 구현 아키텍처

#### 2.3.1 ContextOptimizer 클래스
```python
class ContextOptimizer:
    def determine_context_strategy(self, file_diff: FileDiff) -> ContextStrategy:
        """파일 diff를 분석하여 최적 컨텍스트 전략 결정"""
        
        # 새 파일이나 전면 재작성인 경우 기존 로직 적용
        if file_diff.line_count == file_diff.additions:
            return ContextStrategy.FULL_CONTEXT  # 전체 컨텍스트로 명확화
        
        # 새로운 최적화 로직
        complexity_score = self._calculate_complexity_score(file_diff)
        
        if complexity_score <= 3:
            return ContextStrategy.MINIMAL_CONTEXT
        elif complexity_score <= 6:
            return ContextStrategy.FUNCTION_CONTEXT
        else:
            return ContextStrategy.FULL_CONTEXT
    
    def _calculate_complexity_score(self, file_diff: FileDiff) -> int:
        """변경 복잡도 점수 계산"""
        score = 0
        
        # 변경 라인 수 기준
        total_changes = file_diff.additions + file_diff.deletions
        score += min(total_changes // 2, 5)
        
        # hunk 개수 기준
        score += min(len(file_diff.hunks), 3)
        
        # 분산도 기준
        if len(file_diff.hunks) > 1:
            score += self._calculate_dispersion_score(file_diff.hunks, file_diff.line_count)
        
        return score
```

#### 2.3.2 ContextStrategy 열거형
```python
from enum import Enum

class ContextStrategy(Enum):
    MINIMAL_CONTEXT = "minimal_context"        # 주변 3줄
    FUNCTION_CONTEXT = "function_context"      # 함수/클래스 전체
    FULL_CONTEXT = "full_context"              # 전체 파일
```

### 2.4 점진적 구현 계획

#### Phase 1: 기본 케이스 구현
**목표**: 단일 hunk, 1-2줄 변경 케이스 처리
- `ContextOptimizer` 기본 클래스 구현
- 단순한 복잡도 점수 계산
- 주변 3줄 컨텍스트 제공 로직
- 기존 테스트와 호환성 유지

**예상 개발 시간**: 1-2일

#### Phase 2: 복합 케이스 확장
**목표**: 여러 hunk 처리 및 복잡도 점수 정교화
- 여러 hunk 처리 로직 구현
- 분산도 계산 알고리즘 개발
- 혼합 전략 (hunk별 다른 컨텍스트 레벨) 구현
- 성능 측정 및 최적화

**예상 개발 시간**: 2-3일

#### Phase 3: 고도화 (선택적)
**목표**: tree-sitter 기반 구문 구조 인식
- 언어별 구문 구조 분석
- 함수/클래스 경계 인식
- 사용자 설정 가능한 옵션 제공
- 고급 최적화 기법 적용

**예상 개발 시간**: 3-5일

## 3. 실제 발생 빈도 분석 필요성

### 3.1 가설적 분포 예측
- **단순 변경 (1-2줄)**: 전체 커밋의 30-40%
- **중간 변경 (3-10줄)**: 전체 커밋의 40-50%
- **복잡 변경 (10줄+)**: 전체 커밋의 10-20%

### 3.2 검증 방법
1. 최근 100개 커밋 분석
2. 각 파일별 변경 라인 수 통계
3. hunk 개수 및 분포 분석
4. 토큰 사용량 감소 효과 측정

### 3.3 ROI 분석
- **구현 시간**: Phase 1-2 기준 3-5일
- **예상 효과**: 토큰 사용량 15-25% 감소 (단순 변경 케이스)
- **품질 리스크**: 컨텍스트 부족으로 인한 리뷰 품질 저하 가능성

## 4. 리스크 및 고려사항

### 4.1 주요 리스크
1. **컨텍스트 부족**: 주변 코드 맥락 부족으로 잘못된 리뷰
2. **복잡성 증가**: 조건 분기 증가로 인한 버그 가능성
3. **언어 차이**: 언어별 구문 구조 차이 미고려
4. **테스트 부담**: 다양한 시나리오에 대한 테스트 케이스 필요

### 4.2 완화 방안
1. **단계적 구현**: Phase 1부터 점진적 적용
2. **A/B 테스트**: 기존 방식과 새 방식 비교 검증
3. **사용자 옵션**: 최적화 레벨 사용자 설정 가능
4. **모니터링**: 리뷰 품질 지표 추적

## 5. 결론 및 권장사항

### 5.1 권장 접근법
1. **Phase 1 우선 구현**: 단순한 케이스부터 시작
2. **실제 데이터 분석**: 최근 커밋 분석으로 가설 검증
3. **점진적 확장**: 검증된 케이스부터 단계적 확장

### 5.2 성공 지표
- 토큰 사용량 15% 이상 감소
- 리뷰 품질 유지 (기존 대비 90% 이상)
- 사용자 만족도 향상
- 처리 속도 개선

### 5.3 다음 단계
1. 실제 커밋 데이터 분석 (2-3시간)
2. Phase 1 구현 시작 (1-2일)
3. 테스트 케이스 작성 및 검증
4. 사용자 피드백 수집 및 개선

---

**문서 작성일**: 2025-07-18  
**작성자**: Claude Code  
**버전**: 1.0