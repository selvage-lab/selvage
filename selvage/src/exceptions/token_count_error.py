"""토큰 계산 관련 예외 클래스 모듈"""


class TokenCountError(Exception):
    """토큰 계산 중 발생하는 에러를 처리하는 예외 클래스.

    Args:
        model: 토큰 계산 중 오류가 발생한 모델명
        message: 에러 메시지
        original_error: 원래 발생한 예외 객체
    """

    def __init__(
        self, model: str, message: str, original_error: Exception | None = None
    ):
        self.model = model
        self.original_error = original_error
        super().__init__(f"[{model}] 토큰 계산 중 오류 발생: {message}")
