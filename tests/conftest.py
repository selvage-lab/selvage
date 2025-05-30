"""Unit/Integration 테스트를 위한 pytest 설정."""


def pytest_configure(config):
    """pytest 설정을 구성합니다. 단위/통합 테스트용 마커들을 등록합니다."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
