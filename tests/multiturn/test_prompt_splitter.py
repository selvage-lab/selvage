"""PromptSplitter 테스트"""

import math

import pytest

from selvage.src.context_extractor.line_range import LineRange
from selvage.src.diff_parser.models.hunk import Hunk
from selvage.src.multiturn.prompt_splitter import PromptSplitter
from selvage.src.utils.prompts.models import FileContextInfo, UserPromptWithFileContent


class TestPromptSplitter:
    """PromptSplitter 클래스 테스트"""

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
    def prompt_splitter(self) -> PromptSplitter:
        """PromptSplitter 인스턴스 생성"""
        return PromptSplitter()

    def test_split_with_token_info(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """토큰 정보가 있을 때 분할 테스트"""
        # Given: 4개 파일, actual_tokens=150000, max_tokens=100000
        actual_tokens = 150000
        max_tokens = 100000

        # When: 토큰 기반 분할 실행
        result = prompt_splitter.split_user_prompts(
            user_prompts=sample_user_prompts,
            actual_tokens=actual_tokens,
            max_tokens=max_tokens,
            max_output_tokens=0,
        )

        # Then: 3개 청크로 분할되어야 함
        # (150000 / (100000 * 0.8) = 1.875 -> max(3, int(1.875)) = max(3, 1) = 3)
        assert len(result) == 3
        # 각 청크가 비어있지 않아야 함
        for chunk in result:
            assert len(chunk) > 0
        # overlap 비적용: 모든 청크 간 파일이 겹치지 않아야 함
        all_files = []
        for chunk in result:
            all_files.extend([p.file_name for p in chunk])
        assert len(all_files) == len(set(all_files))

    def test_split_without_token_info(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """토큰 정보가 없을 때 기본 분할 테스트"""
        # Given: 4개 파일, 토큰 정보 없음
        actual_tokens = None
        max_tokens = None

        # When: 기본 분할 실행
        result = prompt_splitter.split_user_prompts(
            user_prompts=sample_user_prompts,
            actual_tokens=actual_tokens,
            max_tokens=max_tokens,
            max_output_tokens=0,
        )

        # Then: 3개 청크로 분할되어야 함 (최소 3개 보장)
        assert len(result) == 3
        # 각 청크가 비어있지 않아야 함
        for chunk in result:
            assert len(chunk) > 0
        # overlap 비적용: 모든 청크 간 파일이 겹치지 않아야 함
        all_files = []
        for chunk in result:
            all_files.extend([p.file_name for p in chunk])
        assert len(all_files) == len(set(all_files))

    def test_overlap_zero(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """overlap=0일 때 테스트"""
        # Given: 4개 파일, overlap=0
        actual_tokens = 150000
        max_tokens = 100000

        # When: overlap=0으로 분할
        result = prompt_splitter.split_user_prompts(
            user_prompts=sample_user_prompts,
            actual_tokens=actual_tokens,
            max_tokens=max_tokens,
            max_output_tokens=0,
        )

        # Then: 겹치는 파일이 없어야 함
        assert len(result) == 3
        all_files = []
        for chunk in result:
            all_files.extend([prompt.file_name for prompt in chunk])
        # 모든 파일명이 unique해야 함 (겹치지 않음)
        assert len(all_files) == len(set(all_files))

    def test_overlap_one(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """overlap=1일 때 테스트"""
        # Given: 4개 파일, overlap=1
        actual_tokens = 150000
        max_tokens = 100000

        # When: overlap=1로 분할
        result = prompt_splitter.split_user_prompts(
            user_prompts=sample_user_prompts,
            actual_tokens=actual_tokens,
            max_tokens=max_tokens,
            max_output_tokens=0,
        )

        # Then: overlap 비적용, 3개 청크로 분할되며 겹치는 파일 없음
        assert len(result) == 3
        all_files = []
        for chunk in result:
            all_files.extend([p.file_name for p in chunk])
        assert len(all_files) == len(set(all_files))

    def test_overlap_two(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """overlap=2일 때 테스트"""
        # Given: 4개 파일, overlap=2
        actual_tokens = 200000
        max_tokens = 100000

        # When: overlap=2로 분할
        result = prompt_splitter.split_user_prompts(
            user_prompts=sample_user_prompts,
            actual_tokens=actual_tokens,
            max_tokens=max_tokens,
            max_output_tokens=0,
        )

        # Then: overlap 비적용, 최소 2개 청크이며 겹치는 파일 없음
        assert len(result) >= 2
        all_files = []
        for chunk in result:
            all_files.extend([p.file_name for p in chunk])
        assert len(all_files) == len(set(all_files))

    def test_calculate_split_ratio(self, prompt_splitter: PromptSplitter) -> None:
        """분할 비율 계산 테스트"""
        # Given: actual_tokens=150000, max_tokens=100000
        actual_tokens = 150000
        max_tokens = 100000

        # When: 분할 비율 계산
        split_ratio = prompt_splitter._calculate_split_ratio(
            actual_tokens, max_tokens, max_output_tokens=0
        )

        # Then: max(3, int(150000 / (100000 * 0.8))) = max(3, int(1.875)) = max(3, 1) = 3
        safe_max_tokens = (max_tokens - 5000) * 0.8  # system_prompt_tokens=5000 고려
        raw_split_ratio = actual_tokens / safe_max_tokens
        expected_ratio = max(3, int(raw_split_ratio))
        assert split_ratio == expected_ratio
        assert split_ratio == 3

    def test_apply_overlap(
        self,
        prompt_splitter: PromptSplitter,
        sample_user_prompts: list[UserPromptWithFileContent],
    ) -> None:
        """overlap 적용 테스트"""
        # Given: 2개 청크, overlap=1
        chunk1 = sample_user_prompts[:2]  # file_0.py, file_1.py
        chunk2 = sample_user_prompts[2:4]  # file_2.py, file_3.py
        chunks = [chunk1, chunk2]
        overlap = 1

        # When: overlap 적용
        result = prompt_splitter._apply_overlap(chunks, overlap)

        # Then: 두 번째 청크 앞에 첫 번째 청크의 마지막 파일이 추가되어야 함
        assert len(result) == 2
        assert len(result[0]) == 2  # 원래 그대로
        assert len(result[1]) == 3  # overlap으로 1개 추가
        assert result[1][0].file_name == result[0][-1].file_name  # file_1.py가 겹침
