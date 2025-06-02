"""캐시 관리 메인 클래스"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from selvage.src.utils.base_console import console
from selvage.src.utils.platform_utils import get_platform_config_dir
from selvage.src.utils.token.models import ReviewRequest, ReviewResponse, EstimatedCost

from .cache_key_generator import CacheKeyGenerator
from .models import CacheEntry, CacheKeyInfo


class CacheManager:
    """리뷰 결과 캐싱을 관리하는 클래스"""
    
    def __init__(self, cache_ttl_hours: int = 1):
        """캐시 매니저 초기화
        
        Args:
            cache_ttl_hours: 캐시 유효 기간 (hours)
        """
        self.cache_dir = get_platform_config_dir() / "cache"
        self.cache_ttl_hours = cache_ttl_hours
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """캐시 디렉토리 생성"""
        self.cache_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """캐시 파일 경로 생성"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get_cached_review(self, review_request: ReviewRequest) -> Optional[tuple[ReviewResponse, EstimatedCost | None]]:
        """캐시된 리뷰 결과를 조회합니다.
        
        Args:
            review_request: 리뷰 요청 정보
            
        Returns:
            Optional[tuple[ReviewResponse, EstimatedCost]]: 캐시된 결과 (없으면 None)
        """
        try:
            # 캐시 키 생성
            cache_info = CacheKeyInfo(
                diff_content=review_request.diff_content,
                model=review_request.model,
                use_full_context=review_request.use_full_context,
            )
            cache_key = CacheKeyGenerator.generate_cache_key(cache_info)
            
            # 캐시 파일 확인
            cache_file = self._get_cache_file_path(cache_key)
            if not cache_file.exists():
                return None
            
            # 캐시 데이터 로드
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_entry = CacheEntry.model_validate(cache_data)
            
            # 만료 확인
            if datetime.now() > cache_entry.expires_at:
                # 만료된 캐시 삭제
                cache_file.unlink(missing_ok=True)
                return None
            
            console.info(f"[green]캐시 적중![/green] 저장된 리뷰 결과를 사용합니다.")
            return cache_entry.review_response, cache_entry.estimated_cost
            
        except Exception as e:
            console.warning(f"캐시 조회 중 오류 발생: {str(e)}")
            return None
    
    def save_review_to_cache(
        self, 
        review_request: ReviewRequest, 
        review_response: ReviewResponse,
        estimated_cost: EstimatedCost | None = None,
        log_id: str | None = None
    ) -> None:
        """리뷰 결과를 캐시에 저장합니다.
        
        Args:
            review_request: 리뷰 요청 정보
            review_response: 리뷰 응답 결과
            estimated_cost: 비용 정보
            log_id: 원본 리뷰 로그 ID (추적용)
        """
        try:
            # 캐시 키 생성
            cache_info = CacheKeyInfo(
                diff_content=review_request.diff_content,
                model=review_request.model,
                use_full_context=review_request.use_full_context,
            )
            cache_key = CacheKeyGenerator.generate_cache_key(cache_info)
            
            # 캐시 엔트리 생성
            now = datetime.now()
            cache_entry = CacheEntry(
                cache_key=cache_key,
                created_at=now,
                expires_at=now + timedelta(hours=self.cache_ttl_hours),
                request_info={
                    "model": review_request.model,
                    "use_full_context": review_request.use_full_context,
                },
                review_response=review_response,
                estimated_cost=estimated_cost,
                log_id=log_id,
            )
            
            # 캐시 파일에 저장
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(
                    cache_entry.model_dump(mode='json'), 
                    f, 
                    ensure_ascii=False, 
                    indent=2
                )
            
            console.info(
                f"리뷰 결과를 캐시에 저장했습니다. "
                f"(유효기간: {self.cache_ttl_hours}시간)"
            )
            
        except Exception as e:
            console.warning(f"캐시 저장 중 오류 발생: {str(e)}")
    
    def clear_cache(self) -> None:
        """모든 캐시를 삭제합니다."""
        try:
            if not self.cache_dir.exists():
                console.info("삭제할 캐시가 없습니다.")
                return
            
            cache_files = list(self.cache_dir.glob("*.json"))
            for cache_file in cache_files:
                cache_file.unlink(missing_ok=True)
            
            console.success(f"캐시 {len(cache_files)}개를 삭제했습니다.")
            
        except Exception as e:
            console.error(f"캐시 삭제 중 오류 발생: {str(e)}")
    
    def cleanup_expired_cache(self) -> None:
        """만료된 캐시들을 정리합니다."""
        try:
            if not self.cache_dir.exists():
                return
            
            cache_files = list(self.cache_dir.glob("*.json"))
            expired_count = 0
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cache_entry = CacheEntry.model_validate(cache_data)
                    
                    if datetime.now() > cache_entry.expires_at:
                        cache_file.unlink(missing_ok=True)
                        expired_count += 1
                        
                except Exception:
                    # 잘못된 캐시 파일도 삭제
                    cache_file.unlink(missing_ok=True)
                    expired_count += 1
            
            if expired_count > 0:
                console.info(f"만료된 캐시 {expired_count}개를 정리했습니다.")
                
        except Exception as e:
            console.warning(f"캐시 정리 중 오류 발생: {str(e)}")
