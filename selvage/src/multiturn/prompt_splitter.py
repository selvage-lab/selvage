"""프롬프트 분할 담당 클래스"""

import logging
import math

import tiktoken

from selvage.src.utils.prompts.models import UserPromptWithFileContent

logger = logging.getLogger(__name__)


class PromptSplitter:
    """프롬프트 분할 담당 클래스"""

    def __init__(self) -> None:
        """초기화 및 tiktoken encoding 캐시"""
        # tiktoken encoding을 인스턴스 레벨에서 캐시 (성능 최적화)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"tiktoken encoding 초기화 실패: {e}")
            self.encoding = None

    def split_user_prompts(
        self,
        user_prompts: list[UserPromptWithFileContent],
        actual_tokens: int | None,
        max_tokens: int | None,
        max_output_tokens: int = 0,
    ) -> list[list[UserPromptWithFileContent]]:
        """토큰 정보를 기반으로 user_prompts를 분할

        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            actual_tokens: 실제 사용한 토큰 수 (error_response에서 추출)
            max_tokens: 최대 허용 토큰 수 (error_response에서 추출)
            max_output_tokens: 출력용 예약 토큰 수 (기본값: 0)

        Returns:
            분할된 user_prompts 그룹들의 목록

        분할 전략:
        - 토큰 정보 있음: actual_tokens과 max_tokens 비율로 계산하여 분할
        - 토큰 정보 없음: 임의로 반으로 분할 (Gemini 등)
        - overlap 적용: 각 청크에 overlap 개수만큼 이전 청크의 마지막 파일들 포함
        """
        if not user_prompts:
            return []

        # 분할 비율 계산
        if actual_tokens is not None and max_tokens is not None:
            # 토큰 정보 기반 분할
            split_ratio = self._calculate_split_ratio(
                actual_tokens, max_tokens, max_output_tokens
            )
        else:
            # 토큰 정보 없음 - 프롬프트 개수를 기반으로 동적 분할
            split_ratio = max(3, min(len(user_prompts) // 10, 4))

        # 토큰 기반 균등 분배 (context limit 고려)
        chunks, _ = self._distribute_by_text_length(
            user_prompts, split_ratio, max_tokens, max_output_tokens
        )

        return chunks

    def _calculate_split_ratio(
        self, actual_tokens: int, max_tokens: int, max_output_tokens: int = 0
    ) -> int:
        """분할 비율 계산

        Args:
            actual_tokens: 실제 사용한 토큰 수
            max_tokens: 최대 허용 토큰 수
            max_output_tokens: 출력용 예약 토큰 수

        Returns:
            분할할 청크 개수
        """
        # System prompt 토큰(약 5,000)과 출력 토큰을 제외한 후 여유분 20% 확보하여 계산
        system_prompt_tokens = 5000
        available_tokens = max_tokens - max_output_tokens - system_prompt_tokens
        safe_max_tokens = available_tokens * 0.8

        # safe 범위 이하면 분할 없이 단일 처리
        if actual_tokens <= safe_max_tokens:
            return 1

        raw_split_ratio = actual_tokens / safe_max_tokens
        split_ratio = math.ceil(raw_split_ratio)

        return split_ratio

    def _distribute_by_text_length(
        self,
        user_prompts: list[UserPromptWithFileContent],
        target_chunks: int,
        max_tokens: int | None = None,
        max_output_tokens: int = 0,
    ) -> tuple[list[list[UserPromptWithFileContent]], list[int]]:
        """토큰 기반 그리디 균등 분배 (overlap=0, context limit 고려)

        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            target_chunks: 목표 청크 개수
            max_tokens: 최대 허용 토큰 수 (context limit)
            max_output_tokens: 출력용 예약 토큰 수

        Returns:
            (분할된 청크들, 각 청크의 토큰 수)
        """
        if not user_prompts:
            return [], []

        # Context limit 계산: 청크당 허용 토큰 수
        # System prompt를 위한 여유분(약 5,000토큰)과 안전 여유분 확보
        chunk_limit = None
        if max_tokens is not None:
            # System prompt 예상 토큰: 5,000
            # 안전 여유분: 20%
            system_prompt_tokens = 5000
            available_tokens = max_tokens - max_output_tokens - system_prompt_tokens
            chunk_limit = int(available_tokens * 0.8)

        # 1. 각 프롬프트의 토큰 수 계산
        prompt_with_tokens = []

        for prompt in user_prompts:
            estimated_tokens = self._calculate_prompt_tokens(prompt)
            prompt_with_tokens.append((prompt, estimated_tokens))

        # 2. 크기 순 정렬 (큰 것부터)
        prompt_with_tokens.sort(key=lambda x: x[1], reverse=True)

        # 3. 빈 청크들 초기화
        chunks = [[] for _ in range(target_chunks)]
        chunk_token_counts = [0] * target_chunks

        # 4. 각 프롬프트를 context limit을 고려하여 배치
        for prompt, token_count in prompt_with_tokens:
            # Context limit을 초과하지 않는 가장 작은 청크 찾기
            valid_chunks = []
            for i, current_count in enumerate(chunk_token_counts):
                if chunk_limit is None or (current_count + token_count <= chunk_limit):
                    valid_chunks.append((i, current_count))

            if valid_chunks:
                # 가장 작은 청크에 배치
                min_chunk_idx = min(valid_chunks, key=lambda x: x[1])[0]
                chunks[min_chunk_idx].append(prompt)
                chunk_token_counts[min_chunk_idx] += token_count
            else:
                # 모든 청크가 제한을 초과하는 경우 - 새로운 청크 생성
                chunks.append([prompt])
                chunk_token_counts.append(token_count)

        return chunks, chunk_token_counts

    def _calculate_prompt_tokens(self, prompt: UserPromptWithFileContent) -> int:
        """tiktoken을 사용하여 프롬프트의 토큰 수를 계산합니다.

        Args:
            prompt: 토큰 수를 계산할 프롬프트

        Returns:
            추정 토큰 수
        """
        try:
            # 캐시된 encoding 사용
            if self.encoding is None:
                # encoding 초기화가 실패한 경우 fallback으로 이동
                return self._fallback_estimate_tokens(prompt)

            encoding = self.encoding

            # file_context 토큰 계산
            context_content = prompt.file_context.context
            context_tokens = (
                len(encoding.encode(str(context_content))) if context_content else 0
            )

            # formatted_hunks 토큰 계산
            hunks_tokens = 0
            for hunk in prompt.formatted_hunks:
                # before_code와 after_code의 실제 텍스트 내용으로 토큰 계산
                hunk_text = hunk.before_code + hunk.after_code
                hunks_tokens += len(encoding.encode(hunk_text))

            total_tokens = context_tokens + hunks_tokens
            return total_tokens

        except Exception as e:
            logger.warning(f"tiktoken 토큰 계산 실패, fallback 사용: {e}")
            # Fallback: 문자열 길이 기반 추정
            return self._fallback_estimate_tokens(prompt)

    def _fallback_estimate_tokens(self, prompt: UserPromptWithFileContent) -> int:
        """토큰 계산 실패 시 문자열 길이 기반 fallback 추정

        Args:
            prompt: 토큰 수를 계산할 프롬프트

        Returns:
            추정 토큰 수 (문자열 길이 기반)
        """
        # file_context 크기
        context_content = prompt.file_context.context
        context_size = len(str(context_content)) if context_content else 0

        # formatted_hunks의 실제 내용 크기 계산
        hunks_size = 0
        for hunk in prompt.formatted_hunks:
            hunks_size += len(hunk.before_code) + len(hunk.after_code)

        total_chars = context_size + hunks_size

        # 대략적인 토큰 변환 비율 (영어 기준 1토큰 ≈ 4자,
        # 코드에서는 토큰 밀도가 높으므로 3.5로 설정)
        estimated_tokens = int(total_chars / 3.5)
        return estimated_tokens

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
