"""LLM 게이트웨이 생성을 담당하는 팩토리 클래스"""

from selvage.src.llm_gateway import get_model_info
from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.models.model_provider import ModelProvider


class GatewayFactory:
    """LLM 게이트웨이 객체를 생성하는 팩토리 클래스"""

    @staticmethod
    def create(model: str) -> BaseGateway:
        """주어진 모델 이름에 맞는 LLM 게이트웨이 객체를 생성합니다.

        Args:
            model: 사용할 모델 이름

        Returns:
            OpenAIGateway | ClaudeGateway: LLM 게이트웨이 객체
        """
        model_info = get_model_info(model)

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
        else:
            raise ValueError(f"지원하지 않는 provider: {provider}")
