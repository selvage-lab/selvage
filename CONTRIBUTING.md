# 기여 가이드 (Contributing to Selvage)

Selvage에 관심을 가지고 기여해주셔서 감사합니다! 저희는 커뮤니티의 참여를 소중하게 생각하며, 더 나은 AI 기반 코드 리뷰 도구를 만들기 위해 여러분의 도움을 환영합니다.

본 문서는 Selvage에 기여하는 방법에 대한 가이드라인을 제공합니다. 기여하기 전에 잠시 시간을 내어 읽어보시면 원활한 협업에 도움이 될 것입니다.

## 🤝 기여 방법

저희는 다양한 형태의 기여를 환영합니다. Selvage는 MIT 라이선스 하에 완전한 오픈소스 프로젝트로서, 커뮤니티의 자유로운 참여와 기여를 장려합니다.

### 🐛 버그 리포트 (Bug Reports)

버그를 발견하셨다면 언제든지 [GitHub Issues](https://github.com/selvage-team/selvage/issues)를 통해 알려주세요.

**이슈 작성 시 포함해주실 정보:**

- **환경 정보**: 운영체제, Python 버전, Selvage 버전
- **사용한 명령어**: 실행한 selvage 명령어와 옵션
- **사용한 AI 모델**: 어떤 모델을 사용했는지 (예: claude-sonnet-4-thinking)
- **재현 단계**: 버그를 재현할 수 있는 단계별 설명
- **예상 결과 vs 실제 결과**: 무엇을 기대했고 실제로는 무엇이 일어났는지
- **로그 및 오류 메시지**: 관련 에러 메시지나 로그 (가능하다면)
- **Git diff 샘플**: 문제가 발생한 코드 변경사항 (민감하지 않은 범위에서)

### ✨ 기능 제안 (Feature Requests)

새로운 기능이나 개선 아이디어가 있다면 [GitHub Issues](https://github.com/selvage-team/selvage/issues)를 통해 제안해주세요.

**제안 시 포함해주실 정보:**

- **기능 설명**: 제안하는 기능에 대한 명확한 설명
- **사용 사례**: 어떤 상황에서 이 기능이 유용할지
- **기대 효과**: 이 기능이 가져올 개선점
- **대안 검토**: 기존 기능으로 해결 가능한지 검토한 내용

### 🛠️ 코드 기여 (Code Contributions)

#### 환영하는 기여 유형:

- **버그 수정**: 발견된 버그 해결
- **기능 개선**: 기존 기능의 성능, 사용성 개선
- **새로운 기능**: 커뮤니티에서 요청된 새로운 기능
- **테스트 추가**: 테스트 커버리지 향상
- **리팩토링**: 코드 품질 및 구조 개선
- **AI 모델 지원 확대**: 새로운 LLM 모델 또는 제공자 추가

#### 시작하기 좋은 이슈:

`good first issue`, `help wanted`, `bug` 라벨이 붙은 이슈를 확인해보세요.

### 📚 문서 개선 (Documentation Improvements)

문서 기여는 언제나 환영합니다:

- **README 개선**: 사용법, 예시 추가
- **API 문서**: 코드 주석 및 docstring 개선
- **튜토리얼**: 사용 사례별 가이드 작성
- **번역**: 다국어 문서 지원
- **오타 수정**: 맞춤법, 문법 오류 수정

## 📝 Pull Request (PR) 절차

### 1. 개발 환경 설정

```bash
# 저장소 Fork 후 클론
git clone https://github.com/YOUR_USERNAME/selvage.git
cd selvage

# 개발 환경 설치
pip install -e .[dev,e2e]

# 테스트 실행하여 환경 확인
pytest tests/
```

### 2. 브랜치 생성 및 개발

```bash
# 새 브랜치 생성
git checkout -b feat/your-feature-name
# 또는
git checkout -b fix/issue-number

# 코드 작성 및 수정
# ... 개발 작업 ...

# 테스트 실행
pytest tests/

# 코드 스타일 검사 (Ruff 사용)
ruff check .
ruff format .
```

### 3. 커밋 및 푸시

```bash
# 의미있는 커밋 메시지로 커밋
git add .
git commit -m "feat: add new feature for XYZ"

# 브랜치 푸시
git push origin feat/your-feature-name
```

### 4. Pull Request 생성

GitHub에서 Pull Request를 생성할 때:

**PR 제목 작성 규칙:**

- `feat: 새로운 기능 추가`
- `fix: 버그 수정`
- `docs: 문서 개선`
- `test: 테스트 추가/수정`
- `refactor: 코드 리팩토링`

**PR 설명에 포함할 내용:**

- 변경 사항 요약
- 관련 이슈 번호 (예: `Closes #123`)
- 테스트 방법 및 결과
- 스크린샷 (UI 변경 시)
- 체크리스트 (아래 템플릿 사용)

**PR 체크리스트:**

```markdown
- [ ] 테스트를 추가했거나 기존 테스트가 통과합니다
- [ ] 코드가 프로젝트의 스타일 가이드를 준수합니다
- [ ] 문서를 업데이트했습니다 (필요한 경우)
- [ ] 변경 사항이 기존 기능을 손상시키지 않습니다
```

## ✅ 코드 검토 (Code Review)

### 검토 기준:

- **기능성**: 의도한 대로 동작하는가?
- **코드 품질**: 읽기 쉽고 유지보수 가능한가?
- **테스트**: 적절한 테스트가 포함되어 있는가?
- **문서화**: 필요한 문서가 업데이트되었는가?
- **호환성**: 기존 기능을 손상시키지 않는가?

### 검토 과정:

1. 자동화된 테스트 통과 확인
2. 코드 스타일 검사 (Ruff) 통과 확인
3. 관리팀의 코드 리뷰
4. 필요시 수정 요청 및 재검토
5. 승인 후 병합

## 🔧 개발 가이드라인

### 코드 스타일

Selvage는 다음 코딩 스타일을 따릅니다:

- **포매터**: Ruff format 사용
- **린터**: Ruff lint 사용
- **타입 힌팅**: 모든 함수에 타입 힌팅 적용
- **Docstring**: Google 스타일 docstring 사용

### 테스트 작성

- **단위 테스트**: 새로운 함수/클래스에 대한 단위 테스트
- **E2E 테스트**: 전체 워크플로우에 대한 종단간 테스트

### 커밋 메시지 규칙

#### Selvage 프로젝트 권장 형식:

```
<feat | fix>: <summarized description>
  - [detail messages]

Refs: [Branch Name]
```

**예시:**

```
feat: Claude Sonnet-4 모델 지원 추가
  - Anthropic Claude Sonnet-4 모델을 지원 모델 목록에 추가
  - 모델 설정 및 API 호출 로직 구현
  - 관련 테스트 케이스 작성

Refs: feature/claude-sonnet-4-support
```

**Type 종류:**

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드 과정, 도구 설정 등

## 🌟 오픈소스 정신

Selvage는 MIT 라이선스 하에 완전한 오픈소스 프로젝트입니다. 우리는 다음 가치를 추구합니다:

- **투명성**: 모든 개발 과정이 공개되고 투명합니다
- **포용성**: 모든 배경의 기여자를 환영합니다
- **협력**: 커뮤니티와 함께 더 나은 도구를 만들어갑니다
- **품질**: 높은 코드 품질과 사용자 경험을 추구합니다

## 📞 소통 채널

- **이슈 및 토론**: [GitHub Issues](https://github.com/selvage-team/selvage/issues)
- **직접 문의**: anomie7777@gmail.com
- **코드 기여**: Pull Request를 통한 기여

## 📜 행동 강령 (Code of Conduct)

모든 참여자는 상호 존중과 포용의 정신으로 참여해주시기 바랍니다:

- 다른 참여자를 존중하고 배려합니다
- 건설적인 피드백을 제공합니다
- 다양한 관점과 경험을 인정합니다
- 프로젝트 목표에 집중합니다

---

**Selvage에 기여해주셔서 진심으로 감사합니다! 🚀**

여러분의 기여가 전 세계 개발자들의 코드 리뷰 경험을 향상시키는 데 도움이 됩니다.
