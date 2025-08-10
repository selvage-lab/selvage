"""멀티턴 리뷰 실행기"""

import concurrent.futures

from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.prompts.models import (
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.token.models import EstimatedCost, ReviewResponse
from selvage.src.utils.token.token_utils import TokenUtils

from .models import TokenInfo
from .prompt_splitter import PromptSplitter


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

        # 디버깅: 입력 파라미터 로깅
        print("🔍 [DEBUG] MultiturnReviewExecutor 입력:")
        print(f"   - Model: {llm_gateway.get_model_name()}")
        print(f"   - Provider: {llm_gateway.get_provider().value}")
        print(f"   - actual_tokens: {token_info.actual_tokens:,}")
        print(f"   - max_tokens: {token_info.max_tokens:,}")
        print(f"   - user_prompts count: {len(review_prompt.user_prompts)}")

        # 1. user_prompts 분할 (system_prompt는 공통 사용)
        user_prompt_chunks = self.prompt_splitter.split_user_prompts(
            user_prompts=review_prompt.user_prompts,
            actual_tokens=token_info.actual_tokens,
            max_tokens=token_info.max_tokens,
            overlap=0,
        )

        # 디버깅: 분할 결과 로깅
        print("🔍 [DEBUG] 분할 결과:")
        print(f"   - 총 청크 개수: {len(user_prompt_chunks)}")
        for i, chunk in enumerate(user_prompt_chunks):
            print(f"   - 청크 {i}: {len(chunk)} user_prompts")

            # 각 청크의 실제 토큰 수 계산
            chunk_prompt = ReviewPromptWithFileContent(
                system_prompt=review_prompt.system_prompt, user_prompts=chunk
            )
            chunk_tokens = TokenUtils.count_tokens(
                chunk_prompt, llm_gateway.get_model_name()
            )
            print(f"     → 실제 토큰 수: {chunk_tokens:,}")
            status_text = "초과" if chunk_tokens > token_info.max_tokens else "안전"
            print(f"     -> {token_info.max_tokens} 한계 {status_text}")
        print()

        # 2. 순차 API 호출 (OpenRouter 동시성 문제 해결)
        review_results = self._execute_sequential_reviews(
            user_prompt_chunks, review_prompt.system_prompt, llm_gateway
        )

        # 3. 결과 간단 병합
        merged_result = self._merge_review_results(review_results)

        return merged_result

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

        print(f"🔄 [DEBUG] 순차 처리 시작: {len(user_prompt_chunks)}개 청크")

        for i, chunk in enumerate(user_prompt_chunks):
            print(f"🔄 [DEBUG] 청크 {i + 1}/{len(user_prompt_chunks)} 순차 처리 시작")

            chunk_review_prompt = ReviewPromptWithFileContent(
                system_prompt=system_prompt, user_prompts=chunk
            )

            try:
                result = llm_gateway.review_code(chunk_review_prompt)
                review_results.append(result)
                print(f"✅ [DEBUG] 청크 {i + 1} 처리 성공")
            except Exception as e:
                # 개별 청크 실패 시 에러 결과 생성
                error_result = ReviewResult.get_error_result(
                    error=e,
                    model=llm_gateway.get_model_name(),
                    provider=llm_gateway.get_provider().value,
                )
                review_results.append(error_result)
                print(f"❌ [DEBUG] 청크 {i + 1} 처리 실패: {str(e)}")

        print(f"🔄 [DEBUG] 순차 처리 완료: {len(review_results)}개 결과")
        return review_results

    def _merge_review_results(self, review_results: list[ReviewResult]) -> ReviewResult:
        """CR-18 구현을 위한 **최소 기능 구현(MVP)**이며,
        CR-19에서 ReviewSynthesizer로 완전히 교체될 예정
        """
        if not review_results:
            return ReviewResult.get_empty_result("unknown")

        # 실패한 결과가 있는지 확인
        failed_results = [r for r in review_results if not r.success]
        if failed_results:
            # 첫 번째 실패 결과를 반환
            return failed_results[0]

        # 성공한 결과들을 합성
        successful_results = [r for r in review_results if r.success]
        if not successful_results:
            return ReviewResult.get_empty_result("unknown")

        # 내용 합성
        merged_summary_parts = []
        all_recommendations = []
        all_issues = []
        total_cost = EstimatedCost.get_zero_cost("merged")

        for result in successful_results:
            if result.review_response.summary:
                merged_summary_parts.append(result.review_response.summary)
            all_recommendations.extend(result.review_response.recommendations)
            all_issues.extend(result.review_response.issues)

            # 비용 합산
            total_cost = EstimatedCost(
                model=result.estimated_cost.model,
                input_cost_usd=total_cost.input_cost_usd
                + result.estimated_cost.input_cost_usd,
                output_cost_usd=total_cost.output_cost_usd
                + result.estimated_cost.output_cost_usd,
                total_cost_usd=total_cost.total_cost_usd
                + result.estimated_cost.total_cost_usd,
                input_tokens=total_cost.input_tokens
                + result.estimated_cost.input_tokens,
                output_tokens=total_cost.output_tokens
                + result.estimated_cost.output_tokens,
            )

        # 합성된 ReviewResponse 생성
        merged_review_response = ReviewResponse(
            summary="\n\n".join(merged_summary_parts) if merged_summary_parts else "",
            recommendations=all_recommendations,
            issues=all_issues,
            score=successful_results[0].review_response.score,
        )

        return ReviewResult.get_success_result(
            review_response=merged_review_response, estimated_cost=total_cost
        )
