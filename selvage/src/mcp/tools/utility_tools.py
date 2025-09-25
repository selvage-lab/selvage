"""MCP utility tools implementation"""

import logging
from datetime import datetime

from fastmcp import FastMCP

from selvage.__version__ import __version__
from selvage.src.config import get_api_key, has_openrouter_api_key
from selvage.src.model_config import ModelConfig, get_model_info
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.logging.review_log_manager import RepoPath, ReviewLogManager

from ..models.responses import (
    ApiKeyValidationResult,
    ModelInfo,
    ModelValidationResult,
    ReviewDetailsResult,
    ReviewHistoryItem,
    ServerStatus,
)

# 상수 정의
MAX_HISTORY_LIMIT = 50  # 성능 및 메모리 사용량 고려
MIN_HISTORY_LIMIT = 1
DEFAULT_HISTORY_LIMIT = 10
TOTAL_MCP_TOOLS_COUNT = 10  # 리뷰 도구 4개 + 유틸리티 도구 6개


def get_available_models() -> list[ModelInfo]:
    """
    Get list of available AI models in Selvage.

    Returns:
        list[ModelInfo]: List of available model information with the following
            attributes:
            - name: Model name
            - provider: Provider (openai, anthropic, google, openrouter)
            - display_name: Display name
            - description: Model description
            - cost_per_1k_tokens: Cost per 1000 tokens (USD)
            - max_tokens: Maximum token count
            - supports_function_calling: Function calling support
    """
    try:
        config = ModelConfig()
        models_data = config.get_all_models_config()
        model_list: list[ModelInfo] = []

        for model_name, model_data in models_data.items():
            model_info = ModelInfo(
                name=model_name,
                provider=model_data.get("provider", "unknown"),
                display_name=model_data.get("display_name", model_name),
                description=model_data.get("description", ""),
                cost_per_1k_tokens=model_data.get("cost_per_1k_tokens", 0.0),
                max_tokens=model_data.get("max_tokens", 0),
                supports_function_calling=model_data.get(
                    "supports_function_calling", False
                ),
            )
            model_list.append(model_info)

        return model_list
    except (ImportError, AttributeError, KeyError) as e:
        # 예상 가능한 설정 관련 오류만 처리
        logging.warning(f"Failed to load model configuration: {e}")
        return []
    except Exception as e:
        # 예상치 못한 오류는 로깅 후 재발생
        logging.error(f"Unexpected error in get_available_models: {e}")
        raise


def get_review_history(
    limit: int = 10,
    repo_path: RepoPath = "CURRENT_PROJECT",
    model_filter: str | None = None,
) -> list[ReviewHistoryItem]:
    """
    Get recent code review history.

    Args:
        limit: Number of history items to retrieve (max 50)
        repo_path: Repository path filter
            - "CURRENT_PROJECT": Current project logs only (default)
            - "ALL": All project logs
            - Specific path: Logs for that project path (e.g., "/path/to/project")
        model_filter: Filter by specific model (optional)

    Returns:
        list[ReviewHistoryItem]: List of review history items with the following
            attributes:
            - log_id: Log ID
            - timestamp: Review timestamp (ISO 8601 format)
            - model: Model used for review
            - files_count: Number of files reviewed
            - status: Review status (SUCCESS, FAILED)
            - cost: Actual cost (USD)
    """
    try:
        # limit 범위 제한 (성능 및 메모리 사용량 고려)
        if limit > MAX_HISTORY_LIMIT:
            limit = MAX_HISTORY_LIMIT
        if limit < MIN_HISTORY_LIMIT:
            limit = MIN_HISTORY_LIMIT

        # ReviewLogManager에서 최근 로그 조회
        logs_data = ReviewLogManager.get_recent_logs(
            limit=limit,
            repo_path=repo_path,
            model_filter=model_filter,
        )

        history_items = []
        for log_data in logs_data:
            timestamp_str = log_data.get("timestamp", datetime.now().isoformat())

            history_item = ReviewHistoryItem(
                log_id=log_data.get("log_id", ""),
                timestamp=timestamp_str,
                model=log_data.get("model", ""),
                files_count=log_data.get("files_count", 0),
                status=log_data.get("status", "UNKNOWN"),
                cost=log_data.get("cost", 0.0),
            )
            history_items.append(history_item)

        return history_items
    except Exception as e:
        # 예상치 못한 오류는 로깅 후 재발생
        logging.error(f"Unexpected error in get_review_history: {e}")
        raise


def get_review_details(log_id: str) -> ReviewDetailsResult:
    """
    Get detailed information of a specific review.

    Args:
        log_id: Log ID of the review to retrieve

    Returns:
        ReviewDetailsResult: Review details result with the following
            attributes:
            - success: Review retrieval success status
            - data: Review response data (on success)
            - error_message: Error message (on failure)
    """
    try:
        log_data = ReviewLogManager.load_log(log_id)
        review_response = log_data.get("review_response")
        if review_response is None:
            return ReviewDetailsResult(
                success=False,
                data=None,
                error_message="Review response data not found.",
            )
        return ReviewDetailsResult(
            success=True,
            data=review_response,
            error_message=None,
        )
    except Exception as e:
        return ReviewDetailsResult(
            success=False,
            data=None,
            error_message=f"An error occurred while retrieving log: {str(e)}",
        )


def get_server_status() -> ServerStatus:
    """
    Get current MCP server status.

    Returns:
        ServerStatus: Server status information
    """
    return ServerStatus(
        running=True,
        port=None,  # stdio 모드이므로 포트 없음
        host=None,  # stdio 모드이므로 호스트 없음
        start_time=None,  # 시작 시간 추적하지 않음
        version=__version__,
        tools_count=TOTAL_MCP_TOOLS_COUNT,
    )


def validate_model_support(model: str) -> ModelValidationResult:
    """
    모델 지원 여부 및 프로바이더 정보 검증

    Args:
        model: 검증할 모델 이름

    Returns:
        ModelValidationResult: 모델 지원 여부 검증 결과
    """
    try:
        # 1. 모델 정보 검증
        model_info = get_model_info(model)
        if not model_info:
            return ModelValidationResult(
                valid=False,
                error_message=f"Unsupported model: {model}",
            )

        # 2. 프로바이더 정보 추출
        provider_value = model_info.get("provider")
        if isinstance(provider_value, str):
            try:
                provider = ModelProvider.from_string(provider_value)
            except ValueError:
                return ModelValidationResult(
                    valid=False,
                    error_message=f"Unsupported provider: {provider_value}",
                )
        elif isinstance(provider_value, ModelProvider):
            provider = provider_value
        else:
            return ModelValidationResult(
                valid=False,
                error_message=f"Invalid provider type: {type(provider_value)}",
            )

        return ModelValidationResult(
            valid=True,
            model=model,
            provider=provider.get_display_name(),
        )
    except Exception as e:
        return ModelValidationResult(
            valid=False,
            error_message=f"An error occurred while validating model support: {str(e)}",
        )


def validate_api_key_for_provider(model: str) -> ApiKeyValidationResult:
    """
    모델의 API 키 검증 (OpenRouter-first 전략 적용)

    Args:
        model: 검증할 모델 이름

    Returns:
        ApiKeyValidationResult: API 키 검증 결과
    """
    try:
        # 1. 모델 정보 검증
        model_info = get_model_info(model)
        if not model_info:
            return ApiKeyValidationResult(
                valid=False,
                error_message=f"Unsupported model: {model}",
            )

        # 2. OpenRouter-first 전략: OpenRouter 키가 있으면 OpenRouter를 사용
        if has_openrouter_api_key():
            selected_provider = ModelProvider.OPENROUTER
        else:
            # OpenRouter 키가 없으면 모델의 원래 프로바이더 사용
            provider_value = model_info.get("provider")
            if isinstance(provider_value, str):
                try:
                    selected_provider = ModelProvider.from_string(provider_value)
                except ValueError:
                    error_msg = f"Unsupported provider: {provider_value}"
                    return ApiKeyValidationResult(
                        valid=False,
                        error_message=error_msg,
                    )
            elif isinstance(provider_value, ModelProvider):
                selected_provider = provider_value
            else:
                error_msg = f"Invalid provider type: {type(provider_value)}"
                return ApiKeyValidationResult(
                    valid=False,
                    error_message=error_msg,
                )

        # 3. API 키 검증
        api_key = get_api_key(selected_provider)
        if not api_key:
            return ApiKeyValidationResult(
                valid=False,
                provider=selected_provider.get_display_name(),
                api_key_configured=False,
                error_message=(
                    f"{selected_provider.get_display_name()} API key is not configured."
                ),
            )

        return ApiKeyValidationResult(
            valid=True,
            provider=selected_provider.get_display_name(),
            api_key_configured=True,
        )
    except Exception as e:
        return ApiKeyValidationResult(
            valid=False,
            error_message=f"An error occurred while validating API key: {str(e)}",
        )


def register_utility_tools(mcp: FastMCP) -> None:
    """유틸리티 관련 MCP 도구들을 등록합니다."""
    mcp.tool()(get_available_models)
    mcp.tool()(get_review_history)
    mcp.tool()(get_review_details)
    mcp.tool()(get_server_status)
    mcp.tool()(validate_model_support)
    mcp.tool()(validate_api_key_for_provider)
