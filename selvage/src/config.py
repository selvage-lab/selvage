"""
설정 관리 모듈

이 모듈은 API 키 및 기타 설정을 관리합니다.
환경변수를 우선적으로 사용하며, 설정 파일은 하위 호환성을 위해 유지됩니다.
"""

import configparser
import os
import sys
from pathlib import Path

from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
from selvage.src.exceptions.invalid_api_key_error import InvalidAPIKeyError
from selvage.src.exceptions.unsupported_provider_error import UnsupportedProviderError
from selvage.src.models.claude_provider import ClaudeProvider
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.base_console import console
from selvage.src.utils.platform_utils import get_platform_config_dir

# 설정 파일 경로 (플랫폼별 설정 디렉토리 사용)
CONFIG_DIR = get_platform_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.ini"


def ensure_config_dir() -> None:
    """설정 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
    CONFIG_DIR.mkdir(exist_ok=True, parents=True)


def load_config() -> configparser.ConfigParser:
    """설정 파일을 로드합니다. 파일이 없으면 기본 설정을 반환합니다.

    하위 호환성을 위해 기존 macOS 경로도 확인합니다.
    """
    config = configparser.ConfigParser()

    # 플랫폼별 설정 파일 확인
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)

    # 기본 섹션이 없으면 추가
    if "credentials" not in config:
        config["credentials"] = {}

    if "paths" not in config:
        config["paths"] = {}

    if "default" not in config:
        config["default"] = {}

    if "debug" not in config:
        config["debug"] = {}

    return config


def save_config(config: configparser.ConfigParser) -> None:
    """설정을 파일에 저장합니다."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

    # 파일 권한 설정 (Linux/macOS에서만 작동)
    if sys.platform != "win32":
        os.chmod(CONFIG_FILE, 0o600)  # 소유자만 읽기/쓰기 가능


def _validate_api_key(api_key: str, provider: ModelProvider) -> None:
    """API 키의 유효성을 검증합니다.

    Args:
        api_key: 검증할 API 키
        provider: API 제공자 이름

    Raises:
        InvalidAPIKeyError: API 키가 빈 값이거나 너무 짧은 경우
    """
    if not api_key or api_key.strip() == "":
        console.error(f"{provider.get_display_name()} API 키가 비어 있습니다.")
        raise InvalidAPIKeyError(provider, "API 키가 비어 있습니다")

    if len(api_key) < 8:
        console.error(
            f"{provider.get_display_name()} API 키가 너무 짧습니다. 최소 8자 이상이어야 합니다."
        )
        raise InvalidAPIKeyError(
            provider, "API 키가 너무 짧습니다. 최소 8자 이상이어야 합니다"
        )


def get_api_key(provider: ModelProvider) -> str:
    """API 키를 가져옵니다.

    환경변수를 우선적으로 확인하고, 없으면 설정 파일에서 찾습니다.

    Args:
        provider: ModelProvider enum 인스턴스

    Returns:
        API 키

    Raises:
        APIKeyNotFoundError: API 키가 설정되지 않은 경우
        InvalidAPIKeyError: API 키가 유효하지 않은 경우
    """
    # 1. 환경변수에서 확인
    try:
        env_var_name = provider.get_env_var_name()
        api_key = os.getenv(env_var_name)
        if api_key:
            # API 키를 환경변수에서 발견했습니다 (디버그 로그 제거)
            _validate_api_key(api_key, provider)
            return api_key
    except ValueError as e:
        console.error(str(e))
        raise InvalidAPIKeyError(provider, "API 키가 없습니다") from e

    # 2. 설정 파일에서 확인 (하위 호환성)
    config = load_config()
    if provider.value in config["credentials"]:
        api_key = config["credentials"][provider.value]
        # API 키를 설정 파일에서 발견했습니다 (디버그 로그 제거)
        _validate_api_key(api_key, provider)
        return api_key

    console.error(f"API 키가 없습니다: {provider}")
    console.info("다음 중 하나의 방법으로 API 키를 설정하세요:")
    console.info(f"  1. 환경변수: export {env_var_name}=your_api_key")
    console.info(f"  2. CLI 명령어: selvage --set-{provider.value}-key your_api_key")
    raise APIKeyNotFoundError(provider)


def set_api_key(api_key: str, provider: ModelProvider) -> bool:
    """API 키를 설정 파일에 저장합니다.

    Args:
        api_key: 저장할 API 키
        provider: API 제공자 ('openai', 'anthropic', 'google')

    Returns:
        bool: 성공 여부
    """
    try:
        # Provider 유효성 검증 - get_env_var_name이 ValueError를 발생시킴
        provider.get_env_var_name()

        # API 키 유효성 검증
        _validate_api_key(api_key, provider)

        config = load_config()
        config["credentials"][provider.value] = api_key
        save_config(config)

        console.success(
            f"{provider.get_display_name()} API 키가 설정 파일에 저장되었습니다."
        )
        return True
    except (InvalidAPIKeyError, ValueError) as e:
        console.error(str(e))
        return False
    except Exception as e:
        console.error(f"API 키 저장 중 오류 발생: {str(e)}", exception=e)
        return False


def get_default_review_log_dir() -> Path:
    """리뷰 로그 저장 기본 디렉토리를 반환합니다."""
    config = load_config()

    # 설정 파일에 지정된 경우
    if "review_log_dir" in config["paths"]:
        path = config["paths"]["review_log_dir"]
        return Path(os.path.expanduser(path))

    # 기본 위치 (플랫폼별 설정 디렉토리 사용)
    return CONFIG_DIR / "review_log"


def set_default_review_log_dir(log_dir: str) -> bool:
    """리뷰 로그 디렉토리를 설정합니다.

    Args:
        log_dir: 설정할 로그 디렉토리 경로

    Returns:
        bool: 성공 여부
    """
    try:
        # 경로 유효성 검증
        expanded_path = os.path.expanduser(log_dir)
        log_path = Path(expanded_path)

        # 절대 경로로 변환
        if not log_path.is_absolute():
            log_path = log_path.resolve()

        config = load_config()
        config["paths"]["review_log_dir"] = str(log_path)
        save_config(config)

        console.success(f"리뷰 로그 디렉토리가 {log_path}로 설정되었습니다.")
        return True
    except Exception as e:
        console.error(f"리뷰 로그 디렉토리 설정 중 오류 발생: {str(e)}", exception=e)
        return False


def get_default_model() -> str | None:
    """기본 모델을 반환합니다."""
    try:
        config = load_config()
        return config["model"]["default_model"]
    except KeyError:
        return None


def set_default_model(model_name: str) -> bool:
    """기본 모델 설정을 처리합니다."""
    try:
        config = load_config()
        if "model" not in config:
            config["model"] = {}
        config["model"]["default_model"] = model_name
        save_config(config)
        return True
    except Exception as e:
        console.error(f"기본 모델 설정 중 오류 발생: {str(e)}", exception=e)
        return False


def get_default_diff_only() -> bool:
    """diff-only 기본 설정값을 반환합니다."""
    try:
        config = load_config()
        return config["review"].getboolean("diff_only", fallback=False)
    except KeyError:
        return False


def set_default_diff_only(diff_only: bool) -> bool:
    """diff-only 기본 설정값을 설정합니다."""
    try:
        config = load_config()
        if "review" not in config:
            config["review"] = {}
        config["review"]["diff_only"] = str(diff_only).lower()
        save_config(config)
        return True
    except Exception as e:
        console.error(f"diff-only 설정 중 오류 발생: {str(e)}", exception=e)
        return False


def get_default_debug_mode() -> bool:
    """debug_mode 기본 설정값을 반환합니다."""
    try:
        config = load_config()
        return config["debug"].getboolean("debug_mode", fallback=False)
    except KeyError:
        return False


def set_default_debug_mode(debug_mode: bool) -> bool:
    """debug_mode 기본 설정값을 설정합니다."""
    try:
        config = load_config()
        if "debug" not in config:
            config["debug"] = {}
        config["debug"]["debug_mode"] = str(debug_mode).lower()
        save_config(config)
        return True
    except Exception as e:
        console.error(f"debug_mode 설정 중 오류 발생: {str(e)}", exception=e)
        return False


def get_claude_provider() -> ClaudeProvider:
    """Claude 제공자 설정을 반환합니다."""
    try:
        config = load_config()
        if "claude" in config and "provider" in config["claude"]:
            provider_str = config["claude"]["provider"]
        else:
            provider_str = "anthropic"  # 기본값
        return ClaudeProvider.from_string(provider_str)
    except (KeyError, ValueError, UnsupportedProviderError):
        # 설정이 없거나 잘못된 경우 기본값 반환
        return ClaudeProvider.ANTHROPIC


def set_claude_provider(provider: ClaudeProvider) -> bool:
    """Claude 제공자를 설정합니다.

    Args:
        provider: 설정할 Claude 제공자

    Returns:
        bool: 성공 여부
    """
    try:
        config = load_config()
        if "claude" not in config:
            config["claude"] = {}
        config["claude"]["provider"] = provider.value
        save_config(config)
        console.success(
            f"Claude 제공자가 {provider.get_display_name()}로 설정되었습니다."
        )
        return True
    except Exception as e:
        console.error(f"Claude 제공자 설정 중 오류 발생: {str(e)}", exception=e)
        return False
