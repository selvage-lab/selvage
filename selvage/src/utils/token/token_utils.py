import typing
from typing import TypedDict

import tiktoken
from google import genai

from selvage.src.exceptions.token_count_error import TokenCountError
from selvage.src.model_config import get_model_context_limit
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console
from selvage.src.utils.prompts.models.review_prompt_with_file_content import (
    ReviewPromptWithFileContent,
)


# 모델 가격 정보 타입 정의
class ModelPricing(TypedDict):
    input: float
    output: float


class TokenUtils:
    """토큰 계산 및 비용 추정 유틸리티 클래스"""

    @staticmethod
    def count_tokens(
        review_prompt: ReviewPromptWithFileContent, model: str = "gpt-4o"
    ) -> int:
        """텍스트의 토큰 수를 계산합니다.

        Args:
            text: 토큰 수를 계산할 텍스트
            model: 사용할 모델 이름

        Returns:
            int: 토큰 수
        """
        # Claude 모델인 경우 처리
        if "claude" in model.lower():
            return TokenUtils._count_tokens_claude(review_prompt, model)

        if "gemini" in model.lower():
            try:
                # API 키 가져오기 (기존 메커니즘 사용) - 지연 임포트
                from selvage.src.config import get_api_key

                api_key = get_api_key(ModelProvider.GOOGLE)

                # Client 객체 생성
                client = genai.Client(api_key=api_key)

                # 사용 가능한 모델명으로 매핑
                model_name = model.lower()
                # 토큰 수 계산 (최신 API 사용)
                text = review_prompt.to_combined_text()
                response = client.models.count_tokens(model=model_name, contents=text)
                # total_tokens가 None일 경우를 대비해 기본값 0을 제공
                return (
                    response.total_tokens
                    if response
                    and hasattr(response, "total_tokens")
                    and response.total_tokens is not None
                    else 0
                )
            except Exception as e:
                console.error(f"Gemini 토큰 계산 중 오류 발생: {e}", exception=e)
                raise TokenCountError(model, str(e), e) from e

        # 새로 추가된 OpenRouter 모델들에 대한 처리
        if any(
            model_name in model.lower()
            for model_name in ["kimi-k2", "deepseek-v3-0324", "deepseek-r1-0528"]
        ):
            # OpenRouter 모델은 토큰 계산 API가 없으므로 0 반환
            console.info(
                f"OpenRouter 모델 {model}에 대해서는 사전 토큰 계산을 건너뜁니다."
            )
            return 0

        # OpenAI 모델인 경우 tiktoken 사용
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # 모델이 tiktoken에 없는 경우 기본 인코딩 사용
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                console.error(f"OpenAI 토큰 계산 중 오류 발생: {e}", exception=e)
                raise TokenCountError(model, f"Tiktoken 인코딩 오류: {e}", e) from e

        text = review_prompt.to_combined_text()
        try:
            return len(encoding.encode(text))
        except Exception as e:
            console.error(f"OpenAI 토큰 인코딩 중 오류 발생: {e}", exception=e)
            raise TokenCountError(model, f"텍스트 인코딩 오류: {e}", e) from e

    @staticmethod
    def get_model_context_limit(model: str) -> int:
        """모델의 컨텍스트 제한을 반환합니다.

        Args:
            model: 모델 이름

        Returns:
            int: 컨텍스트 제한 (토큰 수)
        """
        return get_model_context_limit(model)

    @staticmethod
    def _count_tokens_claude(
        review_prompt: ReviewPromptWithFileContent, model: str
    ) -> int:
        """Claude 모델의 토큰 수를 계산합니다.
        OpenRouter 사용 시에도 정확한 계산을 위해 Anthropic API를 사용합니다.

        Args:
            review_prompt: 리뷰 프롬프트
            model: 모델 이름

        Returns:
            int: 토큰 수
        """

        return TokenUtils._count_tokens_claude_anthropic(review_prompt, model)

    @staticmethod
    def _count_tokens_claude_anthropic(
        review_prompt: ReviewPromptWithFileContent, model: str
    ) -> int:
        """Anthropic API를 직접 사용하여 Claude 토큰 수를 계산합니다.

        Args:
            review_prompt: 리뷰 프롬프트
            model: 모델 이름

        Returns:
            int: 토큰 수
        """
        try:
            import anthropic

            from selvage.src.config import get_api_key

            api_key = get_api_key(ModelProvider.ANTHROPIC)
            client = anthropic.Anthropic(api_key=api_key)

            # 메시지 목록에서 시스템 메시지 분리
            messages = review_prompt.to_messages()
            system_message = None
            user_messages = []

            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg.get("content", "")
                else:
                    user_messages.append(msg)

            # Anthropic API 호출 시 시스템 메시지는 별도 파라미터로 전달
            kwargs = {
                "model": model,
                "messages": typing.cast(
                    typing.Iterable[anthropic.types.MessageParam],
                    user_messages,
                ),
            }

            # system 파라미터가 None이 아닌 경우에만 추가
            if system_message is not None:
                kwargs["system"] = system_message

            response = client.messages.count_tokens(**kwargs)

            # 응답 처리 - 예상 응답 형식:
            # {"content_tokens": 토큰수} 또는 유사한 구조
            response_dict = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else vars(response)
            )

            # 토큰 수를 포함할 수 있는 필드명들
            token_field_names = [
                "token_count",
                "content_tokens",
                "input_tokens",
                "num_tokens",
                "tokens",
            ]

            # 응답에서 토큰 수를 추출
            for field in token_field_names:
                if field in response_dict:
                    return response_dict[field]

            # 로그 기록 및 예외 처리
            console.warning(f"응답에서 토큰 수를 찾을 수 없습니다: {response_dict}")
            return 0
        except Exception as e:
            console.error(
                f"Claude (Anthropic) 토큰 계산 중 오류 발생: {e}", exception=e
            )
            raise TokenCountError(model, str(e), e) from e

    @staticmethod
    def _count_tokens_claude_with_anthropic_for_openrouter(
        review_prompt: ReviewPromptWithFileContent, model: str
    ) -> int:
        """OpenRouter 사용 시에도 정확한 토큰 계산을 위해 Anthropic API를 사용합니다.

        Args:
            review_prompt: 리뷰 프롬프트
            model: 모델 이름

        Returns:
            int: 토큰 수
        """
        from selvage.src.config import get_api_key

        try:
            # Anthropic API 키 확인
            api_key = get_api_key(ModelProvider.ANTHROPIC)
            if not api_key:
                console.warning(
                    "정확한 토큰 계산을 위해 ANTHROPIC_API_KEY가 필요합니다."
                )
                console.info("환경 변수 설정 방법:")
                console.info("  export ANTHROPIC_API_KEY='your_anthropic_api_key'")
                raise TokenCountError(
                    model,
                    "ANTHROPIC_API_KEY가 설정되지 않았습니다.",
                )

            # Anthropic API를 사용하여 정확한 토큰 계산
            return TokenUtils._count_tokens_claude_anthropic(review_prompt, model)

        except Exception as e:
            console.warning(f"Anthropic API를 통한 토큰 계산 실패: {e}")
            return 0
