"""리뷰 결과 합성기"""

import importlib.resources
import json
from typing import Any

from selvage.src.config import get_api_key, get_default_language
from selvage.src.model_config import ModelConfig, ModelInfoDict
from selvage.src.models.model_provider import ModelProvider
from selvage.src.models.review_result import ReviewResult
from selvage.src.utils.base_console import console
from selvage.src.utils.json_extractor import JSONExtractor
from selvage.src.utils.llm_client_factory import LLMClientFactory
from selvage.src.utils.token.models import (
    EstimatedCost,
    ReviewResponse,
    StructuredSynthesisResponse,
    SynthesisResult,
)


class ReviewSynthesizer:
    """여러 리뷰 결과를 LLM을 활용하여 지능적으로 합성하는 클래스"""

    def __init__(self, model_name: str) -> None:
        """
        Args:
            model_name: 사용할 모델명
        """
        self.model_name = model_name

    def synthesize_review_results(
        self, review_results: list[ReviewResult]
    ) -> ReviewResult:
        """
        여러 리뷰 결과를 합성하여 하나의 통합된 리뷰 결과를 생성

        Args:
            review_results: 합성할 리뷰 결과들

        Returns:
            ReviewResult: 합성된 최종 리뷰 결과
        """
        if not review_results:
            return ReviewResult.get_empty_result(self.model_name)

        # 성공한 결과들만 추출
        successful_results = [r for r in review_results if r.success]
        if not successful_results:
            return ReviewResult.get_empty_result(self.model_name)

        console.info("리뷰 결과 합성 시작")

        # 1. Issues는 단순 합산 (기존 방식 유지)
        all_issues = []
        for result in successful_results:
            all_issues.extend(result.review_response.issues)

        # 현재 상황: overlap=0이므로 정보 보존 우선
        synthesized_summary = self._synthesize_summary_only(successful_results)
        synthesized_recommendations = self._combine_recommendations_simple(
            successful_results
        )

        # 3. 비용 합산
        total_cost = self._calculate_total_cost(successful_results)

        # 4. 최종 결과 생성
        synthesized_review_response = ReviewResponse(
            summary=synthesized_summary,
            recommendations=synthesized_recommendations,
            issues=all_issues,
            score=successful_results[
                0
            ].review_response.score,  # 첫 번째 결과의 점수 사용
        )

        console.info("리뷰 결과 합성 완료")
        return ReviewResult.get_success_result(
            review_response=synthesized_review_response, estimated_cost=total_cost
        )

    def _synthesize_with_llm(
        self, successful_results: list[ReviewResult]
    ) -> SynthesisResult:
        """LLM 기반 합성 (에러 처리 및 fallback 포함)"""

        try:
            # 1. API 키 검증
            model_info = self._load_model_info()
            try:
                api_key = self._load_api_key(model_info["provider"])
                if not api_key:
                    console.warning("API 키가 없습니다. fallback 모드로 전환합니다.")
                    return self._fallback_synthesis(successful_results)
            except Exception as e:
                console.warning(f"API 키 로드 실패: {e}. fallback 모드로 전환합니다.")
                return self._fallback_synthesis(successful_results)

            # 2. LLM 합성 시도 (최대 3회 재시도)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = self._execute_llm_synthesis(successful_results)
                    if result is not None:
                        console.info("LLM 합성 성공")
                        return result
                except Exception as e:
                    console.error(f"LLM 합성 중 예외 발생: {e}")
                    if attempt == max_retries - 1:
                        console.warning("LLM 합성 실패. fallback 모드로 전환합니다.")
                        break

            # 3. Fallback으로 전환
            return self._fallback_synthesis(successful_results)

        except Exception as e:
            console.error(f"LLM 합성 중 예상치 못한 오류: {e}")
            return self._fallback_synthesis(successful_results)

    def _fallback_synthesis(
        self, successful_results: list[ReviewResult]
    ) -> SynthesisResult:
        """간단하고 안정적인 fallback 합성 로직 (CR-19 문서 명세 적용)"""
        # 1. Summary 단순 결합
        summaries = [
            r.review_response.summary
            for r in successful_results
            if r.review_response.summary
        ]

        if not summaries:
            combined_summary = "리뷰 결과를 합성할 수 없습니다."
        elif len(summaries) == 1:
            combined_summary = summaries[0]
        else:
            # 가장 긴 summary를 대표로 선택 (보통 가장 포괄적임)
            combined_summary = max(summaries, key=len)

        # 2. Recommendations 기본 중복 제거
        all_recs = []
        for result in successful_results:
            all_recs.extend(result.review_response.recommendations)

        # 완전 동일한 권장사항만 제거 (단순하고 안전)
        unique_recs = list(dict.fromkeys(all_recs))

        return SynthesisResult(summary=combined_summary, recommendations=unique_recs)

    def _combine_recommendations_simple(
        self, successful_results: list[ReviewResult]
    ) -> list[str]:
        """권장사항 단순 합산 (overlap=0 환경에서 정보 보존 우선)"""
        all_recs = []
        for result in successful_results:
            all_recs.extend(result.review_response.recommendations)

        # 완전 동일한 권장사항만 제거 (단순하고 안전)
        unique_recs = list(dict.fromkeys(all_recs))
        return unique_recs

    def _synthesize_summary_only(self, successful_results: list[ReviewResult]) -> str:
        """Summary만 LLM으로 합성 (부분적 LLM 활용)"""
        try:
            # LLM 합성 시도
            result = self._synthesize_with_llm(successful_results)
            return result.summary
        except Exception as e:
            console.warning(f"Summary LLM 합성 실패: {e}. fallback으로 전환합니다.")
            # fallback으로 전환
            summaries = [
                r.review_response.summary
                for r in successful_results
                if r.review_response.summary
            ]

            if not summaries:
                return "리뷰 결과를 합성할 수 없습니다."
            elif len(summaries) == 1:
                return summaries[0]
            else:
                # 가장 긴 summary를 대표로 선택
                return max(summaries, key=len)

    def _should_use_llm_synthesis(self) -> bool:
        """LLM 합성을 사용할지 결정 (현재는 overlap=0이므로 False)"""
        # TODO: 향후 overlap 감지 로직 구현 시 동적으로 결정
        # 현재는 overlap=0으로 고정되어 있으므로 단순 합산 방식 사용
        return False

    def _load_model_info(self) -> ModelInfoDict:
        """model_name으로부터 ModelInfoDict 로드"""
        config = ModelConfig()
        return config.get_model_info(self.model_name)

    def _load_api_key(self, provider: ModelProvider) -> str:
        """프로바이더별 API 키 로드"""
        return get_api_key(provider)

    def _get_synthesis_system_prompt(self) -> str:
        """합성용 시스템 프롬프트 로드 (사용자 언어 설정 반영)"""
        file_ref = importlib.resources.files(
            "selvage.resources.prompt.synthesis"
        ).joinpath("synthesis_system_prompt.txt")
        with importlib.resources.as_file(file_ref) as file_path:
            base_prompt = file_path.read_text(encoding="utf-8")

        user_language = get_default_language()
        return base_prompt.replace("{{LANGUAGE}}", user_language)

    def _create_synthesis_messages(
        self, successful_results: list[ReviewResult]
    ) -> list[dict[str, str]]:
        """합성용 메시지 구조 생성"""

        # 1. 시스템 프롬프트 생성
        system_prompt = self._get_synthesis_system_prompt()

        # 2. 사용자 프롬프트 데이터 구조화
        chunks_data = []
        for i, result in enumerate(successful_results, 1):
            chunk_data = {
                "chunk_id": i,
                "summary": result.review_response.summary,
                "recommendations": result.review_response.recommendations,
            }
            chunks_data.append(chunk_data)

        synthesis_data = {
            "task": "synthesis",
            "chunks": chunks_data,
        }

        # 3. 메시지 리스트 생성
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(synthesis_data, ensure_ascii=False, indent=2),
            },
        ]

        return messages

    def _create_request_params(
        self, messages: list[dict[str, str]], model_info: ModelInfoDict
    ) -> dict[str, Any]:
        """프로바이더별 API 요청 파라미터 생성"""

        provider = model_info["provider"]

        if provider == ModelProvider.OPENAI:
            return {
                "model": model_info["full_name"],
                "messages": messages,
                "max_tokens": 10000,
                "temperature": 0.1,
            }
        elif provider == ModelProvider.GOOGLE:
            # Gemini용 메시지 형식 변환
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    # Gemini는 system role을 지원하지 않으므로 user로 변환
                    contents.append(
                        {
                            "role": "user",
                            "parts": [{"text": f"System: {msg['content']}"}],
                        }
                    )
                else:
                    contents.append(
                        {"role": msg["role"], "parts": [{"text": msg["content"]}]}
                    )

            return {
                "model": model_info["full_name"],
                "contents": contents,
                # Google Gemini에서는 generation_config를 직접 전달하지 않음
            }
        elif provider == ModelProvider.ANTHROPIC:
            # system 메시지 분리
            system_content = None
            anthropic_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    anthropic_messages.append(msg)

            params = {
                "model": model_info["full_name"],
                "messages": anthropic_messages,
                "max_tokens": 10000,
                "temperature": 0.1,
            }

            if system_content:
                params["system"] = system_content

            return params
        elif provider == ModelProvider.OPENROUTER:
            # OpenRouter용 파라미터 (OpenAI 호환 + JSON Schema)
            # models.yml의 openrouter_name 필드 사용
            openrouter_model_name = model_info.get(
                "openrouter_name", model_info["full_name"]
            )

            return {
                "model": openrouter_model_name,
                "messages": messages,
                "max_tokens": 10000,
                "temperature": 0.1,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_synthesis_response",
                        "strict": True,
                        "schema": StructuredSynthesisResponse.model_json_schema(),
                    },
                },
                "usage": {
                    "include_usage": True,
                },
            }
        else:
            raise ValueError(f"지원하지 않는 프로바이더: {provider}")

    def _execute_llm_synthesis(
        self, successful_results: list[ReviewResult]
    ) -> SynthesisResult | None:
        """LLM을 직접 호출하여 합성 실행 (BaseGateway 패턴 적용)"""

        try:
            # 1. 모델 정보 및 클라이언트 준비
            model_info = self._load_model_info()
            api_key = self._load_api_key(model_info["provider"])
            client = LLMClientFactory.create_client(
                model_info["provider"], api_key, model_info
            )

            # 2. 합성용 메시지 구조 생성
            messages = self._create_synthesis_messages(successful_results)

            # 3. 프로바이더별 API 파라미터 생성
            params = self._create_request_params(messages, model_info)

            # 4. API 요청 송신 (프로바이더별 처리)
            provider = model_info["provider"]

            if provider == ModelProvider.OPENAI:
                # OpenAI/Instructor 처리
                structured_response, raw_api_response = (
                    client.chat.completions.create_with_completion(
                        response_model=StructuredSynthesisResponse,
                        max_retries=2,
                        **params,
                    )
                )

            elif provider == ModelProvider.GOOGLE:
                # Google Gemini 처리
                raw_api_response = client.models.generate_content(**params)
                response_text = raw_api_response.text

                if response_text is None:
                    return None

                # JSON 추출 및 파싱 (markdown 코드 블록 처리)
                structured_response = JSONExtractor.validate_and_parse_json(
                    response_text, StructuredSynthesisResponse
                )

                if structured_response is None:
                    return None

            elif provider == ModelProvider.ANTHROPIC:
                # Anthropic Claude 처리
                if model_info.get("thinking_mode", False):
                    # thinking 모드는 직접 호출
                    raw_api_response = client.messages.create(**params)
                    response_text = None
                    for block in raw_api_response.content:
                        if block.type == "text":
                            response_text = block.text

                    if response_text is None:
                        return None

                    # JSON 추출 및 파싱
                    structured_response = JSONExtractor.validate_and_parse_json(
                        response_text, StructuredSynthesisResponse
                    )

                    if structured_response is None:
                        return None
                else:
                    # 일반 모드는 instructor 사용
                    structured_response, raw_api_response = (
                        client.chat.completions.create_with_completion(
                            response_model=StructuredSynthesisResponse,
                            max_retries=2,
                            **params,
                        )
                    )

            elif provider == ModelProvider.OPENROUTER:
                # OpenRouter 처리 (컨텍스트 매니저 방식)
                with client as openrouter_client:
                    raw_response_data = openrouter_client.create_completion(**params)

                    # OpenRouter 응답을 OpenAI 형식으로 변환
                    from selvage.src.llm_gateway.openrouter.models import (
                        OpenRouterResponse,
                    )

                    raw_api_response = OpenRouterResponse.from_dict(raw_response_data)

                    # 응답에서 텍스트 추출
                    if not raw_api_response.choices:
                        console.error("OpenRouter API 응답에 choices가 없습니다")
                        return None

                    response_text = raw_api_response.choices[0].message.content
                    if not response_text:
                        console.error("OpenRouter 응답 텍스트가 비어있습니다")
                        return None

                    # JSON Schema 응답이므로 직접 파싱
                    structured_response = (
                        StructuredSynthesisResponse.model_validate_json(response_text)
                    )

                    if structured_response is None:
                        return None
            else:
                raise ValueError(f"지원하지 않는 프로바이더: {provider}")

            # 5. 응답 검증 및 반환
            if not structured_response:
                return None

            return SynthesisResult(
                summary=structured_response.summary,
                recommendations=structured_response.recommendations,
            )

        except Exception as e:
            console.error(f"LLM 합성 중 예외 발생: {e}")
            return None

    def _calculate_total_cost(
        self, successful_results: list[ReviewResult]
    ) -> EstimatedCost:
        """비용 합산 계산"""
        total_cost = EstimatedCost.get_zero_cost(self.model_name)

        for result in successful_results:
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

        return total_cost
