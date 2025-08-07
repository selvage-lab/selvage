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

        # 분할 비율 계산
        if actual_tokens is not None and max_tokens is not None:
            # 토큰 정보 기반 분할
            split_ratio = self._calculate_split_ratio(actual_tokens, max_tokens)
        else:
            # 토큰 정보 없음 - 기본적으로 반으로 분할
            split_ratio = 2

        # user_prompts를 split_ratio 개수만큼 균등 분할
        chunks = []
        chunk_size = max(1, len(user_prompts) // split_ratio)

        for i in range(0, len(user_prompts), chunk_size):
            chunk = user_prompts[i : i + chunk_size]
            if chunk:  # 빈 청크 방지
                chunks.append(chunk)

        # split_ratio보다 많은 청크가 생성된 경우 마지막 청크들을 합침
        while len(chunks) > split_ratio and len(chunks) > 1:
            last_chunk = chunks.pop()
            chunks[-1].extend(last_chunk)

        # overlap 적용
        if overlap > 0:
            chunks = self._apply_overlap(chunks, overlap)

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
        split_ratio = math.ceil(actual_tokens / safe_max_tokens)
        return max(2, split_ratio)  # 최소 2개로 분할

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
