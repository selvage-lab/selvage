"""기본 콘솔 출력 및 로깅을 위한 모듈."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.status import Status

from selvage.src.utils.logging import get_logger


class BaseConsole:
    """기본 콘솔 출력 및 로깅을 관리하는 클래스."""

    def __init__(self) -> None:
        """콘솔 인스턴스를 초기화합니다."""
        self.console = Console()
        self.logger = get_logger(__name__)

    def success(self, message: str) -> None:
        """성공 메시지를 출력합니다."""
        self.console.print(message, style="bold green")
        self.logger.info(f"SUCCESS: {message}")

    def info(self, message: str) -> None:
        """정보 메시지를 출력합니다."""
        self.console.print(message, style="bold blue")
        self.logger.info(f"INFO: {message}")

    def log_info(self, message: str) -> None:
        """정보 메시지를 로그 파일에만 기록합니다 (터미널 출력 없음)."""
        self.logger.info(f"INFO: {message}")

    def warning(self, message: str) -> None:
        """경고 메시지를 출력합니다."""
        self.console.print(message, style="bold yellow")
        self.logger.warning(f"WARNING: {message}")

    def error(self, message: str, exception: Exception | None = None) -> None:
        """오류 메시지를 출력합니다.

        Args:
            message: 오류 메시지
            exception: 예외 객체 (있을 경우 상세한 로그 정보를 저장)
        """
        self.console.print(message, style="bold red")
        if exception:
            self.logger.error(f"ERROR: {message}", exc_info=True)
        else:
            self.logger.error(f"ERROR: {message}")

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Rich 콘솔의 print 메서드를 래핑합니다."""
        self.console.print(*args, **kwargs)

    @contextmanager
    def status(self, message: str) -> Generator[Status, None, None]:
        """진행 상황을 스피너와 함께 표시합니다."""
        with self.console.status(message, spinner="dots") as status:
            yield status


# 전역 콘솔 인스턴스 (기본 기능만)
console = BaseConsole()
