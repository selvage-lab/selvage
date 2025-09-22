"""BaseConsole MCP 모드 테스트"""

import subprocess
import sys


class TestBaseConsoleMCPMode:
    """BaseConsole MCP 모드 테스트 클래스"""

    def test_base_console_uses_stdout_in_normal_mode(self) -> None:
        """일반 모드에서 BaseConsole은 stdout을 사용해야 함"""
        # 이 테스트는 실패할 예정 (Red 단계)
        # BaseConsole이 아직 MCP 모드를 고려하지 않음
        script = """
from selvage.src.utils.base_console import BaseConsole
import sys
console = BaseConsole()
print("stdout" if console.console.file == sys.stdout else "stderr")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "stdout"

    def test_base_console_uses_stderr_in_mcp_mode(self) -> None:
        """MCP 모드에서 BaseConsole은 stderr를 사용해야 함"""
        # 이 테스트는 실패할 예정 (Red 단계)
        script = """
from selvage.src.config import set_mcp_mode
from selvage.src.utils.base_console import BaseConsole
import sys

set_mcp_mode(True)
console = BaseConsole()
print("stderr" if console.console.file == sys.stderr else "stdout")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "stderr"

    def test_base_console_file_property_changes_based_on_mcp_mode(self) -> None:
        """BaseConsole의 file 속성이 MCP 모드에 따라 변경되어야 함"""
        # 현재 프로세스에서는 MCP 모드를 설정할 수 없으므로 별도 프로세스로 테스트
        # 1. 일반 모드 테스트
        normal_script = """
from selvage.src.utils.base_console import BaseConsole
import sys
console = BaseConsole()
print("has_stdout" if hasattr(console.console, "file") and console.console.file == sys.stdout else "no_stdout")
"""
        normal_result = subprocess.run(
            [sys.executable, "-c", normal_script],
            capture_output=True,
            text=True,
            check=False,
        )

        # 2. MCP 모드 테스트
        mcp_script = """
from selvage.src.config import set_mcp_mode
from selvage.src.utils.base_console import BaseConsole
import sys

set_mcp_mode(True)
console = BaseConsole()
print("has_stderr" if hasattr(console.console, "file") and console.console.file == sys.stderr else "no_stderr")
"""
        mcp_result = subprocess.run(
            [sys.executable, "-c", mcp_script],
            capture_output=True,
            text=True,
            check=False,
        )

        # 현재는 구현되지 않았으므로 둘 다 stdout을 사용할 것
        # 구현 후에는 normal_result가 "has_stdout", mcp_result가 "has_stderr"가 되어야 함
        assert normal_result.stdout.strip() == "has_stdout"
        # 이 assert는 현재 실패할 예정
        assert mcp_result.stdout.strip() == "has_stderr"


class TestBaseConsoleInternalMethods:
    """BaseConsole 내부 메서드 테스트"""

    def test_base_console_import_is_mcp_mode_function(self) -> None:
        """BaseConsole이 is_mcp_mode 함수를 올바르게 import할 수 있어야 함"""
        # 이 테스트는 실패할 예정 (Red 단계)
        # BaseConsole이 아직 is_mcp_mode를 import하지 않음
        script = """
try:
    from selvage.src.utils.base_console import BaseConsole
    from selvage.src.config import is_mcp_mode

    # BaseConsole 내부에서 is_mcp_mode를 사용할 수 있는지 확인
    console = BaseConsole()
    print("success")
except ImportError as e:
    print(f"import_error: {e}")
except Exception as e:
    print(f"other_error: {e}")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == "success"
