"""MCP 유틸리티 도구 구현"""

import logging
from datetime import datetime

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


def register_utility_tools(mcp: FastMCP) -> None:
    """유틸리티 관련 MCP 도구들을 등록합니다."""

    @mcp.tool()
    def get_available_models() -> dict:
        """
        Selvage에서 사용 가능한 AI 모델 목록을 조회합니다.

        Returns:
            dict: 사용 가능한 모델들의 정보 리스트
        """
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

            return {"models": [model.model_dump() for model in model_list]}
        except (ImportError, AttributeError, KeyError) as e:
            # 예상 가능한 설정 관련 오류만 처리
            logging.warning(f"Failed to load model configuration: {e}")
            return {"models": []}
        except Exception as e:
            # 예상치 못한 오류는 로깅 후 재발생
            logging.error(f"Unexpected error in get_available_models: {e}")
            raise

    @mcp.tool()
    def get_review_history(
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
                        timestamp = datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
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

            return {"history": [item.model_dump() for item in history_items]}
        except Exception as e:
            # 예상치 못한 오류는 로깅 후 재발생
            logging.error(f"Unexpected error in get_review_history: {e}")
            raise

    @mcp.tool()
    def get_review_details(log_id: str) -> dict:
        """
        특정 리뷰의 상세 정보를 조회합니다.

        Args:
            log_id: 조회할 리뷰의 로그 ID

        Returns:
            dict: 리뷰 상세 정보 (프롬프트, 응답, 메타데이터 포함)
        """
        try:
            log_data = ReviewLogManager.load_log(log_id)
            return log_data
        except Exception as e:
            return {
                "error": True,
                "error_message": f"로그 조회 중 오류가 발생했습니다: {str(e)}",
            }

    @mcp.tool()
    def get_server_status() -> dict:
        """
        MCP 서버의 현재 상태를 조회합니다.

        Returns:
            dict: 서버 상태 정보
        """
        status = ServerStatus(
            running=True,
            port=None,  # stdio 모드이므로 포트 없음
            host=None,  # stdio 모드이므로 호스트 없음
            start_time=None,  # 시작 시간 추적하지 않음
            version=__version__,
            tools_count=TOTAL_MCP_TOOLS_COUNT,
        )
        return status.model_dump()

    @mcp.tool()
    def validate_model_config(model: str) -> dict:
        """
        지정된 모델의 설정과 API 키를 검증합니다.

        Args:
            model: 검증할 모델명

        Returns:
            dict: 검증 결과 (유효성, 에러 메시지 등)
        """
        try:
            # 1. 모델 정보 검증
            model_info = get_model_info(model)
            if not model_info:
                return {
                    "valid": False,
                    "error": f"지원되지 않는 모델입니다: {model}",
                }

            # 2. 프로바이더 정보 추출
            provider_value = model_info.get("provider")
            if isinstance(provider_value, str):
                try:
                    provider = ModelProvider.from_string(provider_value)
                except ValueError:
                    return {
                        "valid": False,
                        "error": f"지원되지 않는 프로바이더입니다: {provider_value}",
                    }
            elif isinstance(provider_value, ModelProvider):
                provider = provider_value
            else:
                return {
                    "valid": False,
                    "error": f"잘못된 프로바이더 타입입니다: {type(provider_value)}",
                }

            # 3. API 키 검증
            api_key = get_api_key(provider)
            if not api_key:
                return {
                    "valid": False,
                    "error": (
                        f"{provider.get_display_name()} API 키가 설정되지 않았습니다."
                    ),
                }

            return {
                "valid": True,
                "model": model,
                "provider": provider.get_display_name(),
                "api_key_configured": True,
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"모델 설정 검증 중 오류가 발생했습니다: {str(e)}",
            }
