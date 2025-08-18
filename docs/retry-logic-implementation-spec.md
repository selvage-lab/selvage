# Retry Logic 및 Error Handling 개선 구현 명세

## 1. 개요 및 목표

### 문제 상황

- OpenRouter Gateway에서 간헐적으로 structured output이 아닌 응답 발생
- "OpenRouter API 응답에 choices가 없습니다" 에러 빈발
- instructor 라이브러리와 달리 자체 구현된 OpenRouter에서 retry 로직 부재
- 에러 발생 시 충분한 디버깅 정보 부족

### 해결 목표

1. 모든 LLM Gateway에 통일된 retry 로직 적용
2. API 응답 구조 문제에 대한 자동 재시도
3. 구체적인 예외 클래스 정의 및 디버깅 정보 제공
4. CLI 레벨에서 정교한 에러 처리 및 사용자 가이드

## 2. 아키텍처 설계

### Retry 전략

- **재시도 횟수**: 최대 3회 (설정 가능)
- **백오프 전략**: 지수 백오프 (1초, 2초, 4초)
- **재시도 대상 에러**: API timeout, connection error, server error (5xx), rate limit
- **재시도 제외 에러**: authentication error, invalid request format, client error (4xx except 429)

### Exception 체계

```
Exception
├── LLMGatewayError (기존)
│   ├── JSONParsingError (신규)
│   └── OpenRouterAPIError (신규)
│       ├── OpenRouterResponseError (신규)
│       └── OpenRouterConnectionError (신규)
```

## 3. 새로 생성되는 파일들

### 3.1 Tenacity 라이브러리 사용

**pyproject.toml에 추가할 dependency**:

```toml
dependencies = [
    # ... 기존 dependencies
    "tenacity==8.2.3",
]
```

### 3.2 JSON Parsing Exception

**파일 경로**: `selvage/src/exceptions/json_parsing_error.py`

```python
"""JSON 파싱 관련 예외 클래스"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class JSONParsingError(LLMGatewayError):
    """JSON 파싱 실패 시 발생하는 예외"""

    def __init__(self, message: str, raw_response: str = "", parsing_error: Exception | None = None):
        super().__init__(message)
        self.raw_response = raw_response
        self.parsing_error = parsing_error

    def __str__(self) -> str:
        error_msg = super().__str__()
        if self.parsing_error:
            error_msg += f" (원인: {type(self.parsing_error).__name__}: {self.parsing_error})"
        return error_msg
```

### 3.3 OpenRouter API Exception

**파일 경로**: `selvage/src/exceptions/openrouter_api_error.py`

```python
"""OpenRouter API 관련 예외 클래스들"""

from selvage.src.exceptions.llm_gateway_error import LLMGatewayError


class OpenRouterAPIError(LLMGatewayError):
    """OpenRouter API 관련 기본 예외 클래스"""

    def __init__(self, message: str, raw_response: dict | None = None, status_code: int | None = None):
        super().__init__(message)
        self.raw_response = raw_response
        self.status_code = status_code


class OpenRouterResponseError(OpenRouterAPIError):
    """OpenRouter API 응답 구조 문제 시 발생하는 예외"""

    def __init__(self, message: str, raw_response: dict | None = None, missing_field: str | None = None):
        super().__init__(message, raw_response)
        self.missing_field = missing_field


class OpenRouterConnectionError(OpenRouterAPIError):
    """OpenRouter API 연결 문제 시 발생하는 예외"""
    pass


class OpenRouterAuthenticationError(OpenRouterAPIError):
    """OpenRouter API 인증 문제 시 발생하는 예외 (재시도 금지)"""
    pass
```

## 4. 수정되는 기존 파일들

### 4.1 BaseGateway

**파일 경로**: `selvage/src/llm_gateway/base_gateway.py`

**수정 내용**:

1. `review_code` 메서드에 tenacity retry decorator 적용
2. import 구문 추가

```python
# 추가할 import들
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

# 수정할 메서드
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((
        ConnectionError,
        TimeoutError,
        ValueError,  # API 응답 구조 문제
    )),
    before_sleep=before_sleep_log(console.logger, log_level="INFO"),
    after=after_log(console.logger, log_level="DEBUG"),
)
def review_code(self, review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
    # 기존 코드 유지
    ...
```

### 4.2 OpenRouterGateway

**파일 경로**: `selvage/src/llm_gateway/openrouter/gateway.py`

**수정 내용**:

1. import 구문 추가
2. `review_code` 메서드에 tenacity retry decorator 적용
3. L224-236 에러 처리를 새로운 예외 클래스로 변경
4. 더 구체적인 로깅 추가

```python
# 추가할 import들
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterResponseError,
    OpenRouterConnectionError,
)

# 수정할 메서드
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((
        OpenRouterResponseError,
        OpenRouterConnectionError,
        ConnectionError,
        TimeoutError,
    )),
    before_sleep=before_sleep_log(console.logger, log_level="INFO"),
    after=after_log(console.logger, log_level="DEBUG"),
)
def review_code(self, review_prompt: ReviewPromptWithFileContent) -> ReviewResult:
    # ... 기존 코드 ...

    # L224-236 부분 수정 - 리팩토링된 validation 함수들 사용
    self._validate_api_response(raw_api_response, raw_response_data)
    response_text = self._extract_response_content(raw_api_response, raw_response_data)
    self._validate_structured_response(structured_response, response_text)

# 새로 추가할 private 메서드들:

def _validate_api_response(self, raw_api_response: OpenRouterResponse, raw_response_data: dict) -> None:
    """OpenRouter API 응답의 기본 구조를 검증합니다.

    Args:
        raw_api_response: 파싱된 응답 객체
        raw_response_data: 원본 응답 데이터

    Raises:
        OpenRouterResponseError: choices가 없는 경우
    """
    if not raw_api_response.choices:
        error_msg = "OpenRouter API 응답에 choices가 없습니다"
        console.error(error_msg)
        if console.is_debug_mode():
            console.error(f"원본 응답: {raw_response_data}")
        raise OpenRouterResponseError(
            error_msg,
            raw_response=raw_response_data,
            missing_field="choices"
        )

def _extract_response_content(self, raw_api_response: OpenRouterResponse, raw_response_data: dict) -> str:
    """응답에서 텍스트 내용을 추출하고 검증합니다.

    Args:
        raw_api_response: 파싱된 응답 객체
        raw_response_data: 원본 응답 데이터

    Returns:
        str: 추출된 응답 텍스트

    Raises:
        OpenRouterResponseError: content가 없는 경우
    """
    response_text = raw_api_response.choices[0].message.content
    if not response_text:
        error_msg = "OpenRouter API 응답에 content가 없습니다"
        console.error(error_msg)
        if console.is_debug_mode():
            console.error(f"원본 응답: {raw_response_data}")
        raise OpenRouterResponseError(
            error_msg,
            raw_response=raw_response_data,
            missing_field="content"
        )
    return response_text

def _validate_structured_response(self, structured_response: StructuredReviewResponse | None, response_text: str) -> None:
    """구조화된 응답의 유효성을 검증합니다.

    Args:
        structured_response: 파싱된 구조화된 응답
        response_text: 원본 응답 텍스트

    Raises:
        OpenRouterResponseError: 구조화된 응답이 None인 경우
    """
    if structured_response is None:
        error_msg = "OpenRouter API 응답에서 유효한 JSON을 파싱할 수 없습니다"
        console.error(error_msg)
        console.error(f"원본 응답: {response_text}")
        raise OpenRouterResponseError(error_msg)
```

### 4.3 JSONExtractor

**파일 경로**: `selvage/src/utils/json_extractor.py`

**수정 내용**:

1. `JSONParsingError` 사용
2. 더 구체적인 예외 처리

```python
# 추가할 import
from selvage.src.exceptions.json_parsing_error import JSONParsingError

# validate_and_parse_json 메서드 수정
@staticmethod
def validate_and_parse_json(json_str: str, target_model: type[T]) -> T | None:
    """JSON 문자열을 검증하고 지정된 모델로 파싱합니다."""
    try:
        json_matches = re.findall(JSON_PATTERN, json_str)

        structured_response = None
        last_parsing_error = None

        for json_text in json_matches:
            try:
                # JSON 유효성 검사
                json.loads(json_text)
                structured_response = target_model.model_validate_json(json_text)
                break
            except (json.JSONDecodeError, ValueError, pydantic.ValidationError) as e:
                last_parsing_error = e
                console.error(f"JSON 파싱 오류: {str(json_text[:100])}...")
                continue

        if structured_response is None:
            console.warning("입력 문자열에서 유효한 JSON을 찾을 수 없습니다.")
            if last_parsing_error:
                raise JSONParsingError(
                    "JSON 파싱에 실패했습니다",
                    raw_response=json_str[:500] + "..." if len(json_str) > 500 else json_str,
                    parsing_error=last_parsing_error
                )
            return None
    except JSONParsingError:
        raise  # JSONParsingError는 그대로 재발생
    except Exception as parse_error:
        console.error(f"파싱 오류: {str(parse_error)}", exception=parse_error)
        if console.is_debug_mode():
            console.error(f"원본 응답: {json_str}")
        raise JSONParsingError(
            f"예상치 못한 파싱 오류: {str(parse_error)}",
            raw_response=json_str,
            parsing_error=parse_error
        )
    return structured_response
```

### 4.4 CLI 에러 처리

**파일 경로**: `selvage/cli.py`

**수정 내용**:

1. `_handle_api_error` 함수 개선
2. OpenRouter 관련 에러 처리 추가
3. 디버그 모드 지원 강화

```python
# 추가할 import들
from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterAPIError,
    OpenRouterResponseError,
    OpenRouterAuthenticationError,
)
from selvage.src.exceptions.json_parsing_error import JSONParsingError

# _handle_api_error 함수 수정
def _handle_api_error(error_response: ErrorResponse) -> None:
    """API 에러 처리"""

    # OpenRouter 관련 에러 특별 처리
    if isinstance(error_response.exception, OpenRouterAPIError):
        _handle_openrouter_error(error_response.exception)
    elif isinstance(error_response.exception, JSONParsingError):
        _handle_json_parsing_error(error_response.exception)
    else:
        # 기존 에러 처리 로직
        console.error(f"API 오류: {error_response.error_message}")

    raise Exception(f"API error: {error_response.error_message}")

def _handle_openrouter_error(error: OpenRouterAPIError) -> None:
    """OpenRouter 관련 에러 처리"""
    if isinstance(error, OpenRouterAuthenticationError):
        console.error("OpenRouter API 인증 오류")
        console.info("해결 방법:")
        console.print("  1. OPENROUTER_API_KEY 환경변수 확인")
        console.print("  2. API 키 유효성 확인")
    elif isinstance(error, OpenRouterResponseError):
        console.error(f"OpenRouter API 응답 구조 오류: {error}")
        if error.missing_field:
            console.error(f"누락된 필드: {error.missing_field}")
        if config.is_debug_mode() and error.raw_response:
            console.error(f"원본 응답: {error.raw_response}")
    else:
        console.error(f"OpenRouter API 오류: {error}")

def _handle_json_parsing_error(error: JSONParsingError) -> None:
    """JSON 파싱 에러 처리"""
    console.error("구조화된 응답 파싱에 실패했습니다")
    console.error(f"오류: {error}")

    if config.is_debug_mode():
        console.error("디버그 정보:")
        if error.parsing_error:
            console.error(f"  파싱 오류: {error.parsing_error}")
        if error.raw_response:
            console.error(f"  원본 응답 (일부): {error.raw_response}")
```

### 4.5 Console 디버그 모드 지원

**파일 경로**: `selvage/src/utils/base_console.py`

**수정 내용**:
디버그 모드 확인 메서드 추가 (config import 필요할 수 있음)

```python
def is_debug_mode(self) -> bool:
    """디버그 모드 여부 확인"""
    try:
        from selvage.src.config import config
        return config.is_debug_mode()
    except ImportError:
        return False
```

## 5. Exception 체계 재설계

### 5.1 기존 예외 체계 유지

- `LLMGatewayError`: 기본 예외 클래스 (변경 없음)
- 기존의 모든 예외들은 그대로 유지

### 5.2 새로운 예외 추가

1. **JSONParsingError**: 모든 JSON 파싱 오류

   - 범용적으로 사용 가능
   - raw_response와 parsing_error 정보 포함

2. **OpenRouterAPIError 계열**: OpenRouter 전용
   - OpenRouterResponseError: 응답 구조 문제
   - OpenRouterConnectionError: 연결 문제
   - OpenRouterAuthenticationError: 인증 문제 (재시도 금지)

## 6. 테스트 전략

** 주의: 테스트의 목적과 부합하게 테스트를 작성해야합니다. 테스트를 그저 성공시키기 위해 assert 값을 조작하면 안됩니다.
근본적인 문제와 테스트 대상 모듈의 목적과 구현을 정확히 테스트해야합니다.
만약 이 기준에 미흡할 것 같다면 즉시 작업을 멈추고 저에게 도움을 요청해주세요 \.**

### 6.1 Unit Tests

**새로 생성할 테스트 파일들**:

- `tests/test_retry_decorator.py`: retry decorator 테스트
- `tests/test_json_parsing_error.py`: JSON 파싱 예외 테스트
- `tests/test_openrouter_api_error.py`: OpenRouter 예외 테스트

### 6.2 Integration Tests

**수정할 테스트 파일들**:

- `tests/test_openrouter_gateway.py`: retry 로직 통합 테스트
- `tests/test_base_gateway.py`: BaseGateway retry 테스트

### 6.3 E2E Tests

- 실제 API 호출 시뮬레이션
- 다양한 에러 시나리오 테스트
- 재시도 동작 검증

## 7. 마이그레이션 가이드

### 7.1 Breaking Changes

없음 - 모든 변경사항은 backward compatible

### 7.2 새로운 기능

1. 자동 retry 기능 활성화
2. 더 구체적인 에러 메시지
3. 디버그 모드에서 raw response 노출

### 7.3 설정 옵션

- 환경변수나 config를 통한 retry 설정 커스터마이즈 가능성 (향후 확장)

## 8. 성능 및 안정성 고려사항

### 8.1 성능 영향

- retry로 인한 응답 시간 증가 (최대 약 7초 - 1+2+4초)
- 메모리 사용량 증가 미미 (raw_response 저장)

### 8.2 안정성 향상

- 간헐적 API 응답 문제 해결
- 더 나은 에러 진단 및 디버깅 지원
- 사용자에게 명확한 에러 해결 가이드 제공

### 8.3 모니터링

- retry 시도 횟수 로깅
- 실패 패턴 분석을 위한 로그 개선
- 성공/실패 비율 추적 가능

## 9. 구현 순서

1. **Dependency 추가**: pyproject.toml에 tenacity 추가
2. **Exception 클래스들 생성**: `json_parsing_error.py`, `openrouter_api_error.py`
3. **JSONExtractor 수정**: JSONParsingError 사용
4. **BaseGateway에 retry 적용**: tenacity decorator 적용
5. **OpenRouterGateway 수정**: 특화된 retry 및 예외 처리
6. **CLI 에러 처리 개선**: 구체적인 예외별 처리
7. **Console 디버그 모드 지원**: raw response 노출
8. **테스트 코드 작성 및 검증**
9. **문서화 업데이트**

## 10. Tenacity 사용의 장점

1. **검증된 안정성**: 널리 사용되는 라이브러리로 버그가 적음
2. **풍부한 기능**: 다양한 백오프 전략, 조건부 재시도, 로깅 지원
3. **유지보수성**: 자체 구현 대비 코드가 간결하고 이해하기 쉬움
4. **확장성**: 향후 다른 재시도 전략 추가 시 쉽게 변경 가능
5. **성능**: 최적화된 구현으로 오버헤드 최소화

## 11. Tenacity 설정 옵션

- `stop_after_attempt(n)`: n번 시도 후 중단
- `wait_exponential(multiplier, min, max)`: 지수 백오프
- `retry_if_exception_type(exceptions)`: 특정 예외만 재시도
- `before_sleep_log()`: 재시도 전 로그
- `after_log()`: 완료 후 로그

이 명세를 바탕으로 단계별 구현을 진행하면 안정적이고 유지보수성이 높은 retry 시스템을 구축할 수 있습니다.
