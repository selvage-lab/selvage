"""데코레이터가 포함된 샘플 클래스 - tree-sitter 파싱 테스트에 사용됩니다."""

from dataclasses import dataclass, field
from functools import wraps
from typing import ClassVar


def log_calls(func):
    """함수 호출을 로깅하는 데코레이터"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper


@dataclass
class UserInfo:
    """사용자 정보를 담는 데이터클래스"""

    name: str
    age: int
    email: str = field(default="")
    active: bool = field(default=True)

    def get_display_name(self) -> str:
        """표시용 이름 반환"""
        return f"{self.name} ({self.age})"


@dataclass
class ConfigSettings:
    """설정 정보를 담는 데이터클래스"""

    api_key: str
    timeout: int = 30
    debug_mode: bool = False
    max_retries: int = 3

    @property
    def is_debug_enabled(self) -> bool:
        """디버그 모드 활성화 여부"""
        return self.debug_mode

    @staticmethod
    def create_default() -> "ConfigSettings":
        """기본 설정 생성"""
        return ConfigSettings(api_key="default_key")


class DatabaseManager:
    """데이터베이스 관리 클래스"""

    _instance: ClassVar["DatabaseManager"] = None

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @log_calls
    def connect(self, connection_string: str) -> bool:
        """데이터베이스 연결"""
        print(f"Connecting to: {connection_string}")
        return True

    @log_calls
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return True


@log_calls
def process_user_data(user_info: UserInfo) -> dict:
    """사용자 데이터 처리 함수"""
    return {
        "name": user_info.name,
        "age": user_info.age,
        "display": user_info.get_display_name(),
    }


# 모듈 레벨 상수
DEFAULT_CONFIG = ConfigSettings(api_key="test_key", debug_mode=True)
