"""MCP 서버 통합 테스트"""

from unittest.mock import Mock, patch

import pytest_asyncio

from selvage.src.mcp.server import SelvageMCPServer
from selvage.src.mcp.tools.review_tools import (
    review_against_branch,
    review_against_commit,
    review_current_changes,
    review_staged_changes,
)
from selvage.src.mcp.tools.utility_tools import (
    get_available_models,
    get_review_details,
    get_review_history,
    get_server_status,
    validate_api_key_for_provider,
    validate_model_support,
)


class MCPServerTestHelper:
    """MCP 서버 테스트를 위한 헬퍼 클래스"""

    def __init__(self):
        self.server = SelvageMCPServer()

    def get_server_info(self) -> dict:
        """서버 정보를 반환합니다."""
        return self.server.get_tools_info()


@pytest_asyncio.fixture
async def mcp_server():
    """MCP 서버 테스트 헬퍼 픽스처"""
    helper = MCPServerTestHelper()
    yield helper


class TestMCPServerIntegration:
    """MCP 서버 통합 테스트"""

    def test_server_initialization(self, mcp_server: MCPServerTestHelper) -> None:
        """서버가 올바르게 초기화되는지 테스트"""
        server_info = mcp_server.get_server_info()

        assert server_info["server_name"] == "Selvage Code Review Server"
        assert server_info["transport"] == "stdio"
        assert server_info["tools_registered"] is True

        # 모든 예상 도구가 등록되어 있는지 확인
        expected_review_tools = [
            "review_current_changes_tool",
            "review_staged_changes_tool",
            "review_against_branch_tool",
            "review_against_commit_tool",
        ]
        expected_utility_tools = [
            "get_available_models_tool",
            "get_review_history_tool",
            "get_review_details_tool",
            "get_server_status_tool",
            "validate_model_support_tool",
            "validate_api_key_for_provider_tool",
        ]

        assert server_info["review_tools"] == expected_review_tools
        assert server_info["utility_tools"] == expected_utility_tools

    def test_get_server_status_function(self) -> None:
        """서버 상태 조회 함수 테스트"""
        status = get_server_status()

        assert status.running is True
        assert status.port is None  # stdio 모드
        assert status.host is None  # stdio 모드
        assert status.start_time is None
        assert isinstance(status.version, str)
        assert status.tools_count == 10

    def test_get_available_models_function(self) -> None:
        """사용 가능한 모델 조회 함수 테스트"""
        models = get_available_models()

        assert isinstance(models, list)
        # 모델이 있다면 각 모델은 ModelInfo 객체여야 함
        for model in models:
            assert hasattr(model, "name")
            assert hasattr(model, "provider")
            assert hasattr(model, "display_name")

    def test_validate_model_support_function_valid_model(self) -> None:
        """유효한 모델 지원 여부 검증 함수 테스트"""
        from selvage.src.mcp.models.responses import ModelValidationResult

        # 실제 존재하는 모델로 테스트
        result = validate_model_support("claude-sonnet-4.5-20250929")

        assert isinstance(result, ModelValidationResult)
        assert result.model == "claude-sonnet-4.5-20250929"

        if result.valid:
            assert result.provider is not None

    def test_validate_model_support_function_invalid_model(self) -> None:
        """무효한 모델 지원 여부 검증 함수 테스트"""
        from selvage.src.mcp.models.responses import ModelValidationResult

        result = validate_model_support("invalid-model-name-12345")

        assert isinstance(result, ModelValidationResult)
        assert result.valid is False
        assert result.error_message is not None

    def test_validate_api_key_for_provider_function(self) -> None:
        """API 키 검증 함수 테스트"""
        from selvage.src.mcp.models.responses import ApiKeyValidationResult

        result = validate_api_key_for_provider("claude-sonnet-4.5-20250929")

        assert isinstance(result, ApiKeyValidationResult)
        # API 키가 있든 없든 올바른 구조로 반환되어야 함
        # OpenRouter 키가 있으면 "OpenRouter", 없으면 "Anthropic" 또는 검증 실패
        assert result.provider in ["OpenRouter", "Anthropic"] or result.valid is False

    def test_get_review_history_function(self) -> None:
        """리뷰 히스토리 조회 함수 테스트"""
        history = get_review_history(limit=5, repo_path=".", model_filter=None)

        assert isinstance(history, list)
        # 히스토리가 있다면 각 항목은 ReviewHistoryItem 객체여야 함
        for item in history:
            assert hasattr(item, "log_id")
            assert hasattr(item, "timestamp")
            assert hasattr(item, "model")
            assert hasattr(item, "status")

    def test_get_review_details_function_invalid_id(self) -> None:
        """잘못된 로그 ID로 리뷰 상세 조회 함수 테스트"""
        details = get_review_details("invalid-log-id-12345")

        assert hasattr(details, "success")
        assert hasattr(details, "error_message")
        # 에러 정보가 포함되어야 함
        assert details.success is False
        assert details.error_message is not None

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_current_changes_function(self, mock_workflow: Mock) -> None:
        """현재 변경사항 리뷰 함수 테스트"""
        from selvage.src.mcp.models.responses import ReviewResult

        # Mock 설정
        mock_result = ReviewResult(
            success=True,
            estimated_cost=0.05,
            model_used="claude-sonnet-4.5-20250929",
            files_reviewed=["test.py"],
        )
        mock_workflow.return_value = mock_result

        # 함수 호출
        result = review_current_changes(
            model="claude-sonnet-4.5-20250929",
            repo_path="/test/repo",
        )

        # 검증
        assert result.success is True
        assert result.model_used == "claude-sonnet-4.5-20250929"
        assert result.response is None  # response는 선택적 필드
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5-20250929",
            repo_path="/test/repo",
            staged=False,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_staged_changes_function(self, mock_workflow: Mock) -> None:
        """스테이징된 변경사항 리뷰 함수 테스트"""
        from selvage.src.mcp.models.responses import ReviewResult

        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5-20250929",
        )

        result = review_staged_changes(model="claude-sonnet-4.5-20250929", repo_path="/test/repo")

        assert result.success is True
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5-20250929",
            repo_path="/test/repo",
            staged=True,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_against_branch_function(self, mock_workflow: Mock) -> None:
        """브랜치 대비 리뷰 함수 테스트"""
        from selvage.src.mcp.models.responses import ReviewResult

        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5-20250929",
        )

        result = review_against_branch(
            model="claude-sonnet-4.5-20250929",
            target_branch="main",
            repo_path="/test/repo",
        )

        assert result.success is True
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5-20250929",
            repo_path="/test/repo",
            target_branch="main",
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_against_commit_function(self, mock_workflow: Mock) -> None:
        """커밋 대비 리뷰 함수 테스트"""
        from selvage.src.mcp.models.responses import ReviewResult

        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5-20250929",
        )

        result = review_against_commit(
            model="claude-sonnet-4.5-20250929",
            target_commit="abc1234",
            repo_path="/test/repo",
        )

        assert result.success is True
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5-20250929",
            repo_path="/test/repo",
            target_commit="abc1234",
        )


class TestMCPServerErrorHandling:
    """MCP 서버 에러 처리 테스트"""

    def test_invalid_model_validation(self) -> None:
        """존재하지 않는 모델 검증 테스트"""
        from selvage.src.mcp.models.responses import ModelValidationResult

        result = validate_model_support("non-existent-model-12345")

        assert isinstance(result, ModelValidationResult)
        assert result.valid is False
        assert result.error_message is not None

    def test_invalid_log_id_review_details(self) -> None:
        """존재하지 않는 로그 ID로 상세 조회 테스트"""
        details = get_review_details("invalid-log-id-67890")

        assert hasattr(details, "success")
        assert hasattr(details, "error_message")
        assert details.success is False
        assert details.error_message is not None


class TestMCPServerFunctionalIntegration:
    """MCP 서버 기능 통합 테스트"""

    def test_server_basic_functionality(self) -> None:
        """서버의 기본 기능 테스트"""
        # 서버 상태 조회
        status = get_server_status()
        assert status.running is True
        assert status.tools_count == 10

        # 모델 목록 조회
        models = get_available_models()
        assert isinstance(models, list)

        # 히스토리 조회
        history = get_review_history(limit=1)
        assert isinstance(history, list)
