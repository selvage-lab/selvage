"""
CLI claude-provider 명령어 테스트 모듈.
"""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from selvage.cli import cli
from selvage.src.models.claude_provider import ClaudeProvider


class TestCLIClaudeProvider(unittest.TestCase):
    """CLI claude-provider 명령어 테스트 클래스."""

    def setUp(self):
        """테스트 설정."""
        self.runner = CliRunner()

    @patch("selvage.cli.set_claude_provider")
    def test_set_claude_provider_anthropic(self, mock_set_claude_provider) -> None:
        """claude-provider anthropic 설정 테스트."""
        mock_set_claude_provider.return_value = True

        result = self.runner.invoke(cli, ["config", "claude-provider", "anthropic"])

        self.assertEqual(result.exit_code, 0)
        mock_set_claude_provider.assert_called_once_with(ClaudeProvider.ANTHROPIC)

    @patch("selvage.cli.set_claude_provider")
    def test_set_claude_provider_openrouter(self, mock_set_claude_provider) -> None:
        """claude-provider openrouter 설정 테스트."""
        mock_set_claude_provider.return_value = True

        result = self.runner.invoke(cli, ["config", "claude-provider", "openrouter"])

        self.assertEqual(result.exit_code, 0)
        mock_set_claude_provider.assert_called_once_with(ClaudeProvider.OPENROUTER)

    def test_set_claude_provider_invalid(self) -> None:
        """지원되지 않는 claude-provider 설정 테스트 (Click validation)."""
        result = self.runner.invoke(cli, ["config", "claude-provider", "invalid"])

        self.assertEqual(result.exit_code, 2)  # Click validation error
        self.assertIn("is not one of", result.output.lower())

    @patch("selvage.cli.set_claude_provider")
    def test_set_claude_provider_failure(self, mock_set_claude_provider) -> None:
        """claude-provider 설정 실패 테스트."""
        mock_set_claude_provider.return_value = False

        result = self.runner.invoke(cli, ["config", "claude-provider", "anthropic"])

        self.assertEqual(result.exit_code, 0)
        mock_set_claude_provider.assert_called_once_with(ClaudeProvider.ANTHROPIC)

    @patch("selvage.cli.get_claude_provider")
    @patch("selvage.cli.console")
    def test_get_claude_provider_current_setting(
        self, mock_console, mock_get_claude_provider
    ) -> None:
        """현재 claude-provider 설정 조회 테스트."""
        mock_get_claude_provider.return_value = ClaudeProvider.ANTHROPIC

        result = self.runner.invoke(cli, ["config", "claude-provider"])

        self.assertEqual(result.exit_code, 0)
        mock_get_claude_provider.assert_called_once()
        mock_console.info.assert_any_call("현재 Claude Provider: Anthropic")
        mock_console.info.assert_any_call("지원되는 Provider: anthropic, openrouter")
        mock_console.info.assert_any_call(
            "새로운 Provider를 설정하려면 'selvage config claude-provider <provider>' "
            "명령어를 사용하세요."
        )

    def test_claude_provider_help_command(self) -> None:
        """claude-provider 서브명령어 도움말 테스트."""
        result = self.runner.invoke(cli, ["config", "claude-provider", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Claude Provider 설정", result.output)

    def test_config_help_includes_claude_provider(self) -> None:
        """config 도움말에 claude-provider 명령어가 포함되는지 테스트."""
        result = self.runner.invoke(cli, ["config", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("claude-provider", result.output)


if __name__ == "__main__":
    unittest.main()
