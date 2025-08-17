"""Multiturn 관련 데이터 모델"""

from dataclasses import dataclass

from selvage.src.models.error_response import ErrorResponse


@dataclass
class TokenInfo:
    """토큰 정보를 담는 데이터 클래스"""

    actual_tokens: int | None
    max_tokens: int | None

    @classmethod
    def from_error_response(cls, error_response: ErrorResponse) -> "TokenInfo":
        """ErrorResponse에서 토큰 정보를 추출하여 TokenInfo 생성

        Args:
            error_response: LLM API 에러 응답

        Returns:
            TokenInfo: 토큰 정보 객체
        """
        actual_tokens = error_response.raw_error.get("actual_tokens")
        max_tokens = error_response.raw_error.get("max_tokens")

        return cls(
            actual_tokens=int(actual_tokens) if actual_tokens else None,
            max_tokens=int(max_tokens) if max_tokens else None,
        )

    @classmethod
    def empty(cls) -> "TokenInfo":
        """빈 토큰 정보 생성 (토큰 정보가 없는 경우)

        Returns:
            TokenInfo: 빈 토큰 정보 객체
        """
        return cls(actual_tokens=None, max_tokens=None)
