"""Versioned Pydantic contracts for deterministic evaluation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VersionRef(BaseModel):
    """Reference to a versioned review component."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    digest: str | None = None


class DiffSnapshot(BaseModel):
    """Immutable diff material captured for a review run."""

    model_config = ConfigDict(extra="forbid")

    base_sha: str
    head_sha: str
    patch: str
    sha256: str
    files: list[str]


class ContextChunk(BaseModel):
    """A context fragment made available to the reviewer."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    file: str
    start_line: int | None = None
    end_line: int | None = None
    content_sha256: str
    text: str | None = None
    strategy: str


class ToolCall(BaseModel):
    """A tool invocation observed during a review."""

    model_config = ConfigDict(extra="forbid")

    call_id: str
    name: str
    arguments: dict
    result_sha256: str | None = None
    status: str
    duration_ms: int


class Budget(BaseModel):
    """Resource usage for a review run."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    max_context_tokens: int | None = None
    cost_usd: float = 0
    wall_time_ms: int = 0


class Finding(BaseModel):
    """Normalized issue emitted by a review run."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    file: str
    start_line: int | None = None
    end_line: int | None = None
    category: str
    severity: str
    title: str
    description: str
    target_symbol: str | None = None
    evidence: list[str] = Field(default_factory=list)


class ReviewRun(BaseModel):
    """Replayable manifest for one code review execution."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "review-run/v1"
    run_id: str
    created_at: datetime
    source: dict
    diff: DiffSnapshot
    model: VersionRef
    prompt: VersionRef
    skills: list[VersionRef] = Field(default_factory=list)
    context_chunks: list[ContextChunk] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    budgets: Budget
    findings: list[Finding] = Field(default_factory=list)
    status: str
    error: str | None = None


ALLOWED_EXTERNAL_LICENSES = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "MPL-2.0",
    }
)


class DiffSource(BaseModel):
    """Synthetic inline diff or metadata-only external OSS diff.

    External source code is never stored in a fixture. It is resolved at runtime
    from the repository metadata after its license has passed the allowlist.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["synthetic", "external"]
    inline_patch: str | None = None
    repo_url: str | None = None
    commit_sha: str | None = None
    diff_range: str | None = None
    license_attribution: str | None = None
    license_kind: str | None = None

    @field_validator("license_kind")
    @classmethod
    def validate_license_kind(cls, value: str | None) -> str | None:
        """Accept only the explicitly approved OSS license identifiers."""
        if value is not None and value not in ALLOWED_EXTERNAL_LICENSES:
            allowed = ", ".join(sorted(ALLOWED_EXTERNAL_LICENSES))
            raise ValueError(f"license_kind must be one of: {allowed}")
        return value

    @model_validator(mode="after")
    def validate_source_shape(self) -> "DiffSource":
        """Keep synthetic code and external repository metadata disjoint."""
        external_fields = (
            "repo_url",
            "commit_sha",
            "diff_range",
            "license_attribution",
            "license_kind",
        )
        if self.kind == "synthetic":
            if self.inline_patch is None:
                raise ValueError("inline_patch is required for synthetic sources")
            populated = [
                name for name in external_fields if getattr(self, name) is not None
            ]
            if populated:
                names = ", ".join(populated)
                raise ValueError(f"synthetic sources forbid external fields: {names}")
            return self

        required = [name for name in external_fields if getattr(self, name) is None]
        if required:
            names = ", ".join(required)
            raise ValueError(f"external sources require fields: {names}")
        if self.inline_patch is not None:
            raise ValueError("inline_patch is forbidden for external sources")
        return self


class Location(BaseModel):
    """An expected finding location or symbol."""

    model_config = ConfigDict(extra="forbid")

    file: str
    start_line: int | None = None
    end_line: int | None = None
    symbol: str | None = None


class ExpectedFinding(BaseModel):
    """A positively labelled finding in a golden fixture."""

    model_config = ConfigDict(extra="forbid")

    id: str
    locations: list[Location]
    categories: set[str]
    severity: str
    aliases: set[str] = Field(default_factory=set)
    required: bool = True
    tags: set[str] = Field(default_factory=set)


class NegativeExpectation(BaseModel):
    """A finding category that must not be emitted."""

    model_config = ConfigDict(extra="forbid")

    id: str
    location: Location | None = None
    forbidden_categories: set[str] = Field(default_factory=set)


class GoldenFixture(BaseModel):
    """Versioned deterministic ground truth for a diff."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "golden/v1"
    case_id: str
    diff_source: DiffSource
    diff_sha256: str
    stack: str
    expected: list[ExpectedFinding]
    negatives: list[NegativeExpectation] = Field(default_factory=list)
    thresholds: dict[str, float]
    provenance: dict


class MetricResult(BaseModel):
    """One metric with an explicit denominator and visible N/A state."""

    model_config = ConfigDict(extra="forbid")

    value: float | None
    numerator: float
    denominator: float
    na_reason: str | None = None

    @model_validator(mode="after")
    def validate_na_state(self) -> "MetricResult":
        """Require an explanation whenever a metric is not applicable."""
        if self.value is None and self.na_reason is None:
            raise ValueError("na_reason is required when value is N/A")
        if self.value is not None and self.na_reason is not None:
            raise ValueError("na_reason is only valid when value is N/A")
        return self


class EvalReport(BaseModel):
    """Evaluation results containing both micro and macro aggregates."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "eval-report/v1"
    report_id: str
    created_at: datetime
    micro: dict[str, MetricResult]
    macro: dict[str, MetricResult]
    cases: dict[str, dict[str, MetricResult]] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
