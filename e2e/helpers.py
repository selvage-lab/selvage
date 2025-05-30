"""E2E 테스트용 헬퍼 함수들."""


def install_selvage_from_testpypi(container) -> None:
    """TestPyPI에서 selvage 설치하는 헬퍼 함수."""
    install_command = "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --no-deps selvage"
    exit_code, output = container.exec(install_command)
    assert exit_code == 0, (
        f"TestPyPI에서 selvage 설치가 성공해야 합니다. 출력: {output.decode()}"
    )
    print("TestPyPI에서 selvage 설치 완료")
