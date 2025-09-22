"""MCP CLI 명령어 테스트"""

import subprocess
import sys

import pytest


class TestMCPCLICommand:
    """MCP CLI 명령어 테스트"""

    def test_mcp_command_exists(self) -> None:
        """selvage mcp 명령어가 존재하는지 테스트"""
        result = subprocess.run(
            [sys.executable, "-m", "selvage", "mcp", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        # 명령어가 존재하고 help 출력이 나와야 함
        assert result.returncode == 0
        assert "Start MCP (Model Context Protocol) server" in result.stdout

    def test_mcp_command_help_output(self) -> None:
        """MCP 명령어 도움말 출력 테스트"""
        result = subprocess.run(
            [sys.executable, "-m", "selvage", "mcp", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        help_output = result.stdout
        assert "Start MCP (Model Context Protocol) server" in help_output
        assert "Usage:" in help_output

    def test_mcp_function_exists_and_callable(self) -> None:
        """MCP 함수가 존재하고 호출 가능한지 테스트"""
        from selvage.cli import mcp

        assert callable(mcp), "mcp 함수가 호출 가능하지 않습니다"

    def test_mcp_function_has_correct_docstring(self) -> None:
        """MCP 함수가 올바른 docstring을 가지는지 테스트"""
        from selvage.cli import mcp

        assert mcp.__doc__ is not None
        assert "MCP" in mcp.__doc__
        assert "Model Context Protocol" in mcp.__doc__
        assert "server" in mcp.__doc__.lower()

    def test_mcp_command_integration_with_cli_group(self) -> None:
        """MCP 명령어가 CLI 그룹에 올바르게 통합되어 있는지 테스트"""
        # CLI 모듈을 직접 import해서 명령어 등록 확인
        from selvage.cli import cli

        # CLI 그룹에서 mcp 명령어 찾기
        commands = cli.list_commands(None)
        assert "mcp" in commands, "mcp 명령어가 CLI에 등록되지 않았습니다"

        # 명령어 객체 가져오기
        mcp_command = cli.get_command(None, "mcp")
        assert mcp_command is not None, "mcp 명령어를 가져올 수 없습니다"
        assert mcp_command.name == "mcp"

    def test_mcp_import_structure(self) -> None:
        """MCP 관련 import가 올바르게 구성되어 있는지 테스트"""
        # mcp 함수에서 사용하는 import들이 정상적으로 동작하는지 확인
        try:
            from selvage.src.mcp.server import main_sync

            # import가 성공했는지 확인
            assert callable(main_sync)
        except ImportError as e:
            pytest.fail(f"MCP 관련 import 실패: {e}")

    def test_cli_main_commands_list(self) -> None:
        """CLI 메인 명령어 목록에 mcp가 포함되어 있는지 테스트"""
        result = subprocess.run(
            [sys.executable, "-m", "selvage", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        help_output = result.stdout
        # mcp 명령어가 도움말에 표시되는지 확인
        assert "mcp" in help_output, "mcp 명령어가 메인 CLI 도움말에 표시되지 않습니다"

    def test_mcp_command_is_click_command(self) -> None:
        """MCP 명령어가 Click 명령어인지 테스트"""
        import click

        from selvage.cli import mcp

        # Click 명령어 객체인지 확인
        assert isinstance(mcp, click.Command), "mcp가 Click 명령어 객체가 아닙니다"


class TestMCPCommandIntegration:
    """MCP 명령어 통합 테스트"""

    def test_all_cli_commands_present(self) -> None:
        """모든 CLI 명령어가 존재하는지 테스트"""
        from selvage.cli import cli

        commands = cli.list_commands(None)

        # 기본 명령어들
        expected_commands = ["review", "view", "config", "models", "mcp"]

        for expected_cmd in expected_commands:
            assert expected_cmd in commands, (
                f"{expected_cmd} 명령어가 CLI에 등록되지 않았습니다"
            )

    def test_mcp_command_description(self) -> None:
        """MCP 명령어 설명이 올바른지 테스트"""
        from selvage.cli import cli

        mcp_command = cli.get_command(None, "mcp")
        assert mcp_command is not None

        # 명령어 설명 확인
        assert "MCP" in mcp_command.help
        assert "Model Context Protocol" in mcp_command.help
        assert "server" in mcp_command.help.lower()
