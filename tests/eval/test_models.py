"""Contract tests for review-run/v1 and golden/v1 models."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from selvage.src.eval.models import (
    Budget,
    ContextChunk,
    DiffSnapshot,
    EvalReport,
    ExpectedFinding,
    Finding,
    GoldenFixture,
    Location,
    MetricResult,
    NegativeExpectation,
    ReviewRun,
    ToolCall,
    VersionRef,
)
from selvage.src.eval.schema_export import schema_documents


def _instances() -> list[BaseModel]:
    version = VersionRef(name="selvage", version="v4", digest="sha256:prompt")
    diff = DiffSnapshot(
        base_sha="a" * 40,
        head_sha="b" * 40,
        patch="diff --git a/app.py b/app.py\n",
        sha256="c" * 64,
        files=["app.py"],
    )
    chunk = ContextChunk(
        chunk_id="chunk-1",
        file="app.py",
        start_line=1,
        end_line=4,
        content_sha256="d" * 64,
        text="def f():\n    pass\n",
        strategy="smart",
    )
    tool_call = ToolCall(
        call_id="call-1",
        name="read_file",
        arguments={"path": "app.py"},
        result_sha256="e" * 64,
        status="success",
        duration_ms=5,
    )
    budget = Budget(input_tokens=10, output_tokens=20, wall_time_ms=30)
    finding = Finding(
        finding_id="finding-1",
        file="app.py",
        start_line=2,
        end_line=2,
        category="correctness",
        severity="error",
        title="Incorrect return",
        description="The function returns the wrong value.",
        evidence=["return False"],
    )
    run = ReviewRun(
        run_id="run-1",
        created_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        source={"repo": "selvage", "commit": "b" * 40},
        diff=diff,
        model=VersionRef(name="provider/model", version="2026-07-18"),
        prompt=version,
        skills=[VersionRef(name="review", version="1")],
        context_chunks=[chunk],
        tool_calls=[tool_call],
        budgets=budget,
        findings=[finding],
        status="success",
    )
    location = Location(file="app.py", start_line=2, end_line=2, symbol="f")
    expected = ExpectedFinding(
        id="expected-1",
        locations=[location],
        categories={"correctness"},
        severity="error",
        aliases={"logic"},
        tags={"caller"},
    )
    negative = NegativeExpectation(
        id="negative-1",
        location=location,
        forbidden_categories={"style"},
    )
    fixture = GoldenFixture(
        case_id="python-wrong-return",
        diff_source={"kind": "synthetic", "inline_patch": diff.patch},
        diff_sha256=diff.sha256,
        stack="python",
        expected=[expected],
        negatives=[negative],
        thresholds={"precision": 0.8, "recall": 0.8},
        provenance={"source_sha": "b" * 40, "labelers": ["alice", "bob"]},
    )
    report = EvalReport(
        report_id="report-1",
        created_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        micro={
            "precision": MetricResult(value=1.0, numerator=1, denominator=1),
            "false_positive_rate": MetricResult(
                value=None,
                numerator=0,
                denominator=0,
                na_reason="no negative expectations",
            ),
        },
        macro={"precision": MetricResult(value=1.0, numerator=1, denominator=1)},
    )
    return [
        version,
        diff,
        chunk,
        tool_call,
        budget,
        finding,
        run,
        location,
        expected,
        negative,
        fixture,
        report.micro["precision"],
        report,
    ]


@pytest.mark.parametrize("instance", _instances())
def test_models_round_trip(instance: BaseModel) -> None:
    payload = json.dumps(instance.model_dump(mode="json"))

    restored = type(instance).model_validate_json(payload)

    assert restored == instance


@pytest.mark.parametrize("instance", _instances())
def test_all_models_forbid_extra_fields(instance: BaseModel) -> None:
    payload = instance.model_dump(mode="json")
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="unexpected"):
        type(instance).model_validate(payload)


def test_schema_version_defaults() -> None:
    run = next(item for item in _instances() if isinstance(item, ReviewRun))
    fixture = next(item for item in _instances() if isinstance(item, GoldenFixture))
    report = next(item for item in _instances() if isinstance(item, EvalReport))

    assert run.schema_version == "review-run/v1"
    assert fixture.schema_version == "golden/v1"
    assert report.schema_version == "eval-report/v1"


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (VersionRef, {"name": "prompt"}),
        (
            DiffSnapshot,
            {"base_sha": "a", "head_sha": "b", "patch": "", "sha256": "c"},
        ),
        (ReviewRun, {"run_id": "run-1"}),
        (Location, {}),
        (ExpectedFinding, {"id": "finding-1"}),
        (GoldenFixture, {"case_id": "case-1"}),
        (EvalReport, {"report_id": "report-1"}),
    ],
)
def test_required_fields(model: type[BaseModel], payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_metric_result_exposes_zero_denominator_as_na() -> None:
    result = MetricResult(
        value=None,
        numerator=0,
        denominator=0,
        na_reason="no negative expectations",
    )

    assert result.value is None
    assert result.na_reason == "no negative expectations"


def test_metric_result_rejects_hidden_na_state() -> None:
    with pytest.raises(ValidationError):
        MetricResult(value=None, numerator=0, denominator=0)


def test_exported_schemas_match_committed_contracts() -> None:
    schema_dir = Path(__file__).parents[2] / "eval" / "schemas"

    for filename, schema in schema_documents().items():
        committed = json.loads((schema_dir / filename).read_text(encoding="utf-8"))
        assert committed == schema
