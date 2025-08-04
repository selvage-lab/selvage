"""DeepEval을 사용한 고급 테스트 예제."""

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    ContextualPrecisionMetric,
    ContextualRelevancyMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase


# 테스트할 LLM 응답 함수 (실제 LLM을 호출하는 대신 간단한 mock 함수 사용)
def get_llm_response(user_input: str, context: str | None = None) -> str:
    """사용자 입력과 컨텍스트에 따라 응답을 반환하는 모의 LLM 함수."""
    if "파이썬" in user_input:
        return "파이썬은 가독성이 좋고 다양한 라이브러리를 갖춘 프로그래밍 언어입니다."
    elif "딥러닝" in user_input:
        return "딥러닝은 인공신경망을 사용하여 데이터로부터 패턴을 학습하는 기계학습의 한 분야입니다."
    elif context and "날씨" in context:
        return "제공된 정보에 따르면, 오늘은 맑은 날씨가 예상됩니다."
    else:
        return "질문에 대한 정확한 답변을 드리기 어렵습니다. 더 자세한 정보를 제공해주시겠어요?"


# 여러 지표를 사용한 복합 테스트
@pytest.mark.skip(reason="DeepEval CLI에서 실행 제외")
def test_multiple_metrics():
    """여러 평가 지표를 사용한 테스트."""
    input_query = "파이썬 프로그래밍 언어에 대해 알려주세요."
    actual_output = get_llm_response(input_query)

    # 여러 평가 지표 설정
    metrics = [
        AnswerRelevancyMetric(threshold=0.7, model="o4-mini"),
        BiasMetric(threshold=0.3, model="o4-mini"),
        ToxicityMetric(threshold=0.1, model="o4-mini"),
    ]

    test_case = LLMTestCase(input=input_query, actual_output=actual_output)

    assert_test(test_case, metrics)


# 컨텍스트 기반 테스트
@pytest.mark.skip(reason="DeepEval CLI에서 실행 제외")
def test_context_based_metrics():
    """컨텍스트 기반 평가 지표를 사용한 테스트."""
    context_text = "서울의 오늘 날씨는 맑고 기온은 25도입니다."
    input_query = "오늘 날씨 어때요?"
    actual_output = get_llm_response(input_query, context_text)
    expected_output = "오늘 서울은 맑고 기온은 25도입니다."

    # 컨텍스트 기반 평가 지표
    metrics = [
        ContextualRelevancyMetric(threshold=0.7, model="o4-mini"),
        ContextualPrecisionMetric(threshold=0.7, model="o4-mini"),
    ]

    # ContextualRelevancyMetric은 retrieval_context 매개변수가 필요함
    # ContextualPrecisionMetric은 expected_output 매개변수가 필요함
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        context=[context_text],
        retrieval_context=[context_text],
        expected_output=expected_output,
    )

    assert_test(test_case, metrics)
