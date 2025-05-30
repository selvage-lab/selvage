"""DeepEval을 사용한 간단한 'Hello World' 테스트 예제."""

import pytest
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


# 테스트할 LLM 응답 함수 (실제 LLM을 호출하는 대신 간단한 mock 함수 사용)
def get_llm_response(user_input: str) -> str:
    """사용자 입력에 따라 간단한 응답을 반환하는 모의 LLM 함수."""
    if "안녕" in user_input:
        return "안녕하세요! 무엇을 도와드릴까요?"
    elif "날씨" in user_input:
        return "오늘 서울의 날씨는 맑습니다."
    else:
        return "죄송합니다. 잘 이해하지 못했어요."


# 기본적인 AnswerRelevancyMetric 테스트
@pytest.mark.skip(reason="DeepEval CLI에서 실행 제외")
def test_hello_world_answer_relevancy():
    """응답 관련성 지표를 사용한 기본 테스트."""
    input_query = "안녕"
    actual_output = get_llm_response(input_query)

    # 참고: 실제 환경에서는 API 키 설정이 필요할 수 있습니다.
    # 환경 변수 또는 다음과 같이 직접 설정:
    # from deepeval import confident_ai
    # confident_ai.api_key = "YOUR_API_KEY"

    metric = AnswerRelevancyMetric(threshold=0.7, model="o4-mini")
    test_case = LLMTestCase(input=input_query, actual_output=actual_output)

    assert_test(test_case, [metric])


# 예상 결과를 사용하는 테스트 예시
@pytest.mark.skip(reason="DeepEval CLI에서 실행 제외")
def test_expected_output_example():
    """예상 결과를 포함한 테스트 예시."""
    input_query = "오늘 날씨 어때?"
    actual_output = get_llm_response("날씨")  # 일부러 약간 다른 입력 사용
    expected_similar_output = "오늘 날씨는 좋습니다."  # 의미상 유사한 기대 결과

    metric = AnswerRelevancyMetric(threshold=0.5, model="o4-mini")
    test_case = LLMTestCase(
        input=input_query,
        actual_output=actual_output,
        expected_output=expected_similar_output,  # 이 지표에서는 참고용으로만 사용될 수 있음
    )

    assert_test(test_case, [metric])
