"""리뷰 로그 관리 모듈."""

import json
import os
from datetime import datetime
from pathlib import Path

from selvage.src.config import get_default_review_log_dir
from selvage.src.model_config import get_model_info
from selvage.src.models.review_status import ReviewStatus
from selvage.src.utils.prompts.models.review_prompt_with_file_content import (
    ReviewPromptWithFileContent,
)
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse


class ReviewLogManager:
    """리뷰 로그 관리 클래스."""

    @staticmethod
    def generate_log_id(model: str) -> str:
        """리뷰 로그 ID를 생성합니다."""
        model_info = get_model_info(model)
        provider = model_info.get("provider", "unknown")
        model_name = model_info.get("full_name", model)
        now = datetime.now()
        return f"{provider.value}-{model_name}-{int(now.timestamp())}"

    @staticmethod
    def save(
        prompt: ReviewPromptWithFileContent | None,
        review_request: ReviewRequest,
        review_response: ReviewResponse | None,
        status: ReviewStatus,
        error: Exception | None = None,
        log_id: str | None = None,
        review_log_dir: str | None = None,
        estimated_cost: EstimatedCost | None = None,
    ) -> str:
        """리뷰 로그를 저장하고 파일 경로를 반환합니다."""
        model_info = get_model_info(review_request.model)

        # 리뷰 로그 디렉토리 결정: 파라미터로 제공되면 사용, 없으면 기본값 사용
        if review_log_dir:
            log_dir = Path(os.path.expanduser(review_log_dir))
            # 절대 경로로 변환
            if not log_dir.is_absolute():
                log_dir = log_dir.resolve()
        else:
            log_dir = get_default_review_log_dir()

        log_dir.mkdir(parents=True, exist_ok=True)

        # 로그 저장을 위한 프롬프트 데이터 변환
        prompt_data = None
        if prompt:
            prompt_data = prompt.to_messages()

        # 로그 저장을 위한 응답 데이터 JSON 직렬화
        response_data = None
        if review_response:
            response_data = review_response.model_dump(mode="json")

        now = datetime.now()
        if log_id is None:
            log_id = ReviewLogManager.generate_log_id(review_request.model)

        provider = model_info.get("provider", "unknown")
        model_name = model_info.get("full_name", review_request.model)

        # JSON 로그 데이터 구성
        review_log = {
            "id": log_id,
            "model": {"provider": provider.value, "name": model_name},
            "created_at": now.isoformat(),
            "prompt": prompt_data,
            "review_request": review_request.model_dump(mode="json"),
            "review_response": response_data,
            "status": status.value,
            "error": str(error) if error else None,
            "prompt_version": "v3",
            "repo_path": review_request.repo_path,
        }

        # 비용 정보가 있는 경우 추가
        if estimated_cost:
            review_log["token_info"] = {
                "input_tokens": estimated_cost.input_tokens,
                "output_tokens": estimated_cost.output_tokens,
            }
            review_log["total_cost"] = estimated_cost.total_cost_usd

        # 파일 저장
        formatted = now.strftime("%Y%m%d_%H%M%S")
        file_name = f"{formatted}_{model_name}_review_log"
        file_path = log_dir / f"{file_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(review_log, f, ensure_ascii=False, indent=2)

        return str(file_path)
