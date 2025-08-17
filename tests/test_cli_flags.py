"""
CLI 플래그 기능 테스트 모듈.
"""

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from selvage.cli import cli
from selvage.src.model_config import ModelProvider


class TestCLIFlags(unittest.TestCase):
    """CLI 플래그 기능 테스트 클래스."""

    def setUp(self):
        """테스트 설정."""
        self.runner = CliRunner()


    @patch("selvage.cli.get_diff_content")
    @patch("selvage.cli.get_api_key")
    @patch("selvage.cli.get_model_info")
    def test_default_review_command(
        self, mock_get_model_info, mock_get_api_key, mock_get_diff_content
    ) -> None:
        """기본 review 명령어 테스트 (API 키가 없을 때)."""
        mock_get_model_info.return_value = {"provider": ModelProvider.OPENAI}
        mock_get_api_key.return_value = None
        mock_get_diff_content.return_value = ""

        result = self.runner.invoke(cli, [])

        # API 키가 없으면 warning 메시지가 나와야 함
        self.assertEqual(result.exit_code, 0)

    def test_help_command(self) -> None:
        """도움말 명령어 테스트."""
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("LLM 기반 코드 리뷰 도구", result.output)

    def test_review_help_command(self) -> None:
        """review 서브명령어 도움말 테스트."""
        result = self.runner.invoke(cli, ["review", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("코드 리뷰 수행", result.output)

    def test_config_help_command(self) -> None:
        """config 서브명령어 도움말 테스트."""
        result = self.runner.invoke(cli, ["config", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("설정 관리", result.output)

    def test_no_print_option_in_help(self) -> None:
        """--no-print 옵션이 도움말에 표시되는지 테스트."""
        result = self.runner.invoke(cli, ["review", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--no-print", result.output)
        self.assertIn("터미널에 리뷰 결과를 출력하지 않음", result.output)

    def test_open_ui_option_in_help(self) -> None:
        """--open-ui 옵션이 도움말에 표시되는지 테스트."""
        result = self.runner.invoke(cli, ["review", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--open-ui", result.output)
        self.assertIn("리뷰 완료 후 UI로 결과 보기", result.output)


if __name__ == "__main__":
    unittest.main()
