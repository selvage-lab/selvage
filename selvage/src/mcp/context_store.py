"""에이전트 위임 리뷰 컨텍스트 저장소.

대규모 diff 컨텍스트를 로컬 파일에 저장하고
파일별로 분할 조회할 수 있는 기능을 제공합니다.
"""

import json
import time
import uuid
from pathlib import Path

from selvage.src.utils.platform_utils import get_platform_config_dir


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
        context_data["created_at"] = time.time()

        file_path = self.store_dir / f"{context_id}.json"
        file_path.write_text(
            json.dumps(context_data, ensure_ascii=False), encoding="utf-8"
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
            if isinstance(content, str) and file_path in content:
                return target

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
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                deleted += 1
        return deleted

    def _load_context(self, context_id: str) -> dict | None:
        """컨텍스트 ID로 JSON 파일을 로드합니다."""
        file_path = self.store_dir / f"{context_id}.json"
        if not file_path.exists():
            return None
        return json.loads(file_path.read_text(encoding="utf-8"))
