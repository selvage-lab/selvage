"""ModelChoice: CLI에서 모델 선택을 위한 커스텀 Choice 클래스."""

from typing import TYPE_CHECKING

import click

from selvage.src.models.model_provider import ModelProvider

if TYPE_CHECKING:
    pass


class ModelChoice(click.Choice):
    """모델 선택을 위한 커스텀 Choice 클래스"""

    def __init__(self) -> None:
        # 런타임에 임포트하여 순환 임포트 방지
        from selvage.src.model_config import get_supported_models

        self.supported_models = get_supported_models()
        super().__init__(self.supported_models, case_sensitive=True)

    def get_metavar(self, param: click.Parameter) -> str:
        """메타변수 표시 방식을 커스터마이징합니다."""
        return "[MODEL]"

    def convert(self, value, param, ctx):
        """값 변환 및 유효성 검사를 수행하면서 커스텀 에러 메시지를 제공합니다."""
        # 기본 변환 시도
        try:
            return super().convert(value, param, ctx)
        except click.BadParameter:
            # 커스텀 에러 메시지 생성
            help_text = self.build_help_text()
            self.fail(
                f"'{value}'는 지원되지 않는 모델입니다.\n\n{help_text}",
                param,
                ctx,
            )

    @staticmethod
    def build_help_text() -> str:
        """모델 선택 옵션의 help 텍스트를 생성합니다."""
        # 런타임에 임포트하여 순환 임포트 방지
        from selvage.src.model_config import ModelConfig

        model_config = ModelConfig()
        if model_config._config is None:
            return "사용 가능한 AI 모델 목록"

        # 프로바이더별로 그룹화
        providers = {}
        for key, info in model_config._config.items():
            provider = info["provider"]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append((key, info))

        provider_info = []
        for provider in [
            ModelProvider.OPENAI,
            ModelProvider.ANTHROPIC,
            ModelProvider.GOOGLE,
        ]:
            if provider not in providers:
                continue

            provider_name = provider.get_display_name()
            models_list = []

            for key, info in providers[provider]:
                aliases = info.get("aliases", [])
                if aliases:
                    # 가장 짧은 별칭만 표시
                    shortest_alias = min(aliases, key=len)
                    models_list.append(f"{shortest_alias}({key})")
                else:
                    models_list.append(key)

            models_str = ", ".join(models_list)
            provider_info.append(f"[{provider_name}] {models_str}")

        all_providers = " | ".join(provider_info)
        return f"사용 가능한 AI 모델 목록 - {all_providers}"
