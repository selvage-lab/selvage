"""MCP 모드 관리 기능 테스트"""

import subprocess
import sys

from selvage.src.config import get_mcp_mode_status, is_mcp_mode


class TestMCPModeManagement:
    """MCP 모드 관리 기능 테스트 클래스"""

    def test_get_mcp_mode_status_returns_dict(self) -> None:
        """MCP 모드 상태 정보는 딕셔너리로 반환되어야 함"""
        status = get_mcp_mode_status()
        assert isinstance(status, dict)
        assert "mcp_mode" in status
        assert "mcp_mode_set" in status
        assert isinstance(status["mcp_mode"], bool)
        assert isinstance(status["mcp_mode_set"], bool)

    def test_is_mcp_mode_returns_bool(self) -> None:
        """is_mcp_mode는 bool 값을 반환해야 함"""
        result = is_mcp_mode()
        assert isinstance(result, bool)


class TestMCPModeIsolation:
    """별도 프로세스에서 MCP 모드 격리 테스트"""

    def test_initial_mcp_mode_is_false(self) -> None:
        """초기 MCP 모드는 False여야 함"""
        # 별도 프로세스에서 확인
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from selvage.src.config import is_mcp_mode; print(is_mcp_mode())",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "False"

    def test_set_mcp_mode_to_true(self) -> None:
        """MCP 모드를 True로 설정할 수 있어야 함"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from selvage.src.config import set_mcp_mode, is_mcp_mode; "
                "set_mcp_mode(True); print(is_mcp_mode())",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "True"

    def test_set_mcp_mode_to_false(self) -> None:
        """MCP 모드를 False로 설정할 수 있어야 함"""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from selvage.src.config import set_mcp_mode, is_mcp_mode; "
                "set_mcp_mode(False); print(is_mcp_mode())",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "False"

    def test_mcp_mode_can_only_be_set_once(self) -> None:
        """MCP 모드는 프로세스당 한번만 설정 가능해야 함"""
        script = """
from selvage.src.config import set_mcp_mode
set_mcp_mode(True)
try:
    set_mcp_mode(False)
    print("ERROR")
except RuntimeError as e:
    print("SUCCESS" if "MCP mode can only be set once" in str(e) else f"WRONG_ERROR: {e}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "SUCCESS"
