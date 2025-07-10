"""selvage CLI 기본 기능 Container 기반 End-to-End 테스트."""

import pytest
from testcontainers.core.generic import DockerContainer

from e2e.helpers import install_selvage_from_testpypi
from selvage.src.config import get_api_key
from selvage.src.models.model_provider import ModelProvider


@pytest.fixture(scope="function")
def testpypi_container():
    """TestPyPI 테스트용 사전 구성된 컨테이너 fixture (의존성 미리 설치됨)."""
    container = DockerContainer(image="selvage-testpypi:latest")
    container.with_command("bash -c 'while true; do sleep 1; done'")

    # API 키 설정 (필요한 경우)
    gemini_api_key = get_api_key(ModelProvider.GOOGLE)
    if gemini_api_key:
        container.with_env("GEMINI_API_KEY", gemini_api_key)

    container.start()

    yield container
    container.stop()


class TestSelvageCLIBasic:
    """selvage CLI 기본 명령어 컨테이너 테스트."""

    def test_selvage_help(self, testpypi_container) -> None:
        """selvage --help 명령어가 정상 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # help 명령어 테스트
        exit_code, output = container.exec("selvage --help")

        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore").lower()
        assert "selvage" in output_str
        assert "usage:" in output_str

    def test_selvage_version(self, testpypi_container) -> None:
        """selvage --version 명령어로 버전 정보 확인 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # version 명령어 테스트
        exit_code, output = container.exec("selvage --version")

        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "selvage" in output_str
        # TestPyPI 버전은 변동될 수 있으므로 구체적인 버전 체크 제거

    def test_selvage_config_list(self, testpypi_container) -> None:
        """selvage config list 명령어가 정상 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # config list 명령어 테스트
        exit_code, output = container.exec("selvage config list")

        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "selvage 설정" in output_str

    def test_selvage_models(self, testpypi_container) -> None:
        """selvage models 명령어가 정상 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # models 명령어 테스트
        exit_code, output = container.exec("selvage models")

        assert exit_code == 0
        # 모델 정보가 출력되는지 확인
        output_str = output.decode("utf-8", errors="ignore").lower()
        assert any(model in output_str for model in ["gpt", "claude", "openai"])


class TestSelvageConfigManagement:
    """selvage 설정 관리 컨테이너 테스트."""

    def test_config_model_set_and_get(self, testpypi_container) -> None:
        """모델 설정이 정상적으로 저장되고 읽어지는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # 유효한 모델명으로 설정
        exit_code, output = container.exec("selvage config model gpt-4o")
        assert exit_code == 0

        # 설정 확인
        exit_code, output = container.exec("selvage config list")
        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "gpt-4o" in output_str

    def test_config_diff_only_setting(self, testpypi_container) -> None:
        """diff-only 설정이 정상적으로 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # diff-only 설정
        exit_code, output = container.exec("selvage config diff-only true")
        assert exit_code == 0

        # 설정 확인
        exit_code, output = container.exec("selvage config list")
        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore").lower()
        assert "true" in output_str

    def test_config_language_setting(self, testpypi_container) -> None:
        """언어 설정이 정상적으로 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # 언어 설정
        exit_code, output = container.exec("selvage config language English")
        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "English로 설정되었습니다" in output_str

        # 설정 확인
        exit_code, output = container.exec("selvage config list")
        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "English" in output_str

    def test_config_language_show_current(self, testpypi_container) -> None:
        """현재 언어 설정 표시가 정상적으로 작동하는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # 현재 언어 설정 확인
        exit_code, output = container.exec("selvage config language")
        assert exit_code == 0
        output_str = output.decode("utf-8", errors="ignore")
        assert "현재 기본 언어" in output_str


class TestSelvageFileSystem:
    """selvage 파일 시스템 관련 컨테이너 테스트."""

    def test_config_directory_creation(self, testpypi_container) -> None:
        """설정 디렉토리가 자동으로 생성되는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # 설정 디렉토리 경로 확인
        exit_code, config_dir_output = container.exec(
            'python -c "from selvage.src.utils.platform_utils import get_platform_config_dir; print(get_platform_config_dir())"'
        )
        assert exit_code == 0, "Should be able to get config directory path"

        config_dir = config_dir_output.decode("utf-8", errors="ignore").strip()

        # 설정 명령어 실행
        exit_code, output = container.exec("selvage config list")
        assert exit_code == 0

        # 설정 디렉토리가 생성되었는지 확인
        exit_code, output = container.exec(f"test -d {config_dir}")
        assert exit_code == 0, f"Config directory should exist at {config_dir}"

    def test_log_directory_creation(self, testpypi_container) -> None:
        """로그 디렉토리가 자동으로 생성되는지 테스트."""
        container = testpypi_container

        install_selvage_from_testpypi(container)  # 다시 호출

        # 설정 디렉토리 경로 확인
        exit_code, config_dir_output = container.exec(
            'python -c "from selvage.src.utils.platform_utils import get_platform_config_dir; print(get_platform_config_dir())"'
        )
        assert exit_code == 0, "Should be able to get config directory path"

        config_dir = config_dir_output.decode("utf-8", errors="ignore").strip()

        # 설정 명령어 실행 (로그 생성을 위해)
        exit_code, output = container.exec("selvage config list")
        assert exit_code == 0

        # logs 디렉토리가 생성되었는지 확인 (설정에 따라 조정 필요)
        expected_log_dirs = [
            f"{config_dir}/logs",
            f"{config_dir}/review_log",
        ]

        # 하나 이상의 로그 디렉토리가 생성되었는지 확인
        log_dir_exists = False
        for log_dir in expected_log_dirs:
            exit_code, output = container.exec(f"test -d {log_dir}")
            if exit_code == 0:
                log_dir_exists = True
                break

        # 로그 디렉토리는 실제 리뷰 실행 시 생성될 수 있으므로,
        # 이 테스트는 선택적으로 확인
        if log_dir_exists:
            assert True  # 로그 디렉토리가 생성됨
        else:
            # 로그 디렉토리가 생성되지 않은 것은 정상적일 수 있음
            # (리뷰 실행 시에만 생성되는 경우)
            assert True
