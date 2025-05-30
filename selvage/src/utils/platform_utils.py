"""플랫폼별 유틸리티 함수들.

이 모듈은 플랫폼에 따른 설정 디렉토리, 경로 등을 처리하는 함수들을 제공합니다.
"""

import os
import platform
from pathlib import Path


def get_platform_config_dir() -> Path:
    """플랫폼별 설정 디렉토리를 반환합니다.

    Returns:
        Path: 플랫폼에 맞는 설정 디렉토리 경로
    """
    system = platform.system().lower()

    if system == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "selvage"
    elif system == "windows":
        # Windows APPDATA 경로 사용
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "selvage"
        return Path.home() / "AppData" / "Roaming" / "selvage"
    else:  # Linux 및 기타 Unix 계열
        # XDG Base Directory 규격 준수
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "selvage"
        return Path.home() / ".config" / "selvage"
