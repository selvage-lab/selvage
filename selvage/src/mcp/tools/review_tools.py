"""MCP 리뷰 도구 구현"""

from dataclasses import dataclass

from fastmcp import FastMCP

from selvage.cli import get_diff_content
from selvage.src.config import get_api_key
from selvage.src.diff_parser import parse_git_diff
from selvage.src.model_config import get_model_info
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_status import ReviewStatus
from selvage.src.utils.logging.review_log_manager import ReviewLogManager
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse

from ..models.responses import ReviewResult

# 공통 ReviewResult 설명 (중복 제거를 위해 상수로 정의)
REVIEW_RESULT_DESCRIPTION = """
ReviewResult: 구조화된 리뷰 결과 객체
    - success: 리뷰 성공 여부
    - response: 전체 ReviewResponse (issues, summary, score, recommendations)
    - estimated_cost: 예상 비용 (USD)
    - model_used: 사용된 AI 모델
    - files_reviewed: 리뷰된 파일 목록
    - log_id: 로그 ID
    - log_path: 로그 파일 경로
    - timestamp: 리뷰 완료 시간
    - error_message: 에러 메시지 (실패 시)
"""


@dataclass
class ReviewExecutionResult:
    """리뷰 실행 결과를 담는 데이터 클래스"""

    review_response: ReviewResponse
    estimated_cost: EstimatedCost
    log_id: str
    log_path: str


def _validate_model_and_api_key(
    model: str,
) -> tuple[bool, str | None, ModelProvider | None]:
    """모델과 API 키를 검증합니다.

    Returns:
        tuple: (성공 여부, 에러 메시지, ModelProvider)
    """
    model_info = get_model_info(model)
    if not model_info:
        return False, f"지원되지 않는 모델입니다: {model}", None

    provider_value = model_info.provider
    if isinstance(provider_value, str):
        try:
            provider = ModelProvider.from_string(provider_value)
        except ValueError:
            return False, f"지원되지 않는 프로바이더입니다: {provider_value}", None
    elif isinstance(provider_value, ModelProvider):
        provider = provider_value
    else:
        return False, f"잘못된 프로바이더 타입입니다: {type(provider_value)}", None

    api_key = get_api_key(provider)
    if not api_key:
        error_msg = f"{provider.get_display_name()} API 키가 설정되지 않았습니다."
        return False, error_msg, None

    return True, None, provider


def _extract_and_validate_diff(
    repo_path: str,
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
) -> tuple[bool, str | None, str | None]:
    """Git diff를 추출하고 검증합니다.

    Returns:
        tuple: (성공 여부, 에러 메시지, diff 내용)
    """
    diff_content = get_diff_content(
        repo_path=repo_path,
        staged=staged,
        target_commit=target_commit,
        target_branch=target_branch,
    )

    if not diff_content:
        return False, "리뷰할 변경사항이 없습니다.", None

    return True, None, diff_content


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
        is_valid, error_msg, provider = _validate_model_and_api_key(model)
        if not is_valid:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=error_msg,
            )

        # 2. Git diff 추출 및 검증
        is_valid, error_msg, diff_content = _extract_and_validate_diff(
            repo_path, staged, target_commit, target_branch
        )
        if not is_valid:
            return ReviewResult(
                success=False,
                model_used=model,
                error_message=error_msg,
            )

        # 3. 리뷰 요청 생성
        review_request = _create_review_request(diff_content, repo_path, model)

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
            error_message=f"리뷰 중 오류가 발생했습니다: {str(e)}",
        )


def _generate_summary(review_content: str) -> str:
    """리뷰 내용에서 요약 생성"""
    # 간단한 요약 생성 로직
    lines = review_content.split("\n")
    summary_lines = []

    for line in lines[:10]:  # 첫 10줄에서 요약 추출
        if line.strip() and not line.startswith("#"):
            summary_lines.append(line.strip())
            if len(summary_lines) >= 3:
                break

    return " ".join(summary_lines)[:200] + "..." if summary_lines else "리뷰 완료"


# 실제 도구 함수들
def review_current_changes(model: str, repo_path: str = ".") -> ReviewResult:
    """현재 작업 디렉토리의 unstaged 변경사항을 AI로 코드 리뷰합니다."""
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        staged=False,
    )


def review_staged_changes(model: str, repo_path: str = ".") -> ReviewResult:
    """스테이징 영역의 변경사항을 AI로 코드 리뷰합니다."""
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        staged=True,
    )


def review_against_branch(
    model: str, target_branch: str, repo_path: str = "."
) -> ReviewResult:
    """현재 브랜치와 지정된 브랜치 간의 차이점을 AI로 코드 리뷰합니다."""
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        target_branch=target_branch,
    )


def review_against_commit(
    model: str, target_commit: str, repo_path: str = "."
) -> ReviewResult:
    """지정된 커밋부터 HEAD까지의 변경사항을 AI로 코드 리뷰합니다."""
    return _execute_review_workflow(
        model=model,
        repo_path=repo_path,
        target_commit=target_commit,
    )


def register_review_tools(mcp: FastMCP) -> None:
    """리뷰 관련 MCP 도구들을 등록합니다."""

    @mcp.tool()
    def review_current_changes_tool(model: str, repo_path: str = ".") -> ReviewResult:
        """
        현재 작업 디렉토리의 unstaged 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델 (예: claude-sonnet-4, gpt-4o)
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)

        Returns:
            ReviewResult: 리뷰 결과 (success, response, estimated_cost, files_reviewed)
        """
        result = review_current_changes(model, repo_path)
        return result

    @mcp.tool()
    def review_staged_changes_tool(model: str, repo_path: str = ".") -> ReviewResult:
        """
        스테이징 영역의 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델 (예: claude-sonnet-4, gpt-4o)
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)

        Returns:
            ReviewResult: 리뷰 결과 (success, response, estimated_cost, files_reviewed)
        """
        result = review_staged_changes(model, repo_path)
        return result

    @mcp.tool()
    def review_against_branch_tool(
        model: str, target_branch: str, repo_path: str = "."
    ) -> ReviewResult:
        """
        현재 브랜치와 지정된 브랜치 간의 차이점을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델 (예: claude-sonnet-4, gpt-4o)
            target_branch: 비교할 브랜치명 (예: main, develop)
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)

        Returns:
            ReviewResult: 리뷰 결과 (success, response, estimated_cost, files_reviewed)
        """
        result = review_against_branch(model, target_branch, repo_path)
        return result

    @mcp.tool()
    def review_against_commit_tool(
        model: str, target_commit: str, repo_path: str = "."
    ) -> ReviewResult:
        """
        지정된 커밋부터 HEAD까지의 변경사항을 AI로 코드 리뷰합니다.

        Args:
            model: 사용할 AI 모델 (예: claude-sonnet-4, gpt-4o)
            target_commit: 기준 커밋 해시 (예: abc1234)
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)

        Returns:
            ReviewResult: 리뷰 결과 (success, response, estimated_cost, files_reviewed)
        """
        result = review_against_commit(model, target_commit, repo_path)
        return result
