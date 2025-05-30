"""ReviewStatus: 리뷰 상태를 나타내는 열거형 클래스를 포함한 모듈."""

from enum import Enum


class ReviewStatus(Enum):
    """리뷰 상태를 나타내는 열거형 클래스."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"