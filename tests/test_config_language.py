"""언어 설정 기능을 테스트하는 모듈."""

import configparser
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from selvage.src.config import get_default_language, load_config, set_default_language


@pytest.fixture
def temp_config_file():
    """임시 설정 파일을 생성하는 fixture."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as f:
        config_path = Path(f.name)

    yield config_path

    # 정리
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def mock_config_file_path(temp_config_file):
    """config.py의 CONFIG_FILE을 임시 파일로 설정하는 fixture."""
    with patch("selvage.src.config.CONFIG_FILE", temp_config_file):
        yield temp_config_file


class TestLanguageConfig:
    """언어 설정 테스트 클래스."""

    def test_load_config_creates_language_section(self, mock_config_file_path):
        """load_config()가 language 섹션을 생성하는지 테스트."""
        config = load_config()

        assert "language" in config
        assert isinstance(config["language"], configparser.SectionProxy)

    def test_get_default_language_returns_korean_when_no_config(
        self, mock_config_file_path
    ):
        """설정이 없을 때 기본 언어로 Korean을 반환하는지 테스트."""
        language = get_default_language()

        assert language == "Korean"

    def test_get_default_language_from_config(self, mock_config_file_path):
        """설정 파일에서 언어를 읽어오는지 테스트."""
        # 설정 파일에 언어 설정
        config = configparser.ConfigParser()
        config["language"] = {"default": "English"}
        with open(mock_config_file_path, "w", encoding="utf-8") as f:
            config.write(f)

        language = get_default_language()

        assert language == "English"

    def test_set_default_language_success(self, mock_config_file_path):
        """언어 설정이 성공적으로 저장되는지 테스트."""
        result = set_default_language("Japanese")

        assert result is True

        # 설정이 저장되었는지 확인
        language = get_default_language()
        assert language == "Japanese"

    def test_set_default_language_creates_section_if_not_exists(
        self, mock_config_file_path
    ):
        """language 섹션이 없을 때 섹션을 생성하고 설정하는지 테스트."""
        # 빈 설정 파일 생성
        config = configparser.ConfigParser()
        with open(mock_config_file_path, "w", encoding="utf-8") as f:
            config.write(f)

        result = set_default_language("Chinese")

        assert result is True

        # 설정이 제대로 저장되었는지 확인
        config = load_config()
        assert "language" in config
        assert config["language"]["default"] == "Chinese"

    @patch("selvage.src.config.save_config")
    def test_set_default_language_handles_save_error(
        self, mock_save_config, mock_config_file_path
    ):
        """설정 저장 중 오류가 발생할 때 False를 반환하는지 테스트."""
        mock_save_config.side_effect = Exception("저장 오류")

        result = set_default_language("German")

        assert result is False

    def test_multiple_language_changes(self, mock_config_file_path):
        """여러 번 언어를 변경할 때 제대로 작동하는지 테스트."""
        languages = ["English", "Japanese", "Chinese", "Korean"]

        for language in languages:
            result = set_default_language(language)
            assert result is True

            current_language = get_default_language()
            assert current_language == language

    def test_language_persistence_across_loads(self, mock_config_file_path):
        """설정이 load_config() 호출 간에도 유지되는지 테스트."""
        # 언어 설정
        set_default_language("Spanish")

        # 새로운 config 인스턴스 로드
        config1 = load_config()
        config2 = load_config()

        assert config1["language"]["default"] == "Spanish"
        assert config2["language"]["default"] == "Spanish"

    def test_config_file_structure_after_language_setting(self, mock_config_file_path):
        """언어 설정 후 config 파일 구조가 올바른지 테스트."""
        set_default_language("French")

        config = load_config()

        # 필수 섹션들이 모두 존재하는지 확인
        expected_sections = ["paths", "default", "debug", "language"]
        for section in expected_sections:
            assert section in config

        # 언어 설정이 올바른 위치에 있는지 확인
        assert config["language"]["default"] == "French"


class TestLanguageConfigEdgeCases:
    """언어 설정 엣지 케이스 테스트 클래스."""

    def test_get_default_language_with_corrupted_config(self):
        """설정 파일이 손상된 경우에도 기본값을 반환하는지 테스트."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as f:
            f.write("invalid config content")
            corrupted_config_path = Path(f.name)

        try:
            with patch("selvage.src.config.CONFIG_FILE", corrupted_config_path):
                language = get_default_language()
                assert language == "Korean"
        finally:
            corrupted_config_path.unlink()

    def test_empty_language_value(self, mock_config_file_path):
        """빈 언어 값을 설정할 때의 동작을 테스트."""
        result = set_default_language("")

        assert result is True

        language = get_default_language()
        assert language == ""

    def test_special_characters_in_language(self, mock_config_file_path):
        """특수 문자가 포함된 언어명을 처리하는지 테스트."""
        special_language = "한국어-韓國語"

        result = set_default_language(special_language)

        assert result is True

        language = get_default_language()
        assert language == special_language

    def test_very_long_language_name(self, mock_config_file_path):
        """매우 긴 언어명을 처리하는지 테스트."""
        long_language = "a" * 1000

        result = set_default_language(long_language)

        assert result is True

        language = get_default_language()
        assert language == long_language


class TestLanguageCLI:
    """언어 설정 CLI 명령어 테스트 클래스."""

    def setup_method(self):
        """테스트 설정."""
        from click.testing import CliRunner

        self.runner = CliRunner()

    def test_config_language_help(self):
        """config language 도움말 테스트."""
        from selvage.cli import cli

        result = self.runner.invoke(cli, ["config", "language", "--help"])

        assert result.exit_code == 0
        assert "Default language setting" in result.output

    @patch("selvage.cli.get_default_language")
    @patch("selvage.cli.console")
    def test_config_language_show_current(
        self, mock_console, mock_get_default_language
    ):
        """현재 언어 설정 표시 테스트."""
        from selvage.cli import cli

        mock_get_default_language.return_value = "English"

        result = self.runner.invoke(cli, ["config", "language"])

        assert result.exit_code == 0
        mock_get_default_language.assert_called_once()
        mock_console.info.assert_any_call("Current default language: English")

    @patch("selvage.cli.set_default_language")
    @patch("selvage.cli.console")
    def test_config_language_set_success(self, mock_console, mock_set_default_language):
        """언어 설정 성공 테스트."""
        from selvage.cli import cli

        mock_set_default_language.return_value = True

        result = self.runner.invoke(cli, ["config", "language", "English"])

        assert result.exit_code == 0
        mock_set_default_language.assert_called_once_with("English")
        mock_console.success.assert_called_with("Default language has been set to English.")

    @patch("selvage.cli.set_default_language")
    @patch("selvage.cli.console")
    def test_config_language_set_failure(self, mock_console, mock_set_default_language):
        """언어 설정 실패 테스트."""
        from selvage.cli import cli

        mock_set_default_language.return_value = False

        result = self.runner.invoke(cli, ["config", "language", "Spanish"])

        assert result.exit_code == 0
        mock_set_default_language.assert_called_once_with("Spanish")
        mock_console.error.assert_called_with("Failed to set default language.")

    @patch("selvage.cli.get_default_language")
    def test_config_language_in_config_list(self, mock_get_default_language):
        """config list에서 언어 설정이 표시되는지 테스트."""
        from selvage.cli import cli
        from selvage.src.exceptions.api_key_not_found_error import APIKeyNotFoundError
        from selvage.src.models.model_provider import ModelProvider

        mock_get_default_language.return_value = "Japanese"

        with patch("selvage.cli.get_api_key") as mock_get_api_key:
            # API 키 관련 모킹 (다른 설정들이 테스트에 영향주지 않도록)
            mock_get_api_key.side_effect = APIKeyNotFoundError(ModelProvider.OPENAI)

            with patch("selvage.cli.get_default_model", return_value=None):
                with patch("selvage.cli.console.is_debug_mode", return_value=False):
                    with patch(
                        "selvage.cli.get_default_review_log_dir",
                        return_value="/test/log",
                    ):
                        result = self.runner.invoke(cli, ["config", "list"])

        assert result.exit_code == 0
        assert "Japanese" in result.output
        assert "Default language" in result.output
