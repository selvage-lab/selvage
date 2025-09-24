"""리뷰 로그 관리 모듈."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from selvage.src.config import get_default_review_log_dir
from selvage.src.model_config import get_model_info
from selvage.src.models.review_status import ReviewStatus
from selvage.src.utils.file_utils import find_project_root
from selvage.src.utils.prompts.models.review_prompt_with_file_content import (
    ReviewPromptWithFileContent,
)
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse

# 타입 정의
RepoPath = Literal["CURRENT_PROJECT", "ALL"] | str


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
            "prompt_version": "v4",
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

    @staticmethod
    def get_recent_logs(
        limit: int = 10,
        repo_path: RepoPath = "CURRENT_PROJECT",
        model_filter: str | None = None,
    ) -> list[dict]:
        """최근 리뷰 로그들을 조회합니다.

        Args:
            limit: 조회할 로그 수 (기본: 10)
            repo_path: 리포지토리 경로 필터
                - "CURRENT_PROJECT": 현재 프로젝트 로그만 조회 (기본값)
                - "ALL": 모든 프로젝트 로그 조회
                - 특정 경로: 해당 경로의 프로젝트 로그만 조회 (예: "/path/to/project")
            model_filter: 모델 필터 (선택사항)

        Returns:
            list[dict]: 로그 데이터 리스트 (최신순 정렬)
        """
        log_dir = get_default_review_log_dir()
        if not log_dir.exists():
            return []

        # repo_path 처리: "CURRENT_PROJECT"이면 현재 프로젝트 경로 사용
        if repo_path == "CURRENT_PROJECT":
            try:
                repo_path = str(find_project_root())
            except FileNotFoundError:
                # 프로젝트 루트를 찾을 수 없으면 현재 디렉토리 사용
                repo_path = str(Path.cwd())

        logs = []

        # JSON 로그 파일들을 찾아서 파싱
        for log_file in log_dir.glob("*.json"):
            try:
                with open(log_file, encoding="utf-8") as f:
                    log_data = json.load(f)

                # 필터링 적용
                if model_filter:
                    model_name = log_data.get("model", {}).get("name", "")
                    if model_filter not in model_name:
                        continue

                # repo_path 필터링 ("ALL"이면 모든 프로젝트 로그 포함)
                if repo_path != "ALL":
                    log_repo_path = log_data.get("repo_path", "")
                    # 절대 경로 비교를 위해 resolve() 사용
                    try:
                        if log_repo_path and repo_path:
                            log_path_resolved = Path(log_repo_path).resolve()
                            repo_path_resolved = Path(repo_path).resolve()
                            if log_path_resolved != repo_path_resolved:
                                continue
                        elif log_repo_path != repo_path:
                            continue
                    except (OSError, ValueError):
                        # 경로 해석 실패 시 문자열 직접 비교
                        if log_repo_path != repo_path:
                            continue

                # MCP에서 요구하는 형태로 데이터 변환
                log_item = {
                    "log_id": log_data.get("id", ""),
                    "timestamp": ReviewLogManager._parse_timestamp(
                        log_data.get("created_at", "")
                    ),
                    "model": log_data.get("model", {}).get("name", ""),
                    "files_count": ReviewLogManager._extract_files_count(log_data),
                    "status": log_data.get("status", "UNKNOWN"),
                    "cost": log_data.get("total_cost", 0.0),
                }
                logs.append(log_item)

            except (json.JSONDecodeError, KeyError, TypeError):
                # 잘못된 로그 파일은 건너뛰기
                continue

        # 최신순으로 정렬
        logs.sort(key=lambda x: x["timestamp"], reverse=True)

        # limit 적용
        return logs[:limit]

    @staticmethod
    def load_log(log_id: str) -> dict:
        """특정 로그 ID의 로그를 로드합니다.

        Args:
            log_id: 로드할 로그 ID

        Returns:
            dict: 로그 데이터

        Raises:
            FileNotFoundError: 로그 파일을 찾을 수 없는 경우
            json.JSONDecodeError: JSON 파싱 실패 시
        """
        log_dir = get_default_review_log_dir()
        if not log_dir.exists():
            raise FileNotFoundError(f"로그 디렉토리를 찾을 수 없습니다: {log_dir}")

        # 모든 JSON 파일을 검색하여 해당 log_id 찾기
        json_decode_errors = []
        for log_file in log_dir.glob("*.json"):
            try:
                with open(log_file, encoding="utf-8") as f:
                    log_data = json.load(f)

                if log_data.get("id") == log_id:
                    return log_data

            except json.JSONDecodeError as e:
                # JSON 파싱 에러는 따로 수집하여 마지막에 발생
                json_decode_errors.append((log_file, e))
                continue
            except (KeyError, TypeError):
                # 잘못된 로그 파일은 건너뛰기
                continue

        # JSON 파싱 에러가 있었다면 먼저 발생
        if json_decode_errors:
            first_error_file, first_error = json_decode_errors[0]
            raise json.JSONDecodeError(
                f"Invalid JSON in {first_error_file}: {first_error.msg}",
                first_error.doc,
                first_error.pos,
            )

        raise FileNotFoundError(f"로그 ID '{log_id}'를 찾을 수 없습니다")

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> str:
        """타임스탬프 문자열을 검증하고 ISO 형식으로 정규화합니다."""
        if not timestamp_str:
            return datetime.now().isoformat()

        try:
            # Z suffix 제거
            normalized_str = timestamp_str
            if normalized_str.endswith("Z"):
                normalized_str = normalized_str.replace("Z", "+00:00")

            # 유효한 ISO 형식인지 검증
            parsed_dt = datetime.fromisoformat(normalized_str)

            # timezone-naive 객체로 변환하고 ISO 형식 문자열로 반환
            if parsed_dt.tzinfo is not None:
                parsed_dt = parsed_dt.replace(tzinfo=None)

            return parsed_dt.isoformat()
        except ValueError:
            return datetime.now().isoformat()

    @staticmethod
    def _extract_files_count(log_data: dict) -> int:
        """로그 데이터에서 파일 수를 추출합니다."""
        review_request = log_data.get("review_request", {})
        files = review_request.get("files", [])

        if isinstance(files, list):
            return len(files)

        return 0
