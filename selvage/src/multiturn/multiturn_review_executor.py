"""멀티턴 리뷰 실행기"""

import concurrent.futures

from deprecated import deprecated

from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.prompts.models import (
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)

from .models import TokenInfo
from .prompt_splitter import PromptSplitter
from .review_synthesizer import ReviewSynthesizer


class MultiturnReviewExecutor:
    """Multiturn Review 메인 실행기"""

    def __init__(self) -> None:
        self.prompt_splitter = PromptSplitter()

    def execute_multiturn_review(
        self,
        review_prompt: ReviewPromptWithFileContent,
        token_info: TokenInfo,
        llm_gateway: BaseGateway,
    ) -> ReviewResult:
        """
        Context limit 초과 시 프롬프트를 분할하여 병렬 처리 후 결과 합성

        Args:
            review_prompt: 이미 생성된 리뷰 프롬프트 (cli.py:L383에서 생성)
            token_info: 토큰 정보 (actual_tokens, max_tokens)
            llm_gateway: LLM API 호출 게이트웨이

        Returns:
            ReviewResult: 합성된 최종 리뷰 결과
        """
        # 빈 user_prompts 처리
        if not review_prompt.user_prompts:
            return ReviewResult.get_empty_result(llm_gateway.get_model_name())

        console.info("Large context 처리 시작")

        # 1. user_prompts 분할 (system_prompt는 공통 사용)
        user_prompt_chunks = self.prompt_splitter.split_user_prompts(
            user_prompts=review_prompt.user_prompts,
            actual_tokens=token_info.actual_tokens,
            max_tokens=token_info.max_tokens,
            overlap=0,
        )

        # 2. 순차 API 호출 (OpenRouter 동시성 문제 해결)
        review_results = self._execute_sequential_reviews(
            user_prompt_chunks, review_prompt.system_prompt, llm_gateway
        )

        # 3. 결과 지능적 합성 (ReviewSynthesizer 사용)
        synthesizer = ReviewSynthesizer(llm_gateway.get_model_name())
        merged_result = synthesizer.synthesize_review_results(review_results)

        console.info("Large context 처리 완료")
        return merged_result

    @deprecated(reason="Use _execute_sequential_reviews instead")
    def _execute_parallel_reviews(
        self,
        user_prompt_chunks: list[list[UserPromptWithFileContent]],
        system_prompt: SystemPrompt,
        llm_gateway: BaseGateway,
    ) -> list[ReviewResult]:
        """분할된 청크들에 대한 병렬 API 호출"""
        review_results: list[ReviewResult] = []

        # ThreadPoolExecutor를 사용한 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 각 청크에 대해 리뷰 요청 생성
            future_to_chunk = {}
            for chunk in user_prompt_chunks:
                chunk_review_prompt = ReviewPromptWithFileContent(
                    system_prompt=system_prompt, user_prompts=chunk
                )
                future = executor.submit(llm_gateway.review_code, chunk_review_prompt)
                future_to_chunk[future] = chunk

            # 결과 수집
            for future in concurrent.futures.as_completed(future_to_chunk):
                try:
                    result = future.result()
                    review_results.append(result)
                except Exception as e:
                    # 개별 청크 실패 시 에러 결과 생성
                    error_result = ReviewResult.get_error_result(
                        error=e,
                        model=llm_gateway.get_model_name(),
                        provider=llm_gateway.get_provider().value,
                    )
                    review_results.append(error_result)

        return review_results

    def _execute_sequential_reviews(
        self,
        user_prompt_chunks: list[list[UserPromptWithFileContent]],
        system_prompt: SystemPrompt,
        llm_gateway: BaseGateway,
    ) -> list[ReviewResult]:
        """분할된 청크들에 대한 순차 API 호출 (OpenRouter 동시성 문제 해결)"""
        review_results: list[ReviewResult] = []

        for chunk in user_prompt_chunks:
            chunk_review_prompt = ReviewPromptWithFileContent(
                system_prompt=system_prompt, user_prompts=chunk
            )

            try:
                result = llm_gateway.review_code(chunk_review_prompt)
                review_results.append(result)
            except Exception as e:
                # 개별 청크 실패 시 에러 결과 생성
                error_result = ReviewResult.get_error_result(
                    error=e,
                    model=llm_gateway.get_model_name(),
                    provider=llm_gateway.get_provider().value,
                )
                review_results.append(error_result)

        return review_results
