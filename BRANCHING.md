# Branching Policy

selvage는 3-티어 브랜치 모델을 사용합니다.

## 브랜치 구조

| 브랜치 | 용도 | 권한 |
|---|---|---|
| `main` | 프로덕션 릴리스. tag `vX.Y.Z`로 PyPI 정식 배포 | 관리자만 머지 |
| `develop` | Sprint 통합 지점. TestPyPI 자동 배포 | 관리자 + 핵심 기여자 |
| `feature/*` | 개별 task 작업. PR → develop | 누구나 생성 |

## 워크플로우

1. **feature 브랜치 생성**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/sprint-N-<topic>
   ```

2. **작업 + 커밋** (Conventional Commits 준수)
   - `feat:` 새 기능
   - `fix:` 버그 수정
   - `chore:` 설정, 의존성, 문서
   - `ci:` CI/CD 변경
   - `docs:` 문서만 변경

3. **PR 생성**: `feature/* → develop`
   - CI 자동 실행 (pytest, ruff, build)
   - 모두 통과 시 머지 가능

4. **develop → main PR** (Sprint 종료 시)
   - 관리자가 squash merge
   - main push → PyPI 정식 배포 + tag + GitHub Release 자동

## 네이밍 컨벤션

- `feature/sprint-N-<topic>` — Sprint N의 개별 task (예: `feature/sprint-0a-ci-yaml`)
- `fix/<topic>` — 버그 수정
- `chore/<topic>` — 설정, 문서, 의존성
- `release/vX.Y.Z` — 릴리스 준비 (필요 시)

## 보호 규칙 (GitHub Settings)

- `main`: PR required, status checks (CI) required, dismiss stale reviews
- `develop`: PR required, status checks (CI) required
- `feature/*`: 자유 (fork-equivalent)

## CI/CD 파이프라인 요약

```
feature/* → PR → develop    [ci.yml: pytest + ruff + build]
develop  push              [release.yml: TestPyPI + Docker e2e]
main     merge             [release.yml: PyPI + tag + GitHub Release]
```

자세한 사양은 `docs/superpowers/specs/2026-07-17-selvage-master-plan.md`와 `docs/superpowers/plans/2026-07-17-sprint-0a-ci-cd.md` 참조.
