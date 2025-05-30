"""시스템 프롬프트 데이터 클래스 모듈"""

from dataclasses import dataclass


@dataclass
class SystemPrompt:
    """시스템 프롬프트 데이터 클래스"""

    role: str
    content: str
