"""Validation tests for licensed synthetic and external diff sources."""

import pytest
from pydantic import ValidationError

from selvage.src.eval.models import DiffSource


def test_synthetic_requires_inline_patch() -> None:
    with pytest.raises(ValidationError, match="inline_patch"):
        DiffSource(kind="synthetic")


@pytest.mark.parametrize("forbidden", ["repo_url", "commit_sha"])
def test_synthetic_forbids_external_repository_fields(forbidden: str) -> None:
    payload = {"kind": "synthetic", "inline_patch": "diff --git a/a b/a\n"}
    payload[forbidden] = (
        "https://example.com/repo.git" if forbidden == "repo_url" else "abc"
    )

    with pytest.raises(ValidationError, match=forbidden):
        DiffSource.model_validate(payload)


def test_external_requires_all_attribution_fields() -> None:
    required = {
        "repo_url": "https://example.com/repo.git",
        "commit_sha": "a" * 40,
        "diff_range": "HEAD^..HEAD",
        "license_attribution": "Copyright Example Authors, MIT License",
        "license_kind": "MIT",
    }
    for missing in required:
        payload = {"kind": "external", **required}
        del payload[missing]
        with pytest.raises(ValidationError, match=missing):
            DiffSource.model_validate(payload)


def test_external_forbids_inline_patch() -> None:
    with pytest.raises(ValidationError, match="inline_patch"):
        DiffSource(
            kind="external",
            inline_patch="external code must not be stored",
            repo_url="https://example.com/repo.git",
            commit_sha="a" * 40,
            diff_range="HEAD^..HEAD",
            license_attribution="Copyright Example Authors",
            license_kind="MIT",
        )


@pytest.mark.parametrize(
    "license_kind",
    [
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "MPL-2.0",
    ],
)
def test_external_accepts_whitelisted_licenses(license_kind: str) -> None:
    source = DiffSource(
        kind="external",
        repo_url="https://example.com/repo.git",
        commit_sha="a" * 40,
        diff_range="HEAD^..HEAD",
        license_attribution="Copyright Example Authors",
        license_kind=license_kind,
    )

    assert source.license_kind == license_kind


@pytest.mark.parametrize(
    "license_kind", ["GPL-3.0", "LGPL-3.0", "AGPL-3.0", "Commercial"]
)
def test_external_rejects_non_whitelisted_licenses(license_kind: str) -> None:
    with pytest.raises(ValidationError, match="license_kind"):
        DiffSource(
            kind="external",
            repo_url="https://example.com/repo.git",
            commit_sha="a" * 40,
            diff_range="HEAD^..HEAD",
            license_attribution="Copyright Example Authors",
            license_kind=license_kind,
        )


def test_diff_source_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError, match="mirror_url"):
        DiffSource(
            kind="synthetic",
            inline_patch="diff --git a/a b/a\n",
            mirror_url="https://example.com/mirror.git",
        )
