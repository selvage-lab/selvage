# ROLE

당신은 문제 해결 중심의 정확하고 충실한 테크니컬 라이터입니다.
아래 지시 사항을 충실히 이행해주세요.

# PROBLEM

현재 코드 리뷰 애플리케이션에서는 llm에게 리뷰를 받은 데이터를 deepeval로 llm_eval하고 있습니다.
deepeval의 metric을 통해 평가하고 있으며, 아래는 llm_eval fail(score가 threshold에 미치치 못한 결과)한 결과들입니다.
json 형식이며, 영어로 fail reason이 적혀있어 평가가 어렵니다.

## INSTRUCTIONS

1. 각 testCase의 metricsData만 추출해주세요.
   ```python
     metric = [metric for case in testCases for metric in case['metricsData']]
   ```
2. 각 testCase의 metricsData.reason들을 번역해주세요.
   ```python
     reason = [metric['reason'] for case in testCases for metric in case['metricsData']]
     translate_to_korean(reason)
   ```
3. reason이 준 의견을 토대로 input(프롬프트), actualOutput에서 어디가 문제인지 관련된 부분만 같이 첨부해주세요.
   만약 문제가 없다면(threshold를 pass) 생략 가능
4. json와 별개로 reason의 결과를 종합한 의견을 첨부해주세요.

# reason이 영어로 되어있고, input, actualOutput이 방대해서 보기가 힘들어서 요청하는 사항입니다. 가독성을 고려해서 편집해서 반환해주세요.

## METRICS_DESCRIPTION

```python
correctness = GEval(
    name="Correctness",
    model=model,
    evaluation_steps=[
        "Verify that the issues identified in the code review match the actual code changes.",
        "Check if filenames and line numbers are accurately specified.",
        "Evaluate whether the identified issue types (bug, security, performance, style, design) are appropriate for the code.",
        "Confirm that severity levels (info, warning, error) are assigned appropriately based on the actual importance of the issue.",
        "Review whether the issue descriptions accurately reflect the actual impact of the code changes.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
    threshold=0.7,
)
```

```python
clarity = GEval(
    name="Clarity",
    model=model,
    evaluation_steps=[
        "Evaluate whether the code review explanations use concise and direct language.",
        "Check if technical terms or jargon are properly explained.",
        "Assess whether issue descriptions and suggestions are specific and clear.",
        "Review if the purpose and intent of code changes are clearly understandable.",
        "Verify that improved code examples are provided and easy to understand.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
    threshold=0.7,
)
```

```python
actionability = GEval(
    name="Actionability",
    model=model,
    evaluation_steps=[
        "각 이슈에 대해 구체적인 해결책이 제시되었는지 확인합니다.",
        "제안된 개선 사항이 실제로 구현 가능한지 평가합니다.",
        "코드 개선 예시가 실제 코드베이스에 통합될 수 있을 만큼 구체적인지 검토합니다.",
        "제안이 코드 품질, 성능, 보안 등의 측면에서 실질적인 개선을 가져올 수 있는지 평가합니다.",
        "전반적인 권장사항이 프로젝트 맥락에서 실행 가능한지 확인합니다.",
    ],
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
    threshold=0.7,
)
```

```python
jsoncorrectness = JsonCorrectnessMetric(
    expected_schema=StructuredReviewResponse(
        issues=[
            StructuredReviewIssue(
                type="",
                line_number=0,
                file="",
                description="",
                suggestion="",
                severity=IssueSeverityEnum.INFO,
                original_code="",
                improved_code="",
            )
        ],
        summary="",
        score=0,
        recommendations=[],
    ),
    model=model,
    include_reason=True,
)
```

## FAILED_RESULT_FROM_LLM_EVAL(JSON)

```json
[]
```
