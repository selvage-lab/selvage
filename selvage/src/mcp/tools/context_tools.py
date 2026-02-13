"""MCP context tools implementation - 에이전트 위임 리뷰 모드"""

import json
import logging

from fastmcp import FastMCP

from selvage.src.diff_parser import parse_git_diff
from selvage.src.mcp.context_store import DelegatedContextStore
from selvage.src.utils.git_utils import get_diff_content
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import ReviewRequest

from ..models.responses import FileReviewContextResult, ReviewContextResult

logger = logging.getLogger(__name__)

VALID_MODES = ("unstaged", "staged", "branch", "commit")
CONTEXT_SIZE_LIMIT = 50_000  # 문자 수 기준

REVIEW_OUTPUT_SCHEMA: dict = {
    "type": "json_schema",
    "schema": {
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "bug",
                                "security",
                                "performance",
                                "style",
                                "design",
                            ],
                        },
                        "file": {"type": "string"},
                        "description": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "error"],
                        },
                        "target_code": {"type": "string"},
                        "suggested_code": {"type": "string"},
                    },
                    "required": ["type", "file", "description", "severity"],
                },
            },
            "summary": {"type": "string"},
            "score": {"type": "number", "minimum": 0, "maximum": 10},
            "recommendations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["issues", "summary", "score", "recommendations"],
    },
}


def get_review_context(
    repo_path: str = ".",
    mode: str = "unstaged",
    target_branch: str | None = None,
    target_commit: str | None = None,
) -> ReviewContextResult:
    """
    Generate structured code review context for agent-delegated review.
    No API key required. The calling agent performs the review using its own LLM.

    Unlike review_* tools which call an external LLM API and return
    finished results, this tool returns the raw review context (system
    prompt, file diffs with AST-based smart context, and expected output
    schema) so the agent can review the code directly.

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
                    f"Invalid mode: {mode}. Supported modes: {', '.join(VALID_MODES)}"
                ),
            )

        # 2. 모드별 파라미터 검증
        if mode == "branch" and not target_branch:
            return ReviewContextResult(
                success=False,
                error_message='target_branch is required for "branch" mode.',
            )
        if mode == "commit" and not target_commit:
            return ReviewContextResult(
                success=False,
                error_message='target_commit is required for "commit" mode.',
            )

        # 3. Git diff 추출
        staged = mode == "staged"
        diff_text = get_diff_content(
            repo_path=repo_path,
            staged=staged,
            target_commit=target_commit,
            target_branch=target_branch,
        )

        if not diff_text:
            return ReviewContextResult(
                success=False,
                error_message="No changes to review.",
            )

        # 4. Diff 파싱
        diff_result = parse_git_diff(diff_text, repo_path)

        # 5. ReviewRequest 생성 (model은 에이전트 위임이므로 빈 문자열)
        review_request = ReviewRequest(
            diff_content=diff_text,
            processed_diff=diff_result,
            file_paths=[f.filename for f in diff_result.files],
            model="",
            repo_path=repo_path,
        )

        # 6. 프롬프트 생성 (Smart Context 포함)
        prompt = PromptGenerator().create_code_review_prompt(review_request)

        # 7. 메타데이터 구성
        metadata = {
            "files_count": len(diff_result.files),
            "total_additions": sum(f.additions for f in diff_result.files),
            "total_deletions": sum(f.deletions for f in diff_result.files),
            "file_languages": _get_language_stats(diff_result),
        }

        # 8. 결과 생성
        messages = prompt.to_messages()
        result = ReviewContextResult(
            success=True,
            system_prompt=prompt.system_prompt.content,
            review_targets=messages,
            output_format=REVIEW_OUTPUT_SCHEMA,
            metadata=metadata,
        )

        # 9. 크기 체크 - 초과 시 로컬 저장 후 경량 응답 반환
        serialized = result.model_dump_json()
        if len(serialized) <= CONTEXT_SIZE_LIMIT:
            return result

        file_list = _extract_file_list(messages)
        store = DelegatedContextStore()
        store.cleanup_expired()
        context_id = store.save(
            {
                "system_prompt": result.system_prompt,
                "review_targets": result.review_targets,
                "output_format": result.output_format,
                "metadata": result.metadata,
                "file_list": file_list,
            }
        )

        logger.info(
            "Context size %d exceeds limit %d, split into %d files (context_id=%s)",
            len(serialized),
            CONTEXT_SIZE_LIMIT,
            len(file_list),
            context_id,
        )

        return ReviewContextResult(
            success=True,
            system_prompt=result.system_prompt,
            review_targets=[],
            output_format=result.output_format,
            metadata=metadata,
            context_id=context_id,
            file_list=file_list,
        )

    except Exception as e:
        return ReviewContextResult(
            success=False,
            error_message=f"An error occurred: {str(e)}",
        )


def get_file_review_context(
    context_id: str,
    file_path: str,
) -> FileReviewContextResult:
    """
    Retrieve the review context for a specific file from a split context.
    Use this only when get_review_context returned a context_id (meaning the
    full context exceeded the size limit).

    The calling agent should call this tool in parallel for each file in the
    file_list returned by get_review_context.

    Args:
        context_id: Context ID returned by get_review_context
        file_path: File path to retrieve (from file_list)

    Returns:
        FileReviewContextResult:
            - success: bool
            - file_path: str (requested file path)
            - review_target: dict (the file's review context with role + content)
            - error_message: str | None
    """
    store = DelegatedContextStore()
    target = store.load_file_context(context_id, file_path)
    if target is None:
        return FileReviewContextResult(
            success=False,
            file_path=file_path,
            error_message=f"File '{file_path}' not found in context '{context_id}'",
        )
    return FileReviewContextResult(
        success=True,
        file_path=file_path,
        review_target=target,
    )


def _extract_file_list(messages: list[dict]) -> list[str]:
    """to_messages() 결과에서 user role 메시지의 file_name을 추출합니다."""
    file_list: list[str] = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        try:
            data = json.loads(content)
            file_name = data.get("file_name")
            if file_name:
                file_list.append(file_name)
        except (json.JSONDecodeError, TypeError, AttributeError):
            continue
    return file_list


def _get_language_stats(diff_result: object) -> dict[str, int]:
    """파일 언어별 통계를 반환합니다."""
    stats: dict[str, int] = {}
    for f in diff_result.files:
        lang = f.language or "unknown"
        stats[lang] = stats.get(lang, 0) + 1
    return stats


def register_context_tools(mcp: FastMCP) -> None:
    """에이전트 위임 리뷰 도구를 등록합니다."""
    mcp.tool()(get_review_context)
    mcp.tool()(get_file_review_context)
