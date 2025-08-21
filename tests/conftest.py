"""Unit/Integration 테스트를 위한 pytest 설정."""

import pytest


def pytest_addoption(parser):
    """pytest에 커스텀 옵션을 추가합니다."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="통합 테스트를 포함하여 실행합니다.",
    )
    parser.addoption(
        "--run-all",
        action="store_true",
        default=False,
        help="모든 마크를 무시하고 모든 테스트를 강제 실행합니다.",
    )


def pytest_configure(config):
    """pytest 설정을 구성합니다. 단위/통합 테스트용 마커들을 등록합니다."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (use --integration to run)",
    )
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 테스트 아이템을 수정합니다."""
    # --run-all 옵션이 있으면 모든 마크를 무시하고 실행
    if config.getoption("--run-all"):
        return
    
    if not config.getoption("--integration"):
        # --integration 옵션이 없으면 integration 마커가 있는 테스트들을 스킵
        skip_integration = pytest.mark.skip(
            reason="통합 테스트는 --integration 옵션을 사용하세요"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
