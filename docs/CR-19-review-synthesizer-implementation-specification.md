# CR-19: Review Synthesizer 로직 구현 명세서

## 📋 개요

Linear CR-19 이슈에 따라 Multiturn Review에서 분할된 리뷰 결과들을 하나의 일관된 결과로 합성하는 ReviewSynthesizer 기능을 구현합니다.

**주요 목표:**
- 분할된 리뷰 결과들의 효과적인 병합
- LLM을 활용한 지능적 요약 및 종합 판단
- 중복 이슈 제거 및 우선순위 정렬
- 일관된 점수 및 권장사항 제공

## 🎯 Linear 이슈 정보

**CR-19: synthesize 로직 구현**
- 우선순위: High (2)
- 추정: 3 Points
- 상태: Todo
- 마감일: 2025-08-08

**요구사항:**
- CR-18을 구현 후 받는 리뷰 결과들을 합산하는 로직 구현
- 분할된 리뷰가 모두 끝나면, 각 리뷰의 결과를 모아 LLM에게 다시 전달
- 전체 커밋에 대한 최종 요약, 점수, 권장 사항을 생성하는 '종합 단계' 추가

## 🔧 핵심 컴포넌트 인터페이스

### ReviewSynthesizer

```python
class ReviewSynthesizer:
    """분할된 리뷰 결과 합성 클래스"""
    
    def synthesize_reviews(
        self,
        review_results: list[ReviewResult],
        llm_gateway: BaseGateway
    ) -> ReviewResult:
        """
        분할된 리뷰 결과들을 하나의 일관된 결과로 합성
        
        Args:
            review_results: 분할된 각각의 리뷰 결과들
            llm_gateway: 최종 합성 요청을 위한 게이트웨이
            
        Returns:
            ReviewResult: 합성된 최종 리뷰 결과
            
        합성 전략:
        1. issues 병합: 중복 제거 및 우선순위 정렬
        2. summary 통합: LLM에 각 summary를 제공하여 전체 요약 생성
        3. score 계산: 가중 평균 또는 최종 LLM 판단
        4. recommendations 통합: 중복 제거 및 중요도 기준 정렬
        """
        pass
    
    def _merge_issues(self, review_results: list[ReviewResult]) -> list[dict]:
        """이슈 목록 병합 및 중복 제거"""
        pass
    
    def _generate_unified_summary(
        self, 
        summaries: list[str], 
        llm_gateway: BaseGateway
    ) -> str:
        """LLM을 사용한 통합 요약 생성"""
        pass
    
    def _calculate_final_score(self, scores: list[int]) -> int:
        """최종 점수 계산"""
        pass
```

## 💡 구현 세부사항

### 결과 합성 프롬프트

```python
SYNTHESIS_SYSTEM_PROMPT = """
당신은 분할된 코드 리뷰 결과들을 하나의 일관된 리뷰로 합성하는 전문가입니다.

주어진 여러 개의 리뷰 결과를 분석하여:
1. 전체 커밋에 대한 종합적인 summary 작성
2. 일관된 score (0-10) 산정  
3. 통합된 recommendations 제시
4. 중복 issues 제거 및 우선순위 정렬

각 분할된 리뷰는 전체 변경사항의 일부만을 다루므로, 
전체적인 맥락을 고려한 종합 판단을 제공해주세요.
"""

def create_synthesis_prompt(review_results: list[ReviewResult]) -> str:
    """합성용 프롬프트 생성"""
    synthesis_content = "분할된 리뷰 결과들:\n\n"
    
    for i, result in enumerate(review_results, 1):
        synthesis_content += f"=== 리뷰 결과 {i} ===\n"
        synthesis_content += f"Summary: {result.review_response.summary}\n"
        synthesis_content += f"Score: {result.review_response.score}\n"
        synthesis_content += f"Issues: {len(result.review_response.issues)}개\n"
        synthesis_content += f"Recommendations: {result.review_response.recommendations}\n\n"
    
    return synthesis_content
```

## 🧪 테스트 전략

### 단위 테스트

#### `test_review_synthesizer.py`
- 이슈 병합 로직 테스트
- summary 통합 테스트
- score 계산 테스트

## 🗂️ 구현 대상 파일

### 신규 생성 파일
- `selvage/src/multiturn/review_synthesizer.py`

## 📋 체크리스트

- [ ] ReviewSynthesizer 클래스 구현
- [ ] 이슈 병합 로직 구현
- [ ] LLM 기반 summary 통합 구현
- [ ] 점수 계산 로직 구현
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성

## 🔗 관련 이슈

- **Linear CR-19**: synthesize 로직 구현
- **Linear CR-18**: multiturn review 실행 로직 구현 (선행 작업)