"""에이전트 위임 리뷰 컨텍스트 저장소.

대규모 diff 컨텍스트를 로컬 파일에 저장하고
파일별로 분할 조회할 수 있는 기능을 제공합니다.
"""

import json
import logging
import re
import time
import uuid
from pathlib import Path

from selvage.src.utils.platform_utils import get_platform_config_dir

logger = logging.getLogger(__name__)

_CONTEXT_ID_PATTERN = re.compile(r"^ctx-\d+-[0-9a-f]{8}$")


class DelegatedContextStore:
    """에이전트 위임 리뷰 컨텍스트를 로컬 파일에 저장/조회하는 클래스.

    저장 경로: {platform_config_dir}/delegated_context/{context_id}.json
    TTL: 60분 (리뷰 세션 내에서만 유효)
    """

    def __init__(self, store_dir: Path | None = None) -> None:
        if store_dir is None:
            store_dir = get_platform_config_dir() / "delegated_context"
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def save(self, context_data: dict) -> str:
        """컨텍스트 데이터를 JSON 파일로 저장합니다.

        Args:
            context_data: 저장할 컨텍스트 데이터
                (system_prompt, review_targets, output_format, metadata, file_list)

        Returns:
            context_id: "ctx-{unix_timestamp}-{uuid_hex[:8]}" 형태의 고유 ID
        """
        context_id = f"ctx-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        data_to_save = {**context_data, "created_at": time.time()}

        file_path = self.store_dir / f"{context_id}.json"
        file_path.write_text(
            json.dumps(data_to_save, ensure_ascii=False), encoding="utf-8"
        )

        return context_id

    def load_file_context(self, context_id: str, file_path: str) -> dict | None:
        """저장된 컨텍스트에서 특정 파일의 리뷰 타겟을 조회합니다.

        Args:
            context_id: 컨텍스트 ID
            file_path: 조회할 파일 경로

        Returns:
            해당 파일의 리뷰 타겟 dict (role + content) 또는 None
        """
        data = self._load_context(context_id)
        if data is None:
            return None

        review_targets = data.get("review_targets", [])
        for target in review_targets:
            content = target.get("content", "")
            if not isinstance(content, str):
                continue
            try:
                parsed = json.loads(content)
                if parsed.get("file_name") == file_path:
                    return target
            except (json.JSONDecodeError, TypeError, AttributeError) as e:
                logger.warning(
                    "Failed to parse review target content in context %s: %s",
                    context_id,
                    e,
                )
                continue

        return None

    def load_metadata(self, context_id: str) -> dict | None:
        """컨텍스트 ID의 전체 메타데이터를 반환합니다.

        Args:
            context_id: 컨텍스트 ID

        Returns:
            전체 컨텍스트 데이터 dict 또는 None
        """
        return self._load_context(context_id)

    def cleanup_expired(self, ttl_minutes: int = 60) -> int:
        """mtime 기준 만료된 컨텍스트 파일을 삭제합니다.

        Args:
            ttl_minutes: 만료 시간 (분, 기본: 60)

        Returns:
            삭제된 파일 수
        """
        cutoff = time.time() - (ttl_minutes * 60)
        deleted = 0
        for file_path in self.store_dir.glob("ctx-*.json"):
            try:
                if file_path.stat().st_mtime < cutoff:
                    file_path.unlink()
                    deleted += 1
            except OSError as e:
                logger.warning("Failed to clean up %s: %s", file_path, e)
        return deleted

    @staticmethod
    def _validate_context_id(context_id: str) -> bool:
        """context_id가 유효한 형식인지 검증합니다."""
        return bool(_CONTEXT_ID_PATTERN.match(context_id))

    def _load_context(self, context_id: str) -> dict | None:
        """컨텍스트 ID로 JSON 파일을 로드합니다."""
        if not self._validate_context_id(context_id):
            logger.warning("Invalid context_id format: %s", context_id)
            return None
        file_path = self.store_dir / f"{context_id}.json"
        if not file_path.exists():
            logger.info("Context file not found: %s (may have expired)", context_id)
            return None
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load context %s: %s", context_id, e)
            return None
