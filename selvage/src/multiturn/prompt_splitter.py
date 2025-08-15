"""프롬프트 분할 담당 클래스"""

import logging
import math

from selvage.src.utils.prompts.models import UserPromptWithFileContent

logger = logging.getLogger(__name__)


class PromptSplitter:
    """프롬프트 분할 담당 클래스"""

    def split_user_prompts(
        self,
        user_prompts: list[UserPromptWithFileContent],
        actual_tokens: int | None,
        max_tokens: int | None,
    ) -> list[list[UserPromptWithFileContent]]:
        """토큰 정보를 기반으로 user_prompts를 분할

        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            actual_tokens: 실제 사용한 토큰 수 (error_response에서 추출)
            max_tokens: 최대 허용 토큰 수 (error_response에서 추출)

        Returns:
            분할된 user_prompts 그룹들의 목록

        분할 전략:
        - 토큰 정보 있음: actual_tokens과 max_tokens 비율로 계산하여 분할
        - 토큰 정보 없음: 임의로 반으로 분할 (Gemini 등)
        - overlap 적용: 각 청크에 overlap 개수만큼 이전 청크의 마지막 파일들 포함
        """
        if not user_prompts:
            return []

        logger.debug("PromptSplitter 분할 시작")
        logger.debug(f"user_prompts 개수: {len(user_prompts)}")
        logger.debug(
            f"actual_tokens: {actual_tokens:,}"
            if actual_tokens
            else "actual_tokens: None"
        )

        # 분할 비율 계산
        if actual_tokens is not None and max_tokens is not None:
            # 토큰 정보 기반 분할
            split_ratio = self._calculate_split_ratio(actual_tokens, max_tokens)
        else:
            # 토큰 정보 없음 - 프롬프트 개수를 기반으로 동적 분할
            split_ratio = max(2, min(len(user_prompts) // 10, 4))

        logger.debug(f"분할 비율: {split_ratio}")

        # 텍스트 길이 기반 균등 분배 (현재 구현에서는 overlap 미적용)
        chunks, _ = self._distribute_by_text_length(user_prompts, split_ratio)

        logger.debug(f"PromptSplitter 분할 완료: {len(chunks)}개 청크 생성")
        return chunks

    def _calculate_split_ratio(self, actual_tokens: int, max_tokens: int) -> int:
        """분할 비율 계산

        Args:
            actual_tokens: 실제 사용한 토큰 수
            max_tokens: 최대 허용 토큰 수

        Returns:
            분할할 청크 개수
        """
        # 여유분 20% 확보하여 계산
        safe_max_tokens = max_tokens * 0.8

        # safe 범위 이하면 분할 없이 단일 처리
        if actual_tokens <= safe_max_tokens:
            logger.debug("토큰 safe 범위 이내 -> 단일 처리")
            return 1

        raw_split_ratio = actual_tokens / safe_max_tokens
        split_ratio = math.ceil(raw_split_ratio)
        final_split_ratio = max(2, split_ratio)  # 최소 2개로 분할 (초과/근접시)

        logger.debug(
            f"분할 비율 계산: {actual_tokens:,}/{max_tokens:,} ->"
            f"{final_split_ratio}개 청크"
        )

        return final_split_ratio

    def _distribute_by_text_length(
        self, user_prompts: list[UserPromptWithFileContent], target_chunks: int
    ) -> tuple[list[list[UserPromptWithFileContent]], list[int]]:
        """텍스트 길이 기반 그리디 균등 분배 (overlap=0)

        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            target_chunks: 목표 청크 개수

        Returns:
            (분할된 청크들, 각 청크의 텍스트 길이)
        """
        if not user_prompts:
            return [], []

        # 1. 각 프롬프트의 상대적 크기 계산 (빠른 추정)
        # file_context 길이 + formatted_hunks 개수로 상대적 크기 추정
        prompt_with_sizes = []
        for prompt in user_prompts:
            # FileContextInfo의 텍스트 길이 + formatted_hunks 개수 * 평균 크기
            context_content = prompt.file_context.context
            context_size = len(str(context_content)) if context_content else 0
            hunks_size = len(prompt.formatted_hunks) * 500  # 평균 500자로 추정
            estimated_size = context_size + hunks_size
            prompt_with_sizes.append((prompt, estimated_size))

        # 2. 크기 순 정렬 (큰 것부터)
        prompt_with_sizes.sort(key=lambda x: x[1], reverse=True)

        # 3. 빈 청크들 초기화
        chunks = [[] for _ in range(target_chunks)]
        chunk_text_lengths = [0] * target_chunks

        total_text_length = sum(size for _, size in prompt_with_sizes)
        logger.debug(
            f"텍스트 길이 기반 분배: {total_text_length:,} chars -> "
            f"{target_chunks}개 청크"
        )

        # 4. 각 프롬프트를 가장 작은 청크에 배치 (그리디 알고리즘)
        for prompt, text_length in prompt_with_sizes:
            min_chunk_idx = chunk_text_lengths.index(min(chunk_text_lengths))
            chunks[min_chunk_idx].append(prompt)
            chunk_text_lengths[min_chunk_idx] += text_length

        return chunks, chunk_text_lengths

    def _apply_overlap(
        self,
        chunks: list[list[UserPromptWithFileContent]],
        overlap: int,
    ) -> list[list[UserPromptWithFileContent]]:
        """분할된 청크에 overlap 적용

        Args:
            chunks: 분할된 청크 목록
            overlap: 겹치는 파일 개수

        Returns:
            overlap이 적용된 청크 목록
        """
        if overlap <= 0 or len(chunks) <= 1:
            return chunks

        result_chunks = [chunks[0]]  # 첫 번째 청크는 그대로

        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            prev_chunk = chunks[i - 1]

            # 이전 청크의 마지막 overlap 개수만큼 현재 청크 앞에 추가
            if len(prev_chunk) >= overlap:
                overlap_items = prev_chunk[-overlap:]
                new_chunk = overlap_items + current_chunk
                result_chunks.append(new_chunk)
            else:
                # 이전 청크가 overlap보다 작으면 이전 청크 전체를 추가
                overlap_items = prev_chunk
                new_chunk = overlap_items + current_chunk
                result_chunks.append(new_chunk)

        return result_chunks
