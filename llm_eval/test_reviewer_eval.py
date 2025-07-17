"""selvage 애플리케이션의 코드 리뷰 결과를 DeepEval로 평가하는 테스트."""

import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import GEval, JsonCorrectnessMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from selvage.src.utils.token.models import (
    IssueSeverityEnum,
    StructuredReviewIssue,
    StructuredReviewResponse,
)

model = "gemini-2.5-pro"
# Correctness GEval - 코드 리뷰 정확성 평가
# """
# # criteria="코드 리뷰 결과가 실제 코드 변경 사항에 대해 정확한 분석과 제안을 제공하는지 평가합니다.",
# evaluation_steps
# # 코드 리뷰 결과에서 식별된 이슈들이 실제 코드 변경 사항과 일치하는지 확인합니다.
# # 파일명과 라인 번호가 정확하게 지정되었는지 확인합니다.
# # 식별된 문제 유형(버그, 보안, 성능, 스타일, 설계)이 해당 코드에 적절한지 평가합니다.
# # 심각도 레벨(info, warning, error)이 이슈의 실제 중요도에 맞게 할당되었는지 확인합니다.
# # 이슈 설명이 코드 변경 사항의 실제 영향을 올바르게 반영하는지 검토합니다.
# """
# correctness = GEval(
#     name="Correctness",
#     model=model,
#     evaluation_steps=[
#         "Verify that the issues identified in the code review match the actual code changes.",
#         "Check if filenames and line numbers are accurately specified.",
#         "Evaluate whether the identified issue types (bug, security, performance, style, design) are appropriate for the code.",
#         "Confirm that severity levels (info, warning, error) are assigned appropriately based on the actual importance of the issue.",
#         "Review whether the issue descriptions accurately reflect the actual impact of the code changes.",
#     ],
#     evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
#     threshold=0.7,
# )

"""
Correctness GEval - 코드 리뷰 정확성 평가
입력 코드에서 발견된 모든 관련 주요 이슈(예: 버그, 보안 취약점, 성능 문제, 중대한 스타일/설계 결함)가 'issues' 배열에 보고되었는지 확인합니다.
출력의 'issues' 배열이 비어 있는 경우, 입력 코드를 비판적으로 평가하여 이 비어 있음이 실제 관련 이슈의 부재로 정당화되는 것인지, 탐지 실패가 아닌지 확인합니다.
이슈가 보고된 경우, 명시된 파일명과 라인 번호가 정확한지 확인합니다.
이슈가 보고된 경우, 식별된 유형(버그, 보안, 성능, 스타일, 디자인)이 해당 코드에 적절한지 평가합니다.
이슈가 보고된 경우, 심각도 수준(info, warning, error)이 각 이슈의 실제 영향에 따라 적절히 할당되었는지 확인합니다.
이슈가 보고된 경우, 해당 설명이 코드 변경의 영향을 정확하고 사실적으로 반영하는지 검토합니다.
(입력 코드에 관련 이슈가 존재하지 않아) 'issues' 배열이 정당하게 비어 있는 경우, 'summary'가 시스템 프롬프트 가이드라인에 따라 이 상황을 적절히 명시하는지 확인합니다.
"""
correctness = GEval(
    name="Correctness",
    model=model,
    evaluation_steps=[
        "Verify that all pertinent issues (e.g., bugs, security vulnerabilities, performance issues, significant style/design flaws) found in the input code are reported in the 'issues' array.",
        "If the 'issues' array in the output is empty, critically assess the input code to confirm this emptiness is justified by an actual absence of pertinent issues, not a failure of detection.",
        "If issues are reported, check if their specified filenames and line numbers are accurate.",
        "If issues are reported, evaluate if their identified types (bug, security, performance, style, design) are appropriate for the code.",
        "If issues are reported, confirm if their severity levels (info, warning, error) are assigned according to the actual impact of each issue.",
        "If issues are reported, review if their descriptions accurately and factually reflect the impact of the code changes.",
        "If the 'issues' array is legitimately empty (because no pertinent issues exist in the input code), verify that the 'summary' appropriately states this, aligning with system prompt guidelines.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
    threshold=0.7,
)

"""
# criteria="코드 리뷰 피드백이 명확하고 이해하기 쉬운지 평가합니다.",
evaluation_steps
# 코드 리뷰 설명이 간결하고 직접적인 언어를 사용하는지 평가합니다.
# 이슈 설명과 제안과 추천이 구체적이고 명확한지 평가합니다.
# 코드 변경의 목적과 의도를 명확하게 이해할 수 있는지 검토합니다.
# 개선된 코드 예시가 제공되었고 이해하기 쉬운지 확인합니다.
"""
# Clarity GEval - 코드 리뷰 명확성 평가
clarity = GEval(
    name="Clarity",
    model=model,
    evaluation_steps=[
        "Evaluate whether the overall code review output (including summary, and if present, issue descriptions, suggestions, and recommendations) uses concise and direct language.",
        "Assess whether issue descriptions and suggestions and recommendations are specific and clear.",
        "Review if the purpose and intent of code changes are clearly understandable.",
        "Verify that improved code examples are provided and easy to understand.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)

"""
# criteria="코드 리뷰 피드백이 실제로 적용 가능한 구체적인 제안을 포함하는지 평가합니다.",
evaluation_steps
# 각 이슈에 대해 구체적인 해결책이 제시되었는지 확인합니다.
# 제안된 개선 사항이 실제로 구현 가능한지 평가합니다.
# 코드 개선 예시가 실제 코드베이스에 통합될 수 있을 만큼 구체적인지 검토합니다.
# 제안이 코드 품질, 성능, 보안 등의 측면에서 실질적인 개선을 가져올 수 있는지 평가합니다.
# 전반적인 권장사항이 프로젝트 맥락에서 실행 가능한지 확인합니다.
"""
# Actionability GEval - 코드 리뷰 실행 가능성 평가
actionability = GEval(
    name="Actionability",
    model=model,
    evaluation_steps=[
        "Check if specific solutions are provided for each issue.",
        "Evaluate whether the suggested improvements are practically implementable.",
        "Review if code improvement examples are specific enough to be integrated into the actual codebase.",
        "Assess whether the suggestions can bring substantial improvements in terms of code quality, performance, security, etc.",
        "Confirm that overall recommendations are actionable within the project context.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
    threshold=0.7,
)

jsoncorrectness = JsonCorrectnessMetric(
    expected_schema=StructuredReviewResponse(
        issues=[
            StructuredReviewIssue(
                type="",
                line_number=0,
                file="",
                description="",
                suggestion="",
                severity=IssueSeverityEnum.INFO,
                target_code="",
                suggested_code="",
            )
        ],
        summary="",
        score=0,
        recommendations=[],
    ),
    model=model,
    include_reason=True,
)

dataset = EvaluationDataset()
dataset.add_test_cases_from_json_file(
    file_path="llm_eval/data_set/test_data_20250523_115314.json",
    input_key_name="input",
    actual_output_key_name="actual_output",
)


@pytest.mark.parametrize(
    "test_case",
    dataset,
)
def test_code_review_evaluation(test_case: LLMTestCase):
    """코드 리뷰 평가 테스트."""
    assert_test(
        test_case,
        metrics=[correctness, clarity, actionability, jsoncorrectness],
        # run_async=False,
    )
