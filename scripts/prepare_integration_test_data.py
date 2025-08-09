#!/usr/bin/env python3
"""통합 테스트용 데이터 준비 스크립트"""

import json
import pickle
from pathlib import Path
from typing import Any

from selvage.src.utils.prompts.models import (
    ReviewPromptWithFileContent,
    SystemPrompt,
    UserPromptWithFileContent,
)
from selvage.src.utils.token.token_utils import TokenUtils


def prepare_test_data():
    """통합 테스트용 데이터를 미리 준비하여 저장"""

    # review_log 디렉토리
    review_log_dir = Path.home() / "Library/Application Support/selvage/review_log"

    # 결과 저장 디렉토리
    test_data_dir = Path(__file__).parent.parent / "tests/data/multiturn_integration"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    print("=== 통합 테스트 데이터 준비 시작 ===")
    print(f"Review log 디렉토리: {review_log_dir}")
    print(f"테스트 데이터 저장 디렉토리: {test_data_dir}")

    # 파일별 토큰 수 저장
    file_tokens = []
    found_1m_file = None
    found_300k_file = None

    # 모든 review_log 파일들 스캔
    all_files = list(review_log_dir.glob("*.json"))
    print(f"Review log 파일 {len(all_files)}개 발견")

    for file_path in all_files:
        try:
            review_prompt = _load_review_prompt_from_file(file_path)
            if not review_prompt:
                continue

            # 토큰 수 계산
            token_count = TokenUtils.count_tokens(
                review_prompt, "claude-sonnet-4-20250514"
            )

            print(f"File: {file_path.name}, Tokens: {token_count:,}")

            if token_count > 0:
                file_info = {
                    "path": str(file_path),
                    "tokens": token_count,
                    "review_prompt": review_prompt,
                    "user_prompts_count": len(review_prompt.user_prompts),
                }
                file_tokens.append(file_info)

                # 1M+ 토큰 파일 발견시 우선 저장
                if token_count >= 1_000_000 and not found_1m_file:
                    found_1m_file = file_info
                    print(
                        f"✅ 1M+ 토큰 파일 발견: {file_path.name} ({token_count:,} 토큰)"
                    )

                # 300K+ 토큰 파일 발견시 저장 (더 큰 파일로 업데이트 가능)
                if token_count >= 300_000:
                    if not found_300k_file or token_count > found_300k_file["tokens"]:
                        found_300k_file = file_info
                        print(
                            f"✅ 300K+ 토큰 파일: {file_path.name} ({token_count:,} 토큰)"
                        )

                # 1M+ 파일을 찾았고 300K+ 파일도 있으면 조기 종료
                if found_1m_file and found_300k_file:
                    print(
                        f"✅ 목표 달성! 1M+: {found_1m_file['tokens']:,}, 300K+: {found_300k_file['tokens']:,}"
                    )
                    break

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue

    # 300K+ 테스트 파일 저장
    if found_300k_file:
        _save_test_prompt(
            found_300k_file["review_prompt"],
            test_data_dir / "large_300k_prompt.pkl",
            found_300k_file,
        )
    else:
        print("❌ 300K+ 토큰 파일을 찾지 못했습니다.")

    # 1M+ 테스트 파일 저장 (자연 파일 우선)
    if found_1m_file:
        # 자연적으로 1M+ 토큰 파일이 존재
        _save_test_prompt(
            found_1m_file["review_prompt"],
            test_data_dir / "natural_1m_prompt.pkl",
            found_1m_file,
        )
        print("✅ 자연적 1M+ 토큰 파일 사용 - 합성 불필요!")
    elif len(file_tokens) >= 3:
        # 자연 파일이 없으면 합성 생성
        print("⚙️ 1M+ 토큰 자연 파일 없음 - 합성 파일 생성")
        # 토큰 수 기준으로 내림차순 정렬
        file_tokens.sort(key=lambda x: x["tokens"], reverse=True)
        synthetic_prompt, synthetic_info = _create_synthetic_1m_prompt(file_tokens)
        if synthetic_prompt:
            _save_test_prompt(
                synthetic_prompt,
                test_data_dir / "synthetic_1m_prompt.pkl",
                synthetic_info,
            )
    else:
        print("❌ 1M+ 토큰 파일 생성 불가 - 충분한 파일이 없습니다.")

    print("=== 데이터 준비 완료 ===")


def _load_review_prompt_from_file(
    file_path: Path,
) -> ReviewPromptWithFileContent | None:
    """파일에서 ReviewPromptWithFileContent 로드"""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        prompt_data = data.get("prompt", [])
        if not prompt_data:
            return None

        # SystemPrompt와 UserPrompt 분리
        system_prompt = None
        user_prompts = []

        for msg in prompt_data:
            if msg["role"] == "system":
                system_prompt = SystemPrompt(role=msg["role"], content=msg["content"])
            elif msg["role"] == "user":
                try:
                    user_data = json.loads(msg["content"])
                    user_prompt = _create_user_prompt_from_json(user_data)
                    if user_prompt:
                        user_prompts.append(user_prompt)
                except (json.JSONDecodeError, KeyError):
                    continue

        if not system_prompt or not user_prompts:
            return None

        return ReviewPromptWithFileContent(
            system_prompt=system_prompt, user_prompts=user_prompts
        )

    except Exception as e:
        print(f"Error loading {file_path.name}: {e}")
        return None


def _create_user_prompt_from_json(
    user_data: dict[str, Any],
) -> UserPromptWithFileContent | None:
    """JSON 데이터에서 UserPromptWithFileContent 생성"""
    try:
        from selvage.src.context_extractor.line_range import LineRange
        from selvage.src.diff_parser.models.hunk import Hunk
        from selvage.src.utils.prompts.models import FileContextInfo

        file_name = user_data.get("file_name", "")
        file_content = user_data.get("file_content", "")

        # formatted_hunks에서 Hunk 생성
        hunks = []
        formatted_hunks = user_data.get("formatted_hunks", [])

        for hunk_data in formatted_hunks:
            # 라인 번호가 0이면 1로 설정 (최소값 보장)
            start_line = max(hunk_data.get("after_code_start_line_number", 1), 1)

            hunk = Hunk(
                header=f"@@ -{start_line},1 +{start_line},1 @@",
                content=hunk_data.get("after_code", ""),
                before_code=hunk_data.get("before_code", ""),
                after_code=hunk_data.get("after_code", ""),
                start_line_original=1,
                line_count_original=1,
                start_line_modified=start_line,
                line_count_modified=len(hunk_data.get("after_code", "").split("\n")),
                change_line=LineRange(
                    start_line=start_line,
                    end_line=start_line
                    + len(hunk_data.get("after_code", "").split("\n")),
                ),
            )
            hunks.append(hunk)

        return UserPromptWithFileContent(
            file_name=file_name,
            file_context=FileContextInfo.create_full_context(file_content),
            hunks=hunks,
            language=_detect_language(file_name),
        )

    except Exception as e:
        print(f"Error creating UserPromptWithFileContent: {e}")
        return None


def _detect_language(file_name: str) -> str:
    """파일명에서 언어 감지"""
    ext = Path(file_name).suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".md": "markdown",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return language_map.get(ext, "text")


def _create_synthetic_1m_prompt(
    file_tokens: list[dict],
) -> tuple[ReviewPromptWithFileContent | None, dict]:
    """여러 파일을 합쳐서 1M+ 토큰 합성 프롬프트 생성"""
    print("\n=== 1M 토큰 합성 프롬프트 생성 시작 ===")

    # 첫 번째 파일의 system_prompt 사용
    base_file = file_tokens[0]
    combined_system_prompt = base_file["review_prompt"].system_prompt
    combined_user_prompts = []
    total_tokens = 0
    used_files = []

    # 1M 토큰을 초과할 때까지 파일들을 합치기
    for file_info in file_tokens:
        if total_tokens > 1_000_000:
            break

        # 현재 파일의 user_prompts 추가
        review_prompt = file_info["review_prompt"]
        combined_user_prompts.extend(review_prompt.user_prompts)
        total_tokens += file_info["tokens"]
        used_files.append(Path(file_info["path"]).name)

        print(
            f"Added: {Path(file_info['path']).name} ({file_info['tokens']:,} tokens) - Total: {total_tokens:,}"
        )

    print(
        f"최종 합성 프롬프트: {len(used_files)}개 파일, {total_tokens:,} 토큰, {len(combined_user_prompts)}개 user_prompts"
    )

    # 합성된 ReviewPromptWithFileContent 생성
    synthetic_prompt = ReviewPromptWithFileContent(
        system_prompt=combined_system_prompt, user_prompts=combined_user_prompts
    )

    synthetic_info = {
        "total_tokens": total_tokens,
        "used_files": used_files,
        "user_prompts_count": len(combined_user_prompts),
        "type": "synthetic_1m",
    }

    return synthetic_prompt, synthetic_info


def _save_test_prompt(prompt: ReviewPromptWithFileContent, filepath: Path, info: dict):
    """테스트 프롬프트를 pickle 파일로 저장"""

    # pickle로 전체 객체 저장
    with open(filepath, "wb") as f:
        pickle.dump(prompt, f)

    # 정보만 JSON으로 저장 (객체 제외)
    info_file = filepath.with_suffix(".json")
    json_info = {k: v for k, v in info.items() if k != "review_prompt"}
    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(json_info, f, indent=2, ensure_ascii=False)

    print(
        f"저장 완료: {filepath} ({info.get('total_tokens', info.get('tokens', 0)):,} tokens)"
    )


if __name__ == "__main__":
    prepare_test_data()
