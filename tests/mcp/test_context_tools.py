"""에이전트 위임 리뷰 도구 테스트"""

from unittest.mock import MagicMock, patch

from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.mcp.models.responses import ReviewContextResult
from selvage.src.mcp.tools.context_tools import (
    REVIEW_OUTPUT_SCHEMA,
    get_review_context,
    register_context_tools,
)


class TestReviewContextResultModel:
    """ReviewContextResult 모델 테스트"""

    def test_success_result_creation(self) -> None:
        """성공 결과 생성 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt="You are a code reviewer...",
            review_targets=[
                {"role": "user", "content": '{"file_name": "app.py"}'}
            ],
            output_format={"type": "json_schema", "schema": {}},
            metadata={"files_count": 1, "total_additions": 10, "total_deletions": 3},
        )

        assert result.success is True
        assert result.system_prompt is not None
        assert len(result.review_targets) == 1
        assert result.output_format is not None
        assert result.metadata["files_count"] == 1
        assert result.error_message is None

    def test_error_result_creation(self) -> None:
        """에러 결과 생성 테스트"""
        result = ReviewContextResult(
            success=False,
            error_message="No changes to review.",
        )

        assert result.success is False
        assert result.system_prompt is None
        assert result.review_targets == []
        assert result.error_message == "No changes to review."

    def test_json_serialization(self) -> None:
        """JSON 직렬화 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt="prompt",
            review_targets=[{"role": "user", "content": "test"}],
            output_format={"type": "json_schema"},
            metadata={"files_count": 1},
        )

        json_str = result.model_dump_json()
        assert (
            '"success":true' in json_str.lower()
            or '"success": true' in json_str.lower()
        )

    def test_metadata_fields(self) -> None:
        """metadata 필드 구조 테스트"""
        metadata = {
            "files_count": 3,
            "total_additions": 42,
            "total_deletions": 10,
            "file_languages": {"python": 2, "javascript": 1},
        }
        result = ReviewContextResult(
            success=True,
            system_prompt="prompt",
            review_targets=[],
            output_format={},
            metadata=metadata,
        )

        assert result.metadata["files_count"] == 3
        assert result.metadata["total_additions"] == 42
        assert result.metadata["file_languages"]["python"] == 2


def _make_diff_result(
    files: list[FileDiff] | None = None,
) -> DiffResult:
    """테스트용 DiffResult를 생성합니다."""
    if files is None:
        files = [
            FileDiff(
                filename="app.py",
                file_content="print('hello')",
                language="python",
                additions=5,
                deletions=2,
            )
        ]
    return DiffResult(files=files)


class TestGetReviewContext:
    """get_review_context 도구 테스트"""

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_unstaged_mode(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """unstaged 모드 기본 동작 테스트"""
        # Arrange
        mock_get_diff.return_value = "diff --git a/app.py b/app.py\n..."
        mock_parse.return_value = _make_diff_result()

        mock_system_prompt = MagicMock()
        mock_system_prompt.content = "You are a code reviewer..."

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = mock_system_prompt
        mock_prompt.to_messages.return_value = [
            {"role": "system", "content": "You are a code reviewer..."},
            {"role": "user", "content": '{"file_name": "app.py"}'},
        ]

        mock_prompt_gen = MagicMock()
        mock_prompt_gen.create_code_review_prompt.return_value = mock_prompt
        mock_prompt_gen_cls.return_value = mock_prompt_gen

        # Act
        result = get_review_context(repo_path="/test/repo")

        # Assert
        assert result.success is True
        assert result.system_prompt == "You are a code reviewer..."
        assert len(result.review_targets) == 2
        assert result.metadata["files_count"] == 1
        assert result.metadata["total_additions"] == 5
        assert result.metadata["total_deletions"] == 2
        assert result.metadata["file_languages"] == {"python": 1}
        assert result.error_message is None

        mock_get_diff.assert_called_once_with(
            repo_path="/test/repo",
            staged=False,
            target_commit=None,
            target_branch=None,
        )

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_staged_mode(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """staged 모드 테스트"""
        mock_get_diff.return_value = "diff --git ..."
        mock_parse.return_value = _make_diff_result(files=[])

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="prompt")
        mock_prompt.to_messages.return_value = [{"role": "system", "content": "prompt"}]
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = (
            mock_prompt
        )

        result = get_review_context(repo_path="/test/repo", mode="staged")

        mock_get_diff.assert_called_once_with(
            repo_path="/test/repo",
            staged=True,
            target_commit=None,
            target_branch=None,
        )
        assert result.success is True

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_branch_mode(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """branch 모드 테스트"""
        mock_get_diff.return_value = "diff --git ..."
        mock_parse.return_value = _make_diff_result(files=[])

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="prompt")
        mock_prompt.to_messages.return_value = []
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = (
            mock_prompt
        )

        result = get_review_context(
            repo_path="/test/repo", mode="branch", target_branch="main"
        )

        mock_get_diff.assert_called_once_with(
            repo_path="/test/repo",
            staged=False,
            target_commit=None,
            target_branch="main",
        )
        assert result.success is True

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_commit_mode(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """commit 모드 테스트"""
        mock_get_diff.return_value = "diff --git ..."
        mock_parse.return_value = _make_diff_result(files=[])

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="prompt")
        mock_prompt.to_messages.return_value = []
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = (
            mock_prompt
        )

        result = get_review_context(
            repo_path="/test/repo", mode="commit", target_commit="abc1234"
        )

        mock_get_diff.assert_called_once_with(
            repo_path="/test/repo",
            staged=False,
            target_commit="abc1234",
            target_branch=None,
        )
        assert result.success is True

    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_no_changes(self, mock_get_diff: MagicMock) -> None:
        """변경사항 없을 때 에러 반환 테스트"""
        mock_get_diff.return_value = ""

        result = get_review_context(repo_path="/test/repo")

        assert result.success is False
        assert result.error_message is not None
        assert "No changes" in result.error_message

    def test_invalid_mode(self) -> None:
        """잘못된 모드 입력 테스트"""
        result = get_review_context(repo_path="/test/repo", mode="invalid")

        assert result.success is False
        assert result.error_message is not None

    def test_branch_mode_without_target(self) -> None:
        """branch 모드에서 target_branch 누락 테스트"""
        result = get_review_context(repo_path="/test/repo", mode="branch")

        assert result.success is False
        assert "target_branch" in result.error_message

    def test_commit_mode_without_target(self) -> None:
        """commit 모드에서 target_commit 누락 테스트"""
        result = get_review_context(repo_path="/test/repo", mode="commit")

        assert result.success is False
        assert "target_commit" in result.error_message

    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_exception_handling(self, mock_get_diff: MagicMock) -> None:
        """예외 발생 시 에러 반환 테스트"""
        mock_get_diff.side_effect = ValueError("Git repository not found")

        result = get_review_context(repo_path="/invalid/path")

        assert result.success is False
        assert "Git repository not found" in result.error_message

    def test_output_format_contains_schema(self) -> None:
        """output_format에 리뷰 스키마가 포함되는지 테스트"""
        assert "issues" in REVIEW_OUTPUT_SCHEMA["schema"]["properties"]
        assert "summary" in REVIEW_OUTPUT_SCHEMA["schema"]["properties"]
        assert "score" in REVIEW_OUTPUT_SCHEMA["schema"]["properties"]
        assert "recommendations" in REVIEW_OUTPUT_SCHEMA["schema"]["properties"]

    def test_register_context_tools(self) -> None:
        """context 도구 등록 테스트"""
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda fn: fn

        register_context_tools(mock_mcp)

        mock_mcp.tool.assert_called_once()
