"""
캐시 기능을 테스트하는 모듈입니다.
"""

import pytest

from selvage.src.cache import CacheKeyGenerator, CacheKeyInfo, CacheManager
from selvage.src.diff_parser.models.diff_result import DiffResult
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse


@pytest.fixture
def cache_info_fixture() -> CacheKeyInfo:
    """캐시 키 정보 픽스처"""
    return CacheKeyInfo(
        diff_content="test diff content",
        model="gpt-5",
    )


@pytest.fixture
def review_request_fixture() -> ReviewRequest:
    """리뷰 요청 픽스처"""
    diff_result = DiffResult(files=[])
    return ReviewRequest(
        diff_content="test diff content",
        processed_diff=diff_result,
        file_paths=["test.py"],
        model="gpt-5",
        repo_path="/test",
    )


@pytest.fixture
def review_response_fixture() -> ReviewResponse:
    """리뷰 응답 픽스처"""
    return ReviewResponse(
        summary="Test review summary",
        issues=[],
        recommendations=["Test recommendation"],
    )


@pytest.fixture
def cache_manager_fixture() -> CacheManager:
    """캐시 매니저 픽스처"""
    cache_manager = CacheManager()
    # 테스트 전에 캐시 클리어
    cache_manager.clear_cache()
    return cache_manager


def test_cache_key_generation(cache_info_fixture: CacheKeyInfo):
    """캐시 키 생성을 테스트합니다."""
    cache_key = CacheKeyGenerator.generate_cache_key(cache_info_fixture)

    assert cache_key is not None
    assert isinstance(cache_key, str)
    assert len(cache_key) > 0


def test_cache_miss(
    cache_manager_fixture: CacheManager, review_request_fixture: ReviewRequest
):
    """캐시 미스 상황을 테스트합니다."""
    cached_result = cache_manager_fixture.get_cached_review(review_request_fixture)

    assert cached_result is None


def test_cache_save_and_hit(
    cache_manager_fixture: CacheManager,
    review_request_fixture: ReviewRequest,
    review_response_fixture: ReviewResponse,
):
    """캐시 저장 및 캐시 히트를 테스트합니다."""
    estimated_cost = EstimatedCost.get_zero_cost("gpt-5")

    # 캐시에 저장
    cache_manager_fixture.save_review_to_cache(
        review_request_fixture, review_response_fixture, estimated_cost
    )

    # 캐시에서 가져오기
    cached_result = cache_manager_fixture.get_cached_review(review_request_fixture)

    assert cached_result is not None
    cached_response, _ = cached_result
    assert cached_response.summary == "Test review summary"
    assert cached_response.issues == []
    assert cached_response.recommendations == ["Test recommendation"]


def test_cache_key_consistency(cache_info_fixture: CacheKeyInfo):
    """동일한 입력에 대해 일관된 캐시 키가 생성되는지 테스트합니다."""
    cache_key_1 = CacheKeyGenerator.generate_cache_key(cache_info_fixture)
    cache_key_2 = CacheKeyGenerator.generate_cache_key(cache_info_fixture)

    assert cache_key_1 == cache_key_2


def test_cache_key_different_for_different_inputs():
    """다른 입력에 대해 다른 캐시 키가 생성되는지 테스트합니다."""
    cache_info_1 = CacheKeyInfo(
        diff_content="test diff content 1",
        model="gpt-5",
    )
    cache_info_2 = CacheKeyInfo(
        diff_content="test diff content 2",
        model="gpt-5",
    )

    cache_key_1 = CacheKeyGenerator.generate_cache_key(cache_info_1)
    cache_key_2 = CacheKeyGenerator.generate_cache_key(cache_info_2)

    assert cache_key_1 != cache_key_2
