"""
LLM Gateway의 코드 리뷰 기능을 테스트하는 모듈입니다.
"""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import instructor
import pytest
from google import genai

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.models import Hunk
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.model_config import ModelInfoDict, ModelParamsDict, ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.prompts.models import (
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.token.models import (
    IssueSeverityEnum,
    ReviewResponse,
    StructuredReviewIssue,
    StructuredReviewResponse,
)


@pytest.fixture
def model_info_fixture() -> ModelInfoDict:
    params: ModelParamsDict = {"temperature": 0.0}
    model_info: ModelInfoDict = {
        "full_name": "test-model-fixture",
        "aliases": ["test-fixture"],
        "description": "Fixture를 사용한 테스트용 모델",
        "provider": ModelProvider.OPENAI,
        "params": params,
        "thinking_mode": False,
        "pricing": {
            "input": 0.002,
            "output": 0.004,
            "description": "Test model pricing",
        },
        "context_limit": 128000,
    }
    return model_info


@pytest.fixture
def google_model_info_fixture() -> ModelInfoDict:
    params: ModelParamsDict = {"temperature": 0.1}
    model_info: ModelInfoDict = {
        "full_name": "google-test-model-fixture",
        "aliases": ["google-test-fixture"],
        "description": "Fixture를 사용한 Google 테스트용 모델",
        "provider": ModelProvider.GOOGLE,
        "params": params,
        "thinking_mode": False,
        "pricing": {
            "input": 0.001,
            "output": 0.002,
            "description": "Test model pricing",
        },
        "context_limit": 1048576,
    }
    return model_info


@pytest.fixture
def review_prompt_fixture() -> ReviewPromptWithFileContent:
    system_prompt = SystemPrompt(role="system", content="코드를 분석하고 리뷰하세요.")

    # Hunk 객체 생성
    hunk = Hunk(
        header="@@ -1,1 +1,1 @@",
        content=" def example(): pass\n-def example(): pass\n+def example(): return 'Hello'",
        before_code="def example(): pass",
        after_code="def example(): return 'Hello'",
        start_line_original=1,
        line_count_original=1,
        start_line_modified=1,
        line_count_modified=1,
        change_line=LineRange(start_line=1, end_line=1),
    )

    # FileContextInfo 생성
    file_context = FileContextInfo.create_full_context("def example(): pass")

    user_prompt = UserPromptWithFileContent(
        file_name="example.py",
        file_context=file_context,
        hunks=[hunk],
        language="python",
    )
    return ReviewPromptWithFileContent(
        system_prompt=system_prompt, user_prompts=[user_prompt]
    )


class MockBaseGateway(BaseGateway):
    """BaseGateway 추상 클래스를 상속받은 테스트용 구현체"""

    def __init__(
        self, model_info: ModelInfoDict, api_key: str | None = "fake-api-key"
    ) -> None:
        self.model: ModelInfoDict
        self._set_model(model_info)
        self.api_key = api_key if api_key is not None else self._load_api_key()

    def _load_api_key(self) -> str:
        return "fake-api-key"

    def _set_model(self, model_info: ModelInfoDict) -> None:
        self.model = model_info

    def _create_request_params(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return {"model": self.get_model_name(), "messages": messages}

    def get_model_name(self):
        return self.model["full_name"]

    def get_provider(self) -> ModelProvider:
        return self.model["provider"]




@patch("selvage.src.llm_gateway.base_gateway.BaseGateway._create_client")
def test_review_code_success_with_instructor(
    mock_create_client,
    model_info_fixture: ModelInfoDict,
    review_prompt_fixture: ReviewPromptWithFileContent,
):
    """Instructor 클라이언트를 사용한 성공적인 리뷰 코드 호출을 테스트합니다."""
    mock_instructor = MagicMock(spec=instructor.Instructor)
    mock_completions = MagicMock()
    mock_instructor.chat.completions = mock_completions

    # 테스트용 상세 응답 데이터
    expected_issues_data = [
        {
            "type": "issue",
            "description": "함수에 구현 내용이 없습니다.",
            "file": "example.py",
            "suggestion": "함수에 의미 있는 구현을 추가하세요.",
            "severity": IssueSeverityEnum.WARNING,
            "target_code": "def example(): pass",
            "suggested_code": "def example(): return 'Hello'",
        },
        {
            "type": "suggestion",
            "description": "변수명을 더 명확하게 변경하세요.",
            "file": "another_module.py",
            "suggestion": "예: `data_list` -> `user_records`",
            "severity": IssueSeverityEnum.INFO,
            "target_code": "data = get_data()",
            "suggested_code": "user_records = get_data()",
        },
    ]
    expected_summary = "코드에 몇 가지 개선 사항이 있습니다."
    expected_score = 75.0
    expected_recommendations = ["명확한 변수명 사용", "함수 구현 추가"]

    structured_response_data = StructuredReviewResponse(
        issues=[StructuredReviewIssue(**data) for data in expected_issues_data],
        summary=expected_summary,
        score=expected_score,
        recommendations=expected_recommendations,
    )
    mock_completions.create_with_completion.return_value = (
        structured_response_data,
        None,
    )
    mock_create_client.return_value = mock_instructor

    with patch.object(MockBaseGateway, "_create_request_params") as mock_create_params:
        mock_create_params.return_value = {
            "model": model_info_fixture["full_name"],
            "messages": [],
            "temperature": 0.0,
        }
        gateway = MockBaseGateway(model_info_fixture)
        review_result: ReviewResult = gateway.review_code(review_prompt_fixture)
        response: ReviewResponse = review_result.review_response
        mock_create_client.assert_called_once()
        mock_create_params.assert_called_once()

        assert response.summary == expected_summary
        assert response.score == expected_score
        assert response.recommendations == expected_recommendations
        assert len(response.issues) == len(expected_issues_data)
        for i, actual_issue in enumerate(response.issues):
            expected_issue_data = expected_issues_data[i]
            assert actual_issue.type == expected_issue_data["type"]
            assert actual_issue.description == expected_issue_data["description"]
            # line_number는 LineNumberCalculator에 의해 계산되므로 파일이 없는 경우 None
            assert actual_issue.line_number is None  # 테스트에서는 실제 파일이 없음
            assert actual_issue.file == expected_issue_data["file"]
            assert actual_issue.suggestion == expected_issue_data["suggestion"]
            assert actual_issue.severity == expected_issue_data["severity"].value
            assert actual_issue.target_code == expected_issue_data["target_code"]
            assert actual_issue.suggested_code == expected_issue_data["suggested_code"]


@patch("selvage.src.llm_gateway.base_gateway.BaseGateway._create_client")
def test_review_code_success_with_genai(
    mock_create_client,
    google_model_info_fixture: ModelInfoDict,
    review_prompt_fixture: ReviewPromptWithFileContent,
):
    """genai 클라이언트를 사용한 성공적인 리뷰 코드 호출을 테스트합니다."""
    mock_genai_client = MagicMock(spec=genai.Client)
    mock_genai_models = MagicMock()
    mock_genai_client.models = mock_genai_models
    mock_genai_response = MagicMock()

    expected_issues_raw_data = [
        {
            "type": "issue",
            "description": "genai: 함수 구현 필요",
            "severity": "warning",
            "file": "main.py",
            "suggestion": "빠르게 구현해주세요.",
            "target_code": "def main():",
            "suggested_code": "def main():\\n    print('Hello from GenAI')",
        }
    ]
    expected_summary_genai = "GenAI 리뷰: 요약입니다."
    expected_score_genai = 80.0
    expected_recommendations_genai = ["GenAI 권장 사항1", "GenAI 권장 사항2"]

    # JSON 문자열 생성 시, 내부 문자열 값에 포함된 특수문자가 올바르게 이스케이프되도록 직접 구성
    # json.dumps를 문자열 전체가 아닌, 개별 문자열 값에만 적용하거나, 수동으로 이스케이프
    issues_list_for_json = [
        {
            "type": expected_issues_raw_data[0]["type"],
            "description": expected_issues_raw_data[0]["description"],
            "severity": expected_issues_raw_data[0]["severity"],
            "line_number": None,  # LineNumberCalculator에 의해 계산되므로 LLM은 None 반환
            "file": expected_issues_raw_data[0]["file"],
            "suggestion": expected_issues_raw_data[0]["suggestion"],
            "target_code": expected_issues_raw_data[0]["target_code"],
            "suggested_code": expected_issues_raw_data[0]["suggested_code"],
        }
    ]

    mock_genai_response.text = f"""
    {{
        "issues": {json.dumps(issues_list_for_json)},
        "summary": "{expected_summary_genai}", 
        "score": {expected_score_genai}, 
        "recommendations": {json.dumps(expected_recommendations_genai)}
    }}
    """
    mock_genai_models.generate_content.return_value = mock_genai_response
    mock_create_client.return_value = mock_genai_client

    with patch.object(MockBaseGateway, "_create_request_params") as mock_create_params:
        mock_create_params.return_value = {
            "model": google_model_info_fixture["full_name"],
            "contents": "content",
            "config": MagicMock(),
        }
        gateway = MockBaseGateway(google_model_info_fixture)
        review_result: ReviewResult = gateway.review_code(review_prompt_fixture)
        response: ReviewResponse = review_result.review_response

        mock_create_client.assert_called_once()
        mock_create_params.assert_called_once()

        assert response.summary == expected_summary_genai
        assert response.score == expected_score_genai
        assert response.recommendations == expected_recommendations_genai
        assert len(response.issues) == len(expected_issues_raw_data)
        for i, actual_issue in enumerate(response.issues):
            expected_issue_data = expected_issues_raw_data[i]
            assert actual_issue.type == expected_issue_data["type"]
            assert actual_issue.description == expected_issue_data["description"]
            # line_number는 LineNumberCalculator에 의해 계산되므로 파일이 없는 경우 None
            assert actual_issue.line_number is None  # 테스트에서는 실제 파일이 없음
            assert actual_issue.file == expected_issue_data["file"]
            assert actual_issue.suggestion == expected_issue_data["suggestion"]
            assert actual_issue.severity == expected_issue_data["severity"]
            assert actual_issue.target_code == expected_issue_data["target_code"]
            assert actual_issue.suggested_code == expected_issue_data["suggested_code"]


@patch("selvage.src.llm_gateway.base_gateway.BaseGateway._create_client")
def test_review_code_empty_response(
    mock_create_client,
    model_info_fixture: ModelInfoDict,
    review_prompt_fixture: ReviewPromptWithFileContent,
):
    """빈 응답 처리를 테스트합니다."""
    mock_instructor = MagicMock(spec=instructor.Instructor)
    mock_completions = MagicMock()
    mock_instructor.chat.completions = mock_completions
    mock_completions.create_with_completion.return_value = None, None
    mock_create_client.return_value = mock_instructor

    gateway = MockBaseGateway(model_info_fixture)
    review_result: ReviewResult = gateway.review_code(review_prompt_fixture)
    response: ReviewResponse = review_result.review_response

    assert len(response.issues) == 0
    assert "비어있" in response.summary


@patch("selvage.src.llm_gateway.base_gateway.BaseGateway._create_client")
def test_review_code_error_handling(
    mock_create_client,
    model_info_fixture: ModelInfoDict,
    review_prompt_fixture: ReviewPromptWithFileContent,
):
    """예외 처리를 테스트합니다."""
    mock_create_client.side_effect = Exception("API 호출 중 오류 발생")

    gateway = MockBaseGateway(model_info_fixture)
    review_result: ReviewResult = gateway.review_code(review_prompt_fixture)
    response: ReviewResponse = review_result.review_response

    assert len(response.issues) == 0
    assert "오류 발생" in response.summary


@patch("selvage.src.llm_gateway.base_gateway.BaseGateway._create_client")
def test_review_code_parsing_error(
    mock_create_client,
    google_model_info_fixture: ModelInfoDict,
    review_prompt_fixture: ReviewPromptWithFileContent,
):
    """Google API 응답 파싱 오류 처리를 테스트합니다."""
    mock_genai_client = MagicMock(spec=genai.Client)
    mock_genai_models = MagicMock()
    mock_genai_client.models = mock_genai_models
    mock_genai_response = MagicMock()
    mock_genai_response.text = """{"issues": [{"type": "issue", "description": "desc", "line_number": invalid_value}]}"""  # 잘못된 JSON
    mock_genai_models.generate_content.return_value = mock_genai_response
    mock_create_client.return_value = mock_genai_client

    with patch.object(MockBaseGateway, "_create_request_params"):
        gateway = MockBaseGateway(google_model_info_fixture)
        review_result: ReviewResult = gateway.review_code(review_prompt_fixture)
        response: ReviewResponse = review_result.review_response

        assert len(response.issues) == 0
        assert "API 처리 중 오류" in response.summary


if __name__ == "__main__":
    pytest.main()
