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


def _scan_eval_directory(eval_log_dir: Path) -> list[Path]:
    """eval 디렉토리에서 review_log 파일들을 스캔"""
    eval_files = []

    if not eval_log_dir.exists():
        print(f"⚠️ Eval 디렉토리가 존재하지 않습니다: {eval_log_dir}")
        return eval_files

    # {project_name}/{session_id}/qwen3_coder/ 구조를 순회
    for project_dir in eval_log_dir.iterdir():
        if not project_dir.is_dir():
            continue

        print(f"프로젝트 디렉토리 스캔 중: {project_dir.name}")

        for session_dir in project_dir.iterdir():
            if not session_dir.is_dir():
                continue

            # qwen3-coder 디렉토리 확인
            qwen_dir = session_dir / "qwen3-coder"
            if not qwen_dir.exists():
                continue

            # qwen3-coder 디렉토리 안의 모든 JSON 파일 수집
            for json_file in qwen_dir.glob("*.json"):
                eval_files.append(json_file)
                print(
                    f"  발견: {project_dir.name}/{session_dir.name}/qwen3-coder/{json_file.name}"
                )

    return eval_files


def prepare_test_data():
    """통합 테스트용 데이터를 미리 준비하여 저장"""

    # eval 디렉토리
    eval_log_dir = Path(
        "/Users/demin_coder/Library/selvage-eval/review_logs/eval_20250810_161628_8f6fb0bd"
    )

    # 결과 저장 디렉토리
    test_data_dir = Path(__file__).parent.parent / "tests/data/multiturn_integration"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    print("=== 통합 테스트 데이터 준비 시작 ===")
    print(f"Eval log 디렉토리: {eval_log_dir}")
    print(f"테스트 데이터 저장 디렉토리: {test_data_dir}")

    # 파일별 토큰 수 저장
    file_tokens = []

    # eval 디렉토리에서 파일들 스캔
    all_files = _scan_eval_directory(eval_log_dir)
    print(f"Eval 디렉토리에서 {len(all_files)}개 파일 발견")

    for file_path in all_files:
        try:
            review_prompt, token_count = _load_review_prompt_from_file(file_path)
            if not review_prompt:
                continue

            print(f"File: {file_path.name}, Tokens: {token_count:,}")

            if token_count > 0:
                file_info = {
                    "path": str(file_path),
                    "tokens": token_count,
                    "review_prompt": review_prompt,
                    "user_prompts_count": len(review_prompt.user_prompts),
                }
                file_tokens.append(file_info)

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue

    # 300K+ 토큰 파일들을 토큰 수 기준으로 내림차순 정렬
    large_files = [f for f in file_tokens if f["tokens"] >= 300_000]
    large_files.sort(key=lambda x: x["tokens"], reverse=True)

    print(f"\\n=== 300K+ 토큰 파일 {len(large_files)}개 발견 ===")

    # 상위 5개 파일 저장
    top_count = min(5, len(large_files))
    for i in range(top_count):
        file_info = large_files[i]
        filename = f"top{i + 1}_300k_prompt.pkl"
        _save_test_prompt(
            file_info["review_prompt"],
            test_data_dir / filename,
            file_info,
        )
        print(f"저장: {filename} - {file_info['tokens']:,} tokens")

    if len(large_files) == 0:
        print("❌ 300K+ 토큰 파일을 찾지 못했습니다.")
    else:
        print(f"✅ 상위 {top_count}개 파일 저장 완료")

    print("=== 데이터 준비 완료 ===")


def _load_review_prompt_from_file(
    file_path: Path,
) -> tuple[ReviewPromptWithFileContent | None, int]:
    """파일에서 ReviewPromptWithFileContent 로드 및 토큰 정보 반환"""
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # 토큰 정보 추출
        token_info = data.get("token_info", {})
        input_tokens = token_info.get("input_tokens", 0)

        prompt_data = data.get("prompt", [])
        if not prompt_data:
            return None, input_tokens

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
            return None, input_tokens

        review_prompt = ReviewPromptWithFileContent(
            system_prompt=system_prompt, user_prompts=user_prompts
        )
        return review_prompt, input_tokens

    except Exception as e:
        print(f"Error loading {file_path.name}: {e}")
        return None, 0


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
