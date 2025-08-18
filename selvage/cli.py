"""
CLI 인터페이스를 제공하는 모듈입니다.
"""

import os
import sys
from pathlib import Path

import click

from selvage.__version__ import __version__
from selvage.src.cache import CacheManager
from selvage.src.config import (
    get_api_key,
    get_default_debug_mode,
    get_default_language,
    get_default_model,
    get_default_review_log_dir,
    has_openrouter_api_key,
    set_default_debug_mode,
    set_default_language,
    set_default_model,
    set_default_review_log_dir,
)
from selvage.src.diff_parser import parse_git_diff
from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.json_parsing_error import JSONParsingError
from selvage.src.exceptions.openrouter_api_error import (
    OpenRouterAPIError,
    OpenRouterAuthenticationError,
    OpenRouterResponseError,
)
from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.model_config import ModelProvider, get_model_info
from selvage.src.models import ModelChoice, ReviewStatus
from selvage.src.models.error_response import ErrorResponse
from selvage.src.multiturn.models import TokenInfo
from selvage.src.multiturn.multiturn_review_executor import MultiturnReviewExecutor
from selvage.src.ui import run_app
from selvage.src.utils.base_console import console
from selvage.src.utils.file_utils import find_project_root
from selvage.src.utils.git_utils import GitDiffMode, GitDiffUtility
from selvage.src.utils.logging import LOG_LEVEL_INFO, setup_logging
from selvage.src.utils.logging.review_log_manager import ReviewLogManager
from selvage.src.utils.prompts.models import ReviewPromptWithFileContent
from selvage.src.utils.prompts.prompt_generator import PromptGenerator
from selvage.src.utils.review_display import review_display
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse


@click.group(invoke_without_command=True)
@click.option(
    "--version",
    is_flag=True,
    help="버전 정보를 출력합니다.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    version: bool,
) -> None:
    """LLM 기반 코드 리뷰 도구"""
    # Context 객체 초기화
    if ctx.obj is None:
        ctx.obj = {}

    # 버전 정보 출력
    if version:
        click.echo(f"selvage {__version__}")
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


def config_language(language: str | None = None) -> None:
    """언어 설정을 처리합니다."""
    if language is not None:
        if set_default_language(language):
            console.success(f"기본 언어가 {language}로 설정되었습니다.")
        else:
            console.error("기본 언어 설정에 실패했습니다.")
    else:
        # 언어가 지정되지 않은 경우 현재 설정을 표시
        current_language = get_default_language()
        console.info(f"현재 기본 언어: {current_language}")
        console.info(
            "기본 언어를 설정하려면 'selvage config language <language>' "
            "명령어를 사용하세요."
        )


def config_review_log_dir(log_dir: str | None = None) -> None:
    """리뷰 로그 디렉토리 설정을 처리합니다."""
    if log_dir is not None:
        set_default_review_log_dir(log_dir)
    else:
        # 값이 지정되지 않은 경우 현재 설정을 표시
        current_value = get_default_review_log_dir()
        if current_value:
            console.info(f"현재 리뷰 로그 디렉토리: {current_value}")
        else:
            console.info("리뷰 로그 디렉토리가 설정되지 않았습니다.")


def config_list() -> None:
    """모든 설정을 표시합니다."""
    console.print("==== selvage 설정 ====", style="bold cyan")
    console.print("")

    # OpenRouter First 방식 안내

    if has_openrouter_api_key():
        console.print(
            "🚀 [bold green]OpenRouter First 모드[/bold green]: 모든 모델이 OpenRouter를 통해 작동합니다",
            style="green",
        )
    else:
        console.print(
            "💡 [bold yellow]OpenRouter First[/bold yellow]: OPENROUTER_API_KEY를 설정하면 모든 모델을 OpenRouter를 통해 사용할 수 있습니다",
            style="yellow",
        )
    console.print("")

    # 기존 API key 표시 로직은 유지...
    for provider in ModelProvider:
        provider_display = provider.get_display_name()
        env_var_name = provider.get_env_var_name()
        env_value = os.getenv(env_var_name)

        try:
            # API 키 가져오기 시도 (에러 메시지 억제)
            from unittest.mock import patch

            with patch("selvage.src.config.console"):
                get_api_key(provider)

            if env_value:
                console.print(
                    f"{provider_display} API 키: [bold green]환경변수[/bold green] {env_var_name}에서 설정됨 ✓",
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

    console.print("")

    # 기본 설정들 표시
    console.print("[bold]기본 설정[/bold]", style="cyan")
    default_model = get_default_model()
    if default_model:
        console.print(f"기본 모델: {default_model}", style="green")
    else:
        console.print("기본 모델: 설정되지 않음", style="red")

    default_language = get_default_language()
    if default_language:
        console.print(f"기본 언어: {default_language}", style="green")
    else:
        console.print("기본 언어: 설정되지 않음", style="red")

    default_debug_mode = get_default_debug_mode()
    console.print(f"디버그 모드: {default_debug_mode}", style="green")

    review_log_dir = get_default_review_log_dir()
    console.print(f"리뷰 로그 디렉토리: {review_log_dir}", style="green")


def _handle_context_limit_error(
    review_prompt: ReviewPromptWithFileContent,
    error_response: ErrorResponse,
    llm_gateway: BaseGateway,
) -> tuple[ReviewResponse, EstimatedCost]:
    """Context limit 에러 시 multiturn review 실행"""
    token_info = TokenInfo.from_error_response(error_response)
    executor = MultiturnReviewExecutor()
    multiturn_result = executor.execute_multiturn_review(
        review_prompt=review_prompt,
        token_info=token_info,
        llm_gateway=llm_gateway,
    )

    return multiturn_result.review_response, multiturn_result.estimated_cost


def _handle_api_error(error_response: ErrorResponse) -> None:
    """API 에러 처리"""

    # OpenRouter 관련 에러 특별 처리
    if isinstance(error_response.exception, OpenRouterAPIError):
        _handle_openrouter_error(error_response.exception)
    elif isinstance(error_response.exception, JSONParsingError):
        _handle_json_parsing_error(error_response.exception)
    else:
        # 기존 에러 처리 로직
        console.error(
            f"API 오류 ({error_response.provider}): {error_response.error_message}"
        )

    raise Exception(f"API error: {error_response.error_message}")


def _handle_openrouter_error(error: OpenRouterAPIError) -> None:
    """OpenRouter 관련 에러 처리"""
    if isinstance(error, OpenRouterAuthenticationError):
        console.error("OpenRouter API 인증 오류")
        console.info("해결 방법:")
        console.print("  1. OPENROUTER_API_KEY 환경변수 확인")
        console.print("  2. API 키 유효성 확인")
    elif isinstance(error, OpenRouterResponseError):
        console.error(f"OpenRouter API 응답 구조 오류: {error}")
        if error.missing_field:
            console.error(f"누락된 필드: {error.missing_field}")
        if get_default_debug_mode() and error.raw_response:
            console.error(f"원본 응답: {error.raw_response}")
    else:
        console.error(f"OpenRouter API 오류: {error}")


def _handle_json_parsing_error(error: JSONParsingError) -> None:
    """JSON 파싱 에러 처리"""
    console.error("구조화된 응답 파싱에 실패했습니다")
    console.error(f"오류: {error}")

    if get_default_debug_mode():
        console.error("디버그 정보:")
        if error.parsing_error:
            console.error(f"  파싱 오류: {error.parsing_error}")
        if error.raw_response:
            console.error(f"  원본 응답 (일부): {error.raw_response}")


def _handle_unknown_error() -> None:
    """알 수 없는 에러 처리"""
    console.error("알 수 없는 오류가 발생했습니다.")
    raise Exception("Unknown error occurred")


def _perform_new_review(
    review_request: ReviewRequest,
) -> tuple[ReviewResponse, EstimatedCost]:
    """새로운 리뷰를 수행하고 결과를 반환합니다."""
    # LLM 게이트웨이 가져오기
    llm_gateway = GatewayFactory.create(model=review_request.model)

    # 새로운 enhanced_progress_review 컨텍스트 매니저 사용
    with review_display.enhanced_progress_review(review_request.model) as progress:
        review_prompt = PromptGenerator().create_code_review_prompt(review_request)
        review_result = llm_gateway.review_code(review_prompt)

        # 에러 처리
        if not review_result.success:
            if not review_result.error_response:
                _handle_unknown_error()

            error_response = review_result.error_response
            if error_response.is_context_limit_error():
                # UI 연속성을 유지하면서 멀티턴 모드로 전환
                progress.transition_to_multiturn(
                    "Context 한계 도달! Long context mode로 처리 중..."
                )
                result = _handle_context_limit_error(
                    review_prompt, error_response, llm_gateway
                )
                progress.complete()
                return result
            else:
                _handle_api_error(error_response)

        progress.complete()
        return review_result.review_response, review_result.estimated_cost


def review_code(
    model: str,
    repo_path: str = ".",
    staged: bool = False,
    target_commit: str | None = None,
    target_branch: str | None = None,
    open_ui: bool = False,
    print_result: bool = False,
    port: int = 8501,
    skip_cache: bool = False,
    clear_cache: bool = False,
    review_log_dir: str | None = None,
) -> None:
    """코드 리뷰를 수행합니다."""
    # API 키 확인 - OpenRouter First 방식
    model_info = get_model_info(model)
    provider = model_info.get("provider", "unknown")

    # OpenRouter First: OpenRouter key가 있으면 OpenRouter를 사용

    if has_openrouter_api_key():
        provider = ModelProvider.OPENROUTER

    api_key = get_api_key(provider)
    if not api_key:
        console.error(f"{provider.get_display_name()} API 키가 설정되지 않았습니다.")
        console.info("환경변수로 API 키를 설정해주세요:")
        console.print(
            f"  [green]export {provider.get_env_var_name()}=YOUR_API_KEY[/green]"
        )
        return

    # 캐시 매니저 초기화
    cache_manager = CacheManager()

    # 캐시 삭제 요청시
    if clear_cache:
        cache_manager.clear_cache()

    # 만료된 캐시 정리
    cache_manager.cleanup_expired_cache()

    # Git diff 내용 가져오기
    diff_content = get_diff_content(repo_path, staged, target_commit, target_branch)
    if not diff_content:
        console.warning("변경 사항이 없거나 diff를 가져올 수 없습니다.")
        return

    # repo_path 결정 - 사용자 입력 또는 프로젝트 루트
    repo_path = str(Path(repo_path)) if repo_path != "." else str(find_project_root())
    diff_result = parse_git_diff(diff_content, repo_path)
    review_prompt = None
    # 리뷰 요청 생성
    review_request = ReviewRequest(
        diff_content=diff_content,
        processed_diff=diff_result,
        file_paths=[file.filename for file in diff_result.files],
        model=model,
        repo_path=repo_path,
    )
    try:
        if skip_cache:
            # 캐시 사용하지 않고 직접 리뷰 수행
            log_id = ReviewLogManager.generate_log_id(model)
            review_response, estimated_cost = _perform_new_review(review_request)
            review_prompt = PromptGenerator().create_code_review_prompt(review_request)
            log_path = ReviewLogManager.save(
                review_prompt,
                review_request,
                review_response,
                ReviewStatus.SUCCESS,
                log_id=log_id,
                review_log_dir=review_log_dir,
                estimated_cost=estimated_cost,
            )
        else:
            # 캐시 확인 시도
            cached_result = cache_manager.get_cached_review(review_request)

            if cached_result:
                # 캐시 적중: 저장된 결과 사용
                review_response, cached_cost = cached_result

                # 캐시 적중 비용 표시 (0 USD)
                estimated_cost = EstimatedCost.get_zero_cost(model)

                # 캐시된 결과에 대해서도 log_id 생성
                log_id = ReviewLogManager.generate_log_id(model)
                review_prompt = PromptGenerator().create_code_review_prompt(
                    review_request
                )
                log_path = ReviewLogManager.save(
                    review_prompt,
                    review_request,
                    review_response,
                    ReviewStatus.SUCCESS,
                    log_id=log_id,
                    review_log_dir=review_log_dir,
                    estimated_cost=estimated_cost,
                )

                console.success("캐시된 리뷰 결과를 사용했습니다! (API 비용 절약)")
            else:
                # 캐시 미스: 새로운 리뷰 수행 후 캐시에 저장
                log_id = ReviewLogManager.generate_log_id(model)
                review_response, estimated_cost = _perform_new_review(review_request)

                # 리뷰 결과를 캐시에 저장
                cache_manager.save_review_to_cache(
                    review_request, review_response, estimated_cost, log_id=log_id
                )

                review_prompt = PromptGenerator().create_code_review_prompt(
                    review_request
                )
                log_path = ReviewLogManager.save(
                    review_prompt,
                    review_request,
                    review_response,
                    ReviewStatus.SUCCESS,
                    log_id=log_id,
                    review_log_dir=review_log_dir,
                    estimated_cost=estimated_cost,
                )

        # 리뷰 완료 정보 통합 출력
        review_display.review_complete(
            model_info=model_info,
            log_path=log_path,
            estimated_cost=estimated_cost,
        )

        console.success("코드 리뷰가 완료되었습니다!")
    except UnsupportedModelError:
        # UnsupportedModelError는 이미 명확한 메시지가 표시되었으므로 
        # 추가 메시지 없이 종료
        return
    except Exception as e:
        console.error(f"코드 리뷰 중 오류가 발생했습니다: {str(e)}", exception=e)
        error_log_id = ReviewLogManager.generate_log_id(model)
        log_path = ReviewLogManager.save(
            review_prompt,
            review_request,
            None,
            ReviewStatus.FAILED,
            error=e,
            log_id=error_log_id,
            review_log_dir=review_log_dir,
        )
        return

    # 터미널에 리뷰 결과 출력
    if print_result:
        review_display.print_review_result(log_path)

    # UI 자동 실행
    if open_ui:
        console.info("리뷰 결과 UI를 시작합니다...")
        handle_view_command(port)


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
    "--no-print",
    "no_print_result",
    is_flag=True,
    help="터미널에 리뷰 결과를 출력하지 않음",
    type=bool,
)
@click.option(
    "--skip-cache",
    is_flag=True,
    help="캐시를 사용하지 않고 새로운 리뷰 수행",
    type=bool,
)
@click.option(
    "--clear-cache", is_flag=True, help="캐시를 삭제한 후 리뷰 수행", type=bool
)
@click.option(
    "--log-dir",
    help="로그 저장 디렉토리",
    type=str,
)
def review(
    repo_path: str,
    staged: bool,
    target_commit: str | None,
    target_branch: str | None,
    model: str | None,
    open_ui: bool,
    no_print_result: bool,
    skip_cache: bool,
    clear_cache: bool,
    log_dir: str | None,
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

    # 터미널 출력 로직: 기본적으로 출력하되, --open-ui 사용 시 또는 --no-print 사용 시 비활성화
    print_result = not (open_ui or no_print_result)

    review_code(
        model=model,
        repo_path=repo_path,
        staged=staged,
        target_commit=target_commit,
        target_branch=target_branch,
        open_ui=open_ui,
        print_result=print_result,
        skip_cache=skip_cache,
        clear_cache=clear_cache,
        review_log_dir=log_dir,
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
@click.argument(
    "value", type=click.Choice(["on", "off"]), required=False, default="off"
)
def debug_mode(value: str | None) -> None:
    """디버그 모드 설정 (on / off)"""
    config_debug_mode(value)


@config.command(name="review-log-dir")
@click.argument("directory_path", required=False)
def review_log_dir(directory_path: str | None) -> None:
    """리뷰 로그 저장 디렉토리 설정"""
    config_review_log_dir(directory_path)


@config.command(name="language")
@click.argument("language_name", required=False)
def language(language_name: str | None) -> None:
    """기본 언어 설정"""
    config_language(language_name)


@config.command(name="list")
def show_config() -> None:
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
