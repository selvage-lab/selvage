"""LLM 게이트웨이 생성을 담당하는 팩토리 클래스"""

from selvage.src.config import has_openai_api_key, has_openrouter_api_key
from selvage.src.llm_gateway import get_model_info
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.models.model_provider import ModelProvider


class GatewayFactory:
    """LLM 게이트웨이 객체를 생성하는 팩토리 클래스"""

    @staticmethod
    def create(model: str) -> BaseGateway:
        """주어진 모델 이름에 맞는 LLM 게이트웨이 객체를 생성합니다.

        OpenRouter First 방식:
        1. BYOK 필수 모델은 직접 원본 provider 게이트웨이 사용
        2. OpenRouter API key가 설정되어 있으면 나머지 모델을 OpenRouter로 처리
        3. 그렇지 않으면 기존 provider별 게이트웨이 사용

        Args:
            model: 사용할 모델 이름

        Returns:
            BaseGateway: LLM 게이트웨이 객체
        """
        model_info = get_model_info(model)

        if model_info.get("requires_byok", False):
            provider = model_info["provider"]
            if provider == ModelProvider.OPENAI:
                if not has_openai_api_key():
                    from selvage.src.exceptions.api_key_not_found_error import (
                        APIKeyNotFoundError,
                    )

                    raise APIKeyNotFoundError(
                        message=f"{model} 모델은 OpenAI API key가 필요합니다. "
                        f"OPENAI_API_KEY 환경변수를 설정하거나 "
                        f"OpenRouter BYOK를 설정하세요: "
                        f"https://openrouter.ai/settings/integrations"
                    )
                from selvage.src.llm_gateway.openai_gateway import OpenAIGateway

                return OpenAIGateway(model_info=model_info)

        # OpenRouter First: API key가 있으면 나머지 모델을 OpenRouter로
        if has_openrouter_api_key():
            from selvage.src.llm_gateway.openrouter_gateway import OpenRouterGateway

            return OpenRouterGateway(model_info=model_info)

        # 기존 로직: provider별 게이트웨이 선택
        provider = model_info["provider"]

        if provider == ModelProvider.OPENAI:
            from selvage.src.llm_gateway.openai_gateway import OpenAIGateway

            return OpenAIGateway(model_info=model_info)
        elif provider == ModelProvider.ANTHROPIC:
            from selvage.src.llm_gateway.claude_gateway import ClaudeGateway

            return ClaudeGateway(model_info=model_info)
        elif provider == ModelProvider.GOOGLE:
            from selvage.src.llm_gateway.google_gateway import GoogleGateway

            return GoogleGateway(model_info=model_info)
        elif provider == ModelProvider.OPENROUTER:
            from selvage.src.llm_gateway.openrouter_gateway import OpenRouterGateway

            return OpenRouterGateway(model_info=model_info)
        else:
            raise ValueError(f"지원하지 않는 provider: {provider}")
