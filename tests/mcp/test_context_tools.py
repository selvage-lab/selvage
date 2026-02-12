"""에이전트 위임 리뷰 도구 테스트"""

from unittest.mock import MagicMock, patch

import pytest

from selvage.src.mcp.models.responses import ReviewContextResult


class TestReviewContextResultModel:
    """ReviewContextResult 모델 테스트"""

    def test_success_result_creation(self) -> None:
        """성공 결과 생성 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt='You are a code reviewer...',
            review_targets=[
                {'role': 'user', 'content': '{"file_name": "app.py"}'}
            ],
            output_format={'type': 'json_schema', 'schema': {}},
            metadata={'files_count': 1, 'total_additions': 10, 'total_deletions': 3},
        )

        assert result.success is True
        assert result.system_prompt is not None
        assert len(result.review_targets) == 1
        assert result.output_format is not None
        assert result.metadata['files_count'] == 1
        assert result.error_message is None

    def test_error_result_creation(self) -> None:
        """에러 결과 생성 테스트"""
        result = ReviewContextResult(
            success=False,
            error_message='No changes to review.',
        )

        assert result.success is False
        assert result.system_prompt is None
        assert result.review_targets == []
        assert result.error_message == 'No changes to review.'

    def test_json_serialization(self) -> None:
        """JSON 직렬화 테스트"""
        result = ReviewContextResult(
            success=True,
            system_prompt='prompt',
            review_targets=[{'role': 'user', 'content': 'test'}],
            output_format={'type': 'json_schema'},
            metadata={'files_count': 1},
        )

        json_str = result.model_dump_json()
        assert '"success":true' in json_str.lower() or '"success": true' in json_str.lower()

    def test_metadata_fields(self) -> None:
        """metadata 필드 구조 테스트"""
        metadata = {
            'files_count': 3,
            'total_additions': 42,
            'total_deletions': 10,
            'file_languages': {'python': 2, 'javascript': 1},
        }
        result = ReviewContextResult(
            success=True,
            system_prompt='prompt',
            review_targets=[],
            output_format={},
            metadata=metadata,
        )

        assert result.metadata['files_count'] == 3
        assert result.metadata['total_additions'] == 42
        assert result.metadata['file_languages']['python'] == 2
