# 에이전트 위임 리뷰 모드 - 상세 구현 명세

> **NOTE**: 이 문서는 초기 설계 명세로, 실제 구현과 차이가 있을 수 있습니다.
> 최신 동작은 소스 코드(`selvage/src/mcp/tools/context_tools.py`)를 참고하세요.

> Linear: CR-40, CR-45 | Branch: `anomie7777/cr-45-get_review_context-mcp-도구-구현`

---

## 1. 변경 대상 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `selvage/src/mcp/tools/context_tools.py` | **신규** | `get_review_context` 도구 구현 |
| `selvage/src/mcp/models/responses.py` | **수정** | `ReviewContextResult` 응답 모델 추가 |
| `selvage/src/mcp/tools/__init__.py` | **수정** | `register_context_tools` export 추가 |
| `selvage/src/mcp/server.py` | **수정** | `--mode` 옵션 지원 및 조건부 도구 등록 |
| `selvage/cli.py` | **수정** | `selvage mcp --mode` 옵션 전달 |
| `selvage/src/mcp/tools/review_tools.py` | **수정** | 기존 도구 description 업데이트 |
| `tests/mcp/test_context_tools.py` | **신규** | context 도구 단위 테스트 |
| `tests/mcp/test_mcp_server_mode.py` | **신규** | 서버 모드별 도구 등록 테스트 |

---

## 2. 구현 순서 (TDD)

```
[Phase 1] 응답 모델 정의 + 테스트
[Phase 2] get_review_context 도구 구현 + 테스트
[Phase 3] 서버 모드 옵션 + 조건부 도구 등록 + 테스트
[Phase 4] CLI 옵션 전달 + 기존 도구 description 업데이트
[Phase 5] 기존 테스트 통과 확인
```

---

## Phase 1: 응답 모델 정의

### 1.1 테스트 먼저 (RED)

**파일: `tests/mcp/test_context_tools.py`**

```python
"""에이전트 위임 리뷰 도구 테스트"""

from unittest.mock import MagicMock, patch

import pytest

from selvage.src.mcp.models.responses import ReviewContextResult


class TestReviewContextResultModel:
    """ReviewContextResult 모델 테스트"""

    def test_success_result_creation(self) -> None:
        """성공 결과 생성 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt='You are a code reviewer...',
            review_targets=[
                {'role': 'user', 'content': '{"file_name": "app.py"}'}
            ],
            output_format={'type': 'json_schema', 'schema': {}},
            metadata={'files_count': 1, 'total_additions': 10, 'total_deletions': 3},
        )

        assert result.success is True
        assert result.system_prompt is not None
        assert len(result.review_targets) == 1
        assert result.output_format is not None
        assert result.metadata['files_count'] == 1
        assert result.error_message is None

    def test_error_result_creation(self) -> None:
        """에러 결과 생성 테스트"""
        result = ReviewContextResult(
            success=False,
            error_message='No changes to review.',
        )

        assert result.success is False
        assert result.system_prompt is None
        assert result.review_targets == []
        assert result.error_message == 'No changes to review.'

    def test_json_serialization(self) -> None:
        """JSON 직렬화 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt='prompt',
            review_targets=[{'role': 'user', 'content': 'test'}],
            output_format={'type': 'json_schema'},
            metadata={'files_count': 1},
        )

        json_str = result.model_dump_json()
        assert '"success": true' in json_str.lower() or '"success":true' in json_str.lower()

    def test_metadata_fields(self) -> None:
        """metadata 필드 구조 테스트"""
        metadata = {
            'files_count': 3,
            'total_additions': 42,
            'total_deletions': 10,
            'file_languages': {'python': 2, 'javascript': 1},
        }
        result = ReviewContextResult(
            success=True,
            system_prompt='prompt',
            review_targets=[],
            output_format={},
            metadata=metadata,
        )

        assert result.metadata['files_count'] == 3
        assert result.metadata['total_additions'] == 42
        assert result.metadata['file_languages']['python'] == 2
```

### 1.2 구현 (GREEN)

**파일: `selvage/src/mcp/models/responses.py` - 추가할 코드**

기존 `ReviewDetailsResult` 클래스 아래에 추가:

```python
class ReviewContextResult(BaseModel):
    """에이전트 위임 리뷰용 컨텍스트 응답 모델

    get_review_context 도구에서 반환되는 구조화된 리뷰 컨텍스트입니다.
    에이전트가 이 데이터를 기반으로 직접 코드 리뷰를 수행합니다.
    """

    success: bool = Field(description='컨텍스트 생성 성공 여부')
    system_prompt: str | None = Field(
        None, description='코드 리뷰 시스템 프롬프트'
    )
    review_targets: list[dict] = Field(
        default_factory=list,
        description='파일별 리뷰 컨텍스트 (system_prompt에 이어서 처리)',
    )
    output_format: dict | None = Field(
        None, description='기대하는 리뷰 결과 JSON 스키마'
    )
    metadata: dict = Field(
        default_factory=dict,
        description='파일 수, 변경 라인 수 등 메타데이터',
    )
    error_message: str | None = Field(None, description='에러 메시지 (실패 시)')
```

---

## Phase 2: get_review_context 도구 구현

### 2.1 테스트 먼저 (RED)

**파일: `tests/mcp/test_context_tools.py` - 추가**

```python
from selvage.src.mcp.tools.context_tools import (
    get_review_context,
    register_context_tools,
)


class TestGetReviewContext:
    """get_review_context 도구 테스트"""

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    @patch('selvage.src.mcp.tools.context_tools.parse_git_diff')
    @patch('selvage.src.mcp.tools.context_tools.PromptGenerator')
    def test_unstaged_mode(
        self,
        mock_prompt_gen_cls: MagicMock,
        mock_parse: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """unstaged 모드 기본 동작 테스트"""
        # Arrange
        mock_get_diff.return_value = 'diff --git a/app.py b/app.py\n...'

        mock_file = MagicMock()
        mock_file.filename = 'app.py'
        mock_file.additions = 5
        mock_file.deletions = 2
        mock_file.language = 'python'

        mock_diff_result = MagicMock()
        mock_diff_result.files = [mock_file]
        mock_diff_result.is_include_entirely_new_content.return_value = False
        mock_parse.return_value = mock_diff_result

        mock_system_prompt = MagicMock()
        mock_system_prompt.content = 'You are a code reviewer...'

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = mock_system_prompt
        mock_prompt.to_messages.return_value = [
            {'role': 'system', 'content': 'You are a code reviewer...'},
            {'role': 'user', 'content': '{"file_name": "app.py"}'},
        ]

        mock_prompt_gen = MagicMock()
        mock_prompt_gen.create_code_review_prompt.return_value = mock_prompt
        mock_prompt_gen_cls.return_value = mock_prompt_gen

        # Act
        result = get_review_context(repo_path='/test/repo')

        # Assert
        assert result.success is True
        assert result.system_prompt == 'You are a code reviewer...'
        assert len(result.review_targets) == 2
        assert result.metadata['files_count'] == 1
        assert result.error_message is None

        mock_get_diff.assert_called_once_with(
            repo_path='/test/repo',
            staged=False,
            target_commit=None,
            target_branch=None,
        )

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    @patch('selvage.src.mcp.tools.context_tools.parse_git_diff')
    @patch('selvage.src.mcp.tools.context_tools.PromptGenerator')
    def test_staged_mode(
        self,
        mock_prompt_gen_cls: MagicMock,
        mock_parse: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """staged 모드 테스트"""
        mock_get_diff.return_value = 'diff --git ...'
        mock_diff_result = MagicMock()
        mock_diff_result.files = []
        mock_diff_result.is_include_entirely_new_content.return_value = False
        mock_parse.return_value = mock_diff_result

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content='prompt')
        mock_prompt.to_messages.return_value = [{'role': 'system', 'content': 'prompt'}]
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = mock_prompt

        result = get_review_context(repo_path='/test/repo', mode='staged')

        mock_get_diff.assert_called_once_with(
            repo_path='/test/repo',
            staged=True,
            target_commit=None,
            target_branch=None,
        )
        assert result.success is True

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    @patch('selvage.src.mcp.tools.context_tools.parse_git_diff')
    @patch('selvage.src.mcp.tools.context_tools.PromptGenerator')
    def test_branch_mode(
        self,
        mock_prompt_gen_cls: MagicMock,
        mock_parse: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """branch 모드 테스트"""
        mock_get_diff.return_value = 'diff --git ...'
        mock_diff_result = MagicMock()
        mock_diff_result.files = []
        mock_diff_result.is_include_entirely_new_content.return_value = False
        mock_parse.return_value = mock_diff_result

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content='prompt')
        mock_prompt.to_messages.return_value = []
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = mock_prompt

        result = get_review_context(
            repo_path='/test/repo', mode='branch', target_branch='main'
        )

        mock_get_diff.assert_called_once_with(
            repo_path='/test/repo',
            staged=False,
            target_commit=None,
            target_branch='main',
        )
        assert result.success is True

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    @patch('selvage.src.mcp.tools.context_tools.parse_git_diff')
    @patch('selvage.src.mcp.tools.context_tools.PromptGenerator')
    def test_commit_mode(
        self,
        mock_prompt_gen_cls: MagicMock,
        mock_parse: MagicMock,
        mock_get_diff: MagicMock,
    ) -> None:
        """commit 모드 테스트"""
        mock_get_diff.return_value = 'diff --git ...'
        mock_diff_result = MagicMock()
        mock_diff_result.files = []
        mock_diff_result.is_include_entirely_new_content.return_value = False
        mock_parse.return_value = mock_diff_result

        mock_prompt = MagicMock()
        mock_prompt.system_prompt = MagicMock(content='prompt')
        mock_prompt.to_messages.return_value = []
        mock_prompt_gen_cls.return_value.create_code_review_prompt.return_value = mock_prompt

        result = get_review_context(
            repo_path='/test/repo', mode='commit', target_commit='abc1234'
        )

        mock_get_diff.assert_called_once_with(
            repo_path='/test/repo',
            staged=False,
            target_commit='abc1234',
            target_branch=None,
        )
        assert result.success is True

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    def test_no_changes(self, mock_get_diff: MagicMock) -> None:
        """변경사항 없을 때 에러 반환 테스트"""
        mock_get_diff.return_value = ''

        result = get_review_context(repo_path='/test/repo')

        assert result.success is False
        assert result.error_message is not None
        assert 'No changes' in result.error_message

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    def test_invalid_mode(self, mock_get_diff: MagicMock) -> None:
        """잘못된 모드 입력 테스트"""
        result = get_review_context(repo_path='/test/repo', mode='invalid')

        assert result.success is False
        assert result.error_message is not None

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    def test_branch_mode_without_target(self, mock_get_diff: MagicMock) -> None:
        """branch 모드에서 target_branch 누락 테스트"""
        result = get_review_context(repo_path='/test/repo', mode='branch')

        assert result.success is False
        assert 'target_branch' in result.error_message

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    def test_commit_mode_without_target(self, mock_get_diff: MagicMock) -> None:
        """commit 모드에서 target_commit 누락 테스트"""
        result = get_review_context(repo_path='/test/repo', mode='commit')

        assert result.success is False
        assert 'target_commit' in result.error_message

    @patch('selvage.src.mcp.tools.context_tools.get_diff_content')
    def test_exception_handling(self, mock_get_diff: MagicMock) -> None:
        """예외 발생 시 에러 반환 테스트"""
        mock_get_diff.side_effect = ValueError('Git repository not found')

        result = get_review_context(repo_path='/invalid/path')

        assert result.success is False
        assert 'Git repository not found' in result.error_message

    def test_output_format_contains_schema(self) -> None:
        """output_format에 리뷰 스키마가 포함되는지 테스트"""
        from selvage.src.mcp.tools.context_tools import REVIEW_OUTPUT_SCHEMA

        assert 'issues' in REVIEW_OUTPUT_SCHEMA['schema']['properties']
        assert 'summary' in REVIEW_OUTPUT_SCHEMA['schema']['properties']
        assert 'score' in REVIEW_OUTPUT_SCHEMA['schema']['properties']
        assert 'recommendations' in REVIEW_OUTPUT_SCHEMA['schema']['properties']

    def test_register_context_tools(self) -> None:
        """context 도구 등록 테스트"""
        mock_mcp = MagicMock()
        mock_mcp.tool.return_value = lambda fn: fn

        register_context_tools(mock_mcp)

        mock_mcp.tool.assert_called_once()
```

### 2.2 구현 (GREEN)

**파일: `selvage/src/mcp/tools/context_tools.py` (신규)**

```python
"""MCP context tools implementation - 에이전트 위임 리뷰 모드"""

from fastmcp import FastMCP

from selvage.src.diff_parser import parse_git_diff
from selvage.src.utils.git_utils import get_diff_content
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import ReviewRequest

from ..models.responses import ReviewContextResult

VALID_MODES = ('unstaged', 'staged', 'branch', 'commit')

REVIEW_OUTPUT_SCHEMA: dict = {
    'type': 'json_schema',
    'schema': {
        'properties': {
            'issues': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'enum': ['bug', 'security', 'performance', 'style', 'design'],
                        },
                        'file': {'type': 'string'},
                        'description': {'type': 'string'},
                        'suggestion': {'type': 'string'},
                        'severity': {
                            'type': 'string',
                            'enum': ['info', 'warning', 'error'],
                        },
                        'target_code': {'type': 'string'},
                        'suggested_code': {'type': 'string'},
                    },
                    'required': ['type', 'file', 'description', 'severity'],
                },
            },
            'summary': {'type': 'string'},
            'score': {'type': 'number', 'minimum': 0, 'maximum': 10},
            'recommendations': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['issues', 'summary', 'score', 'recommendations'],
    },
}


def get_review_context(
    repo_path: str = '.',
    mode: str = 'unstaged',
    target_branch: str | None = None,
    target_commit: str | None = None,
) -> ReviewContextResult:
    """
    Generate structured code review context for agent-delegated review.
    No API key required. The calling agent performs the review using its own LLM.

    Unlike review_* tools which call an external LLM API and return finished results,
    this tool returns the raw review context (system prompt, file diffs with AST-based
    smart context, and expected output schema) so the agent can review the code directly.

    Args:
        repo_path: Git repository path (default: current directory)
        mode: Diff mode - "unstaged" (default), "staged", "branch", or "commit"
        target_branch: Target branch for "branch" mode (e.g., "main")
        target_commit: Target commit hash for "commit" mode (e.g., "abc1234")

    Returns:
        ReviewContextResult:
            - success: bool
            - system_prompt: str (code review system prompt)
            - review_targets: list[dict] (per-file context with hunks)
            - output_format: dict (expected review result JSON schema)
            - metadata: dict (files_count, total_additions, total_deletions, etc.)
            - error_message: str | None
    """
    try:
        # 1. 모드 검증
        if mode not in VALID_MODES:
            return ReviewContextResult(
                success=False,
                error_message=(
                    f'Invalid mode: {mode}. '
                    f'Supported modes: {", ".join(VALID_MODES)}'
                ),
            )

        # 2. 모드별 파라미터 검증
        if mode == 'branch' and not target_branch:
            return ReviewContextResult(
                success=False,
                error_message='target_branch is required for "branch" mode.',
            )
        if mode == 'commit' and not target_commit:
            return ReviewContextResult(
                success=False,
                error_message='target_commit is required for "commit" mode.',
            )

        # 3. Git diff 추출
        staged = mode == 'staged'
        diff_text = get_diff_content(
            repo_path=repo_path,
            staged=staged,
            target_commit=target_commit,
            target_branch=target_branch,
        )

        if not diff_text:
            return ReviewContextResult(
                success=False,
                error_message='No changes to review.',
            )

        # 4. Diff 파싱
        diff_result = parse_git_diff(diff_text, repo_path)

        # 5. ReviewRequest 생성 (model 필드는 에이전트 위임이므로 빈 문자열)
        review_request = ReviewRequest(
            diff_content=diff_text,
            processed_diff=diff_result,
            file_paths=[f.filename for f in diff_result.files],
            model='',
            repo_path=repo_path,
        )

        # 6. 프롬프트 생성 (Smart Context 포함)
        prompt = PromptGenerator().create_code_review_prompt(review_request)

        # 7. 메타데이터 구성
        metadata = {
            'files_count': len(diff_result.files),
            'total_additions': sum(f.additions for f in diff_result.files),
            'total_deletions': sum(f.deletions for f in diff_result.files),
            'file_languages': _get_language_stats(diff_result),
        }

        # 8. 결과 반환
        return ReviewContextResult(
            success=True,
            system_prompt=prompt.system_prompt.content,
            review_targets=prompt.to_messages(),
            output_format=REVIEW_OUTPUT_SCHEMA,
            metadata=metadata,
        )

    except Exception as e:
        return ReviewContextResult(
            success=False,
            error_message=f'An error occurred: {str(e)}',
        )


def _get_language_stats(diff_result: object) -> dict[str, int]:
    """파일 언어별 통계를 반환합니다."""
    stats: dict[str, int] = {}
    for f in diff_result.files:
        lang = f.language or 'unknown'
        stats[lang] = stats.get(lang, 0) + 1
    return stats


def register_context_tools(mcp: FastMCP) -> None:
    """에이전트 위임 리뷰 도구를 등록합니다."""
    mcp.tool()(get_review_context)
```

---

## Phase 3: 서버 모드 옵션 + 조건부 도구 등록

### 3.1 테스트 먼저 (RED)

**파일: `tests/mcp/test_mcp_server_mode.py` (신규)**

```python
"""MCP 서버 모드별 도구 등록 테스트"""

import os
from unittest.mock import patch

import pytest


class TestServerModeToolRegistration:
    """서버 모드에 따른 도구 등록 테스트"""

    @patch.dict(os.environ, {}, clear=True)
    def test_auto_mode_without_api_keys(self) -> None:
        """auto 모드 + API 키 없음 -> context 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode='auto')
        info = server.get_tools_info()

        assert 'get_review_context' in info['context_tools']
        assert info['review_tools'] == []

    @patch.dict(
        os.environ,
        {'ANTHROPIC_API_KEY': 'test-key'},
        clear=False,
    )
    def test_auto_mode_with_api_key(self) -> None:
        """auto 모드 + API 키 있음 -> 모든 도구 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode='auto')
        info = server.get_tools_info()

        assert len(info['review_tools']) == 4
        assert 'get_review_context' in info['context_tools']

    def test_agent_mode(self) -> None:
        """agent 모드 -> context 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode='agent')
        info = server.get_tools_info()

        assert info['review_tools'] == []
        assert 'get_review_context' in info['context_tools']

    def test_independent_mode(self) -> None:
        """independent 모드 -> review 도구만 등록"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer(mode='independent')
        info = server.get_tools_info()

        assert len(info['review_tools']) == 4
        assert info['context_tools'] == []

    def test_default_mode_is_auto(self) -> None:
        """기본 모드는 auto"""
        from selvage.src.mcp.server import SelvageMCPServer

        server = SelvageMCPServer()
        assert server.mode == 'auto'

    def test_invalid_mode_raises_error(self) -> None:
        """잘못된 모드는 ValueError 발생"""
        from selvage.src.mcp.server import SelvageMCPServer

        with pytest.raises(ValueError, match='Invalid mode'):
            SelvageMCPServer(mode='invalid')


class TestHasAnyApiKey:
    """API 키 존재 여부 확인 함수 테스트"""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_api_keys(self) -> None:
        from selvage.src.mcp.server import _has_any_api_key

        assert _has_any_api_key() is False

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test'}, clear=True)
    def test_anthropic_key_only(self) -> None:
        from selvage.src.mcp.server import _has_any_api_key

        assert _has_any_api_key() is True

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test'}, clear=True)
    def test_openrouter_key_only(self) -> None:
        from selvage.src.mcp.server import _has_any_api_key

        assert _has_any_api_key() is True

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test'}, clear=True)
    def test_openai_key_only(self) -> None:
        from selvage.src.mcp.server import _has_any_api_key

        assert _has_any_api_key() is True

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test'}, clear=True)
    def test_gemini_key_only(self) -> None:
        from selvage.src.mcp.server import _has_any_api_key

        assert _has_any_api_key() is True
```

### 3.2 구현 (GREEN)

**파일: `selvage/src/mcp/server.py` (전체 교체)**

```python
"""Selvage MCP 서버 구현"""

import os
import sys
import warnings

from fastmcp import FastMCP

from selvage.src.config import set_mcp_mode
from selvage.src.mcp.tools.context_tools import register_context_tools
from selvage.src.mcp.tools.review_tools import register_review_tools
from selvage.src.mcp.tools.utility_tools import register_utility_tools

VALID_MODES = ('auto', 'agent', 'independent')

_API_KEY_ENV_VARS = (
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'GEMINI_API_KEY',
    'OPENROUTER_API_KEY',
)


def _setup_mcp_environment() -> None:
    """MCP 환경을 설정합니다.

    stdout에 출력되는 모든 것을 차단하고, 로깅과 경고를 stderr로 리다이렉트합니다.
    """
    # MCP 모드 활성화 (가장 먼저 설정)
    set_mcp_mode(True)

    # 콘솔 인스턴스 재설정 (MCP 모드 반영)
    from selvage.src.utils.base_console import reset_console

    reset_console()

    # warnings를 stderr로 강제 리다이렉트
    warnings.showwarning = lambda msg, cat, _fn, _ln, _file=None, _line=None: print(
        f"{cat.__name__}: {msg}", file=sys.stderr
    )


def _has_any_api_key() -> bool:
    """LLM API 키가 하나라도 설정되어 있는지 확인합니다."""
    return any(os.getenv(var) for var in _API_KEY_ENV_VARS)


class SelvageMCPServer:
    """Selvage MCP 서버 메인 클래스"""

    def __init__(
        self, name: str = 'Selvage Code Review Server', mode: str = 'auto'
    ) -> None:
        if mode not in VALID_MODES:
            raise ValueError(
                f'Invalid mode: {mode}. Supported modes: {", ".join(VALID_MODES)}'
            )

        # MCP 환경 설정 (stdout 보호)
        _setup_mcp_environment()

        self.name = name
        self.mode = mode
        self.mcp = FastMCP(name)
        self._registered_review_tools: list[str] = []
        self._registered_context_tools: list[str] = []
        self._register_tools()

    def _register_tools(self) -> None:
        """모드에 따라 MCP 도구들을 등록합니다."""
        should_register_review = False
        should_register_context = False

        if self.mode == 'auto':
            should_register_context = True
            should_register_review = _has_any_api_key()
        elif self.mode == 'agent':
            should_register_context = True
        elif self.mode == 'independent':
            should_register_review = True

        if should_register_review:
            register_review_tools(self.mcp)
            self._registered_review_tools = [
                'review_current_changes',
                'review_staged_changes',
                'review_against_branch',
                'review_against_commit',
            ]

        if should_register_context:
            register_context_tools(self.mcp)
            self._registered_context_tools = ['get_review_context']

        register_utility_tools(self.mcp)

    async def run(self, transport: str = 'stdio') -> None:
        """MCP 서버를 실행합니다."""
        if transport == 'stdio':
            await self.mcp.run(show_banner=False)
        else:
            raise NotImplementedError(f'Transport {transport} is not yet supported')

    def get_tools_info(self) -> dict:
        """등록된 도구들의 정보를 반환합니다."""
        return {
            'server_name': self.name,
            'transport': 'stdio',
            'mode': self.mode,
            'tools_registered': True,
            'review_tools': self._registered_review_tools,
            'context_tools': self._registered_context_tools,
            'utility_tools': [
                'get_available_models',
                'get_review_history',
                'get_review_details',
                'get_server_status',
                'validate_model_support',
                'validate_api_key_for_provider',
            ],
        }


def main_sync(mode: str = 'auto') -> None:
    """MCP 서버 동기 엔트리 포인트"""
    server = SelvageMCPServer(mode=mode)

    print(f'Starting {server.name} (mode={mode})...', file=sys.stderr)
    print(f'Tools info: {server.get_tools_info()}', file=sys.stderr)

    try:
        server.mcp.run(show_banner=False)
    except KeyboardInterrupt:
        print('Server stopped by user', file=sys.stderr)
    except Exception as e:
        print(f'Server error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mode',
        choices=list(VALID_MODES),
        default='auto',
        help='Tool registration mode (default: auto)',
    )
    args = parser.parse_args()
    main_sync(mode=args.mode)


def run_server(mode: str = 'auto') -> None:
    """서버를 실행합니다 (외부 호출용)"""
    main_sync(mode=mode)
```

---

## Phase 4: CLI 옵션 전달 + 기존 도구 description 업데이트

### 4.1 CLI mcp 명령어 수정

**파일: `selvage/cli.py` - `mcp` 함수 수정**

기존:
```python
@cli.command()
def mcp() -> None:
    """Start MCP (Model Context Protocol) server"""
    import subprocess
    import sys

    try:
        subprocess.run([sys.executable, "-m", "selvage.src.mcp.server"], check=True)
    except subprocess.CalledProcessError as e:
        ...
```

변경:
```python
@cli.command()
@click.option(
    '--mode',
    type=click.Choice(['auto', 'agent', 'independent']),
    default='auto',
    help='Tool registration mode. '
    'auto: detect API keys, '
    'agent: context-only (no API key needed), '
    'independent: review tools only (API key required)',
)
def mcp(mode: str) -> None:
    """Start MCP (Model Context Protocol) server"""
    import subprocess
    import sys

    try:
        cmd = [sys.executable, '-m', 'selvage.src.mcp.server']
        if mode != 'auto':
            cmd.extend(['--mode', mode])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f'MCP server failed with exit code {e.returncode}', file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print('\nMCP server stopped by user.', file=sys.stderr)
    except Exception as e:
        print(f'MCP server error: {str(e)}', file=sys.stderr)
        sys.exit(1)
```

### 4.2 기존 review 도구 description 업데이트

**파일: `selvage/src/mcp/tools/review_tools.py` - docstring 수정**

각 review 함수의 docstring 첫 줄을 수정:

```python
def review_current_changes(model: str, repo_path: str = '.') -> ReviewResult:
    """
    Review unstaged changes using an independent LLM API call.
    Requires an API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.).
    If no API key is available, use get_review_context instead
    to let the agent perform the review directly.

    Args:
        model: AI model to use (e.g., claude-sonnet-4, gpt-4o)
        repo_path: Git repository path (default: current directory)
    ...
    """
```

동일 패턴으로 `review_staged_changes`, `review_against_branch`, `review_against_commit`도 수정.

### 4.3 __init__.py 업데이트

**파일: `selvage/src/mcp/tools/__init__.py`**

```python
"""MCP 도구들"""

from .context_tools import register_context_tools
from .review_tools import register_review_tools
from .utility_tools import register_utility_tools

__all__ = [
    'register_context_tools',
    'register_review_tools',
    'register_utility_tools',
]
```

---

## Phase 5: 기존 테스트 호환성

### 5.1 영향받는 기존 테스트

**`tests/mcp/test_mcp_server_integration.py`**

`SelvageMCPServer()`를 직접 생성하는 부분에서 `get_tools_info()` 반환값 구조가 변경됨.

**변경 필요 사항:**

```python
# 기존 (라인 54-70):
expected_review_tools = [
    "review_current_changes_tool",
    ...
]
assert server_info["review_tools"] == expected_review_tools

# 변경:
# mode=auto + API 키 유무에 따라 review_tools가 달라짐
# context_tools 필드 추가 확인
assert 'context_tools' in server_info
assert 'review_tools' in server_info
```

**`tests/mcp/test_mcp_server_integration.py` - `test_get_server_status_function`**

```python
# 기존 (라인 81):
assert status.tools_count == 10

# 변경:
# 도구 수가 mode에 따라 달라지므로 정확한 숫자 대신 범위 체크
assert status.tools_count >= 7  # utility(6) + context(1) 최소
```

**`selvage/src/mcp/tools/utility_tools.py` - `TOTAL_MCP_TOOLS_COUNT` 상수**

```python
# 기존 (라인 24):
TOTAL_MCP_TOOLS_COUNT = 10

# 변경: 동적 계산 또는 제거 필요
# get_server_status에서 mcp 인스턴스의 실제 도구 수를 반환하도록 수정
```

### 5.2 기존 테스트 깨지지 않는지 확인 명령

```bash
# Phase별 테스트 실행
pytest tests/mcp/test_context_tools.py -v          # Phase 1-2 테스트
pytest tests/mcp/test_mcp_server_mode.py -v         # Phase 3 테스트
pytest tests/mcp/ -v                                 # MCP 전체 테스트
pytest tests/ -v                                     # 전체 테스트
```

---

## 부록 A: 파일별 전체 diff 요약

### `selvage/src/mcp/models/responses.py`

```diff
 class ReviewDetailsResult(BaseModel):
     ...
+
+
+class ReviewContextResult(BaseModel):
+    """에이전트 위임 리뷰용 컨텍스트 응답 모델"""
+
+    success: bool = Field(description='컨텍스트 생성 성공 여부')
+    system_prompt: str | None = Field(None, description='코드 리뷰 시스템 프롬프트')
+    review_targets: list[dict] = Field(
+        default_factory=list,
+        description='파일별 리뷰 컨텍스트',
+    )
+    output_format: dict | None = Field(None, description='기대하는 리뷰 결과 JSON 스키마')
+    metadata: dict = Field(default_factory=dict, description='메타데이터')
+    error_message: str | None = Field(None, description='에러 메시지')
```

### `selvage/src/mcp/server.py`

```diff
-from selvage.src.mcp.tools.review_tools import register_review_tools
+from selvage.src.mcp.tools.context_tools import register_context_tools
+from selvage.src.mcp.tools.review_tools import register_review_tools

+VALID_MODES = ('auto', 'agent', 'independent')
+_API_KEY_ENV_VARS = (...)
+
+def _has_any_api_key() -> bool: ...
+
 class SelvageMCPServer:
-    def __init__(self, name: str = "Selvage Code Review Server") -> None:
+    def __init__(self, name: str = 'Selvage Code Review Server', mode: str = 'auto') -> None:
+        if mode not in VALID_MODES:
+            raise ValueError(...)
+        self.mode = mode
         ...

     def _register_tools(self) -> None:
-        register_review_tools(self.mcp)
-        register_utility_tools(self.mcp)
+        # 모드에 따라 조건부 등록
+        ...
```

### `selvage/src/mcp/tools/__init__.py`

```diff
+from .context_tools import register_context_tools
 from .review_tools import register_review_tools
 from .utility_tools import register_utility_tools

 __all__ = [
+    "register_context_tools",
     "register_review_tools",
     "register_utility_tools",
 ]
```

---

## 부록 B: 에이전트가 보게 되는 도구 목록 (모드별)

### `selvage mcp` (auto, API 키 없음)

```
1. get_review_context     - 코드 리뷰 컨텍스트 반환 (API 키 불필요)
2. get_available_models   - 지원 모델 목록
3. get_review_history     - 리뷰 히스토리
4. get_review_details     - 리뷰 상세
5. get_server_status      - 서버 상태
6. validate_model_support - 모델 지원 여부
7. validate_api_key_for_provider - API 키 검증
```

### `selvage mcp` (auto, API 키 있음)

```
1-4.  review_current_changes, review_staged_changes, review_against_branch, review_against_commit
5.    get_review_context
6-11. (utility tools)
```

### `selvage mcp --mode agent`

```
1. get_review_context
2-7. (utility tools)
```

### `selvage mcp --mode independent`

```
1-4. review_current_changes, review_staged_changes, review_against_branch, review_against_commit
5-10. (utility tools)
```

---

## Phase 6: Claude Code Plugin (서브에이전트 기반)

> Linear: CR-47 | 선택적 구현 트랙 (Phase 1-5 완료 후)

### 6.1 배경 및 동기

`get_review_context`가 반환하는 프롬프트는 수십~수백 KB에 달할 수 있다.
이를 메인 대화 컨텍스트에서 직접 처리하면:

- 200k 컨텍스트 윈도우 중 상당 부분을 리뷰 프롬프트가 차지
- 후속 대화 품질이 저하될 수 있음

Claude Code의 **서브에이전트(Task tool)**를 활용하면:

- 독립 컨텍스트 윈도우에서 리뷰 수행
- 메인 대화에는 압축된 결과만 반환
- MCP 도구(`get_review_context`)와 동일한 기반 공유

### 6.2 플러그인 디렉토리 구조

```
selvage/
  .claude/
    skills/
      review/
        SKILL.md          # 코드 리뷰 스킬 정의
    agents/
      selvage-reviewer.md # 리뷰 전용 에이전트 정의
  .mcp.json               # MCP 서버 연결 설정 (로컬 개발용)
```

> `.claude-plugin/plugin.json` 구조는 Anthropic 공식 플러그인 디렉토리 제출 시 사용.
> 로컬 개발/개인 사용 시에는 `skills/`와 `.mcp.json`만으로 충분.

### 6.3 MCP 연결 설정

**파일: `.mcp.json` (리포지토리 루트)**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

이 파일은 Claude Code가 프로젝트 디렉토리에서 자동으로 감지하여
selvage MCP 서버를 사용할 수 있게 한다.

### 6.4 코드 리뷰 스킬 정의

**파일: `.claude/skills/review/SKILL.md`**

```markdown
---
name: selvage-review
description: selvage의 코드 리뷰 컨텍스트 엔진을 활용한 코드 리뷰
context: fork
tools:
  - mcp__selvage__get_review_context
allowed-tools:
  - Read
  - Glob
  - Grep
---

# Selvage Code Review Skill

## Instructions

You are a code review agent powered by Selvage's context engine.

### Step 1: Get Review Context

Call the `mcp__selvage__get_review_context` tool to get structured review context:

- Default mode: `unstaged` (reviews uncommitted changes)
- Use `mode: "staged"` for pre-commit review
- Use `mode: "branch"` with `target_branch` for PR review
- Use `mode: "commit"` with `target_commit` for specific commit review

### Step 2: Perform Review

Using the returned `system_prompt` and `review_targets`:

1. Follow the system_prompt instructions exactly
2. Review each file in review_targets
3. Produce output matching the `output_format` schema

### Step 3: Return Results

Return a structured review with:
- `issues`: List of found issues with type, severity, file, description
- `summary`: Overall review summary
- `score`: Code quality score (0-10)
- `recommendations`: Action items for the developer
```

**핵심: `context: fork`**

- `context: fork`는 이 스킬을 **독립 서브에이전트**로 실행
- 메인 대화와 별도의 컨텍스트 윈도우를 사용
- 큰 리뷰 프롬프트가 메인 대화를 오염시키지 않음
- 결과만 메인 대화로 반환

### 6.5 리뷰 에이전트 정의

**파일: `.claude/agents/selvage-reviewer.md`**

```markdown
---
name: selvage-reviewer
description: Selvage 기반 코드 리뷰 에이전트
model: sonnet
tools:
  - mcp__selvage__get_review_context
  - Read
  - Glob
---

# Selvage Code Review Agent

You are a specialized code review agent. Your role is to:

1. Call `mcp__selvage__get_review_context` to get the review context
2. Analyze the code changes thoroughly using the provided system prompt
3. If needed, use Read/Glob to examine related files for deeper understanding
4. Return a structured JSON review result

## Review Guidelines

- Focus on bugs, security issues, and design problems
- Be specific: include file names, line references, and code snippets
- Provide actionable suggestions, not just problem descriptions
- Rate severity accurately: error > warning > info
- Keep the summary concise (2-3 sentences)
```

### 6.6 사용 시나리오

#### A. 스킬 기반 사용 (메인 대화에서)

```
User: /selvage-review
Claude Code: (서브에이전트 fork)
  -> get_review_context() 호출
  -> 독립 컨텍스트에서 리뷰 수행
  -> 압축된 결과만 메인 대화로 반환
User: "3개 이슈가 발견되었습니다..."
```

#### B. 에이전트 기반 사용 (Task tool)

```
User: "코드 리뷰해줘"
Claude Code:
  Task(prompt="selvage-reviewer 에이전트로 코드 리뷰 수행",
       subagent_type="general-purpose")
  -> 서브에이전트가 get_review_context() 호출
  -> 독립 컨텍스트에서 리뷰 수행
  -> 요약된 결과 반환
```

#### C. 직접 사용 (기존 방식)

```
User: "현재 변경사항 리뷰해줘"
Claude Code:
  -> get_review_context() 직접 호출
  -> 메인 컨텍스트에서 리뷰 수행
  (변경사항이 작을 때 적합)
```

### 6.7 구현 우선순위

| 순서 | 항목 | 필수 여부 |
|------|------|-----------|
| 1 | `.mcp.json` 생성 | 필수 (Phase 1-5와 동시 가능) |
| 2 | `SKILL.md` 작성 | 권장 |
| 3 | `selvage-reviewer.md` 에이전트 | 선택 |
| 4 | 공식 플러그인 디렉토리 제출 | 선택 (CR-39 연계) |

---

## 부록 C: 로컬 빌드 및 테스트 가이드

### C.1 개발 환경 설정

```bash
# 1. 리포지토리 클론 및 개발 모드 설치
cd /Users/demin_coder/Dev/selvage
pip install -e ".[dev]"

# 2. 설치 확인
selvage --version
selvage mcp --help
```

`pip install -e .`는 editable 모드로 설치하므로, 코드 변경 시 재설치 없이 즉시 반영된다.

### C.2 MCP 서버 단독 테스트

#### fastmcp dev (Inspector UI)

```bash
# MCP Inspector UI로 도구 테스트
fastmcp dev selvage/src/mcp/server.py

# 특정 모드로 테스트
fastmcp dev selvage/src/mcp/server.py -- --mode agent
```

브라우저에서 `http://localhost:5173`에 접속하면 MCP Inspector에서
각 도구를 직접 호출하고 결과를 확인할 수 있다.

#### 직접 실행

```bash
# stdio 모드로 직접 실행
python -m selvage.src.mcp.server --mode agent

# 또는 CLI를 통해
selvage mcp --mode agent
```

### C.3 Claude Code에서 테스트

#### 방법 1: 프로젝트 `.mcp.json` (권장)

selvage 리포지토리 루트에 `.mcp.json`을 생성하면 Claude Code가 자동 감지:

```json
{
  "mcpServers": {
    "selvage": {
      "command": "selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

이후 Claude Code에서 selvage MCP 도구가 자동으로 노출된다.

#### 방법 2: `claude mcp add` 명령

```bash
# 프로젝트 스코프 (현재 프로젝트에서만)
claude mcp add selvage --scope project -- selvage mcp --mode agent

# 글로벌 스코프 (모든 프로젝트에서)
claude mcp add selvage --scope user -- selvage mcp --mode agent
```

#### 방법 3: 글로벌 설정 파일 직접 편집

**파일: `~/.claude.json`**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

#### 연결 확인

```bash
# Claude Code 실행 후 MCP 서버 상태 확인
claude
> /mcp

# selvage 서버가 connected 상태인지 확인
# 도구 목록에 get_review_context가 보이는지 확인
```

### C.4 Antigravity에서 테스트

#### MCP 설정 파일

**파일: `~/.gemini/settings.json`**

```json
{
  "mcpServers": {
    "selvage": {
      "command": "selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

> Antigravity의 MCP 설정 경로는 버전에 따라 다를 수 있음.
> `~/.gemini/settings.json` 또는 프로젝트 루트의 `.gemini/settings.json` 확인.

#### 연결 확인

Antigravity 실행 후 MCP 도구 목록에서 `selvage__get_review_context`가 보이는지 확인.

### C.5 Cursor에서 테스트

Cursor Settings > MCP 탭에서 서버 추가:

```json
{
  "mcpServers": {
    "selvage": {
      "command": "selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

또는 프로젝트 루트에 `.cursor/mcp.json` 파일을 생성.

### C.6 디버깅 팁

#### MCP 서버 로그 확인

```bash
# stderr 출력으로 서버 동작 확인
selvage mcp --mode agent 2>mcp_debug.log

# 다른 터미널에서 로그 모니터링
tail -f mcp_debug.log
```

#### 일반적인 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| `selvage: command not found` | pip install 미완료 | `pip install -e .` 재실행 |
| MCP 서버 연결 안됨 | PATH 문제 | `which selvage` 확인, 절대 경로 사용 |
| 도구가 안 보임 | mode 설정 오류 | `--mode agent` 확인 |
| `get_review_context` 에러 | git repo 아님 | `repo_path`가 git 저장소인지 확인 |
| JSON 파싱 실패 | 프롬프트가 너무 큼 | 변경 파일 수 줄이기, 또는 특정 파일만 staged |

#### 절대 경로 사용 (PATH 문제 시)

```bash
# selvage 실행 경로 확인
which selvage
# 예: /Users/demin_coder/.pyenv/shims/selvage

# .mcp.json에 절대 경로 사용
{
  "mcpServers": {
    "selvage": {
      "command": "/Users/demin_coder/.pyenv/shims/selvage",
      "args": ["mcp", "--mode", "agent"]
    }
  }
}
```

### C.7 E2E 테스트 (자동화)

```bash
# 단위 테스트
pytest tests/mcp/test_context_tools.py -v
pytest tests/mcp/test_mcp_server_mode.py -v

# MCP 전체 테스트
pytest tests/mcp/ -v

# 전체 테스트 (기존 호환성 확인)
pytest tests/ -v
```
