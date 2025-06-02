"""캐시 키 생성 로직"""

import hashlib
import json

from .models import CacheKeyInfo


class CacheKeyGenerator:
    """캐시 키 생성을 담당하는 클래스"""

    @staticmethod
    def generate_cache_key(cache_info: CacheKeyInfo) -> str:
        """캐시 키를 생성합니다.

        Args:
            cache_info: 캐시 키 생성에 필요한 정보

        Returns:
            str: SHA256 해시로 생성된 캐시 키
        """
        # 캐시 키 생성에 영향을 주는 요소들을 정렬된 딕셔너리로 구성
        key_data = {
            "diff_content": cache_info.diff_content,
            "model": cache_info.model,
            "use_full_context": cache_info.use_full_context,
        }

        # JSON 직렬화 (키 정렬 보장)
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)

        # SHA256 해시 생성
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()
