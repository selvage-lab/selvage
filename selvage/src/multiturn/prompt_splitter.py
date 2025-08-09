"""프롬프트 분할 담당 클래스"""

import math

from selvage.src.utils.prompts.models import UserPromptWithFileContent


class PromptSplitter:
    """프롬프트 분할 담당 클래스"""

    def split_user_prompts(
        self,
        user_prompts: list[UserPromptWithFileContent],
        actual_tokens: int | None,
        max_tokens: int | None,
        overlap: int = 1,
    ) -> list[list[UserPromptWithFileContent]]:
        """토큰 정보를 기반으로 user_prompts를 분할

        Args:
            user_prompts: 분할할 사용자 프롬프트 목록
            actual_tokens: 실제 사용한 토큰 수 (error_response에서 추출)
            max_tokens: 최대 허용 토큰 수 (error_response에서 추출)
            overlap: 분할된 청크간 겹치는 파일 개수 (기본값: 1)

        Returns:
            분할된 user_prompts 그룹들의 목록

        분할 전략:
        - 토큰 정보 있음: actual_tokens과 max_tokens 비율로 계산하여 분할
        - 토큰 정보 없음: 임의로 반으로 분할 (Gemini 등)
        - overlap 적용: 각 청크에 overlap 개수만큼 이전 청크의 마지막 파일들 포함
        """
        if not user_prompts:
            return []

        print("[DEBUG] PromptSplitter 분할 시작:")
        print(f"   - user_prompts 개수: {len(user_prompts)}")
        print(
            f"   - actual_tokens: {actual_tokens:,}"
            if actual_tokens
            else "   - actual_tokens: None"
        )
        print(
            f"   - max_tokens: {max_tokens:,}"
            if max_tokens
            else "   - max_tokens: None"
        )
        print(f"   - overlap: {overlap}")

        # 분할 비율 계산
        if actual_tokens is not None and max_tokens is not None:
            # 토큰 정보 기반 분할
            split_ratio = self._calculate_split_ratio(actual_tokens, max_tokens)
        else:
            # 토큰 정보 없음 - 기본적으로 반으로 분할
            split_ratio = 2

        print("[DEBUG] 분할 비율 계산 완료:")
        print(f"   - split_ratio: {split_ratio}")

        # 텍스트 길이 기반 균등 분배 (현재 구현에서는 overlap 미적용)
        chunks, _ = self._distribute_by_text_length(user_prompts, split_ratio)

        print(
            f"[DEBUG] PromptSplitter 분할 완료: {len(chunks)}개 청크 생성 "
            f"(overlap 비적용)"
        )
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
            print("[DEBUG] _calculate_split_ratio: safe 범위 이내 -> 1개로 처리")
            print(f"   - actual_tokens: {actual_tokens:,}")
            print(f"   - max_tokens: {max_tokens:,}")
            print(f"   - safe_max_tokens: {safe_max_tokens:,} (= max_tokens * 0.8)")
            return 1

        raw_split_ratio = actual_tokens / safe_max_tokens
        split_ratio = math.ceil(raw_split_ratio)
        final_split_ratio = max(2, split_ratio)  # 최소 2개로 분할 (초과/근접시)

        print("[DEBUG] _calculate_split_ratio 계산:")
        print(f"   - actual_tokens: {actual_tokens:,}")
        print(f"   - max_tokens: {max_tokens:,}")
        print(f"   - safe_max_tokens: {safe_max_tokens:,} (= max_tokens * 0.8)")
        print(f"   - raw_split_ratio: {raw_split_ratio:.2f}")
        print(f"   - split_ratio: {split_ratio} (= math.ceil({raw_split_ratio:.2f}))")
        print(f"   - final_split_ratio: {final_split_ratio} (= max(2, {split_ratio}))")

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

        print("[DEBUG] 텍스트 길이 기반 균등 분배:")
        total_text_length = sum(size for _, size in prompt_with_sizes)
        print(f"   - 총 텍스트 길이: {total_text_length:,} chars")
        print(f"   - 목표 청크 수: {target_chunks}")
        avg_chunk_size = total_text_length // target_chunks
        print(f"   - 평균 청크 크기: {avg_chunk_size:,} chars")

        # 4. 각 프롬프트를 가장 작은 청크에 배치 (그리디 알고리즘)
        for prompt, text_length in prompt_with_sizes:
            min_chunk_idx = chunk_text_lengths.index(min(chunk_text_lengths))
            chunks[min_chunk_idx].append(prompt)
            chunk_text_lengths[min_chunk_idx] += text_length

        # 디버깅: 분배 결과 출력
        for i, (chunk, chunk_length) in enumerate(
            zip(chunks, chunk_text_lengths, strict=True)
        ):
            # 대략 추정 (chars * 0.75 ≈ tokens)
            estimated_tokens = int(chunk_length * 0.75)
            print(f"   - 청크 {i}: {len(chunk)} prompts")
            print(f"     -> 텍스트 길이: {chunk_length:,} chars")
            print(f"     -> 예상 토큰: ~{estimated_tokens:,}")

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
