"""MCP review tools implementation"""

from dataclasses import dataclass

from fastmcp import FastMCP

from selvage.src.config import get_api_key, has_openrouter_api_key
from selvage.src.diff_parser import parse_git_diff
from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.model_config import get_model_info
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_status import ReviewStatus
from selvage.src.utils.git_utils import get_diff_content
from selvage.src.utils.logging.review_log_manager import ReviewLogManager
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse

from ..models.responses import DiffContentResult, ReviewResult, ValidationResult


@dataclass
class ReviewExecutionResult:
    """리뷰 실행 결과를 담는 데이터 클래스"""

    review_response: ReviewResponse
    estimated_cost: EstimatedCost
    log_id: str
    log_path: str


def _validate(
    model: str,
) -> ValidationResult:
    """OpenRouter-first로 provider를 결정하고 API 키를 검증합니다.

    Returns:
        ValidationResult: 검증 결과 (success, error_message)
    """
    model_info = get_model_info(model)
    if not model_info:
        return ValidationResult(
            success=False, error_message=f"Unsupported model: {model}"
        )

    provider_value = model_info["provider"]
    if isinstance(provider_value, str):
        try:
            provider = ModelProvider.from_string(provider_value)
        except ValueError:
            return ValidationResult(
                success=False,
                error_message=f"Unsupported provider: {provider_value}",
            )
    elif isinstance(provider_value, ModelProvider):
        provider = provider_value
    else:
        return ValidationResult(
            success=False,
            error_message=f"Invalid provider type: {type(provider_value)}",
        )

    # OpenRouter-first: OpenRouter 키가 있으면 OpenRouter를 사용
    selected_provider = (
        ModelProvider.OPENROUTER if has_openrouter_api_key() else provider
    )

    try:
        _ = get_api_key(selected_provider)
    except APIKeyNotFoundError:
        error_msg = f"{selected_provider.get_display_name()} API key is not configured."
        return ValidationResult(success=False, error_message=error_msg)

    return ValidationResult(success=True, error_message=None)


def get_diff_content_result(
    repo_path: str,
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
) -> DiffContentResult:
    """Extract and validate Git diff content."""
    diff_text = get_diff_content(
        repo_path=repo_path,
        staged=staged,
        target_commit=target_commit,
        target_branch=target_branch,
    )

    if not diff_text:
        return DiffContentResult(
            success=False,
            error_message="No changes to review.",
            diff_content=None,
        )

    return DiffContentResult(success=True, error_message=None, diff_content=diff_text)


def _create_review_request(
    diff_content: str, repo_path: str, model: str
) -> ReviewRequest:
    """diff 내용으로부터 리뷰 요청을 생성합니다."""
    diff_result = parse_git_diff(diff_content, repo_path)
    return ReviewRequest(
        diff_content=diff_content,
        processed_diff=diff_result,
        file_paths=[file.filename for file in diff_result.files],
        model=model,
        repo_path=repo_path,
    )


def _perform_review_and_save_log(
    review_request: ReviewRequest, model: str
) -> ReviewExecutionResult:
    """리뷰를 수행하고 로그를 저장합니다.

    Returns:
        ReviewExecutionResult: 리뷰 실행 결과 (response, cost, log_id, log_path)
    """
    from selvage.cli import _perform_new_review

    review_response, estimated_cost = _perform_new_review(review_request)
    review_prompt = PromptGenerator().create_code_review_prompt(review_request)

    log_id = ReviewLogManager.generate_log_id(model)
    log_path = ReviewLogManager.save(
        prompt=review_prompt,
        review_request=review_request,
        review_response=review_response,
        status=ReviewStatus.SUCCESS,
        log_id=log_id,
        estimated_cost=estimated_cost,
    )

    return ReviewExecutionResult(
        review_response=review_response,
        estimated_cost=estimated_cost,
        log_id=log_id,
        log_path=log_path,
    )


def _execute_review_workflow(
    model: str,
    repo_path: str,
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
) -> ReviewResult:
    """공통 리뷰 워크플로우 실행"""
    try:
        # 1. 모델 및 API 키 검증
        validation = _validate(model)
        if not validation.success:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=validation.error_message,
            )

        # 2. Git diff 추출 및 검증
        diff_result = get_diff_content_result(
            repo_path, staged, target_commit, target_branch
        )
        if not diff_result.success:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=diff_result.error_message,
            )

        # 3. 리뷰 요청 생성
        review_request = _create_review_request(
            diff_result.diff_content, repo_path, model
        )

        # 4. 리뷰 수행 및 로그 저장
        execution_result = _perform_review_and_save_log(review_request, model)

        # 5. 결과 반환
        return ReviewResult(
            success=True,
            response=execution_result.review_response,
            estimated_cost=execution_result.estimated_cost.total_cost_usd,
            model_used=model,
            files_reviewed=[f.filename for f in review_request.processed_diff.files],
            log_id=execution_result.log_id,
            log_path=execution_result.log_path,
        )

    except Exception as e:
        return ReviewResult(
            success=False,
            model_used=model,
            error_message=f"An error occurred during review: {str(e)}",
        )


def review_current_changes(model: str, repo_path: str = ".") -> ReviewResult:
    """
    Review unstaged changes in the repository with AI.

    Args:
        model: AI model to use (e.g., claude-sonnet-4, gpt-4o)
        repo_path: Git repository path (default: current directory)

    Returns:
        ReviewResult:
            - success: bool
            - response: ReviewResponse | None
            - estimated_cost: float (USD)
            - model_used: str
            - files_reviewed: list[str]
            - log_id: str | None
            - log_path: str | None
            - timestamp: str (ISO 8601)
            - error_message: str | None
    """
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        staged=False,
    )


def review_staged_changes(model: str, repo_path: str = ".") -> ReviewResult:
    """
    Review staged changes with AI.

    Args:
        model: AI model to use (e.g., claude-sonnet-4, gpt-4o)
        repo_path: Git repository path (default: current directory)

    Returns:
        ReviewResult:
            - success: bool
            - response: ReviewResponse | None
            - estimated_cost: float (USD)
            - model_used: str
            - files_reviewed: list[str]
            - log_id: str | None
            - log_path: str | None
            - timestamp: str (ISO 8601)
            - error_message: str | None
    """
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        staged=True,
    )


def review_against_branch(
    model: str, target_branch: str, repo_path: str = "."
) -> ReviewResult:
    """
    Review differences between current branch and specified branch with AI.

    Args:
        model: AI model to use (e.g., claude-sonnet-4, gpt-4o)
        target_branch: Target branch to compare (e.g., main, develop)
        repo_path: Git repository path (default: current directory)

    Returns:
        ReviewResult:
            - success: bool
            - response: ReviewResponse | None
            - estimated_cost: float (USD)
            - model_used: str
            - files_reviewed: list[str]
            - log_id: str | None
            - log_path: str | None
            - timestamp: str (ISO 8601)
            - error_message: str | None
    """
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        target_branch=target_branch,
    )


def review_against_commit(
    model: str, target_commit: str, repo_path: str = "."
) -> ReviewResult:
    """
    Review changes from specified commit to HEAD with AI.

    Args:
        model: AI model to use (e.g., claude-sonnet-4, gpt-4o)
        target_commit: Base commit hash (e.g., abc1234)
        repo_path: Git repository path (default: current directory)

    Returns:
        ReviewResult:
            - success: bool
            - response: ReviewResponse | None
            - estimated_cost: float (USD)
            - model_used: str
            - files_reviewed: list[str]
            - log_id: str | None
            - log_path: str | None
            - timestamp: str (ISO 8601)
            - error_message: str | None
    """
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        target_commit=target_commit,
    )


def register_review_tools(mcp: FastMCP) -> None:
    """리뷰 관련 MCP 도구들을 등록합니다."""
    mcp.tool()(review_current_changes)
    mcp.tool()(review_staged_changes)
    mcp.tool()(review_against_branch)
    mcp.tool()(review_against_commit)
