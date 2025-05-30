"""CLI --version 옵션 테스트 모듈."""

import unittest

from click.testing import CliRunner

from selvage.__version__ import __version__
from selvage.cli import cli


class TestCLIVersion(unittest.TestCase):
    """CLI --version 옵션 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 설정."""
        self.runner = CliRunner()

    def test_version_option(self) -> None:
        """--version 옵션이 버전 정보를 출력하는지 테스트."""
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("selvage", result.output)
        self.assertIn(__version__, result.output)
        self.assertEqual(result.output.strip(), f"selvage {__version__}")

    def test_version_option_does_not_run_default_command(self) -> None:
        """--version 옵션이 기본 review 명령어를 실행하지 않는지 테스트."""
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        # review 명령어 관련 메시지가 없어야 함
        self.assertNotIn("코드 리뷰", result.output)
        self.assertNotIn("API 키", result.output)


if __name__ == "__main__":
    unittest.main()
