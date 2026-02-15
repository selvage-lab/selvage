"""MCP 리뷰 도구 테스트"""

import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

from selvage.src.config import APIKeyNotFoundError, ModelProvider
from selvage.src.mcp.models.responses import ReviewResult
from selvage.src.mcp.tools.review_tools import (
    register_review_tools,
    review_changes,
)


class TestReviewToolsRegistration:
    """MCP 리뷰 도구 등록 테스트"""

    def test_register_review_tools_function_exists(self) -> None:
        """register_review_tools 함수가 존재해야 함"""
        assert callable(register_review_tools)

    @patch("selvage.src.mcp.tools.review_tools.FastMCP")
    def test_register_review_tools_registers_all_tools(
        self, mock_fastmcp: Mock
    ) -> None:
        """register_review_tools가 도구를 등록해야 함"""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        register_review_tools(mock_mcp_instance)

        # tool 데코레이터가 1번 호출되어야 함 (review_changes 1개)
        assert mock_mcp_instance.tool.call_count == 1


class TestReviewChanges:
    """review_changes 통합 도구 테스트"""

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_unstaged_mode_default(self, mock_workflow: Mock) -> None:
        """기본 mode(unstaged) 리뷰 성공 테스트"""
        mock_result = ReviewResult(
            success=True,
            estimated_cost=0.05,
            model_used="claude-sonnet-4.5",
            files_reviewed=["test.py"],
        )
        mock_workflow.return_value = mock_result

        result = review_changes(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
        )

        assert result.success is True
        assert result.model_used == "claude-sonnet-4.5"
        assert result.response is None
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            staged=False,
            target_branch=None,
            target_commit=None,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_unstaged_mode_failure(self, mock_workflow: Mock) -> None:
        """unstaged mode 리뷰 실패 테스트"""
        mock_result = ReviewResult(
            success=False,
            model_used="claude-sonnet-4.5",
            error_message="No changes found",
        )
        mock_workflow.return_value = mock_result

        result = review_changes(
            model="claude-sonnet-4.5",
            repo_path="/empty/repo",
        )

        assert result.success is False
        assert result.error_message == "No changes found"

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_staged_mode(self, mock_workflow: Mock) -> None:
        """staged mode 리뷰 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5",
        )

        review_changes(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            diff_scope="staged",
        )

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            staged=True,
            target_branch=None,
            target_commit=None,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_branch_mode(self, mock_workflow: Mock) -> None:
        """branch mode 리뷰 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5",
        )

        review_changes(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            diff_scope="branch",
            target_branch="main",
        )

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            staged=False,
            target_branch="main",
            target_commit=None,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_commit_mode(self, mock_workflow: Mock) -> None:
        """commit mode 리뷰 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4.5",
        )

        review_changes(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            diff_scope="commit",
            target_commit="abc1234",
        )

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            staged=False,
            target_branch=None,
            target_commit="abc1234",
        )

    def test_invalid_mode_returns_error(self) -> None:
        """잘못된 mode가 에러를 반환하는지 테스트"""
        result = review_changes(
            model="claude-sonnet-4.5",
            diff_scope="invalid",
        )

        assert result.success is False
        assert "Invalid diff_scope" in result.error_message
        assert "invalid" in result.error_message

    def test_branch_mode_without_target_branch_returns_error(self) -> None:
        """branch mode에서 target_branch 누락 시 에러 반환 테스트"""
        result = review_changes(
            model="claude-sonnet-4.5",
            diff_scope="branch",
        )

        assert result.success is False
        assert "target_branch" in result.error_message

    def test_commit_mode_without_target_commit_returns_error(self) -> None:
        """commit mode에서 target_commit 누락 시 에러 반환 테스트"""
        result = review_changes(
            model="claude-sonnet-4.5",
            diff_scope="commit",
        )

        assert result.success is False
        assert "target_commit" in result.error_message

    def test_model_is_required(self) -> None:
        """model은 필수 파라미터"""
        with pytest.raises(TypeError):
            review_changes()

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_repo_path_has_default(self, mock_workflow: Mock) -> None:
        """repo_path는 기본값이 있음"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="test-model",
        )
        result = review_changes(model="test-model")
        assert result.success is True


class TestExecuteReviewWorkflow:
    """_execute_review_workflow 내부 함수 테스트"""

    @patch("selvage.src.mcp.tools.review_tools.get_model_info")
    @patch("selvage.src.mcp.tools.review_tools.get_api_key")
    @patch("selvage.src.mcp.tools.review_tools.get_diff_content")
    @patch("selvage.src.mcp.tools.review_tools.parse_git_diff")
    @patch("selvage.cli._perform_new_review")
    @patch("selvage.src.mcp.tools.review_tools.ReviewLogManager")
    def test_execute_review_workflow_success_path(
        self,
        mock_log_manager: Mock,
        mock_perform_review: Mock,
        mock_parse_diff: Mock,
        mock_get_diff: Mock,
        mock_get_api_key: Mock,
        mock_get_model_info: Mock,
    ) -> None:
        """성공적인 리뷰 워크플로우 테스트"""
        from selvage.src.mcp.tools.review_tools import _execute_review_workflow

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": "anthropic",
            "name": "claude-sonnet-4.5",
        }
        mock_get_api_key.return_value = "test-api-key"
        mock_get_diff.return_value = "diff content"
        from selvage.src.diff_parser.models import DiffResult, FileDiff

        mock_parse_diff.return_value = DiffResult(
            files=[FileDiff(filename="test.py", file_content="test content", hunks=[])]
        )
        # 실제 ReviewResponse 객체와 EstimatedCost Mock 생성
        from selvage.src.utils.token.models import ReviewResponse

        mock_review_response = ReviewResponse(
            issues=[],
            summary="Test review summary",
            score=8.0,
            recommendations=["Test recommendation"],
        )
        mock_estimated_cost = Mock()
        mock_estimated_cost.total_cost_usd = 0.05
        mock_estimated_cost.total_cost = 0.05  # 백업용

        mock_perform_review.return_value = (
            mock_review_response,
            mock_estimated_cost,
        )
        mock_log_manager.generate_log_id.return_value = "log-123"
        mock_log_manager.save.return_value = "/path/to/log.json"

        # 실행
        result = _execute_review_workflow(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
            staged=False,
        )

        # 검증
        assert result.success is True
        assert result.model_used == "claude-sonnet-4.5"
        assert result.estimated_cost == 0.05
        assert result.log_id == "log-123"

    @patch("selvage.src.mcp.tools.review_tools.get_model_info")
    def test_execute_review_workflow_unsupported_model(
        self, mock_get_model_info: Mock
    ) -> None:
        """지원되지 않는 모델 에러 테스트"""
        from selvage.src.mcp.tools.review_tools import _execute_review_workflow

        # Mock 설정
        mock_get_model_info.return_value = None

        # 실행
        result = _execute_review_workflow(
            model="invalid-model",
            repo_path="/test/repo",
        )

        # 검증
        assert result.success is False
        assert "Unsupported model" in result.error_message

    @patch("selvage.src.mcp.tools.review_tools.get_model_info")
    @patch("selvage.src.mcp.tools.review_tools.get_api_key")
    def test_execute_review_workflow_missing_api_key(
        self, mock_get_api_key: Mock, mock_get_model_info: Mock
    ) -> None:
        """API 키 누락 에러 테스트"""
        from selvage.src.mcp.tools.review_tools import _execute_review_workflow

        # Mock 설정
        mock_get_model_info.return_value = {"provider": "anthropic"}
        mock_get_api_key.side_effect = APIKeyNotFoundError(ModelProvider.ANTHROPIC)

        # 실행
        result = _execute_review_workflow(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
        )

        # 검증
        assert result.success is False
        assert "API key is not configured" in result.error_message

    @patch("selvage.src.mcp.tools.review_tools.get_model_info")
    @patch("selvage.src.mcp.tools.review_tools.get_api_key")
    @patch("selvage.src.mcp.tools.review_tools.get_diff_content")
    def test_execute_review_workflow_no_changes(
        self, mock_get_diff: Mock, mock_get_api_key: Mock, mock_get_model_info: Mock
    ) -> None:
        """변경사항 없음 테스트"""
        from selvage.src.mcp.tools.review_tools import _execute_review_workflow

        # Mock 설정
        mock_get_model_info.return_value = {"provider": "anthropic"}
        mock_get_api_key.return_value = "test-key"
        mock_get_diff.return_value = ""

        # 실행
        result = _execute_review_workflow(
            model="claude-sonnet-4.5",
            repo_path="/test/repo",
        )

        # 검증
        assert result.success is False
        assert "No changes to review" in result.error_message


class TestReviewToolsIntegration:
    """MCP 리뷰 도구 통합 테스트"""

    def test_review_tools_import_existing_functions(self) -> None:
        """기존 selvage 함수들을 올바르게 import할 수 있는지 테스트"""
        script = """
try:
    from selvage.cli import get_diff_content
    from selvage.src.model_config import get_model_info
    from selvage.src.config import get_api_key
    from selvage.src.diff_parser import parse_git_diff
    print("import_success")
except ImportError as e:
    print(f"import_error: {e}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "import_success"
