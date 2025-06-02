"""
CLI 인터페이스를 제공하는 모듈입니다.
"""

import getpass
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import click

from selvage.__version__ import __version__
from selvage.src.config import (
    get_api_key,
    get_default_debug_mode,
    get_default_diff_only,
    get_default_model,
    get_default_review_log_dir,
    set_api_key,
    set_default_debug_mode,
    set_default_diff_only,
    set_default_model,
)
from selvage.src.diff_parser import parse_git_diff
from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.model_config import ModelProvider, get_model_info
from selvage.src.models import ModelChoice, ReviewStatus
from selvage.src.ui import run_app
from selvage.src.utils.base_console import console
from selvage.src.utils.file_utils import find_project_root
from selvage.src.utils.git_utils import GitDiffMode, GitDiffUtility
from selvage.src.utils.logging import LOG_LEVEL_INFO, setup_logging
from selvage.src.utils.prompts.models.review_prompt import ReviewPrompt
from selvage.src.utils.prompts.models.review_prompt_with_file_content import (
    ReviewPromptWithFileContent,
)
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.review_display import review_display
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewRequest,
    ReviewResponse,
)
from selvage.src.cache import CacheManager
from selvage.src.cache.models import CacheKeyInfo
from selvage.src.cache.cache_key_generator import CacheKeyGenerator
from selvage.src.utils.logging.utils import generate_log_id


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    help="버전 정보를 출력합니다.",
)
@click.option(
    "--set-openai-key",
    is_flag=True,
    help="OpenAI API 키 설정.",
)
@click.option(
    "--set-claude-key",
    is_flag=True,
    help="Anthropic API 키 설정.",
)
@click.option(
    "--set-gemini-key",
    is_flag=True,
    help="Gemini API 키 설정.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    version: bool,
    set_openai_key: bool,
    set_claude_key: bool,
    set_gemini_key: bool,
) -> None:
    """LLM 기반 코드 리뷰 도구"""
    # Context 객체 초기화
    if ctx.obj is None:
        ctx.obj = {}

    # 버전 정보 출력
    if version:
        click.echo(f"selvage {__version__}")
        return

    # API 키 설정 플래그 처리
    if set_openai_key:
        _process_single_api_key(
            ModelProvider.OPENAI.get_display_name(), ModelProvider.OPENAI
        )
        return
    elif set_claude_key:
        _process_single_api_key(
            ModelProvider.ANTHROPIC.get_display_name(), ModelProvider.ANTHROPIC
        )
        return
    elif set_gemini_key:
        _process_single_api_key(
            ModelProvider.GOOGLE.get_display_name(), ModelProvider.GOOGLE
        )
        return

    # 명령어가 지정되지 않은 경우 기본으로 review 명령어 호출
    if ctx.invoked_subcommand is None:
        ctx.invoke(review)


def get_diff_content(
    repo_path: str = ".",
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
) -> str:
    """Git diff 내용을 가져옵니다."""
    try:
        # 모드 결정
        mode = GitDiffMode.UNSTAGED
        target = None

        if staged:
            mode = GitDiffMode.STAGED
        elif target_commit:
            mode = GitDiffMode.TARGET_COMMIT
            target = target_commit
        elif target_branch:
            mode = GitDiffMode.TARGET_BRANCH
            target = target_branch

        git_diff = GitDiffUtility(repo_path=repo_path, mode=mode, target=target)
        return git_diff.get_diff()
    except ValueError as e:
        console.error(f"Git diff 오류: {str(e)}", exception=e)
        return ""


def config_model(model_name: str | None = None) -> None:
    """모델 설정을 처리합니다."""
    # 새 모델 설정이 주어진 경우
    if model_name:
        if set_default_model(model_name):
            console.success(f"기본 모델이 {model_name}로 설정되었습니다.")
        else:
            console.error("기본 모델 설정에 실패했습니다.")
    else:
        # 모델이 지정되지 않은 경우 현재 설정을 표시
        current_model = get_default_model()
        if current_model:
            console.info(f"현재 기본 모델: {current_model}")
        else:
            console.info("기본 모델이 설정되지 않았습니다.")
        console.info(
            "기본 모델을 설정하려면 'selvage config model <model_name>' "
            "명령어를 사용하세요."
        )


def config_diff_only(value: str | None = None) -> None:
    """diff-only 설정을 처리합니다."""
    if value is not None:
        diff_only = value.lower() == "true"
        if set_default_diff_only(diff_only):
            console.success(f"기본 diff-only 값이 {diff_only}로 설정되었습니다.")
        else:
            console.error("기본 diff-only 값 설정에 실패했습니다.")
    else:
        # 값이 지정되지 않은 경우 현재 설정을 표시
        current_value = get_default_diff_only()
        console.info(f"현재 기본 diff-only 값: {current_value}")
        console.info(
            "새로운 값을 설정하려면 'selvage config diff-only true' 또는 "
            "'selvage config diff-only false' 명령어를 사용하세요."
        )


def config_debug_mode(value: str | None = None) -> None:
    """debug_mode 설정을 처리합니다."""
    if value is not None:
        debug_mode = value.lower() == "on"
        if set_default_debug_mode(debug_mode):
            console.success(
                f"디버그 모드가 {'활성화' if debug_mode else '비활성화'}되었습니다."
            )
        else:
            console.error("디버그 모드 설정에 실패했습니다.")
    else:
        # 값이 지정되지 않은 경우 현재 설정을 표시
        current_value = get_default_debug_mode()
        status = "활성화" if current_value else "비활성화"
        console.info(f"현재 디버그 모드: {status}")
        console.info(
            "디버그 모드를 변경하려면 'selvage config debug-mode on' 또는 "
            "'selvage config debug-mode off' 명령어를 사용하세요."
        )


def config_list() -> None:
    """모든 설정을 표시합니다."""
    console.print("==== selvage 설정 ====", style="bold cyan")
    console.print("")

    for provider in ModelProvider:
        provider_display = provider.get_display_name()
        env_var_name = provider.get_env_var_name()
        env_value = os.getenv(env_var_name)

        try:
            # API 키 가져오기 시도
            get_api_key(provider)
            if env_value:
                console.print(
                    f"{provider_display} API 키: 환경변수 {env_var_name}에서 설정됨",
                    style="green",
                )
            else:
                console.print(
                    f"{provider_display} API 키: 설정 파일에서 설정됨", style="green"
                )
        except APIKeyNotFoundError:
            console.print(f"{provider_display} API 키: 설정되지 않음", style="red")
            console.print(
                f"  설정 방법: [green]export {env_var_name}=your_api_key[/green]"
            )
            console.print(f"  또는: [green]selvage --set-{provider.value}-key[/green]")

    console.print("")
    # 리뷰 로그 저장 디렉토리
    console.info(f"리뷰 로그 저장 디렉토리: {get_default_review_log_dir()}")

    # 기본 모델
    default_model = get_default_model()
    if default_model:
        console.info(f"기본 모델: {default_model}")
    else:
        console.info("기본 모델이 설정되지 않았습니다.")

    # 기본 diff-only 설정
    console.info(f"기본 diff-only 값: {get_default_diff_only()}")

    # 기본 debug-mode 설정
    debug_status = "활성화" if get_default_debug_mode() else "비활성화"
    console.info(f"디버그 모드: {debug_status}")


def save_review_log(
    prompt: ReviewPrompt | ReviewPromptWithFileContent | None,
    review_request: ReviewRequest,
    review_response: ReviewResponse | None,
    status: ReviewStatus,
    error: Exception | None = None,
    log_id: str | None = None,  # New parameter
) -> str:
    """리뷰 로그를 저장하고 파일 경로를 반환합니다."""
    model_info = get_model_info(review_request.model)
    now = datetime.now() # Moved now to be accessible for log_id generation
    provider = model_info.get("provider", "unknown") # Moved provider up
    model_name = model_info.get("full_name", review_request.model) # Moved model_name up
    log_dir = get_default_review_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # 프롬프트 직렬화
    prompt_data = None
    if prompt:
        prompt_data = prompt.to_messages()

    # 응답 직렬화
    response_data = None
    if review_response:
        response_data = review_response.model_dump(mode="json")

    # Use provided log_id or generate a new one
    current_log_id = log_id if log_id else f"{provider.value}-{model_name}-{int(now.timestamp())}"

    # JSON 로그 데이터 구성
    review_log = {
        "id": current_log_id,
        "model": {"provider": provider.value, "name": model_name},
        "created_at": now.isoformat(),
        "prompt": prompt_data,
        "review_request": review_request.model_dump(mode="json"),
        "review_response": response_data,
        "status": status.value,
        "error": str(error) if error else None,
        "prompt_version": "v2",
    }

    # 파일 저장
    formatted = now.strftime("%Y%m%d_%H%M%S")
    file_name = f"{formatted}_{model_name}_review_log"
    file_path = log_dir / f"{file_name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(review_log, f, ensure_ascii=False, indent=2)

    return str(file_path)


def _perform_new_review(
    review_request: ReviewRequest,
    review_prompt: ReviewPrompt | ReviewPromptWithFileContent,
) -> tuple[ReviewResponse, EstimatedCost | None]:
    """Performs a new code review using the LLM gateway.
    The progress display (review_display.progress_review) should wrap the call to this function.
    """
    llm_gateway = GatewayFactory.create(model=review_request.model)
    review_result = llm_gateway.review_code(review_prompt)  # review_prompt is an argument
    return review_result.review_response, review_result.estimated_cost


def review_code(
    model: str,
    repo_path: str = ".",
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
    diff_only: bool = False,
    open_ui: bool = False,
    port: int = 8501,
    skip_cache: bool = False,  # Add new
    clear_cache: bool = False,  # Add new
) -> None:
    """코드 리뷰를 수행합니다."""
    # API 키 확인 (model_info is defined here)
    model_info = get_model_info(model)
    provider = model_info.get("provider", "unknown")
    api_key = get_api_key(provider)
    if not api_key:
        console.error(f"{provider.get_display_name()} API 키가 설정되지 않았습니다.")
        console.info("다음 명령어로 API 키를 설정하세요:")
        console.print(
            f"  1. 환경변수(권장): "
            f"[green]export {provider.get_env_var_name()}=YOUR_API_KEY[/green]"
        )
        console.print(
            f"  2. CLI 명령어: [green]selvage --set-{provider.value}-key[/green]"
        )
        return

    provider = model_info.get("provider", "unknown")
    api_key = get_api_key(provider)
    if not api_key:
        console.error(f"{provider.get_display_name()} API 키가 설정되지 않았습니다.")
        # ... (rest of API key error handling)
        console.print(
            f"  1. 환경변수(권장): "
            f"[green]export {provider.get_env_var_name()}=YOUR_API_KEY[/green]"
        )
        console.print(
            f"  2. CLI 명령어: [green]selvage --set-{provider.value}-key[/green]"
        )
        return

    # Initialize CacheManager
    cache_manager = CacheManager()  # Default TTL

    # Handle --clear-cache option
    if clear_cache:
        console.info("CLI 옵션에 따라 캐시를 삭제합니다...")
        cache_manager.clear_cache()

    # Cleanup expired cache
    cache_manager.cleanup_expired_cache()

    # Git diff 내용 가져오기
    diff_content = get_diff_content(repo_path, staged, target_commit, target_branch)
    if not diff_content:
        console.warning("변경 사항이 없거나 diff를 가져올 수 없습니다.")
        return

    # diff 파싱 및 메타데이터 추가
    use_full_context = not diff_only
    # repo_path 결정 - 사용자 입력 또는 프로젝트 루트
    actual_repo_path = str(Path(repo_path)) if repo_path != "." else str(find_project_root())
    diff_result = parse_git_diff(diff_content, use_full_context, actual_repo_path)

    # 리뷰 요청 생성
    review_request = ReviewRequest(
        diff_content=diff_content,
        processed_diff=diff_result,
        file_paths=[file.filename for file in diff_result.files],
        use_full_context=use_full_context,
        model=model,
        repo_path=actual_repo_path,
    )

    review_response: ReviewResponse | None = None
    estimated_cost: EstimatedCost | None = None
    current_log_id: str | None = None # Renamed log_id to current_log_id to avoid confusion
    log_path: str | None = None
    review_prompt_obj: ReviewPrompt | ReviewPromptWithFileContent | None = None

    try:
        if not skip_cache:
            console.info("캐시된 리뷰 결과를 확인합니다...")
            cached_result = cache_manager.get_cached_review(review_request)
            if cached_result:
                review_response, _ = cached_result # Original cached_cost is not directly used for display
                estimated_cost = EstimatedCost.get_zero_cost(review_request.model)

                original_log_id_from_cache = None
                try:
                    # Attempt to retrieve the original log_id from the cache entry
                    temp_cache_key_info = CacheKeyInfo(
                        diff_content=review_request.diff_content,
                        model=review_request.model,
                        use_full_context=review_request.use_full_context
                    )
                    temp_cache_key = CacheKeyGenerator.generate_cache_key(temp_cache_key_info)
                    cache_file_path_temp = cache_manager._get_cache_file_path(temp_cache_key)
                    if cache_file_path_temp.exists():
                        with open(cache_file_path_temp, 'r', encoding='utf-8') as f_temp:
                            cache_data_temp = json.load(f_temp)
                            original_log_id_from_cache = cache_data_temp.get("log_id")
                except Exception as e_cache_read:
                    console.warning(f"캐시된 로그 ID를 읽는 중 오류 발생: {e_cache_read}")

                current_log_id = generate_log_id(review_request.model) # New log for this cache hit event
                log_path = save_review_log(
                    prompt=None,
                    review_request=review_request,
                    review_response=review_response,
                    status=ReviewStatus.SUCCESS,
                    log_id=current_log_id, # Use new log_id for this specific log record
                    # Consider adding cached_from_log_id=original_log_id_from_cache to save_review_log if schema supports
                )
                console.success(
                    f"캐시된 리뷰 결과를 사용했습니다! (원본 로그 ID: {original_log_id_from_cache or 'N/A'}) (API 비용 절약)"
                )

        if review_response is None:  # Cache miss or skip_cache is True
            if skip_cache:
                console.info("CLI 옵션에 따라 캐시를 건너뛰고 새로운 리뷰를 수행합니다...")
            else:
                console.info("캐시된 결과가 없습니다. 새로운 리뷰를 수행합니다...")

            current_log_id = generate_log_id(review_request.model)
            review_prompt_obj = PromptGenerator().create_code_review_prompt(review_request)

            with review_display.progress_review(review_request.model):
                review_response, estimated_cost = _perform_new_review(review_request, review_prompt_obj)

            if not skip_cache and review_response: # Ensure review_response is not None before caching
                cache_manager.save_review_to_cache(
                    review_request=review_request,
                    review_response=review_response,
                    estimated_cost=estimated_cost, # Save the actual cost to cache
                    log_id=current_log_id # Save the log_id of this new review
                )

            log_path = save_review_log(
                prompt=review_prompt_obj,
                review_request=review_request,
                review_response=review_response,
                status=ReviewStatus.SUCCESS,
                log_id=current_log_id
            )

        review_display.review_complete(
            model_info=model_info,
            log_path=log_path,
            estimated_cost=estimated_cost, # This will be 0 for cache hits, or actual for new
        )
        console.success("코드 리뷰가 완료되었습니다!")

        if open_ui:
            console.info("리뷰 결과 UI를 시작합니다...")
            handle_view_command(port)

    except Exception as e:
        console.error(f"코드 리뷰 중 오류가 발생했습니다: {str(e)}", exception=e)
        error_log_id = current_log_id if current_log_id else generate_log_id(model)

        # review_request should be defined, review_prompt_obj might be None
        log_path = save_review_log(
            prompt=review_prompt_obj,
            review_request=review_request, # review_request should exist
            review_response=None,
            status=ReviewStatus.FAILED,
            error=e,
            log_id=error_log_id,
        )
        return


def handle_view_command(port: int) -> None:
    """UI 보기 명령을 처리합니다."""
    try:
        console.info(
            f"Streamlit UI를 시작합니다. 브라우저에서 "
            f"[blue]http://localhost:{port}[/blue]으로 접속하세요..."
        )
        # 포트 설정
        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        # UI 실행
        run_app()
    except ImportError as e:
        console.error("Streamlit 라이브러리가 설치되어 있지 않습니다.", exception=e)
        console.info("다음 명령어로 설치하세요: [green]pip install streamlit[/green]")
        return


def _process_single_api_key(display_name: str, provider: ModelProvider) -> bool:
    """단일 API 키 설정을 처리하는 공통 함수.

    Args:
        display_name: 사용자에게 표시할 프로바이더 이름 (예: "OpenAI")
        provider: 내부 프로바이더 식별자 (예: "openai")

    Returns:
        bool: 항상 True (API 키 설정이 시도되었음을 의미)
    """
    try:
        api_key = getpass.getpass(f"{display_name} API 키를 입력하세요: ")
        api_key = api_key.strip()
        if not api_key:
            console.error("API 키가 입력되지 않았습니다.")
            return True
    except KeyboardInterrupt:
        console.info("\n입력이 취소되었습니다.")
        return True

    if set_api_key(api_key, provider):
        console.success(f"{display_name} API 키가 성공적으로 설정되었습니다.")
    else:
        console.error(f"{display_name} API 키 설정에 실패했습니다.")
    return True


@cli.command()
@click.option(
    "--repo-path", default=".", help="Git 저장소 경로 (기본값: 현재 디렉토리)", type=str
)
@click.option("--staged", is_flag=True, help="Staged 변경사항만 리뷰", type=bool)
@click.option(
    "--target-commit",
    help="특정 커밋부터 HEAD까지의 변경사항을 리뷰 (예: abc1234)",
    type=str,
)
@click.option(
    "--target-branch",
    help="현재 브랜치와 지정된 브랜치 간의 변경사항을 리뷰 (예: main)",
    type=str,
)
@click.option(
    "--model",
    type=ModelChoice(),
    default=get_default_model(),
    help=ModelChoice.build_help_text(),
)
@click.option("--open-ui", is_flag=True, help="리뷰 완료 후 UI로 결과 보기", type=bool)
@click.option(
    "--diff-only",
    is_flag=True,
    default=get_default_diff_only(),
    help="변경된 부분만 분석",
    type=bool,
)
@click.option(
    "--skip-cache",
    is_flag=True,
    help="캐시를 사용하지 않고 새로운 리뷰 수행",
    default=False, # Explicitly set default
    show_default=True, # Show default in help
    type=bool,
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="캐시를 삭제한 후 리뷰 수행",
    default=False, # Explicitly set default
    show_default=True, # Show default in help
    type=bool
)
def review(
    repo_path: str,
    staged: bool,
    target_commit: str | None,
    target_branch: str | None,
    model: str | None,
    open_ui: bool,
    diff_only: bool,
    skip_cache: bool, # New parameter
    clear_cache: bool, # New parameter
) -> None:
    """코드 리뷰 수행"""
    # 상호 배타적 옵션 검증
    exclusive_options = sum([staged, bool(target_commit), bool(target_branch)])
    if exclusive_options > 1:
        click.echo(
            "오류: --staged, --target-commit, --target-branch 옵션은 "
            "동시에 사용할 수 없습니다.",
            err=True,
        )
        return

    if not model:
        console.warning("리뷰 모델을 지정하지 않았습니다.")
        message = (
            "리뷰 모델을 지정해주세요. 사용 가능한 모델은 'selvage models' 명령어로 확인할 수 있습니다.\n\n"
            "사용 예시:\n"
            "  selvage review --model <모델명>\n"
            "또는 기본 모델 설정:\n"
            "  selvage config model <모델명>"
        )
        console.print(message)
        return

    review_code(
        model=model,
        repo_path=repo_path,
        staged=staged,
        target_commit=target_commit,
        target_branch=target_branch,
        diff_only=diff_only,
        open_ui=open_ui,
        skip_cache=skip_cache, # Pass new parameter
        clear_cache=clear_cache, # Pass new parameter
    )


@cli.group()
def config() -> None:
    """설정 관리"""
    pass


@config.command()
@click.argument("model_name", type=ModelChoice(), required=False)
def model(model_name: str | None) -> None:
    """모델 설정 (selvage models 명령어로 사용 가능한 모델 목록 확인 가능)"""
    config_model(model_name)


@config.command()
@click.argument("value", type=click.Choice(["true", "false"]), required=False)
def diff_only(value: str | None) -> None:
    """diff-only 옵션 설정 (true / false)"""
    config_diff_only(value)


@config.command()
@click.argument(
    "value", type=click.Choice(["on", "off"]), required=False, default="off"
)
def debug_mode(value: str | None) -> None:
    """디버그 모드 설정 (on / off)"""
    config_debug_mode(value)


@config.command(name="list")
def show_config():
    """모든 설정 표시"""
    config_list()


@cli.command()
@click.option(
    "--port", default=8501, type=int, help="Streamlit 서버 포트 (기본값: 8501)"
)
def view(port: int) -> None:
    """리뷰 결과를 UI로 보기"""
    handle_view_command(port)


@cli.command()
def models() -> None:
    """사용 가능한 AI 모델 목록 보기"""
    review_display.show_available_models()


def main() -> None:
    """애플리케이션의 메인 진입점."""
    # 로깅 설정 초기화 (파일 로깅만 활성화, 콘솔 로깅은 비활성화)
    setup_logging(level=LOG_LEVEL_INFO)

    try:
        cli()
    except KeyboardInterrupt:
        console.info("\n프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        console.error(f"오류 발생: {str(e)}", exception=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
