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

_이 문서는 CR-17 이슈의 상세 구현 가이드입니다. 실제 구현시 이 문서를 기준으로 작업을 진행하며, 필요에 따라 세부사항을 조정할 수 있습니다._
