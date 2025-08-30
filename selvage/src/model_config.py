"""
LLM 모델 설정 정보를 로드하고 제공하는 모듈입니다.
"""

import importlib.resources
import threading
from typing import Any, TypedDict

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

import yaml

from selvage.src.exceptions.unsupported_model_error import UnsupportedModelError
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console


class ModelParamsDict(TypedDict, total=False):
    """모델별 파라미터 타입"""

    temperature: float
    reasoning_effort: str
    thinking: dict[str, Any]


class PricingDict(TypedDict):
    """가격 정보 타입"""

    input: float
    output: float
    description: str


class ModelInfoDict(TypedDict):
    """모델 정보 타입"""

    full_name: str
    aliases: list[str]
    description: str
    provider: ModelProvider
    params: ModelParamsDict
    thinking_mode: bool
    pricing: PricingDict
    context_limit: int
    openrouter_name: NotRequired[str]


class ModelConfig:
    """
    LLM 모델 설정 정보를 로드하고 제공하는 유틸리티 클래스입니다.
    YAML 파일에서 설정을 읽어와 관리합니다.
    """

    _config: dict[str, ModelInfoDict] | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        if ModelConfig._config is None:
            with ModelConfig._lock:
                # Double-checked locking pattern
                if ModelConfig._config is None:
                    ModelConfig._load_config_from_yaml()

    @classmethod
    def _load_config_from_yaml(cls) -> None:
        """YAML 파일에서 모델 정보를 로드하여 클래스 변수에 저장합니다."""
        try:
            file_ref = importlib.resources.files("selvage.resources").joinpath(
                "models.yml"
            )
            with importlib.resources.as_file(file_ref) as file_path:
                data = yaml.safe_load(file_path.read_text(encoding="utf-8"))

            # YAML 데이터 유효성 검증
            cls._validate_yaml_data(data)

            # provider 문자열을 enum으로 변환
            models = data["models"]
            for _model_name, model_info in models.items():
                provider_str = model_info["provider"]
                model_info["provider"] = ModelProvider.from_string(provider_str)

            cls._config = models

        except Exception as e:
            console.error(f"모델 설정 파일을 찾을 수 없습니다: {file_ref}", exception=e)
            raise FileNotFoundError(
                f"모델 설정 파일을 찾을 수 없습니다: {file_ref}"
            ) from e

    @classmethod
    def _validate_yaml_data(cls, data: dict[str, Any]) -> None:
        """YAML 데이터의 구조와 내용을 검증합니다.

        Args:
            data: YAML에서 로드된 데이터

        Raises:
            ValueError: YAML 구조가 올바르지 않은 경우
        """
        # 기본 구조 검증
        if not isinstance(data, dict):
            raise ValueError("YAML 데이터가 dictionary 형태가 아닙니다")

        if "models" not in data:
            raise ValueError("YAML에 'models' 키가 없습니다")

        models = data["models"]
        if not isinstance(models, dict):
            raise ValueError("'models' 값이 dictionary 형태가 아닙니다")

        # 각 모델 정보 검증
        required_fields = [
            "full_name",
            "aliases",
            "description",
            "provider",
            "params",
            "thinking_mode",
            "pricing",
            "context_limit",
        ]

        for model_name, model_info in models.items():
            if not isinstance(model_info, dict):
                raise ValueError(
                    f"모델 '{model_name}'의 정보가 dictionary 형태가 아닙니다"
                )

            # 필수 필드 검증
            for field in required_fields:
                if field not in model_info:
                    raise ValueError(
                        f"모델 '{model_name}'에 필수 필드 '{field}'가 없습니다"
                    )

            # provider 값 검증 (YAML에서는 아직 문자열이므로)
            valid_providers = [p.value for p in ModelProvider]
            if model_info["provider"] not in valid_providers:
                raise ValueError(
                    f"모델 '{model_name}'의 provider "
                    f"'{model_info['provider']}'가 유효하지 않습니다. "
                    f"유효한 값: {valid_providers}"
                )

            # pricing 구조 검증
            pricing = model_info["pricing"]
            if not isinstance(pricing, dict) or not all(
                key in pricing for key in ["input", "output", "description"]
            ):
                raise ValueError(
                    f"모델 '{model_name}'의 pricing 정보가 올바르지 않습니다"
                )

    def get_model_info(self, model_name: str) -> ModelInfoDict:
        """모델 이름에 해당하는 전체 정보를 반환합니다.

        Args:
            model_name: 모델 이름 (정식 이름 또는 축약형)

        Returns:
            ModelInfoDict: 모델 정보

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        # 타입 체커를 위한 방어 코드
        if self._config is None:
            raise RuntimeError("모델 설정이 초기화되지 않았습니다")

        # 정식 이름으로 시도
        if model_name in self._config:
            return self._config[model_name]

        # 축약형으로 시도
        for model_info in self._config.values():
            if model_name in model_info["aliases"]:
                return model_info

        raise UnsupportedModelError(model_name)

    def get_supported_models(self) -> list[str]:
        """지원하는 모든 모델 이름 목록을 반환합니다.

        Returns:
            list[str]: 지원하는 모델 이름 목록 (정식 이름 + 별칭)
        """
        # 타입 체커를 위한 방어 코드
        if self._config is None:
            raise RuntimeError("모델 설정이 초기화되지 않았습니다")

        alias_names = [
            alias
            for model_info in self._config.values()
            for alias in model_info["aliases"]
        ]
        all_names = list(self._config.keys()) + alias_names
        return list(set(all_names))

    def get_model_pricing(self, model_name: str) -> PricingDict:
        """모델의 가격 정보를 반환합니다.

        Args:
            model_name: 모델 이름

        Returns:
            PricingDict: 가격 정보

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        model_info = self.get_model_info(model_name)
        return model_info["pricing"]

    def get_model_context_limit(self, model_name: str) -> int:
        """모델의 컨텍스트 제한을 반환합니다.

        Args:
            model_name: 모델 이름

        Returns:
            int: 컨텍스트 제한 (토큰 수)

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        model_info = self.get_model_info(model_name)
        return model_info["context_limit"]

    def get_model_provider(self, model_name: str) -> ModelProvider:
        """모델의 제공자를 반환합니다.

        Args:
            model_name: 모델 이름

        Returns:
            ModelProvider: 모델 제공자

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        model_info = self.get_model_info(model_name)
        return model_info["provider"]

    def get_model_params(self, model_name: str) -> ModelParamsDict:
        """모델의 파라미터를 반환합니다.

        Args:
            model_name: 모델 이름

        Returns:
            ModelParamsDict: 모델 파라미터

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        model_info = self.get_model_info(model_name)
        return model_info["params"]

    def is_thinking_mode_model(self, model_name: str) -> bool:
        """모델이 thinking mode를 지원하는지 여부를 반환합니다.

        Args:
            model_name: 모델 이름

        Returns:
            bool: thinking mode 지원 여부

        Raises:
            UnsupportedModelError: 지원되지 않는 모델인 경우
        """
        model_info = self.get_model_info(model_name)
        return model_info["thinking_mode"]

    def get_all_models_config(self) -> dict[str, ModelInfoDict]:
        """모든 모델의 설정 정보를 반환합니다.

        Returns:
            dict[str, ModelInfoDict]: 모든 모델의 설정 정보 사본

        Raises:
            RuntimeError: 모델 설정이 초기화되지 않은 경우
        """
        # 타입 체커를 위한 방어 코드
        if self._config is None:
            raise RuntimeError("모델 설정이 초기화되지 않았습니다")

        # 내부 _config의 사본을 반환하여 외부에서 수정할 수 없도록 보호
        return self._config.copy()


# 편의를 위한 전역 함수들 (하위 호환성 유지)
def get_model_info(model_name: str) -> ModelInfoDict:
    """모델 이름에 해당하는 정보를 반환합니다."""
    config = ModelConfig()
    return config.get_model_info(model_name)


def get_supported_models() -> list[str]:
    """지원하는 모든 모델 목록을 반환합니다."""
    config = ModelConfig()
    return config.get_supported_models()


def get_model_pricing(model_name: str) -> PricingDict:
    """모델의 가격 정보를 반환합니다."""
    config = ModelConfig()
    return config.get_model_pricing(model_name)


def get_model_context_limit(model_name: str) -> int:
    """모델의 컨텍스트 제한을 반환합니다."""
    config = ModelConfig()
    return config.get_model_context_limit(model_name)
