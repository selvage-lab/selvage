# CR-17: 토큰 검증 방식 개선 상세 계획

## 📋 개요

이 문서는 selvage의 토큰 검증 방식을 개선하여 확장성과 사용자 경험을 향상시키는 작업의 상세 계획을 기술합니다.

**주요 목표:**

- 사전 토큰 검증 제거로 확장성 확보
- OpenRouter 중심 아키텍처로 API key 관리 단순화
- API 응답 기반 에러 처리로 실용성 향상
- Multiturn review 시스템으로 대용량 컨텍스트 지원

## 🔍 현황 분석

### 현재 토큰 검증 시스템

#### TokenUtils 클래스 (`selvage/src/utils/token/token_utils.py`)

**주요 메서드:**

- `count_tokens(review_prompt, model)`: 모델별 토큰 계산
- `get_model_context_limit(model)`: 모델별 컨텍스트 제한 조회
- `_count_tokens_claude(review_prompt, model)`: Claude 토큰 계산
- `_count_tokens_claude_anthropic(review_prompt, model)`: Anthropic API 직접 사용
- `_count_tokens_claude_with_anthropic_for_openrouter()`: OpenRouter용 Anthropic API 사용

**현재 토큰 계산 플로우:**

```pseudocode
if model contains "claude":
    if provider == OpenRouter:
        call Anthropic API directly (requires ANTHROPIC_API_KEY)
    else:
        call Anthropic API normally
elif model contains "gemini":
    call Google AI API (requires GOOGLE_API_KEY)
elif model in ["kimi-k2", "deepseek-v3-0324", "deepseek-r1-0528"]:
    return 0  // Skip token calculation
else:
    use tiktoken for OpenAI models
```

#### ContextLimitExceededError 예외 (`selvage/src/exceptions/context_limit_exceeded_error.py`)

```python
class ContextLimitExceededError(LLMGatewayError):
    def __init__(self, input_tokens: int | None = None, context_limit: int | None = None):
        # 토큰 수와 제한 정보를 포함한 에러 메시지 생성
```

#### BaseGateway.validate_review_request() 메서드

**파일:** `selvage/src/llm_gateway/base_gateway.py`
**라인:** 161-184

```python
def validate_review_request(self, review_prompt: ReviewPromptWithFileContent) -> None:
    input_token_count = TokenUtils.count_tokens(review_prompt, self.get_model_name())
    context_limit = TokenUtils.get_model_context_limit(self.get_model_name())
    if input_token_count > context_limit:
        raise ContextLimitExceededError(input_tokens=input_token_count, context_limit=context_limit)
```

### 문제점 분석

1. **확장성 한계**: 새 모델 추가시마다 tokenizer 구현 필요
2. **복잡성**: Provider별 토큰 계산 로직의 복잡성 증가
3. **API Key 관리 부담**: OpenRouter 사용시에도 개별 provider API key 필요
4. **일관성 부족**: 일부 모델은 토큰 계산 건너뛰기
5. **유지보수 비용**: 각 provider별 API 변경사항 대응 필요

## 🗑️ 제거 대상 코드 명세

### Phase 1: 토큰 검증 로직 제거

#### 1. BaseGateway 검증 메서드 제거

- **파일:** `selvage/src/llm_gateway/base_gateway.py`
- **제거 대상:** `validate_review_request()` 메서드 (L161-184)

## 🔄 새로운 워크플로우 설계

### 1. API 응답 기반 에러 처리

#### Provider별 Context Limit 에러 패턴

```python
# 새로운 에러 패턴 매핑
CONTEXT_LIMIT_ERROR_PATTERNS = {
    "openai": {
        "error_codes": ["context_length_exceeded"],
        "error_messages": ["maximum context length", "token limit", "too many tokens"]
    },
    "anthropic": {
        "error_codes": ["invalid_request_error"],
        "error_messages": ["prompt is too long", "maximum context length", "token limit exceeded"]
    },
    "google": {
        "error_codes": ["400"],
        "error_messages": ["Request payload size exceeds", "Token limit exceeded"]
    },
    "openrouter": {
        "error_codes": ["context_length_exceeded","400", "413"],
        "error_messages": ["context length exceeded", "prompt too long", "payload too large"]
    }
}
```

#### 새로운 에러 처리 플로우

```pseudocode
function review_code(review_prompt):
    try:
        // 직접 API 호출 시도
        response = call_api(review_prompt)
        return success_result(response)

    catch ApiError as error:
        if is_context_limit_error(error):
            // Multiturn review로 전환
            return execute_multiturn_review(review_prompt)
        else:
            // 기타 에러는 기존 방식으로 처리
            throw error

function is_context_limit_error(error):
    provider = self.model.provider
    patterns = CONTEXT_LIMIT_ERROR_PATTERNS[provider]

    return (error.code in patterns.error_codes) or
           any(msg in error.message for msg in patterns.error_messages)
```

### 2. Multiturn Review 시스템

#### Context 분할 전략

```pseudocode
function execute_multiturn_review(original_prompt):
    file_contexts = extract_file_contexts(original_prompt)

    // 파일별 우선순위 계산 (변경된 라인 수, 파일 크기 등)
    prioritized_contexts = prioritize_contexts(file_contexts)

    // 컨텍스트 크기 기반 그룹핑
    context_groups = group_contexts_by_size(prioritized_contexts, target_size=0.7 * context_limit)

    reviews = []
    for group in context_groups:
        partial_prompt = create_partial_prompt(group)
        partial_review = call_api(partial_prompt)
        reviews.append(partial_review)

    // 개별 리뷰 결과 병합
    return merge_reviews(reviews)
```

#### Context 우선순위 알고리즘

```python
class ContextPrioritizer:
    def calculate_priority(self, file_context):
        score = 0

        # 변경된 라인 수 (높을수록 우선)
        score += file_context.changed_lines * 10

        # 파일 타입 가중치 (핵심 파일 우선)
        if file_context.is_core_file():
            score += 50

        # 컨텍스트 타입 가중치 (SMART_CONTEXT 우선)
        if file_context.context_type == "SMART_CONTEXT":
            score += 30
        elif file_context.context_type == "FALLBACK_CONTEXT":
            score += 10

        return score
```

## 📋 단계별 구현 계획

### Phase 1: 기존 검증 로직 제거 (1-2일)

**작업 항목:**

1. `BaseGateway.validate_review_request()` 메서드 제거
2. 모든 Gateway 클래스에서 검증 호출 제거
3. 관련 import문 정리
4. 기존 테스트 코드 업데이트

**검증 방법:**

- 기존 테스트 실행하여 회귀 없음 확인
- 간단한 리뷰 요청으로 기본 동작 확인

### Phase 2: API 응답 기반 에러 처리 구현 (3-4일)

**작업 항목:**

1. Context limit 에러 패턴 정의
2. `ContextLimitErrorDetector` 클래스 구현
3. 각 Gateway에 에러 감지 로직 추가
4. Multiturn 전환 로직 구현

**새로운 클래스 설계:**

```python
# selvage/src/exceptions/context_limit_detector.py
class ContextLimitErrorDetector:
    @staticmethod
    def is_context_limit_error(error: Exception, provider: ModelProvider) -> bool:
        # Provider별 에러 패턴 매칭

    @staticmethod
    def should_retry_with_multiturn(error: Exception) -> bool:
        # Multiturn 재시도 가능 여부 판단
```

### Phase 3: Multiturn Review 시스템 구현 (5-7일)

**작업 항목:**

1. Context 분할 알고리즘 구현
2. 우선순위 기반 Context 그룹핑
3. 부분 리뷰 결과 병합 로직
4. 진행 상황 표시 UI 개선

**새로운 클래스 설계:**

```python
# selvage/src/llm_gateway/multiturn_reviewer.py
class MultiturnReviewer:
    def __init__(self, gateway: BaseGateway):
        self.gateway = gateway
        self.context_splitter = ContextSplitter()
        self.review_merger = ReviewMerger()

    def execute_multiturn_review(self, review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
        # Multiturn 리뷰 실행 로직

# selvage/src/utils/context_splitter.py
class ContextSplitter:
    def split_contexts(self, review_prompt: ReviewPromptWithFileContent,
                      target_size: int) -> List[ReviewPromptWithFileContent]:
        # Context 분할 로직

# selvage/src/utils/review_merger.py
class ReviewMerger:
    def merge_reviews(self, partial_reviews: List[ReviewResult]) -> ReviewResult:
        # 부분 리뷰 병합 로직
```

### Phase 4: 최적화 및 테스팅 (2-3일)

**작업 항목:**

1. 성능 최적화 (불필요한 API 호출 최소화)
2. 에러 처리 강화
3. 통합 테스트 작성
4. 문서 업데이트

## 🔌 인터페이스 설계

### 1. 에러 감지 인터페이스

```python
from abc import ABC, abstractmethod
from selvage.src.models.model_provider import ModelProvider

class ErrorDetector(ABC):
    @abstractmethod
    def is_context_limit_error(self, error: Exception, provider: ModelProvider) -> bool:
        """Context limit 에러 여부 판단"""
        pass

    @abstractmethod
    def should_retry_with_multiturn(self, error: Exception) -> bool:
        """Multiturn으로 재시도할지 여부 판단"""
        pass
```

### 2. Context 분할 인터페이스

```python
from typing import List
from selvage.src.utils.prompts.models.review_prompt_with_file_content import ReviewPromptWithFileContent

class ContextSplitter(ABC):
    @abstractmethod
    def split_contexts(self,
                      review_prompt: ReviewPromptWithFileContent,
                      target_size: int) -> List[ReviewPromptWithFileContent]:
        """프롬프트를 여러 부분으로 분할"""
        pass

    @abstractmethod
    def calculate_context_size(self, review_prompt: ReviewPromptWithFileContent) -> int:
        """예상 컨텍스트 크기 계산 (대략적)"""
        pass
```

### 3. 리뷰 병합 인터페이스

```python
from typing import List
from selvage.src.models.review_result import ReviewResult

class ReviewMerger(ABC):
    @abstractmethod
    def merge_reviews(self, partial_reviews: List[ReviewResult]) -> ReviewResult:
        """부분 리뷰들을 하나로 병합"""
        pass

    @abstractmethod
    def merge_review_responses(self, responses: List[ReviewResponse]) -> ReviewResponse:
        """리뷰 응답들을 병합"""
        pass
```

### 4. Gateway 인터페이스 확장

```python
# BaseGateway 클래스에 추가될 메서드들
class BaseGateway:
    def execute_multiturn_review(self, review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
        """Multiturn 리뷰 실행"""
        multiturn_reviewer = MultiturnReviewer(self)
        return multiturn_reviewer.execute_multiturn_review(review_prompt)

    def handle_context_limit_error(self, error: Exception,
                                  review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
        """Context limit 에러 처리"""
        if ContextLimitErrorDetector.should_retry_with_multiturn(error):
            return self.execute_multiturn_review(review_prompt)
        else:
            return ReviewResult.get_error_result(error, self.get_model_name())
```

## 📊 예상 효과

### 개발 효율성

- **신규 모델 지원 시간**: 기존 2-3일 → 30분 (90% 단축)
- **코드 복잡도**: TokenUtils 관련 코드 ~300라인 제거
- **유지보수 비용**: Provider별 API 변경 대응 불필요

### 사용자 경험

- **API Key 설정**: OpenRouter 하나로 통합
- **에러 투명성**: 실제 API 응답 기반 명확한 에러 메시지
- **확장성**: 무제한 모델 지원 가능

### 성능

- **실패 비용**: Context limit 실패시에도 API 비용 미미
- **성공률**: 실제 API 제한 기준으로 정확한 판단
- **대용량 처리**: Multiturn으로 제한 없는 컨텍스트 처리

## ⚠️ 고려사항

### 잠재적 위험

1. **API 호출 증가**: 실패시 추가 호출 발생 (하지만 실패 비용은 낮음)
2. **응답 시간 증가**: Multiturn시 순차 처리로 인한 지연
3. **복잡성 이동**: 토큰 계산 → 에러 감지 및 Context 분할

### 완화 방안

1. **비용 모니터링**: 실패 API 호출 추적 및 알림
2. **병렬 처리**: 가능한 경우 Multiturn 병렬 실행
3. **점진적 적용**: Feature flag로 단계적 롤아웃

## 📅 일정 계획

| Phase       | 기간        | 주요 작업               |
| ----------- | ----------- | ----------------------- |
| Phase 1     | 1-2일       | 기존 검증 로직 제거     |
| Phase 2     | 3-4일       | API 응답 기반 에러 처리 |
| Phase 3     | 5-7일       | Multiturn 시스템 구현   |
| Phase 4     | 2-3일       | 최적화 및 테스팅        |
| **총 기간** | **11-16일** | **완전 구현**           |

---

_이 문서는 CR-17 이슈의 상세 구현 가이드입니다. 실제 구현시 이 문서를 기준으로 작업을 진행하며, 필요에 따라 세부사항을 조정할 수 있습니다._
