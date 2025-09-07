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
from selvage.src.models.model_provider import ModelProvider
from selvage.src.utils.platform_utils import get_platform_config_dir

# 설정 파일 경로 (플랫폼별 설정 디렉토리 사용)
CONFIG_DIR = get_platform_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.ini"

# 기본 설정 섹션 목록
DEFAULT_SECTIONS = [
    "paths",  # 경로 설정
    "default",  # 기본값 설정
    "debug",  # 디버그 설정
    "language",  # 언어 설정
]


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
        try:
            config.read(CONFIG_FILE)
        except (configparser.Error, UnicodeDecodeError) as e:
            # 설정 파일이 손상된 경우 기본 설정으로 진행
            from selvage.src.utils.base_console import console

            console.warning(
                f"Configuration file is corrupted, using default settings: {e}"
            )
            config = configparser.ConfigParser()

    # 기본 섹션이 없으면 추가
    for section in DEFAULT_SECTIONS:
        if section not in config:
            config[section] = {}

    return config


def save_config(config: configparser.ConfigParser) -> None:
    """설정을 파일에 저장합니다."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)

    # 파일 권한 설정 (Linux/macOS에서만 작동)
    if sys.platform != "win32":
        os.chmod(CONFIG_FILE, 0o600)  # 소유자만 읽기/쓰기 가능


def get_api_key(provider: ModelProvider) -> str:
    """환경변수에서 API 키를 가져옵니다.

    Args:
        provider: ModelProvider enum 인스턴스

    Returns:
        API 키

    Raises:
        APIKeyNotFoundError: API 키가 설정되지 않은 경우
    """
    env_var_name = provider.get_env_var_name()
    api_key = os.getenv(env_var_name)

    if not api_key:
        from selvage.src.utils.base_console import console

        console.error(f"API key is missing: {provider.get_display_name()}")
        console.info("Please set API key as environment variable:")
        console.info(f"  export {env_var_name}=your_api_key")
        raise APIKeyNotFoundError(provider)

    return api_key


def has_api_key(provider: ModelProvider) -> bool:
    """API 키가 설정되어 있는지 확인합니다."""
    return bool(os.getenv(provider.get_env_var_name()))


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

        from selvage.src.utils.base_console import console

        console.success(f"Review log directory has been set to {log_path}.")
        return True
    except Exception as e:
        from selvage.src.utils.base_console import console

        console.error(
            f"Error occurred while setting review log directory: {str(e)}", exception=e
        )
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
        from selvage.src.utils.base_console import console

        console.error(
            f"Error occurred while setting default model: {str(e)}", exception=e
        )
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
        from selvage.src.utils.base_console import console

        console.error(f"Error occurred while setting debug_mode: {str(e)}", exception=e)
        return False


def has_openrouter_api_key() -> bool:
    """OpenRouter API key가 설정되어 있는지 확인합니다.

    Returns:
        bool: OPENROUTER_API_KEY 환경변수 존재 여부
    """
    return bool(os.getenv("OPENROUTER_API_KEY"))


def has_openai_api_key() -> bool:
    """OpenAI API key가 설정되어 있는지 확인합니다.

    Returns:
        bool: OPENAI_API_KEY 환경변수 존재 여부
    """
    return bool(os.getenv("OPENAI_API_KEY"))


def get_default_language() -> str:
    """기본 언어를 반환합니다.

    Returns:
        str: 기본 언어 (기본값: Korean)
    """
    try:
        config = load_config()
        return config["language"].get("default", "Korean")
    except KeyError:
        return "Korean"


def set_default_language(language: str) -> bool:
    """기본 언어를 설정합니다.

    Args:
        language: 설정할 언어

    Returns:
        bool: 성공 여부
    """
    try:
        config = load_config()
        if "language" not in config:
            config["language"] = {}
        config["language"]["default"] = language
        save_config(config)
        return True
    except Exception as e:
        from selvage.src.utils.base_console import console

        console.error(
            f"Error occurred while setting default language: {str(e)}", exception=e
        )
        return False
