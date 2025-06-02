import pytest
from datetime import datetime, timedelta, timezone
import json # Added import for json

# Assuming these models are accessible from this path
# Adjust if necessary based on actual project structure
from selvage.src.cache import CacheKeyGenerator, CacheKeyInfo, CacheManager
from selvage.src.utils.token.models import EstimatedCost, ReviewRequest, ReviewResponse, ProcessedDiff, DiffFile, Hunk

@pytest.fixture
def review_request_fixture() -> ReviewRequest:
    """Basic ReviewRequest fixture for testing."""
    return ReviewRequest(
        diff_content="test diff content",
        processed_diff=ProcessedDiff(
            files=[
                DiffFile(
                    filename="test_file.py",
                    status="modified",
                    hunks=[
                        Hunk(
                            header="@@ -1,1 +1,1 @@",
                            lines=["-old line", "+new line"],
                            start_line_old=1,
                            end_line_old=1,
                            start_line_new=1,
                            end_line_new=1,
                        )
                    ],
                    is_binary=False,
                    is_too_large=False,
                    content_before=None,
                    content_after=None,
                    language="python"
                )
            ],
            summary={"added": 0, "modified": 1, "removed": 0, "renamed": 0},
            is_full_context=True
        ),
        file_paths=["test_file.py"],
        use_full_context=True,
        model="gpt-4o",
        repo_path="."
    )

@pytest.fixture
def review_response_fixture() -> ReviewResponse:
    """Basic ReviewResponse fixture for testing."""
    return ReviewResponse(
        summary="Test summary",
        issues=[] # Empty issues list for simplicity
    )

@pytest.fixture
def cache_info_fixture() -> CacheKeyInfo:
    """캐시 키 정보 픽스처"""
    return CacheKeyInfo(
        diff_content="test diff content",
        model="gpt-4o",
        use_full_context=True,
    )

@pytest.fixture
def cache_manager_fixture() -> CacheManager:
    """캐시 매니저 픽스처"""
    # Use a temporary cache directory for tests if possible, or ensure cleanup
    cache_manager = CacheManager(cache_ttl_hours=1)
    # Ensure the cache is clean before each test that uses this fixture
    cache_manager.clear_cache()
    # Run cleanup of expired cache to ensure a clean state as well
    cache_manager.cleanup_expired_cache()
    return cache_manager

def test_cache_key_generation(cache_info_fixture: CacheKeyInfo):
    """캐시 키 생성을 테스트합니다."""
    cache_key = CacheKeyGenerator.generate_cache_key(cache_info_fixture)

    assert cache_key is not None
    assert isinstance(cache_key, str)
    assert len(cache_key) == 64  # SHA256 hex length

def test_cache_miss(cache_manager_fixture: CacheManager, review_request_fixture: ReviewRequest):
    """캐시 미스 상황을 테스트합니다."""
    cached_result = cache_manager_fixture.get_cached_review(review_request_fixture)
    assert cached_result is None

def test_cache_save_and_hit(
    cache_manager_fixture: CacheManager,
    review_request_fixture: ReviewRequest,
    review_response_fixture: ReviewResponse,
):
    """캐시 저장 및 캐시 히트를 테스트합니다."""
    estimated_cost = EstimatedCost.get_zero_cost("gpt-4o") # Using a zero cost for testing cache hit

    # 캐시에 저장
    cache_manager_fixture.save_review_to_cache(
        review_request_fixture, review_response_fixture, estimated_cost, log_id="test-log-123"
    )

    # 캐시에서 가져오기
    cached_result = cache_manager_fixture.get_cached_review(review_request_fixture)

    assert cached_result is not None
    cached_response, cached_cost = cached_result
    assert cached_response.summary == review_response_fixture.summary
    assert cached_response.issues == review_response_fixture.issues
    # Verify that the cost returned from cache is what was saved
    assert cached_cost is not None
    assert cached_cost.total_cost == 0.0


def test_cache_key_consistency(cache_info_fixture: CacheKeyInfo):
    """동일한 입력에 대해 일관된 캐시 키가 생성되는지 테스트합니다."""
    cache_key_1 = CacheKeyGenerator.generate_cache_key(cache_info_fixture)

    # Create another CacheKeyInfo instance with the same data to ensure it's not object identity
    cache_info_same = CacheKeyInfo(
        diff_content="test diff content",
        model="gpt-4o",
        use_full_context=True,
    )
    cache_key_2 = CacheKeyGenerator.generate_cache_key(cache_info_same)

    assert cache_key_1 == cache_key_2

def test_cache_clear(
    cache_manager_fixture: CacheManager,
    review_request_fixture: ReviewRequest,
    review_response_fixture: ReviewResponse
):
    """캐시 삭제 기능을 테스트합니다."""
    # Save something to cache
    cache_manager_fixture.save_review_to_cache(
        review_request_fixture, review_response_fixture, EstimatedCost.get_zero_cost("gpt-4o"), log_id="test-log-clear" # Added EstimatedCost
    )

    # Ensure it's saved
    assert cache_manager_fixture.get_cached_review(review_request_fixture) is not None

    # Clear cache
    cache_manager_fixture.clear_cache()

    # Verify it's cleared
    assert cache_manager_fixture.get_cached_review(review_request_fixture) is None
    # Additionally, check if the cache directory is empty or non-existent for *.json files
    # This depends on the implementation of clear_cache (e.g., deletes files or the dir itself)
    # For this test, we assume clear_cache() removes all .json files from the cache_dir
    cache_files = list(cache_manager_fixture.cache_dir.glob("*.json"))
    assert len(cache_files) == 0


def test_cache_expiration(
    cache_manager_fixture: CacheManager, # Uses default 1 hour TTL from fixture
    review_request_fixture: ReviewRequest,
    review_response_fixture: ReviewResponse
):
    """캐시 만료 기능을 테스트합니다."""
    # Save an item to cache
    cache_manager_fixture.save_review_to_cache(
        review_request_fixture, review_response_fixture, EstimatedCost.get_zero_cost("gpt-4o"), log_id="test-log-expire" # Added EstimatedCost
    )

    # Retrieve the cache entry directly to manipulate its created_at/expires_at for testing
    cache_info = CacheKeyInfo(
        diff_content=review_request_fixture.diff_content,
        model=review_request_fixture.model,
        use_full_context=review_request_fixture.use_full_context,
    )
    cache_key = CacheKeyGenerator.generate_cache_key(cache_info)
    cache_file_path = cache_manager_fixture._get_cache_file_path(cache_key)

    assert cache_file_path.exists()

    # Load the cache entry and modify its 'expires_at' to a past time
    with open(cache_file_path, 'r+', encoding='utf-8') as f:
        cache_data = json.load(f)
        # Set expires_at to 2 hours in the past from now (UTC for consistency)
        # Pydantic models expect datetime objects, but JSON stores ISO strings.
        # The CacheManager's save method uses .isoformat() via model_dump(mode='json').
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        cache_data['expires_at'] = past_time.isoformat()

        f.seek(0) # Rewind to the beginning of the file
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
        f.truncate() # Remove trailing part if new data is shorter

    # Attempt to get the review - it should be None as it's now expired
    # The get_cached_review method should handle deletion of expired cache.
    assert cache_manager_fixture.get_cached_review(review_request_fixture) is None

    # Verify the cache file was deleted due to expiration
    assert not cache_file_path.exists()

def test_cleanup_expired_cache(
    cache_manager_fixture: CacheManager, # Uses default 1 hour TTL
    review_request_fixture: ReviewRequest,
    review_response_fixture: ReviewResponse
):
    """만료된 캐시 정리 기능을 테스트합니다."""
    # 1. Save a cache entry that is not expired
    review_request_not_expired = review_request_fixture.model_copy(update={"model": "gpt-3.5-turbo"})
    cache_manager_fixture.save_review_to_cache(
        review_request_not_expired, review_response_fixture, EstimatedCost.get_zero_cost("gpt-3.5-turbo"), log_id="test-log-not-expired" # Added EstimatedCost
    )
    cache_key_not_expired = CacheKeyGenerator.generate_cache_key(CacheKeyInfo(
        diff_content=review_request_not_expired.diff_content,
        model=review_request_not_expired.model,
        use_full_context=review_request_not_expired.use_full_context,
    ))
    path_not_expired = cache_manager_fixture._get_cache_file_path(cache_key_not_expired)


    # 2. Save a cache entry and make it expired by modifying its file
    cache_manager_fixture.save_review_to_cache(
        review_request_fixture, review_response_fixture, EstimatedCost.get_zero_cost("gpt-4o"), log_id="test-log-expired-cleanup" # Added EstimatedCost
    )
    cache_key_expired = CacheKeyGenerator.generate_cache_key(CacheKeyInfo(
        diff_content=review_request_fixture.diff_content,
        model=review_request_fixture.model,
        use_full_context=review_request_fixture.use_full_context,
    ))
    path_expired = cache_manager_fixture._get_cache_file_path(cache_key_expired)

    assert path_expired.exists()
    with open(path_expired, 'r+', encoding='utf-8') as f:
        cache_data = json.load(f)
        past_time = datetime.now(timezone.utc) - timedelta(hours=2) # 2 hours in the past
        cache_data['expires_at'] = past_time.isoformat()
        f.seek(0)
        json.dump(cache_data, f, indent=2)
        f.truncate()

    # 3. Call cleanup_expired_cache
    cache_manager_fixture.cleanup_expired_cache()

    # 4. Assertions
    # The expired cache should be deleted
    assert not path_expired.exists(), "Expired cache file should be deleted by cleanup."
    # The non-expired cache should still exist
    assert path_not_expired.exists(), "Non-expired cache file should not be deleted by cleanup."

    # Clean up the non-expired entry as well for subsequent tests
    path_not_expired.unlink(missing_ok=True)
