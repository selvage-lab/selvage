"""MCP 응답 모델 정의"""

from dataclasses import dataclass
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
    """Review history item"""

    log_id: str = Field(description="Log ID")
    timestamp: str = Field(description="Review timestamp (ISO 8601 format)")
    model: str = Field(description="Model used for review")
    files_count: int = Field(description="Number of files reviewed")
    status: str = Field(description="Review status (SUCCESS, FAILED)")
    cost: float = Field(description="Actual cost (USD)")


class ServerStatus(BaseModel):
    """MCP 서버 상태"""

    running: bool = Field(description="서버 실행 여부")
    port: int | None = Field(None, description="서버 포트")
    host: str | None = Field(None, description="서버 호스트")
    start_time: datetime | None = Field(None, description="서버 시작 시간")
    version: str = Field(description="Selvage 버전")
    tools_count: int = Field(description="등록된 도구 수")


@dataclass
class ValidationResult:
    """Internal validation result model for MCP tools."""

    success: bool
    error_message: str | None = None


@dataclass
class DiffContentResult:
    """Result model for diff content extraction/validation."""

    success: bool
    error_message: str | None
    diff_content: str | None


class ModelValidationResult(BaseModel):
    """모델 지원 여부 검증 결과"""

    valid: bool = Field(description="모델 지원 여부")
    model: str | None = Field(None, description="모델 이름")
    provider: str | None = Field(None, description="프로바이더 이름")
    error_message: str | None = Field(None, description="에러 메시지")


class ApiKeyValidationResult(BaseModel):
    """API 키 검증 결과"""

    valid: bool = Field(description="API 키 유효성")
    provider: str | None = Field(None, description="프로바이더 이름")
    api_key_configured: bool = Field(False, description="API 키 설정 여부")
    error_message: str | None = Field(None, description="에러 메시지")


class ReviewDetailsResult(BaseModel):
    """Review details result response model

    Structured review details information returned from MCP tools.

    Attributes:
        success: Review retrieval success status
        data: Review response data (on success)
        error_message: Error message (on failure)
    """

    success: bool = Field(description="Review retrieval success status")
    data: dict | None = Field(None, description="Review response data")
    error_message: str | None = Field(None, description="Error message (on failure)")


class ReviewContextResult(BaseModel):
    """에이전트 위임 리뷰용 컨텍스트 응답 모델

    get_review_context 도구에서 반환되는 구조화된 리뷰 컨텍스트입니다.
    에이전트가 이 데이터를 기반으로 직접 코드 리뷰를 수행합니다.

    컨텍스트가 CONTEXT_SIZE_LIMIT 이내이면 review_targets에 전체 데이터가 포함됩니다.
    초과 시에는 context_id와 file_list가 반환되며, 에이전트가
    get_file_review_context(context_id, file_path)로 파일별 조회합니다.
    """

    success: bool = Field(description="컨텍스트 생성 성공 여부")
    system_prompt: str | None = Field(None, description="코드 리뷰 시스템 프롬프트")
    review_targets: list[dict] = Field(
        default_factory=list,
        description="파일별 리뷰 컨텍스트 (system_prompt에 이어서 처리)",
    )
    output_format: dict | None = Field(
        None, description="기대하는 리뷰 결과 JSON 스키마"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="파일 수, 변경 라인 수 등 메타데이터",
    )
    error_message: str | None = Field(None, description="에러 메시지 (실패 시)")
    context_id: str | None = Field(
        None,
        description="분할 조회용 컨텍스트 ID (컨텍스트 초과 시에만 존재)",
    )
    file_list: list[str] = Field(
        default_factory=list,
        description="리뷰 대상 파일 목록 (분할 시에만 존재)",
    )


class FileReviewContextResult(BaseModel):
    """파일별 리뷰 컨텍스트 응답 모델

    get_file_review_context 도구에서 반환되는 개별 파일 리뷰 컨텍스트입니다.
    get_review_context가 context_id를 반환한 경우에만 사용합니다.
    """

    success: bool = Field(description="파일 컨텍스트 조회 성공 여부")
    file_path: str | None = Field(None, description="요청한 파일 경로")
    review_target: dict | None = Field(
        None, description="해당 파일의 리뷰 컨텍스트 (role + content)"
    )
    error_message: str | None = Field(None, description="에러 메시지")
