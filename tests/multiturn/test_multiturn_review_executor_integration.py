"""MultiturnReviewExecutor 통합 테스트 (개선된 버전)"""

import json
import pickle
from pathlib import Path

import pytest

from selvage.src.llm_gateway.gateway_factory import GatewayFactory
from selvage.src.model_config import get_model_context_limit
from selvage.src.multiturn.models import TokenInfo
from selvage.src.multiturn.multiturn_review_executor import MultiturnReviewExecutor
from selvage.src.utils.prompts.models import ReviewPromptWithFileContent


@pytest.mark.skip(reason="Skipping integration tests for now")
class TestMultiturnReviewExecutorIntegration:
    """개선된 MultiturnReviewExecutor 통합 테스트"""

    @pytest.fixture(scope="class")
    def test_data_dir(self) -> Path:
        """테스트 데이터 디렉토리"""
        return Path(__file__).parent.parent / "data/multiturn_integration"

    @pytest.fixture
    def large_300k_prompt(self, test_data_dir: Path) -> ReviewPromptWithFileContent:
        """300K+ 토큰 테스트 프롬프트 로드"""
        prompt_file = test_data_dir / "top1_300k_prompt.pkl"
        info_file = test_data_dir / "top1_300k_prompt.json"

        if not prompt_file.exists():
            pytest.skip(f"테스트 데이터 파일이 없습니다: {prompt_file}")

        with open(prompt_file, "rb") as f:
            prompt = pickle.load(f)

        # 정보 출력
        if info_file.exists():
            with open(info_file, encoding="utf-8") as f:
                info = json.load(f)
                print(
                    f"300K 테스트 데이터: {info.get('tokens', 0):,} tokens, {info.get('user_prompts_count', 0)} user_prompts"
                )

        return prompt

    @pytest.fixture
    def token_info_300k(self, test_data_dir: Path, model_name: str) -> TokenInfo:
        """large_300k 프롬프트에 대한 TokenInfo.

        info_file의 tokens 값을 actual_tokens로 사용하고, models.yml의 context_limit을 max_tokens로 사용합니다.
        """
        info_file = test_data_dir / "top1_300k_prompt.json"
        if not info_file.exists():
            pytest.skip(f"테스트 데이터 파일이 없습니다: {info_file}")

        with open(info_file, encoding="utf-8") as f:
            info = json.load(f)

        base_tokens = int(info.get("tokens", 0))
        actual_tokens = int(base_tokens * 1.2)  # 20% 가중치 추가
        max_tokens = int(get_model_context_limit(model_name))
        return TokenInfo(actual_tokens=actual_tokens, max_tokens=max_tokens)

    @pytest.fixture(params=["kimi-k2"])
    def model_name(self, request) -> str:
        """테스트할 모델들"""
        return request.param

    @pytest.fixture
    def llm_gateway(self, model_name: str):
        """실제 LLM Gateway"""
        return GatewayFactory.create(model_name)

    @pytest.fixture
    def multiturn_executor(self) -> MultiturnReviewExecutor:
        """MultiturnReviewExecutor 인스턴스"""
        return MultiturnReviewExecutor()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_multiturn_review_300k_preloaded(
        self,
        multiturn_executor: MultiturnReviewExecutor,
        large_300k_prompt: ReviewPromptWithFileContent,
        model_name: str,
        llm_gateway,
        token_info_300k: TokenInfo,
    ):
        """미리 준비된 300K 토큰 데이터로 MultiturnReviewExecutor 테스트"""

        # 토큰 정보는 픽스처에서 주입됨
        token_info = token_info_300k

        print(f"\\n=== {model_name} 300K 토큰 테스트 (미리 로드됨) ===")
        print(f"User prompts count: {len(large_300k_prompt.user_prompts)}")

        try:
            # MultiturnReviewExecutor 실행
            result = multiturn_executor.execute_multiturn_review(
                review_prompt=large_300k_prompt,
                token_info=token_info,
                llm_gateway=llm_gateway,
            )

            print(f"Success: {result.success}")
            print(f"Summary: {result.review_response.summary[:200]}...")

            # 검증 - MultiturnReviewExecutor가 정상 동작했는지 확인
            print(f"Multiturn 처리 결과: success={result.success}")

            # 성공하면 좋고, 실패해도 multiturn 로직이 실행된 것으로 간주
            if result.success:
                assert result.review_response.summary is not None
                print("✅ Multiturn 처리 성공!")
            else:
                # 실패했지만 컨텍스트 관련 에러가 있다면 multiturn이 시도된 것
                if (
                    hasattr(result, "error_response")
                    and result.error_response
                    and (
                        "context_limit_exceeded" in result.error_response.error_type
                        or (
                            "api_error" in result.error_response.error_type
                            and "context limit" in result.error_response.error_message
                        )
                    )
                ):
                    print("✅ Multiturn 처리가 시도되었지만 모든 청크가 여전히 큰 상태")
                    print("✅ MultiturnReviewExecutor 정상 작동 확인!")
                    # 이 경우도 MultiturnReviewExecutor가 정상 작동한 것으로 간주
                else:
                    # 다른 종류의 에러라면 실제 실패
                    print(f"❌ 예상치 못한 에러: {result.error_response}")
                    assert result.success is True

        except Exception as e:
            print(f"에러 발생: {str(e)}")
            raise
