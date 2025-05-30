# DeepEval 설정 및 사용 가이드

## 설치 환경

- Python 버전: 3.13.2
- 설치된 패키지:
  - deepeval
  - aiobotocore (DeepEval의 Amazon Bedrock 기능을 위해 필요)

## 설치 방법

```bash
# 기본 설치
pip install deepeval

# Amazon Bedrock 기능을 위한 추가 패키지 설치
pip install aiobotocore
```

## 테스트 예제

### 1. 기본 테스트 (`test_deepeval_hello_world.py`)

간단한 "Hello World" 수준의 테스트로, DeepEval이 올바르게 설치되었는지 확인합니다.

```python
import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# 모의 LLM 응답 함수
def get_llm_response(user_input: str) -> str:
    if "안녕" in user_input:
        return "안녕하세요! 무엇을 도와드릴까요?"
    elif "날씨" in user_input:
        return "오늘 서울의 날씨는 맑습니다."
    else:
        return "죄송합니다. 잘 이해하지 못했어요."

# 응답 관련성 테스트
def test_hello_world_answer_relevancy():
    input_query = "안녕"
    actual_output = get_llm_response(input_query)

    metric = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o")
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output
    )

    assert_test(test_case, [metric])
```

### 2. 고급 테스트 (`test_deepeval_advanced.py`)

여러 평가 지표를 사용한 고급 테스트 예제입니다.

```python
from typing import List, Optional
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    ToxicityMetric,
    ContextualRelevancyMetric,
    ContextualPrecisionMetric,
)
from deepeval.test_case import LLMTestCase

# 여러 지표를 사용한 복합 테스트
def test_multiple_metrics():
    input_query = "파이썬 프로그래밍 언어에 대해 알려주세요."
    actual_output = get_llm_response(input_query)

    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model="gpt-4o"),
        BiasMetric(threshold=0.3, model="gpt-4o"),
        ToxicityMetric(threshold=0.1, model="gpt-4o")
    ]

    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output
    )

    assert_test(test_case, metrics)

# 컨텍스트 기반 테스트
def test_context_based_metrics():
    context_text = "서울의 오늘 날씨는 맑고 기온은 25도입니다."
    input_query = "오늘 날씨 어때요?"
    actual_output = get_llm_response(input_query, context_text)
    expected_output = "오늘 서울은 맑고 기온은 25도입니다."

    metrics = [
        ContextualRelevancyMetric(threshold=0.7, model="gpt-4o"),
        ContextualPrecisionMetric(threshold=0.7, model="gpt-4o"),
    ]

    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        context=[context_text],
        retrieval_context=[context_text],
        expected_output=expected_output
    )

    assert_test(test_case, metrics)
```

## 테스트 실행 방법

```bash
# 기본 테스트 실행
deepeval test run ./llm_eval/test_deepeval_hello_world.py -v

# 고급 테스트 실행
deepeval test run ./llm_eval/test_deepeval_advanced.py -v

# 모든 테스트 실행
deepeval test run ./llm_eval
```

## 주요 평가 지표

DeepEval은 다양한 평가 지표를 제공합니다:

1. **AnswerRelevancyMetric**: 응답이 입력 질문과 얼마나 관련이 있는지 평가
2. **BiasMetric**: 응답에 편향성이 있는지 평가
3. **ToxicityMetric**: 응답에 유해한 내용이 있는지 평가
4. **ContextualRelevancyMetric**: 응답이 주어진 컨텍스트와 얼마나 관련이 있는지 평가
5. **ContextualPrecisionMetric**: 응답이 컨텍스트 정보를 얼마나 정확하게 활용하는지 평가

## 참고 사항

- 실행을 위해 실제 API 키 설정이 필요합니다.

## 참고 자료

- [DeepEval 공식 문서](https://docs.confident-ai.com/docs/getting-started)
- [Pytest 통합 가이드](https://docs.confident-ai.com/docs/getting-started-pytest)
- [테스트 케이스 개념](https://docs.confident-ai.com/docs/concepts-test-cases)
- [어설션 사용법](https://docs.confident-ai.com/docs/assertion-python-sdk)
