"""MultiturnReviewExecutor 테스트"""

from unittest.mock import Mock

import pytest

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.models.hunk import Hunk
from selvage.src.models.error_response import ErrorResponse
from selvage.src.models.review_result import ReviewResult
from selvage.src.multiturn.models import TokenInfo
from selvage.src.multiturn.multiturn_review_executor import MultiturnReviewExecutor
from selvage.src.utils.prompts.models import (
    FileContextInfo,
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.token.models import EstimatedCost, ReviewResponse


class TestMultiturnReviewExecutor:
    """MultiturnReviewExecutor 클래스 테스트"""

    @pytest.fixture
    def sample_user_prompts(self) -> list[UserPromptWithFileContent]:
        """테스트용 UserPromptWithFileContent 리스트 생성"""
        hunks = [
            Hunk(
                header="@@ -1,3 +1,4 @@",
                content="+print('Hello')\n print('World')\n",
                before_code="print('World')\n",
                after_code="print('Hello')\nprint('World')\n",
                start_line_original=1,
                line_count_original=3,
                start_line_modified=1,
                line_count_modified=4,
                change_line=LineRange(start_line=1, end_line=4),
            )
        ]

        user_prompts = []
        for i in range(4):
            user_prompt = UserPromptWithFileContent(
                file_name=f"file_{i}.py",
                file_context=FileContextInfo.create_full_context(f"file {i} content"),
                hunks=hunks,
                language="python",
            )
            user_prompts.append(user_prompt)

        return user_prompts

    @pytest.fixture
    def sample_review_prompt_with_file_content(
        self, sample_user_prompts: list[UserPromptWithFileContent]
    ) -> ReviewPromptWithFileContent:
        """테스트용 ReviewPromptWithFileContent 생성"""
        system_prompt = SystemPrompt(
            role="system", content="You are a code review assistant."
        )
        return ReviewPromptWithFileContent(
            system_prompt=system_prompt, user_prompts=sample_user_prompts
        )

    @pytest.fixture
    def sample_token_info_with_tokens(self) -> TokenInfo:
        """토큰 정보가 있는 TokenInfo 생성"""
        return TokenInfo(actual_tokens=150000, max_tokens=100000)

    @pytest.fixture
    def sample_token_info_without_tokens(self) -> TokenInfo:
        """토큰 정보가 없는 TokenInfo 생성"""
        return TokenInfo.empty()

    @pytest.fixture
    def sample_error_response_with_tokens(self) -> ErrorResponse:
        """토큰 정보가 있는 ErrorResponse 생성 (TokenInfo 테스트용)"""
        return ErrorResponse(
            error_type="context_limit_exceeded",
            error_code="context_length_exceeded",
            error_message="Context limit exceeded",
            provider="openai",
            raw_error={"actual_tokens": 150000, "max_tokens": 100000},
        )

    @pytest.fixture
    def sample_error_response_without_tokens(self) -> ErrorResponse:
        """토큰 정보가 없는 ErrorResponse 생성 (TokenInfo 테스트용)"""
        return ErrorResponse(
            error_type="context_limit_exceeded",
            error_code="context_length_exceeded",
            error_message="Context limit exceeded",
            provider="gemini",
            raw_error={},
        )

    @pytest.fixture
    def mock_llm_gateway(self) -> Mock:
        """Mock BaseGateway 생성"""
        gateway = Mock()
        gateway.get_model_name.return_value = "mock-model"
        gateway.get_provider.return_value = Mock(value="mock-provider")
        # 성공적인 ReviewResult 반환 설정
        gateway.review_code.return_value = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="Mock summary",
                issues=[],
                recommendations=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("mock-model"),
        )
        return gateway

    @pytest.fixture
    def sample_review_results(self) -> list[ReviewResult]:
        """테스트용 ReviewResult 리스트 생성"""
        results = []
        for i in range(2):
            result = ReviewResult.get_success_result(
                review_response=ReviewResponse(
                    summary=f"Summary {i}",
                    issues=[],
                    recommendations=[f"Recommendation {i}"],
                ),
                estimated_cost=EstimatedCost.get_zero_cost("test-model"),
            )
            results.append(result)
        return results

    @pytest.fixture
    def multiturn_executor(self) -> MultiturnReviewExecutor:
        """MultiturnReviewExecutor 인스턴스 생성"""
        return MultiturnReviewExecutor()

    def test_execute_multiturn_review_success(
        self,
        multiturn_executor: MultiturnReviewExecutor,
        sample_review_prompt_with_file_content: ReviewPromptWithFileContent,
        sample_token_info_with_tokens: TokenInfo,
        mock_llm_gateway: Mock,
    ) -> None:
        """토큰 정보가 있을 때 성공적인 multiturn 리뷰 실행 테스트"""
        # Given: 토큰 정보가 있는 TokenInfo와 프롬프트
        # When: multiturn 리뷰 실행
        result = multiturn_executor.execute_multiturn_review(
            review_prompt=sample_review_prompt_with_file_content,
            token_info=sample_token_info_with_tokens,
            llm_gateway=mock_llm_gateway,
        )

        # Then: 성공적인 결과 반환
        assert result.success is True
        assert result.review_response.summary is not None
        # Gateway가 여러 번 호출되어야 함 (분할된 청크 수만큼)
        assert mock_llm_gateway.review_code.call_count >= 1

    def test_execute_multiturn_review_no_token_info(
        self,
        multiturn_executor: MultiturnReviewExecutor,
        sample_review_prompt_with_file_content: ReviewPromptWithFileContent,
        sample_token_info_without_tokens: TokenInfo,
        mock_llm_gateway: Mock,
    ) -> None:
        """토큰 정보가 없을 때 기본 분할로 실행 테스트"""
        # Given: 토큰 정보가 없는 TokenInfo
        # When: multiturn 리뷰 실행
        result = multiturn_executor.execute_multiturn_review(
            review_prompt=sample_review_prompt_with_file_content,
            token_info=sample_token_info_without_tokens,
            llm_gateway=mock_llm_gateway,
        )

        # Then: 기본 분할로 실행되어야 함
        assert result.success is True
        assert mock_llm_gateway.review_code.call_count >= 1

    def test_token_info_from_error_response_with_tokens(
        self, sample_error_response_with_tokens: ErrorResponse
    ) -> None:
        """ErrorResponse에서 토큰 정보 추출 성공 테스트"""
        # When: TokenInfo.from_error_response로 토큰 정보 추출
        token_info = TokenInfo.from_error_response(sample_error_response_with_tokens)

        # Then: 올바른 토큰 정보 반환
        assert token_info.actual_tokens == 150000
        assert token_info.max_tokens == 100000

    def test_token_info_from_error_response_without_tokens(
        self, sample_error_response_without_tokens: ErrorResponse
    ) -> None:
        """토큰 정보가 없을 때 None 반환 테스트"""
        # When: TokenInfo.from_error_response로 토큰 정보 추출
        token_info = TokenInfo.from_error_response(sample_error_response_without_tokens)

        # Then: None 반환
        assert token_info.actual_tokens is None
        assert token_info.max_tokens is None

    def test_token_info_empty(self) -> None:
        """TokenInfo.empty() 테스트"""
        # When: 빈 토큰 정보 생성
        token_info = TokenInfo.empty()

        # Then: 모든 값이 None
        assert token_info.actual_tokens is None
        assert token_info.max_tokens is None

    def test_parallel_api_calls(
        self,
        multiturn_executor: MultiturnReviewExecutor,
        sample_user_prompts: list[UserPromptWithFileContent],
        mock_llm_gateway: Mock,
    ) -> None:
        """분할된 청크들에 대한 병렬 API 호출 테스트"""
        # Given: 분할된 청크들
        system_prompt = SystemPrompt(
            role="system", content="You are a code review assistant."
        )
        chunks = [sample_user_prompts[:2], sample_user_prompts[2:]]

        # When: 병렬 API 호출 실행
        results = multiturn_executor._execute_parallel_reviews(
            chunks, system_prompt, mock_llm_gateway
        )

        # Then: 각 청크마다 결과 반환
        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_llm_gateway.review_code.call_count == 2

    def test_result_synthesizing_with_synthesizer(
        self,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """ReviewSynthesizer를 통한 여러 ReviewResult 합성 테스트"""
        from selvage.src.multiturn.review_synthesizer import ReviewSynthesizer
        
        # Given: ReviewSynthesizer 인스턴스
        synthesizer = ReviewSynthesizer(mock_llm_gateway.get_model_name())
        
        # When: 결과 합성
        merged_result = synthesizer.synthesize_review_results(sample_review_results)

        # Then: 합성된 결과 반환
        assert merged_result.success is True
        assert merged_result.review_response.summary is not None
        assert len(merged_result.review_response.recommendations) >= 0

    def test_empty_user_prompts(
        self,
        multiturn_executor: MultiturnReviewExecutor,
        sample_token_info_with_tokens: TokenInfo,
        mock_llm_gateway: Mock,
    ) -> None:
        """빈 user_prompts 처리 테스트"""
        # Given: 빈 user_prompts
        empty_review_prompt = ReviewPromptWithFileContent(
            system_prompt=SystemPrompt(
                role="system", content="You are a code review assistant."
            ),
            user_prompts=[],
        )

        # When: multiturn 리뷰 실행
        result = multiturn_executor.execute_multiturn_review(
            review_prompt=empty_review_prompt,
            token_info=sample_token_info_with_tokens,
            llm_gateway=mock_llm_gateway,
        )

        # Then: 빈 결과 반환
        assert result.success is True
        # Gateway 호출되지 않아야 함
        assert mock_llm_gateway.review_code.call_count == 0
