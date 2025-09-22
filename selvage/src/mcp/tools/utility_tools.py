"""MCP 유틸리티 도구 구현"""

import logging
from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from selvage.__version__ import __version__
from selvage.src.config import get_api_key
from selvage.src.model_config import ModelConfig, get_model_info
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.logging.review_log_manager import ReviewLogManager

from ..models.responses import ModelInfo, ReviewHistoryItem, ServerStatus

# 상수 정의
MAX_HISTORY_LIMIT = 50  # 성능 및 메모리 사용량 고려
MIN_HISTORY_LIMIT = 1
DEFAULT_HISTORY_LIMIT = 10
TOTAL_MCP_TOOLS_COUNT = 9  # 리뷰 도구 4개 + 유틸리티 도구 5개


def get_available_models() -> list[ModelInfo]:
    """Selvage에서 사용 가능한 AI 모델 목록을 조회합니다."""
    try:
        config = ModelConfig()
        models_data = config.get_all_models_config()
        model_list = []

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
    limit: int = DEFAULT_HISTORY_LIMIT,
    repo_path: str = ".",
    model_filter: str | None = None,
) -> list[ReviewHistoryItem]:
    """최근 코드 리뷰 히스토리를 조회합니다.

    Args:
        limit: 조회할 히스토리 개수 (1-50 범위로 제한됨)
        repo_path: Git 저장소 경로
        model_filter: 특정 모델로 필터링
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
            # timestamp가 문자열이면 datetime으로 변환
            timestamp = log_data.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = datetime.now()
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()

            history_item = ReviewHistoryItem(
                log_id=log_data.get("log_id", ""),
                timestamp=timestamp,
                model=log_data.get("model", ""),
                files_count=log_data.get("files_count", 0),
                status=log_data.get("status", "UNKNOWN"),
                cost=log_data.get("cost", 0.0),
                review_type=log_data.get("review_type", "unknown"),
                target=log_data.get("target"),
            )
            history_items.append(history_item)

        return history_items
    except (ImportError, AttributeError, KeyError, ValueError) as e:
        # 예상 가능한 데이터 처리 관련 오류
        logging.warning(f"Failed to load review history: {e}")
        return []
    except Exception as e:
        # 예상치 못한 오류는 로깅 후 재발생
        logging.error(f"Unexpected error in get_review_history: {e}")
        raise


def get_review_details(log_id: str) -> dict[str, Any]:
    """특정 리뷰의 상세 정보를 조회합니다."""
    try:
        log_data = ReviewLogManager.load_log(log_id)
        return log_data
    except Exception as e:
        return {
            "error": True,
            "error_message": f"로그 조회 중 오류가 발생했습니다: {str(e)}",
        }


def get_server_status() -> ServerStatus:
    """MCP 서버의 현재 상태를 조회합니다."""
    return ServerStatus(
        running=True,
        port=None,  # stdio 모드이므로 포트 없음
        host=None,  # stdio 모드이므로 호스트 없음
        start_time=None,  # 시작 시간 추적하지 않음
        version=__version__,
        tools_count=TOTAL_MCP_TOOLS_COUNT,
    )


def validate_model_config(model: str) -> dict[str, Any]:
    """지정된 모델의 설정과 API 키를 검증합니다."""
    try:
        # 1. 모델 정보 검증
        model_info = get_model_info(model)
        if not model_info:
            return {
                "valid": False,
                "model": model,
                "error_message": f"지원되지 않는 모델입니다: {model}",
            }

        # 2. 프로바이더 정보 추출
        provider_str = model_info.get("provider")
        if isinstance(provider_str, str):
            try:
                provider = ModelProvider(provider_str)
            except ValueError:
                return {
                    "valid": False,
                    "model": model,
                    "error_message": f"지원되지 않는 프로바이더입니다: {provider_str}",
                }
        else:
            provider = provider_str

        # 3. API 키 검증
        api_key = get_api_key(provider)
        has_api_key = bool(api_key)

        return {
            "valid": True,
            "model": model,
            "provider": provider.get_display_name(),
            "has_api_key": has_api_key,
            "model_info": {
                "display_name": model_info.get("display_name", model),
                "description": model_info.get("description", ""),
                "max_tokens": model_info.get("max_tokens", 0),
                "cost_per_1k_tokens": model_info.get("cost_per_1k_tokens", 0.0),
            },
        }
    except Exception as e:
        return {
            "valid": False,
            "model": model,
            "error_message": f"모델 검증 중 오류가 발생했습니다: {str(e)}",
        }


def register_utility_tools(mcp: FastMCP) -> None:
    """유틸리티 관련 MCP 도구들을 등록합니다."""

    @mcp.tool()
    def get_available_models_tool() -> dict:
        """
        Selvage에서 사용 가능한 AI 모델 목록을 조회합니다.

        Returns:
            dict: 사용 가능한 모델들의 정보 리스트
        """
        models = get_available_models()
        return {"models": [model.model_dump() for model in models]}

    @mcp.tool()
    def get_review_history_tool(
        limit: int = 10,
        repo_path: str = ".",
        model_filter: str | None = None,
    ) -> dict:
        """
        최근 코드 리뷰 히스토리를 조회합니다.

        Args:
            limit: 조회할 히스토리 개수 (최대 50)
            repo_path: Git 저장소 경로
            model_filter: 특정 모델로 필터링 (선택적)

        Returns:
            dict: 리뷰 히스토리 목록
        """
        history = get_review_history(limit, repo_path, model_filter)
        return {"history": [item.model_dump() for item in history]}

    @mcp.tool()
    def get_review_details_tool(log_id: str) -> dict:
        """
        특정 리뷰의 상세 정보를 조회합니다.

        Args:
            log_id: 조회할 리뷰의 로그 ID

        Returns:
            dict: 리뷰 상세 정보 (프롬프트, 응답, 메타데이터 포함)
        """
        return get_review_details(log_id)

    @mcp.tool()
    def get_server_status_tool() -> dict:
        """
        MCP 서버의 현재 상태를 조회합니다.

        Returns:
            dict: 서버 상태 정보
        """
        status = get_server_status()
        return status.model_dump()

    @mcp.tool()
    def validate_model_config_tool(model: str) -> dict:
        """
        지정된 모델의 설정과 API 키를 검증합니다.

        Args:
            model: 검증할 모델명

        Returns:
            dict: 검증 결과 (유효성, 에러 메시지 등)
        """
        return validate_model_config(model)
