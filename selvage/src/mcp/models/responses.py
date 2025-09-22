"""MCP 응답 모델 정의"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from selvage.src.utils.token.models import ReviewResponse


class ReviewResult(BaseModel):
    """코드 리뷰 결과 응답 모델

    MCP 도구에서 반환되는 구조화된 리뷰 결과입니다.

    Attributes:
        success: 리뷰 성공 여부
        response: 전체 ReviewResponse (issues, summary, score, recommendations)
        estimated_cost: 예상 비용 (USD)
        model_used: 사용된 AI 모델
        files_reviewed: 리뷰된 파일 목록
        log_id: 로그 ID
        log_path: 로그 파일 경로
        timestamp: 리뷰 완료 시간
        error_message: 에러 메시지 (실패 시)
    """

    success: bool = Field(description="리뷰 성공 여부")
    # 전체 리뷰 응답(issues/summary/score/recommendations)을 포함해 클라이언트에 전달
    response: ReviewResponse | None = Field(
        None, description="전체 ReviewResponse 페이로드"
    )
    estimated_cost: float = Field(0.0, description="예상 비용 (USD)")
    model_used: str = Field(description="사용된 AI 모델")
    files_reviewed: list[str] = Field(
        default_factory=list, description="리뷰된 파일 목록"
    )
    log_id: str | None = Field(None, description="로그 ID")
    log_path: str | None = Field(None, description="로그 파일 경로")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="리뷰 완료 시간"
    )
    error_message: str | None = Field(None, description="에러 메시지 (실패 시)")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        """timestamp를 ISO 형식 문자열로 직렬화"""
        return value.isoformat()


class ModelInfo(BaseModel):
    """AI 모델 정보"""

    name: str = Field(description="모델 이름")
    provider: str = Field(
        description="프로바이더 (openai, anthropic, google, openrouter)"
    )
    display_name: str = Field(description="표시용 이름")
    description: str = Field(description="모델 설명")
    cost_per_1k_tokens: float = Field(description="1000토큰당 비용 (USD)")
    max_tokens: int = Field(description="최대 토큰 수")
    supports_function_calling: bool = Field(
        default=False, description="함수 호출 지원 여부"
    )


class ReviewHistoryItem(BaseModel):
    """리뷰 히스토리 항목"""

    log_id: str = Field(description="로그 ID")
    timestamp: datetime = Field(description="리뷰 시간")
    model: str = Field(description="사용된 모델")
    files_count: int = Field(description="리뷰된 파일 수")
    status: str = Field(description="리뷰 상태 (SUCCESS, FAILED)")
    cost: float = Field(description="실제 비용 (USD)")
    review_type: str = Field(description="리뷰 타입 (current, staged, branch, commit)")
    target: str | None = Field(
        None, description="타겟 브랜치 또는 커밋 (해당되는 경우)"
    )


class ServerStatus(BaseModel):
    """MCP 서버 상태"""

    running: bool = Field(description="서버 실행 여부")
    port: int | None = Field(None, description="서버 포트")
    host: str | None = Field(None, description="서버 호스트")
    start_time: datetime | None = Field(None, description="서버 시작 시간")
    version: str = Field(description="Selvage 버전")
    tools_count: int = Field(description="등록된 도구 수")
