"""ReviewFormatter: 리뷰 결과를 다양한 형식으로 변환하는 로직을 포함한 모듈."""

import html

from selvage.src.utils.language_detector import detect_language_from_filename
from selvage.src.utils.token.models import ReviewResponse


class ReviewFormatter:
    """리뷰 결과를 다양한 형식으로 변환하는 클래스.

    이 클래스는 리뷰 응답을 마크다운, HTML 등 다양한 출력 형식으로
    변환하는 기능을 제공합니다.
    """

    def format(self, review: ReviewResponse, output_format: str = "markdown") -> str:
        """리뷰 결과를 지정된 형식으로 변환합니다.

        Args:
            review: 리뷰 응답 객체
            output_format: 출력 형식 (markdown, html)

        Returns:
            str: 변환된 리뷰 결과

        Raises:
            ValueError: 지원하지 않는 출력 형식인 경우
        """
        if output_format == "markdown":
            return self.to_markdown(review)
        elif output_format == "html":
            return self.to_html(review)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    @staticmethod
    def _format_code_block(
        code: str | None, header: str, language: str | None = None
    ) -> list[str]:
        """마크다운 코드 블록을 포맷합니다.

        코드가 이미 백틱으로 감싸져 있으면 그대로 사용합니다.

        Args:
            code: 포맷할 코드 문자열
            header: 코드 블록 앞에 붙을 헤더 문자열 (예: "**리뷰 대상 코드**:\n")

        Returns:
            list[str]: 포맷된 마크다운 라인 리스트
        """
        lines = []
        if code:
            # 코드 앞뒤 공백 제거 후 검사
            stripped_code = code.strip()
            if stripped_code.startswith("```") and stripped_code.endswith("```"):
                # 이미 코드 블록 형식이면, 원본 문자열을 그대로 사용
                lines.append(header + "\n" + code)
            else:
                fence = f"```{language}" if language else "```"
                lines.append(f"{header}\n{fence}\n{code}\n```\n")
        return lines

    @staticmethod
    def to_markdown(review: ReviewResponse) -> str:
        """리뷰 결과를 마크다운 형식으로 변환합니다.

        Args:
            review: 리뷰 응답 객체

        Returns:
            str: 마크다운 형식의 리뷰 결과
        """
        md_lines = ["# 코드 리뷰 결과\n"]

        # 요약 및 점수
        md_lines.append("## 요약\n")
        md_lines.append(f"{review.summary}\n")

        if review.score is not None:
            md_lines.append(f"**점수**: {review.score}/10\n")

        # 이슈 목록
        if review.issues:
            md_lines.append("## 발견된 이슈\n")

            for i, issue in enumerate(review.issues, 1):
                severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🛑"}.get(
                    issue.severity, "ℹ️"
                )
                language = None
                md_lines.append(f"### {i}. {severity_emoji} {issue.type}\n")

                if issue.file:
                    file_info = f"**파일**: `{issue.file}`"
                    if issue.line_number:
                        file_info += f", **라인**: {issue.line_number}"
                    md_lines.append(f"{file_info}\n")
                    language = detect_language_from_filename(issue.file)

                md_lines.append(f"**설명**: {issue.description}\n")

                if issue.suggestion:
                    md_lines.append(f"**제안**: {issue.suggestion}\n")

                # 리뷰 대상 코드 추가

                md_lines.extend(
                    ReviewFormatter._format_code_block(
                        issue.target_code, "**리뷰 대상 코드**:", language
                    )
                )

                # 개선된 코드 추가
                md_lines.extend(
                    ReviewFormatter._format_code_block(
                        issue.suggested_code, "**개선된 코드**:", language
                    )
                )

        # 권장사항
        if review.recommendations:
            md_lines.append("## 권장사항\n")
            for i, rec in enumerate(review.recommendations, 1):
                md_lines.append(f"{i}. {rec}\n")

        return "\n".join(md_lines)

    @staticmethod
    def to_html(review: ReviewResponse) -> str:
        """리뷰 결과를 HTML 형식으로 변환합니다.

        Args:
            review: 리뷰 응답 객체

        Returns:
            str: HTML 형식의 리뷰 결과
        """
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>코드 리뷰 결과</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; line-height: 1.6; "
            "max-width: 800px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #444; border-bottom: 1px solid #eee; padding-bottom: 5px; }",
            "h3 { color: #555; }",
            ".issue { padding: 10px; margin-bottom: 15px; }",
            ".info {  }",
            ".warning {  }",
            ".error {  }",
            ".file-info { font-family: monospace; background-color: #eee; "
            "padding: 3px 5px; border-radius: 3px; }",
            ".recommendations { padding: 10px; border-radius: 5px; }",
            "</style>",
            "<style>",
            "pre { background-color: #f5f5f5; padding: 10px; "
            "border-radius: 5px; overflow-x: auto; }",
            "code { font-family: 'Courier New', Courier, monospace; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>코드 리뷰 결과</h1>",
        ]

        # 요약 및 점수
        html_lines.append("<h2>요약</h2>")
        html_lines.append(f"<p>{html.escape(review.summary)}</p>")

        if review.score is not None:
            html_lines.append(f"<p><strong>점수</strong>: {review.score}/10</p>")

        # 이슈 목록
        if review.issues:
            html_lines.append("<h2>발견된 이슈</h2>")

            for i, issue in enumerate(review.issues, 1):
                severity_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🛑"}.get(
                    issue.severity, "ℹ️"
                )

                html_lines.append(f"<div class='issue {issue.severity}'>")
                html_lines.append(f"<h3>{i}. {severity_emoji} {issue.type}</h3>")
                language = None
                if issue.file:
                    file_info = (
                        "<strong>파일</strong>: "
                        f"<span class='file-info'>{issue.file}</span>"
                    )
                    if issue.line_number:
                        file_info += f", <strong>라인</strong>: {issue.line_number}"
                    html_lines.append(f"<p>{file_info}</p>")
                    html_lines.append(
                        f"<p><strong>설명</strong>: {issue.description}</p>"
                    )
                    language = detect_language_from_filename(issue.file)

                if issue.suggestion:
                    html_lines.append(
                        f"<p><strong>제안</strong>: {issue.suggestion}</p>"
                    )

                # 리뷰 대상 코드 추가
                if issue.target_code:
                    html_lines.append("<p><strong>리뷰 대상 코드</strong>:</p>")
                    html_lines.append(
                        f"<pre><code class='language-{language}'>"
                        f"{html.escape(issue.target_code)}</code></pre>"
                    )

                # 개선된 코드 추가
                if issue.suggested_code:
                    html_lines.append("<p><strong>개선된 코드</strong>:</p>")
                    html_lines.append(
                        f"<pre><code class='language-{language}'>"
                        f"{html.escape(issue.suggested_code)}</code></pre>"
                    )

                html_lines.append("</div>")

        # 권장사항
        if review.recommendations:
            html_lines.append("<h2>권장사항</h2>")
            html_lines.append("<div class='recommendations'>")
            html_lines.append("<ol>")
            for rec in review.recommendations:
                html_lines.append(f"<li>{rec}</li>")
            html_lines.append("</ol>")
            html_lines.append("</div>")

        html_lines.extend(["</body>", "</html>"])

        return "\n".join(html_lines)
