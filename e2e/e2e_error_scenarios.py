"""E2E 에러 시나리오 및 예외 상황 테스트."""

import pytest
from testcontainers.core.generic import DockerContainer

from e2e.helpers import install_selvage_from_testpypi


@pytest.fixture(scope="function")
def error_test_container():
    """에러 테스트용 TestPyPI 컨테이너 fixture"""
    container = DockerContainer(image="selvage-testpypi:latest")
    container.with_command("bash -c 'while true; do sleep 1; done'")

    # 의도적으로 잘못된 API 키 설정
    container.with_env("GEMINI_API_KEY", "invalid_api_key_for_testing")
    container.start()

    yield container
    container.stop()


def test_invalid_api_key_handling(error_test_container) -> None:
    """잘못된 API 키로 리뷰 시도 시 에러 처리 테스트."""
    container = error_test_container

    # TestPyPI에서 selvage 설치
    install_selvage_from_testpypi(container)

    # 테스트 저장소 생성 및 git init
    exit_code, output = container.exec(
        "bash -c 'mkdir -p /tmp/error_test_repo && cd /tmp/error_test_repo && git init'"
    )
    assert exit_code == 0, (
        f"Git init should succeed. Output: {output.decode('utf-8', errors='ignore')}"
    )

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/error_test_repo && git config user.email test@example.com'"
    )
    assert exit_code == 0, "Git config should succeed"

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/error_test_repo && git config user.name \"Test User\"'"
    )
    assert exit_code == 0, "Git config should succeed"

    # 테스트 파일 생성
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/error_test_repo && echo \"def test(): pass\" > test.py && git add test.py'"
    )
    assert exit_code == 0, "Test file creation should succeed"

    # 잘못된 API 키로 리뷰 시도 (모델 지정하지 않으면 모델 설정 에러가 먼저 발생)
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/error_test_repo && selvage review --staged --model gemini-2.5-flash'"
    )

    # 실제로는 모델 미설정 에러가 먼저 발생함
    output_str = output.decode("utf-8", errors="ignore").lower()
    assert any(
        keyword in output_str
        for keyword in ["api_key_invalid", "400 invalid_argument."]
    ), f"Should handle model not configured error. Actual output: {output_str}"


def test_not_config_default_model_handling(error_test_container) -> None:
    """기본 모델이 설정되지 않았을 때 리뷰 시도 시 에러 처리 테스트."""
    container = error_test_container

    # TestPyPI에서 selvage 설치
    install_selvage_from_testpypi(container)

    # 빈 저장소 생성 및 git init
    exit_code, output = container.exec(
        "bash -c 'mkdir -p /tmp/empty_repo && cd /tmp/empty_repo && git init'"
    )
    assert exit_code == 0, (
        f"Git init should succeed. Output: {output.decode('utf-8', errors='ignore')}"
    )

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && git config user.email test@example.com'"
    )
    assert exit_code == 0, "Git config should succeed"

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && git config user.name \"Test User\"'"
    )
    assert exit_code == 0, "Git config should succeed"

    # 스테이징된 변경사항 없이 리뷰 시도
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && selvage review --staged'"
    )

    # 적절한 처리가 되어야 함 (에러이거나 적절한 메시지)
    output_str = output.decode("utf-8", errors="ignore").lower()
    assert any(
        keyword in output_str for keyword in ["리뷰 모델을 지정하지 않았습니다."]
    ), f"Should handle empty repository appropriately. Actual output: {output_str}"


def test_empty_repository_handling(error_test_container) -> None:
    """빈 저장소에서 리뷰 시도 시 에러 처리 테스트."""
    container = error_test_container

    # TestPyPI에서 selvage 설치
    install_selvage_from_testpypi(container)

    # 빈 저장소 생성 및 git init
    exit_code, output = container.exec(
        "bash -c 'mkdir -p /tmp/empty_repo && cd /tmp/empty_repo && git init'"
    )
    assert exit_code == 0, (
        f"Git init should succeed. Output: {output.decode('utf-8', errors='ignore')}"
    )

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && git config user.email test@example.com'"
    )
    assert exit_code == 0, "Git config should succeed"

    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && git config user.name \"Test User\"'"
    )
    assert exit_code == 0, "Git config should succeed"

    # 스테이징된 변경사항 없이 리뷰 시도
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/empty_repo && selvage review --staged --model gemini-2.5-flash'"
    )

    # 적절한 처리가 되어야 함 (에러이거나 적절한 메시지)
    output_str = output.decode("utf-8", errors="ignore").lower()
    assert any(
        keyword in output_str
        for keyword in ["변경 사항이 없거나 diff를 가져올 수 없습니다."]
    ), f"Should handle empty repository appropriately. Actual output: {output_str}"


def test_non_git_directory_handling(error_test_container) -> None:
    """Git 저장소가 아닌 디렉토리에서 리뷰 시도 시 에러 처리 테스트."""
    container = error_test_container

    # TestPyPI에서 selvage 설치
    install_selvage_from_testpypi(container)

    # Git 저장소가 아닌 일반 디렉토리 생성
    exit_code, output = container.exec("mkdir -p /tmp/non_git_dir")
    assert exit_code == 0, "Non-git directory creation should succeed"

    # Git 저장소가 아닌 곳에서 리뷰 시도
    exit_code, output = container.exec(
        "bash -c 'cd /tmp/non_git_dir && selvage review --staged --model gemini-2.5-flash'"
    )

    # 적절한 에러 처리가 되어야 함
    output_str = output.decode("utf-8", errors="ignore").lower()

    assert any(
        keyword in output_str
        for keyword in ["git diff 오류", "유효한 git 저장소", "변경 사항이 없거나"]
    ), (
        f"Error message should mention git repository requirement. Actual output: {output_str}"
    )


@pytest.mark.parametrize(
    "invalid_model", ["nonexistent-model", "gpt-999", "invalid-model-name"]
)
def test_invalid_model_configuration(error_test_container, invalid_model: str) -> None:
    """잘못된 모델 설정 시 에러 처리 테스트."""
    container = error_test_container

    # TestPyPI에서 selvage 설치
    install_selvage_from_testpypi(container)

    # 잘못된 모델 설정 시도 - 설정 단계에서 실패해야 함
    exit_code, output = container.exec(f"selvage config model {invalid_model}")

    # 설정 명령이 실패해야 함
    assert exit_code != 0, f"Invalid model '{invalid_model}' configuration should fail"

    output_str = output.decode("utf-8", errors="ignore").lower()
    assert any(
        keyword in output_str
        for keyword in ["지원되지 않는 모델", "invalid value", "사용 가능한 ai 모델"]
    ), (
        f"Should handle invalid model '{invalid_model}' with appropriate error message. Actual output: {output_str}"
    )
