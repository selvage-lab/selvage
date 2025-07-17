"""Claude 제공자 enum 정의 모듈"""

from enum import Enum

from selvage.src.exceptions.unsupported_provider_error import UnsupportedProviderError


class ClaudeProvider(Enum):
    """Claude 모델 제공자 enum"""

    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"

    @classmethod
    def from_string(cls, provider_str: str) -> "ClaudeProvider":
        """문자열을 ClaudeProvider enum으로 변환합니다.

        Args:
            provider_str: provider 문자열

        Returns:
            ClaudeProvider: 해당하는 enum 값

        Raises:
            UnsupportedProviderError: 지원하지 않는 provider인 경우
        """
        for provider in cls:
            if provider.value == provider_str.lower():
                return provider

        valid_providers = [p.value for p in cls]
        raise UnsupportedProviderError(
            f"지원하지 않는 Claude provider '{provider_str}'. 유효한 값: {valid_providers}"
        )

    def get_display_name(self) -> str:
        """사용자에게 표시할 provider 이름을 반환합니다."""
        display_names = {
            ClaudeProvider.ANTHROPIC: "Anthropic",
            ClaudeProvider.OPENROUTER: "OpenRouter",
        }
        return display_names[self]

    def get_env_var_name(self) -> str:
        """해당 provider의 환경 변수 이름을 반환합니다."""
        env_vars = {
            ClaudeProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ClaudeProvider.OPENROUTER: "OPENROUTER_API_KEY",
        }
        return env_vars[self]
