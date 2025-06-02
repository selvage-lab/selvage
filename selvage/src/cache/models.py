"""캐시 관련 데이터 모델"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from selvage.src.utils.token.models import ReviewResponse, EstimatedCost


class CacheEntry(BaseModel):
    """캐시 엔트리 모델"""
    
    cache_key: str
    created_at: datetime
    expires_at: datetime
    request_info: dict[str, Any]
    review_response: ReviewResponse
    estimated_cost: EstimatedCost | None = None
    log_id: str | None = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheKeyInfo(BaseModel):
    """캐시 키 생성에 사용되는 정보"""
    
    diff_content: str
    model: str
    use_full_context: bool
