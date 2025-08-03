"""파일 컨텍스트 정보를 담는 데이터 클래스 모듈"""

from dataclasses import dataclass
from enum import Enum


class ContextType(Enum):
    """컨텍스트 추출 방식을 나타내는 열거형"""

    FULL_CONTEXT = "full_context"
    SMART_CONTEXT = "smart_context"
    FALLBACK_CONTEXT = "fallback_context"


@dataclass
class FileContextInfo:
    """파일 컨텍스트 정보를 담는 데이터 클래스"""

    context_type: ContextType
    context: str
    description: str

    @classmethod
    def create_full_context(cls, file_content: str) -> "FileContextInfo":
        """전체 파일 내용을 포함하는 FileContextInfo를 생성한다.

        Args:
            file_content: 전체 파일 내용

        Returns:
            FileContextInfo 인스턴스
        """
        return cls(
            context_type=ContextType.FULL_CONTEXT,
            context=file_content,
            description="Complete file content",
        )

    @classmethod
    def create_smart_context(cls, context_blocks: list[str]) -> "FileContextInfo":
        """tree-sitter 기반 스마트 컨텍스트를 포함하는 FileContextInfo를 생성한다.

        Args:
            context_blocks: 추출된 컨텍스트 블록들

        Returns:
            FileContextInfo 인스턴스
        """
        return cls(
            context_type=ContextType.SMART_CONTEXT,
            context=get_combined_content(context_blocks),
            description="AST-based context extraction",
        )

    @classmethod
    def create_fallback_context(cls, context_blocks: list[str]) -> "FileContextInfo":
        """fallback 방식 컨텍스트를 포함하는 FileContextInfo를 생성한다.

        Args:
            context_blocks: 추출된 컨텍스트 블록들

        Returns:
            FileContextInfo 인스턴스
        """
        return cls(
            context_type=ContextType.FALLBACK_CONTEXT,
            context=get_combined_content(context_blocks),
            description="Text-based context extraction (AST fallback)",
        )

    def to_dict(self) -> dict[str, str]:
        """FileContextInfo를 JSON 직렬화 가능한 딕셔너리로 변환한다.

        Returns:
            dict[str, str]: JSON 직렬화 가능한 딕셔너리
        """
        return {
            "context_type": self.context_type.value,
            "context": self.context,
            "description": self.description,
        }


def get_combined_content(context_blocks: list[str]) -> str:
    """모든 추출된 블록들을 하나의 문자열로 결합한다.

    Returns:
        결합된 컨텍스트 내용
    """
    return "\n".join(context_blocks)
