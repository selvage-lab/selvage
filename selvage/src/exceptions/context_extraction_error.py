"""
컨텍스트 추출 관련 예외 클래스 정의 모듈입니다.
"""


class ContextExtractionError(Exception):
    """컨텍스트 추출 중 발생하는 일반적인 예외"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnsupportedLanguageError(ContextExtractionError):
    """지원하지 않는 프로그래밍 언어일 때 발생하는 예외"""

    def __init__(self, language: str) -> None:
        self.language = language
        super().__init__(f"Unsupported programming language: {language}")


class TreeSitterError(ContextExtractionError):
    """Tree-sitter 관련 오류가 발생할 때의 예외"""

    def __init__(self, message: str) -> None:
        super().__init__(f"Tree-sitter error: {message}")
