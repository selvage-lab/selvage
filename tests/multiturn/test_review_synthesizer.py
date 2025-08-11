"""ReviewSynthesizer 테스트"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from selvage.src.model_config import ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.multiturn.review_synthesizer import ReviewSynthesizer
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewIssue,
    ReviewResponse,
    StructuredSynthesisResponse,
)


class TestReviewSynthesizer:
    """ReviewSynthesizer 클래스 테스트"""

    @pytest.fixture
    def mock_llm_gateway(self) -> Mock:
        """Mock BaseGateway 생성"""
        gateway = Mock()
        gateway.get_model_name.return_value = "test-model"
        gateway.get_provider.return_value = Mock(value="test-provider")

        # 합성 요청에 대한 성공적인 응답 설정
        gateway.review_code.return_value = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="통합된 요약: 코드 품질이 전반적으로 향상되었습니다.",
                recommendations=[
                    "중복 코드를 제거하세요",
                    "에러 처리를 개선하세요",
                    "테스트 커버리지를 늘리세요",
                ],
                issues=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("test-model"),
        )

        return gateway

    @pytest.fixture
    def sample_review_results(self) -> list[ReviewResult]:
        """테스트용 ReviewResult 리스트 생성"""
        results = []

        # 첫 번째 청크 결과
        result1 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="첫 번째 청크 요약: 새로운 함수가 추가되었습니다.",
                recommendations=[
                    "함수명을 더 명확하게 변경하세요",
                    "에러 처리를 추가하세요",
                ],
                issues=[
                    ReviewIssue(
                        type="style",
                        line_number=10,
                        file="test1.py",
                        description="함수명 컨벤션",
                        severity="info",
                    )
                ],
            ),
            estimated_cost=EstimatedCost(
                model="test-model",
                input_tokens=1000,
                input_cost_usd=0.01,
                output_tokens=200,
                output_cost_usd=0.02,
                total_cost_usd=0.03,
            ),
        )

        # 두 번째 청크 결과
        result2 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="두 번째 청크 요약: 기존 로직이 개선되었습니다.",
                recommendations=[
                    "에러 처리를 추가하세요",  # 중복
                    "주석을 더 상세하게 작성하세요",
                ],
                issues=[
                    ReviewIssue(
                        type="bug",
                        line_number=25,
                        file="test2.py",
                        description="잠재적 null pointer 오류",
                        severity="warning",
                    )
                ],
            ),
            estimated_cost=EstimatedCost(
                model="test-model",
                input_tokens=800,
                input_cost_usd=0.008,
                output_tokens=150,
                output_cost_usd=0.015,
                total_cost_usd=0.023,
            ),
        )

        results.extend([result1, result2])
        return results

    @pytest.fixture
    def review_synthesizer(self, mock_llm_gateway: Mock) -> ReviewSynthesizer:
        """ReviewSynthesizer 인스턴스 생성"""
        return ReviewSynthesizer(mock_llm_gateway.get_model_name())

    def test_synthesize_review_results_success(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """성공적인 리뷰 결과 합성 테스트"""
        # When: 리뷰 결과 합성
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 합성된 결과 반환
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.recommendations) > 0

        # Issues는 모든 청크의 이슈가 포함되어야 함
        assert len(result.review_response.issues) == 2

        # 모델명이 일치해야 함
        assert result.estimated_cost.model == "test-model"

        # 비용이 합산되어야 함
        assert result.estimated_cost.input_tokens == 1800  # 1000 + 800
        assert result.estimated_cost.total_cost_usd == 0.053  # 0.03 + 0.023

        # 현재는 fallback 방식을 사용하므로 LLM 호출 없음
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_empty_results(
        self,
        review_synthesizer: ReviewSynthesizer,
        mock_llm_gateway: Mock,
    ) -> None:
        """빈 리뷰 결과 리스트 처리 테스트"""
        # When: 빈 리스트로 합성
        result = review_synthesizer.synthesize_review_results([])

        # Then: 빈 결과 반환
        assert result.success is True
        assert result.estimated_cost.model == "test-model"

        # LLM이 호출되지 않아야 함
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_failed_results_only(
        self,
        review_synthesizer: ReviewSynthesizer,
        mock_llm_gateway: Mock,
    ) -> None:
        """실패한 결과들만 있을 때 테스트"""
        # Given: 실패한 결과들
        failed_results = [
            ReviewResult.get_error_result(
                error=Exception("Test error"),
                model="test-model",
                provider="test-provider",
            )
        ]

        # When: 실패한 결과들로 합성
        result = review_synthesizer.synthesize_review_results(failed_results)

        # Then: 빈 결과 반환
        assert result.success is True
        assert result.estimated_cost.model == "test-model"

        # LLM이 호출되지 않아야 함
        assert mock_llm_gateway.review_code.call_count == 0

    def test_synthesize_with_fallback_deduplication(
        self,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """Fallback 방식의 중복 제거 테스트"""
        # Given: ReviewSynthesizer 인스턴스
        synthesizer = ReviewSynthesizer(mock_llm_gateway.get_model_name())

        # When: 합성 실행
        result = synthesizer.synthesize_review_results(sample_review_results)

        # Then: fallback으로 기본 합성 실행되어야 함
        assert result.success is True
        assert result.review_response.summary is not None
        assert len(result.review_response.recommendations) > 0

        # 중복 제거가 되어야 함 (fallback의 특징)
        unique_recommendations = set(result.review_response.recommendations)
        assert "에러 처리를 추가하세요" in unique_recommendations

        # 중복 제거로 인해 실제 권장사항 개수가 4개보다 적어야 함
        # (원본: [함수명 변경, 에러 처리, 에러 처리 중복, 주석 작성] = 4개 → 3개로 중복 제거)
        assert len(result.review_response.recommendations) == 3

    def test_model_name_consistency(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """모델명 일관성 테스트"""
        # When: 합성 실행
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 모델명이 gateway의 모델명과 일치해야 함
        assert result.estimated_cost.model == mock_llm_gateway.get_model_name()
        assert result.estimated_cost.model == "test-model"

    def test_cost_calculation(
        self,
        review_synthesizer: ReviewSynthesizer,
        sample_review_results: list[ReviewResult],
        mock_llm_gateway: Mock,
    ) -> None:
        """비용 계산 정확성 테스트"""
        # When: 합성 실행
        result = review_synthesizer.synthesize_review_results(sample_review_results)

        # Then: 비용이 정확히 합산되어야 함
        expected_input_tokens = 1000 + 800  # 각 result의 input_tokens 합
        expected_total_cost = 0.03 + 0.023  # 각 result의 total_cost_usd 합

        assert result.estimated_cost.input_tokens == expected_input_tokens
        assert abs(result.estimated_cost.total_cost_usd - expected_total_cost) < 0.001


class TestReviewSynthesizerLLMIntegration:
    """ReviewSynthesizer LLM 통합 기능 테스트"""

    @pytest.fixture
    def sample_model_info(self) -> ModelInfoDict:
        """테스트용 모델 정보 생성"""
        return {
            "full_name": "gpt-4o",
            "aliases": [],
            "description": "테스트 모델",
            "provider": ModelProvider.OPENAI,
            "params": {"temperature": 0.0},
            "thinking_mode": False,
            "pricing": {"input": 2.5, "output": 10.0, "description": "test"},
            "context_limit": 128000,
            "openrouter_name": "openai/gpt-4o",
        }

    @pytest.fixture
    def sample_review_results(self) -> list[ReviewResult]:
        """테스트용 ReviewResult 리스트 생성"""
        result1 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="첫 번째 청크: 함수가 추가되었습니다.",
                recommendations=["함수명 개선", "에러 처리 추가"],
                issues=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("gpt-4o"),
        )

        result2 = ReviewResult.get_success_result(
            review_response=ReviewResponse(
                summary="두 번째 청크: 로직이 전면적으로 개선되었습니다.",  # 더 긴 summary
                recommendations=["에러 처리 추가", "주석 추가"],  # 중복 있음
                issues=[],
            ),
            estimated_cost=EstimatedCost.get_zero_cost("gpt-4o"),
        )

        return [result1, result2]

    def test_structured_synthesis_response_model(self) -> None:
        """StructuredSynthesisResponse Pydantic 모델 검증"""
        # Given: 유효한 데이터
        valid_data = {
            "summary": "통합된 요약입니다.",
            "recommendations": ["권장사항1", "권장사항2"],
            "synthesis_quality": "excellent",
        }

        # When: 모델 생성
        response = StructuredSynthesisResponse(**valid_data)

        # Then: 정상 생성 및 필드 검증
        assert response.summary == "통합된 요약입니다."
        assert len(response.recommendations) == 2
        assert response.synthesis_quality == "excellent"

    def test_structured_synthesis_response_validation(self) -> None:
        """StructuredSynthesisResponse 유효성 검증 테스트"""
        # Given: 최소 길이 미만의 summary
        with pytest.raises(ValueError):
            StructuredSynthesisResponse(
                summary="짧음",  # min_length=10 미만
                recommendations=[],
                synthesis_quality="good",
            )

        # Given: 잘못된 synthesis_quality 값
        with pytest.raises(ValueError):
            StructuredSynthesisResponse(
                summary="유효한 길이의 요약입니다.",
                recommendations=[],
                synthesis_quality="invalid_value",  # pattern 불일치
            )

    @patch("selvage.src.multiturn.review_synthesizer.ModelConfig")
    def test_load_model_info(
        self, mock_model_config_class: Mock, sample_model_info: ModelInfoDict
    ) -> None:
        """모델 정보 로드 기능 테스트"""
        # Given: ModelConfig 인스턴스 및 메서드 Mock 설정
        mock_config_instance = Mock()
        mock_config_instance.get_model_info.return_value = sample_model_info
        mock_model_config_class.return_value = mock_config_instance

        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: _load_model_info 호출
        result = synthesizer._load_model_info()

        # Then: 올바른 모델 정보 반환
        assert result == sample_model_info
        mock_model_config_class.assert_called_once()
        mock_config_instance.get_model_info.assert_called_once_with("gpt-4o")

    @patch("selvage.src.multiturn.review_synthesizer.get_api_key")
    def test_load_api_key(self, mock_get_api_key: Mock) -> None:
        """프로바이더별 API 키 로드 테스트"""
        # Given: API 키 Mock 설정
        mock_get_api_key.return_value = "test_api_key_123"
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: _load_api_key 호출
        result = synthesizer._load_api_key(ModelProvider.OPENAI)

        # Then: 올바른 API 키 반환
        assert result == "test_api_key_123"
        mock_get_api_key.assert_called_once_with(ModelProvider.OPENAI)

    @patch("selvage.src.multiturn.review_synthesizer.LLMClientFactory.create_client")
    def test_create_client(
        self, mock_create_client: Mock, sample_model_info: ModelInfoDict
    ) -> None:
        """프로바이더별 클라이언트 생성 테스트"""
        # Given: 클라이언트 생성 Mock 설정
        mock_instructor_client = MagicMock()
        mock_create_client.return_value = mock_instructor_client
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: _create_client 호출
        result = synthesizer._create_client(sample_model_info, "test_api_key")

        # Then: 올바른 클라이언트 반환
        assert result == mock_instructor_client
        mock_create_client.assert_called_once_with(
            ModelProvider.OPENAI, "test_api_key", sample_model_info
        )

    def test_fallback_synthesis_single_result(
        self, sample_review_results: list[ReviewResult]
    ) -> None:
        """Fallback 합성 - 단일 결과 테스트"""
        # Given: 단일 결과
        single_result = [sample_review_results[0]]
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: fallback 합성 실행
        summary, recommendations = synthesizer._fallback_synthesis(single_result)

        # Then: 결과가 그대로 반환되어야 함
        assert summary == "첫 번째 청크: 함수가 추가되었습니다."
        assert recommendations == ["함수명 개선", "에러 처리 추가"]

    def test_fallback_synthesis_multiple_results(
        self, sample_review_results: list[ReviewResult]
    ) -> None:
        """Fallback 합성 - 다중 결과 테스트 (문서 명세 적용)"""
        # Given: 다중 결과
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: fallback 합성 실행
        summary, recommendations = synthesizer._fallback_synthesis(
            sample_review_results
        )

        # Then: 가장 긴 summary가 선택되어야 함 (문서 명세)
        expected_longest = (
            "두 번째 청크: 로직이 전면적으로 개선되었습니다."  # 더 긴 summary
        )
        assert summary == expected_longest

        # Then: 중복 제거된 권장사항이 반환되어야 함
        expected_recs = ["함수명 개선", "에러 처리 추가", "주석 추가"]  # 중복 제거됨
        assert set(recommendations) == set(expected_recs)
        assert len(recommendations) == 3

    def test_fallback_synthesis_empty_summaries(self) -> None:
        """Fallback 합성 - 빈 summary 처리 테스트"""
        # Given: summary가 없는 결과들
        empty_results = [
            ReviewResult.get_success_result(
                review_response=ReviewResponse(
                    summary="",  # 빈 summary
                    recommendations=["권장사항1"],
                    issues=[],
                ),
                estimated_cost=EstimatedCost.get_zero_cost("gpt-4o"),
            )
        ]
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: fallback 합성 실행
        summary, recommendations = synthesizer._fallback_synthesis(empty_results)

        # Then: 기본 메시지 반환 (문서 명세)
        assert summary == "리뷰 결과를 합성할 수 없습니다."
        assert recommendations == ["권장사항1"]

    def test_synthesis_message_creation_structure(
        self, sample_review_results: list[ReviewResult]
    ) -> None:
        """합성용 메시지 구조 생성 테스트"""
        synthesizer = ReviewSynthesizer("gpt-4o")

        # When: _create_synthesis_messages 호출
        messages = synthesizer._create_synthesis_messages(sample_review_results)

        # Then: 시스템 프롬프트 포함된 메시지 리스트 생성 확인
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        # 시스템 프롬프트 내용 확인
        system_content = messages[0]["content"]
        assert "expert code review synthesis specialist" in system_content
        assert "Silicon Valley tech company" in system_content

        # 사용자 메시지의 JSON 구조 확인
        user_content = json.loads(messages[1]["content"])
        assert user_content["task"] == "synthesis"
        assert len(user_content["chunks"]) == 2

        # 청크 데이터 구조 검증
        chunk1 = user_content["chunks"][0]
        assert chunk1["chunk_id"] == 1
        assert chunk1["summary"] == "첫 번째 청크: 함수가 추가되었습니다."
        assert chunk1["recommendations"] == ["함수명 개선", "에러 처리 추가"]

        chunk2 = user_content["chunks"][1]
        assert chunk2["chunk_id"] == 2
        assert chunk2["summary"] == "두 번째 청크: 로직이 전면적으로 개선되었습니다."
        assert chunk2["recommendations"] == ["에러 처리 추가", "주석 추가"]

    def test_provider_specific_params_openai(
        self, sample_model_info: ModelInfoDict
    ) -> None:
        """OpenAI 프로바이더 요청 파라미터 생성 테스트"""
        synthesizer = ReviewSynthesizer("gpt-4o")
        messages = [
            {"role": "system", "content": "test system"},
            {"role": "user", "content": "test user"},
        ]

        # When: _create_request_params 호출
        params = synthesizer._create_request_params(messages, sample_model_info)

        # Then: OpenAI 파라미터 확인
        assert params["model"] == "gpt-4o"
        assert params["messages"] == messages
        assert params["max_tokens"] == 20000  # 기본값
        assert params["temperature"] == 0.1

    def test_provider_specific_params_anthropic(self) -> None:
        """Anthropic 프로바이더 요청 파라미터 생성 테스트"""
        synthesizer = ReviewSynthesizer("claude-sonnet-4")
        anthropic_model_info = {
            "full_name": "claude-sonnet-4",
            "provider": ModelProvider.ANTHROPIC,
            "max_tokens": 8000,
        }
        messages = [
            {"role": "system", "content": "test system"},
            {"role": "user", "content": "test user"},
        ]

        # When: _create_request_params 호출
        params = synthesizer._create_request_params(messages, anthropic_model_info)

        # Then: Anthropic 파라미터 확인
        assert params["model"] == "claude-sonnet-4"
        assert params["system"] == "test system"  # system 메시지 분리
        assert params["messages"] == [
            {"role": "user", "content": "test user"}
        ]  # system 제외
        assert params["max_tokens"] == 8000
        assert params["temperature"] == 0.1

    def test_provider_specific_params_google(self) -> None:
        """Google 프로바이더 요청 파라미터 생성 테스트"""
        # 구현 후 다음 검증 예정:
        # - contents 형식 변환 확인 (system → user 변환)
        # - generation_config 설정 확인
        pass

    def test_provider_specific_params_openrouter(
        self, sample_model_info: ModelInfoDict
    ) -> None:
        """OpenRouter 프로바이더 요청 파라미터 생성 테스트"""
        # 구현 후 다음 검증 예정:
        # - JSON Schema 형식 확인
        # - openrouter_name 필드 사용 확인
        # - response_format 설정 확인
        pass
