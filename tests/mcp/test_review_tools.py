"""MCP 리뷰 도구 테스트"""

import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

from selvage.src.config import APIKeyNotFoundError, ModelProvider
from selvage.src.mcp.models.responses import ReviewResult
from selvage.src.mcp.tools.review_tools import (
    register_review_tools,
    review_against_branch,
    review_against_commit,
    review_current_changes,
    review_staged_changes,
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
        """register_review_tools가 모든 도구를 등록해야 함"""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        register_review_tools(mock_mcp_instance)

        # tool 데코레이터가 4번 호출되어야 함 (4개 리뷰 도구)
        assert mock_mcp_instance.tool.call_count == 4


class TestReviewCurrentChanges:
    """review_current_changes 도구 테스트"""

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_current_changes_success(self, mock_workflow: Mock) -> None:
        """현재 변경사항 리뷰 성공 테스트"""
        # Mock 설정
        mock_result = ReviewResult(
            success=True,
            estimated_cost=0.05,
            model_used="claude-sonnet-4",
            files_reviewed=["test.py"],
        )
        mock_workflow.return_value = mock_result

        # 실행
        result = review_current_changes(
            model="claude-sonnet-4",
            repo_path="/test/repo",
        )

        # 검증
        assert result.success is True
        assert result.model_used == "claude-sonnet-4"
        assert result.response is None  # response는 선택적 필드
        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4",
            repo_path="/test/repo",
            staged=False,
        )

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_current_changes_failure(self, mock_workflow: Mock) -> None:
        """현재 변경사항 리뷰 실패 테스트"""
        # Mock 설정
        mock_result = ReviewResult(
            success=False,
            model_used="claude-sonnet-4",
            error_message="No changes found",
        )
        mock_workflow.return_value = mock_result

        # 실행
        result = review_current_changes(
            model="claude-sonnet-4",
            repo_path="/empty/repo",
        )

        # 검증
        assert result.success is False
        assert result.error_message == "No changes found"

    def test_review_current_changes_parameter_validation(self) -> None:
        """파라미터 검증 테스트"""
        # model은 필수 파라미터
        with pytest.raises(TypeError):
            review_current_changes()  # model 누락

        # repo_path는 기본값이 있음
        with patch(
            "selvage.src.mcp.tools.review_tools._execute_review_workflow"
        ) as mock_workflow:
            mock_workflow.return_value = ReviewResult(
                success=True,
                model_used="test-model",
            )
            result = review_current_changes(model="test-model")
            assert result.success is True


class TestReviewStagedChanges:
    """review_staged_changes 도구 테스트"""

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_staged_changes_calls_workflow_with_staged_true(
        self, mock_workflow: Mock
    ) -> None:
        """스테이징된 변경사항 리뷰가 staged=True로 호출되는지 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )

        review_staged_changes(model="claude-sonnet-4", repo_path="/test/repo")

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4",
            repo_path="/test/repo",
            staged=True,
        )


class TestReviewAgainstBranch:
    """review_against_branch 도구 테스트"""

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_against_branch_calls_workflow_with_target_branch(
        self, mock_workflow: Mock
    ) -> None:
        """브랜치 대비 리뷰가 target_branch 파라미터로 호출되는지 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )

        review_against_branch(
            model="claude-sonnet-4",
            target_branch="main",
            repo_path="/test/repo",
        )

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4",
            repo_path="/test/repo",
            target_branch="main",
        )

    def test_review_against_branch_requires_target_branch(self) -> None:
        """target_branch 파라미터가 필수인지 테스트"""
        with pytest.raises(TypeError):
            review_against_branch(model="claude-sonnet-4")  # target_branch 누락


class TestReviewAgainstCommit:
    """review_against_commit 도구 테스트"""

    @patch("selvage.src.mcp.tools.review_tools._execute_review_workflow")
    def test_review_against_commit_calls_workflow_with_target_commit(
        self, mock_workflow: Mock
    ) -> None:
        """커밋 대비 리뷰가 target_commit 파라미터로 호출되는지 테스트"""
        mock_workflow.return_value = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )

        review_against_commit(
            model="claude-sonnet-4",
            target_commit="abc1234",
            repo_path="/test/repo",
        )

        mock_workflow.assert_called_once_with(
            model="claude-sonnet-4",
            repo_path="/test/repo",
            target_commit="abc1234",
        )

    def test_review_against_commit_requires_target_commit(self) -> None:
        """target_commit 파라미터가 필수인지 테스트"""
        with pytest.raises(TypeError):
            review_against_commit(model="claude-sonnet-4")  # target_commit 누락


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
            "name": "claude-sonnet-4",
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
            model="claude-sonnet-4",
            repo_path="/test/repo",
            staged=False,
        )

        # 검증
        assert result.success is True
        assert result.model_used == "claude-sonnet-4"
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
            model="claude-sonnet-4",
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
            model="claude-sonnet-4",
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
