"""로깅 설정 관리 모듈.

이 모듈은 애플리케이션의 로깅 설정을 구성하고 초기화하는 기능을 제공합니다.
다양한 로그 레벨, 포맷, 핸들러를 설정하고 외부 로깅 서비스와의 통합을 관리합니다.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from selvage.src.utils.platform_utils import get_platform_config_dir

# 로그 레벨 상수
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

# 로그 포맷
DETAILED_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)

# 로거 캐시
_loggers = {}


def get_default_log_dir() -> Path:
    """기본 로그 디렉토리를 반환합니다.

    Returns:
        Path: 플랫폼별 기본 로그 디렉토리 경로
    """
    return get_platform_config_dir() / "logs"


def should_enable_console_logging() -> bool:
    """설정을 기반으로 콘솔 로깅 활성화 여부를 결정합니다.

    Returns:
        bool: 콘솔 로깅 활성화 여부
    """
    try:
        from selvage.src.config import get_default_debug_mode

        return get_default_debug_mode()
    except ImportError:
        # 순환 임포트 방지를 위한 fallback
        return False


class TimedSizeRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """날짜별 로테이션과 크기별 로테이션을 동시에 지원하는 핸들러.

    이 핸들러는 TimedRotatingFileHandler를 상속받아 크기 기반 로테이션 기능을 추가합니다.
    """

    def __init__(
        self,
        filename,
        when="midnight",
        interval=1,
        backupCount=0,
        maxBytes=0,
        *args,
        **kwargs,
    ):
        """핸들러를 초기화합니다.

        Args:
            filename: 로그 파일 경로
            when: 시간 기반 로테이션 조건 ('midnight', 'H', 'D' 등)
            interval: 로테이션 간격
            backupCount: 보관할 백업 파일 수
            maxBytes: 파일 최대 크기 (바이트 단위, 0이면 크기 제한 없음)
        """
        super().__init__(filename, when, interval, backupCount, *args, **kwargs)
        self.maxBytes = maxBytes

    def shouldRollover(self, record):
        """로테이션이 필요한지 확인합니다.

        시간 기반 로테이션 조건과 크기 기반 로테이션 조건을 모두 확인합니다.

        Args:
            record: 로그 레코드

        Returns:
            bool: 로테이션 필요 여부
        """
        # 시간 기반 로테이션 확인
        if super().shouldRollover(record):
            return True

        # 크기 기반 로테이션 확인
        if self.maxBytes > 0 and self.stream:
            self.stream.seek(0, 2)  # 파일 끝으로 이동
            if self.stream.tell() >= self.maxBytes:
                return True

        return False


def setup_logging(
    level: int = LOG_LEVEL_DEBUG,
    log_format: str = DETAILED_LOG_FORMAT,
    log_dir: Optional[Path] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 30,  # 30일 분량의 로그 보관
    rotation_interval: int = 1,
) -> None:
    """애플리케이션의 로깅 시스템을 설정합니다.

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 로그 메시지 형식
        log_to_file: 파일에 로그 저장 여부
        log_dir: 로그 파일이 저장될 디렉토리 경로 (기본값: 플랫폼별 설정 디렉토리)
        max_file_size_mb: 로그 파일 최대 크기 (MB)
        backup_count: 보관할 로그 파일 백업 수
        rotation_when: 시간 기반 로테이션 조건 ('midnight', 'H', 'D' 등)
        rotation_interval: 로테이션 간격
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 로그 포맷 설정
    formatter = logging.Formatter(log_format)

    # 콘솔 로깅 설정 (디버그 모드일 때만)
    log_to_console = should_enable_console_logging()

    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 파일 로깅 설정 (항상 활성화)
    if log_dir is None:
        log_dir = get_default_log_dir()

    # 로그 디렉토리 생성
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "selvage.log"

    # 날짜별 + 크기별 로테이션 핸들러 사용
    file_handler = TimedSizeRotatingFileHandler(
        log_file,
        when="midnight",
        interval=rotation_interval,
        backupCount=backup_count,
        maxBytes=max_file_size_mb * 1024 * 1024,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """지정된 이름의 로거를 반환합니다.

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
        level: 로거의 레벨 (지정하지 않으면 상위 로거의 레벨 상속)

    Returns:
        구성된 로거 인스턴스
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)

    # 로거 캐싱
    _loggers[name] = logger
    return logger
