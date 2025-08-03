"""E2E 테스트용 헬퍼 함수들."""


def verify_selvage_installation(container) -> None:
    """TestPyPI 컨테이너는 이미 selvage가 설치되어 있음을 확인하는 헬퍼 함수."""
    exit_code, output = container.exec("selvage --version")
    assert exit_code == 0, f"selvage가 설치되어 있지 않습니다. 출력: {output.decode()}"
    print("TestPyPI selvage 설치 확인 완료")
