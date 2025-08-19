"""
리뷰 로그 디렉토리 설정 기능 테스트 모듈.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from selvage.cli import cli
from selvage.src.config import get_default_review_log_dir, set_default_review_log_dir


class TestReviewLogDirConfig(unittest.TestCase):
    """리뷰 로그 디렉토리 설정 기능 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 시작 전 설정."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_dir = os.path.join(self.temp_dir, "test_review_logs")

    def tearDown(self) -> None:
        """테스트 완료 후 정리."""
        # 임시 디렉토리 정리
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("selvage.src.config.load_config")
    def test_get_default_review_log_dir_with_config(self, mock_load_config) -> None:
        """설정 파일에 review_log_dir가 있을 때 테스트."""
        test_path = "/custom/review/log/path"
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "paths"
        mock_config.__getitem__.return_value = {"review_log_dir": test_path}
        mock_load_config.return_value = mock_config

        result = get_default_review_log_dir()

        self.assertEqual(result, Path(test_path))

    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.CONFIG_DIR", Path("/test/config/dir"))
    def test_get_default_review_log_dir_without_config(self, mock_load_config) -> None:
        """설정 파일에 review_log_dir가 없을 때 기본값 반환 테스트."""
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "paths"
        mock_config.__getitem__.return_value = {}  # review_log_dir 키가 없음
        mock_load_config.return_value = mock_config

        result = get_default_review_log_dir()

        expected = Path("/test/config/dir") / "review_log"
        self.assertEqual(result, expected)

    @patch("selvage.src.config.load_config")
    def test_get_default_review_log_dir_with_tilde_path(self, mock_load_config) -> None:
        """홈 디렉토리 경로(~)가 포함된 설정 테스트."""
        test_path = "~/Documents/selvage_reviews"
        mock_config = MagicMock()
        mock_config.__contains__.side_effect = lambda key: key == "paths"
        mock_config.__getitem__.return_value = {"review_log_dir": test_path}
        mock_load_config.return_value = mock_config

        result = get_default_review_log_dir()

        # ~ 경로가 확장되었는지 확인
        self.assertEqual(result, Path(os.path.expanduser(test_path)))

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_default_review_log_dir_success(
        self, mock_console, mock_load_config, mock_save_config
    ) -> None:
        """리뷰 로그 디렉토리 설정 성공 테스트."""
        mock_config = MagicMock()
        mock_config.__getitem__.return_value = {}
        mock_load_config.return_value = mock_config

        result = set_default_review_log_dir(self.test_log_dir)

        self.assertTrue(result)
        mock_save_config.assert_called_once_with(mock_config)
        mock_console.success.assert_called_once()

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_default_review_log_dir_with_tilde(
        self, mock_console, mock_load_config, mock_save_config
    ) -> None:
        """홈 디렉토리 경로(~)로 리뷰 로그 디렉토리 설정 테스트."""
        tilde_path = "~/Documents/test_reviews"
        mock_config = MagicMock()
        paths_section = {}
        mock_config.__getitem__.return_value = paths_section
        mock_load_config.return_value = mock_config

        result = set_default_review_log_dir(tilde_path)

        self.assertTrue(result)
        # paths 섹션에 설정이 저장되었는지 확인
        self.assertIn("review_log_dir", paths_section)
        # 저장된 경로가 절대 경로인지 확인
        saved_path = paths_section["review_log_dir"]
        self.assertTrue(os.path.isabs(saved_path))
        mock_save_config.assert_called_once_with(mock_config)

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_default_review_log_dir_relative_path(
        self, mock_console, mock_load_config, mock_save_config
    ) -> None:
        """상대 경로로 리뷰 로그 디렉토리 설정 테스트."""
        relative_path = "logs/reviews"
        mock_config = MagicMock()
        paths_section = {}
        mock_config.__getitem__.return_value = paths_section
        mock_load_config.return_value = mock_config

        result = set_default_review_log_dir(relative_path)

        self.assertTrue(result)
        # paths 섹션에 설정이 저장되었는지 확인
        self.assertIn("review_log_dir", paths_section)
        # 저장된 경로가 절대 경로인지 확인
        saved_path = paths_section["review_log_dir"]
        self.assertTrue(os.path.isabs(saved_path))
        mock_save_config.assert_called_once_with(mock_config)

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_default_review_log_dir_failure(
        self, mock_console, mock_load_config, mock_save_config
    ) -> None:
        """리뷰 로그 디렉토리 설정 실패 테스트."""
        mock_load_config.side_effect = Exception("설정 파일 로드 실패")

        result = set_default_review_log_dir(self.test_log_dir)

        self.assertFalse(result)
        mock_console.error.assert_called_once()
        mock_save_config.assert_not_called()

    @patch("selvage.src.config.save_config")
    @patch("selvage.src.config.load_config")
    @patch("selvage.src.config.console")
    def test_set_default_review_log_dir_save_failure(
        self, mock_console, mock_load_config, mock_save_config
    ) -> None:
        """설정 저장 실패 테스트."""
        mock_config = MagicMock()
        mock_config.__getitem__.return_value = {}
        mock_load_config.return_value = mock_config
        mock_save_config.side_effect = Exception("설정 파일 저장 실패")

        result = set_default_review_log_dir(self.test_log_dir)

        self.assertFalse(result)
        mock_console.error.assert_called_once()


class TestCLIConfigReviewLogDir(unittest.TestCase):
    """CLI config review-log-dir 명령어 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 설정."""
        self.runner = CliRunner()

    @patch("selvage.cli.get_default_review_log_dir")
    @patch("selvage.cli.console")
    def test_config_review_log_dir_show_current(
        self, mock_console, mock_get_default_review_log_dir
    ) -> None:
        """현재 리뷰 로그 디렉토리 표시 테스트."""
        mock_get_default_review_log_dir.return_value = "/current/log/path"

        result = self.runner.invoke(cli, ["config", "review-log-dir"])

        self.assertEqual(result.exit_code, 0)
        mock_get_default_review_log_dir.assert_called_once()
        mock_console.info.assert_called()

    @patch("selvage.cli.set_default_review_log_dir")
    @patch("selvage.cli.console")
    def test_config_review_log_dir_set_success(
        self, mock_console, mock_set_default_review_log_dir
    ) -> None:
        """리뷰 로그 디렉토리 설정 성공 테스트."""
        test_path = "/new/log/directory"
        mock_set_default_review_log_dir.return_value = True

        result = self.runner.invoke(cli, ["config", "review-log-dir", test_path])

        self.assertEqual(result.exit_code, 0)

    @patch("selvage.cli.set_default_review_log_dir")
    @patch("selvage.cli.console")
    def test_config_review_log_dir_set_failure(
        self, mock_console, mock_set_default_review_log_dir
    ) -> None:
        """리뷰 로그 디렉토리 설정 실패 테스트."""
        test_path = "/invalid/path"
        mock_set_default_review_log_dir.return_value = False

        result = self.runner.invoke(cli, ["config", "review-log-dir", test_path])

        self.assertEqual(result.exit_code, 0)

    @patch("selvage.cli.set_default_review_log_dir")
    @patch("selvage.cli.console")
    def test_config_review_log_dir_with_tilde_path(
        self, mock_console, mock_set_default_review_log_dir
    ) -> None:
        """홈 디렉토리 경로(~)로 설정 테스트."""
        tilde_path = "~/Documents/selvage_reviews"
        mock_set_default_review_log_dir.return_value = True

        result = self.runner.invoke(cli, ["config", "review-log-dir", tilde_path])

        self.assertEqual(result.exit_code, 0)

    @patch("selvage.cli.set_default_review_log_dir")
    @patch("selvage.cli.console")
    def test_config_review_log_dir_with_relative_path(
        self, mock_console, mock_set_default_review_log_dir
    ) -> None:
        """상대 경로로 설정 테스트."""
        relative_path = "logs/reviews"
        mock_set_default_review_log_dir.return_value = True

        result = self.runner.invoke(cli, ["config", "review-log-dir", relative_path])

        self.assertEqual(result.exit_code, 0)

    def test_config_review_log_dir_help(self) -> None:
        """config review-log-dir 도움말 테스트."""
        result = self.runner.invoke(cli, ["config", "review-log-dir", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("리뷰 로그 저장 디렉토리 설정", result.output)

    @patch("selvage.cli.get_default_review_log_dir")
    def test_config_review_log_dir_in_config_list(
        self, mock_get_default_review_log_dir
    ) -> None:
        """config list에서 리뷰 로그 디렉토리가 표시되는지 테스트."""
        test_path = "/test/review/log/path"
        mock_get_default_review_log_dir.return_value = test_path

        with patch("selvage.cli.get_api_key") as mock_get_api_key:
            # API 키 관련 모킹 (다른 설정들이 테스트에 영향주지 않도록)
            from selvage.src.exceptions.api_key_not_found_error import (
                APIKeyNotFoundError,
            )
            from selvage.src.models.model_provider import ModelProvider

            mock_get_api_key.side_effect = APIKeyNotFoundError(ModelProvider.OPENAI)

            with patch("selvage.cli.get_default_model", return_value=None):
                with patch("selvage.cli.console.is_debug_mode", return_value=False):
                    result = self.runner.invoke(cli, ["config", "list"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(test_path, result.output)
        self.assertIn("리뷰 로그 디렉토리", result.output)


class TestCLIReviewLogDirOption(unittest.TestCase):
    """CLI review --review-log-dir 옵션 테스트 클래스."""

    def setUp(self) -> None:
        """테스트 설정."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.custom_log_dir = os.path.join(self.temp_dir, "custom_reviews")

    def tearDown(self) -> None:
        """테스트 완료 후 정리."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("selvage.cli.get_model_info")
    def test_save_review_log_with_custom_dir(self, mock_get_model_info) -> None:
        """save_review_log 함수가 사용자 지정 디렉토리를 올바르게 처리하는지 테스트."""
        from selvage.src.diff_parser.models.diff_result import DiffResult
        from selvage.src.models.model_provider import ModelProvider
        from selvage.src.models.review_status import ReviewStatus
        from selvage.src.utils.logging.review_log_manager import ReviewLogManager
        from selvage.src.utils.token.models import ReviewRequest

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": ModelProvider.OPENAI,
            "full_name": "gpt-5",
        }

        # ReviewRequest Mock 생성
        diff_result = DiffResult(files=[])
        review_request = ReviewRequest(
            diff_content="test diff",
            processed_diff=diff_result,
            file_paths=["test.py"],
            model="gpt-5",
            repo_path="/test/repo",
        )

        # save_review_log 호출
        log_path = ReviewLogManager.save(
            prompt=None,
            review_request=review_request,
            review_response=None,
            status=ReviewStatus.SUCCESS,
            review_log_dir=self.custom_log_dir,
            estimated_cost=None,
        )

        # 사용자 지정 디렉토리에 로그가 저장되었는지 확인
        self.assertTrue(log_path.startswith(self.custom_log_dir))
        self.assertTrue(os.path.exists(log_path))

        # 로그 파일 내용 확인
        with open(log_path, encoding="utf-8") as f:
            log_data = json.load(f)

        self.assertEqual(log_data["model"]["name"], "gpt-5")
        self.assertEqual(log_data["status"], "SUCCESS")

    @patch("selvage.cli.get_model_info")
    def test_save_review_log_with_default_dir(self, mock_get_model_info) -> None:
        """save_review_log 함수가 기본 디렉토리를 올바르게 사용하는지 테스트."""
        from selvage.src.config import get_default_review_log_dir
        from selvage.src.diff_parser.models.diff_result import DiffResult
        from selvage.src.models.model_provider import ModelProvider
        from selvage.src.models.review_status import ReviewStatus
        from selvage.src.utils.logging.review_log_manager import ReviewLogManager
        from selvage.src.utils.token.models import ReviewRequest

        # Mock 설정
        mock_get_model_info.return_value = {
            "provider": ModelProvider.OPENAI,
            "full_name": "gpt-5",
        }

        # ReviewRequest Mock 생성
        diff_result = DiffResult(files=[])
        review_request = ReviewRequest(
            diff_content="test diff",
            processed_diff=diff_result,
            file_paths=["test.py"],
            model="gpt-5",
            repo_path="/test/repo",
        )

        # save_review_log 호출 (review_log_dir=None)
        log_path = ReviewLogManager.save(
            prompt=None,
            review_request=review_request,
            review_response=None,
            status=ReviewStatus.SUCCESS,
            review_log_dir=None,
            estimated_cost=None,
        )

        # 기본 디렉토리에 로그가 저장되었는지 확인
        default_dir = str(get_default_review_log_dir())
        self.assertTrue(log_path.startswith(default_dir))
        self.assertTrue(os.path.exists(log_path))

    def test_review_log_dir_help(self) -> None:
        """review 명령어 도움말에 --log-dir 옵션이 포함되는지 테스트."""
        result = self.runner.invoke(cli, ["review", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--log-dir", result.output)
        self.assertIn("로그 저장 디렉토리", result.output)


if __name__ == "__main__":
    unittest.main()
