"""Python 버전별 selvage 호환성 테스트.

이 파일은 Python 버전 호환성 확인을 위해 기존 방식(로컬 마운트)을 유지합니다.
"""

import pytest
from testcontainers.core.generic import DockerContainer


@pytest.mark.parametrize("python_version", ["3.10", "3.11", "3.12", "3.13"])
def test_selvage_python_compatibility(python_version: str) -> None:
    """Python 버전별 selvage 호환성 테스트."""
    # project_root = Path(__file__).parent.parent # 더 이상 필요하지 않음

    container = DockerContainer(image=f"python:{python_version}-slim")
    # container.with_volume_mapping(str(project_root), "/app", "rw") # 로컬 볼륨 마운트 제거
    container.with_kwargs(
        working_dir="/app"
    )  # working_dir은 유지하거나 필요에 따라 제거
    container.with_command("bash -c 'while true; do sleep 1; done'")
    container.start()

    try:
        # 컨테이너 상태 확인
        wrapped_container = container.get_wrapped_container()
        wrapped_container.reload()
        container_attrs = wrapped_container.attrs

        assert container_attrs["State"]["Running"], "Container should be running"

        # 필요한 패키지 설치
        exit_code, output = container.exec(
            "bash -c 'DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get install -y git'"
        )
        assert exit_code == 0, "Package installation should succeed"

        # Git 설정
        container.exec("bash -c 'git config --global user.email test@example.com'")
        container.exec("bash -c 'git config --global user.name \"Test User\"'")

        # selvage 설치 (testpypi 사용)
        # poetry lock --no-update && poetry version --short을 통해 현재 버전을 가져오는 것이 이상적이나,
        # e2e 테스트 환경의 복잡성을 줄이기 위해 하드코딩된 버전 또는 __version__ 사용
        # 여기서는 예시로 "0.1.1"을 사용합니다. 실제 사용 시에는 동적으로 가져오는 것을 고려해야 합니다.
        # TODO: CI 환경 등에서 현재 패키지 버전을 동적으로 가져와 사용하도록 개선 필요
        current_version = "0.1.1"  # 이전 단계에서 확인한 버전
        install_command = f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple selvage=={current_version}"
        exit_code, output = container.exec(f"bash -c '{install_command}'")
        assert exit_code == 0, (
            f"Selvage installation should succeed. Output: {output.decode()}"
        )

        # 기본 명령어 테스트
        exit_code, output = container.exec(
            "bash -c 'python -m selvage --help'"  # 'cd /app' 제거
        )
        assert exit_code == 0, "Selvage help command should work"
        assert b"selvage" in output.lower(), "Output should contain 'selvage'"

    finally:
        container.stop()


def test_selvage_python_incompatibility() -> None:
    """Python 3.9에서 selvage가 설치되지 않는 것을 확인하는 테스트."""
    # project_root = Path(__file__).parent.parent # 더 이상 필요하지 않음

    container = DockerContainer(image="python:3.9-slim")
    # container.with_volume_mapping(str(project_root), "/app", "rw") # 로컬 볼륨 마운트 제거
    container.with_kwargs(
        working_dir="/app"
    )  # working_dir은 유지하거나 필요에 따라 제거
    container.with_command("bash -c 'while true; do sleep 1; done'")
    container.start()

    try:
        # 컨테이너 상태 확인
        wrapped_container = container.get_wrapped_container()
        wrapped_container.reload()
        container_attrs = wrapped_container.attrs

        assert container_attrs["State"]["Running"], "Container should be running"

        # 필요한 패키지 설치
        exit_code, output = container.exec(
            "bash -c 'DEBIAN_FRONTEND=noninteractive apt-get update -y && apt-get install -y git'"
        )
        assert exit_code == 0, "Package installation should succeed"

        # Git 설정
        container.exec("bash -c 'git config --global user.email test@example.com'")
        container.exec("bash -c 'git config --global user.name \"Test User\"'")

        # selvage 설치 시도 - Python 3.9에서는 실패해야 함 (python_requires=">=3.10")
        # testpypi 사용
        current_version = "0.1.1"  # 이전 단계에서 확인한 버전
        install_command = f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple selvage=={current_version}"
        exit_code, output = container.exec(f"bash -c '{install_command}'")

        # Python 3.9에서는 설치가 실패해야 함
        assert exit_code != 0, "Selvage installation should fail on Python 3.9"

        print("Python 3.9 incompatibility confirmed. Install failed as expected.")

    finally:
        container.stop()
