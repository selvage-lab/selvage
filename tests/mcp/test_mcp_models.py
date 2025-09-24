"""MCP 응답 모델 테스트"""

from datetime import datetime

import pytest

# 이 테스트는 실패할 예정 (Red 단계)
# MCP 모델들이 아직 구현되지 않음
try:
    from selvage.src.mcp.models.responses import (
        ModelInfo,
        ReviewHistoryItem,
        ReviewResult,
        ServerStatus,
    )
except ImportError:
    pytest.skip("MCP models not implemented yet", allow_module_level=True)


class TestReviewResult:
    """ReviewResult 모델 테스트"""

    def test_review_result_successful_creation(self) -> None:
        """성공적인 ReviewResult 생성 테스트"""
        result = ReviewResult(
            success=True,
            estimated_cost=0.05,
            model_used="claude-sonnet-4",
            files_reviewed=["test.py", "main.py"],
            log_id="test-log-123",
            log_path="/path/to/log.json",
        )

        assert result.success is True
        assert result.response is None  # response는 선택적 필드
        assert result.estimated_cost == 0.05
        assert result.model_used == "claude-sonnet-4"
        assert result.files_reviewed == ["test.py", "main.py"]
        assert result.log_id == "test-log-123"
        assert result.log_path == "/path/to/log.json"
        assert isinstance(result.timestamp, datetime)
        assert result.error_message is None

    def test_review_result_failed_creation(self) -> None:
        """실패한 ReviewResult 생성 테스트"""
        result = ReviewResult(
            success=False,
            model_used="claude-sonnet-4",
            error_message="API key not found",
        )

        assert result.success is False
        assert result.response is None
        assert result.estimated_cost == 0.0
        assert result.model_used == "claude-sonnet-4"
        assert result.files_reviewed == []
        assert result.log_id is None
        assert result.log_path is None
        assert isinstance(result.timestamp, datetime)
        assert result.error_message == "API key not found"

    def test_review_result_json_serialization(self) -> None:
        """ReviewResult JSON 직렬화 테스트"""
        result = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )

        json_data = result.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["success"] is True
        assert json_data["response"] is None  # response는 선택적
        assert json_data["model_used"] == "claude-sonnet-4"
        assert "timestamp" in json_data
        # timestamp는 ISO 형식 문자열이어야 함
        assert isinstance(json_data["timestamp"], str)

    def test_review_result_required_fields(self) -> None:
        """ReviewResult 필수 필드 검증 테스트"""
        # model_used는 필수 필드
        with pytest.raises(ValueError):
            ReviewResult(success=True)  # model_used 누락

        # success는 필수 필드
        with pytest.raises(ValueError):
            ReviewResult(model_used="claude-sonnet-4")  # success 누락


class TestModelInfo:
    """ModelInfo 모델 테스트"""

    def test_model_info_creation(self) -> None:
        """ModelInfo 생성 테스트"""
        model = ModelInfo(
            name="claude-sonnet-4",
            provider="anthropic",
            display_name="Claude Sonnet 4",
            description="High-performance reasoning model",
            cost_per_1k_tokens=0.003,
            max_tokens=200000,
            supports_function_calling=True,
        )

        assert model.name == "claude-sonnet-4"
        assert model.provider == "anthropic"
        assert model.display_name == "Claude Sonnet 4"
        assert model.description == "High-performance reasoning model"
        assert model.cost_per_1k_tokens == 0.003
        assert model.max_tokens == 200000
        assert model.supports_function_calling is True

    def test_model_info_defaults(self) -> None:
        """ModelInfo 기본값 테스트"""
        model = ModelInfo(
            name="test-model",
            provider="test-provider",
            display_name="Test Model",
            description="Test model description",
            cost_per_1k_tokens=0.001,
            max_tokens=4096,
        )

        assert model.supports_function_calling is False  # 기본값

    def test_model_info_required_fields(self) -> None:
        """ModelInfo 필수 필드 검증"""
        required_fields = [
            "name",
            "provider",
            "display_name",
            "description",
            "cost_per_1k_tokens",
            "max_tokens",
        ]

        for field in required_fields:
            kwargs = {
                "name": "test",
                "provider": "test",
                "display_name": "test",
                "description": "test",
                "cost_per_1k_tokens": 0.001,
                "max_tokens": 4096,
            }
            del kwargs[field]

            with pytest.raises(ValueError):
                ModelInfo(**kwargs)


class TestReviewHistoryItem:
    """ReviewHistoryItem 모델 테스트"""

    def test_review_history_item_creation(self) -> None:
        """ReviewHistoryItem 생성 테스트"""
        timestamp_str = "2023-12-01T10:00:00"
        item = ReviewHistoryItem(
            log_id="log-123",
            timestamp=timestamp_str,
            model="claude-sonnet-4",
            files_count=3,
            status="SUCCESS",
            cost=0.05,
        )

        assert item.log_id == "log-123"
        assert item.timestamp == timestamp_str
        assert item.model == "claude-sonnet-4"
        assert item.files_count == 3
        assert item.status == "SUCCESS"
        assert item.cost == 0.05

    def test_review_history_item_with_target(self) -> None:
        """간단한 ReviewHistoryItem 테스트 (target/review_type 필드 제거됨)"""
        item = ReviewHistoryItem(
            log_id="log-456",
            timestamp="2023-12-01T11:00:00",
            model="gpt-4o",
            files_count=5,
            status="SUCCESS",
            cost=0.10,
        )

        assert item.log_id == "log-456"
        assert item.timestamp == "2023-12-01T11:00:00"
        assert item.model == "gpt-4o"
        assert item.files_count == 5
        assert item.status == "SUCCESS"
        assert item.cost == 0.10


class TestServerStatus:
    """ServerStatus 모델 테스트"""

    def test_server_status_creation(self) -> None:
        """ServerStatus 생성 테스트"""
        start_time = datetime.now()
        status = ServerStatus(
            running=True,
            port=3000,
            host="localhost",
            start_time=start_time,
            version="0.1.8",
            tools_count=6,
        )

        assert status.running is True
        assert status.port == 3000
        assert status.host == "localhost"
        assert status.start_time == start_time
        assert status.version == "0.1.8"
        assert status.tools_count == 6

    def test_server_status_stdio_mode(self) -> None:
        """stdio 모드 ServerStatus 테스트"""
        status = ServerStatus(
            running=True,
            port=None,
            host=None,
            start_time=None,
            version="0.1.8",
            tools_count=6,
        )

        assert status.running is True
        assert status.port is None
        assert status.host is None
        assert status.start_time is None
        assert status.version == "0.1.8"
        assert status.tools_count == 6

    def test_server_status_required_fields(self) -> None:
        """ServerStatus 필수 필드 검증"""
        required_fields = ["running", "version", "tools_count"]

        for field in required_fields:
            kwargs = {
                "running": True,
                "version": "0.1.8",
                "tools_count": 6,
            }
            del kwargs[field]

            with pytest.raises(ValueError):
                ServerStatus(**kwargs)


class TestModelSerialization:
    """모델 직렬화 통합 테스트"""

    def test_all_models_json_serializable(self) -> None:
        """모든 모델이 JSON 직렬화 가능한지 테스트"""
        # ReviewResult
        review_result = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )
        assert isinstance(review_result.model_dump(), dict)

        # ModelInfo
        model_info = ModelInfo(
            name="test",
            provider="test",
            display_name="test",
            description="test",
            cost_per_1k_tokens=0.001,
            max_tokens=4096,
        )
        assert isinstance(model_info.model_dump(), dict)

        # ReviewHistoryItem
        history_item = ReviewHistoryItem(
            log_id="test",
            timestamp="2023-12-01T12:00:00",
            model="test",
            files_count=1,
            status="SUCCESS",
            cost=0.01,
        )
        assert isinstance(history_item.model_dump(), dict)

        # ServerStatus
        server_status = ServerStatus(
            running=True,
            version="0.1.8",
            tools_count=6,
        )
        assert isinstance(server_status.model_dump(), dict)

    def test_datetime_serialization_format(self) -> None:
        """datetime 직렬화 형식 테스트"""
        result = ReviewResult(
            success=True,
            model_used="claude-sonnet-4",
        )

        json_data = result.model_dump()
        timestamp_str = json_data["timestamp"]

        # ISO 형식인지 확인
        assert isinstance(timestamp_str, str)
        # datetime으로 파싱 가능한지 확인
        parsed_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(parsed_dt, datetime)
