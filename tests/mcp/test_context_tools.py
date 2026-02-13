"""에이전트 위임 리뷰 도구 테스트"""

import json

from unittest.mock import MagicMock, patch

from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.diff_parser.models.file_diff import FileDiff
from selvage.src.mcp.models.responses import (
    FileReviewContextResult,
    ReviewContextResult,
)
from selvage.src.mcp.tools.context_tools import (
    CONTEXT_SIZE_LIMIT,
    REVIEW_OUTPUT_SCHEMA,
    get_file_review_context,
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
        """context 도구 등록 테스트 - get_review_context + get_file_review_context"""
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda fn: fn

        register_context_tools(mock_mcp)

        assert mock_mcp.tool.call_count == 2


class TestContextSplitting:
    """컨텍스트 분할 동작 테스트"""

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_small_context_returns_full_data(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """크기 이내 시 context_id가 None이고 review_targets에 데이터 존재"""
        mock_get_diff.return_value = "diff --git a/app.py b/app.py\n..."
        mock_parse.return_value = _make_diff_result()

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="short prompt")
        mock_prompt.to_messages.return_value = [
            {"role": "user", "content": '{"file_name": "app.py"}'},
        ]
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = (
            mock_prompt
        )

        result = get_review_context(repo_path="/test/repo")

        assert result.success is True
        assert result.context_id is None
        assert result.file_list == []
        assert len(result.review_targets) == 1

    @patch("selvage.src.mcp.tools.context_tools.DelegatedContextStore")
    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_large_context_returns_split(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
        mock_store_cls: MagicMock,
    ) -> None:
        """크기 초과 시 context_id 존재, file_list에 파일명 포함, review_targets 비어있음"""
        mock_get_diff.return_value = "diff --git a/app.py b/app.py\n..."
        mock_parse.return_value = _make_diff_result()

        # CONTEXT_SIZE_LIMIT을 초과하는 큰 콘텐츠 생성
        large_content = "x" * (CONTEXT_SIZE_LIMIT + 1000)
        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="system prompt")
        mock_prompt.to_messages.return_value = [
            {"role": "user", "content": json.dumps({"file_name": "app.py", "data": large_content})},
            {"role": "user", "content": json.dumps({"file_name": "utils.py", "data": large_content})},
        ]
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = (
            mock_prompt
        )

        mock_store = MagicMock()
        mock_store.save.return_value = "ctx-1234567890-abcdef12"
        mock_store.cleanup_expired.return_value = 0
        mock_store_cls.return_value = mock_store

        result = get_review_context(repo_path="/test/repo")

        assert result.success is True
        assert result.context_id == "ctx-1234567890-abcdef12"
        assert result.file_list == ["app.py", "utils.py"]
        assert result.review_targets == []
        assert result.system_prompt == "system prompt"
        assert result.output_format is None
        mock_store.save.assert_called_once()
        mock_store.cleanup_expired.assert_called_once()


class TestGetFileReviewContext:
    """get_file_review_context 도구 테스트"""

    @patch("selvage.src.mcp.tools.context_tools.DelegatedContextStore")
    def test_file_context_found(self, mock_store_cls: MagicMock) -> None:
        """정상적으로 파일 컨텍스트 조회"""
        mock_store = MagicMock()
        mock_store.load_file_context.return_value = {
            "role": "user",
            "content": '{"file_name": "app.py", "diff": "..."}',
        }
        mock_store_cls.return_value = mock_store

        result = get_file_review_context(
            context_id="ctx-1234567890-abcdef12",
            file_path="app.py",
        )

        assert result.success is True
        assert result.file_path == "app.py"
        assert result.review_target is not None
        assert result.review_target["role"] == "user"
        assert result.error_message is None

    @patch("selvage.src.mcp.tools.context_tools.DelegatedContextStore")
    def test_file_context_not_found(self, mock_store_cls: MagicMock) -> None:
        """존재하지 않는 파일 조회 시 에러 반환"""
        mock_store = MagicMock()
        mock_store.load_file_context.return_value = None
        mock_store_cls.return_value = mock_store

        result = get_file_review_context(
            context_id="ctx-1234567890-abcdef12",
            file_path="nonexistent.py",
        )

        assert result.success is False
        assert result.file_path == "nonexistent.py"
        assert result.review_target is None
        assert "nonexistent.py" in result.error_message

    @patch("selvage.src.mcp.tools.context_tools.DelegatedContextStore")
    def test_invalid_context_id(self, mock_store_cls: MagicMock) -> None:
        """잘못된 context_id로 조회 시 에러 반환"""
        mock_store = MagicMock()
        mock_store.load_file_context.return_value = None
        mock_store_cls.return_value = mock_store

        result = get_file_review_context(
            context_id="ctx-invalid-12345678",
            file_path="app.py",
        )

        assert result.success is False
        assert "ctx-invalid-12345678" in result.error_message


class TestFileReviewContextResultModel:
    """FileReviewContextResult 모델 테스트"""

    def test_success_result(self) -> None:
        """성공 결과 생성 테스트"""
        result = FileReviewContextResult(
            success=True,
            file_path="app.py",
            review_target={"role": "user", "content": "test"},
        )
        assert result.success is True
        assert result.file_path == "app.py"
        assert result.error_message is None

    def test_error_result(self) -> None:
        """에러 결과 생성 테스트"""
        result = FileReviewContextResult(
            success=False,
            file_path="app.py",
            error_message="File not found",
        )
        assert result.success is False
        assert result.review_target is None
        assert result.error_message == "File not found"

    def test_default_values(self) -> None:
        """기본값 테스트"""
        result = FileReviewContextResult(success=True)
        assert result.file_path is None
        assert result.review_target is None
        assert result.error_message is None


class TestDelegatedPrompt:
    """delegated 모드 프롬프트 관련 테스트"""

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_get_review_context_uses_delegated_prompt(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """get_review_context가 delegated=True로 프롬프트를 생성하는지 확인"""
        mock_get_diff.return_value = "diff --git a/app.py b/app.py\n..."
        mock_parse.return_value = _make_diff_result()

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="delegated prompt")
        mock_prompt.to_messages.return_value = [
            {"role": "user", "content": '{"file_name": "app.py"}'},
        ]

        mock_prompt_gen = MagicMock()
        mock_prompt_gen.create_code_review_prompt.return_value = mock_prompt
        mock_prompt_gen_cls.return_value = mock_prompt_gen

        get_review_context(repo_path="/test/repo")

        mock_prompt_gen.create_code_review_prompt.assert_called_once()
        call_kwargs = mock_prompt_gen.create_code_review_prompt.call_args
        assert call_kwargs[1]["delegated"] is True

    @patch("selvage.src.mcp.tools.context_tools.PromptGenerator")
    @patch("selvage.src.mcp.tools.context_tools.parse_git_diff")
    @patch("selvage.src.mcp.tools.context_tools.get_diff_content")
    def test_output_format_is_none(
        self,
        mock_get_diff: MagicMock,
        mock_parse: MagicMock,
        mock_prompt_gen_cls: MagicMock,
    ) -> None:
        """delegated 모드에서 output_format이 None인지 확인"""
        mock_get_diff.return_value = "diff --git a/app.py b/app.py\n..."
        mock_parse.return_value = _make_diff_result()

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content="delegated prompt")
        mock_prompt.to_messages.return_value = [
            {"role": "user", "content": '{"file_name": "app.py"}'},
        ]

        mock_prompt_gen = MagicMock()
        mock_prompt_gen.create_code_review_prompt.return_value = mock_prompt
        mock_prompt_gen_cls.return_value = mock_prompt_gen

        result = get_review_context(repo_path="/test/repo")

        assert result.success is True
        assert result.output_format is None
