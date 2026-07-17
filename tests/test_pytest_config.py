"""pytest 설정이 valid한지 검증."""
import configparser
from pathlib import Path

import pytest


def test_pytest_config_no_unknown_options():
    """pyproject.toml의 [tool.pytest.ini_options]가 모두 인식되는지 확인."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    with pyproject.open("rb") as f:
        data = tomllib.load(f)

    pytest_config = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
    assert pytest_config, "[tool.pytest.ini_options] must exist"

    plugin_keys = {
        "asyncio_mode": "pytest-asyncio",
        "asyncio_default_fixture_loop_scope": "pytest-asyncio",
        "env": "pytest-env",
    }
    installed_plugins = _get_installed_plugins()

    for key, plugin in plugin_keys.items():
        if key in pytest_config:
            assert plugin in installed_plugins, (
                f"'{key}' requires '{plugin}' but it's not installed. "               f"Add '{plugin}' to [project.optional-dependencies] dev."
            )


def _get_installed_plugins() -> set[str]:
    """pip list에서 pytest-* 플러그인 추출."""
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "list", "--format=freeze"],
            capture_output=True, text=True, check=True,
        )
        return {
            line.split("==")[0].lower()
            for line in result.stdout.splitlines()
            if line.startswith("pytest-")
        }
    except Exception:
        return set()
