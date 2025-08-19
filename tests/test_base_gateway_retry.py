"""BaseGateway retry 로직 테스트"""

from selvage.src.llm_gateway.base_gateway import BaseGateway
from selvage.src.models.model_provider import ModelProvider


class MockGateway(BaseGateway):
    """테스트용 BaseGateway 구현체"""

    def _load_api_key(self) -> str:
        return "test-api-key"

    def _set_model(self, model_info) -> None:
        self.model = model_info

    def _create_request_params(self, messages):
        return {"messages": messages, "model": "test-model"}


class TestBaseGatewayRetry:
    """BaseGateway retry 기능 테스트"""

    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.model_info = {
            "full_name": "test-model",
            "provider": ModelProvider.OPENAI,
        }
        self.gateway = MockGateway(self.model_info)

    def test_retry_decorator_applied(self):
        """retry 데코레이터가 _review_code_with_retry 메서드에 올바르게 적용되었는지 테스트"""
        # _review_code_with_retry 메서드에 retry 관련 속성이 있는지 확인
        assert hasattr(self.gateway._review_code_with_retry, "retry")

        # tenacity retry 객체의 속성들 확인
        retry_obj = self.gateway._review_code_with_retry.retry

        # 재시도 횟수 (최대 3회)
        assert retry_obj.stop.max_attempt_number == 3

        # 지수 백오프 설정 (multiplier=1, min=1, max=8)
        wait_obj = retry_obj.wait
        assert wait_obj.multiplier == 1
        assert wait_obj.min == 1
        assert wait_obj.max == 8

        # 재시도 대상 예외 타입 확인
        retry_condition = retry_obj.retry
        exception_types = retry_condition.exception_types
        assert ConnectionError in exception_types
        assert TimeoutError in exception_types
        assert ValueError in exception_types
